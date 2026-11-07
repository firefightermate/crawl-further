using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// On the hero while a Rime Warden's Challenge holds (3 s): his hits on anything but that Warden do half damage. Shows
    /// a frost brand over his head that matches the sigil over the Warden.
    /// </summary>
    public class YsvChallenged : MonoBehaviour
    {
        public const float Duration = 3f, Cut = 0.5f;
        static int s_active;
        GameObject m_by, m_brand;
        float m_left;
        bool m_on;

        /// <summary>True while any hero is challenged (a cheap check for the hit patch).</summary>
        public static bool Any { get { return s_active > 0; } }

        public static void Begin(GameObject hero, GameObject warden)
        {
            if (hero == null) return;
            var c = hero.GetComponent<YsvChallenged>() ?? hero.AddComponent<YsvChallenged>();
            c.m_by = warden; c.m_left = Duration;
            if (!c.m_on) { c.m_on = true; s_active++; }
            if (c.m_brand == null && YsveldFx.Brand != null) c.m_brand = ModAttach.Spawn(YsveldFx.Brand, hero, new Vector2(0f, 22f));
            c.enabled = true;
        }

        /// <summary>The factor a hit from <paramref name="hero"/> on <paramref name="victim"/> is scaled by.</summary>
        public static float ScaleFor(GameObject hero, GameObject victim)
        {
            if (s_active <= 0 || hero == null) return 1f;
            var c = hero.GetComponent<YsvChallenged>();
            if (c == null || !c.m_on || victim == c.m_by) return 1f;
            return Cut;
        }

        void Update()
        {
            m_left -= Time.deltaTime;
            if (m_left <= 0f || !YsvUtil.Alive(m_by)) End();
        }

        void End()
        {
            if (m_on) { m_on = false; s_active--; }
            if (m_brand != null) { ModAttach.Drop(m_brand, gameObject); m_brand = null; }
            m_by = null;
            enabled = false;
        }

        void OnDisable() { End(); }
    }
}
