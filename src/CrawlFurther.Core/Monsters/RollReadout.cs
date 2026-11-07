using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Util;

    /// <summary>
    /// Put on a damaging effect (a thrown die, a weapon swing): when it lands a hit, the roll it carries pops up over the
    /// victim as a <see cref="FloatNumber"/>. Shows once per victim per spawn.
    /// </summary>
    public class RollReadout : MonoBehaviour
    {
        /// <summary>The face rolled (ignored when <see cref="fromSource"/> is set).</summary>
        public int roll;
        /// <summary>Faces on the die: the top face shows gold, a 1 grey-red.</summary>
        public int max = 6;
        /// <summary>Read the roll from the <see cref="RollSource"/> on the same object instead of <see cref="roll"/>.</summary>
        public bool fromSource;
        /// <summary>Show the number beside the hit point (right of a die face that pops there) instead of over the head.</summary>
        public bool besideHit;

        readonly List<GameObject> m_shown = new List<GameObject>(4);

        void OnEnable() { m_shown.Clear(); }
        void MsgSetSpawner(DamageSource s) { m_shown.Clear(); }

        int Value
        {
            get
            {
                if (!fromSource) return roll;
                var c = GetComponent<RollSource>();
                return c != null ? c.lastRoll : 0;
            }
        }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_isDamageFromStatus) return;
            int v = Value;
            if (v <= 0) return;
            var victim = d.m_victim;
            for (int i = 0; i < m_shown.Count; i++) if (m_shown[i] == victim) return;
            if (m_shown.Count >= 8) m_shown.RemoveAt(0);
            m_shown.Add(victim);
            if (besideHit)
            {
                // where DamageEffect puts its spawnOnHit puff: the victim's centre line, at the hit's height
                var box = ModUtil.Hurtbox(victim);
                Vector2 me = transform.position;
                float x = box != null ? box.bounds.center.x : victim.transform.position.x;
                float y = box != null ? Mathf.Clamp(me.y, box.bounds.min.y, box.bounds.max.y) : me.y;
                FloatNumber.Roll(v, max, new Vector2(x + 12f, y + 11f), victim);
            }
            else FloatNumber.RollOver(victim, v, max);
        }
    }
}
