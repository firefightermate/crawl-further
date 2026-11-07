using System;
using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>"LABEL" (dim) over "&lt; value &gt;": left / right cycle through count() values.</summary>
    public class CycleRow : EdRow
    {
        public string label;
        public Func<int> count, get;
        public Action<int> set;
        public Func<int, string> name;
        public Func<int, bool> locked;       // optional: a value that exists but can't be taken (shown dim)
        TextMesh m_label, m_value;
        exSprite m_left, m_right;
        bool m_focused;
        float m_baseSize = 0.8f;
        const float ArrowX = 21f;
        /// <summary>Label line above the value line, 6 apart; rows go Pitch (13) apart, so a value line and the next
        /// row's label never touch (the thin font's glyphs are 5.6 tall). Three rows fit under the portrait.</summary>
        public const float LabelY = 4.4f, ValueY = -1.6f, Pitch = 13f, FirstY = -64f;

        public override void Build()
        {
            m_label = ui.NewText(root.transform, "Label", new Vector3(0f, LabelY, 0f), SlotArt.Dim);
            m_label.text = label ?? "";
            m_value = ui.NewText(root.transform, "Value", new Vector3(0f, ValueY, 0f), SlotArt.Body);
            m_baseSize = m_value.characterSize;
            m_left = SlotArt.Sprite("ArrowL", root.transform, new Vector3(-ArrowX, ValueY, -0.2f), SlotArt.Clip("EdArrow", "Off"));
            m_left.scale = new Vector2(-1f, 1f);
            m_right = SlotArt.Sprite("ArrowR", root.transform, new Vector3(ArrowX, ValueY, -0.2f), SlotArt.Clip("EdArrow", "Off"));
        }

        public override void Refresh(bool focused)
        {
            m_focused = focused;
            int i = get(), n = count();
            string v = n > 0 && i >= 0 ? name(i) : "";
            m_value.text = v;
            // long names ("THIEVING KNIFE") shrink to fit between the arrows rather than run under them
            float w = SlotArt.Width(v), room = 2f * (ArrowX - 3.5f);
            m_value.characterSize = m_baseSize * (w > room ? room / w : 1f);
            bool lk = locked != null && i >= 0 && locked(i);
            m_value.color = lk ? SlotArt.Dim : focused ? SlotArt.Tier(ui.Tier) : SlotArt.Body;
            var a = SlotArt.Clip("EdArrow", focused ? SlotArt.Anim(ui.Tier) : "Off");
            SlotArt.Play(m_left, a); SlotArt.Play(m_right, a);
            m_left.gameObject.SetActive(n > 1); m_right.gameObject.SetActive(n > 1);
        }

        public override void Step(int dir)
        {
            int n = count();
            if (n <= 1) return;
            set(((get() + dir) % n + n) % n);
            ui.Sound(false);
            ui.RefreshAll();
            var arrow = dir < 0 ? m_left : m_right;
            SlotArt.Play(arrow, SlotArt.Clip("EdArrow", "Lit"));
            m_flash = 0.12f; m_flashed = arrow;
        }

        float m_flash; exSprite m_flashed;
        public void Tick()
        {
            if (m_flash <= 0f) return;
            m_flash -= Time.unscaledDeltaTime;
            if (m_flash <= 0f && m_flashed != null) SlotArt.Play(m_flashed, SlotArt.Clip("EdArrow", m_focused ? SlotArt.Anim(ui.Tier) : "Off"));
        }

        public override void Press() { ui.Sound(true); ui.Next(); }

        public override bool Hover(Vector2 w) { return root != null && Around(root.transform, 50f, 13f).Contains(w); }

        public override void Click(Vector2 w)
        {
            float x = w.x - root.transform.position.x;
            if (x < -ArrowX + 5f) Step(-1);
            else if (x > ArrowX - 5f) Step(1);
            else Step(1);
        }
    }
}
