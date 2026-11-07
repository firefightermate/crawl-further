using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Stormcaller's Static Build: the hero's hair stands on end for <see cref="Delay"/> s (every rod glints), then a bolt
    /// strikes his spot (1.2, after a short mark). Lightning Rods: if he stands within <see cref="Cover"/> px of a Kaurn rod or
    /// stud by then, the rod takes the bolt instead.
    /// </summary>
    public class CallerStaticBuild : KaurnBehaviour
    {
        public const float Delay = 1.5f, Cover = 20f;

        /// <summary>Clip event: the staff goes up.</summary>
        public void KrnStaticBuild() { StopAllCoroutines(); StartCoroutine(Build()); }

        IEnumerator Build()
        {
            var hero = ModUtil.Hero();
            if (hero == null) yield break;
            if (KaurnFx.HairInd != null) ModInd.Set(hero, KaurnFx.HairInd, true, Delay);
            Glint();
            yield return new WaitForSeconds(Delay * 0.5f);
            Glint();
            yield return new WaitForSeconds(Delay * 0.5f);
            if (hero == null || !hero.activeInHierarchy) yield break;
            Vector2 hp = hero.transform.position;
            var rod = KrnNode.Nearest(hp, Cover, n => n.kind == KrnNode.Kind.Rod || n.kind == KrnNode.Kind.Stud);
            if (rod != null)
            {
                if (KaurnFx.RodStrike != null) SystemPool.Spawn(KaurnFx.RodStrike, rod.transform.position);
                if (KaurnFx.HitFx != null) SystemPool.Spawn(KaurnFx.HitFx, rod.Top);
                yield break;
            }
            if (KaurnFx.StaticBolt != null) FxFactory.SpawnOwned(KaurnFx.StaticBolt, hp, Own);
        }

        static void Glint()
        {
            foreach (var n in KrnNode.Snapshot())
                if (n != null && (n.kind == KrnNode.Kind.Rod || n.kind == KrnNode.Kind.Stud) && KaurnFx.RodGlow != null)
                    SystemPool.Spawn(KaurnFx.RodGlow, n.transform.position);
        }
    }
}
