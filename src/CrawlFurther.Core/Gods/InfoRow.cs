using System;
using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>One or two lines of text that describe the focused thing (not focusable).</summary>
    public class InfoRow : EdRow
    {
        public Func<string> line1, line2;
        public bool paragraph;            // line1 as a wrapping paragraph (up to four lines below y)
        public float wrap = 44f;
        TextMesh m_a, m_b;
        GUIText m_p;
        public override bool Focusable { get { return false; } }

        public override void Build()
        {
            if (paragraph) m_p = ui.NewParagraph(root.transform, "Para", Vector3.zero, wrap, SlotArt.Body);
            else
            {
                m_a = ui.NewText(root.transform, "A", Vector3.zero, SlotArt.Body);
                m_b = ui.NewText(root.transform, "B", new Vector3(0f, -5.1f, 0f), SlotArt.Dim);
            }
        }

        public override void Refresh(bool focused)
        {
            if (m_p != null) { m_p.SetText(line1 != null ? line1() : ""); return; }
            Fit(m_a, line1 != null ? line1() : "");
            Fit(m_b, line2 != null ? line2() : "");
        }

        float m_size = -1f;
        void Fit(TextMesh tm, string s)
        {
            if (tm == null) return;
            if (m_size < 0f) m_size = tm.characterSize;
            tm.text = s;
            float w = SlotArt.Width(s);
            tm.characterSize = w > 46f ? m_size * 46f / w : m_size;
        }
    }
}
