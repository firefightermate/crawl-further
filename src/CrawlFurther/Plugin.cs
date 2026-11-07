using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using UnityEngine;

namespace CrawlFurther.Content
{
    using CrawlFurther.Monsters;

    [BepInPlugin(GUID, NAME, VERSION)]
    [BepInDependency(FurtherCore.GUID)]
    public class Plugin : BaseUnityPlugin
    {
        public const string GUID = "com.firefightermate.crawlfurther";
        public const string NAME = "Crawl: Further";   // display name only; BepInEx names the [Bosses] config file after GUID
        public const string VERSION = "1.0.1";

        public static Plugin I;
        internal static ManualLogSource Log;
        internal static string ModDir;

        float m_bannerTimer = 12f;
        static bool s_started;
        static FurtherMod s_mod;

        void Awake()
        {
            I = this;
            Log = Logger;
            useGUILayout = false;   // OnGUI only draws two labels: skip IMGUI's per-frame layout pass for the whole game
            ModDir = Path.GetDirectoryName(Info.Location);
            // Do NOT touch any game type here. On Unity 5.4, loading Assembly-CSharp before the engine has
            // registered its scripts breaks every MonoBehaviour in the game ("referenced script is missing").
            // Core calls OnGameReady once the game has booted.
            s_mod = Further.AddMod(this, OnGameReady);
            Log.LogInfo(NAME + " awake. Unity " + Application.unityVersion + ", dir " + ModDir);
        }

        void Update()
        {
            if (m_bannerTimer > 0f) m_bannerTimer -= Time.unscaledDeltaTime;
            if (!s_started) return;
            GameTick();
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        static void OnGameReady()
        {
            s_mod.PatchAll(PatchOrder);
            SheetScales.Register();
            ContentSetup.Install();
            if (CrawlFurther.Testing.TestMode.On) Testing.ContentTestActions.Register();
            s_started = true;
        }

        /// <summary>
        /// Patch classes that share a target method with another of ours (Health.Damage, Player.Awake and others), in the
        /// order they must run: at equal priority Harmony runs patches in the order they were applied.
        /// </summary>
        static readonly string[] PatchOrder =
        {
            "Patch_Items3PlayerAwake", "Patch_Items3HeroChange", "Patch_Items3Kill", "Patch_Items3Damage", "Patch_SilverAwake",
            "Patch_HeroKill", "Patch_UmbraelHits", "Patch_JinxHeroHits",
            "Patch_VhorrulHits", "Patch_GhostSlotsNewRun", "Patch_GhostSlotDamage", "Patch_SylveneHeroHits",
            "Patch_GoldDamage", "Patch_GoldSecretAwake", "Patch_StatueDamageOut", "Patch_StatueDamageIn", "Patch_StatueAwake",
            "Patch_WeaponRuntimeAwake", "Patch_WeaponHeroHit", "Patch_WeaponHandsMaterial", "Patch_ItemDamageTag",
            "Patch_OssHits", "Patch_ZhkHeroHits", "Patch_ZhkHeroStruck",
            "Patch_ZhekraMantisExecute", "Patch_ZhekraAwake", "Patch_GleanerValue", "Patch_KaurnAwake", "Patch_BelMoraHits",
            "Patch_SilverVariantFrames", "Patch_CustomGodInUse", "Patch_CustomPerkEcho",
        };

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        void GameTick()
        {
            if (Input.GetKeyDown(KeyCode.F10)) CycleBoss();
        }

        static int s_bossPick;
        static string s_note;
        static float s_noteTime;

        /// <summary>F10: force the next boss fight to be a mod boss (for testing), or go back to random.</summary>
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        static void CycleBoss()
        {
            var list = BossFactory.Built;
            if (list.Count == 0) return;   // bosses switched off
            s_bossPick = (s_bossPick + 1) % (list.Count + 1);
            BossFactory.Forced = s_bossPick == 0 ? null : list[s_bossPick - 1];
            s_note = "Next boss: " + (BossFactory.Forced == null ? "random" : BossFactory.Forced.GetDisplayName());
            s_noteTime = 4f;
            Log.LogInfo(s_note);
        }

        void OnGUI()
        {
            if (s_noteTime > 0f)
            {
                s_noteTime -= Time.unscaledDeltaTime;
                GUI.color = new Color(0.8f, 0.9f, 1f, Mathf.Clamp01(s_noteTime));
                GUI.Label(new Rect(8, 28, 900, 24), "(" + NAME + ") " + s_note);
            }
            if (m_bannerTimer <= 0f) return;
            GUI.color = new Color(1f, 0.85f, 0.4f, Mathf.Clamp01(m_bannerTimer));
            GUI.Label(new Rect(8, 6, 900, 24), NAME + " " + VERSION + " loaded: " + (s_started ? StatusText() : "starting") + (s_started && AnyModBoss() ? "  (F10: force a mod boss)" : ""));
            var test = s_started ? TestBanner() : null;
            if (test != null) GUI.Label(new Rect(8, 48, 900, 24), test);
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        static bool AnyModBoss() { return BossFactory.Built.Count > 0; }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        static string TestBanner() { return CrawlFurther.Testing.TestMode.Banner; }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
        static string StatusText()
        {
            return Further.Status;
        }
    }
}
