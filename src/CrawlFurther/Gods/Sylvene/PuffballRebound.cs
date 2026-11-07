using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Puffball Brute, Rebound: it is light, so the hero's hits knock it back twice as far; knocked into a wall it
    /// squashes against it and bounces straight back at the hero (1.0) in a burst of spores. Tell: the squash on the wall.
    /// </summary>
    public class PuffballRebound : SylveneBehaviour
    {
        public const float Knock = 2f, BounceSpeed = 260f, BounceTime = 0.25f, Cooldown = 1f;
        /// <summary>The squash against the wall (set by the kit).</summary>
        public static exSpriteAnimClip SquashClip;

        float m_ready;
        bool m_bouncing;

        protected override void OnEnable() { base.OnEnable(); m_ready = 0f; m_bouncing = false; }

        public override float KnockScale(DamageInfo d) { return Knock; }

        void Update()
        {
            if (!Alive || m_bouncing || Time.time < m_ready || Body == null || Body.GetState() != Player.ePlayerState.Knockback) return;
            var v = Move != null ? Move.GetVelocity() : Vector2.zero;
            if (v.sqrMagnitude < 30f * 30f) return;
            if (ModUtil.Clear(Me + new Vector2(0f, 6f), Me + new Vector2(0f, 6f) + v.normalized * 9f)) return;
            StartCoroutine(Rebound(v.normalized));
        }

        IEnumerator Rebound(Vector2 into)
        {
            m_bouncing = true;
            m_ready = Time.time + Cooldown;
            if (Move != null) Move.AnimCancelKnockback();
            if (SquashClip != null && Anim != null) { Ensure(SquashClip); Anim.Play(SquashClip.name); }
            if (SylveneFx.SporePuff != null) FxFactory.SpawnOwned(SylveneFx.SporePuff, Me + into * 6f + new Vector2(0f, 6f), Own, AngleTo(Me, Me - into));
            yield return new WaitForSeconds(0.16f);
            if (!Alive) { m_bouncing = false; yield break; }
            var dir = (HeroPos - Me).sqrMagnitude > 1f ? (HeroPos - Me).normalized : -into;
            var hit = SylveneFx.PuffWall != null ? FxFactory.SpawnOwned(SylveneFx.PuffWall, Me, Own) : null;
            float t = 0f;
            while (t < BounceTime && Alive)
            {
                Push(dir * BounceSpeed, 0.06f);
                if (hit != null && hit.activeInHierarchy) hit.transform.position = new Vector3(Me.x, Me.y, hit.transform.position.z);
                t += Time.deltaTime;
                yield return null;
            }
            m_bouncing = false;
        }
    }
}
