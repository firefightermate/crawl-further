using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Heroes
{
    using CrawlFurther.Art;
    using CrawlFurther.Ghosts;
    using CrawlFurther.Gods;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>
    /// The ghost page's second row: which blob the highlighted form spawns with Back. It sits where the god page shows its
    /// starter boxes (hidden on the ghost page) as a row of the same boxes: the regular blob first, then every blob the
    /// form can choose (GhostBlobs). A form with no choice (the Wisp, the Banshee to the Miser) shows no row. An open blob
    /// shows its picture, a locked one only its dark outline. The blob in effect has a dashed frame; while the row has the
    /// focus the box under the cursor has the form's metal frame and runs.
    /// The row only draws and keeps the cursor: the origin picker routes input to it and writes the pick.
    /// </summary>
    public class GhostBlobRow
    {
        const float Scale = 0.8f, Pitch = 9.5f;
        /// <summary>The most art (px) a box shows at full size: what the Spitter and the Gel take up running, the largest of
        /// the small blobs. A bigger blob (the King) is drawn smaller to fit the same room, still and running, and so is its
        /// locked outline.</summary>
        const float FitW = 16f, FitH = 14f;

        readonly MenuDeitySelectPlayer m_panel;
        readonly int m_pid;
        GameObject m_root;
        readonly List<BoxView> m_boxes = new List<BoxView>();
        readonly List<Vector2> m_baseScale = new List<Vector2>();   // each box picture's own scale
        readonly List<GhostBlobDef> m_entries = new List<GhostBlobDef>();   // [0] = the regular blob
        readonly List<GameObject> m_hidden = new List<GameObject>();
        GhostFormDef m_form;
        Vector3 m_centre;
        float m_shake;
        AudioCue m_sndMove, m_sndAction;
        static readonly Dictionary<string, exSpriteAnimClip> s_dark = new Dictionary<string, exSpriteAnimClip>();

        /// <summary>The box under the cursor (0 = the regular blob).</summary>
        public int Cursor { get; private set; }
        /// <summary>The row has the focus (the cursor is shown and the text panel describes it).</summary>
        public bool Focused { get; private set; }
        /// <summary>The form has a choice: the row shows and can take the focus.</summary>
        public bool Shown { get { return m_entries.Count > 1; } }

        public GhostBlobRow(MenuDeitySelectPlayer panel, int playerId)
        {
            m_panel = panel;
            m_pid = playerId;
            var item = R.Get<MenuItemImage>(panel, "m_prefabMenuItem");
            if (item != null) { m_sndMove = R.Get<AudioCue>(item, "m_soundOnSelect"); m_sndAction = R.Get<AudioCue>(item, "m_soundOnAction"); }
        }

        /// <summary>The blob under the cursor.</summary>
        public GhostBlobDef AtCursor { get { return Cursor >= 0 && Cursor < m_entries.Count ? m_entries[Cursor] : null; } }

        /// <summary>The blob under the cursor can be picked.</summary>
        public bool CursorOpen { get { return GhostBlobs.IsOpen(AtCursor); } }

        /// <summary>The form the row shows.</summary>
        public GhostFormDef Form { get { return m_form; } }

        PlayerData Player { get { try { return SystemPlayers.GetPlayer(m_pid); } catch { return null; } } }

        /// <summary>Show the row for <paramref name="form"/> (rebuilt when the form changes) in place of the starter boxes;
        /// a form with no choice shows nothing there.</summary>
        public void Show(GhostFormDef form)
        {
            if (m_root == null && !Build()) return;
            HidePlates();
            if (form != m_form)
            {
                m_form = form;
                m_entries.Clear();
                m_entries.AddRange(GhostBlobs.ChoicesFor(form));
                if (!Shown) Focused = false;
                Layout();
                CursorToPick();
            }
            m_root.SetActive(Shown);
            Refresh();
        }

        /// <summary>Hide the row and put the starter boxes back as they were.</summary>
        public void Hide()
        {
            Focused = false;
            if (m_root != null) m_root.SetActive(false);
            foreach (var g in m_hidden) if (g != null) g.SetActive(true);
            m_hidden.Clear();
        }

        public void Destroy()
        {
            Hide();
            foreach (var b in m_boxes) b.Destroy();
            m_boxes.Clear();
            if (m_root != null) Object.Destroy(m_root);
            m_root = null;
            m_form = null;
        }

        /// <summary>Give the row the focus (the cursor starts on the pick) or take it away.</summary>
        public void SetFocus(bool on)
        {
            if (Focused == on) return;
            Focused = on;
            if (!on) CursorToPick();
            Sound(false);
            Refresh();
        }

        /// <summary>Move the cursor; returns true if it moved.</summary>
        public bool Step(int dir)
        {
            int to = Mathf.Clamp(Cursor + dir, 0, m_entries.Count - 1);
            if (to == Cursor) return false;
            Cursor = to;
            Sound(false);
            Refresh();
            return true;
        }

        /// <summary>Put the cursor on box <paramref name="i"/> (pointer hover).</summary>
        public void Point(int i)
        {
            if (i < 0 || i >= m_entries.Count || i == Cursor) return;
            Cursor = i;
            Sound(false);
            Refresh();
        }

        /// <summary>The cursor goes back to the blob in effect for this form.</summary>
        public void CursorToPick() { Cursor = Mathf.Max(0, PickIndex()); }

        /// <summary>The box index at a world point, or -1.</summary>
        public int HitTest(Vector2 world)
        {
            if (m_root == null || !m_root.activeInHierarchy || !Shown) return -1;
            for (int i = 0; i < m_boxes.Count && i < m_entries.Count; i++)
                if (m_boxes[i].root != null && m_boxes[i].root.activeSelf && m_boxes[i].WorldRect().Contains(world)) return i;
            return -1;
        }

        /// <summary>A locked box was confirmed: the row shakes.</summary>
        public void Deny() { m_shake = 0.24f; }

        public void Sound(bool action)
        {
            try { var s = action ? m_sndAction : m_sndMove; if (s != null) s.Play(); } catch { }
        }

        /// <summary>Called every frame by the picker while the row shows.</summary>
        public void Tick()
        {
            if (m_root == null || m_shake <= 0f) return;
            m_shake -= Time.unscaledDeltaTime;
            float k = m_shake > 0f ? Mathf.Sign(Mathf.Sin(m_shake * 90f)) : 0f;
            m_root.transform.localPosition = m_centre + new Vector3(k, 0f, 0f);
        }

        // ------------------------------------------------------------------ the text panel
        /// <summary>The name line for the cursor's box.</summary>
        public string Name()
        {
            var d = AtCursor;
            return d != null ? d.name.ToUpperInvariant() : "";
        }

        /// <summary>The text line for the cursor's box: what it does, or how to earn it.</summary>
        public string Text()
        {
            var d = AtCursor;
            if (d == null) return "";
            if (!GhostBlobs.IsOpen(d))
            {
                var c = Unlocks.Find(d.unlock);
                return c == null ? "Locked" : c.text + "  " + Unlocks.ProgressShort(c.id);
            }
            return GhostControls.Personalise(d.summary, GhostControls.Name(m_pid));
        }

        // ------------------------------------------------------------------ drawing
        bool Build()
        {
            var mons = R.Get<exSprite[]>(m_panel, "m_monsters");
            if (mons == null || mons.Length == 0 || mons[0] == null) return false;
            var sum = Vector3.zero; int n = 0;
            foreach (var s in mons) if (s != null) { sum += s.transform.parent.position; n++; }
            m_centre = m_panel.transform.InverseTransformPoint(sum / n);
            m_centre.z = m_panel.transform.InverseTransformPoint(mons[0].transform.parent.position).z;
            m_root = new GameObject("ModGhostBlobRow");
            m_root.layer = m_panel.gameObject.layer;
            m_root.transform.SetParent(m_panel.transform, false);
            m_root.transform.localPosition = m_centre;
            return true;
        }

        /// <summary>The starter boxes (and a gold idol's fourth) go while the row is up.</summary>
        void HidePlates()
        {
            var mons = R.Get<exSprite[]>(m_panel, "m_monsters");
            if (mons != null)
                foreach (var s in mons) if (s != null) Hide(s.transform.parent.gameObject);
            var plates = mons != null && mons.Length > 0 && mons[0] != null ? mons[0].transform.parent.parent : null;
            var four = plates != null ? plates.Find("ModMonster4") : null;   // the gold idol's fourth box (GodSlots)
            if (four != null) Hide(four.gameObject);
        }

        void Hide(GameObject g)
        {
            if (g == null || !g.activeSelf) return;
            g.SetActive(false);
            m_hidden.Add(g);
        }

        void Layout()
        {
            var mons = R.Get<exSprite[]>(m_panel, "m_monsters");
            var template = mons[0].transform.parent.gameObject;
            while (m_boxes.Count < m_entries.Count)
            {
                var b = BoxView.Create(template, m_root.transform, "Blob" + m_boxes.Count, Vector3.zero, Scale);
                m_boxes.Add(b);
                m_baseScale.Add(b.img != null ? b.img.scale : Vector2.one);
            }
            for (int i = 0; i < m_boxes.Count; i++)
            {
                bool on = i < m_entries.Count;
                m_boxes[i].root.SetActive(on);
                if (on) m_boxes[i].root.transform.localPosition = new Vector3((i - (m_entries.Count - 1) * 0.5f) * Pitch, 0f, 0f);
            }
        }

        /// <summary>Redraw every box: pictures, outlines, frames.</summary>
        public void Refresh()
        {
            if (m_root == null) return;
            var pd = Player;
            int pick = PickIndex();
            for (int i = 0; i < m_entries.Count && i < m_boxes.Count; i++)
            {
                var b = m_boxes[i];
                var d = m_entries[i];
                bool cur = Focused && i == Cursor;
                if (!GhostBlobs.IsOpen(d))
                {
                    var c = Dark(d);
                    FitTo(i, Fit(c));
                    b.SetClip(c);
                }
                else
                {
                    var prefab = GhostBlobs.Prefab(d, pd);
                    var p = prefab != null ? prefab.GetComponent<Player>() : null;
                    // one size for the still picture and the run, so the hovered box does not jump
                    if (FitTo(i, p != null ? Fit(R.Get<exSpriteAnimClip>(p, "m_portraitAnim") ?? p.GetIdleAnim(), p.GetRunAnim()) : 1f))
                        b.SetMonster(null, false);   // set the picture up again at its new size
                    b.SetMonster(p, cur);
                }
                var metal = m_form != null && m_form.tier == SlotTier.Gold ? "Gold" : "Silver";
                b.SetFrame(cur ? SlotArt.Clip("EdCell", metal) : i == pick ? SlotArt.Clip("EdCell", "Slot") : null);
            }
        }

        /// <summary>Scale box <paramref name="i"/>'s picture to <paramref name="k"/> of its own size (keeping its flip).
        /// True if it changed.</summary>
        bool FitTo(int i, float k)
        {
            var img = m_boxes[i].img;
            if (img == null) return false;
            var cur = img.scale;
            var want = new Vector2(Mathf.Sign(cur.x) * Mathf.Abs(m_baseScale[i].x) * k, Mathf.Sign(cur.y) * Mathf.Abs(m_baseScale[i].y) * k);
            if ((want - cur).sqrMagnitude < 1e-6f) return false;
            img.scale = want;
            return true;
        }

        /// <summary>How much the clips' largest frame (its drawn pixels) must shrink to fit FitW x FitH (1 when it fits).</summary>
        static float Fit(params exSpriteAnimClip[] clips)
        {
            float w = 0f, h = 0f;
            foreach (var c in clips)
            {
                if (c == null || c.frameInfos == null) continue;
                foreach (var f in c.frameInfos)
                {
                    var r = ArtSize(f.atlas, f.index);
                    w = Mathf.Max(w, r.x); h = Mathf.Max(h, r.y);
                }
            }
            if (w <= 0f || h <= 0f) return 1f;
            return Mathf.Min(1f, FitW / w, FitH / h);
        }

        static readonly Dictionary<exAtlas, Vector2[]> s_artSize = new Dictionary<exAtlas, Vector2[]>();

        /// <summary>
        /// The drawn size (px) of one atlas element. Mod sheets keep whole cells as their elements, so their opaque
        /// pixels are measured (once per element); a vanilla atlas is already trimmed to them.
        /// </summary>
        static Vector2 ArtSize(exAtlas atlas, int index)
        {
            if (atlas == null || atlas.elements == null || index < 0 || index >= atlas.elements.Length) return Vector2.zero;
            var e = atlas.elements[index];
            Vector2[] sizes;
            if (!s_artSize.TryGetValue(atlas, out sizes)) s_artSize[atlas] = sizes = new Vector2[atlas.elements.Length];
            if (sizes[index] != Vector2.zero) return sizes[index];
            var size = new Vector2(e.trimRect.width, e.trimRect.height);
            var tex = atlas.texture as Texture2D;
            bool whole = Mathf.Approximately(e.trimRect.width, e.originalWidth) && Mathf.Approximately(e.trimRect.height, e.originalHeight);
            if (whole && tex != null && !e.rotated)
            {
                try
                {
                    int x0 = Mathf.RoundToInt(e.coords.x * tex.width), y0 = Mathf.RoundToInt(e.coords.y * tex.height);
                    int w = Mathf.RoundToInt(e.coords.width * tex.width), h = Mathf.RoundToInt(e.coords.height * tex.height);
                    var px = tex.GetPixels(x0, y0, w, h);
                    int minX = w, minY = h, maxX = -1, maxY = -1;
                    for (int y = 0; y < h; y++)
                        for (int x = 0; x < w; x++)
                            if (px[y * w + x].a > 0) { minX = Mathf.Min(minX, x); maxX = Mathf.Max(maxX, x); minY = Mathf.Min(minY, y); maxY = Mathf.Max(maxY, y); }
                    if (maxX >= 0) size = new Vector2(maxX - minX + 1, maxY - minY + 1);
                }
                catch { }   // an unreadable texture: keep the element's own size
            }
            sizes[index] = size;
            return size;
        }

        /// <summary>The box of the blob in effect for this form (the pick, else the form's default).</summary>
        int PickIndex()
        {
            var d = GhostBlobs.ChoiceFor(Player, m_form);
            int i = m_entries.IndexOf(d);
            return i >= 0 ? i : 0;
        }

        /// <summary>A locked blob: its Portrait frame as a dark outline (counted as mod art, so it keeps its one gem).</summary>
        static exSpriteAnimClip Dark(GhostBlobDef d)
        {
            exSpriteAnimClip c;
            if (d.art != null && s_dark.TryGetValue(d.art, out c) && SlotArt.Alive(c)) return c;
            var sh = d.art != null ? SpriteSheets.Get(d.art) : null;
            if (sh == null) return null;
            var anim = sh.Has("Portrait") ? "Portrait" : "Idle";
            c = Silhouette.Clip(sh, sh.Anim(anim).frames[0], "ModBlobLocked_" + d.art);
            if (c != null) { ModMark.MarkArt(c.frameInfos[0].atlas); s_dark[d.art] = c; }
            return c;
        }
    }
}
