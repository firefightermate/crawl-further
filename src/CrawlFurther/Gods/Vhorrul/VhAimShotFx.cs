using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>A hatching Tallow Sow egg: spits <see cref="projectile"/> at the hero, then leaves <see cref="leave"/> (wax).</summary>
    public class VhAimShotFx : MonoBehaviour
    {
        public GameObject projectile, leave;
        public float lift;
        bool m_done;

        public void Restart() { m_done = false; }
        void OnEnable() { m_done = false; }

        void Update()
        {
            if (m_done || projectile == null) return;
            m_done = true;
            var hero = ModUtil.Hero();
            var src = FxFactory.SourceOf(gameObject);
            Vector2 p = (Vector2)transform.position + new Vector2(0f, lift);
            float ang = Random.Range(0f, 360f);
            if (hero != null) { var d = (Vector2)hero.transform.position + new Vector2(0f, 6f) - p; ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg; }
            FxFactory.SpawnOwned(projectile, p, src, ang);
            if (leave != null) FxFactory.SpawnOwned(leave, transform.position, src);
        }
    }
}
