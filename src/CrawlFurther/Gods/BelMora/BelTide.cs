using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Rising Tide, Bel'Mora's perk (the dead still leave a small brine pool too). While a live Bel'Mora monster is in the
    /// hero's room, a tide comes in 1.5 s after the fight starts and then every 14 s: a surge washes over the floor and
    /// leaves two wide brine shallows (three while 3+ Bel'Mora monsters are up), at most four at a time, each 11.7 s. A
    /// hero wading in one is slowed; Bel'Mora monsters standing in one regenerate 0.35 health a second. Pools never form
    /// under the hero (36 px clear) and one forms near a Bel'Mora monster, so they have somewhere to fall back to.
    /// Monsters that time things to the tide listen to <see cref="TideIn"/> and <see cref="SecondsToNext"/>.
    /// </summary>
    public class BelTide : MonoBehaviour
    {
        public const float FirstTide = 1.5f, Every = 14f, MinFromHero = 36f, MinBetween = 56f;
        public const int MaxPools = 4;
        static BelTide s_inst;
        static readonly System.Reflection.MethodInfo s_space = HarmonyLib.AccessTools.Method(typeof(SystemLevel), "CheckForSpawnSpace");
        static readonly List<ModMonster> s_none = new List<ModMonster>();
        static bool s_logged;
        readonly List<ModMonster> m_tide = new List<ModMonster>();
        float m_next = -1f, m_scan;
        Room m_room;

        /// <summary>A tide came in: the pools it left (the Brood Urchin's eggs burst on it).</summary>
        public static event System.Action<List<BelTidePool>> TideIn;

        /// <summary>The live Bel'Mora monsters in the hero's room (refreshed every 0.25 s; the pools heal from this list).</summary>
        public static List<ModMonster> InRoom { get { return s_inst != null ? s_inst.m_tide : s_none; } }

        /// <summary>Seconds until the next tide (a large number while none is due).</summary>
        public static float SecondsToNext { get { return s_inst != null && s_inst.m_next > 0f ? Mathf.Max(0f, s_inst.m_next - Time.time) : 99f; } }

        public static void Ensure()
        {
            if (s_inst != null) return;
            var go = new GameObject("ModBelTide");
            DontDestroyOnLoad(go);
            s_inst = go.AddComponent<BelTide>();
        }

        void Update()
        {
            m_scan -= Time.deltaTime;
            if (m_scan > 0f) return;
            m_scan = 0.25f;
            try
            {
                var hero = ModUtil.Hero();
                var hh = hero != null ? hero.GetComponent<Health>() : null;
                if (hero == null || hh == null || !hh.IsAlive()) { m_next = -1f; return; }
                Room room = SystemLevel.GetCurrentRoom();
                if (room == null) { m_next = -1f; return; }
                m_tide.Clear();
                foreach (var mm in FindObjectsOfType<ModMonster>())
                {
                    if (mm == null || !(mm.Traits is BelMoraTraits)) continue;
                    var h = mm.GetComponent<Health>();
                    if (h == null || !h.IsAlive() || !SystemLevel.GetInCurrentRoom((Vector2)mm.transform.position)) continue;
                    m_tide.Add(mm);
                }
                if (m_tide.Count == 0) { m_next = -1f; return; }
                if (room != m_room || m_next < 0f) { m_room = room; m_next = Time.time + FirstTide; }
                if (Time.time < m_next) return;
                m_next = Time.time + Every;
                Tide(hero.transform.position);
            }
            catch (System.Exception e) { if (!s_logged) { s_logged = true; Plugin.Log.LogWarning("BelTide: " + e.Message); } }
        }

        static bool Floor(Vector2 p)
        {
            if (!SystemLevel.GetInCurrentRoom(p)) return false;
            if (s_space == null) return true;
            var lvl = Singleton<SystemLevel>.Get;
            foreach (var o in new[] { Vector2.zero, new Vector2(-20f, 0f), new Vector2(20f, 0f), new Vector2(0f, -6f), new Vector2(0f, 6f) })
                if (!(bool)s_space.Invoke(lvl, new object[] { p + o })) return false;
            return true;
        }

        static bool Clear(Vector2 p, Vector2 hero, float fromHero)
        {
            if ((p - hero).sqrMagnitude < fromHero * fromHero) return false;
            foreach (var t in BelTidePool.All)
                if (t != null && t.Live && SystemLevel.GetInCurrentRoom(t.Pos) && (t.Pos - p).sqrMagnitude < MinBetween * MinBetween) return false;
            return Floor(p);
        }

        static int LivePools()
        {
            int live = 0;
            foreach (var t in BelTidePool.All) if (t != null && t.Live && SystemLevel.GetInCurrentRoom(t.Pos)) live++;   // last room's don't count
            return live;
        }

        void Tide(Vector2 hero)
        {
            if (BelMoraFx.TidePool == null) return;
            int want = Mathf.Min(m_tide.Count >= 3 ? 3 : 2, MaxPools - LivePools());
            var made = new List<BelTidePool>();
            if (want > 0)
            {
                var lvl = Singleton<SystemLevel>.Get;
                var owner = m_tide[Random.Range(0, m_tide.Count)];
                var src = owner.OwnSource();
                // the first one near a Bel'Mora monster (somewhere it can fall back to), the rest anywhere in the room
                for (int tries = 0; tries < 40 && made.Count < want; tries++)
                {
                    Vector2 p;
                    if (made.Count == 0 && tries < 16)
                    {
                        var m = m_tide[Random.Range(0, m_tide.Count)];
                        p = (Vector2)m.transform.position + (Vector2)(Quaternion.Euler(0, 0, Random.Range(0f, 360f)) * Vector2.right) * Random.Range(8f, 30f);
                    }
                    else p = lvl.CalcRandomPointInCurrentRoom(22f);
                    if (!Clear(p, hero, MinFromHero)) continue;
                    var pool = Well(p, src);
                    if (pool != null) made.Add(pool);
                }
            }
            Raise(made);
        }

        static void Raise(List<BelTidePool> made)
        {
            if (TideIn == null) return;
            foreach (System.Action<List<BelTidePool>> h in TideIn.GetInvocationList())
            {
                try { h(made); }
                catch (System.Exception e) { Plugin.Log.LogWarning("BelTide listener: " + e.Message); }
            }
        }

        /// <summary>Well up one tide pool at <paramref name="p"/> with its surge line; returns it (null if none).</summary>
        public static BelTidePool Well(Vector2 p, DamageSource src)
        {
            if (BelMoraFx.TidePool == null) return null;
            var go = FxFactory.SpawnOwned(BelMoraFx.TidePool, p, src);
            if (BelMoraFx.TideCrest != null)
            {
                var c = SystemPool.Spawn(BelMoraFx.TideCrest, p + new Vector2(0f, 0.5f));
                if (c != null && Random.value < 0.5f) { var ls = c.transform.localScale; c.transform.localScale = new Vector3(-Mathf.Abs(ls.x), ls.y, ls.z); }
            }
            return go != null ? go.GetComponent<BelTidePool>() : null;
        }

        /// <summary>
        /// The tide called in early (the Tide Matriarch's Moon's Pull): <paramref name="count"/> pools well up
        /// <paramref name="dist"/> px from <paramref name="near"/>, clear of the hero, and the tide's listeners hear of it.
        /// </summary>
        public static List<BelTidePool> CallEarly(Vector2 near, int count, float dist, DamageSource src)
        {
            var made = new List<BelTidePool>();
            var hero = ModUtil.Hero();
            Vector2 hp = hero != null ? (Vector2)hero.transform.position : near + Vector2.one * 999f;
            float a0 = Random.Range(0f, 360f);
            for (int i = 0; i < 12 && made.Count < count; i++)
            {
                var dir = (Vector2)(Quaternion.Euler(0, 0, a0 + i * (360f / 12f) * 5f) * Vector2.right);
                var p = ModUtil.SafePoint(near, near + dir * dist, 20f);
                if ((p - near).sqrMagnitude < dist * dist * 0.4f || !Clear(p, hp, 24f)) continue;
                var pool = Well(p, src);
                if (pool != null) made.Add(pool);
            }
            Raise(made);
            return made;
        }
    }

    /// <summary>A tide pool on the floor: Bel'Mora monsters standing in it regenerate (with the regen indicator).</summary>
    public class BelTidePool : Registered<BelTidePool>
    {
        public const float ZoneW = 52f, ZoneH = 14f, HealRate = 0.35f, Life = 11.7f, DrainAt = 11.1f, Rx = 29f, Ry = 8.5f;
        float m_age, m_tick;
        readonly List<GameObject> m_healing = new List<GameObject>();

        public void Arm() { m_age = 0f; m_tick = 0f; }
        protected override void OnEnable() { base.OnEnable(); Arm(); }
        protected override void OnDisable() { base.OnDisable(); StopAll(); }

        /// <summary>Water is on the floor (after the crest washes in, before it drains).</summary>
        public bool Live { get { return isActiveAndEnabled && m_age > 0.15f && m_age < DrainAt; } }

        public bool Inside(Vector2 p)
        {
            var d = p - Pos;
            return (d.x * d.x) / (Rx * Rx) + (d.y * d.y) / (Ry * Ry) <= 1f;
        }

        void Update()
        {
            m_age += Time.deltaTime;
            m_tick -= Time.deltaTime;
            if (m_tick > 0f) return;
            m_tick = 0.25f;
            var still = new List<GameObject>();
            if (Live)
                foreach (var mm in BelTide.InRoom)
                {
                    if (mm == null || !(mm.Traits is BelMoraTraits)) continue;
                    var h = mm.GetComponent<Health>();
                    Vector2 me = mm.transform.position;
                    if (h == null || !h.IsAlive() || !Inside(me)) continue;
                    if (BrineFx.Nearest(me, 12f) != null) continue;   // a death pool under it already heals it (BelMoraTraits)
                    if (h.GetHealthCurrent() >= h.GetHealthMax()) continue;
                    h.Heal(HealRate * 0.25f);
                    still.Add(mm.gameObject);
                    ModInd.Regen(mm.gameObject, true);
                }
            foreach (var g in m_healing)
                if (g != null && !still.Contains(g) && BrineFx.Nearest(g.transform.position, 12f) == null) ModInd.Regen(g, false);
            m_healing.Clear();
            m_healing.AddRange(still);
        }

        void StopAll()
        {
            foreach (var g in m_healing)
                if (g != null && g.activeInHierarchy && BrineFx.Nearest(g.transform.position, 12f) == null) ModInd.Regen(g, false);
            m_healing.Clear();
        }
    }
}
