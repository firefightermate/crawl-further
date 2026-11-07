using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    /// <summary>
    /// Anemone Boxer, Footwork: after every punch it hops <see cref="Back"/> px back out of reach, bouncing on its toes,
    /// then comes in for the next. Tell: the bounce, and two little dust puffs at each landing (HopBack).
    /// </summary>
    public class BoxerFootwork : BelBehaviour
    {
        public const float Back = 18f, Air = 0.16f;
        /// <summary>The hop back (set by the kit).</summary>
        public static exSpriteAnimClip HopBackClip;

        /// <summary>Clip event (the last frame of a punch): hop back.</summary>
        public void BelHopBack()
        {
            if (!Alive || !gameObject.activeInHierarchy) return;
            StopAllCoroutines();
            StartCoroutine(Hop(-ToHero()));
        }

        IEnumerator Hop(Vector2 dir)
        {
            Hold(HopBackClip, 0.32f);
            float t = 0f;
            while (t < Air && Alive)
            {
                t += Time.deltaTime;
                Shift(dir * Back * Time.deltaTime / Air);
                yield return null;
            }
        }
    }
}
