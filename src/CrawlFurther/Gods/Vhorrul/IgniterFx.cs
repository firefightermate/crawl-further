using System;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>Anything burning: ignites wax it touches, and counts as a flame (moth dives, wraith blinks).</summary>
    public class IgniterFx : Registered<IgniterFx>
    {
        public float radius = 10f;
        float m_t;

        /// <summary>Make every instance of <paramref name="tmpl"/> a flame (keeps any spawn hook already there).</summary>
        public static void AddTo(GameObject tmpl)
        {
            Action<GameObject> prev;
            FxFactory.OnSpawn.TryGetValue(tmpl, out prev);
            FxFactory.OnSpawn[tmpl] = i => { if (prev != null) prev(i); if (i.GetComponent<IgniterFx>() == null) i.AddComponent<IgniterFx>(); };
        }

        protected override void OnEnable() { base.OnEnable(); m_t = 0f; }

        void Update()
        {
            m_t -= Time.deltaTime;
            if (m_t > 0f) return;
            m_t = 0.08f;
            Vector2 p = transform.position;
            // backwards over the live list (Ignite removes the puddle): no snapshot copy 12 times a second per flame
            var all = WaxPuddleFx.All;
            for (int i = all.Count - 1; i >= 0; i--)
            {
                if (i >= all.Count) continue;
                var w = all[i];
                if (w == null) { all.RemoveAt(i); continue; }
                if (w.gameObject == gameObject) continue;
                float r = radius + w.radius;
                if ((w.Pos - p).sqrMagnitude <= r * r * 0.5f) w.Ignite(FxFactory.SourceOf(gameObject));
            }
        }
    }
}
