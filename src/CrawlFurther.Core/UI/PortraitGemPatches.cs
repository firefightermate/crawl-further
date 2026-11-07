using HarmonyLib;

namespace CrawlFurther.UI
{
    // Every menu picture of a monster goes through Player.SetupPortrait (a still) or SetupPortraitAnimRun (running): the
    // god select's starter boxes, the evolve menu's buttons, the HUD and the floor results. Each gets the mod gem there.
    // Vault cells are left out: the vault puts its own gem in the cell's corner.

    [HarmonyPatch(typeof(Player), "SetupPortrait")]
    static class Patch_PortraitGem
    {
        static void Postfix(exSprite portraitSprite) { PortraitGem.Attach(portraitSprite); }
    }

    [HarmonyPatch(typeof(Player), "SetupPortraitAnimRun")]
    static class Patch_PortraitRunGem
    {
        static void Postfix(exSprite portraitSprite) { PortraitGem.Attach(portraitSprite); }
    }

    static class PortraitGem
    {
        internal static void Attach(exSprite portrait)
        {
            try
            {
                if (portrait != null && portrait.GetComponentInParent<MenuItemLibraryMonster>() == null) ModGem.Attach(portrait);
            }
            catch (System.Exception e) { FurtherCore.Log.LogWarning("Portrait gem: " + e.Message); }
        }
    }
}
