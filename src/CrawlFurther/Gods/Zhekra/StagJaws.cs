using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Stag Titan, Jaw Gap and Uproot: its pinch hits only at the jaw tips, 26 to 34 px out; closer than
    /// <see cref="Gap"/> px its jaws can't reach and it can only headbutt (basic 1). Uproot hooks the jaws under a hero at
    /// the tips and tosses him up: <see cref="AirTime"/> s in the air (he can't act), and he lands where he was. Tell: the
    /// jaws' shadow on the floor marks the tip zone.
    /// </summary>
    public class StagJaws : ZhkBehaviour
    {
        public const float Gap = 18f, AirTime = 0.6f, HookNear = 20f, HookFar = 40f;

        void Update()
        {
            if (!Alive || InAttack) return;
            NextBasic(HeroDist < Gap ? 1 : 0);
        }

        /// <summary>Clip event (Uproot): the hook under the hero.</summary>
        public void ModZhkUproot()
        {
            var hero = ModUtil.Hero();
            if (!Alive || hero == null) return;
            var to = (Vector2)hero.transform.position - Me;
            float d = to.magnitude;
            if (d < HookNear || d > HookFar || Vector2.Dot(to / Mathf.Max(d, 0.01f), Face) < 0.5f) return;
            if (!ModStatus.AllowCrowdControl(hero)) return;
            ZhkHero.On(hero).Lift(AirTime, 16f);
            StartCoroutine(Land(hero));
        }

        IEnumerator Land(GameObject hero)
        {
            yield return new WaitForSeconds(AirTime);
            if (hero != null && hero.activeInHierarchy && ZhekraFx.TossLand != null) FxFactory.SpawnOwned(ZhekraFx.TossLand, hero.transform.position, Own);
        }
    }
}
