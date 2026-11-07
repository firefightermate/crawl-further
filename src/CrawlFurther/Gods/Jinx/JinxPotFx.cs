using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{

    /// <summary>The High Roller's pot on the floor: ticks, then pays out through its owner; or busts.</summary>
    public class JinxPotFx : MonoBehaviour
    {
        RollerPot m_owner;
        float m_left;

        public void Bind(RollerPot owner, float seconds) { m_owner = owner; m_left = seconds; }

        void OnDisable() { m_owner = null; }

        void Update()
        {
            if (m_owner == null) return;
            m_left -= Time.deltaTime;
            if (m_left > 0f) return;
            var o = m_owner;
            m_owner = null;
            if (JinxFx.PotBurst != null) SystemPool.Spawn(JinxFx.PotBurst, transform.position);
            o.PotPaid(this);
            SystemPool.Despawn(gameObject);
        }

        /// <summary>The pot pays nothing: it collapses into smoke.</summary>
        public void Bust()
        {
            m_owner = null;
            if (!gameObject.activeInHierarchy || SystemMain.GetDeloadInProgress()) return;
            if (JinxFx.PotBust != null) SystemPool.Spawn(JinxFx.PotBust, transform.position);
            SystemPool.Despawn(gameObject);
        }
    }
}
