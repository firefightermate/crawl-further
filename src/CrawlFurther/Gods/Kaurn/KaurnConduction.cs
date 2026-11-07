using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Util;

    /// <summary>
    /// Kaurn's perk, Lightning Arcs. Kaurn monsters and iron posts within 70 px of each other (clear line) are joined by a
    /// crackling arc (a Coil Wisp's reach 110 px). Crossing an arc costs the hero 0.3 health (0.6 from a red-hot rod), at
    /// most once every 0.5 s; the last tenth at either end is safe. Any other living monster near Kaurn iron conducts too.
    /// A wired hero (<see cref="Wire"/>) is an arc end himself. At most 6 arcs, nearest first; rebuilt 10 times a second,
    /// drawn every frame. Other mechanics read the network through <see cref="Links"/>.
    /// </summary>
    public class KaurnConduction : MonoBehaviour
    {
        public const float Range = 70f, TickTime = 0.5f, TickDamage = 0.3f, HotDamage = 0.6f, HitDist = 5.5f, SegLen = 12f, ActiveRadius = 260f;
        public const int MaxLinks = 6, MaxSegs = 10, MaxNodes = 16, MaxHeroLinks = 2;

        /// <summary>One end of an arc: a Kaurn monster, an iron post, another monster, or a wired hero.</summary>
        public class End
        {
            public Component c;
            public float h, range;
            public KaurnUnit unit;
            public KrnNode node;
            public Health other;
            public bool hero;

            public Vector2 Feet { get { return unit != null ? unit.FeetPos : (Vector2)c.transform.position; } }
            public Vector2 Top { get { return Feet + new Vector2(0f, h); } }

            public bool Valid
            {
                get
                {
                    if (c == null || !c.gameObject.activeInHierarchy) return false;
                    if (other != null) return other.IsAlive();
                    if (hero) return Wired;
                    return unit == null || unit.Alive;
                }
            }

            public DamageSource Source() { return unit != null ? unit.OwnSource() : node != null ? node.Source() : null; }
        }

        /// <summary>An arc between two ends.</summary>
        public class Link
        {
            public End a, b;
            /// <summary>An arc from a red-hot rod (double damage).</summary>
            public bool Hot { get { return (a.node != null && a.node.Hot) || (b.node != null && b.node.Hot); } }
            public bool ToHero { get { return a.hero || b.hero; } }
            public bool Has(Component c) { return a.c == c || b.c == c; }
            public End Other(Component c) { return a.c == c ? b : a; }
            public End Kaurn { get { return a.unit != null || a.node != null ? a : b; } }
        }

        static KaurnConduction s_inst;
        static float s_wiredUntil, s_nextHurt, s_nextWired;
        readonly List<Link> m_links = new List<Link>();
        readonly List<GameObject> m_segs = new List<GameObject>();
        float m_rescan;
        Player[] m_players = new Player[0];
        float m_playerScanAt = -1f;

        /// <summary>The arcs this frame (read only).</summary>
        public static List<Link> Links { get { return s_inst != null ? s_inst.m_links : s_empty; } }
        static readonly List<Link> s_empty = new List<Link>();

        /// <summary>True while the hero is wired (Wire Gremlin): an arc end himself.</summary>
        public static bool Wired { get { return Time.time < s_wiredUntil; } }

        /// <summary>Wire the hero for <paramref name="seconds"/>.</summary>
        public static void Wire(float seconds)
        {
            Ensure();
            s_wiredUntil = Mathf.Max(s_wiredUntil, Time.time + seconds);
            var hero = ModUtil.Hero();
            if (hero != null && KaurnFx.WiredInd != null) CrawlFurther.Monsters.ModInd.Set(hero, KaurnFx.WiredInd, true, seconds);
            s_inst.m_rescan = 0f;
        }

        /// <summary>True if <paramref name="c"/> has an arc this frame.</summary>
        public static bool Linked(Component c)
        {
            foreach (var l in Links) if (l.Has(c)) return true;
            return false;
        }

        /// <summary>The arcs joined to <paramref name="c"/> this frame.</summary>
        public static List<Link> LinksOf(Component c)
        {
            var o = new List<Link>();
            foreach (var l in Links) if (l.Has(c)) o.Add(l);
            return o;
        }

        /// <summary>
        /// Hurt the hero by an arc (or anything riding one), sharing the arcs' 0.5 s guard so two arcs crossed together
        /// don't both land. Returns true if the hit was dealt.
        /// </summary>
        public static bool HurtHero(float damage, DamageSource src, Vector2 from)
        {
            if (Time.time < s_nextHurt) return false;
            var hero = ModUtil.Hero();
            var h = hero != null ? hero.GetComponent<Health>() : null;
            if (h == null || !h.IsAlive()) return false;
            Vector2 hp = hero.transform.position;
            var dir = hp - from;
            h.Damage(new DamageInfo(damage, 0f, 0f, dir.sqrMagnitude > 0.01f ? dir.normalized : Vector2.right, src), false);
            if (KaurnFx.HitFx != null) SystemPool.Spawn(KaurnFx.HitFx, hp + new Vector2(0f, 7f));
            s_nextHurt = Time.time + TickTime;
            return true;
        }

        /// <summary>Chest height of a non-Kaurn monster for the arc end: ~60% of its hurtbox top, 6-20 px.</summary>
        static float OtherHeight(Player p)
        {
            var hz = p.transform.Find("HitZone");
            var bc = hz != null ? hz.GetComponent<BoxCollider>() : null;
            float top = bc != null ? (bc.center.y + bc.size.y * 0.5f) : 14f;
            return Mathf.Clamp(top * 0.6f, 6f, 20f);
        }

        public static void Ensure()
        {
            if (s_inst != null) return;
            var go = new GameObject("CrawlMod_KaurnConduction");
            DontDestroyOnLoad(go);
            s_inst = go.AddComponent<KaurnConduction>();
        }

        void Rescan()
        {
            m_links.Clear();
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 hp = hero.transform.position;
            var ends = new List<End>();
            foreach (var u in KaurnUnit.All)
                if (u != null && u.Alive && (u.FeetPos - hp).sqrMagnitude < ActiveRadius * ActiveRadius)
                    ends.Add(new End { c = u, h = u.height, unit = u, range = u.linkRange });
            foreach (var n in KrnNode.All)
                if (n != null && n.gameObject.activeInHierarchy && n.Conducts && ((Vector2)n.transform.position - hp).sqrMagnitude < ActiveRadius * ActiveRadius)
                    ends.Add(new End { c = n, h = n.height, node = n, range = Range });
            if (ends.Count == 0) return;
            if (Time.time - m_playerScanAt >= 0.25f || Time.time < m_playerScanAt) { m_players = FindObjectsOfType<Player>(); m_playerScanAt = Time.time; }
            for (int i = 0; i < m_players.Length; i++)
            {
                var o = m_players[i];
                if (o == null || o.gameObject == hero || o.GetComponent<KaurnUnit>() != null) continue;
                if (((Vector2)o.transform.position - hp).sqrMagnitude >= ActiveRadius * ActiveRadius) continue;
                if (ModUtil.IsGhost(o)) continue;
                var h = o.GetComponent<Health>();
                if (h == null || !h.IsAlive()) continue;
                ends.Add(new End { c = o, h = OtherHeight(o), other = h, range = Range });
            }
            if (ends.Count > MaxNodes) ends.Sort((x, y) => (x.Feet - hp).sqrMagnitude.CompareTo((y.Feet - hp).sqrMagnitude));
            int count = Mathf.Min(ends.Count, MaxNodes);
            var pairs = new List<KeyValuePair<float, Link>>();
            for (int i = 0; i < count; i++)
                for (int j = i + 1; j < count; j++)
                {
                    if (ends[i].other != null && ends[j].other != null) continue;   // an arc always starts at Kaurn
                    float reach = Mathf.Max(ends[i].range, ends[j].range);
                    float d2 = (ends[i].Feet - ends[j].Feet).sqrMagnitude;
                    if (d2 > reach * reach || d2 < 16f) continue;
                    pairs.Add(new KeyValuePair<float, Link>(d2, new Link { a = ends[i], b = ends[j] }));
                }
            pairs.Sort((x, y) => x.Key.CompareTo(y.Key));
            foreach (var kv in pairs)
            {
                if (m_links.Count >= MaxLinks) break;
                if (!ModUtil.Clear(kv.Value.a.Feet, kv.Value.b.Feet)) continue;
                m_links.Add(kv.Value);
            }
            if (!Wired) return;
            // a wired hero conducts: arcs reach him from Kaurn iron within 70 px
            var he = new End { c = hero.transform, h = 8f, hero = true, range = Range };
            var near = new List<KeyValuePair<float, End>>();
            for (int i = 0; i < count; i++)
            {
                if (ends[i].other != null) continue;
                float d2 = (ends[i].Feet - hp).sqrMagnitude;
                if (d2 <= Range * Range && d2 > 16f && ModUtil.Clear(ends[i].Feet, hp)) near.Add(new KeyValuePair<float, End>(d2, ends[i]));
            }
            near.Sort((x, y) => x.Key.CompareTo(y.Key));
            for (int i = 0; i < near.Count && i < MaxHeroLinks; i++) m_links.Add(new Link { a = near[i].Value, b = he });
        }

        void Update()
        {
            m_rescan -= Time.deltaTime;
            if (m_rescan <= 0f) { m_rescan = 0.1f; Rescan(); }
            m_links.RemoveAll(l => !l.a.Valid || !l.b.Valid);
            Draw();
            Hurt();
        }

        GameObject Seg(int i, GameObject tmpl)
        {
            while (m_segs.Count <= i) m_segs.Add(null);
            var s = m_segs[i];
            // a slot keeps its segment unless the arc it draws changed kind (normal, thin, hot)
            if (s != null && s.activeInHierarchy && ModUtil.PrefabName(s) != tmpl.name) { SystemPool.Despawn(s); s = null; }
            if (s == null || !s.activeInHierarchy)
            {
                s = SystemPool.Spawn(tmpl, transform.position);
                m_segs[i] = s;
            }
            return s;
        }

        void Draw()
        {
            int used = 0;
            foreach (var l in m_links)
            {
                Vector2 a = l.a.Top, b = l.b.Top;
                var d = b - a;
                float len = d.magnitude;
                if (len < 1f) continue;
                var tmpl = l.Hot ? KaurnFx.ArcHot : len > Range + 2f ? KaurnFx.ArcThin : KaurnFx.ArcSeg;
                if (tmpl == null) tmpl = KaurnFx.ArcSeg;
                if (tmpl == null) continue;
                int n = Mathf.Clamp(Mathf.CeilToInt(len / SegLen), 1, MaxSegs);
                float ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
                float sx = len / n / SegLen;
                for (int k = 0; k < n; k++)
                {
                    var s = Seg(used++, tmpl);
                    if (s == null) continue;
                    var p = a + d * ((k + 0.5f) / n);
                    s.transform.position = new Vector3(p.x, p.y, s.transform.position.z);
                    s.transform.rotation = Quaternion.Euler(0f, 0f, ang);
                    s.transform.localScale = new Vector3(sx, (k % 2 == 0) ? 1f : -1f, 1f);
                }
            }
            for (int i = m_segs.Count - 1; i >= used; i--)
            {
                if (m_segs[i] != null && m_segs[i].activeInHierarchy) SystemPool.Despawn(m_segs[i]);
                m_segs.RemoveAt(i);
            }
        }

        void Hurt()
        {
            if (m_links.Count == 0) return;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 hp = hero.transform.position;
            // arcs into a wired hero: each one hits him every 0.5 s
            if (Wired && Time.time >= s_nextWired)
            {
                var h = hero.GetComponent<Health>();
                int n = 0;
                foreach (var l in m_links)
                {
                    if (!l.ToHero || h == null || !h.IsAlive()) continue;
                    var k = l.Kaurn;
                    var dir = hp - k.Feet;
                    h.Damage(new DamageInfo(TickDamage, 0f, 0f, dir.sqrMagnitude > 0.01f ? dir.normalized : Vector2.right, k.Source()), false);
                    n++;
                }
                if (n > 0)
                {
                    s_nextWired = Time.time + TickTime;
                    if (KaurnFx.HitFx != null) SystemPool.Spawn(KaurnFx.HitFx, hp + new Vector2(0f, 7f));
                }
            }
            if (Time.time < s_nextHurt) return;
            foreach (var l in m_links)
            {
                if (l.ToHero) continue;
                float t;
                // the arc runs between the two ends; standing right next to an end does not count
                if (KaurnFx.SegDist(hp, l.a.Feet, l.b.Feet, out t) > HitDist || t < 0.1f || t > 0.9f) continue;
                var owner = l.a.unit != null || l.a.node != null ? l.a : l.b;
                if (HurtHero(l.Hot ? HotDamage : TickDamage, owner.Source(), owner.Feet)) return;
            }
        }
    }
}
