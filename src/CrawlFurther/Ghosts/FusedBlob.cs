using UnityEngine;

namespace CrawlFurther.Content.Ghosts
{
    /// <summary>
    /// On the Brute and Titan: a fused blob left to its own AI still uses its special (Bounce, Engulf)
    /// when the hero is in reach. A player inside it uses the special as usual.
    /// </summary>
    public class FusedBlob : MonoBehaviour
    {
        Player m_player;
        Health m_health;
        float m_specialTimer;

        void Awake()
        {
            m_player = GetComponent<Player>();
            m_health = GetComponent<Health>();
        }

        void OnDisable() { m_specialTimer = 0f; }

        void Update()
        {
            if (m_player == null || m_health == null || !m_health.IsAlive()) return;
            AiSpecial.Drive(m_player, ref m_specialTimer);
        }
    }
}
