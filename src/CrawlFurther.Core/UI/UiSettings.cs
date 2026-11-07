using System;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using UnityEngine;

namespace CrawlFurther.UI
{
    /// <summary>BepInEx/config/CrawlFurther.UI.cfg: the player's switches for Core's menu additions (all on by default).</summary>
    public static class UiSettings
    {
        static bool s_init;
        static bool s_wordmark = true, s_dressing = true, s_vaultGrid = true, s_music = true, s_musicTitle;
        static float s_musicChance = 0.34f, s_musicVolume = 1f;

        static void Init()
        {
            if (s_init) return;
            s_init = true;
            try
            {
                var cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, "CrawlFurther.UI.cfg"), true);
                s_wordmark = cfg.Bind("Menus", "FurtherWordmark", true, "Show the mod wordmark next to the CRAWL logo (title screen and credits).").Value;
                s_dressing = cfg.Bind("Menus", "MenuDressing", true, "Title screen embers, the markers beside the selected main menu item, and the mod version line.").Value;
                s_music = cfg.Bind("Music", "CustomMusic", true, "Rotate the music tracks mods add in with the game's own music.").Value;
                s_musicChance = Mathf.Clamp01(cfg.Bind("Music", "CustomMusicChance", 0.34f, "Chance (0 to 1) that a new piece of gameplay music is a mod track instead of the game's own.").Value);
                s_musicTitle = cfg.Bind("Music", "CustomMusicOnTitle", false, "Also roll for a mod track on the title screen and menus.").Value;
                s_musicVolume = Mathf.Clamp(cfg.Bind("Music", "CustomMusicVolume", 1f, "Loudness of the mod tracks next to the game's own (1 = as mixed; the game's music volume setting applies on top).").Value, 0f, 2f);
                s_vaultGrid = cfg.Bind("Menus", "VaultGrid", true, "Show weapons, items, objects and the mod categories of the vault as picture grids (off: the old text lists).").Value;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("UI settings: " + e.Message); }
        }

        public static bool Wordmark { get { Init(); return s_wordmark; } }
        public static bool MenuDressing { get { Init(); return s_dressing; } }
        public static bool VaultGrid { get { Init(); return s_vaultGrid; } }
        public static bool CustomMusic { get { Init(); return s_music; } }
        public static float CustomMusicChance { get { Init(); return s_musicChance; } }
        public static bool CustomMusicOnTitle { get { Init(); return s_musicTitle; } }
        public static float CustomMusicVolume { get { Init(); return s_musicVolume; } }
    }
}
