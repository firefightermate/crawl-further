using System;
using System.IO;
using System.Reflection;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using HarmonyLib;

namespace CrawlFurther
{
    /// <summary>A mod registered with <see cref="Further.AddMod"/>: its identity, folder, log, config and Harmony instance.</summary>
    public sealed class FurtherMod
    {
        /// <summary>The plugin's BepInEx GUID; also its Harmony id.</summary>
        public string Id { get; private set; }

        /// <summary>The plugin's display name.</summary>
        public string Name { get; private set; }

        /// <summary>The folder the plugin's DLL was loaded from. Its art/ subfolder is searched for sprite sheets.</summary>
        public string Dir { get; private set; }

        /// <summary>The plugin's assembly.</summary>
        public Assembly Assembly { get; private set; }

        /// <summary>The plugin's own BepInEx log.</summary>
        public ManualLogSource Log { get; private set; }

        /// <summary>The plugin's own config file (BepInEx/config/&lt;GUID&gt;.cfg). For a file of another name use <see cref="Further.Config"/>.</summary>
        public ConfigFile Config { get; private set; }

        /// <summary>A Harmony instance with the plugin's GUID as its id.</summary>
        public Harmony Harmony { get { return m_harmony ?? (m_harmony = new Harmony(Id)); } }

        Harmony m_harmony;

        internal Action Start;

        internal FurtherMod(BaseUnityPlugin plugin, Action start)
        {
            var meta = MetadataHelper.GetMetadata(plugin);
            Id = meta.GUID;
            Name = meta.Name;
            Assembly = plugin.GetType().Assembly;
            Dir = Path.GetDirectoryName(Assembly.Location);
            // BaseUnityPlugin.Logger is protected; reuse it rather than open a second source with the same name
            Log = (ManualLogSource)AccessTools.Property(typeof(BaseUnityPlugin), "Logger").GetValue(plugin, null);
            Config = plugin.Config;
            Start = start;
        }

        /// <summary>
        /// Apply every [HarmonyPatch] class in the mod's assembly, one class at a time so one bad patch cannot stop the
        /// others. Classes named in <paramref name="order"/> are applied first, in that order (at equal priority Harmony
        /// runs patches on the same method in the order they were applied); the rest follow sorted by full name.
        /// Call it from your start callback, not from Awake.
        /// </summary>
        public void PatchAll(params string[] order)
        {
            FurtherCore.PatchAll(Assembly, Harmony, order, Log);
        }
    }
}
