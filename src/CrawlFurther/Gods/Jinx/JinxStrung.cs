using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>An ally a Puppeteer holds on its strings: it takes less damage from the hero while the Puppeteer lives and
    /// the hold lasts. Shows a little control cross over its head.</summary>
    public class JinxStrung : MonoBehaviour
    {
        /// <summary>The share of a hero hit a held ally still takes.</summary>
        public const float DamageTaken = 0.7f;

        PuppeteerStrings m_holder;
        float m_until;
        bool m_shown;

        /// <summary>True while the hold is on.</summary>
        public bool Held { get { return m_holder != null && m_holder.Alive && m_holder.isActiveAndEnabled && Time.time < m_until; } }

        public PuppeteerStrings Holder { get { return Held ? m_holder : null; } }

        public void Hold(PuppeteerStrings holder, float seconds)
        {
            m_holder = holder;
            m_until = Time.time + seconds;
            Show(true);
        }

        void Show(bool on)
        {
            if (on == m_shown) return;
            m_shown = on;
            if (JinxFx.Strung != null) ModInd.Set(gameObject, JinxFx.Strung, on);
        }

        void Update()
        {
            if (m_shown && !Held) { Show(false); m_holder = null; }
        }

        void OnDisable() { m_holder = null; m_shown = false; }
    }
}
