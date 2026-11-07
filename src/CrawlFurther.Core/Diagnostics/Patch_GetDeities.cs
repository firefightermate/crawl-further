using System.Collections.Generic;
using HarmonyLib;

namespace CrawlFurther.Diagnostics
{
    /// <summary>Logs once that Core's patches reach the game: the first deity list it hands out, and its size.</summary>
    [HarmonyPatch(typeof(SystemDeity), "GetDeities")]
    static class Patch_GetDeities
    {
        static bool s_logged;

        static void Postfix(List<Deity> __result)
        {
            if (s_logged || __result == null) return;
            s_logged = true;
            FurtherCore.Log.LogInfo("[hook ok] SystemDeity.GetDeities -> " + __result.Count + " deities");
        }
    }
}
