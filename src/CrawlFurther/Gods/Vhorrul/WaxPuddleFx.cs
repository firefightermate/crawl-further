using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Unlit wax on the floor. Slows the hero (its status zone), heals the tallow monsters standing in it, and catches
    /// fire from any flame. A Chandler's poured line is touch paper: light one segment and the flame races the rest of
    /// that line at <see cref="LineSpeed"/>.
    /// </summary>
    public class WaxPuddleFx : Registered<WaxPuddleFx>
    {
        /// <summary>Pixels a second the flame runs along a poured line.</summary>
        public const float LineSpeed = 200f;

        public float radius = 11f;
        /// <summary>Laid by the hero's Wax Slick: still burns, but Vhorrul monsters don't heal in it.</summary>
        public bool heroOwned;
        /// <summary>A segment of a Chandler's line (touch paper).</summary>
        public bool line;

        static readonly Dictionary<GameObject, int> s_lineOf = new Dictionary<GameObject, int>();
        static readonly System.Predicate<WaxPuddleFx> s_monsterWax = w => !w.heroOwned;

        bool m_ignited;
        GameObject m_owner;
        int m_lineId = -1;
        float m_igniteIn = -1f;
        DamageSource m_igniteBy;

        protected override void OnEnable()
        {
            base.OnEnable();
            m_ignited = false; heroOwned = false; m_owner = null; m_lineId = -1; m_igniteIn = -1f; m_igniteBy = null;
        }

        /// <summary>Monster wax within healing reach of <paramref name="p"/> (a regeneration test for MonsterTraits).</summary>
        public static bool HealsAt(Vector2 p) { return Nearest(p, 10f, s_monsterWax) != null; }

        /// <summary>The segments <paramref name="owner"/> pours from now on belong to a new line.</summary>
        public static void NewLine(GameObject owner)
        {
            int n;
            s_lineOf.TryGetValue(owner, out n);
            s_lineOf[owner] = n + 1;
        }

        void Update()
        {
            if (line && m_lineId < 0)
            {
                var src = FxFactory.SourceOf(gameObject);
                m_owner = src != null ? src.m_sourceOwner : null;
                int n = 0;
                if (m_owner != null) s_lineOf.TryGetValue(m_owner, out n);
                m_lineId = n;
            }
            if (m_igniteIn < 0f) return;
            m_igniteIn -= Time.deltaTime;
            if (m_igniteIn <= 0f) { m_igniteIn = -1f; Ignite(m_igniteBy); }
        }

        /// <summary>Burst into a burning pool (owned by whoever laid the wax, else <paramref name="by"/>).</summary>
        public void Ignite(DamageSource by)
        {
            if (m_ignited || VhorrulFx.BurningPool == null) return;
            m_ignited = true;
            var src = FxFactory.SourceOf(gameObject) ?? by;
            if (line && m_lineId >= 0)
            {
                // touch paper: the flame runs on to every other segment of this line, nearest first
                foreach (var w in All)
                {
                    if (w == null || w == this || !w.line || w.m_ignited || w.m_owner != m_owner || w.m_lineId != m_lineId) continue;
                    float t = (w.Pos - Pos).magnitude / LineSpeed;
                    if (w.m_igniteIn < 0f || t < w.m_igniteIn) { w.m_igniteIn = t; w.m_igniteBy = src; }
                }
                FxFactory.SpawnOwned(VhorrulFx.LineFlare ?? VhorrulFx.BurningPool, Pos, src);
            }
            else FxFactory.SpawnOwned(VhorrulFx.BurningPool, Pos, src);
            All.Remove(this);
            SystemPool.Despawn(gameObject);
        }
    }
}
