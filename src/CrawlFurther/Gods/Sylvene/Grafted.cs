using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A pod grafted onto a monster's head (Bloom Witch). It bursts when the hero comes within <see cref="Range"/> px of
    /// its host, or when the host dies. Tell: the swollen pod riding on the head.
    /// </summary>
    public class Grafted : MonoBehaviour
    {
        public const float Range = 20f;
        bool m_on;
        Health m_hp;
        DamageSource m_src;

        /// <summary>Graft a pod onto <paramref name="host"/> (owned by the witch's <paramref name="src"/>); one per head.</summary>
        public static void Graft(GameObject host, DamageSource src)
        {
            if (host == null) return;
            var g = host.GetComponent<Grafted>() ?? host.AddComponent<Grafted>();
            g.m_hp = host.GetComponent<Health>();
            g.m_src = src;
            g.m_on = true;
            g.enabled = true;
            ModInd.Set(host, SylveneFx.GraftInd, true);
        }

        void OnDisable() { m_on = false; }

        void Update()
        {
            if (!m_on) return;
            var hero = ModUtil.Hero();
            bool dead = m_hp == null || !m_hp.IsAlive();
            if (dead || (hero != null && ((Vector2)hero.transform.position - (Vector2)transform.position).sqrMagnitude < Range * Range)) Pop();
        }

        void Pop()
        {
            m_on = false;
            ModInd.Set(gameObject, SylveneFx.GraftInd, false);
            Vector2 at = transform.position;
            if (SylveneFx.PodBurstBig != null) FxFactory.SpawnOwned(SylveneFx.PodBurstBig, at, m_src);
            Orchard.PodBurst(at);
        }
    }
}
