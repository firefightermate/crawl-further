using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>Per-character diminishing returns for the timed crowd control in <see cref="ModStatus"/>.</summary>
    internal class CCGuard : MonoBehaviour
    {
        float m_windowEnd = -1f;
        float m_immuneUntil = -1f;
        Player m_player;

        void Awake() { m_player = GetComponent<Player>(); }
        // pooled monsters come back with a fresh life: don't carry an old window or immunity over
        void OnEnable() { m_windowEnd = -1f; m_immuneUntil = -1f; }

        /// <summary>Called before a crowd-control status lands. Returns false to block it.</summary>
        public bool Allow()
        {
            float now = Time.time;
            if (now < m_immuneUntil) return false;
            if (m_windowEnd < 0f) m_windowEnd = now + ModStatus.WindowTime;
            return true;
        }

        void Update()
        {
            if (m_windowEnd < 0f || Time.time < m_windowEnd) return;
            m_windowEnd = -1f;
            m_immuneUntil = Time.time + ModStatus.ImmuneTime;
            if (m_player == null) return;
            var sm = m_player.GetStatusManager();
            if (sm == null) return;
            foreach (var s in new[] { ModStatus.Slow, ModStatus.Root, ModStatus.Daze })
                if (s != null) sm.RemoveStatus(s);
        }
    }
}
