using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>A Card Soldier's trap card: once it has landed it waits face down; when the hero steps on it the spade
    /// blades snap up (damage and a short root). It lies there about 6 s.</summary>
    public class JinxTrapFx : MonoBehaviour
    {
        static readonly List<JinxTrapFx> s_live = new List<JinxTrapFx>();
        public const float ArmTime = 0.3f, ReachX = 8f, ReachY = 5f;
        float m_t;
        bool m_done;

        /// <summary>Trap cards lying about now.</summary>
        public static int Count() { s_live.RemoveAll(x => x == null || !x.isActiveAndEnabled); return s_live.Count; }
        public void Arm() { m_t = 0f; m_done = false; }
        void OnEnable() { Arm(); if (!s_live.Contains(this)) s_live.Add(this); }
        void OnDisable() { s_live.Remove(this); }

        void Update()
        {
            if (m_done) return;
            m_t += Time.deltaTime;
            if (m_t < ArmTime) return;
            var h = ModUtil.Hero();
            if (h == null) return;
            var d = (Vector2)h.transform.position - (Vector2)transform.position;
            if (Mathf.Abs(d.x) > ReachX || Mathf.Abs(d.y) > ReachY) return;
            m_done = true;
            if (JinxFx.TrapSnap != null) FxFactory.SpawnOwned(JinxFx.TrapSnap, transform.position, FxFactory.SourceOf(gameObject));
            SystemPool.Despawn(gameObject);
        }
    }
}
