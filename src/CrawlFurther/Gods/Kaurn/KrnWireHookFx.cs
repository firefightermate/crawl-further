using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Util;

    /// <summary>Wire Gremlin's hooked wire: when it reaches the hero he is wired for <see cref="WiredTime"/> s (Conductor).</summary>
    public class KrnWireHookFx : MonoBehaviour
    {
        public const float WiredTime = 3f;
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
            KaurnConduction.Wire(WiredTime);
        }
    }
}
