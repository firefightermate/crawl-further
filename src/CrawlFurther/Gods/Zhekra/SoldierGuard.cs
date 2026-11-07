using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Hive Soldier, Scythe Guard: it plants its feet and raises its scythes for <see cref="GuardTime"/> s. The instant the
    /// hero comes within <see cref="Reach"/> px it strikes, <see cref="Delay"/> s later (faster than a step back): 1.2 and
    /// a root. If nobody comes, its next sweep is 50% faster (basic 1). Tell: scythes high, antennae flat, eyes glinting.
    /// </summary>
    public class SoldierGuard : ZhkBehaviour
    {
        public const float GuardTime = 2f, Reach = 30f, Delay = 0.1f;
        /// <summary>The ambush strike (set by the kit).</summary>
        public static exSpriteAnimClip StrikeClip;

        bool m_guard;

        protected override void OnEnable() { base.OnEnable(); m_guard = false; }

        /// <summary>Clip event: the scythes are up.</summary>
        public void ModZhkGuardOn() { m_guard = true; }

        /// <summary>Clip event: the guard ran out with nobody in reach.</summary>
        public void ModZhkGuardOff()
        {
            if (!m_guard) return;
            m_guard = false;
            NextBasic(1);
        }

        /// <summary>Clip event: the quick sweep is spent.</summary>
        public void ModZhkSweepDone() { NextBasic(0); }

        void Update()
        {
            if (!m_guard || !Alive) return;
            var hero = ModUtil.Hero();
            if (hero == null || ((Vector2)hero.transform.position - Me).sqrMagnitude > Reach * Reach) return;
            m_guard = false;
            StartCoroutine(Ambush(hero));
        }

        IEnumerator Ambush(GameObject hero)
        {
            yield return new WaitForSeconds(Delay);
            if (!Alive || hero == null) yield break;
            Vector2 hp = hero.transform.position;
            var dir = hp - Me;
            dir = dir.sqrMagnitude > 1f ? dir.normalized : Face;
            Monster.Face(hp);
            if (StrikeClip != null) { Ensure(StrikeClip); Body.StartStatusAnimation(StrikeClip); }
            if (ZhekraFx.GuardStrike != null)
                FxFactory.SpawnOwned(ZhekraFx.GuardStrike, Me + dir * 14f + new Vector2(0f, 6f), Own, Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg);
        }
    }
}
