using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Gorgon, Don't Look: her eyes kindle for 0.4 s before the stone stare fires. If the hero is looking at her when it
    /// fires and the beam catches them, the root holds for the whole crowd-control window (1.2 s, not 0.8) and they grey
    /// over like stone.
    /// </summary>
    public class GorgonGaze : JinxBehaviour
    {
        public const float BeamLength = 62f, BeamHalfWidth = 9f, LookDegrees = 30f, StoneTime = 1.2f;

        /// <summary>Clip event: the stare fires (the beam itself is the clip's attack on the same frame).</summary>
        public void ModJinxStareFires()
        {
            var hero = ModUtil.Hero();
            if (!Alive || hero == null || !HeroAimsAtMe(LookDegrees, BeamLength + 20f)) return;
            Vector2 d = (Vector2)hero.transform.position - Me;
            var f = Face;
            float along = Vector2.Dot(d, f), across = Mathf.Abs(d.x * f.y - d.y * f.x);
            if (along < -4f || along > BeamLength + 6f || across > BeamHalfWidth) return;
            StartCoroutine(Stone(hero));
        }

        IEnumerator Stone(GameObject hero)
        {
            var spr = hero.GetComponent<exSprite>();
            var hp = hero.GetComponent<Player>();
            Color was = spr != null ? spr.color : Color.white;
            if (spr != null) spr.color = new Color(0.62f, 0.64f, 0.6f, was.a);
            yield return new WaitForSeconds(ModStatus.RootTime - 0.1f);
            if (hp != null && hero.activeInHierarchy && ModStatus.Root != null) hp.AddStatus(ModStatus.Root, Own, "jinxstone");
            yield return new WaitForSeconds(StoneTime - ModStatus.RootTime + 0.1f);
            if (spr != null) spr.color = new Color(was.r, was.g, was.b, spr.color.a);
        }

        protected override void OnDisable()
        {
            base.OnDisable();
            var hero = ModUtil.Hero();
            var spr = hero != null ? hero.GetComponent<exSprite>() : null;
            if (spr != null && spr.color.r < 0.7f && spr.color.g < 0.7f) spr.color = new Color(1f, 1f, 1f, spr.color.a);
        }
    }
}
