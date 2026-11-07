using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    /// <summary>Rides on a Ringmaster's hoop: remembers whether it hit anything and reports a clean miss when it ends.</summary>
    public class HoopEncoreFx : MonoBehaviour
    {
        RingmasterEncore m_owner;
        int m_encore;
        bool m_hit;

        public void Bind(RingmasterEncore owner, int encore) { m_owner = owner; m_encore = encore; m_hit = false; }

        void MsgOnAttackContact(DamageInfo d) { m_hit = true; }

        void OnDisable()
        {
            var o = m_owner;
            m_owner = null;
            if (o == null || m_hit || SystemMain.GetDeloadInProgress()) return;
            o.HoopMissed(m_encore);
        }
    }
}
