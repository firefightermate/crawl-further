using System;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using BepInEx.Configuration;

namespace CrawlFurther
{
    /// <summary>
    /// The entry point for mods built on Crawl Further Core: registration, content packs and config files. Game events
    /// are on <see cref="GameEvents"/>.
    /// <code>
    /// [BepInPlugin("com.you.mygod", "My God", "1.0.0")]
    /// [BepInDependency(FurtherCore.GUID)]
    /// public class MyGodPlugin : BaseUnityPlugin
    /// {
    ///     static FurtherMod s_mod;
    ///
    ///     void Awake() { s_mod = Further.AddMod(this, OnBooted); }   // no game types in Awake
    ///
    ///     static void OnBooted()
    ///     {
    ///         s_mod.PatchAll();
    ///         Further.AddPack("My God", MyGodPack.Register);
    ///         GameEvents.RoomChanged += room => s_mod.Log.LogInfo("Entered " + room.name);
    ///     }
    /// }
    /// </code>
    /// </summary>
    public static class Further
    {
        /// <summary>
        /// Register a mod built on Core. Call it from your plugin's Awake, which must not touch any game type (on Unity 5.4
        /// that breaks every script in the game). <paramref name="start"/> runs once the game has booted, in the order mods
        /// were added: apply your Harmony patches and add your packs there. Core adds the mod's art folder for you.
        /// </summary>
        public static FurtherMod AddMod(BaseUnityPlugin plugin, Action start)
        {
            var mod = new FurtherMod(plugin, start);
            FurtherCore.Register(mod);
            return mod;
        }

        /// <summary>
        /// Queue a content pack: <paramref name="register"/> runs once the game's systems are loaded (deities, monster
        /// prefabs), after the packs added before it. Build your gods, monsters and items there. A pack that throws is
        /// logged and skipped; the others still register.
        /// </summary>
        public static void AddPack(string name, Action register)
        {
            ContentManager.AddPack(name, register);
        }

        /// <summary>True once every pack has registered (just before <see cref="GameEvents.GameReady"/>).</summary>
        public static bool IsReady { get { return ContentManager.Registered; } }

        /// <summary>One line on how registration went: packs, monsters, failures and the self-test result.</summary>
        public static string Status { get { return ContentManager.Status; } }

        static readonly Dictionary<string, ConfigFile> s_configs = new Dictionary<string, ConfigFile>(StringComparer.OrdinalIgnoreCase);

        /// <summary>
        /// The config file BepInEx/config/<paramref name="fileName"/> (".cfg" is added when missing), shared by every caller
        /// that asks for the same name, so two parts of a mod never overwrite each other's entries. Created on first use.
        /// </summary>
        public static ConfigFile Config(string fileName)
        {
            if (!fileName.EndsWith(".cfg", StringComparison.OrdinalIgnoreCase)) fileName += ".cfg";
            ConfigFile cfg;
            if (!s_configs.TryGetValue(fileName, out cfg))
                s_configs[fileName] = cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, fileName), true);
            return cfg;
        }
    }
}
