using System.Collections.Generic;
using CrawlFurther.Items;
using CrawlFurther.Monsters;
using CrawlFurther.Util;

namespace ExampleGod
{
    /// <summary>
    /// Glimmer Volley, a shop spell. It is a copy of the vanilla Fetid Discharge (which fires three shots in a fan)
    /// whose shots are swapped for a hero-side copy of the Glimmer Grub's bolt.
    /// </summary>
    public static class GlimmerItems
    {
        public const string VolleyId = "SpellGlimmerVolley";

        public static readonly ItemDef Volley = new ItemDef
        {
            id = VolleyId,
            cloneFrom = "SpellFetidDischarge",
            group = "GroupSpellsPurchasable",
            name = "Glimmer Volley",
            description = "Fire a fan of 3 glimmer bolts, 0.45 damage each",
            cost = 40,
            bubbleArt = "IconGlimmerVolleyBubble",
            customize = (go, item) =>
            {
                // the hero's copy hits monsters; 0.6 x 0.75 = 0.45 damage
                var bolt = FxKit.Weakened(GlimmerFx.Bolt, "ModHeroGlimmerBolt", 0.75f);
                foreach (var slot in R.Get<List<DamageEffectData>>(item, "m_specialAttackDamageEffects")) slot.m_object = bolt;
            },
        };

        /// <summary>Build the spell. Called from the content pack, after <see cref="GlimmerFx.Build"/>.</summary>
        public static void Register()
        {
            ItemRegistry.Register(Volley);
        }
    }
}
