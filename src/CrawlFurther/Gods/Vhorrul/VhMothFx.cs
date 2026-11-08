using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A Moth Matron's ember moth. It only hunts a burning hero: then its wings flare (the Hunt clip) and it flies at
    /// him fast. Otherwise it flutters ahead in a loose cloud, lighting any wax it touches (it is a flame).
    /// </summary>
    public class VhMothFx : MonoBehaviour
    {
        public const float DriftSpeed = 32f, HuntSpeed = 150f, Turn = 400f;

        Vector2 m_dir;
        float m_t, m_wob;
        bool m_hunting, m_init;
        exSpriteAnimation m_anim;
        exSpriteAnimClip m_drift;

        public void Restart() { m_init = false; m_hunting = false; m_t = 0f; }

        void Update()
        {
            if (!m_init)
            {
                m_init = true;
                var pm = GetComponent<ParticleMotion>();
                if (pm != null) pm.enabled = false;
                float a = transform.eulerAngles.z * Mathf.Deg2Rad;
                m_dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                // the moth isn't free-rotated: a left-facing Matron flips it by scale, not by angle
                if (transform.lossyScale.x < 0f) m_dir.x = -Mathf.Abs(m_dir.x);
                transform.rotation = Quaternion.identity;
                m_wob = Random.Range(0f, 6f);
                m_anim = GetComponent<exSpriteAnimation>();
                if (m_anim != null) m_drift = m_anim.GetCurrentAnimation() != null ? m_anim.GetCurrentAnimation().clip : null;
            }
            m_t += Time.deltaTime;
            var hero = ModUtil.Hero();
            bool hunt = hero != null && VhorrulPack.HeroBurning();
            if (hunt != m_hunting) SetHunt(hunt);
            float speed = DriftSpeed;
            if (hunt)
            {
                var to = (Vector2)hero.transform.position + new Vector2(0f, 7f) - (Vector2)transform.position;
                float cur = Mathf.Atan2(m_dir.y, m_dir.x) * Mathf.Rad2Deg;
                float a = Mathf.MoveTowardsAngle(cur, Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg, Turn * Time.deltaTime) * Mathf.Deg2Rad;
                m_dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                speed = HuntSpeed;
            }
            var side = new Vector2(-m_dir.y, m_dir.x) * Mathf.Sin(m_t * 9f + m_wob) * (hunt ? 0f : 18f);
            var step = (m_dir * speed + side) * Time.deltaTime;
            transform.position = new Vector3(transform.position.x + step.x, transform.position.y + step.y, transform.position.z);
        }

        void SetHunt(bool on)
        {
            m_hunting = on;
            if (m_anim == null) return;
            var clip = on ? VhorrulFx.MothHunt : m_drift;
            if (clip == null) return;
            if (m_anim.GetAnimation(clip.name) == null) m_anim.AddAnimation(clip);
            m_anim.Play(clip.name);
        }
    }
}
