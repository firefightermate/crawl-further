using System;
using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>A confirm button: the tier tick and a word; greyed (and refusing) until enabled() holds.</summary>
    public class ButtonRow : EdRow
    {
        public string text;
        public Func<bool> enabled;
        public Action onPress;
        TextMesh m_text;
        exSprite m_tick;

        public override void Build()
        {
            m_text = ui.NewText(root.transform, "Text", new Vector3(3.5f, 0f, 0f), SlotArt.Body);
            m_text.text = text;
            float w = SlotArt.Width(text);
            m_tick = SlotArt.Sprite("Tick", root.transform, new Vector3(3.5f - w / 2f - 6f, 0.5f, -0.2f), SlotArt.Clip("EdCheck", "Off"));
        }

        bool On { get { return enabled == null || enabled(); } }

        public override void Refresh(bool focused)
        {
            bool on = On;
            m_text.color = !on ? new Color(0.45f, 0.4f, 0.35f) : focused ? SlotArt.Tier(ui.Tier) : SlotArt.Body;
            SlotArt.Play(m_tick, SlotArt.Clip("EdCheck", on && focused ? SlotArt.Anim(ui.Tier) : "Off"));
        }

        public override void Press()
        {
            if (!On) { ui.Deny(); return; }
            ui.Sound(true);
            if (onPress != null) onPress();
        }

        public override bool Hover(Vector2 w) { return root != null && Around(root.transform, 44f, 8f).Contains(w); }
    }
}
