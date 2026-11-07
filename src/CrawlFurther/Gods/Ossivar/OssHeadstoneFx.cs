using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A Tombwright headstone: a solid footprint for <see cref="Life"/> seconds (solid once nobody stands in it). Knocked
    /// over, it cracks for a moment, falls away (hitting along <see cref="FallLength"/> px), topples the next standing stone
    /// in its path, and breaks into a bone pile. Left alone it crumbles into one.
    /// </summary>
    public class OssHeadstoneFx : Registered<OssHeadstoneFx>
    {
        public const float Life = 6f, CrackTime = 0.24f, FallLength = 28f, ChainReach = 30f;
        enum State { Stand, Crack, Fall, Gone }
        State m_state;
        GameObject m_body;
        exSpriteAnimation m_anim;
        DamageSource m_src;
        Vector2 m_dir;
        float m_t;
        bool m_solid;

        public bool Standing { get { return m_state == State.Stand && isActiveAndEnabled; } }

        public void Begin(DamageSource src)
        {
            m_src = src; m_state = State.Stand; m_t = 0f; m_solid = false; m_dir = Vector2.zero;
            transform.localScale = Vector3.one;
            m_body = OssFloor.Body(gameObject, 10f, 4f);
            m_anim = GetComponent<exSpriteAnimation>();
        }

        protected override void OnDisable() { base.OnDisable(); if (m_body != null) m_body.SetActive(false); m_solid = false; }

        void Play(exSpriteAnimClip c) { if (m_anim != null && c != null) m_anim.Play(c, 0); }

        /// <summary>Knock it over away from <paramref name="away"/>'s origin (the direction it falls).</summary>
        public void Topple(Vector2 away, DamageSource by)
        {
            if (m_state != State.Stand) return;
            m_dir = away.sqrMagnitude > 0.01f ? away.normalized : Vector2.right;
            if (by != null) m_src = by;
            m_state = State.Crack; m_t = 0f;
            Play(OssivarFx.StoneCrack);
        }

        void Fall()
        {
            m_state = State.Fall; m_t = 0f;
            if (m_body != null) m_body.SetActive(false);
            bool side = Mathf.Abs(m_dir.x) >= Mathf.Abs(m_dir.y) * 0.6f;
            if (side)
            {
                transform.localScale = new Vector3(m_dir.x < 0f ? -1f : 1f, 1f, 1f);
                Play(OssivarFx.StoneFallSide);
            }
            else Play(m_dir.y < 0f ? OssivarFx.StoneFallFront : OssivarFx.StoneFallBack);
            Vector2 me = transform.position;
            if (OssivarFx.StoneFall != null)
                FxFactory.SpawnOwned(OssivarFx.StoneFall, me + m_dir * FallLength * 0.5f, m_src, Mathf.Atan2(m_dir.y, m_dir.x) * Mathf.Rad2Deg);
            // the domino: the next standing stone in the fall's path goes over too
            foreach (var s in Snapshot())
            {
                if (s == null || s == this || !s.Standing) continue;
                Vector2 d = s.Pos - me;
                float along = Vector2.Dot(d, m_dir);
                if (along <= 0f || along > ChainReach) continue;
                if (Mathf.Abs(d.x * m_dir.y - d.y * m_dir.x) > 9f) continue;
                s.Topple(m_dir, m_src);
            }
        }

        void Update()
        {
            m_t += Time.deltaTime;
            Vector2 me = transform.position;
            switch (m_state)
            {
                case State.Stand:
                    if (!m_solid && !OssFloor.Occupied(me, 8f, 4f)) { m_solid = true; if (m_body != null) m_body.SetActive(true); }
                    if (m_t > Life) { m_state = State.Gone; m_t = 0f; if (m_body != null) m_body.SetActive(false); Play(OssivarFx.StoneCrumble); }
                    break;
                case State.Crack:
                    if (m_t > CrackTime) Fall();
                    break;
                case State.Fall:
                    if (m_t > 0.35f) { m_state = State.Gone; m_t = 0f; Play(OssivarFx.StoneCrumble); }
                    break;
                case State.Gone:
                    if (m_t > 0.45f)
                    {
                        Vector2 at = m_dir.sqrMagnitude < 0.01f ? me : me + m_dir * 12f;
                        OssFloor.DropPile(me, at, m_src);
                        transform.localScale = Vector3.one;
                        SystemPool.Despawn(gameObject);
                    }
                    break;
            }
        }
    }
}
