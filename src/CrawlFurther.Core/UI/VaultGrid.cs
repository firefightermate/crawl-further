using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The vault (MenuLibrary) with every category as a picture grid, like the monster one.
    ///
    /// Vanilla: MONSTERS uses m_menuItemsMonster (6 columns of MenuItemLibraryMonster cells, 3 rows visible, scrolling);
    /// WEAPONS / ITEMS / OBJECTS use m_menuItems, a numbered text list; QUESTS is already an icon grid. Here WEAPONS,
    /// ITEMS, OBJECTS and the mod categories (<see cref="Vault.AddCategory"/>) fill the monster grid instead, one cell per
    /// entry, in state "Monster":
    ///  - each cell shows the entry's own picture (weapon: the hero in its stance; item: its shop bubble; object: the
    ///    picture the vault shows big; mod pages: the portrait), fitted into the cell's 12 x 12 box; undiscovered
    ///    entries show a drawn sealed "?" (VaultIcons) and locked pages a padlock;
    ///  - selection, the "new" dot, mouse hover, scrolling and the big picture below are the vanilla ones: UpdateItem
    ///    runs unchanged except that, for these categories, it reads the grid's selection (m_menuItems is pointed at the
    ///    grid for the duration of the call). The entry's name goes above its description in the vault's heading font
    ///    (the achievement title text, moved), and the description is laid out with <see cref="TextFit"/> so it never
    ///    runs under the BACK button;
    ///  - pressing a cell does nothing (vanilla list rows did nothing either); only monster cells start a challenge;
    ///  - the mouse wheel and Page Up / Page Down scroll any vault grid (monsters included) by rows.
    /// Mod categories are listed before BACK, numbered after the vanilla ones (5, 6, ...), each with its own stamp and
    /// summary. CrawlFurther.UI.cfg VaultGrid = false puts the vanilla lists back (and hides the mod categories).
    /// </summary>
    public static class VaultGrid
    {
        public const int Monsters = 0, Weapons = 1, Items = 2, Objects = 3, Achievements = 4, FirstMod = 5;
        const string ModMessage = "MsgCategoryMod";
        const float Box = 10f;          // a picture is fitted to this square inside the 12 x 12 cell ...
        const float MinScale = 0.5f;    // ... but never drawn smaller than half size (bigger art is clipped to the cell, like monsters)
        const float StanceScale = 0.8f; // weapon cells: the hero in that weapon's stance, at the monster cells' 0.8

        internal static readonly HashSet<int> Cells = new HashSet<int>();
        /// <summary>The mod categories listed in the vault, in menu order (category FirstMod + index).</summary>
        static readonly List<VaultCategory> s_listed = new List<VaultCategory>();
        static Type s_catType;
        static MethodInfo s_getEntries, s_setMonsterNull;
        static SpriteSheet s_icons;

        public static Type CatType { get { if (s_catType == null) s_catType = AccessTools.Inner(typeof(MenuLibrary), "eCategory"); return s_catType; } }
        public static int Category(MenuLibrary lib) { return Convert.ToInt32(R.Get<object>(lib, "m_category")); }
        public static bool IsGridCategory(int c) { return c == Weapons || c == Items || c == Objects || CategoryOf(c) != null; }
        public static bool ShowAchievements() { return SystemAchievements.Enabled && Constants.Platform == ePlatform.PC; }

        /// <summary>The mod category with this number, or null.</summary>
        public static VaultCategory CategoryOf(int c)
        {
            int i = c - FirstMod;
            return i >= 0 && i < s_listed.Count ? s_listed[i] : null;
        }

        internal static VaultCategory CategoryOf(string label)
        {
            foreach (var c in s_listed) if (c.label == label) return c;
            return null;
        }

        internal static int NumberOf(VaultCategory c) { int i = s_listed.IndexOf(c); return i < 0 ? -1 : FirstMod + i; }

        internal static bool AnyListed { get { return s_listed.Count > 0; } }

        static SpriteSheet Icons { get { if (s_icons == null) s_icons = SpriteSheets.Get("VaultIcons"); return s_icons; } }

        public static List<SystemLibrary.LibraryEntry> Entries(MenuLibrary lib, int cat)
        {
            if (s_getEntries == null) s_getEntries = AccessTools.Method(typeof(MenuLibrary), "GetCategoryEntries");
            return s_getEntries.Invoke(lib, new[] { Enum.ToObject(CatType, cat) }) as List<SystemLibrary.LibraryEntry>;
        }

        // ------------------------------------------------------------------ the mod category items
        /// <summary>MenuLibrary.Awake: list the mod categories that have pages before BACK (the category menu initialises
        /// in its own Start, later). The vanilla "new" loop asks for each item's entries by its index, so the categories
        /// are numbered in the order they are listed.</summary>
        internal static void OnAwake(MenuLibrary lib)
        {
            ModMark.OwnedBy<MenuItemLibraryMonster>();   // a cell's gem is its own (CellGem), never the portrait's
            if (lib.GetComponent<VaultGridDriver>() == null) lib.gameObject.AddComponent<VaultGridDriver>().Init(lib);
            s_listed.Clear();
            if (!UiSettings.VaultGrid) return;
            var cats = R.Get<MenuTextMenu>(lib, "m_menuCategories");
            if (cats == null) return;
            LibraryEntries.SyncSecrets();
            foreach (var c in Vault.Categories)
            {
                if (LibraryEntries.EntriesOf(c).Count == 0) continue;
                s_listed.Add(c);
                Insert(cats, c.label);
            }
            // room for every row: no scroll arrows in the category list
            R.Set(cats, "m_maxItems", cats.m_itemsData.Count);
            lib.GetComponent<VaultGridDriver>().MakeStamps();
        }

        static void Insert(MenuTextMenu cats, string label)
        {
            foreach (var d in cats.m_itemsData) if (d.m_text == label) return;
            int at = cats.m_itemsData.FindIndex(d => d.m_message == "MsgBack");
            if (at < 0) at = cats.m_itemsData.Count;
            cats.m_itemsData.Insert(at, new MenuTextMenuItemData
            {
                m_text = label, m_enabled = true, m_visible = true, m_message = ModMessage, m_platforms = (ePlatform)(-1),
            });
        }

        static MenuItemLibrary CategoryItem(MenuLibrary lib, string label)
        {
            var cats = R.Get<MenuTextMenu>(lib, "m_menuCategories");
            if (cats == null) return null;
            foreach (var it in cats.GetComponentsInChildren<MenuItemLibrary>()) if (it.GetText() == label) return it;
            return null;
        }

        internal static string SelectedLabel(MenuLibrary lib)
        {
            var cats = R.Get<MenuTextMenu>(lib, "m_menuCategories");
            return cats != null ? cats.GetSelectedString() : null;
        }

        internal static void OnEnterCategoryState(MenuLibrary lib)
        {
            foreach (var c in s_listed)
            {
                var it = CategoryItem(lib, c.label);
                if (it != null) it.SetNew(LibraryEntries.HasNew(c));
            }
            var drv = lib.GetComponent<VaultGridDriver>();
            if (drv != null) drv.GridMode = false;
        }

        // ------------------------------------------------------------------ building a grid
        /// <summary>SetCategory for a grid category: the monster grid filled with picture cells.</summary>
        internal static void Build(MenuLibrary lib, int cat)
        {
            var drv = lib.GetComponent<VaultGridDriver>();
            var mc = CategoryOf(cat);
            if (mc != null)
            {
                if (mc.secrets) LibraryEntries.SyncSecrets();   // late registrations, and found / unfound text and pictures
                else LibraryEntries.RefreshPages(mc);
            }
            R.Set(lib, "m_category", Enum.ToObject(CatType, cat));
            R.Get<MenuStateMachine>(lib, "m_states").SetState("Monster");
            var list = R.Get<MenuTextMenu>(lib, "m_menuItems");
            var grid = R.Get<MenuTextMenu>(lib, "m_menuItemsMonster");
            var ach = R.Get<MenuTextMenu>(lib, "m_menuItemsAchievements");
            list.Clear(); grid.Clear(); ach.Clear();
            Cells.Clear();
            if (drv != null) drv.GridMode = true;
            var entries = Entries(lib, cat);
            if (entries == null) return;
            int first = -1;
            for (int i = 0; i < entries.Count; i++)
            {
                var e = entries[i];
                var cell = grid.AddItem(new MenuTextMenuItemData { m_enabled = true, m_visible = true, m_message = string.Empty }) as MenuItemLibraryMonster;
                if (cell == null) continue;
                Cells.Add(cell.GetInstanceID());
                bool found = false;
                try { found = SetCell(cell, e, cat); }
                catch (Exception ex) { FurtherCore.Log.LogWarning("Vault cell " + e + ": " + ex.Message); }
                if (found && first < 0) first = i;
            }
            grid.SetSelectedItem(first >= 0 ? first : 0);
        }

        static readonly Vector3 CellGemPos = new Vector3(-3.5f, 3.5f, -1.6f);

        /// <summary>The only mark a vault entry gets: the gem in the top-left corner of its cell (the red "new" dot sits
        /// top-right; the challenge tick that shares the top-left never shows for mod entries). It shows and hides with
        /// the cell's own background; the big picture below stays bare (<see cref="Patch_VaultPortraitGem"/>).</summary>
        internal static void CellGem(MenuItemLibraryMonster cell, bool on)
        {
            if (cell == null) return;
            var bg = on ? R.Get<exSprite>(cell, "m_background") : null;
            ModMark.Pin(cell.transform, CellGemPos, bg != null ? bg.GetComponent<Renderer>() : null, on);
        }

        /// <summary>The selected entry of this category sits in a picture cell that carries its mark.</summary>
        internal static bool CellsMark(int cat) { return cat == Monsters || (UiSettings.VaultGrid && IsGridCategory(cat)); }

        struct Pic { public exAtlas atlas; public int index; }

        /// <summary>One cell: picture, found/new state and colours the way SetMonster does them. Returns found.</summary>
        static bool SetCell(MenuItemLibraryMonster cell, SystemLibrary.LibraryEntry e, int cat)
        {
            var img = R.Get<exSprite>(cell, "m_image");
            var flash = R.Get<MenuFlashEffect>(cell, "m_flashEffect");
            var isNew = R.Get<GameObject>(cell, "m_new");
            var passed = R.Get<GameObject>(cell, "m_challengePassed");
            bool found = e.IsFound(string.Empty);
            R.Set(cell, "m_found", found);
            if (isNew != null) isNew.SetActive(e.IsNew(string.Empty));
            if (passed != null) passed.SetActive(false);
            if (flash != null)
            {
                flash.EndFlash();
                flash.StartFlash(R.Get<Color>(cell, found ? "m_textColor" : "m_textColorDisabled"), R.Get<float>(cell, "m_textSize"));
            }
            Pic pic;
            bool have;
            float fixedScale = -1f;
            if (!found) have = IconPic("Undiscovered", out pic);
            else if (cat >= FirstMod && LibraryEntries.IsLocked(e)) have = IconPic("Locked", out pic);
            else
            {
                // weapons: combos of one weapon share its shop bubble, so each cell shows the hero holding that
                // combo in its own stance (the combo's idle, else the weapon's); the bubble is the big picture below
                pic = default(Pic);
                have = cat == Weapons && StancePic(e, out pic);
                if (have) fixedScale = StanceScale;
                else have = EntryPic(e, cat, out pic);
                if (!have) have = IconPic("NoArt", out pic);
            }
            if (have && img != null) Apply(img, pic, fixedScale);
            // mod entries get the gem; a secret only once it is found (a silhouette gives nothing away)
            var c = CategoryOf(cat);
            bool gem = c != null && c.secrets ? Secrets.IsFound(LibraryEntries.SecretOf(e)) : found && LibraryEntries.IsMod(e);
            CellGem(cell, gem);
            // the private SetMonster(Player) with no player only hides the cell's renderers for the spawn-in, as vanilla
            if (s_setMonsterNull == null) s_setMonsterNull = AccessTools.Method(typeof(MenuItemLibraryMonster), "SetMonster", new[] { typeof(Player) });
            s_setMonsterNull.Invoke(cell, new object[] { null });
            return found;
        }

        static bool IconPic(string anim, out Pic pic)
        {
            pic = default(Pic);
            var sh = Icons;
            var a = sh != null ? sh.Anim(anim) : null;
            if (a == null) return false;
            pic.atlas = sh.atlas; pic.index = a.frames[0];
            return true;
        }

        /// <summary>The clip, its first frame's atlas and that atlas's texture all still exist (composed or evicted art
        /// is destroyed at run time; a destroyed one draws magenta or throws).</summary>
        public static bool Alive(exSpriteAnimClip c)
        {
            if (c == null || c.frameInfos == null || c.frameInfos.Count == 0) return false;
            var a = c.frameInfos[0].atlas;
            return a != null && a.texture != null && a.material != null && a.elements != null && c.frameInfos[0].index >= 0 && c.frameInfos[0].index < a.elements.Length;
        }

        static bool FromClip(exSpriteAnimClip c, out Pic pic)
        {
            pic = default(Pic);
            if (!Alive(c)) return false;
            pic.atlas = c.frameInfos[0].atlas; pic.index = c.frameInfos[0].index;
            return true;
        }

        static bool StancePic(SystemLibrary.LibraryEntry e, out Pic pic)
        {
            pic = default(Pic);
            var w = e.m_prefab != null ? e.m_prefab.GetComponent<Weapon>() : null;
            if (w == null) return false;
            exSpriteAnimClip c = null;
            if (w.m_combos != null && !string.IsNullOrEmpty(e.m_type))
                foreach (var cb in w.m_combos) if (cb != null && cb.m_name == e.m_type) { c = cb.m_animationIdle; break; }
            if (c == null && w.m_combos != null && w.m_combos.Count == 1 && w.m_combos[0] != null) c = w.m_combos[0].m_animationIdle;
            if (c == null) c = w.m_animationIdle;
            return FromClip(c, out pic);
        }

        /// <summary>The picture the vault shows big for this entry (same rules as MenuLibrary.UpdateItem).</summary>
        static bool EntryPic(SystemLibrary.LibraryEntry e, int cat, out Pic pic)
        {
            if (FromClip(e.m_portrait, out pic)) return true;
            var go = e.m_prefab;
            if (go == null) return false;
            switch (cat)
            {
                case Weapons:
                {
                    var w = go.GetComponent<Weapon>();
                    return w != null && FromClip(w.m_animationPurchasableBubble, out pic);
                }
                case Items:
                {
                    var p = go.GetComponent<Powerup>();
                    return p != null && FromClip(p.GetPurchasableAnim(), out pic);
                }
                case Objects:
                {
                    exSpriteAnimClip c = null;
                    var asm = go.GetComponent<AnimStateMachine>();
                    if (asm != null)
                    {
                        try
                        {
                            int id = asm.GetStateId("Active");
                            if (id >= 0) c = asm.GetStateAnimation(id);
                            if (c == null) c = asm.GetStateAnimation(0);
                        }
                        catch { }
                    }
                    if (c == null) { var an = go.GetComponent<exSpriteAnimation>(); if (an != null) c = an.defaultAnimation; }
                    if (FromClip(c, out pic)) return true;
                    var s = go.GetComponent<exSprite>();
                    if (s != null && s.atlas != null && s.index >= 0) { pic.atlas = s.atlas; pic.index = s.index; return true; }
                    return false;
                }
            }
            return false;
        }

        static GameObject s_probe;

        /// <summary>Centre the picture's visible pixels in the cell at <paramref name="fixedScale"/>, or fitted to the box
        /// (never larger than 1, never smaller than 0.5), and clip it to the cell box the way SetMonster clips monsters:
        /// exClipping.AddPlane, then the game's clip shader for the atlas's own shader (tinted / paletted + its ramp).</summary>
        static void Apply(exSprite img, Pic pic, float fixedScale)
        {
            img.SetSprite(pic.atlas, pic.index);
            var r = img.GetComponent<Renderer>();
            if (r != null && pic.atlas.material != null) r.sharedMaterial = pic.atlas.material;
            img.anchor = exPlane.Anchor.MidCenter;
            img.useTextureOffset = false;
            img.color = Color.white;
            float w, h, dx = 0f, dy = 0f;
            var sh = SpriteSheets.ByAtlas(pic.atlas);
            int bx, by, bw, bh;
            if (sh != null && MonsterFactory.Bounds(sh, pic.index, out bx, out by, out bw, out bh))
            {
                // mod cells are untrimmed: centre the opaque bounds (counted from the cell's bottom-left)
                w = bw; h = bh;
                dx = bx + bw * 0.5f - sh.manifest.cellW * 0.5f;
                dy = by + bh * 0.5f - sh.manifest.cellH * 0.5f;
            }
            else
            {
                // vanilla elements are trimmed to their pixels: the quad is the trimmed rect
                var el = pic.atlas.elements[pic.index];
                w = el.trimRect.width; h = el.trimRect.height;
            }
            float s = fixedScale > 0f ? fixedScale : Mathf.Clamp(Box / Mathf.Max(1f, Mathf.Max(w, h)), MinScale, 1f);
            s = Mathf.Floor(s * 16f) / 16f;
            img.scale = new Vector2(s, s);
            img.offset = new Vector2(-dx * s, -dy * s);
            var clip = img.GetComponent<exClipping>();
            if (clip != null && r != null)
            {
                clip.AddPlane(img);
                if (s_probe == null)
                {
                    s_probe = new GameObject("CrawlMod_VaultShaderProbe");
                    s_probe.SetActive(false);
                    UnityEngine.Object.DontDestroyOnLoad(s_probe);
                    s_probe.AddComponent<MeshRenderer>();
                }
                var pr = s_probe.GetComponent<Renderer>();
                pr.sharedMaterial = pic.atlas.material;
                if (Singleton<Constants>.Get != null) Utils.SetPalettedClipShader(pr, r);
            }
        }

        // ------------------------------------------------------------------ the entry's name above its description
        // Item layout (MenuLibrary local units; one font pixel each). The rule is at y -8, the big picture at x -52, and the
        // BACK button's row (its key glyph from x 42) spans y -52 to -61. The name sits under the rule, the description
        // hangs from under the name and may use x up to 68 while above the BACK row, up to 40 beside it.
        const float TextLeft = -32f, TitleY = -14.5f, DescTop = -20f;
        const float RightOpen = 68f, RightBesideBack = 40f, BackRowTop = -51f, ScreenBottom = -68f;
        // The category summary hangs under the category list: vanilla's five rows end above SummaryTop, but every mod
        // category adds a row, so it moves down below the list's last row, no lower than SummaryLowest.
        const float SummaryLeft = -65.3f, SummaryTop = -10.1f, SummaryLowest = -26f, SummaryGap = 2f;

        static Vector3 s_titlePos, s_descPos;
        static float s_wrap;
        static TextAnchor s_titleAnchor, s_descAnchor;
        static TextAlignment s_descAlign;
        static bool s_saved, s_moved;

        static void Save(GUIText title, GUIText desc)
        {
            if (s_saved || title == null || desc == null) return;
            var tm = title.GetComponent<TextMesh>();
            var dm = desc.GetComponent<TextMesh>();
            s_titlePos = title.transform.localPosition; if (tm != null) s_titleAnchor = tm.anchor;
            s_descPos = desc.transform.localPosition;
            if (dm != null) { s_descAnchor = dm.anchor; s_descAlign = dm.alignment; }
            s_wrap = desc.GetWrapWidth();
            s_saved = true;
        }

        /// <summary>Lines of text starting at <paramref name="top"/>: as wide as the screen allows above the BACK row,
        /// narrower beside it, and no lower than the screen.</summary>
        static TextFit.LineWidth Widths(float left, float top, float lineH)
        {
            return i => top - (i + 1) * lineH >= BackRowTop ? RightOpen - left : RightBesideBack - left;
        }

        static int MaxLines(float top, float lineH) { return Mathf.Max(1, Mathf.FloorToInt((top - ScreenBottom) / lineH)); }

        /// <summary>The selected entry's name above its description, both laid out to fit.</summary>
        internal static void ShowName(MenuLibrary lib, SystemLibrary.LibraryEntry e, int cat)
        {
            ShowPage(lib, NameOf(e, cat), null);
        }

        /// <summary>A page in the item layout: <paramref name="name"/> under the rule, then <paramref name="text"/> (null:
        /// the text vanilla just set on the description).</summary>
        internal static void ShowPage(MenuLibrary lib, string name, string text)
        {
            var title = R.Get<GUIText>(lib, "m_textTitleAchievement");
            var desc = R.Get<GUIText>(lib, "m_textDescription");
            if (title == null || desc == null) return;
            Save(title, desc);
            s_moved = true;
            title.transform.localPosition = new Vector3(TextLeft, TitleY, s_titlePos.z);
            var tm = title.GetComponent<TextMesh>();
            if (tm != null) tm.anchor = TextAnchor.MiddleLeft;
            title.gameObject.SetActive(true);
            title.SetText((name ?? string.Empty).ToUpperInvariant());
            if (text == null)
            {
                if (!desc.gameObject.activeSelf) return;   // no text: vanilla shows the category summary instead
                text = R.Get<string>(desc, "m_originalText") ?? string.Empty;
            }
            if (text.Length == 0) return;
            desc.gameObject.SetActive(true);
            float lh = TextFit.LineHeight(desc.GetComponent<TextMesh>());
            TextFit.Set(desc, text, new Vector2(TextLeft, DescTop), Widths(TextLeft, DescTop, lh), MaxLines(DescTop, lh));
        }

        /// <summary>The category summary (vanilla's or a mod category's), laid out to fit.</summary>
        internal static void FitSummary(MenuLibrary lib)
        {
            var g = R.Get<GUIText>(lib, "m_textCategorySummary");
            if (g == null || !g.gameObject.activeSelf) return;
            string text = R.Get<string>(g, "m_originalText");
            if (string.IsNullOrEmpty(text)) return;
            float lh = TextFit.LineHeight(g.GetComponent<TextMesh>());
            float top = SummaryTopFor(lib);
            TextFit.Set(g, text, new Vector2(SummaryLeft, top), Widths(SummaryLeft, top, lh), MaxLines(top, lh));
        }

        /// <summary>Just under the lowest drawn row of the category list, in MenuLibrary local units.</summary>
        static float SummaryTopFor(MenuLibrary lib)
        {
            var cats = R.Get<MenuTextMenu>(lib, "m_menuCategories");
            if (cats == null) return SummaryTop;
            float bottom = float.MaxValue;
            foreach (var r in cats.GetComponentsInChildren<Renderer>())
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                float y = lib.transform.InverseTransformPoint(r.bounds.min).y;
                if (y < bottom) bottom = y;
            }
            if (bottom == float.MaxValue) return SummaryTop;
            return Mathf.Clamp(bottom - SummaryGap, SummaryLowest, SummaryTop);
        }

        internal static void RestoreTitle(MenuLibrary lib)
        {
            if (!s_moved || !s_saved) return;
            var title = R.Get<GUIText>(lib, "m_textTitleAchievement");
            var desc = R.Get<GUIText>(lib, "m_textDescription");
            if (title != null)
            {
                title.transform.localPosition = s_titlePos;
                var tm = title.GetComponent<TextMesh>();
                if (tm != null) tm.anchor = s_titleAnchor;
            }
            if (desc != null)
            {
                desc.SetWrapWidth(s_wrap);
                desc.transform.localPosition = s_descPos;
                var dm = desc.GetComponent<TextMesh>();
                if (dm != null) { dm.anchor = s_descAnchor; dm.alignment = s_descAlign; }
            }
            s_moved = false;
        }

        static string NameOf(SystemLibrary.LibraryEntry e, int cat)
        {
            if (!string.IsNullOrEmpty(e.m_name)) return e.m_name;
            if (e.m_prefab != null)
            {
                if (cat == Weapons)
                {
                    if (!string.IsNullOrEmpty(e.m_type)) return e.m_type;
                    var w = e.m_prefab.GetComponent<Weapon>();
                    if (w != null && !string.IsNullOrEmpty(w.m_weaponName)) return w.m_weaponName;
                }
                if (cat == Items)
                {
                    var p = e.m_prefab.GetComponent<Powerup>();
                    if (p != null && !string.IsNullOrEmpty(p.GetDisplayName())) return p.GetDisplayName();
                }
                return e.m_prefab.name;
            }
            return string.Empty;
        }

        public static void SelfCheck(Action<string> bad)
        {
            if (SpriteSheets.Get("VaultIcons") == null) bad("VaultIcons art missing");
            foreach (var c in Vault.Categories)
            {
                if (!string.IsNullOrEmpty(c.stamp) && SpriteSheets.Get(c.stamp) == null) bad("vault category " + c.label + ": stamp " + c.stamp + " missing");
                if (c.summary == null) bad("vault category " + c.label + " has no summary");
            }
            if (CatType == null) bad("MenuLibrary.eCategory not found");
            if (AccessTools.Method(typeof(MenuItemLibraryMonster), "SetMonster", new[] { typeof(Player) }) == null) bad("MenuItemLibraryMonster.SetMonster(Player) not found");
            foreach (var f in new[] { "m_menuItems", "m_menuItemsMonster", "m_menuCategories", "m_textTitleAchievement", "m_textDescription", "m_textDescriptionMonster", "m_textCategorySummary", "m_spriteStamp", "m_category", "m_states" })
                if (AccessTools.Field(typeof(MenuLibrary), f) == null) bad("MenuLibrary." + f + " not found");
            foreach (var f in new[] { "m_image", "m_flashEffect", "m_new", "m_challengePassed", "m_found", "m_background" })
                if (AccessTools.Field(typeof(MenuItemLibraryMonster), f) == null) bad("MenuItemLibraryMonster." + f + " not found");
            foreach (var f in new[] { "m_items", "m_scrollOffset", "m_columns", "m_maxItems" })
                if (AccessTools.Field(typeof(MenuTextMenu), f) == null) bad("MenuTextMenu." + f + " not found");
            if (AccessTools.Field(typeof(GUIText), "m_originalText") == null) bad("GUIText.m_originalText not found");
        }
    }

    // ====================================================================================================== patches

    [HarmonyPatch(typeof(MenuLibrary), "Awake")]
    static class Patch_VaultAwake
    {
        static void Postfix(MenuLibrary __instance)
        {
            try { LibraryEntries.EnsureRegistered(); VaultGrid.OnAwake(__instance); }
            catch (Exception e) { FurtherCore.Log.LogError("Vault awake: " + e); }
        }
    }

    /// <summary>The mod categories' entries; and never throw for QUESTS when achievements are off (with mod categories
    /// added, the category list's "new" loop reaches that index).</summary>
    [HarmonyPatch(typeof(MenuLibrary), "GetCategoryEntries")]
    static class Patch_VaultEntries
    {
        static bool Prefix(object[] __args, ref List<SystemLibrary.LibraryEntry> __result)
        {
            int c = Convert.ToInt32(__args[0]);
            var mc = VaultGrid.CategoryOf(c);
            if (mc != null) { __result = LibraryEntries.EntriesOf(mc); return false; }
            if (c == VaultGrid.Achievements && !VaultGrid.ShowAchievements()) { __result = new List<SystemLibrary.LibraryEntry>(); return false; }
            return true;
        }
    }

    [HarmonyPatch(typeof(MenuLibrary), "SetCategory")]
    static class Patch_VaultSetCategory
    {
        static bool Prefix(MenuLibrary __instance, object[] __args)
        {
            try
            {
                int c = Convert.ToInt32(__args[0]);
                var drv = __instance.GetComponent<VaultGridDriver>();
                if (drv != null) drv.GridMode = false;
                VaultGrid.Cells.Clear();
                if (!UiSettings.VaultGrid || !VaultGrid.IsGridCategory(c)) return true;
                VaultGrid.Build(__instance, c);
                return false;
            }
            catch (Exception e) { FurtherCore.Log.LogError("Vault grid: " + e); return true; }
        }
    }

    [HarmonyPatch(typeof(MenuLibrary), "OnEnterState")]
    static class Patch_VaultEnterState
    {
        static void Postfix(MenuLibrary __instance)
        {
            try
            {
                var st = R.Get<MenuStateMachine>(__instance, "m_states");
                string s = st != null ? st.GetStateName() : null;
                if (s == "Category") VaultGrid.OnEnterCategoryState(__instance);
                if (s == "Category" || s == "Achievements") VaultGrid.RestoreTitle(__instance);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Vault enter state: " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(MenuLibrary), "UpdateCategory")]
    static class Patch_VaultUpdateCategory
    {
        static void Postfix(MenuLibrary __instance, bool showStamp)
        {
            if (!UiSettings.VaultGrid) return;
            try
            {
                var d = __instance.GetComponent<VaultGridDriver>();
                if (d != null && VaultGrid.AnyListed) d.OnUpdateCategory(showStamp);
                VaultGrid.FitSummary(__instance);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Vault category: " + e.Message); }
        }
    }

    /// <summary>For a grid category UpdateItem reads its selection from the grid (m_menuItems points at the grid for
    /// the call), then the entry's name goes above its description when the selection changes to a found entry.</summary>
    [HarmonyPatch(typeof(MenuLibrary), "UpdateItem")]
    static class Patch_VaultUpdateItem
    {
        class State { public MenuTextMenu list; public int before; public int cat; }
        static MenuTextMenu s_saved;   // the real m_menuItems while the grid stands in for it (menus run on one thread)

        static void Prefix(MenuLibrary __instance, int ___m_selectedItem, out State __state)
        {
            __state = null;
            var drv = __instance.GetComponent<VaultGridDriver>();
            if (drv == null || !drv.GridMode) return;
            int cat = VaultGrid.Category(__instance);
            if (!VaultGrid.IsGridCategory(cat)) return;
            __state = new State { list = R.Get<MenuTextMenu>(__instance, "m_menuItems"), before = ___m_selectedItem, cat = cat };
            s_saved = __state.list;
            R.Set(__instance, "m_menuItems", R.Get<MenuTextMenu>(__instance, "m_menuItemsMonster"));
        }

        static void Postfix(MenuLibrary __instance, State __state, int ___m_selectedItem)
        {
            if (__state == null || ___m_selectedItem < 0 || ___m_selectedItem == __state.before) return;
            try
            {
                var list = VaultGrid.Entries(__instance, __state.cat);
                if (list == null || ___m_selectedItem >= list.Count) return;
                VaultGrid.ShowName(__instance, list[___m_selectedItem], __state.cat);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Vault name: " + e.Message); }
        }

        static void Finalizer(MenuLibrary __instance)
        {
            if (s_saved == null) return;
            R.Set(__instance, "m_menuItems", s_saved);
            s_saved = null;
        }
    }

    /// <summary>A picture cell's action would hide its art (it is the monster cell's challenge launch): skip it.</summary>
    [HarmonyPatch(typeof(MenuItemLibraryMonster), "OnAction")]
    static class Patch_VaultCellAction
    {
        static bool Prefix(MenuItemLibraryMonster __instance)
        {
            return __instance == null || !VaultGrid.Cells.Contains(__instance.GetInstanceID());
        }
    }
    /// <summary>
    /// The vault's big picture of a found mod entry (and of a found secret) gets the gem only in the text-list layout
    /// (CrawlFurther.UI.cfg VaultGrid = false): in a picture grid the entry's cell already carries its one mark.
    /// </summary>
    [HarmonyPatch(typeof(MenuLibrary), "UpdateItem")]
    static class Patch_VaultPortraitGem
    {
        static bool s_show;
        static int s_sel = -2, s_cat = -1, s_portrait;

        static void Postfix(MenuLibrary __instance, int ___m_selectedItem, exSpriteAnimation ___m_portrait)
        {
            if (___m_portrait == null) return;
            try
            {
                int cat = VaultGrid.Category(__instance), id = ___m_portrait.GetInstanceID();
                // UpdateItem runs every frame: work only when the selection, the category or the vault itself changes
                if (___m_selectedItem == s_sel && cat == s_cat && id == s_portrait) return;
                s_sel = ___m_selectedItem; s_cat = cat; s_portrait = id;
                s_show = false;
                var spr = ___m_portrait.GetComponent<exSprite>();
                if (spr != null) ModMark.Follow(spr, GemCorner.Art, () => s_show);
                if (VaultGrid.CellsMark(cat) || cat == VaultGrid.Achievements) return;
                var list = VaultGrid.Entries(__instance, cat);
                if (___m_selectedItem >= 0 && list != null && ___m_selectedItem < list.Count)
                {
                    var e = list[___m_selectedItem];
                    s_show = LibraryEntries.IsMod(e) && e.IsFound(string.Empty);
                }
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Vault portrait gem: " + e.Message); }
        }
    }
}
