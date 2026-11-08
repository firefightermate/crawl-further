using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Testing
{
    // The game hooks behind test mode. Prepare keeps every one of them out of the game unless test mode is on.

    /// <summary>The game's debug keys stay usable, except the two that wipe the save (Tab + Delete, Tab + Shift + U).</summary>
    [HarmonyPatch(typeof(SystemMain), "UpdateDebugKeys")]
    static class Patch_TestWipeKeys
    {
        static bool Prepare() { return TestMode.On; }

        static bool Prefix()
        {
            if (!VanillaDebug.WipeKeyDown()) return true;
            TestMode.Say("That debug key would wipe your save: blocked in test mode");
            return false;
        }
    }

    /// <summary>
    /// The game locks the cursor to the middle of the screen every frame for its mouse aiming (SystemInput.UpdateMouseInput),
    /// so IMGUI never sees it move. While the panel is open the mouse is the panel's: the cursor is freed and shown, and
    /// the game's mouse aiming waits.
    /// </summary>
    [HarmonyPatch(typeof(SystemInput), "UpdateMouseInput")]
    static class Patch_TestPanelMouse
    {
        static bool Prepare() { return TestMode.On; }

        static bool Prefix()
        {
            if (!TestPanel.IsOpen) return true;
            if (Cursor.lockState != CursorLockMode.None) Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
            return false;
        }
    }

    /// <summary>Open everything for the session: everything the game keeps locked reads as open. Nothing is written.</summary>
    [HarmonyPatch(typeof(SystemUnlocks), "GetLocked", new[] { typeof(string) })]
    static class Patch_TestUnlocked
    {
        static bool Prepare() { return TestMode.On; }

        static bool Prefix(ref bool __result)
        {
            if (!TestCheats.UnlockAll || !TestMode.Active) return true;
            __result = false;
            return false;
        }
    }

    /// <summary>Open everything for the session also finds every vault entry (monsters, weapons, items, objects), so any
    /// monster's challenge can be started from the vault. Nothing is written.</summary>
    [HarmonyPatch]
    static class Patch_TestVaultAllFound
    {
        static bool Prepare() { return TestMode.On; }

        static System.Reflection.MethodBase TargetMethod()
        {
            return AccessTools.Method(AccessTools.Inner(typeof(SystemLibrary), "LibraryEntry"), "IsFound");
        }

        static bool Prefix(ref bool __result)
        {
            if (!TestCheats.UnlockAll || !TestMode.Active) return true;
            __result = true;
            return false;
        }
    }

    /// <summary>Test play finds nothing for the vault: becoming or spawning a monster must not mark it found in the save.</summary>
    [HarmonyPatch(typeof(SystemLibrary), "OnEntryFound", new[] { typeof(PlayerData), typeof(GameObject), typeof(string) })]
    static class Patch_TestNoVaultFinds
    {
        static bool Prepare() { return TestMode.On; }

        static bool Prefix() { return !TestMode.Active; }
    }

    /// <summary>Test play wins no challenges: a vault challenge's score (any monster's) is not written to the save.</summary>
    [HarmonyPatch(typeof(SystemLibrary), "SetChallengeScore")]
    static class Patch_TestNoChallengeScores
    {
        static bool Prepare() { return TestMode.On; }

        static bool Prefix(int score)
        {
            if (!TestMode.Active) return true;
            TestMode.Say("Challenge level " + score + " not recorded: test mode is on");
            return false;
        }
    }

    /// <summary>Frozen AI: room monsters with their own AI stop thinking...</summary>
    [HarmonyPatch(typeof(PlayerAI), "Update")]
    static class Patch_TestFreezeAI
    {
        static bool Prepare() { return TestMode.On; }

        static bool Prefix() { return !TestCheats.FreezeAI; }
    }

    /// <summary>...stand still...</summary>
    [HarmonyPatch(typeof(PlayerAI), "GetMoveRatio")]
    static class Patch_TestFreezeAIMove
    {
        static bool Prepare() { return TestMode.On; }

        static void Postfix(ref float __result) { if (TestCheats.FreezeAI) __result = 0f; }
    }

    /// <summary>...and start no attacks.</summary>
    [HarmonyPatch(typeof(PlayerAI), "GetAttackToStart")]
    static class Patch_TestFreezeAIAttack
    {
        static bool Prepare() { return TestMode.On; }

        static void Postfix(ref int __result) { if (TestCheats.FreezeAI) __result = -1; }
    }

    /// <summary>Frozen AI: bots press nothing...</summary>
    [HarmonyPatch(typeof(Bot), "Update")]
    static class Patch_TestFreezeBot
    {
        static bool Prepare() { return TestMode.On; }

        static bool Prefix() { return !TestCheats.FreezeAI; }
    }

    /// <summary>...and the stick they last held is let go.</summary>
    [HarmonyPatch(typeof(PlayerBotData), "GetInputMove")]
    static class Patch_TestFreezeBotMove
    {
        static bool Prepare() { return TestMode.On; }

        static void Postfix(ref Vector2 __result) { if (TestCheats.FreezeAI) __result = Vector2.zero; }
    }
}
