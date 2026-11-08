using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Util;

    /// <summary>
    /// Keeps a wrapping paragraph of the god-select panel (the perk text, the flavour, an editor's paragraph rows) within
    /// <see cref="MaxLines"/> lines, the most the game's own texts take there. A text that wraps to more lines (a long
    /// ghost-button name, a translation's wider glyphs) is drawn a little smaller until it fits, never below
    /// <see cref="MinScale"/>; a text that fits is drawn exactly as the game draws it. Lines are counted from the text
    /// the game actually wrapped, so any font works. Call <see cref="Fit"/> after setting the text; the game's own
    /// setters on the panel are patched to do the same.
    /// </summary>
    public class PanelText : MonoBehaviour
    {
        /// <summary>The lines a panel paragraph may take: the game's longest god text and flavour take four.</summary>
        public const int DefaultMaxLines = 4;
        /// <summary>The smallest the characters get, as a share of their own size.</summary>
        public const float MinScale = 0.7f;
        const float Step = 0.06f;

        /// <summary>Lines this paragraph may take.</summary>
        public int MaxLines = DefaultMaxLines;

        GUIText m_text;
        TextMesh m_mesh;
        float m_base = -1f;
        bool m_refit;

        /// <summary>Fit <paramref name="g"/>'s current text to <paramref name="maxLines"/> lines (see the class).</summary>
        public static void Fit(GUIText g, int maxLines = DefaultMaxLines)
        {
            if (g == null) return;
            var p = g.GetComponent<PanelText>() ?? g.gameObject.AddComponent<PanelText>();
            p.MaxLines = Mathf.Max(1, maxLines);
            p.Refit();
        }

        void Init()
        {
            if (m_text != null) return;
            m_text = GetComponent<GUIText>();
            m_mesh = GetComponent<TextMesh>();
            if (m_mesh != null && m_base < 0f) m_base = m_mesh.characterSize;
        }

        // shown again: GUIText sets a text it was given while hidden in its own OnEnable; fit it after that
        void OnEnable() { m_refit = true; }

        void LateUpdate()
        {
            if (!m_refit) return;
            m_refit = false;
            Refit();
        }

        void Refit()
        {
            Init();
            if (m_text == null || m_mesh == null) return;
            if (!gameObject.activeInHierarchy)
            {
                // a hidden GUIText wraps on enable: at the normal size, then OnEnable fits it
                Size(1f);
                m_refit = true;
                return;
            }
            string text = R.Get<string>(m_text, "m_originalText");
            if (string.IsNullOrEmpty(text) || m_text.GetWrapWidth() <= 0f) { if (Size(1f)) m_text.SetText(text ?? string.Empty); return; }
            if (Size(1f)) m_text.SetText(text);
            for (float s = 1f - Step; Lines(m_mesh.text) > MaxLines && s >= MinScale - 0.001f; s -= Step)
            {
                Size(s);
                m_text.SetText(text);
            }
        }

        /// <summary>Draw at <paramref name="scale"/> of the normal size; true if that changed it.</summary>
        bool Size(float scale)
        {
            float want = m_base * scale;
            if (Mathf.Abs(m_mesh.characterSize - want) < 0.0001f) return false;
            m_mesh.characterSize = want;
            // GUIText's wrapper keeps every glyph width it measured: a new one measures at the new size
            R.Set(m_text, "m_textWrapper", null);
            return true;
        }

        static int Lines(string s)
        {
            if (string.IsNullOrEmpty(s)) return 0;
            int n = 1;
            for (int i = 0; i < s.Length; i++) if (s[i] == '\n') n++;
            return n;
        }
    }

    /// <summary>The game's own god-select texts (a god, Random, Trials, a locked god) are fitted the same way.</summary>
    [HarmonyPatch]
    static class Patch_PanelTextFit
    {
        static IEnumerable<MethodBase> TargetMethods()
        {
            foreach (var n in new[] { "SetRandomDeity", "SetTrialsDeity", "SetLockedDeity", "SetDeity" })
            {
                var m = AccessTools.DeclaredMethod(typeof(MenuDeitySelectPlayer), n);
                if (m != null) yield return m;
            }
        }

        static void Postfix(GUIText ___m_text, GUIText ___m_textFlavour)
        {
            try { PanelText.Fit(___m_text); PanelText.Fit(___m_textFlavour); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Panel text fit: " + e.Message); }
        }
    }
}
