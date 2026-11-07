using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Glass Seraph, Guiding Light: Umbrael echoes within 60 px of it bend up to 20 px toward the hero (applied by
    /// <see cref="UmbraelEcho"/>). Tell: a thin thread of light from it to each echo it bends.
    /// </summary>
    public class SeraphLight : UmbraelBehaviour
    {
        static readonly List<SeraphLight> s_all = new List<SeraphLight>();

        protected override void OnEnable() { base.OnEnable(); if (!s_all.Contains(this)) s_all.Add(this); }
        protected override void OnDisable() { base.OnDisable(); s_all.Remove(this); }

        /// <summary>The Seraph nearest <paramref name="p"/> within <paramref name="range"/> that passes <paramref name="ok"/>.</summary>
        public static SeraphLight Nearest(Vector2 p, float range, System.Predicate<SeraphLight> ok)
        {
            SeraphLight best = null; float bd = range * range;
            foreach (var s in s_all)
            {
                if (s == null || !ok(s)) continue;
                float d = ((Vector2)s.transform.position - p).sqrMagnitude;
                if (d < bd) { bd = d; best = s; }
            }
            return best;
        }

        /// <summary>Draw the thread of light to an echo it bent.</summary>
        public void Thread(Vector2 site)
        {
            if (UmbraelFx.LightThread == null) return;
            UmbraelFx.Span(SystemPool.Spawn(UmbraelFx.LightThread, Me), Me + new Vector2(0f, 20f), site + new Vector2(0f, 6f));
        }
    }

    /// <summary>On a Prism feather: the first wall it hits splits it in two (the new half turned 25 degrees off).</summary>
    public class FeatherSplitFx : MonoBehaviour
    {
        ParticleMotion m_pm;
        Vector2 m_dir;
        bool m_init, m_split;

        void Awake() { m_pm = GetComponent<ParticleMotion>(); }
        public void Arm() { m_init = false; m_split = false; }
        void OnEnable() { Arm(); }

        void Update()
        {
            if (m_pm == null || m_split) return;
            var v = m_pm.GetVelocity();
            if (v.sqrMagnitude < 1f) return;
            if (!m_init) { m_dir = v.normalized; m_init = true; return; }
            if (Vector2.Dot(m_dir, v.normalized) > 0.85f) { m_dir = v.normalized; return; }
            m_split = true;
            if (UmbraelFx.Feather == null) return;
            float a = Mathf.Atan2(v.y, v.x) * Mathf.Rad2Deg + (Random.value < 0.5f ? 25f : -25f);
            FxFactory.SpawnOwned(UmbraelFx.Feather, transform.position, FxFactory.SourceOf(gameObject), a);
            if (UmbraelFx.EchoSparkle != null) SystemPool.Spawn(UmbraelFx.EchoSparkle, transform.position);
        }
    }
}
