using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Pit Antlion, Sand Pit and Sand Flick: it digs in and a pit <see cref="PitRadius"/> * 2 px across opens round it for
    /// <see cref="PitTime"/> s. In the pit the hero walks outward at <see cref="OutSpeed"/>x and inward at
    /// <see cref="InSpeed"/>x, and every <see cref="FlickEvery"/> s it flicks sand at him: a puff (0.3) that knocks him
    /// <see cref="FlickPull"/> px toward the middle. Tell: the pit's sliding rings, and sand arcs flying up the slope.
    /// </summary>
    public class AntlionPit : ZhkBehaviour
    {
        public const float PitRadius = 30f, PitTime = 5f, OutSpeed = 0.5f, InSpeed = 1.3f, FlickEvery = 0.8f, FlickPull = 10f;
        /// <summary>Its stance in the pit, the flick and the climb out (set by the kit).</summary>
        public static exSpriteAnimClip PitIdle, FlickClip, EmergeClip;

        Vector2 m_centre;
        float m_until, m_flick;
        bool m_slowing;
        PlayerMovement m_heroMove;

        protected override void OnEnable() { base.OnEnable(); m_until = 0f; }

        protected override void OnDisable() { base.OnDisable(); m_until = 0f; Slope(1f); }

        bool InPit { get { return Time.time < m_until; } }

        /// <summary>Clip event (the end of Dig): the pit opens.</summary>
        public void ModZhkPit()
        {
            if (!Alive) return;
            m_centre = Me;
            m_until = Time.time + PitTime;
            m_flick = FlickEvery * 0.5f;
            if (ZhekraFx.Pit != null) SystemPool.Spawn(ZhekraFx.Pit, m_centre);
            Hold(PitIdle, PitTime + 0.4f);
            StartCoroutine(Climb());
        }

        IEnumerator Climb()
        {
            yield return new WaitForSeconds(PitTime);
            Slope(1f);
            if (Alive && EmergeClip != null && Anim != null) { Ensure(EmergeClip); Anim.Play(EmergeClip.name); }
        }

        void Slope(float k)
        {
            if (m_heroMove == null) return;
            if (Mathf.Abs(k - 1f) < 0.01f) { if (m_slowing) m_heroMove.ResetSpeedMultiplier(); m_slowing = false; return; }
            m_heroMove.SetSpeedMultiplier(k);
            m_slowing = true;
        }

        void Update()
        {
            if (!InPit) return;
            if (!Alive) { m_until = 0f; Slope(1f); return; }
            var hero = ModUtil.Hero();
            if (hero == null) { Slope(1f); return; }
            if (m_heroMove == null || m_heroMove.gameObject != hero) m_heroMove = hero.GetComponent<PlayerMovement>();
            Vector2 hp = hero.transform.position, out_ = hp - m_centre;
            if (out_.sqrMagnitude > PitRadius * PitRadius) { Slope(1f); return; }
            var v = m_heroMove != null ? m_heroMove.GetVelocity() : Vector2.zero;
            if (v.sqrMagnitude > 1f) Slope(Vector2.Dot(v, out_) > 0f ? OutSpeed : InSpeed);
            m_flick -= Time.deltaTime;
            if (m_flick > 0f) return;
            m_flick = FlickEvery;
            StartCoroutine(Flick(hero));
        }

        IEnumerator Flick(GameObject hero)
        {
            Monster.Face(hero.transform.position);
            if (FlickClip != null && Anim != null) { Ensure(FlickClip); Anim.Play(FlickClip.name); }
            yield return new WaitForSeconds(0.08f);
            if (!Alive || hero == null) yield break;
            Vector2 hp = hero.transform.position;
            if (ZhekraFx.SandFlick != null) SystemPool.Spawn(ZhekraFx.SandFlick, hp);
            if (ZhekraFx.FlickHit != null) FxFactory.SpawnOwned(ZhekraFx.FlickHit, hp + new Vector2(0f, 6f), Own);
            var dir = m_centre - hp;
            if (dir.sqrMagnitude > 1f) ModUtil.Teleport(hero, ModUtil.SafePoint(hp, hp + dir.normalized * Mathf.Min(FlickPull, dir.magnitude)));
            yield return new WaitForSeconds(0.25f);
            if (Alive && InPit && PitIdle != null && Anim != null) Anim.Play(PitIdle.name);
        }
    }
}
