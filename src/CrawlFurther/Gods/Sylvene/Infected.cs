using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Fruiting Bodies (Cordyceps Saint): an infected monster that dies within <see cref="Duration"/> s of the infection rises
    /// again as a stalk-headed shambler that fights for 4 s and then bursts into three seeds. Tell: orange stalks on the
    /// infected one's head.
    /// </summary>
    public class Infected : MonoBehaviour
    {
        public const float Duration = 10f;
        float m_until;
        bool m_on;
        Health m_hp;
        DamageSource m_src;

        /// <summary>Infect <paramref name="who"/> for <see cref="Duration"/> s, the Saint's <paramref name="src"/> owning what rises.</summary>
        public static void Infect(GameObject who, DamageSource src)
        {
            if (who == null) return;
            var i = who.GetComponent<Infected>() ?? who.AddComponent<Infected>();
            i.m_hp = who.GetComponent<Health>();
            i.m_src = src;
            i.m_until = Time.time + Duration;
            i.m_on = true;
            i.enabled = true;
            ModInd.Set(who, SylveneFx.StalkInd, true, Duration);
        }

        void OnDisable() { m_on = false; }

        void Update()
        {
            if (!m_on) return;
            if (Time.time > m_until) { m_on = false; return; }
            if (m_hp != null && m_hp.IsAlive()) return;
            m_on = false;
            ModInd.Set(gameObject, SylveneFx.StalkInd, false);
            if (SylveneFx.ShamblerSpawner != null) FxFactory.SpawnOwned(SylveneFx.ShamblerSpawner, transform.position, m_src);
        }
    }
}
