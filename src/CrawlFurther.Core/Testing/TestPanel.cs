using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Testing
{
    /// <summary>
    /// The test panel: an IMGUI window opened with <see cref="TestMode.PanelKey"/>, laid out for 1080p and scaled with
    /// the screen height. A page per section: its buttons and switches on the left, its lists side by side on the right.
    /// Clicks are queued and run in Update, outside the GUI pass.
    /// </summary>
    sealed class TestPanel : MonoBehaviour
    {
        // layout units are 1080p pixels; GUI.matrix scales them to the screen
        const float BaseHeight = 1080f;
        const float Width = 1180f, Height = 700f;
        const float ControlsWidth = 360f, ListWidth = 250f, ListHeight = 470f, RowHeight = 30f;
        /// <summary>The font size of a list row whose label is too long for the row at the normal 16.</summary>
        const int SmallFont = 12;
        const float RepauseDelay = 0.4f;
        const int WindowId = 0x7E57;

        static TestPanel s_panel;

        bool m_open, m_pauseWanted, m_pausedByUs, m_online, m_cursorWas;
        float m_repauseAt = -1f;
        CursorLockMode m_lockWas;
        int m_page;
        Rect m_rect;
        Vector2 m_controlsScroll, m_listsScroll;
        Action m_queued;
        string m_queuedName;
        readonly Dictionary<TestNumber, string> m_numberText = new Dictionary<TestNumber, string>();

        GUIStyle m_window, m_label, m_head, m_group, m_dim, m_note, m_button, m_lit, m_toggle, m_field;
        GUIStyle m_groupSmall, m_buttonSmall, m_litSmall;

        /// <summary>
        /// SystemTime.PauseGame disables every behaviour in the scene except those on layers 17 and 23 (the game's own
        /// menus), so the panel lives on layer 23: it has to keep running to unpause what it paused.
        /// </summary>
        internal static void Create()
        {
            if (s_panel != null) return;
            var go = new GameObject("CrawlFurther.TestPanel");
            go.layer = 23;
            DontDestroyOnLoad(go);
            s_panel = go.AddComponent<TestPanel>();
        }

        internal static bool Exists { get { return s_panel != null; } }

        /// <summary>The panel is up: the mouse belongs to it (see Patch_TestPanelMouse).</summary>
        internal static bool IsOpen { get { return s_panel != null && s_panel.m_open; } }

        void Awake() { useGUILayout = false; }

        void Update()
        {
            bool online = TestMode.Online;
            if (online != m_online)
            {
                m_online = online;
                VanillaDebug.SetActive(!online);
                if (online) { Close(); TestMode.SwitchOff(); TestMode.Say("Test mode is off online"); }
            }
            if (Input.GetKeyDown(TestMode.PanelKey))
            {
                if (online) TestMode.Say("Test mode is off online");
                else if (m_open) Close();
                else Open();
            }
            // IMGUI's layout pass runs for every component that asks for it: only while the window is up
            useGUILayout = m_open;
            if (online) return;
            TestCheats.Tick();
            if (m_queued != null)
            {
                var run = m_queued; var name = m_queuedName;
                m_queued = null;
                if (m_pausedByUs) { Pause(false); m_repauseAt = Time.unscaledTime + RepauseDelay; }
                TestMode.Run(name, run);
            }
            if (m_repauseAt > 0f && Time.unscaledTime >= m_repauseAt)
            {
                m_repauseAt = -1f;
                if (m_open && m_pauseWanted) Pause(true);
            }
            if (m_open) Cursor.visible = true;
            useGUILayout = m_open;
        }

        void Open()
        {
            m_open = true;
            m_cursorWas = Cursor.visible;
            m_lockWas = Cursor.lockState;
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
            TestMode.RefreshLists();
            if (m_pauseWanted) Pause(true);
        }

        void Close()
        {
            if (!m_open) return;
            m_open = false;
            m_repauseAt = -1f;
            Pause(false);
            Cursor.lockState = m_lockWas;
            Cursor.visible = m_cursorWas;
        }

        /// <summary>The game's own pause (MenuDebug uses it too), never stacked on the game's pause menu.</summary>
        void Pause(bool on)
        {
            if (!Singleton<SystemTime>.HasInstance()) { m_pausedByUs = false; return; }
            if (on && !m_pausedByUs && !SystemTime.Paused) { SystemTime.PauseGame(); m_pausedByUs = true; }
            else if (!on && m_pausedByUs) { m_pausedByUs = false; if (SystemTime.Paused) SystemTime.UnPauseGame(); }
        }

        void Queue(string name, Action run) { m_queuedName = name; m_queued = run; }

        void OnDestroy() { if (s_panel == this) s_panel = null; }

        // ------------------------------------------------------------------ drawing

        void OnGUI()
        {
            if (TestCheats.Hitboxes && !m_online && Event.current.type == EventType.Repaint) HitboxOverlay.Draw();
            float scale = Mathf.Max(0.5f, Screen.height / BaseHeight);
            if (!m_open)
            {
                var msg = TestMode.Message;
                if (msg == null || Event.current.type != EventType.Repaint) return;
                Styles();
                GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));
                // wrapped to the screen: a long message takes more lines, never runs off the edge
                float mw = Mathf.Min(1000f, Screen.width / scale - 32f);
                m_msg.text = msg;
                GUI.Label(new Rect(16f, 80f, mw, m_note.CalcHeight(m_msg, mw)), m_msg, m_note);
                GUI.matrix = Matrix4x4.identity;
                return;
            }
            Styles();
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));
            float sw = Screen.width / scale, sh = Screen.height / scale;
            if (m_rect.width <= 0f)
            {
                float w = Mathf.Min(Width, sw - 20f), h = Mathf.Min(Height, sh - 20f);
                m_rect = new Rect((sw - w) * 0.5f, Mathf.Max(10f, (sh - h) * 0.4f), w, h);
            }
            m_rect = GUI.Window(WindowId, m_rect, DrawWindow, "Test mode", m_window);
            m_rect.x = Mathf.Clamp(m_rect.x, 40f - m_rect.width, sw - 40f);
            m_rect.y = Mathf.Clamp(m_rect.y, 0f, sh - 30f);
            GUI.matrix = Matrix4x4.identity;
        }

        void DrawWindow(int id)
        {
            var sections = TestMode.Sections;
            if (sections.Count == 0) { GUILayout.Label("Nothing registered", m_label); return; }
            m_page = Mathf.Clamp(m_page, 0, sections.Count - 1);

            GUILayout.BeginHorizontal();
            for (int i = 0; i < sections.Count; i++)
                if (GUILayout.Button(sections[i].Name, i == m_page ? m_lit : m_button)) m_page = i;
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("Close (" + TestMode.PanelKey + ")", m_button)) Queue("Close", Close);
            GUILayout.EndHorizontal();

            DrawPlayerRow();
            GUILayout.Label(TestMode.Message ?? " ", m_note);

            var page = sections[m_page];
            GUILayout.BeginHorizontal();
            if (page.Controls.Count > 0)
            {
                m_controlsScroll = GUILayout.BeginScrollView(m_controlsScroll, GUILayout.Width(ControlsWidth));
                foreach (var c in page.Controls) DrawControl(c);
                GUILayout.EndScrollView();
            }
            if (page.Lists.Count > 0)
            {
                m_listsScroll = GUILayout.BeginScrollView(m_listsScroll);
                GUILayout.BeginHorizontal();
                foreach (var l in page.Lists) DrawList(l);
                GUILayout.EndHorizontal();
                GUILayout.EndScrollView();
            }
            GUILayout.EndHorizontal();
            GUI.DragWindow(new Rect(0f, 0f, 10000f, 28f));
        }

        void DrawPlayerRow()
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label("Acting for:", m_label, GUILayout.ExpandWidth(false));
            var auto = TestMode.Slot < 0 ? TestMode.Player : null;
            if (GUILayout.Button("Auto" + (auto != null ? " (" + Describe(auto) + ")" : ""), TestMode.Slot < 0 ? m_lit : m_button)) TestMode.Slot = -1;
            if (Singleton<SystemPlayers>.HasInstance())
                foreach (var p in SystemPlayers.GetPlayers())
                    if (p != null && p.IsActive && GUILayout.Button(Describe(p), TestMode.Slot == p.Id ? m_lit : m_button)) TestMode.Slot = p.Id;
            GUILayout.FlexibleSpace();
            bool pause = GUILayout.Toggle(m_pauseWanted, "Pause while open", m_toggle);
            if (pause != m_pauseWanted)
            {
                m_pauseWanted = pause;
                Queue("Pause", () => Pause(pause));
            }
            GUILayout.EndHorizontal();
        }

        static string Describe(PlayerData p)
        {
            string s = "P" + (p.Id + 1);
            if (p.IsHero) s += " hero";
            else if (p.GameObject != null && !p.IsAlive) s += " ghost";
            if (p.IsBot) s += " bot";
            return s;
        }

        void DrawControl(TestControl c)
        {
            var action = c as TestAction;
            if (action != null)
            {
                if (GUILayout.Button(action.Name, m_button)) Queue(action.Name, action.Run);
                return;
            }
            var toggle = c as TestToggle;
            if (toggle != null)
            {
                bool now = false;
                try { now = toggle.Get(); } catch { }
                bool next = GUILayout.Toggle(now, toggle.Name, m_toggle);
                if (next != now) Queue(toggle.Name, () => toggle.Set(next));
                return;
            }
            var number = c as TestNumber;
            if (number != null) { DrawNumber(number); return; }
            var choice = c as TestChoice;
            if (choice != null)
            {
                GUILayout.Label(choice.Name, m_label);
                int cur = -1;
                try { cur = choice.Get(); } catch { }
                GUILayout.BeginHorizontal();
                for (int i = 0; i < choice.Options.Length; i++)
                {
                    int pick = i;
                    if (GUILayout.Button(choice.Options[i], i == cur ? m_lit : m_button)) Queue(choice.Name, () => choice.Set(pick));
                }
                GUILayout.EndHorizontal();
            }
        }

        void DrawNumber(TestNumber n)
        {
            string text;
            if (!m_numberText.TryGetValue(n, out text)) text = n.Value.ToString();
            GUILayout.Label(n.Name, m_label);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("-", m_button, GUILayout.Width(36f))) { n.Value = Mathf.Max(n.Min, n.Value - 1); text = n.Value.ToString(); }
            text = GUILayout.TextField(text, 6, m_field, GUILayout.Width(80f));
            int typed;
            if (int.TryParse(text, out typed)) n.Value = Mathf.Clamp(typed, n.Min, n.Max);
            if (GUILayout.Button("+", m_button, GUILayout.Width(36f))) { n.Value = Mathf.Min(n.Max, n.Value + 1); text = n.Value.ToString(); }
            if (GUILayout.Button("Go", m_button))
            {
                int v = n.Value;
                Queue(n.Name, () => n.Run(v));
            }
            GUILayout.EndHorizontal();
            m_numberText[n] = text;
        }

        /// <summary>Only the rows in view are drawn: a list can hold hundreds of entries and IMGUI handles every control
        /// several times a frame.</summary>
        void DrawList(TestList l)
        {
            GUILayout.BeginVertical(GUILayout.Width(ListWidth));
            GUILayout.Label(l.Name, m_head);
            var items = l.Items;
            bool search = items.Count > TestList.SearchFrom;
            if (search) l.Filter = GUILayout.TextField(l.Filter ?? "", 40, m_field);
            var rows = l.Rows(search ? (l.Filter ?? "").Trim() : "");
            float h = search ? ListHeight - 30f : ListHeight;
            Rect box = GUILayoutUtility.GetRect(ListWidth, h, GUILayout.Width(ListWidth), GUILayout.Height(h));
            if (rows.Count == 0)
            {
                GUI.Label(box, items.Count == 0 ? "Nothing to show yet" : "No match", m_dim);
                GUILayout.EndVertical();
                return;
            }
            var view = new Rect(0f, 0f, box.width - 20f, rows.Count * RowHeight);
            l.Scroll = GUI.BeginScrollView(box, l.Scroll, view);
            int first = Mathf.Max(0, (int)(l.Scroll.y / RowHeight));
            int last = Mathf.Min(rows.Count, first + (int)(h / RowHeight) + 2);
            for (int i = first; i < last; i++)
            {
                var row = rows[i];
                var r = new Rect(0f, i * RowHeight, view.width, RowHeight - 2f);
                if (row.Item == null) { GUI.Label(r, row.Label, Fit(row.Label, m_group, m_groupSmall, r.width)); continue; }
                var item = row.Item;
                bool lit = l.IsSelected(item);
                if (GUI.Button(r, item.Label, Fit(item.Label, lit ? m_lit : m_button, lit ? m_litSmall : m_buttonSmall, r.width))) Queue(item.Label, () => l.Pick(item));
            }
            GUI.EndScrollView();
            GUILayout.EndVertical();
        }

        readonly GUIContent m_msg = new GUIContent(), m_fit = new GUIContent();

        /// <summary>A list row's style: its own, or the smaller one when the label is wider than the row (rows are one
        /// line high, so a long name would be cut).</summary>
        GUIStyle Fit(string label, GUIStyle normal, GUIStyle small, float width)
        {
            m_fit.text = label;
            return normal.CalcSize(m_fit).x <= width ? normal : small;
        }

        /// <summary>Sizes are for 1080p; GUI.matrix scales them with the screen.</summary>
        void Styles()
        {
            if (m_window != null) return;
            var skin = GUI.skin;
            m_window = new GUIStyle(skin.window) { fontSize = 18, fontStyle = FontStyle.Bold };
            m_window.padding = new RectOffset(12, 12, 32, 12);
            m_label = new GUIStyle(skin.label) { fontSize = 16, wordWrap = true };
            m_head = new GUIStyle(m_label) { fontStyle = FontStyle.Bold, fontSize = 17 };
            m_group = new GUIStyle(m_label) { fontStyle = FontStyle.Bold, fontSize = 15 };
            m_group.normal.textColor = new Color(1f, 0.85f, 0.45f);
            m_group.wordWrap = false;
            m_groupSmall = new GUIStyle(m_group) { fontSize = SmallFont };
            m_dim = new GUIStyle(m_label);
            m_dim.normal.textColor = new Color(0.7f, 0.7f, 0.7f);
            m_note = new GUIStyle(m_label) { fontStyle = FontStyle.Bold };
            m_note.normal.textColor = new Color(0.55f, 0.9f, 1f);
            m_button = new GUIStyle(skin.button) { fontSize = 16, alignment = TextAnchor.MiddleLeft, wordWrap = false };
            m_button.padding = new RectOffset(8, 8, 4, 4);
            m_lit = new GUIStyle(m_button) { fontStyle = FontStyle.Bold };
            m_lit.normal.textColor = m_lit.hover.textColor = new Color(1f, 0.85f, 0.3f);
            m_lit.normal.background = m_button.active.background;
            m_buttonSmall = new GUIStyle(m_button) { fontSize = SmallFont };
            m_litSmall = new GUIStyle(m_lit) { fontSize = SmallFont };
            m_toggle = new GUIStyle(skin.toggle) { fontSize = 16 };
            m_field = new GUIStyle(skin.textField) { fontSize = 16 };
        }
    }
}
