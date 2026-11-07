using HarmonyLib;

namespace CrawlFurther.Content.Gods.Kaurn
{
    /// <summary>Every Kaurn monster (prefab name prefix "ModKrn") gets its static charge and arc end at Awake.</summary>
    [HarmonyPatch(typeof(Player), "Awake")]
    static class Patch_KaurnAwake
    {
        static void Postfix(Player __instance)
        {
            if (__instance == null || !__instance.gameObject.name.StartsWith("ModKrn")) return;
            if (__instance.GetComponent<KaurnUnit>() == null) __instance.gameObject.AddComponent<KaurnUnit>();
        }
    }
}
