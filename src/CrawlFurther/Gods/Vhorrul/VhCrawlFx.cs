using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Something that creeps after the hero on the floor. A Grubling crawls at him for <see cref="GrubTime"/> s and bursts
    /// into wax when it reaches him (or runs out of time); one that crawls through fire catches light (its lit clip) and
    /// bursts as a burning pool instead. A Cloud (the Ashen Seraph's smothered fire) drifts at him at walking pace.
    /// </summary>
    public class VhCrawlFx : MonoBehaviour
    {
        public enum Kind { Grub, Cloud }
        public const float GrubSpeed = 20f, GrubTime = 3f, CloudSpeed = 42f, Reach = 6f;

        Kind m_kind;
        float m_t;
        bool m_lit, m_init;

        public void Restart(Kind kind = Kind.Grub) { m_kind = kind; m_t = 0f; m_lit = false; m_init = false; }

        void Update()
        {
            if (!m_init)
            {
                m_init = true;
                var pm = GetComponent<ParticleMotion>();
                if (pm != null) pm.enabled = false;
                transform.rotation = Quaternion.identity;
            }
            m_t += Time.deltaTime;
            var hero = ModUtil.Hero();
            Vector2 me = transform.position;
            Vector2 to = hero != null ? (Vector2)hero.transform.position - me : Vector2.zero;
            float speed = m_kind == Kind.Grub ? GrubSpeed : CloudSpeed;
            if (to.sqrMagnitude > 1f)
            {
                var step = to.normalized * speed * Time.deltaTime;
                transform.position = new Vector3(me.x + step.x, me.y + step.y, transform.position.z);
                var s = transform.localScale;
                if ((step.x < 0f) != (s.x < 0f)) transform.localScale = new Vector3(-s.x, s.y, s.z);
            }
            if (m_kind != Kind.Grub) return;
            if (!m_lit && IgniterFx.Nearest(me, 7f, f => f.gameObject != gameObject) != null) Light();
            if (m_t >= GrubTime || (hero != null && to.sqrMagnitude < Reach * Reach)) Burst();
        }

        void Light()
        {
            m_lit = true;
            var anim = GetComponent<exSpriteAnimation>();
            var clip = VhorrulFx.GrubLit;
            if (anim == null || clip == null) return;
            if (anim.GetAnimation(clip.name) == null) anim.AddAnimation(clip);
            anim.Play(clip.name);
        }

        void Burst()
        {
            var pop = m_lit ? VhorrulFx.GrubPopLit : VhorrulFx.GrubPop;
            if (pop != null) FxFactory.SpawnOwned(pop, transform.position, FxFactory.SourceOf(gameObject));
            SystemPool.Despawn(gameObject);
        }
    }
}
