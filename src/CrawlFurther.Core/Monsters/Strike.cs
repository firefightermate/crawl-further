using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// Attack placement for kits: where effects spawn relative to the art, collider sizes, ground art origins.
    ///
    /// Three engine facts kits have to respect:
    /// 1. A Node-spawned effect lands at transform + m_attackSpawnNode + offset. The node is inherited from the
    ///    vanilla base (gnome y 4, orc y 10, priestess y 14...), so an offset meant as "relative to the feet" is off by
    ///    the base's node. <see cref="Feet"/> moves the node to a chosen launch height for this art and rewrites the
    ///    kit's own slots so their offsets really are feet-relative.
    ///    The node also sets the bot's aim origin (it aims from node height at the hero's chest, y 8), so a
    ///    projectile only flies true when it is released near the node height.
    /// 2. SystemPool resets localScale to (1,1,1) when it re-uses a pooled instance, so a scale set on a template
    ///    only applied to its first spawn. <see cref="KeepScale"/> restores it on every spawn; invisible hitboxes get
    ///    their size baked into the collider instead (<see cref="Collider"/>).
    /// 3. DamageBase-layer effects (ground rings, puddles, lobbed globs) only touch the hero's feet capsule (y -1..2
    ///    around the hero's position); Damage-layer effects touch the hurtbox (8 x 18 above the feet).
    /// </summary>
    public static class Strike
    {
        /// <summary>The number of effect slots so far: pass it to <see cref="Feet"/> to fix only the slots added after it.</summary>
        public static int Mark(Player p) { return Kit.Effects(p).Count; }

        static MinMaxRange Shift(MinMaxRange r, float d)
        {
            if (r == null) return new MinMaxRange(d);
            return r.m_hasMax ? new MinMaxRange(r.m_min + d, r.m_max + d) : new MinMaxRange(r.m_min + d);
        }

        /// <summary>
        /// Put the attack node <paramref name="nodeY"/> px above the art's feet and make every slot added since
        /// <paramref name="from"/> feet-relative (Node slots) / transform-relative-to-feet (Position slots).
        /// </summary>
        public static void Feet(Player p, int from, float nodeY)
        {
            var spr = p.GetComponent<exSprite>();
            float fx = spr != null ? spr.offset.x : 0f, fy = spr != null ? spr.offset.y + 2f : 0f;   // art feet = cell bottom + 2
            var oldNode = R.Get<Vector2>(p, "m_attackSpawnNode");
            var node = new Vector2(fx, fy + nodeY);
            R.Set(p, "m_attackSpawnNode", node);
            // the base's own death drops (loot) keep their old world position
            var deaths = R.Get<DamageEffectData[]>(p, "m_spawnOnDeath");
            if (deaths != null)
                foreach (var d in deaths)
                    if (d != null && d.m_spawnPoint == DamageEffectData.eSpawnPoint.Node && (d.m_object == null || !d.m_object.name.StartsWith("Mod")))
                        d.m_offsetY = Shift(d.m_offsetY, oldNode.y - node.y);
            var list = Kit.Effects(p);
            for (int i = Mathf.Max(0, from); i < list.Count; i++)
            {
                var d = list[i];
                if (d == null) continue;
                if (d.m_spawnPoint == DamageEffectData.eSpawnPoint.Node) d.m_offsetY = Shift(d.m_offsetY, -nodeY);
                else if (d.m_spawnPoint == DamageEffectData.eSpawnPoint.Position) d.m_offsetY = Shift(d.m_offsetY, fy);
            }
        }

        /// <summary>Death spawns go through the node too: put them on the feet (call from customize, after the kit).</summary>
        public static void DeathAtFeet(Player p)
        {
            var arr = R.Get<DamageEffectData[]>(p, "m_spawnOnDeath");
            if (arr == null) return;
            var spr = p.GetComponent<exSprite>();
            float fy = spr != null ? spr.offset.y + 2f : 0f;
            var node = R.Get<Vector2>(p, "m_attackSpawnNode");
            foreach (var d in arr)
            {
                if (d == null || d.m_object == null || !d.m_object.name.StartsWith("Mod")) continue;
                if (d.m_spawnPoint != DamageEffectData.eSpawnPoint.Node) continue;
                if (s_deathFixed.Contains(d)) continue;
                s_deathFixed.Add(d);
                d.m_offsetY = Shift(d.m_offsetY, fy - node.y);
            }
        }
        static readonly HashSet<DamageEffectData> s_deathFixed = new HashSet<DamageEffectData>();

        /// <summary>Size every collider on a template, in its local (pre-scale) pixels.</summary>
        public static void Collider(GameObject go, float w, float h, float cx = 0f, float cy = 0f)
        {
            if (go == null) return;
            foreach (var b in go.GetComponents<BoxCollider>())
            {
                b.size = new Vector3(w, h, b.size.z);
                b.center = new Vector3(cx, cy, b.center.z);
            }
            foreach (var c in go.GetComponents<CapsuleCollider>())
            {
                if (w >= h) { c.direction = 0; c.height = w; c.radius = h * 0.5f; }
                else { c.direction = 1; c.height = h; c.radius = w * 0.5f; }
                c.center = new Vector3(cx, cy, c.center.z);
            }
            foreach (var s in go.GetComponents<SphereCollider>())
            {
                s.radius = Mathf.Max(w, h) * 0.5f;
                s.center = new Vector3(cx, cy, s.center.z);
            }
        }

        /// <summary>An invisible hitbox of an exact size (no template scale, which the pool would drop).</summary>
        public static void HitBox(GameObject go, float w, float h, float cx = 0f, float cy = 0f)
        {
            if (go == null) return;
            go.transform.localScale = Vector3.one;
            Collider(go, w, h, cx, cy);
        }

        /// <summary>
        /// Draw a mod sheet so that its pixel (gx, gy) (cell coords, y down) sits on the effect's origin.
        /// Used to put ground rings and puddles where their collider is.
        /// </summary>
        public static void ArtAt(GameObject go, string sheet, int gx, int gy)
        {
            if (go == null) return;
            var sh = SpriteSheets.Get(sheet);
            var spr = go.GetComponent<exSprite>();
            if (sh == null || spr == null) return;
            spr.anchor = exPlane.Anchor.BotCenter;
            spr.offset = new Vector2(sh.manifest.cellW * 0.5f - gx - 0.5f, gy + 1f - sh.manifest.cellH);
        }

        /// <summary>A ground effect: art origin and a w x h footprint both centred on the spawn point.</summary>
        public static void Ground(GameObject go, string sheet, int gx, int gy, float w, float h)
        {
            ArtAt(go, sheet, gx, gy);
            Collider(go, w, h, 0f, 0f);
        }

        /// <summary>
        /// OrcSwipe2's clip fires "AnimDamageOnNOT" (a disabled event), so a straight clone never deals damage
        /// (the vanilla orc pairs it with an invisible hitbox). Switch damage on at spawn; the clip still turns it off.
        /// </summary>
        public static void ArmSwipe2(GameObject go)
        {
            var d = go != null ? go.GetComponent<DamageEffect>() : null;
            if (d != null) R.Set(d, "m_collisionOnAtStart", true);
        }

        static readonly HashSet<GameObject> s_kept = new HashSet<GameObject>();

        /// <summary>Re-apply a template's own scale on every spawn (the pool resets re-used instances to 1).</summary>
        public static void KeepScale(GameObject tmpl)
        {
            if (tmpl == null || s_kept.Contains(tmpl)) return;
            s_kept.Add(tmpl);
            Action<GameObject> prev;
            FxFactory.OnSpawn.TryGetValue(tmpl, out prev);
            FxFactory.OnSpawn[tmpl] = i =>
            {
                if (prev != null) prev(i);
                if (tmpl == null || i == null) return;
                var s = tmpl.transform.localScale;
                var c = i.transform.localScale;
                i.transform.localScale = new Vector3((c.x < 0f ? -1f : 1f) * Mathf.Abs(s.x), Mathf.Abs(s.y), s.z == 0f ? 1f : Mathf.Abs(s.z));
            };
        }

        /// <summary>Apply <see cref="KeepScale"/> to every scaled template built so far (call once your effects are built).</summary>
        public static void KeepAllScales()
        {
            int n = 0;
            foreach (var kv in FxFactory.Templates)
            {
                var t = kv.Value;
                if (t == null || s_kept.Contains(t)) continue;
                var s = t.transform.localScale;
                if (Mathf.Abs(s.x - 1f) < 0.001f && Mathf.Abs(s.y - 1f) < 0.001f) continue;
                KeepScale(t);
                n++;
            }
            if (n > 0) FurtherCore.Log.LogInfo("Strike: kept template scale on " + n + " effects");
        }
    }

    /// <summary>
    /// Attacks.SpawnEffect only adds a slot's offset for Node spawns (and for attached effects, which follow the owner at
    /// that offset). A non-attached Position or ClosestEnemy slot always lands exactly on the owner or the hero, so every
    /// offset a kit gives those slots (and the feet shift <see cref="Strike.Feet"/> writes into Position slots) would be
    /// dropped: a ring of four rods would all rise on one spot. Apply the offset here, the way the game computes it for
    /// Node slots, for mod monsters only (runs before the echo postfix so echoes copy the spot).
    /// </summary>
    [HarmonyLib.HarmonyPatch(typeof(Attacks), "SpawnEffect", new[] { typeof(DamageEffectData), typeof(int) })]
    [HarmonyLib.HarmonyPriority(HarmonyLib.Priority.High)]
    static class Patch_StrikeSpawnOffset
    {
        static readonly System.Reflection.MethodInfo s_calc = HarmonyLib.AccessTools.Method(typeof(Attacks), "CalculateEffectOffset");
        static readonly HarmonyLib.AccessTools.FieldRef<Attacks, IAttacksOwner> s_owner =
            HarmonyLib.AccessTools.FieldRefAccess<Attacks, IAttacksOwner>("m_owner");
        static bool s_logged;

        static void Postfix(Attacks __instance, DamageEffectData effectData, int effectId, GameObject __result)
        {
            try
            {
                if (__result == null || effectData == null || effectData.m_attach || s_calc == null) return;
                var sp = effectData.m_spawnPoint;
                if (sp != DamageEffectData.eSpawnPoint.Position && sp != DamageEffectData.eSpawnPoint.ClosestEnemy) return;
                var owner = s_owner(__instance);
                var c = owner as Component;
                if (c == null || !(owner is Player) || !c.gameObject.name.StartsWith("Mod")) return;
                var off = (Vector2)s_calc.Invoke(__instance, new object[] { effectData, effectId, owner.GetFaceRotation(effectId), owner.GetFlipped(effectId) });
                if (off.sqrMagnitude < 0.0001f) return;
                var t = __result.transform;
                Vector2 from = t.position;
                var to = ModUtil.SafePoint(from, from + off, 2f);
                t.position = new Vector3(to.x, to.y, t.position.z);
            }
            catch (Exception e)
            {
                if (s_logged) return;
                s_logged = true;
                FurtherCore.Log.LogError("Spawn offset fix failed (further errors muted): " + e);
            }
        }
    }
}
