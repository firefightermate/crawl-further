using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Util;

    /// <summary>
    /// Nailshade, Narrowing: each fan of nails that hits throws the next one tighter (30, then 20, then 10 degrees); a
    /// fan that misses spreads it back to 30. Tell: the spread of the nails held in its fingers (three idles and runs).
    /// Basics 0-2 are the three fans. Pin: a pin that roots, and if it has him, the Nailshade re-forms at his side.
    /// </summary>
    public class NailshadeNarrowing : UmbraelBehaviour
    {
        /// <summary>The idles and runs per spread, wide to tight (set by the kit).</summary>
        public static exSpriteAnimClip[] Idles, Runs;

        int m_level;
        bool m_hit;
        float m_pinnedAt = -99f;

        protected override void OnEnable() { base.OnEnable(); SetLevel(0); m_pinnedAt = -99f; }

        void SetLevel(int level)
        {
            m_level = Mathf.Clamp(level, 0, 2);
            NextBasic(m_level);
            if (Idles != null && Runs != null) SetStance(m_level == 0 ? null : Idles[m_level], m_level == 0 ? null : Runs[m_level]);
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template != UmbraelFx.Nail) return;
            StopCoroutine("Judge");
            m_hit = false;
            StartCoroutine("Judge");
        }

        // a fan's nails live 0.45 s: judge it once they are gone
        IEnumerator Judge()
        {
            yield return new WaitForSeconds(0.5f);
            SetLevel(m_hit ? m_level + 1 : 0);
        }

        public override void OnHitHero(DamageInfo d)
        {
            if (From(d, UmbraelFx.Nail)) m_hit = true;
            else if (From(d, UmbraelFx.Pin)) m_pinnedAt = Time.time;
        }

        /// <summary>Clip event: if the pin has the hero (landed in the last 0.9 s), re-form at his side.</summary>
        public void ModUmbPinPounce()
        {
            if (Time.time - m_pinnedAt > 0.9f) return;
            var h = ModUtil.Hero();
            if (h == null) return;
            Vector2 hero = h.transform.position;
            var side = Me - hero;
            if (side.sqrMagnitude < 1f) side = Vector2.left;
            ModUtil.Teleport(gameObject, ModUtil.SafePoint(hero, hero + side.normalized * 14f, 3f));
            Monster.FaceHero();
            m_pinnedAt = -99f;
        }
    }
}
