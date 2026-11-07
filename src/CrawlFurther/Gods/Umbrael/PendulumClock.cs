using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Pendulum, Tick-Tock: its glass blade swings by itself under the case (drawn in its idle and run), left and right
    /// every 1 s, hitting what it passes. Tell: the swing and a tick at each end. Stop the Clock: for 1.5 s time slows in a ring of r 40 round it: the
    /// hero moves 70 % slower there and his shots hang in the air.
    /// </summary>
    public class PendulumClock : UmbraelBehaviour
    {
        public const float Beat = 1f, Pivot = 11f, Ring = 40f, Stopped = 1.5f, Slowed = 0.3f;
        float m_t;
        int m_beat;
        Player.ePlayerState m_state;
        readonly List<ParticleMotion> m_near = new List<ParticleMotion>();
        readonly List<ParticleMotion> m_held = new List<ParticleMotion>();
        bool m_slowing;

        protected override void OnEnable() { base.OnEnable(); m_t = 0f; m_beat = 0; m_state = Player.ePlayerState.None; }

        protected override void OnDisable()
        {
            base.OnDisable();
            Release();
        }

        void Update()
        {
            if (!Alive || Body == null) return;
            // the blade is drawn in the idle and run (2 s a swing, through the middle on whole seconds); either clip starts
            // over when the state changes, so the beats start over with it
            var st = Body.GetState();
            if (st != m_state) { m_state = st; m_t = 0f; m_beat = 0; }
            if (st != Player.ePlayerState.Idle && st != Player.ePlayerState.Run) return;
            m_t += Time.deltaTime;
            int half = (int)(m_t / (Beat * 0.5f));
            if (half <= m_beat) return;
            m_beat = half;
            if (half % 2 == 0)
            {
                if (UmbraelFx.BladeHit != null) FxFactory.SpawnOwned(UmbraelFx.BladeHit, Me, Own);
            }
            else if (UmbraelFx.Tick != null)
            {
                float side = (half / 2) % 2 == 0 ? 1f : -1f;
                SystemPool.Spawn(UmbraelFx.Tick, Me + new Vector2(14f * side, Pivot - 2f));
            }
        }

        /// <summary>Clip event: stop the clock.</summary>
        public void ModUmbStopClock() { StopCoroutine("StopClock"); StartCoroutine("StopClock"); }

        IEnumerator StopClock()
        {
            Vector2 at = Me;
            if (UmbraelFx.TimeRing != null) SystemPool.Spawn(UmbraelFx.TimeRing, at);
            var hero = ModUtil.Hero();
            bool slowAllowed = hero != null && ModStatus.AllowCrowdControl(hero);
            var mv = hero != null ? hero.GetComponent<PlayerMovement>() : null;
            for (float t = 0f; t < Stopped; t += Time.deltaTime)
            {
                if (hero == null) break;
                bool inside = ((Vector2)hero.transform.position - at).sqrMagnitude < Ring * Ring;
                if (slowAllowed && mv != null && inside != m_slowing)
                {
                    m_slowing = inside;
                    if (inside) mv.SetSpeedMultiplier(Slowed); else mv.ResetSpeedMultiplier();
                }
                HeroShots.Near(at, Ring, m_near);
                foreach (var pm in m_near)
                    if (pm.enabled) { pm.enabled = false; m_held.Add(pm); }
                yield return null;
            }
            Release();
        }

        void Release()
        {
            if (m_slowing)
            {
                var hero = ModUtil.Hero();
                var mv = hero != null ? hero.GetComponent<PlayerMovement>() : null;
                if (mv != null) mv.ResetSpeedMultiplier();
                m_slowing = false;
            }
            foreach (var pm in m_held) if (pm != null && pm.gameObject.activeInHierarchy) pm.enabled = true;
            m_held.Clear();
        }
    }
}
