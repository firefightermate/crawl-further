using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Belltower Hermit. Five Peals: five rings march from its claw toward the hero, <see cref="Step"/> px and
    /// <see cref="Beat"/> s apart (walls stop them). Carried by Water: a peal that reaches brine rings through the whole
    /// pool: a hero anywhere in it is stunned, and the march goes on from the pool's far edge. Tell: the pool shimmers in
    /// rings when a peal enters it.
    /// </summary>
    public class BelltowerPeals : BelBehaviour
    {
        public const int Steps = 5;
        public const float First = 16f, Step = 14f, Beat = 0.12f;

        /// <summary>Clip event (Peals, the slam): the march starts.</summary>
        public void BelMarch()
        {
            if (!Alive || BelMoraFx.BelltowerRing == null || !gameObject.activeInHierarchy) return;
            var dir = HeroPos - Feet;
            if (dir.sqrMagnitude < 1f) dir = Face;
            StopAllCoroutines();
            StartCoroutine(March(Feet, dir.normalized, Own));
        }

        IEnumerator March(Vector2 me, Vector2 dir, DamageSource src)
        {
            var at = me + dir * First;
            var rung = new List<Component>();
            for (int i = 0; i < Steps; i++)
            {
                if (!ModUtil.Clear(me, at)) yield break;
                BelPool pool;
                if (BelWater.PoolAt(at, out pool) && !rung.Contains(pool.Source))
                {
                    rung.Add(pool.Source);
                    RingPool(pool, src);
                    at = pool.Exit(at, dir) + dir * 2f;
                }
                FxFactory.SpawnOwned(BelMoraFx.BelltowerRing, at, src);
                me = at;
                at += dir * Step;
                yield return new WaitForSeconds(Beat);
            }
        }

        static void RingPool(BelPool pool, DamageSource src)
        {
            if (BelMoraFx.PoolRing != null)
            {
                var g = SystemPool.Spawn(BelMoraFx.PoolRing, pool.Pos);
                if (g != null && !pool.Tide) g.transform.localScale = new Vector3(0.45f, 0.5f, 1f);
            }
            var hero = BelWater.HeroPlayer();
            if (hero == null || !pool.Contains(hero.transform.position) || ModStatus.Daze == null) return;
            hero.AddStatus(ModStatus.Daze, src, "belpeal");
        }
    }
}
