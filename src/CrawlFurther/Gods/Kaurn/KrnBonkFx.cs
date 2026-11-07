using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Rivet Imp's Spark Plug: a bonk that lands on the hero stores a second spark, with a double clang.</summary>
    public class KrnBonkFx : MonoBehaviour
    {
        bool m_done;

        public void Reset() { m_done = false; }
        void OnEnable() { m_done = false; }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (m_done || d == null || d.m_victim == null) return;
            var hero = ModUtil.Hero();
            var v = d.m_victim.GetComponentInParent<Player>();
            if (hero == null || v == null || v.gameObject != hero) return;
            m_done = true;
            var src = FxFactory.SourceOf(gameObject);
            var unit = src != null && src.m_sourceOwner != null ? src.m_sourceOwner.GetComponent<KaurnUnit>() : null;
            if (unit == null) return;
            unit.Store(1);
            if (KaurnFx.DoubleClang != null) ModAttach.Front(SystemPool.Spawn(KaurnFx.DoubleClang, unit.Top + new Vector2(0f, 6f)), unit.gameObject);
        }
    }
}
