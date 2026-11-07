using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>
    /// Shows its renderer only while the target object is active (a ribbon behind a player's name), and never while its
    /// sprite has no drawable art: a sprite whose atlas, texture or material is gone would draw as a blank quad.
    /// </summary>
    public class FollowActive : MonoBehaviour
    {
        public GameObject target;
        Renderer m_r;
        exSprite m_s;
        void Awake() { m_r = GetComponent<Renderer>(); m_s = GetComponent<exSprite>(); }
        void LateUpdate()
        {
            if (m_r == null) return;
            bool on = target != null && target.activeInHierarchy && Drawable();
            if (m_r.enabled != on) m_r.enabled = on;
        }

        bool Drawable()
        {
            if (m_s == null) return true;
            var m = m_r.sharedMaterial;
            return m_s.atlas != null && m_s.atlas.texture != null && m != null && m.mainTexture != null;
        }
    }
}
