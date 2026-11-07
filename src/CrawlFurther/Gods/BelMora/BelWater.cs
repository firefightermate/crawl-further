using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>One pool of brine on the floor: a small one (<see cref="BrineFx"/>) or a wide tide pool
    /// (<see cref="BelTidePool"/>), as an ellipse.</summary>
    public struct BelPool
    {
        public Component Source;
        public Vector2 Pos;
        public float Rx, Ry;
        public bool Tide;

        public bool Contains(Vector2 p)
        {
            var d = p - Pos;
            return (d.x * d.x) / (Rx * Rx) + (d.y * d.y) / (Ry * Ry) <= 1f;
        }

        /// <summary>Where a line from <paramref name="from"/> (inside the pool) along <paramref name="dir"/> leaves it.</summary>
        public Vector2 Exit(Vector2 from, Vector2 dir)
        {
            var p = from;
            for (int i = 0; i < 80 && Contains(p); i++) p += dir;
            return p;
        }

        /// <summary>Slide the pool (its art, zone and heal area move with it).</summary>
        public void Move(Vector2 delta)
        {
            if (Source == null) return;
            var t = Source.transform;
            t.position = new Vector3(t.position.x + delta.x, t.position.y + delta.y, t.position.z);
        }
    }

    /// <summary>Brine queries and the small helpers Bel'Mora's quirks share.</summary>
    public static class BelWater
    {
        /// <summary>Half-sizes of a small brine pool's water (its 23 x 8 zone).</summary>
        public const float SmallRx = 11.5f, SmallRy = 4f;

        /// <summary>Every live pool of brine.</summary>
        public static List<BelPool> Pools()
        {
            var list = new List<BelPool>();
            foreach (var b in BrineFx.All)
                if (b != null && b.isActiveAndEnabled) list.Add(new BelPool { Source = b, Pos = b.Pos, Rx = SmallRx, Ry = SmallRy });
            foreach (var t in BelTidePool.All)
                if (t != null && t.Live) list.Add(new BelPool { Source = t, Pos = t.Pos, Rx = BelTidePool.Rx, Ry = BelTidePool.Ry, Tide = true });
            return list;
        }

        /// <summary>Pools whose centre lies within <paramref name="range"/> px of <paramref name="p"/>, nearest first.</summary>
        public static List<BelPool> Near(Vector2 p, float range)
        {
            var list = Pools();
            list.RemoveAll(x => (x.Pos - p).sqrMagnitude > range * range);
            list.Sort((a, b) => (a.Pos - p).sqrMagnitude.CompareTo((b.Pos - p).sqrMagnitude));
            return list;
        }

        /// <summary>True if <paramref name="p"/> stands in brine.</summary>
        public static bool InBrine(Vector2 p)
        {
            foreach (var x in Pools()) if (x.Contains(p)) return true;
            return false;
        }

        /// <summary>The pool <paramref name="p"/> stands in, if any.</summary>
        public static bool PoolAt(Vector2 p, out BelPool pool)
        {
            foreach (var x in Pools()) if (x.Contains(p)) { pool = x; return true; }
            pool = default(BelPool);
            return false;
        }

        /// <summary>The nearest pool within <paramref name="range"/> px (false if none).</summary>
        public static bool Nearest(Vector2 p, float range, out BelPool pool)
        {
            var list = Near(p, range);
            pool = list.Count > 0 ? list[0] : default(BelPool);
            return list.Count > 0;
        }

        /// <summary>Slide <paramref name="who"/> <paramref name="px"/> px toward <paramref name="toward"/> over
        /// <paramref name="seconds"/> (never through a wall), run on <paramref name="host"/>.</summary>
        public static void Drag(MonoBehaviour host, GameObject who, Vector2 toward, float px, float seconds)
        {
            if (host == null || who == null || !host.isActiveAndEnabled) return;
            host.StartCoroutine(DragRun(who, toward, px, seconds));
        }

        static IEnumerator DragRun(GameObject who, Vector2 toward, float px, float seconds)
        {
            float t = 0f, moved = 0f;
            while (t < seconds && moved < px && who != null && who.activeInHierarchy)
            {
                t += Time.deltaTime;
                Vector2 at = who.transform.position;
                var d = toward - at;
                if (d.sqrMagnitude < 36f) yield break;
                float step = Mathf.Min(px * Time.deltaTime / seconds, px - moved);
                var to = ModUtil.SafePoint(at, at + d.normalized * step, 3f);
                ModUtil.Teleport(who, to);
                moved += step;
                yield return null;
            }
        }

        /// <summary>The hero's player component (for statuses), or null.</summary>
        public static Player HeroPlayer() { var h = ModUtil.Hero(); return h != null ? h.GetComponent<Player>() : null; }
    }

    /// <summary>
    /// A row of little sprites laid along a line every frame (a chain, a rope, trailing tentacles, foam arrows):
    /// <see cref="Lay"/> places them, reusing the ones it already has, and <see cref="Clear"/> takes them away.
    /// </summary>
    public class BelLine
    {
        readonly List<GameObject> m_links = new List<GameObject>();

        public void Lay(GameObject template, Vector2 a, Vector2 b, float spacing, bool rotate = false, float sag = 0f)
        {
            if (template == null) { Clear(); return; }
            var d = b - a;
            int n = Mathf.Clamp(Mathf.FloorToInt(d.magnitude / Mathf.Max(1f, spacing)), 0, 40);
            while (m_links.Count < n)
            {
                var g = SystemPool.Spawn(template, a);
                if (g == null) break;
                m_links.Add(g);
            }
            while (m_links.Count > n) { Drop(m_links[m_links.Count - 1]); m_links.RemoveAt(m_links.Count - 1); }
            var rot = rotate ? Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg) : Quaternion.identity;
            for (int i = 0; i < m_links.Count; i++)
            {
                var g = m_links[i];
                if (g == null) continue;
                float t = (i + 0.5f) / n;
                var p = a + d * t + new Vector2(0f, -sag * 4f * t * (1f - t));
                g.transform.position = new Vector3(p.x, p.y, g.transform.position.z);
                g.transform.rotation = rot;
            }
        }

        public void Clear()
        {
            foreach (var g in m_links) Drop(g);
            m_links.Clear();
        }

        static void Drop(GameObject g)
        {
            if (g != null && g.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(g);
        }
    }

    /// <summary>
    /// The hero's attacks in flight, so things on the floor that are not monsters (tide eggs, crawling starfish arms)
    /// can be struck: <see cref="Near"/> is true while a live hero hitbox overlaps a point.
    /// </summary>
    public static class HeroStrikes
    {
        static readonly List<DamageEffect> s_live = new List<DamageEffect>();
        static bool s_on;

        public static void Install()
        {
            if (s_on) return;
            s_on = true;
            MonsterEvents.AttackSpawned += (owner, fx, template) =>
            {
                if (owner == null || fx == null || owner.gameObject != ModUtil.Hero()) return;
                var de = fx.GetComponent<DamageEffect>();
                if (de != null && !s_live.Contains(de)) s_live.Add(de);
                HeroSlime.OnHeroAttack(fx);
            };
        }

        /// <summary>True if a live hero hitbox lies within <paramref name="r"/> px of <paramref name="p"/>.</summary>
        public static bool Near(Vector2 p, float r)
        {
            for (int i = s_live.Count - 1; i >= 0; i--)
            {
                var de = s_live[i];
                if (de == null || !de.isActiveAndEnabled) { s_live.RemoveAt(i); continue; }
                if (!R.Get<bool>(de, "m_damageOn")) continue;
                var c = de.GetComponent<Collider>();
                if (c == null) continue;
                var b = c.bounds;
                if (b.SqrDistance(new Vector3(p.x, p.y, b.center.z)) <= r * r) return true;
            }
            return false;
        }
    }

    /// <summary>
    /// Slime Spew's coat on the hero: for its length his shots fly at half speed and his swings reach two thirds as far.
    /// Tell: slime dripping down him (FxBelSlimeCoat).
    /// </summary>
    public static class HeroSlime
    {
        public const float Length = 3f, ShotSpeed = 0.5f, Reach = 2f / 3f;
        static float s_until;

        public static bool Coated { get { return Time.time < s_until; } }

        public static void Coat()
        {
            var hero = ModUtil.Hero();
            if (hero == null) return;
            s_until = Time.time + Length;
            if (BelMoraFx.SlimeCoat != null) ModInd.Set(hero, BelMoraFx.SlimeCoat, true, Length);
        }

        internal static void OnHeroAttack(GameObject fx)
        {
            if (!Coated) return;
            var hero = ModUtil.Hero();
            var pm = fx.GetComponent<ParticleMotion>();
            if (pm != null && pm.enabled)
            {
                var s = fx.GetComponent<SlimedShot>() ?? fx.AddComponent<SlimedShot>();
                s.Begin(ShotSpeed);
                return;
            }
            // a swing: smaller, and drawn in toward the hero (the pool resets the scale on reuse)
            fx.transform.localScale = Vector3.Scale(fx.transform.localScale, new Vector3(Reach, Reach, 1f));
            if (hero != null && fx.transform.parent == null)
            {
                Vector2 h = hero.transform.position, p = fx.transform.position;
                var q = h + (p - h) * Reach;
                fx.transform.position = new Vector3(q.x, q.y, fx.transform.position.z);
            }
            else if (fx.transform.parent != null) fx.transform.localPosition = Vector3.Scale(fx.transform.localPosition, new Vector3(Reach, Reach, 1f));
        }
    }

    /// <summary>Slows a hero shot fired through slime: each frame it gives back part of the distance it flew.</summary>
    public class SlimedShot : MonoBehaviour
    {
        float m_k = 1f;
        bool m_on;
        Vector3 m_last;

        public void Begin(float k) { m_k = k; m_on = true; m_last = transform.position; }
        void OnDisable() { m_on = false; }

        void LateUpdate()
        {
            if (!m_on) return;
            var p = transform.position;
            var q = m_last + (p - m_last) * m_k;
            transform.position = new Vector3(q.x, q.y, p.z);
            m_last = transform.position;
        }
    }
}
