using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    /// <summary>
    /// Pale Empress, Storm Queen: while she lives the room's blizzard comes every 8 s instead of 12, and its gusts lay
    /// their ice paths toward the hero (<see cref="YsvFloor"/> asks <see cref="AnyIn"/>). Tell: aurora ribbons over her
    /// that flare in the second before each gust.
    /// </summary>
    public class EmpressStormQueen : YsveldBehaviour
    {
        public const float FlareLead = 1f;
        static readonly List<EmpressStormQueen> s_living = new List<EmpressStormQueen>();
        static readonly Vector2 Over = new Vector2(0f, 44f);
        GameObject m_ribbons;
        bool m_flaring;

        protected override void OnEnable() { base.OnEnable(); m_flaring = false; if (!s_living.Contains(this)) s_living.Add(this); }

        protected override void OnDisable() { base.OnDisable(); s_living.Remove(this); Drop(); }

        /// <summary>Is a living Pale Empress in <paramref name="room"/>?</summary>
        public static bool AnyIn(Room room)
        {
            foreach (var q in s_living)
                if (q != null && q.Alive && room.IsPointInRoom(q.transform.position)) return true;
            return false;
        }

        void Drop() { if (m_ribbons != null) { CrawlFurther.Monsters.ModAttach.Drop(m_ribbons, gameObject); m_ribbons = null; } }

        void Update()
        {
            if (!Alive) { Drop(); return; }
            if (m_ribbons == null && YsveldFx.AuroraRibbons != null)
            {
                m_ribbons = CrawlFurther.Monsters.ModAttach.Spawn(YsveldFx.AuroraRibbons, gameObject, Over);
                m_flaring = false;
            }
            if (m_ribbons == null) return;
            float next = YsvFloor.NextBlizzard;
            bool flare = next > 0f && next - Time.time <= FlareLead;
            if (flare == m_flaring) return;
            m_flaring = flare;
            YsvUtil.Play(m_ribbons, flare ? YsveldFx.AuroraFlareClip : YsveldFx.AuroraLoopClip);
        }
    }
}
