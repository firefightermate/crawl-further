using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther
{
    /// <summary>
    /// The Crawl Further Core BepInEx plugin. Mods do not use this class: they register through <see cref="Further.AddMod"/>,
    /// and add <c>[BepInDependency(FurtherCore.GUID)]</c> so BepInEx loads Core first.
    /// </summary>
    [BepInPlugin(GUID, NAME, VERSION)]
    public class FurtherCore : BaseUnityPlugin
    {
        /// <summary>Core's BepInEx GUID, for <c>[BepInDependency(FurtherCore.GUID)]</c>.</summary>
        public const string GUID = "com.firefightermate.crawlfurther.core";
        /// <summary>Core's display name.</summary>
        public const string NAME = "Crawl Further Core";
        /// <summary>Core's version.</summary>
        public const string VERSION = "1.0.0";

        internal static ManualLogSource Log;
        /// <summary>The folder this DLL was loaded from (BepInEx/plugins/CrawlFurther).</summary>
        internal static string ModDir;

        /// <summary>Mods whose start callback threw, with the error. The self-test reports each one.</summary>
        internal static readonly System.Collections.Generic.List<string> FailedStarts = new System.Collections.Generic.List<string>();
        /// <summary>Patch classes that failed to apply, "assembly: class: error" (the self-test lists them).</summary>
        internal static readonly System.Collections.Generic.List<string> FailedPatches = new System.Collections.Generic.List<string>();

        static readonly List<FurtherMod> s_mods = new List<FurtherMod>();
        bool m_started;
        int m_frames;

        internal static void Register(FurtherMod mod) { s_mods.Add(mod); }

        /// <summary>Core's assembly and every registered mod's (self-test scans, patch ownership checks).</summary>
        internal static IEnumerable<Assembly> Assemblies
        {
            get
            {
                yield return typeof(FurtherCore).Assembly;
                foreach (var m in s_mods) yield return m.Assembly;
            }
        }

        /// <summary>True for Core's Harmony id and every registered mod's.</summary>
        internal static bool IsOurHarmonyId(string id)
        {
            if (id == GUID) return true;
            foreach (var m in s_mods) if (m.Id == id) return true;
            return false;
        }

        void Awake()
        {
            Log = Logger;
            useGUILayout = false;   // OnGUI is not used: skip IMGUI's per-frame layout pass for this component
            ModDir = Path.GetDirectoryName(Info.Location);
            // Do NOT touch any game type here. On Unity 5.4, loading Assembly-CSharp before the engine has
            // registered its scripts breaks every MonoBehaviour in the game ("referenced script is missing").
            Log.LogInfo(NAME + " awake. Unity " + Application.unityVersion + ", dir " + ModDir);
        }

        void Update()
        {
            if (!m_started)
            {
                // wait until the game has booted its first scene before touching its code
                if (++m_frames < 10) return;
                m_started = true;
                StartGameHooks();
                return;
            }
            GameTick();
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        void StartGameHooks()
        {
            Art.SpriteSheets.AddFolder(ModDir);
            // before the mods start, so Core's test panel pages come first and mods can add to them
            Testing.TestMode.Start();
            // Mods first, then Core: at equal priority Harmony runs patches in the order they were applied, and mods'
            // patches on methods Core also patches must keep running first.
            FailedStarts.Clear();
            foreach (var m in s_mods)
            {
                Art.SpriteSheets.AddFolder(m.Dir);
                try { if (m.Start != null) m.Start(); }
                catch (Exception e)
                {
                    FailedStarts.Add(m.Id + ": " + e.GetType().Name + " " + e.Message);
                    Log.LogError("Starting " + m.Id + " failed: " + e);
                }
            }
            PatchAll(typeof(FurtherCore).Assembly, new Harmony(GUID), PatchOrder, Log);
        }

        /// <summary>
        /// Core's patch classes that share a target method with another of its patches, in the order they must run.
        /// These go first, the rest by name. Renaming one of these classes means renaming it here too.
        /// </summary>
        static readonly string[] PatchOrder =
        {
            "Patch_StrikeSpawnOffset", "Patch_ObjectsGameStart", "Patch_ObjectsHeroChange", "Patch_ObjectsTrapEnter",
            "Patch_TipsInitAsPlayer", "Patch_TipsTrap", "Patch_StatusAdd", "Patch_StatusRemove", "Patch_UnlockEcto",
            "Patch_HeroGearInitAsPlayer", "Patch_PlayerAwake", "Patch_HealthDamage", "Patch_SpawnEffectEcho",
            "Patch_PlayerDataSetDeity", "Patch_HeroLooksSetDeity", "Patch_HeroLooksInitAsPlayer", "Patch_HeroLooksRemoveStatus",
            "Patch_MenuRefresh", "Patch_BrandTitle", "Patch_LibraryCellAction", "Patch_LibraryItemText", "Patch_VaultUpdateItem",
            "Patch_VaultCellAction", "Patch_VaultPortraitGem",
            "Patch_TestWipeKeys", "Patch_TestPanelMouse", "Patch_TestUnlocked", "Patch_TestNoVaultFinds", "Patch_TestFreezeAI", "Patch_TestFreezeAIMove",
            "Patch_TestFreezeAIAttack", "Patch_TestFreezeBot", "Patch_TestFreezeBotMove",
        };

        /// <summary>
        /// Apply every [HarmonyPatch] class of <paramref name="assembly"/>, class by class, so one bad patch can't take
        /// the others down with it. Classes named in <paramref name="order"/> go first, in that order; the rest follow
        /// sorted by full name, so the order never depends on how the source files are laid out.
        /// </summary>
        internal static void PatchAll(Assembly assembly, Harmony harmony, IList<string> order, ManualLogSource log)
        {
            var types = new List<Type>();
            foreach (var t in assembly.GetTypes())
                if (t.GetCustomAttributes(typeof(HarmonyPatch), false).Length > 0) types.Add(t);
            Func<Type, int> rank = t => { int i = order != null ? order.IndexOf(t.Name) : -1; return i < 0 ? int.MaxValue : i; };
            types.Sort((a, b) =>
            {
                int ra = rank(a), rb = rank(b);
                return ra != rb ? ra.CompareTo(rb) : string.CompareOrdinal(a.FullName, b.FullName);
            });
            int ok = 0, bad = 0;
            foreach (var t in types)
            {
                try { harmony.CreateClassProcessor(t).Patch(); ok++; }
                catch (Exception e)
                {
                    bad++;
                    log.LogError("Patch " + t.Name + " failed: " + e.Message);
                    FailedPatches.Add(assembly.GetName().Name + ": " + t.Name + ": " + e.Message);
                }
            }
            log.LogInfo("Harmony patches applied (" + assembly.GetName().Name + "): " + ok + " ok, " + bad + " failed");
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        void GameTick()
        {
            ContentManager.Tick();
            Diagnostics.DevKeys.Tick();
        }
    }
}
