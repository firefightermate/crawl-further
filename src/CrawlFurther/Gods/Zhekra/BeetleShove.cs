using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Resin Beetle, Shove: its snap pushes the hero <see cref="Push"/> px; pushed onto resin, he sticks (a root). Tell: the
    /// hero skids with a puff of dust, and the resin splashes when he lands in it.
    /// </summary>
    public class BeetleShove : ZhkBehaviour
    {
        public const float Push = 16f, PushTime = 0.12f, ResinReach = 11f;

        protected override void OnHeroContact(DamageInfo d, string effect)
        {
            if (effect != "ModZhkBeetleSnap") return;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            var dir = (Vector2)hero.transform.position - Me;
            dir = dir.sqrMagnitude > 1f ? dir.normalized : Face;
            StartCoroutine(Shove(hero, dir));
        }

        IEnumerator Shove(GameObject hero, Vector2 dir)
        {
            if (ZhekraFx.Skid != null) SystemPool.Spawn(ZhekraFx.Skid, hero.transform.position);
            Vector2 from = hero.transform.position;
            var to = ModUtil.SafePoint(from, from + dir * Push);
            for (float t = 0f; t < PushTime; t += Time.deltaTime)
            {
                if (hero == null || !hero.activeInHierarchy) yield break;
                ModUtil.Teleport(hero, Vector2.Lerp(from, to, t / PushTime));
                yield return null;
            }
            if (hero == null) yield break;
            ModUtil.Teleport(hero, to);
            if (ZhkResinFx.Nearest(to, ResinReach) == null || !ModStatus.AllowCrowdControl(hero)) yield break;
            var p = hero.GetComponent<Player>();
            if (p != null && ZhekraFx.Root != null) p.AddStatus(ZhekraFx.Root, Own, "zhkstick");
            if (ZhekraFx.ResinPop != null) SystemPool.Spawn(ZhekraFx.ResinPop, to);
        }
    }
}
