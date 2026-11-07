using System;
using System.Collections.Generic;
using System.Text;
using UnityEngine;

namespace CrawlFurther.UI
{
    /// <summary>
    /// Lays a GUIText's text out inside a box, measured with the font's real advances. GUIText wraps by summing each
    /// character's drawn width in world units, which leaves out the gap after every glyph and counts the parent's scale,
    /// so its lines come out far wider than its wrap width (in the vault, wide enough to run under the BACK button).
    /// Here lines are broken at word boundaries to fit, the text is anchored at its top left, and anything that would
    /// still not fit is cut with "...". Units are the TextMesh's local units (one font pixel each at the vault's sizes).
    /// </summary>
    internal static class TextFit
    {
        /// <summary>The width a line may use: by line index (0 = first line).</summary>
        public delegate float LineWidth(int line);

        /// <summary>Set <paramref name="text"/> on <paramref name="g"/>, top-left at <paramref name="topLeft"/> (local),
        /// broken to <paramref name="width"/> and cut after <paramref name="maxLines"/> lines.</summary>
        public static void Set(GUIText g, string text, Vector2 topLeft, LineWidth width, int maxLines)
        {
            if (g == null) return;
            var tm = g.GetComponent<TextMesh>();
            if (tm == null) { g.SetText(text); return; }
            var p = g.transform.localPosition;
            g.transform.localPosition = new Vector3(topLeft.x, topLeft.y, p.z);
            tm.anchor = TextAnchor.UpperLeft;
            tm.alignment = TextAlignment.Left;
            g.SetWrapWidth(0f);
            g.SetText(string.Join("\n", Lines(tm, text ?? string.Empty, width, maxLines).ToArray()));
        }

        /// <summary>One line's height in the TextMesh's local units.</summary>
        public static float LineHeight(TextMesh tm)
        {
            if (tm == null || tm.font == null) return 7f;
            return tm.font.lineHeight * tm.lineSpacing * Scale(tm);
        }

        /// <summary>Local units per font pixel of this TextMesh (TextMesh draws fontSize-pixel glyphs at 0.1 x characterSize).</summary>
        static float Scale(TextMesh tm)
        {
            int size = tm.fontSize > 0 ? tm.fontSize : tm.font.fontSize;
            float native = tm.font.fontSize > 0 ? tm.font.fontSize : size;
            return tm.characterSize * 0.1f * size / native;
        }

        public static List<string> Lines(TextMesh tm, string text, LineWidth width, int maxLines)
        {
            var lines = new List<string>();
            text = text.Replace("\r", string.Empty);
            if (tm.font != null) tm.font.RequestCharactersInTexture(text + ".", FontSize(tm), tm.fontStyle);
            float space = Advance(tm, ' ');
            foreach (var para in text.Split('\n'))
            {
                var cur = new StringBuilder();
                float w = 0f;
                foreach (var word in para.Split(' '))
                {
                    float ww = Width(tm, word);
                    float max = width(lines.Count);
                    if (cur.Length > 0 && w + space + ww > max)
                    {
                        lines.Add(cur.ToString());
                        cur.Length = 0;
                        w = 0f;
                    }
                    if (cur.Length > 0) { cur.Append(' '); w += space; }
                    cur.Append(word);
                    w += ww;
                }
                lines.Add(cur.ToString());
            }
            while (lines.Count > 0 && lines[lines.Count - 1].Length == 0) lines.RemoveAt(lines.Count - 1);
            if (maxLines > 0 && lines.Count > maxLines)
            {
                lines.RemoveRange(maxLines, lines.Count - maxLines);
                int last = maxLines - 1;
                string l = lines[last];
                float max = width(last), dots = Width(tm, "...");
                while (l.Length > 0 && Width(tm, l) + dots > max) l = l.Substring(0, l.Length - 1);
                lines[last] = l.TrimEnd() + "...";
            }
            return lines;
        }

        static int FontSize(TextMesh tm) { return tm.fontSize > 0 ? tm.fontSize : (tm.font != null ? tm.font.fontSize : 0); }

        static float Advance(TextMesh tm, char c)
        {
            CharacterInfo ci;
            if (tm.font != null && tm.font.GetCharacterInfo(c, out ci, FontSize(tm), tm.fontStyle))
                return ci.advance * tm.characterSize * 0.1f;
            return 4f;   // a typical glyph of the vault's body font
        }

        /// <summary>A run of text's width in local units; rich-text tags take none.</summary>
        public static float Width(TextMesh tm, string s)
        {
            float w = 0f;
            bool tag = false;
            foreach (char c in s)
            {
                if (c == '<') { tag = true; continue; }
                if (tag) { if (c == '>') tag = false; continue; }
                w += Advance(tm, c);
            }
            return w;
        }
    }
}
