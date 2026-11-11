using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Slime Hag. Knot and Tear: a bite that lands ties her round the hero: her body coils up him two and a half turns
    /// (FxBelHagKnot Wrap, then Hold), he is rooted, and <see cref="Delay"/> s after the bite the knot snaps taut and
    /// bursts (Tear) with a second, bleeding bite, if he is still within <see cref="Reach"/> px. Slime Spew: a glob that
    /// hits coats the hero in slime (<see cref="HeroSlime"/>). Tell: her body loops into a figure-eight (Knot).
    /// <para>Before 1.3.3 only her own body knotted, the hero was never wrapped, and the second bite needed him right at
    /// her jaws (reported: "says it curls it in a knot, but it doesn't, and it looks boring").</para>
    /// </summary>
    public class HagKnot : BelBehaviour
    {
        public const float Delay = 0.8f, Reach = 40f, WrapTime = 0.25f;
        /// <summary>The knot and twist (set by the kit).</summary>
        public static exSpriteAnimClip KnotClip;

        bool m_tying;
        GameObject m_on;

        protected override void OnEnable() { base.OnEnable(); m_tying = false; }
        protected override void OnDisable() { base.OnDisable(); Drop(); m_tying = false; }

        public override void OnHitHero(DamageInfo d)
        {
            if (HitFrom(d, BelMoraFx.HagGlob)) { HeroSlime.Coat(); return; }
            if (!HitFrom(d, BelMoraFx.HagRasp) || m_tying || !gameObject.activeInHierarchy) return;
            StartCoroutine(Tie());
        }

        void Drop()
        {
            if (m_on != null && m_on.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(m_on);
            m_on = null;
        }

        void Show(GameObject template, Vector2 at)
        {
            Drop();
            if (template != null) m_on = SystemPool.Spawn(template, at);
        }

        IEnumerator Tie()
        {
            m_tying = true;
            var hero = ModUtil.Hero();
            if (hero == null) { m_tying = false; yield break; }
            if (Alive) Hold(KnotClip, Delay + 0.1f);
            var hp = hero.GetComponent<Player>();
            if (hp != null) hp.AddStatus(ModStatus.Root, Own, "bel");
            Show(BelMoraFx.HagWrap, hero.transform.position);
            var wrap = m_on; m_on = null;              // the wrap plays out on its own
            float t = 0f;
            bool holding = false;
            while (t < Delay && Alive && hero != null && hero.activeInHierarchy)
            {
                t += Time.deltaTime;
                Vector2 at = hero.transform.position;
                if (wrap != null && wrap.activeInHierarchy) wrap.transform.position = at;
                if (!holding && t >= WrapTime) { holding = true; Show(BelMoraFx.HagHold, at); }
                if (m_on != null) m_on.transform.position = at;
                yield return null;
            }
            Drop();
            m_tying = false;
            if (!Alive || hero == null || !hero.activeInHierarchy) yield break;
            if (((Vector2)hero.transform.position - Me).sqrMagnitude > Reach * Reach) yield break;
            if (BelMoraFx.HagSnap != null) SystemPool.Spawn(BelMoraFx.HagSnap, hero.transform.position);
            if (BelMoraFx.HagTear != null) FxFactory.SpawnOwned(BelMoraFx.HagTear, hero.transform.position, Own);
        }
    }
}
