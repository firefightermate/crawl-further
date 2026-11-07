using System.Collections.Generic;
using UnityEngine;
using CrawlFurther.Items;
using CrawlFurther.Monsters;
using CrawlFurther.Testing;

namespace ExampleGod
{
    /// <summary>A "Glimmer" page in the test panel (F2). Nothing is added unless test mode is on.</summary>
    public static class GlimmerTests
    {
        public static void Register()
        {
            if (!TestMode.On) return;
            TestMode.AddList("Glimmer", "Become a Glimmer monster", Bodies,
                item => TestGame.Become(TestMode.Player, (GameObject)item.Value));
            TestMode.AddList("Glimmer", "Spawn a hostile Glimmer monster", Bodies,
                item => TestGame.SpawnHostile((GameObject)item.Value));
            TestMode.AddAction("Glimmer", "Give the hero Glimmer Volley", () =>
            {
                Powerup volley;
                if (!ItemRegistry.Items.TryGetValue(GlimmerItems.VolleyId, out volley)) throw new TestModeException("Glimmer Volley was not built");
                TestGame.GiveItem(volley);
                TestMode.Say("The hero has Glimmer Volley");
            });
        }

        static IEnumerable<TestItem> Bodies()
        {
            foreach (var m in GlimmerPack.Monsters)
            {
                Player p;
                if (MonsterFactory.Built.TryGetValue(m.id, out p) && p != null) yield return new TestItem(m.id, p.gameObject);
            }
        }
    }
}
