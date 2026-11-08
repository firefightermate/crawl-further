using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Heroes
{
    using CrawlFurther.Art;
    using CrawlFurther.Ghosts;
    using CrawlFurther.Gods;
    using CrawlFurther.Heroes;
    using CrawlFurther.UI;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Ghosts;
    using CrawlFurther.Content.Gods;

    /// <summary>Confirming a god opens the origin page instead of finishing straight away.</summary>
    [HarmonyPatch(typeof(MenuDeitySelectPlayer), "OnSelect")]
    static class Patch_DeityOnSelect
    {
        public static bool Bypass;

        static bool Prefix(MenuDeitySelectPlayer __instance, bool trials)
        {
            if (!trials && GodSlots.Selected(__instance) != SlotTier.Normal)
            {
                // an idol: vanilla OnSelect would read the slot index as a trial god
                if (Bypass) { GodSlots.FinishSelect(__instance); return false; }
            }
            if (Bypass) return true;
            try
            {
                int id = R.Get<int>(__instance, "m_playerId");
                var pd = SystemPlayers.GetPlayer(id);
                if (pd == null) return true;
                if (pd.IsBot)
                {
                    HeroClasses.Chosen[id] = UnityEngine.Random.Range(1, Mathf.Max(2, HeroClasses.RegularCount));   // never a silver / gold slot
                    GhostPack.Chosen[id] = 0;   // bot ghosts can't use the form abilities
                    return true;
                }
                var picker = __instance.GetComponent<OriginPicker>() ?? __instance.gameObject.AddComponent<OriginPicker>();
                picker.Open(__instance, trials);
                return false;
            }
            catch (Exception e)
            {
                Plugin.Log.LogError("Origin picker failed, falling back to vanilla select: " + e);
                return true;
            }
        }
    }

    /// <summary>While the origin page is open, the god page stays frozen.</summary>
    [HarmonyPatch(typeof(MenuDeitySelectPlayer), "Update")]
    static class Patch_DeityUpdate
    {
        static bool Prefix(MenuDeitySelectPlayer __instance)
        {
            var p = __instance.GetComponent<OriginPicker>();
            if (p != null && p.IsOpen) return false;
            if (SlotEditorUI.OpenOn(__instance)) return false;
            try { return GodSlots.PanelUpdate(__instance); }
            catch (Exception e) { Plugin.Log.LogError("Idol slots update: " + e); return true; }
        }
    }

    /// <summary>
    /// Origin and ghost pages. Each is its own icon grid built like the god list (same item prefab, spacing and
    /// columns, scrolling when it outgrows three rows), shown in the god list's place. The panel's portrait, name
    /// and text show the highlighted entry. Confirm moves origin -> ghost -> done, back steps out.
    /// A ghost form with a blob to choose (GhostBlobs: the Gleaner, Poltergeist and Binder once they earn theirs, silver
    /// and gold always) adds a third page after it, the blob step: the same kind of list, one entry per blob, laid over a
    /// row of starter boxes that show the blobs (GhostBlobBoxes). Every page is a vanilla MenuTextMenu, so each player's
    /// pad, keys, mouse or Online Crawl input drives it exactly as it drives the god list.
    /// </summary>
    public class OriginPicker : MonoBehaviour
    {
        MenuDeitySelectPlayer m_menu;
        bool m_trials;
        int m_index;
        int m_openFrame;
        int m_prevChoice;
        int m_stage;           // 0 = hero origin, 1 = ghost form, 2 = blob
        int m_ghostIndex, m_prevGhost;
        bool m_trialsWasActive;
        MenuTextMenu m_originList, m_ghostList, m_blobList;
        GhostBlobBoxes m_blobBoxes;
        readonly List<GhostBlobDef> m_blobEntries = new List<GhostBlobDef>();
        GhostFormEntry m_blobForm;
        Dictionary<string, string> m_prevBlobs;
        public bool IsOpen { get; private set; }
        /// <summary>Frame on which the picker was last cancelled (the Back press must not also leave god select).</summary>
        public int CancelFrame { get; private set; }
        public static readonly List<OriginPicker> Live = new List<OriginPicker>();
        void Awake() { Live.Add(this); }
        void OnDestroy()
        {
            Live.Remove(this);
            if (m_blobBoxes != null) m_blobBoxes.Destroy();
        }

        int m_pid = -1;
        /// <summary>The panel's player id, read once per Open (it is read several times a frame).</summary>
        int PlayerId { get { return m_pid; } }

        public void Open(MenuDeitySelectPlayer menu, bool trials)
        {
            m_menu = menu;
            m_pid = R.Get<int>(menu, "m_playerId");
            m_editing = false;          // a page left mid-edit (player dropped out) must not stay frozen
            m_listsRecorded = false;
            m_trials = trials;
            // resolve "Random" now so the god page has a real god under it while the origin is chosen
            var list = R.Get<MenuTextMenu>(menu, "m_menu");
            if (!trials && list.GetSelectedId() == 0)
            {
                int num = SystemDeity.GetRandomUnlockedDeityId();
                if (num >= 0)
                {
                    list.SetSelectedItem(num + 1);
                    AccessTools.Method(typeof(MenuDeitySelectPlayer), "SetDeity").Invoke(menu, new object[] { SystemDeity.GetDeity(num), true });
                }
            }
            int prev;
            m_index = HeroClasses.Chosen.TryGetValue(PlayerId, out prev) ? prev : 0;
            m_prevChoice = m_index;
            m_stage = 0;
            m_ghostIndex = GhostPack.Chosen.TryGetValue(PlayerId, out prev) ? prev : 0;
            m_prevGhost = m_ghostIndex;
            m_prevBlobs = GhostBlobs.PicksOf(PlayerId);
            if (m_blobBoxes != null) m_blobBoxes.Destroy();
            m_blobBoxes = new GhostBlobBoxes(menu, PlayerId);
            foreach (var s in R.Get<exSprite[]>(menu, "m_monsters")) if (s != null) s.gameObject.SetActive(false);
            GodSlots.HideExtras(menu);
            R.Get<GameObject>(menu, "m_arrowL").SetActive(false);
            R.Get<GameObject>(menu, "m_arrowR").SetActive(false);
            SetGodListsVisible(false);
            IsOpen = true;
            m_openFrame = Time.frameCount;
            ShowStage();
        }

        bool m_listsRecorded;

        void SetGodListsVisible(bool on)
        {
            var a = R.Get<MenuTextMenu>(m_menu, "m_menu");
            var b = R.Get<MenuTextMenu>(m_menu, "m_menuTrials");
            // which list was showing is recorded once, when the page opens: hiding again later (after an editor) must
            // not overwrite it, or Back would bring the main list up over a trial god
            if (!on && b != null && !m_listsRecorded) { m_trialsWasActive = b.gameObject.activeSelf; m_listsRecorded = true; }
            if (on) m_listsRecorded = false;
            if (a != null) { a.enabled = on; a.gameObject.SetActive(on && !m_trialsWasActive); }
            if (b != null) { b.enabled = on; b.gameObject.SetActive(on && m_trialsWasActive); }
        }

        void SetGodListsEnabled(bool on)
        {
            var a = R.Get<MenuTextMenu>(m_menu, "m_menu");
            var b = R.Get<MenuTextMenu>(m_menu, "m_menuTrials");
            if (a != null) a.enabled = on;
            if (b != null) b.enabled = on;
        }

        /// <summary>A new icon grid configured like the god list, sitting where it sits.</summary>
        /// <summary>
        /// A copy of the god list's own GameObject (same components, layer, spacing, pip prefab and position),
        /// emptied and refilled with this page's entries. Three rows show; longer lists scroll.
        /// </summary>
        MenuTextMenu BuildList(string name, int count, Func<int, exSpriteAnimClip> icon, int selected)
        {
            var god = R.Get<MenuTextMenu>(m_menu, "m_menu");
            var m = CloneGodList(name);
            int cols = Mathf.Max(1, R.Get<int>(god, "m_columns"));
            R.Set(m, "m_maxItems", Mathf.CeilToInt(count / (float)cols) > 3 ? 2 : 0);
            m.gameObject.SetActive(true);
            var prefab = R.Get<MenuItemImage>(m_menu, "m_prefabMenuItem");
            for (int i = 0; i < count; i++)
            {
                var item = m.AddItem(new MenuTextMenuItemData { m_enabled = true, m_prefabMenuItem = prefab, m_message = "MsgModPick" }) as MenuItemImage;
                if (item != null) item.SetAnim(icon(i));
            }
            m.SetSelectedItem(Mathf.Clamp(selected, 0, count - 1));
            var items = R.Get<List<MenuTextMenuItem>>(m, "m_items");
            Plugin.Log.LogInfo(name + ": " + items.Count + " pips at " + m.transform.position + (items.Count > 0 ? ", first at " + items[0].transform.position : "")
                               + " (god list at " + god.transform.position + ")");
            return m;
        }

        /// <summary>
        /// An empty, inactive copy of the god list (its own player, owner and settings; no items yet), its MenuTextMenu
        /// switched on. The copy takes the god list's component state, and Open has already switched the god list off
        /// (SetGodListsVisible): a copy left that way never runs MenuTextMenu.Update, the one place a list reads its
        /// player's Left, Right, Action and mouse, so it would sit on screen and ignore every press.
        /// </summary>
        MenuTextMenu CloneGodList(string name)
        {
            var god = R.Get<MenuTextMenu>(m_menu, "m_menu");
            bool wasActive = god.gameObject.activeSelf;
            god.gameObject.SetActive(false);            // clone inactive so nothing runs before it is set up
            var go = UnityEngine.Object.Instantiate(god.gameObject);
            god.gameObject.SetActive(wasActive);
            go.name = name;
            go.transform.SetParent(god.transform.parent, false);
            go.transform.localPosition = god.transform.localPosition;
            go.transform.localRotation = god.transform.localRotation;
            go.transform.localScale = god.transform.localScale;
            // drop the copied god pips, arrows and indicator; the copy's own lists start empty
            var kids = new List<GameObject>();
            foreach (Transform t in go.transform) kids.Add(t.gameObject);
            foreach (var k in kids) UnityEngine.Object.DestroyImmediate(k);
            var m = go.GetComponent<MenuTextMenu>();
            R.Set(m, "m_initialised", true);             // skip the god list's serialized items on Start
            R.Set(m, "m_scrollOffset", 0);
            R.Set(m, "m_selectedItem", -1);
            m.SetOwner(gameObject);
            m.SetPlayerId(PlayerId);
            m.enabled = true;
            m.SetActive(true);
            return m;
        }

        void ShowStage()
        {
            var vanillaPip = ModIcons.VanillaPip(m_menu);
            var modPip = ModIcons.VioletPip(m_menu) ?? vanillaPip;
            if (m_stage == 0)
            {
                // pips by what the origin grants (violet weapon, azure spell, rose prism both); silver / gold slots last
                if (m_originList == null)
                    m_originList = BuildList("ModOriginList", HeroClasses.All.Count,
                                             i => SlotArt.OriginPip(HeroClasses.All[i], m_menu, Unlocks.IdFor("Hero", HeroClasses.All[i].tier)) ?? modPip, m_index);
                m_originList.gameObject.SetActive(true);
                m_originList.enabled = true;
                m_originList.SetSelectedItem(m_index);
                if (m_ghostList != null) m_ghostList.gameObject.SetActive(false);
                CloseBlobStep();
            }
            else if (m_stage == 2)
            {
                if (m_ghostList != null) m_ghostList.gameObject.SetActive(false);
                if (m_originList != null) m_originList.gameObject.SetActive(false);
                if (!BuildBlobStep()) { m_stage = 1; Confirm(); return; }   // no starter boxes to stand in for: take the default
            }
            else
            {
                CloseBlobStep();
                if (m_ghostList == null)
                    m_ghostList = BuildList("ModGhostList", GhostPack.Forms.Count, i =>
                    {
                        var t = SlotCompat.GhostTier(GhostPack.Forms[i]);
                        if (t != SlotTier.Normal) return SlotArt.TierPip(t, Unlocks.IsUnlocked(Unlocks.IdFor("Ghost", t))) ?? modPip;
                        return i == 0 ? vanillaPip : modPip;
                    }, m_ghostIndex);
                m_ghostList.gameObject.SetActive(true);
                m_ghostList.enabled = true;
                m_ghostList.SetSelectedItem(m_ghostIndex);
                if (m_originList != null) m_originList.gameObject.SetActive(false);
            }
            Show();
        }

        void Show()
        {
            var text = R.Get<GUIText>(m_menu, "m_text");
            var flav = R.Get<GUIText>(m_menu, "m_textFlavour");
            var portrait = R.Get<exSpriteAnimation>(m_menu, "m_portrait");
            if (m_stage == 2)
            {
                ShowBlob(text, flav);
                return;
            }
            if (m_stage == 1)
            {
                var g = GhostPack.Forms[m_ghostIndex];
                var gt = SlotCompat.GhostTier(g);
                bool gOpen = gt == SlotTier.Normal || Unlocks.IsUnlocked(Unlocks.IdFor("Ghost", gt));
                SlotArt.FitName(R.Get<TextMesh>(m_menu, "m_name"), g.name);
                if (text != null) text.SetText(gOpen ? GhostControls.Personalise(g.summary, GhostControls.Name(PlayerId)) : LockedText("Ghost", gt));
                if (flav != null) flav.SetText(g.flavour);
                PanelText.Fit(text); PanelText.Fit(flav);
                int gi = m_ghostIndex;
                m_portraitFn = () => { var f = GhostPack.Forms[gi]; return SlotCompat.GhostPortrait(f, PlayerId) ?? Portrait("ghost_" + f.name, f.portraitArt); };
                PlayPortrait(portrait);
                SlotLock.Show(m_menu, !gOpen);
                if (gOpen) GhostPack.Chosen[PlayerId] = m_ghostIndex;   // a locked slot is only looked at
                return;
            }
            var def = HeroClasses.All[m_index];
            bool open = def.tier == SlotTier.Normal || Unlocks.IsUnlocked(Unlocks.IdFor("Hero", def.tier));
            SlotArt.FitName(R.Get<TextMesh>(m_menu, "m_name"), def.name);
            if (text != null) text.SetText(open ? def.summary : LockedText("Hero", def.tier));
            if (flav != null) flav.SetText(def.flavour);
            PanelText.Fit(text); PanelText.Fit(flav);
            int hi = m_index;
            m_portraitFn = () => { var d = HeroClasses.All[hi]; return HeroClasses.PortraitClip(d, PlayerId) ?? Portrait(d.id, d.portraitArt); };   // this player's colour set
            PlayPortrait(portrait);
            SlotLock.Show(m_menu, !open);
            if (!open) return;
            HeroClasses.Chosen[PlayerId] = m_index;
            var pd = SystemPlayers.GetPlayer(PlayerId);
            if (pd != null && pd.GetDeity() != null) pd.SetDeity(pd.GetDeity());   // re-apply so the preview is live
        }

        Func<exSpriteAnimClip> m_portraitFn;
        float m_nextPortraitCheck;

        /// <summary>Play the highlighted entry's portrait, never a destroyed (pruned) composite.</summary>
        void PlayPortrait(exSpriteAnimation portrait)
        {
            if (portrait == null || m_portraitFn == null) return;
            if (!SlotArt.SafePlay(portrait, m_portraitFn())) portrait.PlayDefault();
        }

        /// <summary>Four times a second: a portrait whose composite was freed under it is fetched again.</summary>
        void CheckPortrait()
        {
            if (Time.unscaledTime < m_nextPortraitCheck) return;
            m_nextPortraitCheck = Time.unscaledTime + 0.25f;
            var portrait = R.Get<exSpriteAnimation>(m_menu, "m_portrait");
            var cur = portrait != null ? portrait.GetCurrentAnimation() : null;
            if (cur != null && !SlotArt.Alive(cur.clip)) PlayPortrait(portrait);
        }

        static string LockedText(string list, SlotTier t)
        {
            var c = Unlocks.Find(Unlocks.IdFor(list, t));
            return c == null ? "Locked" : c.text + "  " + Unlocks.ProgressShort(c.id);
        }

        static readonly Dictionary<string, exSpriteAnimClip> s_clips = new Dictionary<string, exSpriteAnimClip>();
        static exSpriteAnimClip Portrait(string key, string art)
        {
            exSpriteAnimClip c;
            if (s_clips.TryGetValue(key, out c) && c != null) return c;
            var sh = SpriteSheets.Get(art);
            if (sh == null || !sh.Has("Idle")) return null;
            c = new ClipBuilder(sh, "Idle", "ModOrigin_" + key).Loop().Build();
            s_clips[key] = c;
            return c;
        }

        void Update()
        {
            if (!IsOpen || m_menu == null) return;
            if (m_editing) return;
            CheckPortrait();
            var list = m_stage == 0 ? m_originList : m_stage == 1 ? m_ghostList : m_blobList;
            if (list != null)
            {
                int sel = list.GetSelectedId();
                if (m_stage == 0 && sel >= 0 && sel != m_index) { m_index = sel; Show(); }
                if (m_stage == 1 && sel >= 0 && sel != m_ghostIndex) { m_ghostIndex = sel; Show(); }
                if (m_stage == 2 && sel >= 0 && sel != m_blobIndex) { m_blobIndex = sel; Show(); }
            }
            if (m_stage == 2 && m_blobBoxes != null) m_blobBoxes.Tick();
            if (Time.frameCount <= m_openFrame + 1) return;      // ignore the press that opened us
            if (SystemInput.InputDown(eInput.Alt, PlayerId))
            {
                if (m_stage == 2)
                {
                    // back to the forms, the confirmed one still highlighted; the pick is left as it was
                    Plugin.Log.LogInfo("Blob step: back for player " + (PlayerId + 1));
                    m_stage = 1; CancelFrame = Time.frameCount; m_openFrame = Time.frameCount;
                    ShowStage();
                }
                else if (m_stage == 1)
                {
                    m_stage = 0; CancelFrame = Time.frameCount; m_openFrame = Time.frameCount;
                    GhostPack.Chosen[PlayerId] = m_prevGhost; m_ghostIndex = m_prevGhost;
                    ShowStage();
                }
                else Cancel();
            }
        }

        /// <summary>Sent by the icon lists when an entry is confirmed.</summary>
        void MsgModPick()
        {
            if (!IsOpen || m_editing || Time.frameCount <= m_openFrame + 1) return;
            if (m_stage == 0)
            {
                if (m_originList != null) m_index = Mathf.Max(0, m_originList.GetSelectedId());
                var t = HeroClasses.All[m_index].tier;
                if (t != SlotTier.Normal && !Unlocks.IsUnlocked(Unlocks.IdFor("Hero", t))) { SlotLock.Deny(m_menu); return; }
                Action next = () => { m_stage = 1; m_openFrame = Time.frameCount; ShowStage(); };
                if (t != SlotTier.Normal && SlotEditors.Hero != null) OpenEditor(SlotEditors.Hero, t, next);
                else next();
            }
            else if (m_stage == 1)
            {
                if (m_ghostList != null) m_ghostIndex = Mathf.Max(0, m_ghostList.GetSelectedId());
                var t = SlotCompat.GhostTier(GhostPack.Forms[m_ghostIndex]);
                if (t != SlotTier.Normal && !Unlocks.IsUnlocked(Unlocks.IdFor("Ghost", t))) { SlotLock.Deny(m_menu); return; }
                if (t != SlotTier.Normal && SlotEditors.Ghost != null) OpenEditor(SlotEditors.Ghost, t, AfterForm);
                else AfterForm();
            }
            else
            {
                if (m_blobList != null) m_blobIndex = Mathf.Max(0, m_blobList.GetSelectedId());
                var d = m_blobIndex < m_blobEntries.Count ? m_blobEntries[m_blobIndex] : null;
                if (d == null || !GhostBlobs.IsOpen(d)) { if (m_blobBoxes != null) m_blobBoxes.Deny(); return; }
                GhostBlobs.SetPick(PlayerId, m_blobForm, d);
                Plugin.Log.LogInfo("Blob step: confirm for player " + (PlayerId + 1) + ": " + d.id + " (" + m_blobForm.id + ")");
                Confirm();
            }
        }

        /// <summary>Sent by a locked blob's entry (the game's locked item, as for a locked god): the boxes shake.</summary>
        void MsgModBlobLocked()
        {
            if (!IsOpen || m_stage != 2 || Time.frameCount <= m_openFrame + 1) return;
            Plugin.Log.LogInfo("Blob step: locked blob for player " + (PlayerId + 1));
            if (m_blobBoxes != null) m_blobBoxes.Deny();
        }

        // ------------------------------------------------------------------ the blob step
        int m_blobIndex;

        /// <summary>The form is confirmed: the blob step when it has a choice, else done.</summary>
        void AfterForm()
        {
            var pd = SystemPlayers.GetPlayer(PlayerId);
            var form = GhostPack.Forms[m_ghostIndex];
            if (pd == null || pd.IsBot || !HasBlobChoice(form)) { Confirm(); return; }
            Plugin.Log.LogInfo("Blob step: open for player " + (PlayerId + 1) + " (" + form.id + ")");
            m_blobForm = form;
            m_stage = 2;
            m_openFrame = Time.frameCount;
            ShowStage();
        }

        /// <summary>A form has a blob step when one of its blobs besides the regular one is open (a locked own blob
        /// is no choice yet; silver and gold always have the King).</summary>
        static bool HasBlobChoice(GhostFormDef form)
        {
            foreach (var d in GhostBlobs.ChoicesFor(form))
                if (d != GhostBlobs.Regular && GhostBlobs.IsOpen(d)) return true;
            return false;
        }

        /// <summary>
        /// The blob step's list: a copy of the god list with one entry per blob, in a single row whose entries sit right
        /// over the blob boxes, a column per box; each entry's mouse hotspot is its column (entry and box). Open blobs
        /// get the plain pip (the box owns the mod mark), locked ones the game's locked item. It starts on the blob the
        /// form spawns now: the player's last pick for it, else its default.
        /// </summary>
        bool BuildBlobStep()
        {
            m_blobEntries.Clear();
            m_blobEntries.AddRange(GhostBlobs.ChoicesFor(m_blobForm));
            int n = m_blobEntries.Count;
            if (n < 2 || m_blobBoxes == null || !m_blobBoxes.Show(m_blobForm, m_blobEntries)) return false;
            DestroyBlobList();
            var m = CloneGodList("ModBlobList");
            Vector3 first = m_blobBoxes.WorldCentre(0), last = m_blobBoxes.WorldCentre(n - 1);
            var top = m_blobBoxes.WorldRect(0).yMax;
            var god = R.Get<MenuTextMenu>(m_menu, "m_menu");
            m.transform.position = new Vector3((first.x + last.x) * 0.5f, top + 2.5f, god.transform.position.z);
            R.Set(m, "m_columns", n);
            R.Set(m, "m_columnSpacing", (last.x - first.x) / (n - 1));
            R.Set(m, "m_maxItems", 0);
            m.gameObject.SetActive(true);
            var open = R.Get<MenuItemImage>(m_menu, "m_prefabMenuItem");
            var locked = R.Get<MenuItemImage>(m_menu, "m_prefabMenuItemLocked") ?? open;
            var pip = ModIcons.VanillaPip(m_menu);
            var lockedPip = R.Get<exSpriteAnimClip>(m_menu, "m_deityPortraitLocked") ?? pip;
            for (int i = 0; i < n; i++)
            {
                bool isOpen = GhostBlobs.IsOpen(m_blobEntries[i]);
                var item = m.AddItem(new MenuTextMenuItemData
                {
                    m_enabled = true, m_prefabMenuItem = isOpen ? open : locked, m_message = isOpen ? "MsgModPick" : "MsgModBlobLocked",
                }) as MenuItemImage;
                if (item == null) continue;
                item.SetAnim(isOpen ? pip : lockedPip);
                // the mouse finds the entry anywhere in its column: from its box up to just over the entry itself
                var box = m_blobBoxes.WorldRect(i);
                Vector2 at = item.transform.position;
                R.Set(item, "m_mouseRect", Rect.MinMaxRect(box.xMin - at.x, box.yMin - at.y, box.xMax - at.x, 2f));
            }
            var now = GhostBlobs.ChoiceFor(SystemPlayers.GetPlayer(PlayerId), m_blobForm);
            m_blobIndex = Mathf.Max(0, m_blobEntries.IndexOf(now));
            m.SetSelectedItem(m_blobIndex);
            m_blobList = m;
            Plugin.Log.LogInfo("ModBlobList: " + n + " entries for player " + (PlayerId + 1) + " at " + m.transform.position + ", starting on "
                               + m_blobEntries[m_blobIndex].id + (m.isActiveAndEnabled ? "" : " (NOT ACTIVE: it will take no input)"));
            return true;
        }

        void ShowBlob(GUIText text, GUIText flav)
        {
            var d = m_blobIndex < m_blobEntries.Count ? m_blobEntries[m_blobIndex] : null;
            if (d == null) return;
            SlotArt.FitName(R.Get<TextMesh>(m_menu, "m_name"), d.name.ToUpperInvariant());
            string line;
            if (GhostBlobs.IsOpen(d)) line = GhostControls.Personalise(d.summary, GhostControls.Name(PlayerId));
            else
            {
                var c = Unlocks.Find(d.unlock);
                line = c == null ? "Locked" : c.text + "  " + Unlocks.ProgressShort(c.id);
            }
            if (text != null) text.SetText(line);
            if (flav != null) flav.SetText(m_blobForm != null ? m_blobForm.flavour : "");
            SlotLock.Show(m_menu, false);
            var now = GhostBlobs.ChoiceFor(SystemPlayers.GetPlayer(PlayerId), m_blobForm);
            if (m_blobBoxes != null) m_blobBoxes.Refresh(m_blobIndex, m_blobEntries.IndexOf(now));
        }

        /// <summary>Leave the blob step: its list goes and the starter boxes come back.</summary>
        void CloseBlobStep()
        {
            DestroyBlobList();
            if (m_blobBoxes != null) m_blobBoxes.Hide();
        }

        void DestroyBlobList()
        {
            if (m_blobList == null) return;
            m_blobList.gameObject.SetActive(false);
            UnityEngine.Object.Destroy(m_blobList.gameObject);
            m_blobList = null;
        }

        /// <summary>A silver / gold slot's editor, opened over this page; the page comes back when it closes.</summary>
        void OpenEditor(Func<MenuDeitySelectPlayer, ISlotEditor> factory, SlotTier t, Action then)
        {
            var ed = factory(m_menu);
            if (ed == null) { then(); return; }
            var list = m_stage == 0 ? m_originList : m_ghostList;
            if (list != null) { list.enabled = false; list.gameObject.SetActive(false); }
            CloseBlobStep();
            m_editing = true;
            ed.Open(m_menu, PlayerId, t,
                () => { m_editing = false; if (!IsOpen) return; m_openFrame = Time.frameCount; ShowStageAfterEditor(); then(); },
                () => { m_editing = false; if (!IsOpen) return; m_openFrame = Time.frameCount; ShowStageAfterEditor(); });
        }

        bool m_editing;

        void ShowStageAfterEditor()
        {
            // the editor put the god list back: hide it again under this page
            SetGodListsVisible(false);
            foreach (var s in R.Get<exSprite[]>(m_menu, "m_monsters")) if (s != null) s.gameObject.SetActive(false);
            GodSlots.HideExtras(m_menu);
            R.Get<GameObject>(m_menu, "m_arrowL").SetActive(false);
            R.Get<GameObject>(m_menu, "m_arrowR").SetActive(false);
            ShowStage();
        }

        void HideLists()
        {
            if (m_originList != null) m_originList.gameObject.SetActive(false);
            if (m_ghostList != null) m_ghostList.gameObject.SetActive(false);
            CloseBlobStep();
        }

        void Close()
        {
            IsOpen = false;
            HideLists();
            SlotLock.Show(m_menu, false);
            SlotArt.ResetName(R.Get<TextMesh>(m_menu, "m_name"));
            SetGodListsVisible(true);
            SetGodListsEnabled(false);
            StartCoroutine(EnableMenusNextFrame());
            // force the god page to redraw everything (portrait, monsters, text) on its next Update
            R.Set(m_menu, "m_deity", null);
            var tf = AccessTools.Field(typeof(MenuDeitySelectPlayer), "m_selectedItemType");
            tf.SetValue(m_menu, Enum.ToObject(tf.FieldType, 0));
        }

        void Confirm()
        {
            HeroClasses.Chosen[PlayerId] = m_index;
            GhostPack.Chosen[PlayerId] = m_ghostIndex;
            Close();
            Patch_DeityOnSelect.Bypass = true;
            try { AccessTools.Method(typeof(MenuDeitySelectPlayer), "OnSelect").Invoke(m_menu, new object[] { m_trials }); }
            catch (Exception e) { Plugin.Log.LogError("Origin confirm failed: " + e); }
            finally { Patch_DeityOnSelect.Bypass = false; }
        }

        System.Collections.IEnumerator EnableMenusNextFrame()
        {
            // the confirm/back press is still "down" this frame: don't let the god list see it
            yield return null;
            yield return null;
            if (!IsOpen) SetGodListsEnabled(true);
        }

        void Cancel()
        {
            CancelFrame = Time.frameCount;
            HeroClasses.Chosen[PlayerId] = m_prevChoice;
            GhostPack.Chosen[PlayerId] = m_prevGhost;
            GhostBlobs.RestorePicks(PlayerId, m_prevBlobs);
            Close();
        }

        void OnDisable()
        {
            // an editor open over this page goes first (its callbacks see the page already closed and do nothing),
            // then the page puts the god list back
            m_editing = false;
            bool wasOpen = IsOpen;
            IsOpen = false;
            var ed = GetComponent<SlotEditorUI>();
            if (ed != null && ed.IsOpen) ed.Abort();
            if (!wasOpen) { if (m_menu != null) SetGodListsEnabled(true); return; }
            SlotLock.Show(m_menu, false);
            SlotArt.ResetName(R.Get<TextMesh>(m_menu, "m_name"));
            HeroClasses.Chosen[PlayerId] = m_prevChoice;
            GhostPack.Chosen[PlayerId] = m_prevGhost;
            GhostBlobs.RestorePicks(PlayerId, m_prevBlobs);
            HideLists();
            if (m_menu != null) { SetGodListsVisible(true); R.Set(m_menu, "m_deity", null); }
        }
    }

    /// <summary>While a player's origin page is open (or on the frame it was cancelled), their menu state machine ignores input.</summary>
    [HarmonyPatch(typeof(MenuStateMachine), "Update")]
    static class Patch_MenuStateMachineUpdate
    {
        static readonly AccessTools.FieldRef<MenuStateMachine, int> s_machineId = AccessTools.FieldRefAccess<MenuStateMachine, int>("m_playerId");
        static readonly AccessTools.FieldRef<MenuDeitySelectPlayer, int> s_panelId = AccessTools.FieldRefAccess<MenuDeitySelectPlayer, int>("m_playerId");

        static bool Prefix(MenuStateMachine __instance)
        {
            // runs every frame for every menu state machine: nothing to do unless an origin page or editor exists
            if (OriginPicker.Live.Count == 0 && !PanelInput.Any) return true;
            int id;
            try { id = s_machineId(__instance); } catch { return true; }
            if (id < 0) return true;
            if (PanelInput.Blocked(id)) return false;
            foreach (var p in OriginPicker.Live)
            {
                if (p == null) continue;
                var panel = p.GetComponent<MenuDeitySelectPlayer>();
                if (panel == null) continue;
                int pid = s_panelId(panel);
                if (pid != id) continue;
                if (p.IsOpen || Time.frameCount - p.CancelFrame <= 1) return false;
            }
            return true;
        }
    }

    /// <summary>Slot data of the hero and ghost lists in one place (the last two entries of each list are silver / gold).</summary>
    public static class SlotCompat
    {
        public static int HeroRegular { get { return HeroClasses.RegularCount; } }
        public static int GhostRegular { get { return GhostPack.RegularCount; } }
        public static SlotTier GhostTier(GhostFormDef g) { return g == null ? SlotTier.Normal : g.tier; }
        public static exSpriteAnimClip GhostPortrait(GhostFormDef g, int pid) { return g == null ? null : GhostPack.PortraitClip(g, pid); }
    }
}
