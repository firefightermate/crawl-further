using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Glass Widow, Brittle: her bite or her web glazes the hero for 3 s (<see cref="Brittle"/>). Glaze Web drops a web on
    /// his spot after 0.4 s (its shadow shows first) that roots him.
    /// </summary>
    public class WidowBrittle : UmbraelBehaviour
    {
        /// <summary>Clip event: the web goes up; it lands where he stands now.</summary>
        public void ModUmbGlazeWeb()
        {
            var h = ModUtil.Hero();
            if (h != null && UmbraelFx.GlazeWeb != null) FxFactory.SpawnOwned(UmbraelFx.GlazeWeb, h.transform.position, Own);
        }

        public override void OnHitHero(DamageInfo d)
        {
            if (From(d, UmbraelFx.WidowFang) || From(d, UmbraelFx.GlazeWeb)) Brittle.Glaze(ModUtil.Hero());
        }
    }

    /// <summary>
    /// The glaze a Glass Widow leaves on the hero: for 3 s the next hit he takes from anyone cracks it for +0.6. Tell: a
    /// glassy sheen on him.
    /// </summary>
    public static class Brittle
    {
        public const float Seconds = 3f, Crack = 0.6f;
        static float s_until;
        static GameObject s_on;

        public static void Glaze(GameObject hero)
        {
            if (hero == null) return;
            s_until = Time.time + Seconds;
            s_on = hero;
            ModInd.Set(hero, UmbraelFx.GlazeInd, true, Seconds);
        }

        /// <summary>A monster's hit is about to land on the hero: crack the glaze.</summary>
        public static void Strike(GameObject hero, DamageInfo d)
        {
            if (hero != s_on || Time.time > s_until) return;
            s_until = 0f;
            d.m_amount += Crack;
            ModInd.Set(hero, UmbraelFx.GlazeInd, false);
            if (UmbraelFx.GlazeCrack != null) SystemPool.Spawn(UmbraelFx.GlazeCrack, hero.transform.position);
        }
    }
}
