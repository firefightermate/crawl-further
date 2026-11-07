using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    /// <summary>The orchard's green wisp: it flies from a burst pod to the Rot Mother it feeds, then fades.</summary>
    public class WispFx : MonoBehaviour
    {
        const float Speed = 150f;
        Transform m_to;

        void OnEnable() { m_to = null; }

        /// <summary>Fly to <paramref name="to"/> (its chest, 18 px up).</summary>
        public void Seek(Transform to) { m_to = to; }

        void Update()
        {
            if (m_to == null || !m_to.gameObject.activeInHierarchy) { Gone(); return; }
            Vector2 target = (Vector2)m_to.position + new Vector2(0f, 18f);
            Vector2 p = transform.position;
            var d = target - p;
            float step = Speed * Time.deltaTime;
            if (d.magnitude <= step) { Gone(); return; }
            // a little wobble, so it reads as a drifting husk and not a bolt
            var side = new Vector2(-d.y, d.x).normalized * Mathf.Sin(Time.time * 18f) * 0.6f;
            transform.position = new Vector3(p.x + d.normalized.x * step + side.x, p.y + d.normalized.y * step + side.y, transform.position.z);
        }

        void Gone()
        {
            m_to = null;
            if (gameObject.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(gameObject);
        }
    }
}
