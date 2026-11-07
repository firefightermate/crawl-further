using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;

    /// <summary>
    /// Timed crowd control with diminishing returns, and drawn overlays for any status.
    ///
    /// The vanilla slows (lava goo, stuck-to-floor) have no duration because the game only applies them from a zone that
    /// removes them on exit: put on a projectile they never expired and also blocked attacking. <see cref="Slow"/>,
    /// <see cref="Root"/> and <see cref="Daze"/> always expire, never block attacks (except the short daze), and once a
    /// chain of crowd control ends the target can't be slowed again for <see cref="ImmuneTime"/> seconds.
    /// <see cref="FxFactory.GetStatus"/> hands these out in place of the vanilla names.
    /// </summary>
    public static class ModStatus
    {
        /// <summary>Seconds of <see cref="Slow"/> (move speed x0.55).</summary>
        public const float SlowTime = 1.0f;
        /// <summary>Seconds of <see cref="Root"/> (move speed x0.15).</summary>
        public const float RootTime = 0.8f;
        /// <summary>Seconds of <see cref="Daze"/> (can't act).</summary>
        public const float DazeTime = 0.6f;
        /// <summary>The longest any chain of crowd control can last, in seconds.</summary>
        public const float WindowTime = 1.2f;
        /// <summary>Seconds of immunity after the window closes.</summary>
        public const float ImmuneTime = 3.0f;

        static Status s_slow, s_root, s_daze;
        static readonly HashSet<Status> s_cc = new HashSet<Status>();

        /// <summary>Timed slow (replaces StatusLavaSteveGoo).</summary>
        public static Status Slow { get { Build(); return s_slow; } }
        /// <summary>Timed root (replaces StatusStuckToFloor).</summary>
        public static Status Root { get { Build(); return s_root; } }
        /// <summary>Short stun (replaces StatusDizzy).</summary>
        public static Status Daze { get { Build(); return s_daze; } }

        /// <summary>
        /// For crowd control of your own (a grab, a hold): true if it may land on <paramref name="who"/> now, which also
        /// opens its window; false while <paramref name="who"/> is immune after an earlier chain.
        /// </summary>
        public static bool AllowCrowdControl(GameObject who)
        {
            if (who == null) return true;
            var g = who.GetComponent<CCGuard>() ?? who.AddComponent<CCGuard>();
            return g.Allow();
        }

        internal static bool IsCC(Status s) { return s != null && s_cc.Contains(s); }

        /// <summary>The timed replacement for a vanilla crowd-control status name, or null for any other name.</summary>
        internal static Status Redirect(string vanillaName)
        {
            switch (vanillaName)
            {
                case "StatusLavaSteveGoo": return Slow;
                case "StatusStuckToFloor": return Root;
                case "StatusDizzy": return Daze;
            }
            return null;
        }

        static void Build()
        {
            if (s_slow != null) return;
            s_slow = Make("StatusLavaSteveGoo", "ModStatusSlow", "Slow", SlowTime, false, 0.55f, 0.7f);
            s_root = Make("StatusStuckToFloor", "ModStatusRoot", "Slow", RootTime, false, 0.15f, 0.4f);
            s_daze = Make("StatusDizzy", "ModStatusDaze", "Stun", DazeTime, true, 0f, 0f);
            foreach (var s in new[] { s_slow, s_root, s_daze }) if (s != null) s_cc.Add(s);
            // the drawn overlays carry the status; the tint stays as a soft second cue in the overlay's colours
            if (s_slow != null) s_slow.m_tintColour = new Color(0.62f, 0.55f, 0.25f, 0.12f);    // ochre sludge
            if (s_root != null) s_root.m_tintColour = new Color(0.55f, 0.42f, 0.28f, 0.12f);    // bark
            if (s_daze != null) s_daze.m_tintColour = new Color(0f, 0f, 0f, 0f);
            RegisterOverlay(s_slow, "FxCommonStatusSlow", "Loop", -2f, OverlayAt.Feet, null);
            RegisterOverlay(s_root, "FxCommonStatusRoot", "Loop", -2f, OverlayAt.Feet, "Grip");
            RegisterOverlay(s_daze, "FxCommonStatusDaze", "Loop", 1f, OverlayAt.Head, null);
        }

        // ------------------------------------------------------------------------------------------- overlays
        static readonly Dictionary<string, StatusOverlayDef> s_overlayByName = new Dictionary<string, StatusOverlayDef>();
        static readonly Dictionary<Status, StatusOverlayDef> s_overlay = new Dictionary<Status, StatusOverlayDef>();

        /// <summary>
        /// Show an animated overlay on anyone (hero or monster) carrying the status named <paramref name="statusName"/>
        /// (the Status object's name, e.g. "ModStatusAcid"), for exactly as long as the status lasts.
        /// <paramref name="anim"/> loops; if the sheet also has "&lt;anim&gt;Big" it is used on large victims.
        /// <paramref name="offsetY"/>: px above the victim's feet for the cell's bottom-centre. A value of 12 or more
        /// means "over the head": the overlay is lifted further when the victim is taller, so it never sits inside it.
        /// </summary>
        public static void RegisterOverlay(string statusName, string sheet, string anim, float offsetY)
        {
            var d = MakeOverlay(statusName, sheet, anim, offsetY, OverlayAt.Feet, null);
            if (d != null) { d.liftOverHead = offsetY >= 12f; Store(d); }
        }

        /// <summary>
        /// As above with an explicit anchor: <see cref="OverlayAt.Head"/> puts the cell's bottom-centre offsetY px above
        /// the victim's head (head overlays stack upward), <see cref="OverlayAt.Feet"/> offsetY px above the feet.
        /// <paramref name="intro"/> (optional) plays once before the loop (e.g. "Grip"), with its own "Big" variant.
        /// </summary>
        public static void RegisterOverlay(string statusName, string sheet, string anim, float offsetY, OverlayAt at, string intro = null)
        {
            var d = MakeOverlay(statusName, sheet, anim, offsetY, at, intro);
            if (d != null) Store(d);
        }

        static void RegisterOverlay(Status status, string sheet, string anim, float offsetY, OverlayAt at, string intro)
        {
            if (status == null) return;
            var d = MakeOverlay(status.gameObject.name, sheet, anim, offsetY, at, intro);
            if (d == null) return;
            d.status = status;
            Store(d);
        }

        /// <summary>
        /// An overlay not tied to a status (stacks, charges, timed buffs, heal bursts): show and hide it with
        /// <see cref="ModInd"/>. Same placement, sizing, stacking and clean-up as status overlays, and it is also dropped
        /// when the character dies. <paramref name="once"/>: plays its anim once and then frees its slot.
        /// </summary>
        public static StatusOverlayDef Indicator(string id, string sheet, string anim, float offsetY, OverlayAt at, bool once = false)
        {
            var d = MakeOverlay(id, sheet, anim, offsetY, at, null, once);
            if (d != null) d.indicator = true;
            return d;
        }

        static void Store(StatusOverlayDef d)
        {
            s_overlayByName[d.statusName] = d;
            // re-resolve lazily: drop cached lookups (including cached misses) for this name
            var stale = new List<Status>();
            foreach (var kv in s_overlay) if (kv.Key != null && (kv.Value == null || kv.Value.statusName == d.statusName)) stale.Add(kv.Key);
            foreach (var k in stale) s_overlay.Remove(k);
            if (d.status != null) s_overlay[d.status] = d;
            FurtherCore.Log.LogInfo("ModStatus overlay: " + d.statusName + " -> " + (d.small != null ? d.small.name : "none") + (d.big != null ? " (+Big)" : ""));
        }

        static StatusOverlayDef MakeOverlay(string statusName, string sheet, string anim, float offsetY, OverlayAt at, string intro, bool once = false)
        {
            if (string.IsNullOrEmpty(statusName)) return null;
            var sh = SpriteSheets.Get(sheet);
            if (sh == null || !sh.Has(anim)) { FurtherCore.Log.LogWarning("ModStatus overlay " + statusName + ": missing " + sheet + "/" + anim); return null; }
            var d = new StatusOverlayDef { statusName = statusName, at = at, offsetY = offsetY };
            d.small = OverlayTemplate(statusName + "Fx", sh, anim, intro, once);
            if (sh.Has(anim + "Big"))
                d.big = OverlayTemplate(statusName + "FxBig", sh, anim + "Big", intro != null && sh.Has(intro + "Big") ? intro + "Big" : intro, once);
            d.once = once;
            var a = sh.Anim(anim);
            int bx, by, bw, bh;
            d.height = a != null && a.frames.Length > 0 && MonsterFactory.Bounds(sh, a.frames[0], out bx, out by, out bw, out bh)
                ? by + bh : sh.manifest.cellH;
            return d.small != null ? d : null;
        }

        static GameObject OverlayTemplate(string name, SpriteSheet sh, string anim, string intro, bool once = false)
        {
            exSpriteAnimClip clip;
            bool hasIntro = intro != null && sh.Has(intro);
            if (once)
            {
                // a one-shot (heal burst): plays once, follows the character, and frees its slot when the anim ends
                var go1 = FxFactory.Visual("Mod" + name, sh, new ClipBuilder(sh, anim, name + "Clip").Once().Build(), loop: false);
                if (go1 == null) return null;
                FxFactory.SetEffect(go1, destroyOnAnimEnd: true, canFlip: false, freeRotate: false);
                var dh1 = go1.GetComponent<DepthHandler>();
                if (dh1 != null) UnityEngine.Object.DestroyImmediate(dh1);
                return go1;
            }
            if (hasIntro)
            {
                var cb = new ClipBuilder(sh, intro, name + "Clip").Once().Then(anim);
                clip = cb.Ev(sh.Anim(intro).frames.Length, "AnimLoopStart").Build();     // Effect replays from the loop start
            }
            else clip = new ClipBuilder(sh, anim, name + "Clip").Loop().Build();
            var go = FxFactory.Visual("Mod" + name, sh, clip, loop: !hasIntro);
            if (go == null) return null;
            FxFactory.SetEffect(go, destroyOnAnimEnd: false, canFlip: false, freeRotate: false);   // lives until the status ends
            var dh = go.GetComponent<DepthHandler>();
            if (dh != null) UnityEngine.Object.DestroyImmediate(dh);                                // StatusOverlays sorts it
            return go;
        }

        /// <summary>The overlay for a status (null if none). One string lookup per Status object, then cached.</summary>
        internal static StatusOverlayDef OverlayFor(Status s)
        {
            if (s == null) return null;
            StatusOverlayDef d;
            if (s_overlay.TryGetValue(s, out d)) return d;
            s_overlayByName.TryGetValue(s.gameObject.name, out d);
            s_overlay[s] = d;
            return d;
        }

        static Status Make(string vanilla, string name, string cls, float duration, bool stun, float speedMult, float animMult)
        {
            Status src = null;
            foreach (var st in Resources.FindObjectsOfTypeAll<Status>())
                if (st.gameObject.name == vanilla) { src = st; break; }
            if (src == null) { FurtherCore.Log.LogWarning("ModStatus: no " + vanilla); return null; }
            var go = MonsterFactory.ClonePrefab(src.gameObject, name);
            var s = go.GetComponent<Status>();
            s.m_class = cls;
            s.m_duration = duration;
            s.m_stacks = false;
            s.m_damage = 0f;
            s.m_preventAttack = stun;
            s.m_preventMove = stun;
            // StatusDizzy's idle anim is the hero's "DizzyStart" (AtlasHero): on a monster it would swap the
            // monster's sprite for hero frames while dazed. These clones land on monsters too, so drop the anims.
            s.m_idleAnim = null; s.m_runAnim = null; s.m_knockbackAnim = null; s.m_gainStatusAnim = null;
            s.m_unityIdleAnim = null; s.m_unityRunAnim = null;
            // StatusDizzy spawns the vanilla FXDizzyStars through m_effects: the drawn overlay replaces it
            s.m_effects = new DamageEffectData[0];
            s.m_damageEffect = new DamageEffectData { m_object = null };
            s.m_effectOnRemove = new DamageEffectData { m_object = null };
            if (!stun)
            {
                var mods = new List<PlayerModifier>();
                Action<PlayerModifier.eType, float> add = (t, v) => mods.Add(new PlayerModifier
                {
                    m_modify = t, m_type = ValueModifier.eModifierType.Multiply, m_value = v, m_priority = 500f
                });
                add(PlayerModifier.eType.HeroSpeed, speedMult);
                add(PlayerModifier.eType.MonsterSpeed, speedMult);
                add(PlayerModifier.eType.HeroAccel, Mathf.Max(0.3f, speedMult));
                add(PlayerModifier.eType.MonsterAccel, Mathf.Max(0.3f, speedMult));
                add(PlayerModifier.eType.HeroMoveAnimSpeed, animMult);
                add(PlayerModifier.eType.MonsterMoveAnimSpeed, animMult);
                s.m_modifiers = mods;
            }
            FurtherCore.Log.LogInfo("ModStatus " + name + ": " + duration + "s");
            return s;
        }
    }

    /// <summary>The crowd-control guard decides whether a timed CC status may land; then its overlay is shown.</summary>
    [HarmonyPatch(typeof(PlayerStatusManager), "AddStatus", new[] { typeof(Status), typeof(DamageSource), typeof(string) })]
    static class Patch_StatusAdd
    {
        static readonly AccessTools.FieldRef<PlayerStatusManager, Player> s_player =
            AccessTools.FieldRefAccess<PlayerStatusManager, Player>("m_player");

        static bool Prefix(PlayerStatusManager __instance, Status status, DamageSource damageSource, bool __runOriginal)
        {
            // another prefix (a boss mod's status immunity, say) already refused it: start no diminishing-returns window
            if (!__runOriginal) return false;
            try
            {
                if (status is StatusThieving && !MayThieve(damageSource)) return false;
                if (status == null || !ModStatus.IsCC(status)) return true;
                var p = s_player(__instance);
                if (p == null) return true;
                var g = p.GetComponent<CCGuard>() ?? p.gameObject.AddComponent<CCGuard>();
                return g.Allow();
            }
            catch (Exception e) { FurtherCore.Log.LogError("CC guard: " + e); return true; }
        }

        /// <summary>
        /// A monster cloned from a thief (the gnome) inherits its gold-stealing hit. Mod monsters keep it only when
        /// their traits say so (<see cref="MonsterTraits.stealsGold"/>); vanilla monsters are untouched.
        /// </summary>
        static bool MayThieve(DamageSource src)
        {
            if (src == null) return true;
            var owner = src.m_sourceOwnerPlayer ?? src.m_sourceOwner ?? src.m_source;
            var mm = owner != null ? owner.GetComponent<ModMonster>() : null;
            return mm == null || (mm.Traits != null && mm.Traits.stealsGold);
        }

        // only once the status is really on (the guard or the game may have refused it)
        static void Postfix(PlayerStatusManager __instance, Status status)
        {
            try
            {
                var d = ModStatus.OverlayFor(status);
                if (d == null || !StatusOverlays.Has(__instance, status)) return;
                var go = StatusOverlays.Owner(__instance);
                if (go == null) return;
                var t = go.GetComponent<StatusOverlays>() ?? go.AddComponent<StatusOverlays>();
                t.Show(d);
            }
            catch (Exception e) { FurtherCore.Log.LogError("status overlay: " + e); }
        }
    }

    /// <summary>Every way a status ends (timer, CC window, damage, death, encounter end, despawn) goes through here.</summary>
    [HarmonyPatch(typeof(PlayerStatusManager), "RemoveStatus", new[] { typeof(ActiveStatus) })]
    static class Patch_StatusRemove
    {
        static void Postfix(PlayerStatusManager __instance, ActiveStatus activeStatus)
        {
            try
            {
                if (activeStatus == null) return;
                var d = ModStatus.OverlayFor(activeStatus.m_data);
                if (d == null || StatusOverlays.Has(__instance, activeStatus.m_data)) return;
                var go = StatusOverlays.Owner(__instance);
                var t = go != null ? go.GetComponent<StatusOverlays>() : null;
                if (t != null) t.Hide(d);
            }
            catch (Exception e) { FurtherCore.Log.LogError("status overlay remove: " + e); }
        }
    }
}
