using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Compat;

    /// <summary>
    /// The boss-unleashed menu scene (shown when the heroes lose) is built from vanilla scene art. When the boss that
    /// won was a mod boss, its redrawn frames are swapped in for the duration of that scene (the vanilla clips are
    /// edited in place there, so every edit is undone before the next scene loads).
    /// </summary>
    internal static class BossScene
    {
        public static BossArt LastLost;
        static readonly List<KeyValuePair<exSpriteAnimClip.FrameInfo, exAtlas>> s_undo = new List<KeyValuePair<exSpriteAnimClip.FrameInfo, exAtlas>>();

        static bool s_hooked;

        /// <summary>Dress the scene; <paramref name="host"/> gets a guard that undoes it when the scene object dies.</summary>
        public static void Dress(GameObject host)
        {
            var art = LastLost;
            if (art == null || art.atlas == null || s_undo.Count > 0) return;
            // every way out of the scene undoes the edit: the guard's OnDestroy, the next scene load (some code calls
            // SceneManager.LoadScene directly, e.g. MenuMain / SystemUsers), and the SystemMain.LoadLevel prefixes
            if (host != null && host.GetComponent<BossSceneGuard>() == null) host.AddComponent<BossSceneGuard>();
            if (!s_hooked) { UnityEngine.SceneManagement.SceneManager.sceneLoaded += (sc, mode) => Undress(); s_hooked = true; }
            int sprites = 0;
            foreach (var anim in UnityEngine.Object.FindObjectsOfType<exSpriteAnimation>())
                foreach (var c in anim.animations)
                    if (c != null)
                        foreach (var f in c.frameInfos)
                            if (art.Has(f.atlas, f.index)) { s_undo.Add(new KeyValuePair<exSpriteAnimClip.FrameInfo, exAtlas>(f, f.atlas)); f.atlas = art.atlas; }
            foreach (var s in UnityEngine.Object.FindObjectsOfType<exSprite>())
                if (art.Has(s.atlas, s.index)) { s.SetSprite(art.atlas, s.index); sprites++; }
            FurtherCore.Log.LogInfo("Boss scene dressed with " + art.sheet + ": " + s_undo.Count + " frames, " + sprites + " sprites");
        }

        public static void Undress()
        {
            if (s_undo.Count == 0) return;
            foreach (var kv in s_undo) kv.Key.atlas = kv.Value;
            FurtherCore.Log.LogInfo("Boss scene undressed: " + s_undo.Count + " vanilla frames restored");
            s_undo.Clear();
        }
    }

    /// <summary>Lives on the boss-unleashed scene's menu object: when it goes, the vanilla clips are restored.</summary>
    internal class BossSceneGuard : MonoBehaviour
    {
        void OnDestroy() { BossScene.Undress(); }
    }

    [HarmonyPatch(typeof(Boss), "GetBossUnleashedSceneName")]
    static class Patch_BossUnleashedScene
    {
        static void Postfix(Boss __instance)
        {
            BossArt a;
            BossScene.LastLost = __instance != null && BossFactory.ArtOf.TryGetValue(__instance, out a) ? a : null;
        }
    }

    [HarmonyPatch(typeof(MenuBoss), "Start")]
    static class Patch_MenuBossStart
    {
        static void Postfix(MenuBoss __instance) { try { BossScene.Dress(__instance != null ? __instance.gameObject : null); } catch (Exception e) { FurtherCore.Log.LogError(e); } }
    }

    [HarmonyPatch(typeof(MenuBossHydraParts), "Start")]
    static class Patch_MenuBossHydraPartsStart
    {
        static void Postfix(MenuBossHydraParts __instance) { try { BossScene.Dress(__instance != null ? __instance.gameObject : null); } catch (Exception e) { FurtherCore.Log.LogError(e); } }
    }

    // Crawl Online also prefixes LoadLevel (and skips it on a client): run after it and only when the load goes ahead
    [HarmonyPatch(typeof(SystemMain), "LoadLevel", new[] { typeof(string) })]
    [HarmonyAfter(CompatOnline.Guid)]
    static class Patch_LoadLevelUndress
    {
        static void Prefix(bool __runOriginal) { if (__runOriginal) BossScene.Undress(); }
    }

    [HarmonyPatch(typeof(SystemMain), "LoadLevel", new[] { typeof(int) })]
    [HarmonyAfter(CompatOnline.Guid)]
    static class Patch_LoadLevelUndressId
    {
        static void Prefix(bool __runOriginal) { if (__runOriginal) BossScene.Undress(); }
    }
}
