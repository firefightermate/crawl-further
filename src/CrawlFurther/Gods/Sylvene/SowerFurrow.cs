using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Sower, Furrow: Strafe flies it <see cref="Span"/> px sideways across the hero's front in <see cref="StrafeTime"/> s
    /// (its player can still drift in or out) firing <see cref="Needles"/> needles that plant a row of seeds. The seeds of
    /// one pass share a furrow (<see cref="Furrow"/>): they ripen together and burst together. Tell: a thin vine joining the row.
    /// </summary>
    public class SowerFurrow : SylveneBehaviour
    {
        public const float Span = 80f, StrafeTime = 1.2f, NeedleSpeed = 220f;
        public const int Needles = 6;
        static readonly Vector2 Muzzle = new Vector2(12f, 10f);

        /// <summary>Clip event: the pass begins.</summary>
        public void ModSylStrafe() { if (Alive) StartCoroutine(Strafe()); }

        IEnumerator Strafe()
        {
            int furrow = Orchard.NewFurrow();
            var to = HeroPos - Me;
            var across = new Vector2(-to.y, to.x).normalized;
            if (across.sqrMagnitude < 0.5f) across = Vector2.up;
            // fly the way that has room for the whole pass
            if (!ModUtil.Clear(Me, Me + across * Span * 0.5f)) across = -across;
            float speed = Span / StrafeTime, t = 0f, next = 0f;
            int fired = 0;
            while (t < StrafeTime && Alive)
            {
                Push(across * speed, 0.08f);
                Monster.FaceHero();
                if (t >= next && fired < Needles)
                {
                    Fire(furrow);
                    fired++;
                    next += StrafeTime / Needles;
                }
                t += Time.deltaTime;
                yield return null;
            }
            // the last needles are still in the air: wait for them to land, then the row ripens as one
            yield return new WaitForSeconds(0.5f);
            Furrow.Close(furrow);
        }

        void Fire(int furrow)
        {
            if (SylveneFx.StrafeNeedle == null) return;
            Vector2 from = Me + new Vector2(Muzzle.x * Side, Muzzle.y);
            Vector2 at = HeroPos;
            var go = FxFactory.SpawnOwned(SylveneFx.StrafeNeedle, from, Own, AngleTo(from, at));
            if (go == null) return;
            var e = go.GetComponent<Effect>();
            if (e != null) R.Set(e, "m_destroyAfterTime", Mathf.Clamp((at - from).magnitude / NeedleSpeed, 0.08f, 0.5f));
            var p = go.GetComponent<PlantOnEnd>();
            if (p != null) p.furrow = furrow;
        }
    }
}
