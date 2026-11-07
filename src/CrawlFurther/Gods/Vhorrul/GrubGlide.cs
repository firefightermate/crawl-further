using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    /// <summary>
    /// Tallow Grub, Upwelling: Melt slumps it into a puddle with its candle stub showing (can't be hit) that glides where
    /// it is steered for up to <see cref="GlideTime"/> s, then bubbles for 0.4 s and bursts up through the puddle (the
    /// Rise clip's hit). The puddle is still wax: fire touching it burns the grub and pops it out with no burst.
    /// </summary>
    public class GrubGlide : VhorrulBehaviour
    {
        public const float GlideTime = 2f, BurnOut = 0.5f, Speed = 1.35f, RiseUnder = 7f;
        public static exSpriteAnimClip Puddle, Glide, Rise, Pop;
        const string Source = "VhGlide";
        bool m_gliding;

        protected override void OnEnable() { base.OnEnable(); m_gliding = false; }
        protected override void OnDisable() { End(); base.OnDisable(); }

        /// <summary>Clip event (end of Melt): the glide begins.</summary>
        public void VhGlide()
        {
            if (!Alive) return;
            StopAllCoroutines();
            StartCoroutine(GlideFor());
        }

        IEnumerator GlideFor()
        {
            m_gliding = true;
            if (Hp != null) Hp.StartInvincibility(Source);
            SetStance(Puddle, Glide);
            SpeedScale(Speed);
            SendMessage("AnimStopInvincibility", SendMessageOptions.DontRequireReceiver);
            float t = 0f;
            bool popped = false;
            while (t < GlideTime && Alive)
            {
                t += Time.deltaTime;
                Steer(HeroPos);
                if (FireNear(8f) != null) { popped = true; break; }
                if (IsBot && HeroDist < RiseUnder) break;
                yield return null;
            }
            Steer(null);
            SpeedScale(1f);
            SetStance(null, null);
            m_gliding = false;
            if (popped) HurtSelf(BurnOut);
            if (Hp != null) Hp.StopInvincibility(Source);
            Hold(popped ? Pop : Rise, popped ? 0.4f : 0.76f);
        }

        void End()
        {
            if (!m_gliding) return;
            m_gliding = false;
            if (Hp != null) Hp.StopInvincibility(Source);
            SendMessage("AnimCollideOn", SendMessageOptions.DontRequireReceiver);
        }
    }
}
