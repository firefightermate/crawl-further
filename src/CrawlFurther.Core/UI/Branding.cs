using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Items;
    using CrawlFurther.Util;

    /// <summary>
    /// A mod's own branding on the game's menus (see <see cref="BrandingDef"/>): a wordmark pinned to the bottom right of
    /// every CRAWL logo the game shows, a version line on the title screen, and flame pips and drifting motes on the main
    /// menu. Nothing is drawn until a mod calls <see cref="Set"/>; the last call wins.
    ///
    /// Where the CRAWL logo appears (traced from the decompiled game and the scene dumps):
    ///  - SceneMenuMain, MenuMain/Title: one exSprite (scale 1.25, 160 x 90 cells of AtlasMenuMain) driven by an
    ///    AnimStateMachine. Frames 347-361 = logo high (main menu), 362-377 = spawn-in, 378-391 = logo low with
    ///    "insert coin" (title loop), 392-403 = moving up / outro, 404-421 = the Powerhoof splash. The wordmark follows
    ///    whichever frame is showing: high or low position, its Glitch anim while the logo glitches, hidden during
    ///    the splash and the transitions, and its In anim again when the logo settles.
    ///  - SceneMenuMain, MenuCredits/ScrollContainer/1Sprite: the logo (frame 379, scale 1) at the top of the credits.
    ///  - AtlasTutorial crawlTitle / shadowyLogo frames are never spawned by the shipped game: nothing to brand.
    /// </summary>
    public static class Branding
    {
        static BrandingDef s_def;
        static SpriteSheet s_wordmark, s_spark;

        /// <summary>Brand the menus. Call it when your mod starts.</summary>
        public static void Set(BrandingDef def)
        {
            s_def = def;
            s_wordmark = null; s_spark = null;
        }

        /// <summary>The branded name ("Crawl: Further"), or Core's own name when no mod has set one.</summary>
        public static string DisplayName { get { return s_def != null && !string.IsNullOrEmpty(s_def.name) ? s_def.name : FurtherCore.NAME; } }
        /// <summary>The branded version, or Core's own.</summary>
        public static string Version { get { return s_def != null && !string.IsNullOrEmpty(s_def.version) ? s_def.version : FurtherCore.VERSION; } }
        /// <summary>The title screen's version line: "Crawl: Further 1.0.0".</summary>
        public static string Versioned { get { return DisplayName + " " + Version; } }

        internal static SpriteSheet Wordmark { get { if (s_wordmark == null && s_def != null && s_def.wordmark != null) s_wordmark = SpriteSheets.Get(s_def.wordmark); return s_wordmark; } }
        internal static SpriteSheet Spark { get { if (s_spark == null && s_def != null && s_def.spark != null) s_spark = SpriteSheets.Get(s_def.spark); return s_spark; } }
        internal static SpriteSheet MenuPip { get { return s_def != null && s_def.menuPip != null ? SpriteSheets.Get(s_def.menuPip) : null; } }
        internal static SpriteSheet MenuMote { get { return s_def != null && s_def.menuMote != null ? SpriteSheets.Get(s_def.menuMote) : null; } }
        internal static bool HasVersionLine { get { return s_def != null && !string.IsNullOrEmpty(s_def.name); } }

        /// <summary>Self-test: the branding sheets and every anim the code plays, the vault art, the mod category pages,
        /// leftover "(MOD)" tags, the music and the secrets.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            var need = new List<KeyValuePair<string, string[]>>();
            if (s_def != null)
            {
                if (s_def.wordmark != null) need.Add(new KeyValuePair<string, string[]>(s_def.wordmark, new[] { "Idle", "Glitch", "In", "Out" }));
                if (s_def.spark != null) need.Add(new KeyValuePair<string, string[]>(s_def.spark, new[] { "Rise" }));
                if (s_def.menuPip != null) need.Add(new KeyValuePair<string, string[]>(s_def.menuPip, new[] { "Burn" }));
                if (s_def.menuMote != null) need.Add(new KeyValuePair<string, string[]>(s_def.menuMote, MenuRefresh.MoteAnims));
            }
            need.Add(new KeyValuePair<string, string[]>("VaultIcons", new[] { "Undiscovered", "NoArt", "Locked" }));
            foreach (var c in Vault.Categories)
                if (!string.IsNullOrEmpty(c.stamp)) need.Add(new KeyValuePair<string, string[]>(c.stamp, new string[0]));
            foreach (var kv in need)
            {
                var sh = SpriteSheets.Get(kv.Key);
                if (sh == null) { bad(kv.Key + " art missing"); continue; }
                foreach (var a in kv.Value) if (!sh.Has(a)) bad(kv.Key + " has no " + a + " anim");
            }
            if (AccessTools.Field(typeof(MenuMain), "m_menuMain") == null) bad("MenuMain.m_menuMain not found");
            if (AccessTools.Field(typeof(MenuCredits), "m_scrollContainer") == null) bad("MenuCredits.m_scrollContainer not found");
            LibraryEntries.SelfCheck(bad);
            NoModTags(bad);
            ModMusic.SelfCheck(bad);
            Secrets.SelfCheck(bad);
            ModMark.SelfCheck(bad);
        }

        /// <summary>Nothing players read carries a "(MOD)" / "[MOD]" tag (the violet gem marks mod things): shop items,
        /// weapons and their combos, mod gods' texts, every vault entry and every monster tip.</summary>
        public static void NoModTags(Action<string> bad)
        {
            Func<string, bool> tagged = t => !string.IsNullOrEmpty(t) && (t.Contains("(MOD)") || t.Contains("[MOD]"));
            foreach (var kv in ItemRegistry.Items)
                if (kv.Value != null && (tagged(kv.Value.GetDisplayName()) || tagged(kv.Value.GetDescription()))) bad("item " + kv.Key + " still tagged");
            foreach (var kv in ItemRegistry.Weapons)
            {
                var w = kv.Value;
                if (w == null) continue;
                if (tagged(w.m_weaponName) || tagged(w.m_weaponDescription)) bad("weapon " + kv.Key + " still tagged");
                if (w.m_combos != null) foreach (var c in w.m_combos) if (c != null && (tagged(c.m_name) || tagged(c.m_description))) bad("weapon " + kv.Key + " combo still tagged");
            }
            foreach (var g in DeityFactory.BuiltNames)
            {
                var d = SystemDeity.GetDeity(g);
                if (d != null && tagged(R.Get<string>(d, "m_text"))) bad("god " + g + " text still tagged");
            }
            if (Singleton<SystemLibrary>.HasInstance())
                foreach (var e in R.Get<List<SystemLibrary.LibraryEntry>>(Singleton<SystemLibrary>.Instance, "m_entryList"))
                    if (e != null && (tagged(e.m_name) || tagged(e.m_description))) bad("vault entry " + e + " still tagged");
            foreach (var key in TipRegistry.VaultOrder)
            {
                MonsterTip t;
                if (TipRegistry.TryGet(key, out t) && (tagged(t.name) || tagged(t.attack) || tagged(t.special) || tagged(t.passive))) bad("tip " + key + " still tagged");
            }
        }

        /// <summary>A plain exSprite child (mesh + renderer) on the parent's layer, showing frame 0 of a sheet.</summary>
        public static exSprite MakeSprite(string name, Transform parent, SpriteSheet sheet, Vector3 localPos)
        {
            var go = new GameObject(name);
            go.layer = parent.gameObject.layer;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();
            var s = go.AddComponent<exSprite>();
            s.anchor = exPlane.Anchor.MidCenter;
            s.useTextureOffset = false;
            s.SetSprite(sheet.atlas, 0);
            go.GetComponent<Renderer>().sharedMaterial = sheet.atlas.material;
            return s;
        }
    }

    [HarmonyPatch(typeof(MenuMain), "Start")]
    static class Patch_BrandTitle
    {
        static void Postfix(MenuMain __instance)
        {
            if (!UiSettings.Wordmark || Branding.Wordmark == null) return;
            try
            {
                var t = __instance.transform.Find("Title");
                var spr = t != null ? t.GetComponent<exSprite>() : null;
                if (spr != null) TitleWordmark.AttachTitle(spr);
                else FurtherCore.Log.LogWarning("Branding: MenuMain has no Title sprite");
            }
            catch (Exception e) { FurtherCore.Log.LogError("Branding title: " + e); }
        }
    }

    /// <summary>The CRAWL logo at the top of the credits (frame 379, scale 1): the wordmark at 0.8, the same size relative
    /// to the logo as on the title (letters end at x 43, bottom y -16 there).</summary>
    [HarmonyPatch(typeof(MenuCredits), "OnEnable")]
    static class Patch_BrandCredits
    {
        static void Postfix(MenuCredits __instance)
        {
            if (!UiSettings.Wordmark || Branding.Wordmark == null) return;
            try
            {
                var box = R.Get<GameObject>(__instance, "m_scrollContainer");
                if (box == null) return;
                foreach (var s in box.GetComponentsInChildren<exSprite>(true))
                {
                    if (s.atlas == null || s.atlas.name != "AtlasMenuMain" || s.index < 347 || s.index > 391) continue;
                    if (s.GetComponent<TitleWordmark>() != null) continue;
                    float k = s.scale.x;   // 1 in the shipped scene
                    TitleWordmark.AttachStatic(s.transform, new Vector3(33f * k, -8.5f * k, -0.5f), 0.8f * k);
                }
            }
            catch (Exception e) { FurtherCore.Log.LogError("Branding credits: " + e); }
        }
    }
}
