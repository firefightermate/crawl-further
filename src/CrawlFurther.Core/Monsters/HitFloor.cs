using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Util;

    /// <summary>
    /// Hit sizes by tier. A tier 2 or 3 monster's strikes (melee boxes and ground slams, not projectiles or lingering
    /// zones) are never smaller than the game's own monsters of that rank: its tier 3 swipes run about 22 x 19, its tier 4
    /// swipes 27-30 x 20-25 and its slam shockwaves 36-75 x 18-33. Every mod strike is also turned from a capsule into a
    /// deep box (<see cref="Strike.Boxify"/>). Runs on each mod monster after its kit; templates are shared, so a template
    /// keeps the largest size any of its users needs.
    /// </summary>
    public static class HitFloor
    {
        /// <summary>Least width x height of a body strike (Damage layer), by tier (index 1..3).</summary>
        public static readonly Vector2[] Body = { Vector2.zero, Vector2.zero, new Vector2(24f, 18f), new Vector2(30f, 22f) };
        /// <summary>Least height of a long thrust (at least twice as wide as tall), by tier.</summary>
        public static readonly float[] Thrust = { 0f, 0f, 14f, 16f };
        /// <summary>Least width x height of a ground strike (DamageBase layer), by tier.</summary>
        public static readonly Vector2[] Ground = { Vector2.zero, Vector2.zero, new Vector2(44f, 18f), new Vector2(56f, 24f) };
        /// <summary>A strike that shows its own art grows at most this much past its authored size, so the hit stays
        /// where the art is (the art itself is sized to the tier).</summary>
        public const float ArtGrowth = 1.15f;

        const int LayerDamage = 13, LayerDamageBase = 19;
        static readonly Dictionary<GameObject, Vector2> s_done = new Dictionary<GameObject, Vector2>();
        static readonly HashSet<GameObject> s_boxed = new HashSet<GameObject>();
        static readonly Dictionary<GameObject, Vector2> s_authored = new Dictionary<GameObject, Vector2>();

        /// <summary>Box every strike and raise it to the floor for <paramref name="tier"/>.</summary>
        public static void Apply(Player p, int tier)
        {
            var list = Kit.Effects(p);
            if (list == null) return;
            int grown = 0;
            foreach (var d in list)
            {
                var t = d != null ? d.m_object : null;
                if (t == null || !t.name.StartsWith("Mod") || !IsStrike(t)) continue;
                if (s_boxed.Add(t)) Strike.Boxify(t);
                if (tier >= 2 && Raise(t, tier)) grown++;
            }
            if (grown > 0) FurtherCore.Log.LogInfo(p.gameObject.name + ": " + grown + " strikes raised to the tier " + tier + " size");
        }

        /// <summary>A hit that lands once: it deals damage, does not fly and does not tick.</summary>
        public static bool IsStrike(GameObject t)
        {
            var de = t.GetComponent<DamageEffect>();
            if (de == null || R.Get<float>(de, "m_damageRate") > 0f) return false;
            foreach (var m in t.GetComponents<ParticleMotion>()) if (m.enabled) return false;
            return t.layer == LayerDamage || t.layer == LayerDamageBase;
        }

        static bool Visible(GameObject t)
        {
            foreach (var r in t.GetComponentsInChildren<Renderer>(true))
                if (r.enabled) { var sp = r.GetComponent<exSprite>(); if (sp == null || sp.enabled) return true; }
            return false;
        }

        static bool Raise(GameObject t, int tier)
        {
            var boxes = t.GetComponents<BoxCollider>();
            if (boxes.Length != 1) return false;
            var b = boxes[0];
            var s = t.transform.localScale;
            float sx = Mathf.Max(0.01f, Mathf.Abs(s.x)), sy = Mathf.Max(0.01f, Mathf.Abs(s.y));
            float w = b.size.x * sx, h = b.size.y * sy;   // world pixels
            Vector2 authored;
            if (!s_authored.TryGetValue(t, out authored)) { authored = new Vector2(w, h); s_authored[t] = authored; }
            bool ground = t.layer == LayerDamageBase;
            Vector2 min = ground ? Ground[Mathf.Clamp(tier, 0, 3)] : Body[Mathf.Clamp(tier, 0, 3)];
            if (!ground && authored.x >= authored.y * 2f) min.y = Thrust[Mathf.Clamp(tier, 0, 3)];
            if (Visible(t)) min = Vector2.Min(min, authored * ArtGrowth);
            Vector2 prev;
            if (s_done.TryGetValue(t, out prev)) min = Vector2.Max(min, prev);
            float nw = Mathf.Max(w, min.x), nh = Mathf.Max(h, min.y);
            s_done[t] = new Vector2(nw, nh);
            if (nw <= w + 0.01f && nh <= h + 0.01f) return false;
            // body strikes grow mostly forward (the face side); ground strikes stay centred on where they land
            float shift = ground ? 0f : (nw - w) * 0.25f / sx;
            b.size = new Vector3(nw / sx, nh / sy, Mathf.Max(b.size.z, Strike.BoxDepth));
            b.center = new Vector3(b.center.x + shift, b.center.y, b.center.z);
            return true;
        }
    }
}
