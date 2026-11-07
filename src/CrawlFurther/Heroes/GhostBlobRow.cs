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
    /// starter boxes (hidden while it is up) as a row of the same boxes: the form's own blob first, then every blob the
    /// form can pick (GhostBlobs). An open blob shows its picture, a locked one only its dark outline. The picked box has a
    /// dashed frame; while the row has the focus the box under the cursor has the form's metal frame and runs.
    /// The row only draws and keeps the cursor: the origin picker routes input to it and writes the pick.
    /// </summary>
    public class GhostBlobRow
    {
        const float Scale = 0.8f, Pitch = 9.5f;

        readonly MenuDeitySelectPlayer m_panel;
        readonly int m_pid;
        GameObject m_root;
        readonly List<BoxView> m_boxes = new List<BoxView>();
        readonly List<GhostBlobDef> m_entries = new List<GhostBlobDef>();   // [0] = null: the form's own
        readonly List<GameObject> m_hidden = new List<GameObject>();
        GhostFormDef m_form;
        Vector3 m_centre;
        float m_shake;
        AudioCue m_sndMove, m_sndAction;
        static readonly Dictionary<string, exSpriteAnimClip> s_dark = new Dictionary<string, exSpriteAnimClip>();

        /// <summary>The box under the cursor (0 = the form's own).</summary>
        public int Cursor { get; private set; }
        /// <summary>The row has the focus (the cursor is shown and the text panel describes it).</summary>
        public bool Focused { get; private set; }
        public int Count { get { return m_entries.Count; } }

        public GhostBlobRow(MenuDeitySelectPlayer panel, int playerId)
        {
            m_panel = panel;
            m_pid = playerId;
            var item = R.Get<MenuItemImage>(panel, "m_prefabMenuItem");
            if (item != null) { m_sndMove = R.Get<AudioCue>(item, "m_soundOnSelect"); m_sndAction = R.Get<AudioCue>(item, "m_soundOnAction"); }
        }

        /// <summary>The entry under the cursor: null for the form's own.</summary>
        public GhostBlobDef AtCursor { get { return Cursor >= 0 && Cursor < m_entries.Count ? m_entries[Cursor] : null; } }

        /// <summary>The entry under the cursor can be picked.</summary>
        public bool CursorOpen { get { var d = AtCursor; return d == null || GhostBlobs.IsOpen(d); } }

        PlayerData Player { get { try { return SystemPlayers.GetPlayer(m_pid); } catch { return null; } } }

        /// <summary>Show the row for <paramref name="form"/> (rebuilt when the form changes), in place of the starter boxes.</summary>
        public void Show(GhostFormDef form)
        {
            if (m_root == null && !Build()) return;
            HidePlates();
            m_root.SetActive(true);
            if (form != m_form)
            {
                m_form = form;
                m_entries.Clear();
                m_entries.Add(null);
                m_entries.AddRange(GhostBlobs.ChoicesFor(form, Player));
                Layout();
                CursorToPick();
            }
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

        /// <summary>The cursor goes back to the player's pick (or the form's own when the pick does not fit this form).</summary>
        public void CursorToPick()
        {
            string id;
            GhostBlobs.Chosen.TryGetValue(m_pid, out id);
            Cursor = 0;
            for (int i = 1; i < m_entries.Count; i++)
                if (m_entries[i].id == id && GhostBlobs.IsOpen(m_entries[i])) Cursor = i;
        }

        /// <summary>The box index at a world point, or -1.</summary>
        public int HitTest(Vector2 world)
        {
            if (m_root == null || !m_root.activeInHierarchy) return -1;
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
            if (d != null) return d.name.ToUpperInvariant();
            var own = GhostBlobs.Own(m_form, Player);
            foreach (var b in GhostBlobs.All) if (GhostBlobs.Prefab(b, Player) == own && own != null) return b.name.ToUpperInvariant();
            return SlotArt.MonsterName(own);
        }

        /// <summary>The text line for the cursor's box: what it does, or how to open it.</summary>
        public string Text()
        {
            var d = AtCursor;
            if (d == null) return "Its own blob, as it always was";
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
                m_boxes.Add(BoxView.Create(template, m_root.transform, "Blob" + m_boxes.Count, Vector3.zero, Scale));
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
                if (d != null && !GhostBlobs.IsOpen(d)) { b.SetClip(Dark(d)); }
                else
                {
                    var prefab = d == null ? GhostBlobs.Own(m_form, pd) : GhostBlobs.Prefab(d, pd);
                    var p = prefab != null ? prefab.GetComponent<Player>() : null;
                    b.SetMonster(p, cur);
                }
                var metal = m_form != null && m_form.tier == SlotTier.Gold ? "Gold" : "Silver";
                b.SetFrame(cur ? SlotArt.Clip("EdCell", metal) : i == pick ? SlotArt.Clip("EdCell", "Slot") : null);
            }
        }

        /// <summary>The box of the pick that counts for this form.</summary>
        int PickIndex()
        {
            string id;
            if (!GhostBlobs.Chosen.TryGetValue(m_pid, out id)) return 0;
            for (int i = 1; i < m_entries.Count; i++) if (m_entries[i].id == id && GhostBlobs.IsOpen(m_entries[i])) return i;
            return 0;
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
