using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Compat;
    using CrawlFurther.Util;

    /// <summary>
    /// Draws the tips with the game's own GUI text: TextMeshes using the HUD's font and material (taken from the
    /// player name on GUIPlayer), on the HUD's layer, in front of the GUI camera.
    /// Every tip belongs to one player (P1-P4, any controller) and sits just above THAT player's own HUD panel (the
    /// game's GUIPlayer row along the bottom: the panel's measured centre, kept inside the player's own column, above
    /// the tallest HUD element so it never covers hearts, gold, the wrath bar or the hero's stats), with the player's
    /// colour on its title and on an accent bar, and a "P2" tag when more than one human plays.
    /// One tip per player at a time: a new monster tip replaces that player's tip, other tips wait in a short queue
    /// (two at most) and are dropped when stale (8 s old or another room). With 3 or 4 HUD panels the tips are compact:
    /// smaller, two body lines at most, 5 s. A tip fades to a third while the hero (or its own player) is behind it.
    /// Nothing is allocated per frame; the objects are made once and reused. Falls back to OnGUI only if the HUD text
    /// can't be found.
    /// </summary>
    public class TipView : MonoBehaviour
    {
        static TipView s_inst;

        class Pending
        {
            public string title, body;
            public int lines, room;
            public Color colour;
            public float at;
            public bool compact;
        }

        class Slot
        {
            public GameObject root;
            public TextMesh title, body, titleShadow, bodyShadow;
            public Renderer rTitle, rBody, rTitleShadow, rBodyShadow;
            public GameObject panel, accent;          // dark backing so the text reads on any floor; the player-colour bar
            public Mesh panelMesh, accentMesh;
            public Renderer rPanel, rAccent;
            public bool active, visible, dirty, compact;
            public float t, alpha = -1f;
            public int measure, appliedFrame, room;
            public float wait;
            public float show = MonsterTips.ShowTime;  // seconds at full alpha (longer for longer tips)
            public float w0, h0, lineH0;             // block width / height / one body line at fit 1 (world units)
            public float fit = -1f;                   // applied scale on top of the HUD scale
            public float dim = 1f;                    // 0.3 while the hero is behind the tip
            public int lines = 2;
            public Color colour;
            public string titleText, bodyText;
            public readonly List<Pending> queue = new List<Pending>(3);
        }

        public const int Players = 4;
        /// <summary>Compact tips (3-4 HUD panels): seconds shown, body lines at most.</summary>
        public const float CompactShowTime = 5f;
        public const int CompactLines = 2;
        /// <summary>A queued tip older than this (or from another room) is dropped instead of shown.</summary>
        public const float StaleAfter = 8f;
        /// <summary>Body line height as a share of the screen height (normal / compact).</summary>
        public const float LineHeight = 0.024f, CompactLineHeight = 0.02f;
        /// <summary>The game's HUD columns (GUIGame.m_plrOffset1-4: each panel's left edge as a share of the width) and
        /// the panel's assumed width there, used until the panels themselves can be measured.</summary>
        static readonly float[][] Offsets =
        {
            new[] { 0.04f }, new[] { 0.04f, 0.775f }, new[] { 0.04f, 0.39f, 0.775f }, new[] { 0.04f, 0.29f, 0.525f, 0.775f },
        };
        const float PanelGuess = 0.2f, HudTopGuess = 0.17f, Margin = 0.012f;

        readonly Slot[] m_slots = new Slot[Players];

        // the HUD's text style
        Font m_font;
        Material m_mat;
        int m_fontSize, m_layer = -1, m_sortLayer, m_sortOrder;
        float m_charSize = 1f;
        Vector3 m_scale = Vector3.one;
        Camera m_cam, m_gameCam;
        float m_nextResolve, m_nextHud, m_nextGameCam;
        bool m_useGui;
        GUIStyle m_style, m_shadowStyle;

        // the HUD layout (viewport units), measured twice a second while a tip shows
        readonly float[] m_cx = new float[Players], m_x0 = new float[Players], m_x1 = new float[Players];
        float m_hudEdge = HudTopGuess;
        bool m_hudBottom = true;
        int m_columns = 1;

        static readonly Color BodyColour = new Color(0.93f, 0.9f, 0.82f, 1f);
        static readonly Color PanelColour = new Color(0.05f, 0.04f, 0.07f, 0.78f);
        Material m_panelMat;
        readonly Color[] m_cols4 = new Color[4];

        // OnGUI only draws with GUI.Label (no GUILayout): skip IMGUI's per-frame layout pass
        void Awake() { useGUILayout = false; }

        public static TipView Get()
        {
            if (s_inst == null)
            {
                var go = new GameObject("CrawlMod_MonsterTips");
                DontDestroyOnLoad(go);
                s_inst = go.AddComponent<TipView>();
            }
            return s_inst;
        }

        public static void HideAll()
        {
            if (s_inst == null) return;
            foreach (var s in s_inst.m_slots) if (s != null) { s.queue.Clear(); s_inst.Deactivate(s); }
        }

        /// <summary>HUD panels on screen (1-4): 3 or more means compact tips.</summary>
        static int Columns()
        {
            try { return Mathf.Clamp(SystemPlayers.GetNumActivePlayers(), 1, Players); } catch { return 1; }
        }

        /// <summary>A tip for one player. It waits its turn behind that player's current tip (see the other overload).</summary>
        public void Show(int playerId, string title, string attack, string special, string passive, Color colour)
        {
            Show(playerId, title, attack, special, passive, colour, false);
        }

        /// <summary>replace: this tip is about what the player is right now (a monster body): it replaces their tip at
        /// once and drops what was queued; otherwise it queues behind it.</summary>
        public void Show(int playerId, string title, string attack, string special, string passive, Color colour, bool replace)
        {
            if (playerId < 0 || playerId >= Players || !MonsterTips.ShowFor(playerId)) return;
            var s = m_slots[playerId];
            if (s == null) s = m_slots[playerId] = new Slot();
            bool compact = Columns() >= 3;
            var p = new Pending { title = title, colour = colour, at = Time.unscaledTime, room = MonsterTips.RoomId(), compact = compact };
            // body: attack + special (+ passive, which may run to more lines); compact keeps two lines
            int lines = string.IsNullOrEmpty(special) ? 1 : 2;
            string body = lines == 2 ? attack + "\n" + special : attack;
            if (!compact && !string.IsNullOrEmpty(passive))
            {
                body += "\n" + passive;
                lines++;
                for (int i = 0; i < passive.Length; i++) if (passive[i] == '\n') lines++;
            }
            p.body = body; p.lines = lines;
            if (replace || !s.active) { s.queue.Clear(); Begin(s, p); return; }
            if (s.queue.Count >= 2) s.queue.RemoveAt(0);
            s.queue.Add(p);
        }

        void Begin(Slot s, Pending p)
        {
            s.titleText = p.title;
            s.bodyText = p.body;
            s.lines = p.lines;
            s.compact = p.compact;
            s.room = p.room;
            s.show = p.compact ? CompactShowTime : MonsterTips.ShowTime + MonsterTips.ShowPerLine * Mathf.Max(0, s.lines - 2);
            s.colour = p.colour;
            s.t = 0f;
            s.active = true;
            s.wait = 0f;
            s.dirty = true;   // the text meshes are (re)filled in LateUpdate, once the HUD style and camera are known
            m_nextResolve = 0f;
            m_nextHud = 0f;
        }

        /// <summary>The slot's tip is over: show the next queued one that is still fresh.</summary>
        void Next(Slot s)
        {
            Deactivate(s);
            int room = MonsterTips.RoomId();
            while (s.queue.Count > 0)
            {
                var p = s.queue[0];
                s.queue.RemoveAt(0);
                if (Time.unscaledTime - p.at <= StaleAfter && p.room == room) { Begin(s, p); return; }
            }
        }

        /// <summary>Fill a slot's text meshes with its new text (made once per slot, then reused).</summary>
        void Apply(Slot s)
        {
            Build(s);
            s.dirty = false;
            s.title.text = s.titleText; s.titleShadow.text = s.titleText;
            s.body.text = s.bodyText; s.bodyShadow.text = s.bodyText;
            s.root.transform.localScale = m_scale;
            s.fit = -1f;
            s.alpha = -1f;
            s.dim = 1f;
            s.measure = 4;   // measured over the next frames (bounds exist once the meshes are built), invisible until then
            s.appliedFrame = Time.frameCount;
            SetAlpha(s, 0f);
        }

        void Deactivate(Slot s)
        {
            s.active = false;
            if (s.root != null) SetVisible(s, false);
        }

        // ---- style and camera
        bool Resolve()
        {
            if (m_font != null && m_cam != null && m_layer >= 0) { m_useGui = false; return true; }
            if (Time.unscaledTime < m_nextResolve) return !m_useGui && m_font != null && m_cam != null;
            m_nextResolve = Time.unscaledTime + 1f;
            try
            {
                TextMesh src = null;
                Camera cam = null;
                foreach (var gp in FindObjectsOfType<GUIPlayer>())
                {
                    var tm = R.Get<TextMesh>(gp, "m_name");
                    if (tm == null || tm.font == null) continue;
                    src = tm;
                    var sa = gp.GetComponent<ScreenAlign>();
                    if (sa != null) cam = sa.m_camera;
                    if (m_panelMat == null)
                    {
                        // a vertex-coloured quad: Unity's built-in sprite/text shaders multiply by vertex colour;
                        // the HUD text's own shader (a font shader, alpha from the texture) is the last resort
                        var r0 = tm.GetComponent<Renderer>();
                        Shader sh = Shader.Find("Sprites/Default") ?? Shader.Find("GUI/Text Shader") ??
                                    (r0 != null && r0.sharedMaterial != null ? r0.sharedMaterial.shader : null);
                        if (sh != null)
                        {
                            var white = new Texture2D(1, 1, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
                            white.SetPixel(0, 0, Color.white); white.Apply();
                            m_panelMat = new Material(sh) { mainTexture = white, name = "CrawlMod_TipPanel" };
                            FurtherCore.Log.LogInfo("Monster tips: panel shader " + sh.name);
                        }
                    }
                    break;
                }
                if (src != null && m_font == null)
                {
                    m_font = src.font;
                    var r = src.GetComponent<Renderer>();
                    m_mat = r != null && r.sharedMaterial != null ? r.sharedMaterial : src.font.material;
                    m_fontSize = src.fontSize;
                    m_charSize = src.characterSize;
                    m_layer = src.gameObject.layer;
                    if (r != null) { m_sortLayer = r.sortingLayerID; m_sortOrder = r.sortingOrder; }
                    var ls = src.transform.lossyScale;
                    m_scale = new Vector3(Mathf.Abs(ls.x) > 0.0001f ? Mathf.Abs(ls.x) : 1f, Mathf.Abs(ls.y) > 0.0001f ? Mathf.Abs(ls.y) : 1f, 1f);
                    FurtherCore.Log.LogInfo("Monster tips: using the HUD font '" + m_font.name + "' (size " + m_fontSize + ", char " + m_charSize + ", layer " + m_layer + ")");
                }
                if (cam == null)
                {
                    try { if (Singleton<SystemLevel>.HasInstance()) cam = SystemLevel.GetCameraGUI(); } catch { }
                }
                if (cam == null)
                {
                    // the game's own rule for its GUI camera (ScreenAlign, EffectTextMarquee): the one far back in z
                    foreach (var c in FindObjectsOfType<Camera>())
                        if (c.transform.position.z < -500f && (m_layer < 0 || (c.cullingMask & (1 << m_layer)) != 0)) { cam = c; break; }
                }
                if (cam != null) m_cam = cam;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Monster tips: HUD lookup failed: " + e.Message); }
            m_useGui = m_font == null || m_layer < 0;
            return !m_useGui && m_cam != null;
        }

        /// <summary>
        /// Where each player's HUD panel is (viewport units): its centre x, the column it may use (half way to the
        /// next panel), and the edge of the whole HUD row the tips sit against (the top of its tallest element when the
        /// row is along the bottom). Until a panel can be measured, the game's own column offsets stand in.
        /// </summary>
        void MeasureHud()
        {
            int n = Columns();
            m_columns = n;
            var offs = Offsets[n - 1];
            int rank = 0;
            for (int i = 0; i < Players; i++)
            {
                m_cx[i] = -1f;
                try
                {
                    var pd = SystemPlayers.GetPlayer(i);
                    if (pd != null && pd.IsActiveNonTemporary && rank < n) { m_cx[i] = offs[rank] + PanelGuess * 0.5f; rank++; }
                }
                catch { }
            }
            float top = -1f, bottom = 2f;
            int measured = 0, below = 0;
            if (m_cam != null)
            {
                try
                {
                    foreach (var gp in FindObjectsOfType<GUIPlayer>())
                    {
                        if (!gp.gameObject.activeInHierarchy) continue;
                        float x0 = 2f, x1 = -1f, y0 = 2f, y1 = -1f;
                        foreach (var r in gp.GetComponentsInChildren<Renderer>())
                        {
                            if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                            var b = r.bounds;
                            if (b.size.x <= 0f && b.size.y <= 0f) continue;
                            var a = m_cam.WorldToViewportPoint(b.min);
                            var c = m_cam.WorldToViewportPoint(b.max);
                            x0 = Mathf.Min(x0, a.x); x1 = Mathf.Max(x1, c.x); y0 = Mathf.Min(y0, a.y); y1 = Mathf.Max(y1, c.y);
                        }
                        if (x1 < x0 || y1 < y0) continue;
                        int id = gp.GetPlayerId();
                        if (id >= 0 && id < Players) m_cx[id] = Mathf.Clamp01((x0 + x1) * 0.5f);
                        measured++;
                        if ((y0 + y1) * 0.5f < 0.5f) below++;
                        top = Mathf.Max(top, y1); bottom = Mathf.Min(bottom, y0);
                    }
                    // the hero's stats (boss fights) share the row: keep clear of them too
                    foreach (var hs in FindObjectsOfType<GUIHeroStats>())
                    {
                        if (!hs.gameObject.activeInHierarchy) continue;
                        foreach (var r in hs.GetComponentsInChildren<Renderer>())
                        {
                            if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                            var b = r.bounds;
                            float a = m_cam.WorldToViewportPoint(b.min).y, c = m_cam.WorldToViewportPoint(b.max).y;
                            if ((a + c) * 0.5f < 0.5f) top = Mathf.Max(top, c); else bottom = Mathf.Min(bottom, a);
                        }
                    }
                }
                catch { }
            }
            m_hudBottom = measured == 0 || below * 2 >= measured;
            m_hudEdge = m_hudBottom ? (top > 0f && top < 0.6f ? top : HudTopGuess) : (bottom < 1f && bottom > 0.4f ? bottom : 1f - HudTopGuess);
            // columns: half way to the neighbouring panels
            for (int i = 0; i < Players; i++)
            {
                if (m_cx[i] < 0f) continue;
                float left = 0.01f, right = 0.99f;
                for (int j = 0; j < Players; j++)
                {
                    if (j == i || m_cx[j] < 0f) continue;
                    float mid = (m_cx[i] + m_cx[j]) * 0.5f;
                    if (m_cx[j] < m_cx[i] || (m_cx[j] == m_cx[i] && j < i)) left = Mathf.Max(left, mid);
                    else right = Mathf.Min(right, mid);
                }
                m_x0[i] = left; m_x1[i] = right;
            }
        }

        Camera GameCamera()
        {
            if (m_gameCam != null && m_gameCam.isActiveAndEnabled) return m_gameCam;
            if (Time.unscaledTime < m_nextGameCam) return null;
            m_nextGameCam = Time.unscaledTime + 1f;
            try
            {
                var cm = Singleton<SystemLevel>.HasInstance() ? SystemLevel.GetCamera() : null;
                m_gameCam = cm != null ? cm.GetComponent<Camera>() : null;
            }
            catch { m_gameCam = null; }
            return m_gameCam;
        }

        void Build(Slot s)
        {
            if (s.root != null) return;
            s.root = new GameObject("Tip");
            s.root.layer = m_layer;
            s.root.transform.SetParent(transform, false);
            s.titleShadow = MakeText(s.root.transform, "TitleShadow", 1, out s.rTitleShadow);
            s.title = MakeText(s.root.transform, "Title", 2, out s.rTitle);
            s.bodyShadow = MakeText(s.root.transform, "BodyShadow", 1, out s.rBodyShadow);
            s.body = MakeText(s.root.transform, "Body", 2, out s.rBody);
            if (m_panelMat != null)
            {
                s.panel = MakeQuad(s.root.transform, "Panel", 0, out s.panelMesh, out s.rPanel);
                s.accent = MakeQuad(s.root.transform, "Accent", 1, out s.accentMesh, out s.rAccent);
            }
        }

        GameObject MakeQuad(Transform parent, string name, int sortAdd, out Mesh mesh, out Renderer rend)
        {
            var go = new GameObject(name);
            go.layer = m_layer;
            go.transform.SetParent(parent, false);
            mesh = new Mesh { name = "Tip" + name };
            mesh.vertices = new Vector3[4];
            mesh.uv = new[] { Vector2.zero, Vector2.up, Vector2.one, Vector2.right };
            mesh.colors = new Color[4];
            mesh.triangles = new[] { 0, 1, 2, 0, 2, 3 };
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = m_panelMat;
            mr.sortingLayerID = m_sortLayer;
            mr.sortingOrder = m_sortOrder + 20 + sortAdd;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            rend = mr;
            return go;
        }

        TextMesh MakeText(Transform parent, string name, int sortAdd, out Renderer rend)
        {
            var go = new GameObject(name);
            go.layer = m_layer;
            go.transform.SetParent(parent, false);
            var mr = go.AddComponent<MeshRenderer>();
            var tm = go.GetComponent<TextMesh>();
            if (tm == null) tm = go.AddComponent<TextMesh>();
            tm.font = m_font;
            tm.fontSize = m_fontSize;
            tm.characterSize = m_charSize;
            tm.anchor = TextAnchor.UpperCenter;
            tm.alignment = TextAlignment.Center;
            tm.richText = false;
            tm.lineSpacing = 1f;
            mr.sharedMaterial = m_mat;
            mr.sortingLayerID = m_sortLayer;
            mr.sortingOrder = m_sortOrder + 22 + sortAdd;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            rend = mr;
            return tm;
        }

        void SetAlpha(Slot s, float a)
        {
            if (Mathf.Abs(a - s.alpha) < 0.004f) return;
            s.alpha = a;
            var c = s.colour; c.a = a;
            s.title.color = c;
            var b = BodyColour; b.a = a;
            s.body.color = b;
            var k = new Color(0f, 0f, 0f, a * 0.85f);
            s.titleShadow.color = k;
            s.bodyShadow.color = k;
            if (s.panelMesh != null)
            {
                var pc = PanelColour; pc.a *= a;
                for (int i = 0; i < 4; i++) m_cols4[i] = pc;
                s.panelMesh.colors = m_cols4;
                CompatOnline.MeshChanged(s.panelMesh);    // Crawl Online only notices ex2D meshes by itself
            }
            if (s.accentMesh != null)
            {
                for (int i = 0; i < 4; i++) m_cols4[i] = c;
                s.accentMesh.colors = m_cols4;
                CompatOnline.MeshChanged(s.accentMesh);
            }
        }

        void SetVisible(Slot s, bool on)
        {
            if (s.visible == on || s.root == null) return;
            s.visible = on;
            s.rTitle.enabled = on; s.rBody.enabled = on; s.rTitleShadow.enabled = on; s.rBodyShadow.enabled = on;
            if (s.rPanel != null) s.rPanel.enabled = on;
            if (s.rAccent != null) s.rAccent.enabled = on;
        }

        static float AlphaAt(float t, float show)
        {
            if (t < MonsterTips.FadeInTime) return t / MonsterTips.FadeInTime;
            if (t < show) return 1f;
            return Mathf.Clamp01(1f - (t - show) / MonsterTips.FadeTime);
        }

        static bool Paused()
        {
            if (Time.timeScale <= 0f) return true;
            try { return Singleton<SystemTime>.HasInstance() && SystemTime.Paused; } catch { return false; }
        }

        void Update()
        {
            bool paused = Paused();
            float dt = Mathf.Min(Time.unscaledDeltaTime, 0.1f);
            bool any = false, dirty = false;
            for (int i = 0; i < Players; i++)
            {
                var s = m_slots[i];
                if (s == null || !s.active) continue;
                if (s.dirty)
                {
                    // no GUI camera yet (scene loading): give up on this tip after a few seconds
                    s.wait += dt;
                    if (s.wait > 3f) { Next(s); continue; }
                }
                else if (!paused) s.t += dt;
                if (s.t >= s.show + MonsterTips.FadeTime) { Next(s); if (!s.active) continue; }
                any = true;
                dirty |= s.dirty;
            }
            if (!any) return;
            // first tip, or a new scene: find the HUD style / its GUI camera (throttled to once a second)
            if (m_cam == null || dirty) Resolve();
            if (Time.unscaledTime >= m_nextHud) { m_nextHud = Time.unscaledTime + 0.5f; MeasureHud(); }
        }

        void LateUpdate()
        {
            if (m_useGui) return;
            bool paused = Paused();
            bool camOk = m_cam != null && m_cam.isActiveAndEnabled;
            float dt = Mathf.Min(Time.unscaledDeltaTime, 0.1f);
            Vector2 view = Vector2.zero;
            Vector3 origin = Vector3.zero;
            float z = 0f;
            bool haveView = false;
            Vector3 heroVp = new Vector3(-9f, -9f, 0f);
            for (int i = 0; i < Players; i++)
            {
                var s = m_slots[i];
                if (s == null) continue;
                if (s.active && s.dirty && camOk) Apply(s);
                if (s.root == null) continue;
                if (!s.active || s.dirty) { SetVisible(s, false); continue; }
                SetVisible(s, camOk && !paused);
                if (!camOk) continue;
                if (s.measure > 0 && s.appliedFrame != Time.frameCount) Measure(s);
                if (s.measure > 0) { SetAlpha(s, 0f); continue; }
                if (!haveView)
                {
                    haveView = true;
                    float dist = m_cam.nearClipPlane + 1f;
                    origin = m_cam.ViewportToWorldPoint(new Vector3(0f, 0f, dist));
                    var far = m_cam.ViewportToWorldPoint(new Vector3(1f, 1f, dist));
                    view = new Vector2(Mathf.Abs(far.x - origin.x), Mathf.Abs(far.y - origin.y));
                    z = m_cam.transform.position.z + dist;
                    heroVp = HeroViewport();
                }
                Place(s, i, view, origin, z, heroVp, dt);
                SetAlpha(s, AlphaAt(s.t, s.show) * s.dim);
            }
        }

        /// <summary>Size and place a player's tip in its column, against the HUD row; dim it while the hero is behind.</summary>
        void Place(Slot s, int id, Vector2 view, Vector3 origin, float z, Vector3 heroVp, float dt)
        {
            float cx = m_cx[id] >= 0f ? m_cx[id] : 0.5f;
            float x0 = m_cx[id] >= 0f ? m_x0[id] : 0.01f, x1 = m_cx[id] >= 0f ? m_x1[id] : 0.99f;
            float colW = (x1 - x0) * 0.94f * view.x;
            float lineTarget = view.y * (s.compact ? CompactLineHeight : LineHeight);
            float fit = s.lineH0 > 0f ? lineTarget / s.lineH0 : 1f;
            if (s.w0 * fit > colW && s.w0 > 0f) fit = colW / s.w0;
            if (Mathf.Abs(fit - s.fit) > 0.0005f)
            {
                s.fit = fit;
                s.root.transform.localScale = new Vector3(m_scale.x * fit, m_scale.y * fit, 1f);
            }
            float w = s.w0 * fit / view.x, h = s.h0 * fit / view.y;   // viewport units
            cx = Mathf.Clamp(cx, x0 + w * 0.5f, x1 - w * 0.5f);
            if (x1 - x0 < w) cx = (x0 + x1) * 0.5f;
            float topVp = m_hudBottom ? m_hudEdge + Margin + h : m_hudEdge - Margin;
            s.root.transform.position = new Vector3(origin.x + cx * view.x, origin.y + topVp * view.y, z);
            // the hero behind the tip: fade it so he is never hidden
            bool behind = heroVp.x > cx - w * 0.5f - 0.01f && heroVp.x < cx + w * 0.5f + 0.01f && heroVp.y > topVp - h - 0.02f && heroVp.y < topVp + 0.04f;
            float target = behind ? 0.3f : 1f;
            s.dim = Mathf.MoveTowards(s.dim, target, dt * 4f);
        }

        Vector3 HeroViewport()
        {
            try
            {
                var cam = GameCamera();
                var hero = SystemPlayers.GetHeroPlayerData();
                var go = hero != null ? hero.GameObject : null;
                if (cam == null || go == null) return new Vector3(-9f, -9f, 0f);
                return cam.WorldToViewportPoint(go.transform.position + new Vector3(0f, 8f, 0f));
            }
            catch { return new Vector3(-9f, -9f, 0f); }
        }

        /// <summary>The block's size at fit 1, once its text meshes have been built (bounds are known a frame later).</summary>
        void Measure(Slot s)
        {
            s.measure--;
            var bt = s.rTitle.bounds.size;
            var bb = s.rBody.bounds.size;
            if ((bt.x <= 0f || bb.x <= 0f) && s.measure > 0) return;   // not built yet: try next frame
            s.measure = 0;
            var ls = s.root.transform.lossyScale;
            float sx = Mathf.Max(0.0001f, Mathf.Abs(ls.x)), sy = Mathf.Max(0.0001f, Mathf.Abs(ls.y));
            // sizes at scale 1 (local units)
            float titleW = bt.x / sx, titleH = bt.y / sy, bodyW = bb.x / sx, bodyH = bb.y / sy;
            if (titleH <= 0f) titleH = m_charSize * Mathf.Max(1, m_fontSize) * 0.1f;
            float pad = titleH * 0.35f, bar = Mathf.Max(titleH * 0.14f, 0.0001f);
            float gap = titleH * 0.15f;
            s.w0 = (Mathf.Max(titleW, bodyW) + pad * 2f) * m_scale.x;
            s.h0 = (titleH + gap + bodyH + pad * 2f + bar) * m_scale.y;
            s.lineH0 = bodyH / Mathf.Max(1, s.lines) * m_scale.y;
            s.fit = -1f;
            float px = Mathf.Max(titleH / 9f, 0.0001f);   // one font pixel (a pixel font line is ~9 px tall)
            float y0 = -(pad + bar);                        // the text starts under the accent bar
            s.title.transform.localPosition = new Vector3(0f, y0, 0f);
            s.titleShadow.transform.localPosition = new Vector3(px, y0 - px, 0.05f);
            s.body.transform.localPosition = new Vector3(0f, y0 - (titleH + gap), 0f);
            s.bodyShadow.transform.localPosition = new Vector3(px, y0 - (titleH + gap) - px, 0.05f);
            float hw = Mathf.Max(titleW, bodyW) * 0.5f + pad, bottom = -(s.h0 / m_scale.y);
            if (s.panelMesh != null)
            {
                s.panelMesh.vertices = new[] { new Vector3(-hw, bottom, 0.1f), new Vector3(-hw, 0f, 0.1f), new Vector3(hw, 0f, 0.1f), new Vector3(hw, bottom, 0.1f) };
                s.panelMesh.RecalculateBounds();
                CompatOnline.MeshChanged(s.panelMesh);
            }
            if (s.accentMesh != null)
            {
                s.accentMesh.vertices = new[] { new Vector3(-hw, -bar, 0.08f), new Vector3(-hw, 0f, 0.08f), new Vector3(hw, 0f, 0.08f), new Vector3(hw, -bar, 0.08f) };
                s.accentMesh.RecalculateBounds();
                CompatOnline.MeshChanged(s.accentMesh);
            }
        }

        // ---- fallback when the HUD text can't be found (only then): each tip over its player's column
        void OnGUI()
        {
            if (!m_useGui) return;
            bool any = false;
            for (int i = 0; i < Players; i++) if (m_slots[i] != null && m_slots[i].active) { any = true; m_slots[i].dirty = false; }
            if (!any || Paused()) return;
            if (m_style == null)
            {
                m_style = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.LowerCenter, wordWrap = true, richText = false };
                m_shadowStyle = new GUIStyle(m_style);
                m_shadowStyle.normal.textColor = Color.black;
            }
            int fs = Mathf.Max(11, Screen.height / (m_columns >= 3 ? 60 : 50));
            m_style.fontSize = fs; m_shadowStyle.fontSize = fs;
            float lh = fs * 1.35f;
            var old = GUI.color;
            for (int i = 0; i < Players; i++)
            {
                var s = m_slots[i];
                if (s == null || !s.active) continue;
                float a = AlphaAt(s.t, s.show);
                float cx = (m_cx[i] >= 0f ? m_cx[i] : 0.5f) * Screen.width;
                float w = ((m_cx[i] >= 0f ? m_x1[i] - m_x0[i] : 0.9f) * 0.94f) * Screen.width;
                float bottom = Screen.height * (1f - HudTopGuess - Margin);
                float bodyH = lh * s.lines;
                DrawLine(new Rect(cx - w * 0.5f, bottom - bodyH, w, bodyH), s.bodyText, BodyColour, a);
                DrawLine(new Rect(cx - w * 0.5f, bottom - bodyH - lh, w, lh), s.titleText, s.colour, a);
            }
            GUI.color = old;
        }

        void DrawLine(Rect r, string text, Color c, float a)
        {
            GUI.color = new Color(1f, 1f, 1f, a);
            m_shadowStyle.normal.textColor = new Color(0f, 0f, 0f, 0.85f);
            GUI.Label(new Rect(r.x + 1, r.y + 1, r.width, r.height), text, m_shadowStyle);
            m_style.normal.textColor = c;
            GUI.Label(r, text, m_style);
        }
    }
}
