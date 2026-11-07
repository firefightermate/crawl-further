using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>A row of N small boxes showing the current picks; left / right picks which one is being edited.</summary>
    public class StripRow : EdRow
    {
        public string label;
        public int slots;
        public Func<int, Player> at;
        public Func<int> current;
        public Action<int> select;
        public Action onPress;
        public float scale = 0.7f, pitch = 9f;
        readonly List<BoxView> m_boxes = new List<BoxView>();
        TextMesh m_label;

        public override void Build()
        {
            if (!string.IsNullOrEmpty(label))
            {
                m_label = ui.NewText(root.transform, "Label", new Vector3(0f, 7.6f, 0f), SlotArt.Dim);
                m_label.text = label;
            }
            for (int i = 0; i < slots; i++)
            {
                float x = (i - (slots - 1) * 0.5f) * pitch;
                var b = ui.NewBox("Slot" + i, root.transform, new Vector3(x, 0f, 0f), scale);
                if (b != null) m_boxes.Add(b);
            }
        }

        public override void Refresh(bool focused)
        {
            int cur = current();
            for (int i = 0; i < m_boxes.Count; i++)
            {
                m_boxes[i].SetMonster(at(i), false);
                if (i == cur) m_boxes[i].SetFrame(SlotArt.Clip("EdCell", focused ? SlotArt.Anim(ui.Tier) : "Slot"));
                else m_boxes[i].SetFrame(null);
            }
            if (m_label != null) m_label.color = focused ? SlotArt.Tier(ui.Tier) : SlotArt.Dim;
        }

        public override void Step(int dir)
        {
            int n = m_boxes.Count;
            if (n == 0) return;
            select(Mathf.Clamp(current() + dir, 0, n - 1));
            ui.Sound(false);
            ui.RefreshAll();
        }

        public override void Press() { ui.Sound(true); if (onPress != null) onPress(); }

        public override bool Hover(Vector2 w)
        {
            foreach (var b in m_boxes) if (b.WorldRect().Contains(w)) return true;
            return false;
        }

        public override void Click(Vector2 w)
        {
            for (int i = 0; i < m_boxes.Count; i++)
                if (m_boxes[i].WorldRect().Contains(w)) { select(i); ui.RefreshAll(); Press(); return; }
        }

        public override void Wheel(int dir) { Step(dir); }
        public override void Destroy() { foreach (var b in m_boxes) b.Destroy(); m_boxes.Clear(); base.Destroy(); }
    }
}
