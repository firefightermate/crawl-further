using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>
    /// An icon grid of boxes (cols x visibleRows, scrolling by rows). Each cell shows monsterAt(i) (still; the focused
    /// one runs) or clipAt(i). taken(i) marks a cell that can't be picked (a cross). onFocus(i) fires when the focused
    /// cell changes (preview / info), onPick(i) on press or click.
    /// </summary>
    public class GridRow : EdRow
    {
        public int cols = 4, visibleRows = 2;
        public float scale = 0.8f, pitchX = 10f, pitchY = 11.6f;
        public Func<int> count;
        public Func<int, Player> monsterAt;
        public Func<int, exSpriteAnimClip> clipAt;
        public Func<int, bool> taken;
        /// <summary>A cell that is a find (a secret entry): a quiet gold glint on its frame.</summary>
        public Func<int, bool> special;
        public Action<int> onFocus, onPick;
        public int cursor;
        int m_scroll;
        readonly List<BoxView> m_cells = new List<BoxView>();
        exSprite m_up, m_down;
        bool m_focused;

        public override void Build()
        {
            for (int r = 0; r < visibleRows; r++)
                for (int c = 0; c < cols; c++)
                {
                    float x = (c - (cols - 1) * 0.5f) * pitchX;
                    var b = ui.NewBox("Cell", root.transform, new Vector3(x, -r * pitchY, 0f), scale);
                    if (b != null) m_cells.Add(b);
                }
            float right = (cols - 1) * 0.5f * pitchX + pitchX * 0.5f + 2.5f;
            m_up = SlotArt.Sprite("More", root.transform, new Vector3(right, 2f, -0.2f), SlotArt.Clip("EdArrow", "Off"));
            m_up.transform.localRotation = Quaternion.Euler(0f, 0f, 90f);
            m_down = SlotArt.Sprite("More", root.transform, new Vector3(right, -(visibleRows - 1) * pitchY - 2f, -0.2f), SlotArt.Clip("EdArrow", "Off"));
            m_down.transform.localRotation = Quaternion.Euler(0f, 0f, -90f);
            cursor = Mathf.Clamp(cursor, 0, Mathf.Max(0, count() - 1));
            ScrollTo();
        }

        int Rows { get { return (count() + cols - 1) / cols; } }

        /// <summary>Put the cursor on i (clamped to the list, which may have changed) and scroll to it.</summary>
        public void SetCursor(int i)
        {
            cursor = Mathf.Clamp(i, 0, Mathf.Max(0, count() - 1));
            ScrollTo();
        }

        void ScrollTo()
        {
            int row = cursor / cols;
            if (row < m_scroll) m_scroll = row;
            if (row >= m_scroll + visibleRows) m_scroll = row - visibleRows + 1;
            m_scroll = Mathf.Clamp(m_scroll, 0, Mathf.Max(0, Rows - visibleRows));
        }

        public override void Refresh(bool focused)
        {
            m_focused = focused;
            int n = count();
            for (int k = 0; k < m_cells.Count; k++)
            {
                int i = m_scroll * cols + k;
                var b = m_cells[k];
                bool on = i < n;
                b.root.SetActive(on);
                if (!on) continue;
                bool cur = i == cursor;
                if (monsterAt != null) b.SetMonster(monsterAt(i), cur && focused);
                else if (clipAt != null) b.SetClip(clipAt(i));
                b.SetFrame(cur ? SlotArt.Clip("EdCell", focused ? SlotArt.Anim(ui.Tier) : "Slot") : null);
                b.SetMark(taken != null && taken(i) ? SlotArt.Clip("EdCell", "Taken")
                          : special != null && special(i) ? SlotArt.Clip("EdCell", "Find") : null);
            }
            var a = SlotArt.Clip("EdArrow", focused ? SlotArt.Anim(ui.Tier) : "Off");
            SlotArt.Play(m_up, a); SlotArt.Play(m_down, a);
            m_up.gameObject.SetActive(m_scroll > 0);
            m_down.gameObject.SetActive(m_scroll + visibleRows < Rows);
        }

        void Move(int to)
        {
            int n = count();
            if (n == 0) return;
            to = Mathf.Clamp(to, 0, n - 1);
            if (to == cursor) return;
            cursor = to;
            ScrollTo();
            ui.Sound(false);
            if (onFocus != null) onFocus(cursor);
            ui.RefreshAll();
        }

        public override void Enter(int fromDir) { if (onFocus != null) onFocus(cursor); ui.RefreshAll(); }

        public override void Step(int dir)
        {
            int c = cursor % cols;
            if (dir < 0 && c > 0) Move(cursor - 1);
            else if (dir > 0 && c < cols - 1 && cursor + 1 < count()) Move(cursor + 1);
        }

        public override bool Up()
        {
            if (cursor - cols < 0) return false;
            Move(cursor - cols);
            return true;
        }

        public override bool Down()
        {
            if (cursor / cols >= Rows - 1) return false;
            Move(Mathf.Min(cursor + cols, count() - 1));
            return true;
        }

        public override void Press()
        {
            if (taken != null && taken(cursor)) { ui.Deny(); return; }
            ui.Sound(true);
            if (onPick != null) onPick(cursor);
            ui.RefreshAll();
        }

        int CellAt(Vector2 w)
        {
            for (int k = 0; k < m_cells.Count; k++)
                if (m_cells[k].root.activeSelf && m_cells[k].WorldRect().Contains(w)) return m_scroll * cols + k;
            return -1;
        }

        public override bool Hover(Vector2 w)
        {
            int i = CellAt(w);
            if (i >= 0 && i != cursor) { cursor = i; if (onFocus != null) onFocus(i); ui.RefreshAll(); }
            if (i >= 0) return true;
            var p = root.transform.position;
            return new Rect(p.x - 25f, p.y - (visibleRows - 0.5f) * pitchY, 50f, visibleRows * pitchY).Contains(w);
        }

        public override void Click(Vector2 w)
        {
            int i = CellAt(w);
            if (i >= 0) { cursor = i; Press(); }
        }

        public override void Wheel(int dir)
        {
            int before = m_scroll;
            m_scroll = Mathf.Clamp(m_scroll + dir, 0, Mathf.Max(0, Rows - visibleRows));
            if (m_scroll != before) { ui.Sound(false); ui.RefreshAll(); }
        }

        public override void Destroy() { foreach (var b in m_cells) b.Destroy(); m_cells.Clear(); base.Destroy(); }
    }
}
