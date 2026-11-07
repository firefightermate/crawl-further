using System.IO;
using UnityEngine;

namespace CrawlFurther.Diagnostics
{
    using CrawlFurther.Art;

    /// <summary>
    /// Developer hotkeys, off for players: they work only with DebugKeys = true in BepInEx/config/CrawlMod.Debug.cfg.
    /// F8 exports every loaded atlas and clip (<see cref="Ex2DExport.All"/>) to the plugin folder's ex2d_export;
    /// F9 toggles a red/blue swap of the hero and monster atlases, a check that runtime atlas swaps reach every clip.
    /// </summary>
    static class DevKeys
    {
        static bool? s_enabled;

        static bool Enabled
        {
            get
            {
                if (s_enabled == null)
                {
                    try
                    {
                        s_enabled = Further.Config("CrawlMod.Debug.cfg").Bind("General", "DebugKeys", false,
                            "Developer hotkeys F8 (export all ex2D atlases and clips) and F9 (tint test). Leave off.").Value;
                    }
                    catch { s_enabled = false; }
                }
                return s_enabled.Value;
            }
        }

        public static void Tick()
        {
            if (!Enabled) return;
            if (Input.GetKeyDown(KeyCode.F8)) Ex2DExport.All(Path.Combine(FurtherCore.ModDir, "ex2d_export"));
            if (Input.GetKeyDown(KeyCode.F9)) TintTest.Toggle();
        }
    }
}
