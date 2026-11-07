using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>Shows its renderer only while the target object is active (a ribbon behind a player's name).</summary>
    public class FollowActive : MonoBehaviour
    {
        public GameObject target;
        Renderer m_r;
        void Awake() { m_r = GetComponent<Renderer>(); }
        void LateUpdate()
        {
            bool on = target != null && target.activeInHierarchy;
            if (m_r != null && m_r.enabled != on) m_r.enabled = on;
        }
    }
}
