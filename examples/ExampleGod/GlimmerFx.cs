using UnityEngine;
using CrawlFurther.Monsters;

namespace ExampleGod
{
    /// <summary>
    /// The effect templates the Glimmer monsters and the Glimmer Volley spell spawn. Build them once, from the content
    /// pack, before the monsters that use them. Damage is in the game's health units (the hero starts with 5 to 7),
    /// speeds in pixels per second, times in seconds.
    /// </summary>
    public static class GlimmerFx
    {
        /// <summary>Melee hitboxes: invisible boxes that live for a moment where the move lands.</summary>
        public static GameObject Bite, DashHit, Burst, DiveHit;

        /// <summary>Projectiles drawn with FxGlimmerBolt.</summary>
        public static GameObject Bolt, Spark;

        /// <summary>The god's perk: a small cloud left where a Glimmer monster dies. It hurts the hero.</summary>
        public static GameObject Wisp;

        public static void Build()
        {
            Bite = Hitbox("ModGlimmerBite", damage: 0.8f, knock: 0.5f, life: 0.15f, w: 12f, h: 11f);
            DashHit = Hitbox("ModGlimmerDashHit", damage: 0.7f, knock: 0.8f, life: 0.5f, w: 13f, h: 11f);
            DiveHit = Hitbox("ModGlimmerDiveHit", damage: 1f, knock: 0.6f, life: 0.45f, w: 13f, h: 10f);

            // a ring around the grub's body: it does not turn with the aim
            Burst = FxKit.BodyHit("ModGlimmerBurst", 0.8f, 0.3f, 0.9f, 0.12f);
            Strike.HitBox(Burst, 24f, 12f);

            Bolt = FxKit.Projectile("ModGlimmerBolt", "DFX_skelMageNewProjectile", "FxGlimmerBolt", "Fly",
                                    speed: 150f, life: 1.5f, damage: 0.6f, knock: 0.4f);
            Spark = FxKit.Projectile("ModGlimmerSpark", "DFX_skelMageNewProjectile", "FxGlimmerBolt", "Fly",
                                     speed: 110f, life: 1.2f, damage: 0.5f, knock: 0.2f, status: ModStatus.Daze, statusChance: 0.3f);

            Wisp = FxKit.Cloud("ModGlimmerWisp", "FxGlimmerWisp", "Play", speed: 0f, damage: 0.3f, rate: 0.5f,
                               status: null, statusChance: 0f, durations: new[] { 0.12f, 0.2f, 0.3f, 0.3f, 0.3f });
            if (Wisp != null)
            {
                Strike.Collider(Wisp, 14f, 12f);
                Strike.ArtAt(Wisp, "FxGlimmerWisp", 10, 14);
            }
        }

        /// <summary>A melee box that turns toward where the monster aims, so it can bite up and down too.</summary>
        static GameObject Hitbox(string name, float damage, float knock, float life, float w, float h)
        {
            var go = FxKit.BodyHit(name, damage, rate: 0.3f, knock: knock, life: life);
            AimedMelee.Rotating(go);
            Strike.HitBox(go, w, h);
            return go;
        }
    }
}
