using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// Impact puffs for mod effects, in place of the vanilla contact effects cloned templates carry (ContactGenericWall /
    /// ContactGenericSmall on walls; ArcadeyHitEffect2halfsize, ContactSkeletonArcher, FX_fishFireball_contact on bodies).
    ///
    /// * <see cref="FxFactory.Clone"/> sanitizes every clone: vanilla impact visuals become the neutral mod puff and the
    ///   hero's specialAttackContact burst (a 1-damage stun with a letterbox) is cleared, so no mod clone shows a vanilla
    ///   impact.
    /// * <see cref="FxKit.Projectile"/> and <see cref="FxKit.TimedHit"/> then theme the puff for their art sheet: a theme
    ///   registered with <see cref="AddTheme"/> claims sheet ids by prefix, the longest matching prefix wins, and
    ///   anything unclaimed keeps the neutral puff.
    ///
    /// Each puff template is a clone of the vanilla contact it replaces (keeping its sound, depth sorting and offsets)
    /// wearing the theme's art, built once per vanilla source and theme.
    /// </summary>
    public static class ImpactFx
    {
        /// <summary>The theme of effects no registered theme claims.</summary>
        public const string Neutral = "Mod";
        const string NeutralSheet = "FxCommonImpactMod";

        static readonly Dictionary<string, string> s_sheets = new Dictionary<string, string> { { Neutral, NeutralSheet } };
        // effect sheet id (without its leading "Fx") prefix -> theme key; sorted longest first on use
        static readonly List<KeyValuePair<string, string>> s_prefix = new List<KeyValuePair<string, string>>();
        static bool s_sorted;

        /// <summary>
        /// Register an impact theme. <paramref name="sheet"/> holds a "Wall" and a "Hit" anim (24 x 24 cells, impact point
        /// at the centre). Effects drawn from sheets whose id, without its leading "Fx", starts with one of
        /// <paramref name="prefixes"/> get its puffs; e.g. AddTheme("Ice", "FxIceImpact", "Ice", "Frost") themes
        /// FxIceShard and FxFrostBolt. Call before building the effects.
        /// </summary>
        public static void AddTheme(string key, string sheet, params string[] prefixes)
        {
            if (string.IsNullOrEmpty(key) || string.IsNullOrEmpty(sheet)) return;
            s_sheets[key] = sheet;
            if (prefixes != null) foreach (var p in prefixes) Map(p, key);
        }

        /// <summary>
        /// Let theme <paramref name="key"/> claim more sheet ids, e.g. Map("HeroGrave", "Bone") for an item sheet
        /// FxHeroGraveSpear. <paramref name="prefix"/> is the id without its leading "Fx". Call before building the effect.
        /// </summary>
        public static void Map(string prefix, string key)
        {
            if (string.IsNullOrEmpty(prefix) || string.IsNullOrEmpty(key)) return;
            if (HasFx(prefix)) prefix = prefix.Substring(2);
            s_prefix.RemoveAll(kv => kv.Key == prefix);
            s_prefix.Add(new KeyValuePair<string, string>(prefix, key));
            s_sorted = false;
        }

        /// <summary>The theme key an effect drawn with <paramref name="sheetId"/> uses (<see cref="Neutral"/> if none).</summary>
        public static string ThemeOf(string sheetId)
        {
            if (string.IsNullOrEmpty(sheetId)) return Neutral;
            if (!s_sorted) { s_prefix.Sort((a, b) => b.Key.Length.CompareTo(a.Key.Length)); s_sorted = true; }
            string id = HasFx(sheetId) ? sheetId.Substring(2) : sheetId;
            foreach (var kv in s_prefix)
                if (id.StartsWith(kv.Key, StringComparison.Ordinal)) return kv.Value;
            return Neutral;
        }

        // starts with the "Fx" every effect sheet id carries
        static bool HasFx(string id) { return id.Length > 2 && id[0] == 'F' && id[1] == 'x'; }

        // a key with no registered sheet falls back to the neutral theme
        static string Resolve(string key) { return key != null && s_sheets.ContainsKey(key) ? key : Neutral; }

        // ------------------------------------------------------------------------------------------------ templates
        /// <summary>Vanilla contact visuals this replaces (exact names; their families start with these).</summary>
        static readonly string[] s_vanillaImpact =
            { "ContactGenericWall", "ContactGenericSmall", "ArcadeyHitEffect", "ContactSkeletonArcher", "FX_fishFireball_contact" };
        /// <summary>Damaging vanilla bursts that must never ride along on a mod clone.</summary>
        static readonly string[] s_vanillaClear = { "specialAttackContact" };

        static readonly Dictionary<string, GameObject> s_puffs = new Dictionary<string, GameObject>();
        /// <summary>mod puff -> the vanilla contact it was cloned from (so a re-theme keeps the same sound/sorting).</summary>
        static readonly Dictionary<GameObject, GameObject> s_source = new Dictionary<GameObject, GameObject>();
        static readonly Dictionary<GameObject, int> s_kind = new Dictionary<GameObject, int>();   // 0 = vanilla impact, 1 = clear, -1 = other

        static int Kind(GameObject spawn)
        {
            if (spawn == null) return -1;
            int k;
            if (s_kind.TryGetValue(spawn, out k)) return k;
            k = -1;
            if (s_source.ContainsKey(spawn)) k = 0;
            else if (spawn.transform.parent == null)            // a vanilla prefab (mod templates live under the Holder)
            {
                var n = spawn.name;
                foreach (var v in s_vanillaClear) if (n == v) k = 1;
                if (k < 0) foreach (var v in s_vanillaImpact) if (n.StartsWith(v, StringComparison.Ordinal)) k = 0;
            }
            s_kind[spawn] = k;
            return k;
        }

        static bool HitsWalls(LayerMask m)
        {
            int wall = LayerMask.NameToLayer("Wall"), wallBase = LayerMask.NameToLayer("WallBase");
            return (wall >= 0 && (m.value & (1 << wall)) != 0) || (wallBase >= 0 && (m.value & (1 << wallBase)) != 0);
        }

        // the theme's puff for a contact that used to spawn vanilla (Wall or Hit anim)
        static GameObject Puff(string key, bool wall, GameObject vanilla = null, bool silent = false)
        {
            if (vanilla == null) vanilla = FxFactory.Vanilla(wall ? "ContactGenericWall" : "ArcadeyHitEffect2halfsize");
            GameObject src;
            if (vanilla != null && s_source.TryGetValue(vanilla, out src)) vanilla = src;     // a puff of ours: back to its source
            if (vanilla == null) return null;
            key = Resolve(key);
            string sheetId = s_sheets[key];
            string cacheKey = sheetId + (wall ? "|W|" : "|H|") + vanilla.GetInstanceID() + (silent ? "|S" : "");
            GameObject go;
            if (s_puffs.TryGetValue(cacheKey, out go)) return go;
            go = Build(key, sheetId, wall, vanilla, silent);
            s_puffs[cacheKey] = go;
            return go;
        }

        static GameObject Build(string key, string sheetId, bool wall, GameObject vanilla, bool silent)
        {
            var sh = SpriteSheets.Get(sheetId);
            string anim = wall ? "Wall" : "Hit";
            if (sh == null || !sh.Has(anim)) { FurtherCore.Log.LogWarning("ImpactFx: no " + sheetId + "/" + anim); return null; }
            string name = "ModImpact" + key + anim + "_" + vanilla.name + (silent ? "_Quiet" : "");
            var go = MonsterFactory.ClonePrefab(vanilla, name);
            FxFactory.Templates[name] = go;
            FxFactory.StripChildren(go);
            FxFactory.Reskin(go, new ClipBuilder(sh, anim, name + "Clip").Once().Build(), sh);
            var spr = go.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = exPlane.Anchor.MidCenter; spr.offset = Vector2.zero; spr.color = Color.white; }
            // radial art: no free rotation, no random tilt; a wall puff sits 3 px off the wall, toward the shooter
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, offsetX: wall ? 3f : 0f, canFlip: true, snap: 0f, freeRotate: false);
            var e = go.GetComponent<Effect>();
            if (e != null) { R.Set(e, "m_startAngle", new MinMaxRange(0f)); R.Set(e, "m_fadeOutTime", 0f); }
            FxFactory.SetMotion(go, 0f, enabled: false);
            foreach (var d in go.GetComponentsInChildren<DamageEffect>(true)) d.enabled = false;
            foreach (var t in go.GetComponentsInChildren<ColorTinter>(true)) t.enabled = false;
            // a puff added where vanilla spawned nothing must not add a sound the game never played there
            if (silent) { var a = go.GetComponent<AudioCueSource>(); if (a != null) R.Set(a, "m_playOnSpawn", null); }
            // a body hit lands at chest height: sort it in front of the victim whose feet are below it
            var dh = go.GetComponent<DepthHandler>();
            if (dh != null) dh.m_heightOffset = wall ? -4f : -22f;
            s_source[go] = vanilla;
            s_kind[go] = 0;
            return go;
        }

        // ------------------------------------------------------------------------------------------------ rewiring
        static bool s_inSanitize;

        /// <summary>
        /// Called by FxFactory.Clone on every new template: vanilla impact visuals become the neutral mod puff, the hero's
        /// damaging specialAttackContact burst is removed.
        /// </summary>
        internal static void Sanitize(GameObject fx)
        {
            if (fx == null || s_inSanitize) return;
            s_inSanitize = true;
            try { Rewire(fx, Neutral, false); }
            catch (Exception ex) { FurtherCore.Log.LogError("ImpactFx.Sanitize " + fx.name + ": " + ex); }
            finally { s_inSanitize = false; }
        }

        /// <summary>Re-theme every impact puff on <paramref name="fx"/> for the theme that claims <paramref name="artSheet"/>.</summary>
        public static void Theme(GameObject fx, string artSheet)
        {
            ThemeAs(fx, ThemeOf(artSheet));
        }

        /// <summary>
        /// Projectiles: re-theme as <see cref="Theme"/>, and give every body contact that ends the shot but spawns nothing
        /// (DFX_skelMageNewProjectile's player contact, webBall's feet contact once its web zone is dropped) the theme's
        /// Hit puff, so every bolt reads on impact. Callers that set their own spawnOnHit afterwards still win.
        /// </summary>
        public static void ThemeProjectile(GameObject fx, string artSheet)
        {
            if (fx == null) return;
            string key = ThemeOf(artSheet);
            try
            {
                Rewire(fx, key, true);
                var d = fx.GetComponent<DamageEffect>();
                if (d == null || d.m_contactData == null) return;
                foreach (var c in d.m_contactData)
                    if (c != null && c.m_spawnOnHit == null && c.m_destroyOnHit && !HitsWalls(c.m_layerMask) && HitsBodies(c.m_layerMask))
                        c.m_spawnOnHit = Puff(key, false, null, silent: true);
            }
            catch (Exception ex) { FurtherCore.Log.LogError("ImpactFx.ThemeProjectile " + fx.name + ": " + ex); }
        }

        static bool HitsBodies(LayerMask m)
        {
            int a = LayerMask.NameToLayer("DamagablePlayer"), b = LayerMask.NameToLayer("PlayerBase");
            return (a >= 0 && (m.value & (1 << a)) != 0) || (b >= 0 && (m.value & (1 << b)) != 0);
        }

        /// <summary>Re-theme every impact puff on <paramref name="fx"/> for theme <paramref name="key"/>.</summary>
        public static void ThemeAs(GameObject fx, string key)
        {
            if (fx == null) return;
            try { Rewire(fx, key ?? Neutral, true); }
            catch (Exception ex) { FurtherCore.Log.LogError("ImpactFx.Theme " + fx.name + ": " + ex); }
        }

        static void Rewire(GameObject fx, string key, bool log)
        {
            int n = 0;
            foreach (var d in fx.GetComponentsInChildren<DamageEffect>(true))
            {
                if (d.m_contactData == null) continue;
                foreach (var c in d.m_contactData)
                {
                    if (c == null || c.m_spawnOnHit == null) continue;
                    int k = Kind(c.m_spawnOnHit);
                    if (k == 1) { c.m_spawnOnHit = null; n++; continue; }
                    if (k != 0) continue;
                    c.m_spawnOnHit = Puff(key, HitsWalls(c.m_layerMask), c.m_spawnOnHit);   // null if the art is missing
                    n++;
                }
                // the legacy top-level field is never read at run time, but keep it consistent for anything that copies it
                if (d.m_spawnOnHit != null)
                {
                    int k = Kind(d.m_spawnOnHit);
                    if (k == 1) d.m_spawnOnHit = null;
                    else if (k == 0) d.m_spawnOnHit = Puff(key, false, d.m_spawnOnHit);
                }
            }
            if (log && n > 0) FurtherCore.Log.LogInfo("ImpactFx: " + fx.name + " -> " + key + " (" + n + " contact" + (n == 1 ? ")" : "s)"));
        }
    }
}
