using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Bone Lancer, Planted Spears: a thrown spear that misses (stops anywhere without hitting) sticks upright in the floor
    /// where it stopped, as an <see cref="OssSpearFx"/>.
    /// </summary>
    public class OssSpearFlightFx : MonoBehaviour
    {
        /// <summary>The volley flies at chest height: a spear that drops stands this far below its flight line.</summary>
        public const float Height = 12f;
        bool m_live, m_hit;
        void OnEnable() { m_live = true; m_hit = false; }

        // sent by Health.Damage to the effect that hit
        void MsgOnAttackContact(DamageInfo d) { m_hit = true; }

        void OnDisable()
        {
            if (!m_live) return;
            m_live = false;
            if (m_hit || OssivarFx.SpearStand == null) return;
            var go = SystemPool.Spawn(OssivarFx.SpearStand, transform.position - new Vector3(0f, Height, 0f));
            if (go == null) return;
            var s = go.GetComponent<OssSpearFx>() ?? go.AddComponent<OssSpearFx>();
            s.Begin(FxFactory.SourceOf(gameObject));
        }
    }
}
