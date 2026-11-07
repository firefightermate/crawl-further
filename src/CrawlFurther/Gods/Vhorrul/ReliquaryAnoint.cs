using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    /// <summary>
    /// Votive Reliquary, Holy Fire: Anoint weeps holy oil over every Vhorrul monster within <see cref="Range"/> px (itself
    /// when none is near). An anointed monster's next 2 hits burn and light wax (a gold sheen and halo flame over it).
    /// Anointed, the Reliquary's own fan throws 5 flames (its second basic attack).
    /// </summary>
    public class ReliquaryAnoint : VhorrulBehaviour
    {
        public const float Range = 50f;
        Attacks m_attacks;
        float m_t;

        protected override void Awake() { base.Awake(); m_attacks = Body != null ? CrawlFurther.Util.R.Get<Attacks>(Body, "m_playerAttacks") : null; }

        /// <summary>Clip event (the skull weeps).</summary>
        public void VhAnoint()
        {
            if (!Alive) return;
            int n = 0;
            foreach (var q in FindObjectsOfType<VhorrulBehaviour>())
            {
                if (q == null || q == this || !q.Alive || ((Vector2)q.transform.position - Me).sqrMagnitude > Range * Range) continue;
                q.SetAnointed(AnointHits);
                n++;
            }
            if (n == 0) SetAnointed(AnointHits);
        }

        void Update()
        {
            m_t -= Time.deltaTime;
            if (m_t > 0f || m_attacks == null) return;
            m_t = 0.1f;
            m_attacks.SetNextAttackOverride(Anointed > 0 ? 1 : 0);
        }
    }
}
