using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// One flame of a Candle Wyrm's Wick Coil: lit wax laid round the hero. When the ring closes every flame glows white
    /// (<see cref="Glow"/>), then they all run in to the ring's centre (<see cref="Close"/>), each carrying a hit.
    /// </summary>
    public class VhCoilFx : MonoBehaviour
    {
        Vector2 m_from, m_to;
        float m_t, m_dur = -1f;
        GameObject m_hit;

        public void Restart() { m_dur = -1f; m_hit = null; }

        public void Glow()
        {
            var anim = GetComponent<exSpriteAnimation>();
            var clip = VhorrulFx.CoilWhite;
            if (anim == null || clip == null) return;
            if (anim.GetAnimation(clip.name) == null) anim.AddAnimation(clip);
            anim.Play(clip.name);
        }

        /// <summary>Run to <paramref name="centre"/> over <paramref name="seconds"/>, carrying the closing hit.</summary>
        public void Close(Vector2 centre, float seconds, DamageSource src)
        {
            m_from = transform.position; m_to = centre; m_t = 0f; m_dur = seconds;
            if (VhorrulFx.CoilClose != null) m_hit = FxFactory.SpawnOwned(VhorrulFx.CoilClose, m_from, src);
        }

        void Update()
        {
            if (m_dur <= 0f) return;
            m_t += Time.deltaTime;
            float k = Mathf.Clamp01(m_t / m_dur);
            var p = Vector2.Lerp(m_from, m_to, k * k);
            transform.position = new Vector3(p.x, p.y, transform.position.z);
            if (m_hit != null && m_hit.activeInHierarchy) m_hit.transform.position = new Vector3(p.x, p.y + 4f, m_hit.transform.position.z);
            if (k < 1f) return;
            m_dur = -1f;
            if (m_hit != null && m_hit.activeInHierarchy) SystemPool.Despawn(m_hit);
            m_hit = null;
            SystemPool.Despawn(gameObject);
        }
    }
}
