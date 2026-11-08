using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Wire Wyvern's Ride the Arc: it dives into the arc network and races along it as a streak of light (up to
    /// <see cref="MaxHops"/> arcs, <see cref="Speed"/> px/s, untouchable), bursting out at the post nearest the hero with a
    /// bite. Lit Route: for the <see cref="Plan"/> s before it rides, every arc on its route flashes white. A hero the streak
    /// passes through takes <see cref="PassDamage"/>. With no arc in reach it streaks straight at the hero instead.
    /// </summary>
    public class WyvernRide : KaurnBehaviour
    {
        public const int MaxHops = 3;
        public const float Speed = 300f, Plan = 0.4f, PassDamage = 1.0f, PassDist = 7f, Fallback = 80f, Board = 60f, Lift = 10f;
        public static exSpriteAnimClip BurstClip;

        class Stop { public KaurnConduction.End e; public Vector2 p; public Vector2 Pos { get { return e != null && e.Valid ? e.Feet : p; } } }

        readonly List<Stop> m_route = new List<Stop>();
        readonly List<List<GameObject>> m_lit = new List<List<GameObject>>();
        exSprite m_sprite;
        GameObject m_streak;
        bool m_planning, m_riding;

        protected override void Awake() { base.Awake(); m_sprite = GetComponent<exSprite>(); }

        protected override void OnEnable() { base.OnEnable(); m_planning = m_riding = false; m_route.Clear(); }

        protected override void OnDisable() { base.OnDisable(); ClearLit(); EndRide(); }

        void ClearLit() { foreach (var s in m_lit) KaurnFx.Clear(s); m_lit.Clear(); }

        /// <summary>Clip event at the start of the dive: pick the route and light it.</summary>
        public void KrnRidePlan()
        {
            m_route.Clear();
            Vector2 hp = HeroPos;
            var links = KaurnConduction.Links;
            // the graph of arcs (ends keyed by what they stand on)
            var adj = new Dictionary<Component, List<KaurnConduction.End>>();
            var ends = new Dictionary<Component, KaurnConduction.End>();
            foreach (var l in links)
            {
                if (l.ToHero) continue;
                foreach (var pair in new[] { new[] { l.a, l.b }, new[] { l.b, l.a } })
                {
                    List<KaurnConduction.End> n;
                    if (!adj.TryGetValue(pair[0].c, out n)) adj[pair[0].c] = n = new List<KaurnConduction.End>();
                    n.Add(pair[1]);
                    ends[pair[0].c] = pair[0];
                }
            }
            // board at itself if it is linked, else at the nearest arc end in reach
            Component start = null;
            if (adj.ContainsKey(Unit)) start = Unit;
            else
            {
                float bd = Board * Board;
                foreach (var kv in ends)
                {
                    float d = (kv.Value.Feet - Me).sqrMagnitude;
                    if (d < bd && ModUtil.Clear(Me, kv.Value.Feet)) { bd = d; start = kv.Key; }
                }
            }
            if (start != null)
            {
                // breadth first up to MaxHops arcs: come out at the end nearest the hero
                var prev = new Dictionary<Component, Component> { { start, null } };
                var depth = new Dictionary<Component, int> { { start, 0 } };
                var q = new Queue<Component>();
                q.Enqueue(start);
                Component best = null; float bestD = float.MaxValue;
                while (q.Count > 0)
                {
                    var c = q.Dequeue();
                    if (c != start)
                    {
                        float d = (ends[c].Feet - hp).sqrMagnitude;
                        if (d < bestD) { bestD = d; best = c; }
                    }
                    if (depth[c] >= MaxHops) continue;
                    foreach (var nb in adj[c])
                        if (nb.c != null && !prev.ContainsKey(nb.c) && nb.other == null) { prev[nb.c] = c; depth[nb.c] = depth[c] + 1; q.Enqueue(nb.c); }
                }
                if (best != null)
                {
                    var path = new List<Component>();
                    for (var c = best; c != null; c = prev[c]) path.Insert(0, c);
                    if (start != Unit) m_route.Add(new Stop { e = ends[start], p = ends[start].Feet });
                    for (int i = 1; i < path.Count; i++) m_route.Add(new Stop { e = ends[path[i]], p = ends[path[i]].Feet });
                }
            }
            if (m_route.Count == 0)
            {
                var d = hp - Me;
                float len = Mathf.Min(Fallback, Mathf.Max(0f, d.magnitude - 16f));
                m_route.Add(new Stop { p = ModUtil.SafePoint(Me, Me + (d.sqrMagnitude > 0.01f ? d.normalized : Face) * len) });
            }
            m_planning = true;
            StartCoroutine(StopPlanning());
        }

        IEnumerator StopPlanning() { yield return new WaitForSeconds(Plan + 0.1f); m_planning = false; ClearLit(); }

        void Update()
        {
            if (!m_planning) return;
            // the lit route follows its ends while they move
            var from = Me;
            for (int i = 0; i < m_route.Count; i++)
            {
                while (m_lit.Count <= i) m_lit.Add(new List<GameObject>());
                var to = m_route[i].Pos;
                KaurnFx.Chain(m_lit[i], KaurnFx.ArcWhite, from + new Vector2(0f, Lift), to + new Vector2(0f, Lift));
                from = to;
            }
        }

        /// <summary>Clip event: it is gone into the arcs.</summary>
        public void KrnRideGo()
        {
            if (!Alive) return;
            // the Dive clip hands the body over here: with no route to ride, give control straight back
            if (m_route.Count == 0) { SendMessage("AnimRun", SendMessageOptions.DontRequireReceiver); return; }
            m_planning = false;
            ClearLit();
            StartCoroutine(Ride());
        }

        IEnumerator Ride()
        {
            m_riding = true;
            if (m_sprite != null) m_sprite.enabled = false;
            if (Hp != null) Hp.StartInvincibility("krnride");
            Body.AnimCollideOff();
            if (KaurnFx.RideFlash != null) SystemPool.Spawn(KaurnFx.RideFlash, Me);
            if (KaurnFx.RideStreak != null) m_streak = SystemPool.Spawn(KaurnFx.RideStreak, Me + new Vector2(0f, Lift));
            Hold(null, 2f);
            bool passed = false;
            var hero = ModUtil.Hero();
            Vector2 pos = Me;
            foreach (var s in m_route)
            {
                float guard = 1.5f;
                while (guard > 0f)
                {
                    guard -= Time.deltaTime;
                    var to = s.Pos;
                    var d = to - pos;
                    float step = Speed * Time.deltaTime;
                    pos = d.magnitude <= step ? to : pos + d.normalized * step;
                    Place(pos);
                    if (m_streak != null)
                    {
                        m_streak.transform.position = new Vector3(pos.x, pos.y + Lift, m_streak.transform.position.z);
                        if (d.sqrMagnitude > 0.01f) m_streak.transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
                    }
                    if (!passed && hero != null && ((Vector2)hero.transform.position - pos).sqrMagnitude < PassDist * PassDist)
                        passed = KaurnConduction.HurtHero(PassDamage, Own, pos);
                    if ((pos - to).sqrMagnitude < 1f) break;
                    yield return null;
                }
            }
            EndRide();
            Release();
            Monster.FaceHero();
            if (KaurnFx.RideFlash != null) SystemPool.Spawn(KaurnFx.RideFlash, Me);
            if (BurstClip != null && Body != null) { Ensure(BurstClip); Body.StartStatusAnimation(BurstClip); }
            yield return new WaitForSeconds(0.1f);
            if (Alive && KaurnFx.WyvernBite != null)
            {
                var dir = HeroPos - Me;
                float a = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
                FxFactory.SpawnOwned(KaurnFx.WyvernBite, Me + (dir.sqrMagnitude > 0.01f ? dir.normalized : Face) * 18f + new Vector2(0f, 14f), Own, a);
            }
        }

        void EndRide()
        {
            if (!m_riding) return;
            m_riding = false;
            if (m_sprite != null) m_sprite.enabled = true;
            if (Hp != null) Hp.StopInvincibility("krnride");
            if (Body != null) Body.AnimCollideOn();
            if (m_streak != null && m_streak.activeInHierarchy) SystemPool.Despawn(m_streak);
            m_streak = null;
        }
    }
}
