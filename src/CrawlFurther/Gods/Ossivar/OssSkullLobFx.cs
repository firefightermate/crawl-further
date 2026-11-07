using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>The thrown skull in flight: wherever it stops (its range, a wall, the hero) it lands as the skull on the floor.</summary>
    public class OssSkullLobFx : MonoBehaviour
    {
        bool m_live;
        void OnEnable() { m_live = true; }

        void OnDisable()
        {
            if (!m_live) return;
            m_live = false;
            var src = FxFactory.SourceOf(gameObject);
            var owner = src != null ? src.m_sourceOwner : null;
            var rb = owner != null ? owner.GetComponent<RattleSkull>() : null;
            if (rb != null) rb.Landed(transform.position);
        }
    }
}
