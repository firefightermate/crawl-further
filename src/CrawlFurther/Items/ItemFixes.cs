using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Items
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.Kaurn;
    using CrawlFurther.Content.Gods.Vhorrul;

    /// <summary>
    /// Shared helpers that make shop items behave the way their descriptions say.
    ///
    /// Follower tokens (Rotting Apple, Saint's Wick, Lightning Rod) are clones of the Book of Tears. The book
    /// activates on the hero's attack (m_activateOn = Attack, so m_activateOnTime does nothing), and it fires through
    /// AnimAttack events inside its own state clips. Swapping every state clip for one looping idle clip removed those
    /// events and left the Activate state (transition on finish) stuck forever on a clip that never finishes, so the
    /// tokens never fired. Follower() switches them to timed activation and gives them an Activate clip that fires.
    /// </summary>
    public static class ItemFixes
    {
        static readonly FieldInfo s_isHero = AccessTools.Field(typeof(Player), "m_isHero");
        static readonly FieldInfo s_ghost = AccessTools.Field(typeof(Player), "m_isGhost");

        /// <summary>The DamageInfo Health.Damage is currently processing (see Patch_ItemDamageTag).</summary>
        public static DamageInfo Incoming;

        // ------------------------------------------------------------------------------------- monsters
        public static bool LiveMonster(Player p, GameObject hero)
        {
            if (p == null || !p.gameObject.activeInHierarchy || p.gameObject == hero) return false;
            if (s_isHero != null && (bool)s_isHero.GetValue(p)) return false;
            if (s_ghost != null && (bool)s_ghost.GetValue(p)) return false;
            var h = p.GetComponent<Health>();
            return h != null && h.IsAlive();
        }

        /// <summary>Centre of a player's hurtbox (the DamagablePlayer child collider), else 8 px above its feet.</summary>
        public static Vector2 AimPoint(GameObject who)
        {
            var c = Hurtbox(who);
            return c != null && c.enabled ? (Vector2)c.bounds.center : (Vector2)who.transform.position + new Vector2(0f, 8f);
        }

        /// <summary>A player's hurtbox collider (the DamagablePlayer child), or null. Searches the children: callers that
        /// track one target every frame should cache the result (see SeekMonsterFx).</summary>
        public static Collider Hurtbox(GameObject who) { return ModUtil.Hurtbox(who); }

        static Player[] s_players;
        static float s_playersAt = -1f;

        /// <summary>Nearest living monster (not the hero, not a ghost) to a point, within range.</summary>
        public static GameObject NearestMonster(Vector2 from, float range)
        {
            var hero = ModUtil.Hero();
            GameObject best = null;
            float bd = range * range;
            if (s_players == null || Time.unscaledTime - s_playersAt > 0.2f)
            {
                s_players = UnityEngine.Object.FindObjectsOfType<Player>();      // one shared scan per 0.2 s for all tokens
                s_playersAt = Time.unscaledTime;
            }
            foreach (var p in s_players)
            {
                if (p == null || !LiveMonster(p, hero)) continue;
                float d = ((Vector2)p.transform.position - from).sqrMagnitude;
                if (d < bd) { bd = d; best = p.gameObject; }
            }
            return best;
        }

        // ------------------------------------------------------------------------------------- templates
        static void Chain(GameObject tmpl, Action<GameObject> a)
        {
            Action<GameObject> prev;
            FxFactory.OnSpawn.TryGetValue(tmpl, out prev);
            FxFactory.OnSpawn[tmpl] = i => { if (prev != null) prev(i); a(i); };
        }

        /// <summary>
        /// On every spawn, turn the effect to face the nearest monster before its Effect / ParticleMotion read the
        /// spawn rotation (the hook runs inside SpawnBegin; their OnSpawn runs at SpawnFinalize or Start).
        /// </summary>
        public static void AimAtMonsters(GameObject tmpl, float range)
        {
            if (tmpl == null) return;
            Chain(tmpl, i =>
            {
                Vector2 p = i.transform.position;
                var t = NearestMonster(p, range);
                if (t == null) return;
                var d = AimPoint(t) - p;
                if (d.sqrMagnitude < 1f) return;
                i.transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
            });
        }

        /// <summary>Keep steering a projectile toward the nearest monster (its ParticleMotion must accelerate).</summary>
        public static void SeekMonsters(GameObject tmpl, float range)
        {
            if (tmpl == null) return;
            foreach (var s in tmpl.GetComponents<ParticleMotionSeek>()) UnityEngine.Object.DestroyImmediate(s);   // that one seeks the hero
            Chain(tmpl, i => { var s = i.GetComponent<SeekMonsterFx>() ?? i.AddComponent<SeekMonsterFx>(); s.range = range; s.Reset(); });
        }

        /// <summary>Pass through bodies but still stop at walls (a blanket destroyOnHit = false also let it fly
        /// through walls for its whole life).</summary>
        public static void PierceMonsters(GameObject tmpl)
        {
            var de = tmpl != null ? tmpl.GetComponent<DamageEffect>() : null;
            if (de == null || de.m_contactData == null) return;
            int wall = LayerMask.NameToLayer("Wall");
            foreach (var c in de.m_contactData)
                if (c != null) c.m_destroyOnHit = wall >= 0 && (c.m_layerMask.value & (1 << wall)) != 0;
        }

        /// <summary>A hero-only copy of a template (keeps its spawn hooks), registered with the other templates.</summary>
        public static GameObject HeroCopy(GameObject template, string name, float damageMult = 1f)
        {
            if (template == null) return null;
            return FxKit.Weakened(template, name, damageMult);
        }

        // ------------------------------------------------------------------------------------- followers
        /// <summary>
        /// Make a Book-of-Tears clone a timed follower: it floats after the hero wearing `art` and every `interval`
        /// seconds (while a monster is within `range` of the hero) fires effect 0 (`shot`) from itself.
        /// </summary>
        public static void Follower(GameObject go, Powerup pu, string art, float interval, GameObject shot, float range = 170f)
        {
            if (go == null || pu == null) return;
            R.Set(pu, "m_activateOn", Powerup.eActivateOn.Time);
            R.Set(pu, "m_activateOnTime", new MinMaxRange(interval));
            R.Set(pu, "m_effectSpawnOnActivate", false);          // the Activate clip fires it, once
            var e = R.Get<System.Collections.IList>(pu, "m_effects");
            if (e != null && e.Count > 0 && shot != null)
            {
                var d = e[0] as DamageEffectData;
                if (d != null) d.m_object = shot;
            }
            TokenClips(go, art);
            Chain(go, i => { var h = i.GetComponent<FollowerHoldFx>() ?? i.AddComponent<FollowerHoldFx>(); h.range = range; h.Reset(); });
        }

        /// <summary>
        /// Re-skin a follower token's states with mod art without breaking its state machine: Idle/Ready/Wait loop
        /// the idle art; Activate plays it once and fires AnimAttack(0) (+ the book's flash) on its second frame, then
        /// finishes so the state machine moves on; WakeUp plays once.
        /// </summary>
        public static void TokenClips(GameObject go, string art)
        {
            var sh = SpriteSheets.Get(art);
            var asm = go != null ? go.GetComponent<AnimStateMachine>() : null;
            if (sh == null || !sh.Has("Idle") || asm == null) return;
            var idle = new ClipBuilder(sh, "Idle", "Mod" + art + "TokenIdle").Loop().Build();
            exSpriteAnimClip shoot, wake, ready, wait;
            if (sh.Has("Activate"))
            {
                // drawn token sheets (art/out_itemfx FxItemToken*): one clip per Book of Tears state. The shot leaves on
                // Activate frame 3, the brightest frame (TIMING.md); Wait is the greyed cooldown, WakeUp the 4-frame flash.
                shoot = new ClipBuilder(sh, "Activate", "Mod" + art + "TokenShoot").Once().Ev(3, "AnimAttack", 0).Ev(3, "AnimFlash", 0).Build();
                ready = new ClipBuilder(sh, sh.Has("Ready") ? "Ready" : "Idle", "Mod" + art + "TokenReady").Loop().Build();
                wait = new ClipBuilder(sh, sh.Has("Wait") ? "Wait" : "Idle", "Mod" + art + "TokenWait").Loop().Build();
                wake = new ClipBuilder(sh, sh.Has("WakeUp") ? "WakeUp" : "Idle", "Mod" + art + "TokenWake").Once().Build();
            }
            else
            {
                var a = sh.Anim("Idle");
                int fire = a.frames.Length > 1 ? 1 : 0;
                shoot = new ClipBuilder(sh, "Idle", "Mod" + art + "TokenShoot").Once().Durations(0.14f, 0.3f)
                    .Ev(fire, "AnimAttack", 0).Ev(fire, "AnimFlash", 0).Build();
                wake = new ClipBuilder(sh, "Idle", "Mod" + art + "TokenWake").Once().Durations(0.1f, 0.1f).Build();
                ready = idle; wait = idle;
            }
            if (idle == null || shoot == null || wake == null || ready == null || wait == null) return;
            foreach (var st in asm.m_states)
            {
                if (st == null || st.m_animation == null) continue;       // Spawn has none: keep it that way
                if (st.m_name == "Activate") st.m_animation = shoot;
                else if (st.m_name == "WakeUp") st.m_animation = wake;
                else if (st.m_name == "Ready") st.m_animation = ready;
                else if (st.m_name == "Wait") st.m_animation = wait;
                else st.m_animation = idle;
            }
            ItemArt.Place(go, art);
            var spr = go.GetComponent<exSprite>();
            if (spr != null && idle.frameInfos.Count > 0)
            {
                spr.SetSprite(sh.atlas, idle.frameInfos[0].index);
                var r = spr.GetComponent<Renderer>();
                if (r != null && sh.atlas.material != null) r.sharedMaterial = sh.atlas.material;
            }
        }
    }

    /// <summary>
    /// Item world art (art/out_itemfx, drawn by tools/sprites/item_fx.py). Every sheet's json carries "origin": the cell
    /// pixel that sits on the effect's spawn point, so <see cref="Place"/> lines the drawing up with the collider the
    /// template already has. <see cref="Wear"/> re-dresses a hero copy of a template in item art while keeping its
    /// clip's events (damage on/off, sounds) on the same times: the item sheets copy the per-frame durations of the
    /// clip they replace, so gameplay timing is unchanged.
    /// </summary>
    public static class ItemArt
    {
        static readonly Dictionary<string, Vector2> s_origin = new Dictionary<string, Vector2>();

        public static bool Origin(string sheet, out int x, out int y)
        {
            x = y = 0;
            Vector2 o;
            if (!s_origin.TryGetValue(sheet, out o))
            {
                o = new Vector2(-1f, -1f);
                try
                {
                    var path = SpriteSheets.PathOf(sheet + ".json");
                    var d = System.IO.File.Exists(path) ? MiniJson.Parse(System.IO.File.ReadAllText(path)) as Dictionary<string, object> : null;
                    object v;
                    if (d != null && d.TryGetValue("origin", out v) && v is List<object> && ((List<object>)v).Count == 2)
                        o = new Vector2(Convert.ToSingle(((List<object>)v)[0]), Convert.ToSingle(((List<object>)v)[1]));
                }
                catch (Exception e) { Plugin.Log.LogWarning("ItemArt: no origin for " + sheet + ": " + e.Message); }
                s_origin[sheet] = o;
            }
            if (o.x < 0f) return false;
            x = (int)o.x; y = (int)o.y;
            return true;
        }

        /// <summary>Put the sheet's origin pixel on the effect's spawn point.</summary>
        public static void Place(GameObject go, string sheet)
        {
            int x, y;
            if (go != null && Origin(sheet, out x, out y)) Strike.ArtAt(go, sheet, x, y);
        }

        /// <summary>
        /// Dress a template in item art: swap its clip for <paramref name="anim"/> of <paramref name="sheet"/> (events kept,
        /// time-scaled to the new length), drop any tint, and place the art on the origin. Colliders are left alone.
        /// </summary>
        public static GameObject Wear(GameObject go, string sheet, string anim, bool? loop = null)
        {
            if (go == null) return null;
            var sh = SpriteSheets.Get(sheet);
            if (sh == null || !sh.Has(anim)) { Plugin.Log.LogWarning("ItemArt: missing " + sheet + "/" + anim); return go; }
            var an = go.GetComponent<exSpriteAnimation>();
            var eff = go.GetComponent<Effect>();
            exSpriteAnimClip tmpl = an != null ? an.defaultAnimation : null;
            if (tmpl == null && eff != null) tmpl = R.Get<exSpriteAnimClip>(eff, "m_animationDefault");
            var clip = SpriteSheets.MakeClip(sh, anim, tmpl, go.name + "Item" + anim);
            if (clip == null) return go;
            if (loop.HasValue) clip.wrapMode = loop.Value ? WrapMode.Loop : WrapMode.Once;
            FxFactory.Reskin(go, clip, sh);
            foreach (var s in go.GetComponents<exSprite>()) s.color = Color.white;
            FxKit.NoTint(go);
            Place(go, sheet);
            DropBorrowedPuffs(go);
            return go;
        }

        /// <summary>
        /// A hero copy of a monster template also copied that monster's (or a vanilla) impact puff on its contacts. Drop
        /// every purely visual on-hit spawn; keep the ones that do something (pools, bursts: anything with a DamageEffect
        /// or StatusZone). Projectiles get the item's own puff back through <see cref="Puffs"/>.
        /// </summary>
        public static void DropBorrowedPuffs(GameObject go)
        {
            var de = go != null ? go.GetComponent<DamageEffect>() : null;
            if (de == null) return;
            if (de.m_contactData != null)
                foreach (var c in de.m_contactData)
                    if (c != null && c.m_spawnOnHit != null && !Functional(c.m_spawnOnHit)) c.m_spawnOnHit = null;
            var top = R.Get<GameObject>(de, "m_spawnOnHit");
            if (top != null && !Functional(top)) R.Set(de, "m_spawnOnHit", null);
        }

        static bool Functional(GameObject g)
        {
            return g.GetComponent<DamageEffect>() != null || g.GetComponent<StatusZone>() != null || g.GetComponent<ParticleMotion>() != null && g.GetComponent<ParticleMotion>().enabled && R.Get<GameObject>(g.GetComponent<ParticleMotion>(), "m_trailObject") != null;
        }

        /// <summary>Art drawn at full size: undo a template scale the copy inherited, including the KeepScale spawn hook
        /// it copied from a scaled monster template (which would put the old scale back on every spawn).</summary>
        public static void UnitScale(GameObject go)
        {
            if (go == null) return;
            go.transform.localScale = Vector3.one;
            Action<GameObject> prev;
            FxFactory.OnSpawn.TryGetValue(go, out prev);
            FxFactory.OnSpawn[go] = i =>
            {
                if (prev != null) prev(i);
                var c = i.transform.localScale;
                i.transform.localScale = new Vector3(c.x < 0f ? -1f : 1f, 1f, 1f);
            };
        }

        /// <summary>A pure visual from an item sheet, placed on its origin.</summary>
        public static GameObject Visual(string name, string sheet, string anim, bool loop = false)
        {
            var v = FxKit.Visual(name, sheet, anim, loop);
            Place(v, sheet);
            return v;
        }

        /// <summary>A clip of an item sheet (for swapping anims on a live instance).</summary>
        public static exSpriteAnimClip Clip(string sheet, string anim, bool loop = false)
        {
            var sh = SpriteSheets.Get(sheet);
            if (sh == null || !sh.Has(anim)) return null;
            var cb = new ClipBuilder(sh, anim, "ModItem" + sheet + anim);
            if (loop) cb.Loop(); else cb.Once();
            return cb.Build();
        }

        /// <summary>Register a clip on a live animation (through AddAnimation: ex2D keeps a name table, and a clip pushed straight
        /// into .animations would make the next Play throw) and optionally play it.</summary>
        public static void Ensure(exSpriteAnimation an, exSpriteAnimClip clip, bool play)
        {
            if (an == null || clip == null) return;
            if (an.GetAnimation(clip.name) == null) an.AddAnimation(clip);
            if (play && an.isActiveAndEnabled) an.Play(clip.name, 0);
        }

        /// <summary>The item's own impact art: hitPuff where it touches a body, wallPuff (or nothing) on walls.</summary>
        public static void Puffs(GameObject go, GameObject hitPuff, GameObject wallPuff = null)
        {
            var de = go != null ? go.GetComponent<DamageEffect>() : null;
            if (de == null) return;
            int wall = LayerMask.NameToLayer("Wall"), wallBase = LayerMask.NameToLayer("WallBase");
            if (de.m_contactData != null)
                foreach (var c in de.m_contactData)
                {
                    if (c == null) continue;
                    bool isWall = (wall >= 0 && (c.m_layerMask.value & (1 << wall)) != 0) || (wallBase >= 0 && (c.m_layerMask.value & (1 << wallBase)) != 0);
                    c.m_spawnOnHit = isWall ? (wallPuff ?? hitPuff) : hitPuff;
                }
            R.Set(de, "m_spawnOnHit", hitPuff);
        }

        /// <summary>
        /// A hero runner (HeroSlimeDropper / WebDropper clone) made visible in its item's art, upright and flipping to
        /// face its way; and the vanilla specialAttackContact burst it carried on its DamageEffect cleared.
        /// </summary>
        public static void Runner(GameObject go, string sheet)
        {
            if (go == null) return;
            Wear(go, sheet, "Run", loop: true);
            if (go.GetComponent<DepthHandler>() == null) go.AddComponent<DepthHandler>();   // sorts with the floor like other effects
            FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: R.Get<float>(go.GetComponent<Effect>(), "m_destroyAfterTime"),
                                canFlip: true, freeRotate: false);
            FxFactory.SetContacts(go, clearSpawnOnHit: true);
        }

        /// <summary>Spawn a visual at a point, facing like <paramref name="like"/> (null: unflipped).</summary>
        public static GameObject Pop(GameObject visual, Vector2 at, Transform like = null)
        {
            if (visual == null) return null;
            var go = SystemPool.Spawn(visual, new Vector3(at.x, at.y, 0f));
            if (go != null && like != null && like.lossyScale.x < 0f)
            {
                var s = go.transform.localScale;
                go.transform.localScale = new Vector3(-Mathf.Abs(s.x), s.y, s.z);
            }
            return go;
        }
    }

    /// <summary>Wax Slick: hero wax that catches fire burns in the item's own fire art (the monster wax keeps Vhorrul's).</summary>
    [HarmonyPatch(typeof(WaxPuddleFx), "Ignite")]
    static class Patch_HeroWaxIgnite
    {
        static bool Prefix(WaxPuddleFx __instance, DamageSource by)
        {
            if (__instance == null || !__instance.heroOwned || ItemPack2.HeroWaxFire == null) return true;
            try
            {
                if (R.Get<bool>(__instance, "m_ignited")) return false;
                R.Set(__instance, "m_ignited", true);
                var src = FxFactory.SourceOf(__instance.gameObject) ?? by;
                FxFactory.SpawnOwned(ItemPack2.HeroWaxFire, __instance.Pos, src);
                WaxPuddleFx.All.Remove(__instance);
                SystemPool.Despawn(__instance.gameObject);
                return false;
            }
            catch (Exception e) { Plugin.Log.LogWarning("Hero wax ignite: " + e.Message); return true; }
        }
    }

    /// <summary>
    /// Chain Spark (Kaurn shop item): each jump flashes Kaurn's monster hit spark (KaurnFx.HitFx) on the monster it leaves.
    /// While a chain spark handles its contact, that one spawn wears the item's own jump flash instead.
    /// </summary>
    [HarmonyPatch]
    static class Patch_ChainSparkJumpFlash
    {
        [ThreadStatic] static bool s_inChain;
        static MethodBase s_target;
        static bool Prepare()
        {
            s_target = AccessTools.Method(typeof(ChainSparkFx), "MsgOnAttackContact");
            return s_target != null;
        }
        static MethodBase TargetMethod() { return s_target; }
        static void Prefix() { s_inChain = true; }
        static void Finalizer() { s_inChain = false; }
        public static bool InChain { get { return s_inChain; } }
    }

    [HarmonyPatch(typeof(SystemPool), "Spawn", new[] { typeof(GameObject), typeof(Vector3) })]
    static class Patch_ChainSparkJumpFlashSwap
    {
        static void Prefix(ref GameObject prefab)
        {
            if (Patch_ChainSparkJumpFlash.InChain && ItemPack2.ChainJumpFlash != null && prefab != null && prefab == KaurnFx.HitFx)
                prefab = ItemPack2.ChainJumpFlash;
        }
    }

    /// <summary>On a follower token: hold its timed shot while no monster is near the hero (no shots into empty rooms).</summary>
    public class FollowerHoldFx : MonoBehaviour
    {
        static readonly FieldInfo s_timer = AccessTools.Field(typeof(Powerup), "m_activateTimer");
        public float range = 170f;
        Powerup m_pu;
        float m_scan;
        bool m_any;

        public void Reset() { m_scan = 0f; m_any = false; }
        void OnEnable() { Reset(); }

        void Update()
        {
            if (m_pu == null) m_pu = GetComponent<Powerup>();
            if (m_pu == null || s_timer == null) return;
            m_scan -= Time.deltaTime;
            if (m_scan <= 0f)
            {
                m_scan = 0.2f;
                var hero = ModUtil.Hero();
                m_any = hero != null && ItemFixes.NearestMonster(hero.transform.position, range) != null;
            }
            if (m_any) return;
            float t = (float)s_timer.GetValue(m_pu);
            if (t < 0.3f) s_timer.SetValue(m_pu, 0.3f);
        }
    }

    /// <summary>Steers an accelerating projectile at the nearest monster (re-picks a target 4 times a second).</summary>
    public class SeekMonsterFx : MonoBehaviour
    {
        public float range = 200f;
        ParticleMotion m_pm;
        GameObject m_target;
        Player m_targetPlayer;
        Collider m_targetBox;          // the target's hurtbox, looked up once per target (not every frame)
        float m_retarget;

        public void Reset() { m_target = null; m_targetPlayer = null; m_targetBox = null; m_retarget = 0f; }
        void OnEnable() { Reset(); }

        void Update()
        {
            if (m_pm == null) m_pm = GetComponent<ParticleMotion>();
            if (m_pm == null) return;
            Vector2 p = transform.position;
            if (m_target != null && !ItemFixes.LiveMonster(m_targetPlayer, ModUtil.Hero())) Reset();
            m_retarget -= Time.deltaTime;
            if (m_target == null && m_retarget <= 0f)
            {
                m_retarget = 0.25f;
                m_target = ItemFixes.NearestMonster(p, range);
                if (m_target != null) { m_targetPlayer = m_target.GetComponent<Player>(); m_targetBox = ItemFixes.Hurtbox(m_target); }
            }
            if (m_target == null) return;
            Vector2 aim = m_targetBox != null && m_targetBox.enabled ? (Vector2)m_targetBox.bounds.center : (Vector2)m_target.transform.position + new Vector2(0f, 8f);
            var d = aim - p;
            if (d.sqrMagnitude > 1f) m_pm.SetDirection(d.normalized);
        }
    }

    /// <summary>Remembers which DamageInfo Health.Damage is handling, so item code called from other patches can
    /// tell a status tick (poison, fire) from a real blow.</summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    [HarmonyPriority(Priority.First)]
    static class Patch_ItemDamageTag
    {
        static void Prefix(DamageInfo damage, out DamageInfo __state)
        {
            __state = ItemFixes.Incoming;
            ItemFixes.Incoming = damage;
        }

        // a finalizer (not a postfix) so a throw inside Health.Damage can never leave a stale tag behind
        static void Finalizer(DamageInfo __state) { ItemFixes.Incoming = __state; }
    }
}
