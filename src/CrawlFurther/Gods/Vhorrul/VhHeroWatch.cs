using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// What Vhorrul's curses do to the hero, checked on his body: with a Fever every unlit wax pool he steps in lights
    /// under him; while Soulless (his soul flame in a Lantern Wraith's lantern) stepping into any fire takes it back.
    /// </summary>
    public class VhHeroWatch : MonoBehaviour
    {
        float m_t;
        PlayerStatusManager m_sm;

        void Update()
        {
            m_t -= Time.deltaTime;
            if (m_t > 0f) return;
            m_t = 0.08f;
            if (m_sm == null) { var p = GetComponent<Player>(); m_sm = p != null ? p.GetStatusManager() : null; if (m_sm == null) return; }
            Vector2 me = transform.position;
            if (VhorrulFx.Fever != null && m_sm.GetHasStatusWithClass(VhorrulFx.Fever.m_class))
            {
                var w = WaxPuddleFx.Nearest(me, 9f);
                if (w != null) w.Ignite(null);
            }
            if (VhorrulFx.Soulless != null && m_sm.GetHasStatusWithClass(VhorrulFx.Soulless.m_class) && IgniterFx.Nearest(me, 9f) != null)
                m_sm.RemoveStatus(VhorrulFx.Soulless);
        }
    }
}
