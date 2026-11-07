using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// Draws <see cref="HudTimers"/>. Each player's countdowns are children of that player's GUIPlayer panel, so they
    /// share its camera, layer and scale and move with it: the number in the HUD's own font (copied from the panel's
    /// name text) and the icon at the HUD's pixel size (copied from the panel's gold icon). They stack in a column beside
    /// the panel when the gap to the next panel (or the screen edge) is wide enough, else in a row just above the panel's
    /// right end. Panels are looked up and measured twice a second, and only while a countdown runs.
    /// </summary>
    internal class HudTimerView : MonoBehaviour
    {
        const int Players = 4;
        const float LookEvery = 0.5f, PausedAlpha = 0.45f;

        sealed class Item
        {
            public GameObject root;
            public exSprite icon;
            public Renderer iconR;
            public TextMesh text, shadow;
            public Renderer textR, shadowR;
            public SpriteSheet sheet;
            public int shown = -1;
            public float alpha = -1f;
            public bool measured;
            public int tries;
        }

        sealed class Panel
        {
            public GUIPlayer gp;
            public GameObject root;
            public readonly List<Item> items = new List<Item>();
            public Bounds bounds;
            public bool hasBounds;
            public float limitRight;       // world x the countdowns may not pass on the right
        }

        static HudTimerView s_inst;
        readonly Panel[] m_panels = new Panel[Players];
        float m_nextLook;
        bool m_shown;

        public static void Ensure()
        {
            if (s_inst != null) return;
            var go = new GameObject("CrawlFurther.HudTimers");
            DontDestroyOnLoad(go);
            s_inst = go.AddComponent<HudTimerView>();
        }

        static bool Paused()
        {
            if (Time.timeScale <= 0f) return true;
            try { return Singleton<SystemTime>.HasInstance() && SystemTime.Paused; } catch { return false; }
        }

        void LateUpdate()
        {
            if (!HudTimers.Any || Paused())
            {
                if (m_shown) HideAll();
                return;
            }
            try
            {
                if (Time.unscaledTime >= m_nextLook) { m_nextLook = Time.unscaledTime + LookEvery; Look(); }
                for (int i = 0; i < Players; i++) Draw(i);
                m_shown = true;
            }
            catch (Exception e)
            {
                FurtherCore.Log.LogWarning("HUD timers: " + e.Message);
                m_nextLook = Time.unscaledTime + 5f;
            }
        }

        void HideAll()
        {
            m_shown = false;
            foreach (var p in m_panels)
                if (p != null) foreach (var it in p.items) Show(it, false);
        }

        // ---- panels
        void Look()
        {
            var found = new GUIPlayer[Players];
            foreach (var gp in FindObjectsOfType<GUIPlayer>())
            {
                int id = gp.GetPlayerId();
                if (id >= 0 && id < Players && gp.gameObject.activeInHierarchy) found[id] = gp;
            }
            for (int i = 0; i < Players; i++)
            {
                var p = m_panels[i];
                if (p != null && p.gp != found[i])
                {
                    if (p.root != null) Destroy(p.root);
                    m_panels[i] = p = null;
                }
                if (p == null && found[i] != null && HudTimers.Players[i].Count > 0) m_panels[i] = p = new Panel { gp = found[i] };
                if (p != null) p.hasBounds = Measure(p.gp, p.root, out p.bounds);
            }
            // the room to the right of each panel: up to the next panel, or the screen edge
            var cam = Camera();
            float edge = cam != null ? cam.ViewportToWorldPoint(new Vector3(1f, 0.5f, cam.nearClipPlane + 1f)).x : float.MaxValue;
            for (int i = 0; i < Players; i++)
            {
                var p = m_panels[i];
                if (p == null || !p.hasBounds) continue;
                p.limitRight = edge;
                for (int j = 0; j < Players; j++)
                {
                    if (j == i || found[j] == null) continue;
                    Bounds b;
                    var other = m_panels[j];
                    if (other != null && other.hasBounds) b = other.bounds;
                    else if (!Measure(found[j], null, out b)) continue;
                    if (b.min.x > p.bounds.center.x) p.limitRight = Mathf.Min(p.limitRight, b.min.x);
                }
            }
        }

        Camera Camera()
        {
            foreach (var p in m_panels)
            {
                var sa = p != null && p.gp != null ? p.gp.GetComponent<ScreenAlign>() : null;
                if (sa != null && sa.m_camera != null) return sa.m_camera;
            }
            try { return Singleton<SystemLevel>.HasInstance() ? SystemLevel.GetCameraGUI() : null; } catch { return null; }
        }

        /// <summary>The panel's drawn area in world units (its visible renderers, leaving out our own countdowns).</summary>
        static bool Measure(GUIPlayer gp, GameObject skip, out Bounds bounds)
        {
            bounds = new Bounds();
            bool any = false;
            foreach (var r in gp.GetComponentsInChildren<Renderer>())
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                if (skip != null && r.transform.IsChildOf(skip.transform)) continue;
                var b = r.bounds;
                if (b.size.x <= 0f && b.size.y <= 0f) continue;
                if (!any) { bounds = b; any = true; } else bounds.Encapsulate(b);
            }
            return any;
        }

        // ---- countdowns
        void Draw(int id)
        {
            var p = m_panels[id];
            var entries = HudTimers.Players[id];
            if (p == null) return;
            if (p.gp == null || !p.gp.gameObject.activeInHierarchy || !p.hasBounds || entries.Count == 0)
            {
                foreach (var it in p.items) Show(it, false);
                return;
            }
            if (p.root == null && !Build(p)) return;
            while (p.items.Count < entries.Count) p.items.Add(MakeItem(p));
            for (int k = entries.Count; k < p.items.Count; k++) Show(p.items[k], false);

            // sizes: icon and number side by side, rows as tall as the taller of the two
            float rowH = 0f, maxW = 0f, gap = 0f;
            bool ready = true;
            for (int k = 0; k < entries.Count; k++)
            {
                var it = p.items[k];
                Fill(it, entries[k]);
                if (!it.measured) { ready = false; continue; }
                var tb = it.textR.bounds.size;
                var ib = it.icon.enabled ? it.iconR.bounds.size : Vector3.zero;
                gap = Mathf.Max(gap, tb.y * 0.25f);
                rowH = Mathf.Max(rowH, Mathf.Max(tb.y, ib.y));
                maxW = Mathf.Max(maxW, ib.x + tb.x);
            }
            if (!ready)
            {
                // a new countdown is laid out once its meshes exist (the frame after it is first shown)
                for (int k = 0; k < entries.Count; k++)
                {
                    var it = p.items[k];
                    if (it.measured) continue;
                    it.measured = it.root.activeSelf && it.textR.bounds.size.x > 0f && (!it.icon.enabled || it.iconR.bounds.size.x > 0f || ++it.tries > 10);
                    if (!it.measured) { SetAlpha(it, 0f); Show(it, true); }
                }
                return;
            }
            maxW += gap;
            var b = p.bounds;
            float z = b.center.z - 0.5f;
            bool beside = b.max.x + gap + maxW <= p.limitRight - gap;
            for (int k = 0; k < entries.Count; k++)
            {
                var it = p.items[k];
                float x, y;
                if (beside)
                {
                    // a column to the right of the panel, centred on it, first countdown on top
                    x = b.max.x + gap;
                    y = b.center.y + (entries.Count - 1) * 0.5f * (rowH + gap * 0.5f) - k * (rowH + gap * 0.5f);
                }
                else
                {
                    // a row just above the panel's right end, first countdown on the right
                    float w = ItemWidth(it, gap);
                    float right = b.max.x;
                    for (int j = 0; j < k; j++) right -= ItemWidth(p.items[j], gap) + gap;
                    x = right - w;
                    y = b.max.y + gap + rowH * 0.5f;
                }
                Place(it, x, y, z);
                SetAlpha(it, entries[k].paused ? PausedAlpha : 1f);
                Show(it, true);
            }
        }

        static float ItemWidth(Item it, float gap)
        {
            float iw = it.icon.enabled ? it.iconR.bounds.size.x : 0f;
            return iw + (iw > 0f ? gap * 0.5f : 0f) + it.textR.bounds.size.x;
        }

        static void Place(Item it, float x, float y, float z)
        {
            float iw = it.icon.enabled ? it.iconR.bounds.size.x : 0f;
            if (it.icon.enabled) it.icon.transform.position = new Vector3(x + iw * 0.5f, y, z);
            float tx = x + iw + (iw > 0f ? it.textR.bounds.size.y * 0.15f : 0f);
            it.text.transform.position = new Vector3(tx, y, z);
            float px = it.textR.bounds.size.y / 9f;     // one font pixel (a pixel font line is about 9 px tall)
            it.shadow.transform.position = new Vector3(tx + px, y - px, z + 0.05f);
        }

        void Fill(Item it, HudTimers.Entry e)
        {
            int n = HudTimers.Shown(e.seconds);
            if (n != it.shown)
            {
                it.shown = n;
                string s = n.ToString();
                it.text.text = s;
                it.shadow.text = s;
            }
            if (e.icon != it.sheet)
            {
                it.sheet = e.icon;
                bool has = e.icon != null && e.icon.atlas != null && e.icon.atlas.elements != null && e.icon.atlas.elements.Length > 0;
                it.icon.enabled = has;
                it.iconR.enabled = has;
                it.measured = false;
                it.tries = 0;
                if (has)
                {
                    var idle = e.icon.Anim("Idle");
                    int cell = idle != null && idle.frames != null && idle.frames.Length > 0 ? idle.frames[0] : 0;
                    it.icon.SetSprite(e.icon.atlas, cell);
                    if (e.icon.atlas.material != null) it.iconR.sharedMaterial = e.icon.atlas.material;
                }
            }
        }

        static void SetAlpha(Item it, float a)
        {
            if (Mathf.Abs(a - it.alpha) < 0.004f) return;
            it.alpha = a;
            it.text.color = new Color(1f, 0.96f, 0.86f, a);
            it.shadow.color = new Color(0f, 0f, 0f, a * 0.85f);
            if (it.icon.enabled) it.icon.color = new Color(1f, 1f, 1f, a);
        }

        static void Show(Item it, bool on)
        {
            if (it.root.activeSelf != on) it.root.SetActive(on);
        }

        // ---- objects (made once per panel and reused)
        TextMesh m_nameRef;
        exSprite m_iconRef;

        bool Build(Panel p)
        {
            m_nameRef = R.Get<TextMesh>(p.gp, "m_name");
            var gold = R.Get<GameObject>(p.gp, "m_goldIcon");
            m_iconRef = gold != null ? gold.GetComponentInChildren<exSprite>(true) : null;
            if (m_iconRef == null) m_iconRef = R.Get<exSprite>(p.gp, "m_portrait");
            if (m_nameRef == null || m_nameRef.font == null) return false;
            p.root = new GameObject("CrawlFurther.HudTimers");
            p.root.layer = p.gp.gameObject.layer;
            p.root.transform.SetParent(p.gp.transform, false);
            return true;
        }

        Item MakeItem(Panel p)
        {
            var it = new Item { root = new GameObject("Countdown") };
            it.root.layer = p.root.layer;
            it.root.transform.SetParent(p.root.transform, false);
            var nr = m_nameRef.GetComponent<Renderer>();
            it.shadow = MakeText(it.root.transform, "Shadow", nr, 4, out it.shadowR);
            it.text = MakeText(it.root.transform, "Text", nr, 5, out it.textR);

            var ig = new GameObject("Picture");
            ig.layer = it.root.layer;
            ig.transform.SetParent(it.root.transform, false);
            ig.AddComponent<MeshFilter>();
            it.iconR = ig.AddComponent<MeshRenderer>();
            it.icon = ig.AddComponent<exSprite>();
            it.icon.anchor = exPlane.Anchor.MidCenter;
            if (m_iconRef != null)
            {
                MatchScale(ig.transform, m_iconRef.transform);
                it.icon.scale = m_iconRef.scale;
                it.icon.ppfScale = m_iconRef.ppfScale;
                var cam = m_iconRef.renderCamera;
                if (cam != null) it.icon.renderCamera = cam;
            }
            it.icon.enabled = false;
            it.iconR.enabled = false;
            it.root.SetActive(false);
            return it;
        }

        TextMesh MakeText(Transform parent, string name, Renderer like, int sortAdd, out Renderer rend)
        {
            var go = new GameObject(name);
            go.layer = parent.gameObject.layer;
            go.transform.SetParent(parent, false);
            MatchScale(go.transform, m_nameRef.transform);
            var mr = go.AddComponent<MeshRenderer>();
            var tm = go.AddComponent<TextMesh>();
            tm.font = m_nameRef.font;
            tm.fontSize = m_nameRef.fontSize;
            tm.characterSize = m_nameRef.characterSize;
            tm.anchor = TextAnchor.MiddleLeft;
            tm.alignment = TextAlignment.Left;
            tm.richText = false;
            mr.sharedMaterial = like != null && like.sharedMaterial != null ? like.sharedMaterial : m_nameRef.font.material;
            if (like != null) { mr.sortingLayerID = like.sortingLayerID; mr.sortingOrder = like.sortingOrder + sortAdd; }
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            mr.receiveShadows = false;
            rend = mr;
            return tm;
        }

        /// <summary>Give <paramref name="t"/> the same world scale as <paramref name="like"/>.</summary>
        static void MatchScale(Transform t, Transform like)
        {
            var want = like.lossyScale;
            var parent = t.parent != null ? t.parent.lossyScale : Vector3.one;
            t.localScale = new Vector3(Div(want.x, parent.x), Div(want.y, parent.y), 1f);
        }

        static float Div(float a, float b) { return Mathf.Abs(b) > 0.0001f ? Mathf.Abs(a / b) : 1f; }
    }
}
