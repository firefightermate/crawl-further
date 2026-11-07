using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Compat;
    using CrawlFurther.Util;

    /// <summary>
    /// A panel-sized editor in the vanilla god-select look, for one player, inside that player's own panel (up to four
    /// side by side, 50 units wide each). It keeps the panel's name line (title) and portrait (preview), hides the god
    /// list, monster boxes and text, and stacks rows under the portrait:
    ///   CycleRow   "LABEL" over "&lt; value &gt;" that cycles with left / right (arrows, click, wheel)
    ///   StripRow   a row of small boxes (the slots being filled); left / right picks one
    ///   GridRow    an icon grid of monster boxes (or clips) with paging; the focused cell animates
    ///   ButtonRow  a confirm button (tick + text), disabled until its condition holds
    ///   InfoRow    one or two lines of plain text (name / detail of whatever is focused)
    /// Input: keyboard and controller (up / down move between rows, left / right inside a row, Action presses, Back
    /// calls onBack); a mouse player hovers (focus follows the pointer), clicks (arrows, cells, buttons) and wheels
    /// (cycle / scroll), right click is Back. Any player id. Rebuild rows freely between pages with Clear().
    /// </summary>
    public class SlotEditorUI : MonoBehaviour
    {
        public MenuDeitySelectPlayer Panel { get; private set; }
        public int PlayerId { get; private set; }
        public SlotTier Tier { get; private set; }
        public bool IsOpen { get; private set; }
        public Transform Root { get { return m_root != null ? m_root.transform : null; } }
        public Action onBack;

        GameObject m_root, m_rowsRoot;
        readonly List<EdRow> m_rows = new List<EdRow>();
        int m_focus;
        int m_openFrame;
        readonly List<GameObject> m_hidden = new List<GameObject>();
        readonly List<exSprite> m_corners = new List<exSprite>();
        string m_oldName;
        float m_shake;
        Vector3 m_rootBase;
        AudioCue m_sndMove, m_sndAction;
        GameObject m_textTemplate, m_descTemplate, m_boxTemplate;
        public static readonly List<SlotEditorUI> Live = new List<SlotEditorUI>();

        void Awake() { Live.Add(this); }
        void OnDestroy() { Live.Remove(this); }

        /// <summary>The panel's editor kit (one per panel, reused by every editor).</summary>
        public static SlotEditorUI For(MenuDeitySelectPlayer panel)
        {
            return panel.GetComponent<SlotEditorUI>() ?? panel.gameObject.AddComponent<SlotEditorUI>();
        }

        /// <summary>True while any editor is open for this panel.</summary>
        public static bool OpenOn(MenuDeitySelectPlayer panel)
        {
            var e = panel != null ? panel.GetComponent<SlotEditorUI>() : null;
            return e != null && e.IsOpen;
        }

        // ------------------------------------------------------------------ open / close
        /// <summary>Open over the panel for one player: hides the god page, keeps the name line (set to <paramref name="title"/>)
        /// and the portrait, and draws the tier's corners. Add rows next.</summary>
        public void Begin(MenuDeitySelectPlayer panel, int playerId, SlotTier tier, string title)
        {
            if (IsOpen) End();
            onAbort = null; onBack = null; m_portraitSource = null;
            Panel = panel; PlayerId = playerId; Tier = tier;
            m_openFrame = Time.frameCount;
            IsOpen = true;
            PanelInput.Hold(playerId, this);
            // templates from the panel's own objects (fonts, colours, spawn flash, the monster box)
            var tw = panel.transform.Find("TextWorships");
            m_textTemplate = tw != null ? tw.gameObject : R.Get<TextMesh>(panel, "m_name").gameObject;
            var dt = R.Get<GUIText>(panel, "m_text");
            m_descTemplate = dt != null ? dt.gameObject : m_textTemplate;
            var mons = R.Get<exSprite[]>(panel, "m_monsters");
            m_boxTemplate = mons != null && mons.Length > 0 && mons[0] != null ? mons[0].transform.parent.gameObject : null;
            var item = R.Get<MenuItemImage>(panel, "m_prefabMenuItem");
            if (item != null) { m_sndMove = R.Get<AudioCue>(item, "m_soundOnSelect"); m_sndAction = R.Get<AudioCue>(item, "m_soundOnAction"); }

            // hide the god page under us, remembering exactly which list was showing (main or trials) and its state
            m_hidden.Clear();
            m_lists = new[] { R.Get<MenuTextMenu>(panel, "m_menu"), R.Get<MenuTextMenu>(panel, "m_menuTrials") };
            for (int i = 0; i < 2; i++)
            {
                var m = m_lists[i];
                m_listActive[i] = m != null && m.gameObject.activeSelf;
                m_listEnabled[i] = m != null && m.enabled;
                if (m != null) { m.enabled = false; m.gameObject.SetActive(false); }
            }
            var portrait0 = R.Get<exSpriteAnimation>(panel, "m_portrait");
            m_portraitWasActive = portrait0 == null || portrait0.gameObject.activeSelf;
            if (mons != null) foreach (var s in mons) if (s != null) HideObj(s.transform.parent.gameObject);
            if (SlotGods.HideExtras != null) SlotGods.HideExtras(panel);
            HideObj(R.Get<GameObject>(panel, "m_arrowL"));
            HideObj(R.Get<GameObject>(panel, "m_arrowR"));
            if (dt != null) HideObj(dt.gameObject);
            SlotLock.Show(panel, false);

            m_root = new GameObject("ModSlotEditor");
            m_root.layer = panel.gameObject.layer;
            m_root.transform.SetParent(panel.transform, false);
            m_rootBase = Vector3.zero;
            m_rowsRoot = new GameObject("Rows");
            m_rowsRoot.layer = m_root.layer;
            m_rowsRoot.transform.SetParent(m_root.transform, false);
            // tier filigree in the corners of the editor area (under the portrait down to the panel's foot)
            m_corners.Clear();
            var cc = SlotArt.Clip("EdCorner", SlotArt.Anim(tier));
            float l = -21.5f, r = 21.5f, t = -39f, b = -108.5f;   // under the name line, above the panel foot
            foreach (var p in new[] { new Vector3(l, t), new Vector3(r, t), new Vector3(l, b), new Vector3(r, b) })
            {
                var s = SlotArt.Sprite("Corner", m_root.transform, new Vector3(p.x, p.y, -0.5f), cc);
                s.scale = new Vector2(p.x > 0 ? -1f : 1f, p.y < -60f ? -1f : 1f);
                m_corners.Add(s);
            }
            var name = R.Get<TextMesh>(panel, "m_name");
            m_oldName = name != null ? name.text : null;
            SetTitle(title);
            m_rows.Clear();
            m_focus = 0;
        }

        void HideObj(GameObject g)
        {
            if (g == null || !g.activeSelf) return;
            g.SetActive(false);
            m_hidden.Add(g);
        }

        /// <summary>Remove every row (between pages); the frame, title and preview stay.</summary>
        public void Clear()
        {
            foreach (var r in m_rows) r.Destroy();
            m_rows.Clear();
            m_focus = 0;
            SetPreviewBox(null);
        }

        MenuTextMenu[] m_lists = new MenuTextMenu[2];
        readonly bool[] m_listActive = new bool[2], m_listEnabled = new bool[2];
        bool m_portraitWasActive = true;

        /// <summary>Called when the editor is torn down without the player choosing (the panel was switched off: a pad
        /// unplugged, the player unjoined, the scene changed). Editors set it to their cancel path.</summary>
        public Action onAbort;

        /// <summary>Close and put the god page back exactly as it was (list, its enabled state, portrait, title, input).</summary>
        public void End()
        {
            if (!IsOpen) return;
            IsOpen = false;
            try
            {
                Clear();
                if (m_previewBox != null) { m_previewBox.Destroy(); m_previewBox = null; }
                if (m_root != null) Destroy(m_root);
                m_root = null;
                foreach (var g in m_hidden) if (g != null) g.SetActive(true);
                m_hidden.Clear();
                if (Panel != null)
                {
                    var portrait = R.Get<exSpriteAnimation>(Panel, "m_portrait");
                    if (portrait != null) portrait.gameObject.SetActive(m_portraitWasActive);
                    var name = R.Get<TextMesh>(Panel, "m_name");
                    if (name != null && m_oldName != null) name.text = m_oldName;
                    SlotArt.ResetName(name);
                }
                for (int i = 0; i < 2; i++) if (m_lists[i] != null) m_lists[i].gameObject.SetActive(m_listActive[i]);
                // the confirm / back press is still down this frame: lists that were live come back two frames later
                // (at once if the panel itself is going away, when no coroutine can run)
                if (isActiveAndEnabled) StartCoroutine(EnableListsLater());
                else RestoreListsEnabled();
            }
            finally
            {
                // whatever failed above, the player's menus must not stay locked
                PanelInput.Free(PlayerId);
            }
            // the god page redraws everything on its next Update
            R.Set(Panel, "m_deity", null);
            var tf = AccessTools.Field(typeof(MenuDeitySelectPlayer), "m_selectedItemType");
            tf.SetValue(Panel, Enum.ToObject(tf.FieldType, 0));
            if (SlotGods.Redraw != null) SlotGods.Redraw(Panel);
        }

        System.Collections.IEnumerator EnableListsLater()
        {
            yield return null;
            yield return null;
            if (!IsOpen) RestoreListsEnabled();
        }

        void RestoreListsEnabled()
        {
            for (int i = 0; i < 2; i++) if (m_lists[i] != null) m_lists[i].enabled = m_listEnabled[i];
        }

        void OnDisable() { Abort(); }

        /// <summary>
        /// Tear down without a choice: the panel went away under us (pad unplugged, player unjoined, scene change). Puts
        /// everything back and lets the editor cancel, once. Safe to call twice and from either side of the panel's
        /// components' OnDisable order.
        /// </summary>
        public void Abort()
        {
            if (!IsOpen) return;
            End();
            var abort = onAbort;
            onAbort = null;
            if (abort != null)
            {
                try { abort(); } catch (Exception e) { FurtherCore.Log.LogWarning("Slot editor abort: " + e.Message); }
            }
        }

        // ------------------------------------------------------------------ panel parts
        /// <summary>The panel's name line (shrunk to fit).</summary>
        public void SetTitle(string t) { SlotArt.FitName(R.Get<TextMesh>(Panel, "m_name"), t); }

        Func<exSpriteAnimClip> m_portraitSource;
        float m_nextPortraitCheck;

        /// <summary>
        /// The panel's portrait plays what <paramref name="source"/> returns, now and again whenever the clip it shows is
        /// destroyed under it (live composites are rebuilt and old ones freed). Use this for anything composed at run time.
        /// </summary>
        public void SetPortraitFrom(Func<exSpriteAnimClip> source)
        {
            m_portraitSource = source;
            SetPortrait(source != null ? source() : null);
        }

        /// <summary>The panel's portrait plays <paramref name="clip"/> (null hides it). A destroyed or half-built clip is
        /// never played: the old picture stays until a good one comes (never the missing-texture magenta).</summary>
        public void SetPortrait(exSpriteAnimClip clip)
        {
            var portrait = R.Get<exSpriteAnimation>(Panel, "m_portrait");
            if (portrait == null) return;
            if ((object)clip == null) { portrait.gameObject.SetActive(false); return; }
            portrait.gameObject.SetActive(m_previewBox == null);
            var g = portrait.GetComponent<Glitch>();
            if (g != null) g.enabled = false;
            SlotArt.SafePlay(portrait, clip);
        }

        /// <summary>Four times a second: if the portrait's clip (or its texture) was destroyed, show the source's current one.</summary>
        void CheckPortrait()
        {
            if (Time.unscaledTime < m_nextPortraitCheck) return;
            m_nextPortraitCheck = Time.unscaledTime + 0.25f;
            var portrait = R.Get<exSpriteAnimation>(Panel, "m_portrait");
            if (portrait == null || !portrait.gameObject.activeInHierarchy) return;
            var cur = portrait.GetCurrentAnimation();
            if (cur == null || SlotArt.Alive(cur.clip)) return;
            var c = m_portraitSource != null ? m_portraitSource() : null;
            if (!SlotArt.SafePlay(portrait, c)) portrait.gameObject.SetActive(false);   // nothing good to show: show nothing
        }

        BoxView m_previewBox;

        /// <summary>Show a monster running in a big box where the portrait sits (null: back to the portrait).</summary>
        public void SetPreviewMonster(Player p)
        {
            if (p == null) { SetPreviewBox(null); return; }
            if (m_previewBox == null)
            {
                m_previewBox = NewBox("Preview", m_root.transform, new Vector3(0f, -46.5f, 0f), 1.5f);
                var portrait = R.Get<exSpriteAnimation>(Panel, "m_portrait");
                if (portrait != null) portrait.gameObject.SetActive(false);
            }
            if (m_previewBox != null) m_previewBox.SetMonster(p, true);
        }

        void SetPreviewBox(object none)
        {
            if (m_previewBox != null) { m_previewBox.Destroy(); m_previewBox = null; }
            var portrait = R.Get<exSpriteAnimation>(Panel, "m_portrait");
            if (portrait != null && IsOpen) portrait.gameObject.SetActive(true);
        }

        // ------------------------------------------------------------------ building blocks for rows
        /// <summary>A line of text in the panel's own font, under <paramref name="parent"/>.</summary>
        public TextMesh NewText(Transform parent, string name, Vector3 local, Color col, TextAnchor anchor = TextAnchor.MiddleCenter)
        {
            return SlotArt.Text(m_textTemplate, parent, name, local, col, anchor);
        }

        /// <summary>A wrapping paragraph (GUIText) <paramref name="wrap"/> units wide, top-centred at <paramref name="local"/>.</summary>
        public GUIText NewParagraph(Transform parent, string name, Vector3 local, float wrap, Color col)
        {
            var tm = SlotArt.Text(m_descTemplate, parent, name, local, col, TextAnchor.UpperCenter);
            var gt = tm.GetComponent<GUIText>() ?? tm.gameObject.AddComponent<GUIText>();
            gt.SetWrapWidth(wrap);
            return gt;
        }

        /// <summary>A starter box like the god select's, <paramref name="scale"/> times its size.</summary>
        public BoxView NewBox(string name, Transform parent, Vector3 local, float scale)
        {
            if (m_boxTemplate == null) return null;
            return BoxView.Create(m_boxTemplate, parent, name, local, scale);
        }

        public Transform RowsRoot { get { return m_rowsRoot.transform; } }

        /// <summary>Build a row and add it under the others (the first row added takes the focus).</summary>
        public T Add<T>(T row) where T : EdRow
        {
            row.ui = this;
            row.root = new GameObject(row.GetType().Name);
            row.root.layer = m_root.layer;
            row.root.transform.SetParent(m_rowsRoot.transform, false);
            row.root.transform.localPosition = new Vector3(0f, row.y, 0f);
            row.Build();
            m_rows.Add(row);
            if (m_rows.Count == 1) { m_focus = 0; }
            RefreshAll();
            return row;
        }

        /// <summary>Focus a row, with the menu's move sound.</summary>
        public void Focus(EdRow row)
        {
            int i = m_rows.IndexOf(row);
            if (i < 0 || i == m_focus) return;
            m_focus = i;
            Sound(false);
            RefreshAll();
        }

        public EdRow Focused { get { return m_focus >= 0 && m_focus < m_rows.Count ? m_rows[m_focus] : null; } }

        /// <summary>Redraw every row.</summary>
        public void RefreshAll()
        {
            for (int i = 0; i < m_rows.Count; i++) m_rows[i].Refresh(i == m_focus);
        }

        /// <summary>The menu's sound: the action sound, or the move sound.</summary>
        public void Sound(bool action)
        {
            try { var s = action ? m_sndAction : m_sndMove; if (s != null) s.Play(); } catch { }
        }

        /// <summary>Refuse (a locked or impossible choice): the editor shakes.</summary>
        public void Deny() { m_shake = 0.24f; }

        bool MoveFocus(int dir)
        {
            for (int i = m_focus + dir; i >= 0 && i < m_rows.Count; i += dir)
                if (m_rows[i].Focusable) { m_focus = i; Sound(false); RefreshAll(); m_rows[i].Enter(dir); return true; }
            return false;
        }

        // ------------------------------------------------------------------ input
        void Update()
        {
            if (!IsOpen || Panel == null || m_root == null) return;
            if (m_shake > 0f)
            {
                m_shake -= Time.unscaledDeltaTime;
                float k = m_shake > 0f ? Mathf.Sign(Mathf.Sin(m_shake * 90f)) * 1f : 0f;
                m_root.transform.localPosition = m_rootBase + new Vector3(k, 0f, 0f);
            }
            if (Time.frameCount <= m_openFrame + 1) return;   // the press that opened us
            var pd = SystemPlayers.GetPlayer(PlayerId);
            if (pd == null) return;
            bool mouse = pd.ControllerId == eController.Mouse;
            foreach (var r0 in m_rows) { var cr = r0 as CycleRow; if (cr != null) cr.Tick(); }
            CheckPortrait();
            var row = Focused;
            Vector2 rm;
            if (!mouse && CompatOnline.RemoteMenuMouse(PlayerId, out rm))
            {
                // an online player pointing with their mouse (Crawl Online): hover focuses, left click (Action) clicks
                for (int i = 0; i < m_rows.Count; i++)
                    if (m_rows[i].Focusable && m_rows[i].Hover(rm) && i != m_focus) { m_focus = i; Sound(false); RefreshAll(); }
                row = Focused;
                if (SystemInput.InputDown(eInput.Alt, PlayerId)) { Sound(false); if (onBack != null) onBack(); return; }
                if (SystemInput.InputDown(eInput.Action, PlayerId)) { if (row != null && row.Hover(rm)) row.Click(rm); return; }
                // keys / stick still work below (their keyboard arrows end mouse mode on their side anyway)
            }
            if (mouse)
            {
                Vector2 m = SystemInput.GetMousePos();
                for (int i = 0; i < m_rows.Count; i++)
                    if (m_rows[i].Focusable && m_rows[i].Hover(m) && i != m_focus) { m_focus = i; Sound(false); RefreshAll(); }
                row = Focused;
                if (Input.GetMouseButtonDown(0) && row != null && row.Hover(m)) row.Click(m);
                float w = Input.GetAxis("Mouse ScrollWheel");
                if (Mathf.Abs(w) > 0.01f && row != null && row.Hover(m)) row.Wheel(w > 0f ? -1 : 1);
                if (SystemInput.InputDown(eInput.Alt, PlayerId)) { Sound(false); if (onBack != null) onBack(); }
                return;
            }
            if (SystemInput.InputDown(eInput.Alt, PlayerId)) { Sound(false); if (onBack != null) onBack(); return; }
            if (row == null) return;
            if (SystemInput.InputDown(eInput.Up, PlayerId)) { if (!row.Up()) MoveFocus(-1); }
            else if (SystemInput.InputDown(eInput.Down, PlayerId)) { if (!row.Down()) MoveFocus(1); }
            else if (SystemInput.InputDown(eInput.Left, PlayerId)) row.Step(-1);
            else if (SystemInput.InputDown(eInput.Right, PlayerId)) row.Step(1);
            else if (SystemInput.InputDown(eInput.Action, PlayerId) || SystemInput.InputDown(eInput.Start, PlayerId)) row.Press();
        }

        /// <summary>Move focus to the next focusable row (after a pick).</summary>
        public void Next() { MoveFocus(1); }
        /// <summary>Focus a row without a sound.</summary>
        public void FocusRow(EdRow r) { int i = m_rows.IndexOf(r); if (i >= 0) { m_focus = i; RefreshAll(); } }
    }
}
