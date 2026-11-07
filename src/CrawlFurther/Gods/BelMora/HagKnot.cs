using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Slime Hag. Knot and Tear: a bite that lands ties her into a knot, and <see cref="Delay"/> s later she twists for a
    /// second bite (it bleeds) if the hero is still within <see cref="Reach"/> px of her jaws. Slime Spew: a glob that hits
    /// coats the hero in slime (<see cref="HeroSlime"/>). Tell: her body loops into a figure-eight (Knot).
    /// </summary>
    public class HagKnot : BelBehaviour
    {
        public const float Delay = 0.5f, Reach = 16f, Jaw = 16f;
        /// <summary>The knot and twist (set by the kit).</summary>
        public static exSpriteAnimClip KnotClip;

        bool m_tying;

        protected override void OnEnable() { base.OnEnable(); m_tying = false; }

        public override void OnHitHero(DamageInfo d)
        {
            if (HitFrom(d, BelMoraFx.HagGlob)) { HeroSlime.Coat(); return; }
            if (!HitFrom(d, BelMoraFx.HagRasp) || m_tying || !gameObject.activeInHierarchy) return;
            StartCoroutine(Tie());
        }

        IEnumerator Tie()
        {
            m_tying = true;
            yield return new WaitForSeconds(0.15f);
            if (Alive) Hold(KnotClip, 0.66f);
            yield return new WaitForSeconds(Delay - 0.15f);
            m_tying = false;
            var hero = ModUtil.Hero();
            if (!Alive || hero == null || BelMoraFx.HagTear == null) yield break;
            var jaw = Me + Face * Jaw;
            if (((Vector2)hero.transform.position - jaw).sqrMagnitude > Reach * Reach) yield break;
            FxFactory.SpawnOwned(BelMoraFx.HagTear, hero.transform.position, Own);
        }
    }
}
