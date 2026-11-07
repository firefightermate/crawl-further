using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Thunder Bull's charging head: tells the bull when it struck the hero (it then stops hitting harder).</summary>
    public class KrnRamFx : MonoBehaviour
    {
        public void Reset() { }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null) return;
            var hero = ModUtil.Hero();
            var v = d.m_victim.GetComponentInParent<Player>();
            if (hero == null || v == null || v.gameObject != hero) return;
            var src = FxFactory.SourceOf(gameObject);
            var bull = src != null && src.m_sourceOwner != null ? src.m_sourceOwner.GetComponent<BullMomentum>() : null;
            if (bull != null) bull.Struck();
        }
    }
}
