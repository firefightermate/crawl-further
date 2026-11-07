using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Ghosts;
    using CrawlFurther.Gods;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Heroes;

    /// <summary>
    /// Custom ghost: LOOK (shape, colour, eyes, trail; the portrait follows live), then POWER (what the silver / gold
    /// ghost can do, in plain words) and DONE. Choices are written as they change and put back on cancel.
    /// </summary>
    public class GhostEditor : ISlotEditor
    {
        // one per player id (panels come and go with scenes; an editor object holds no panel between opens)
        static readonly Dictionary<int, GhostEditor> s_by = new Dictionary<int, GhostEditor>();
        public static ISlotEditor For(MenuDeitySelectPlayer panel)
        {
            int pid = panel != null ? R.Get<int>(panel, "m_playerId") : -1;
            GhostEditor e;
            if (!s_by.TryGetValue(pid, out e)) s_by[pid] = e = new GhostEditor();
            return e;
        }

        SlotEditorUI m_ui;
        int m_pid;
        SlotTier m_tier;
        Action m_done, m_cancel;
        int[] m_before;

        public bool IsOpen { get { return m_ui != null && m_ui.IsOpen; } }
        public void Close() { if (m_ui != null) m_ui.End(); }

        public void Open(MenuDeitySelectPlayer panel, int playerId, SlotTier tier, Action onDone, Action onCancel)
        {
            m_pid = playerId; m_tier = tier; m_done = onDone; m_cancel = onCancel;
            m_before = (int[])GhostCustom.Look(playerId, tier).Clone();
            m_ui = SlotEditorUI.For(panel);
            m_ui.Begin(panel, playerId, tier, tier == SlotTier.Gold ? "GOLD SPECTRE" : "SILVER SHADE");
            m_ui.onAbort = Cancel;   // the look is written as it changes: put the old one back
            Look();
        }

        void Portrait() { m_ui.SetPortraitFrom(() => GhostCustom.PreviewClip(m_pid, m_tier)); }

        void Look() { LookPage(0); }

        /// <summary>Two rows a page (SHAPE, COLOUR / EYES, TRAIL), then POWER.</summary>
        void LookPage(int page)
        {
            m_ui.Clear();
            Portrait();
            int from = page * 2, to = Mathf.Min(GhostCustom.PartCount, from + 2);
            for (int k = from; k < to; k++)
            {
                int part = k;
                m_ui.Add(new CycleRow
                {
                    y = CycleRow.FirstY - (k - from) * CycleRow.Pitch, label = GhostCustom.PartLabel(part),
                    count = () => GhostCustom.ChoiceCount(part),
                    get = () => GhostCustom.Get(m_pid, m_tier, part),
                    set = i => { GhostCustom.Set(m_pid, m_tier, part, i); Portrait(); },
                    name = i => GhostCustom.ChoiceName(part, i),
                });
            }
            bool more = to < GhostCustom.PartCount;
            m_ui.Add(new ButtonRow { y = HeroEditor.ButtonY, text = more ? "NEXT " + (page + 2) + "/" + ((GhostCustom.PartCount + 1) / 2) : "POWER", onPress = () => { if (more) LookPage(page + 1); else Power(); } });
            m_ui.onBack = () => { if (page > 0) LookPage(page - 1); else Cancel(); };
        }

        void Power()
        {
            m_ui.Clear();
            Portrait();
            m_ui.Add(new InfoRow { y = -60.5f, line1 = () => GhostCustom.MechanicTitle(m_tier) });
            m_ui.Add(new InfoRow { y = -65f, paragraph = true, wrap = 46f, line1 = () => Sentences(GhostControls.Personalise(GhostCustom.MechanicText(m_tier), GhostControls.Name(m_pid))) });
            m_ui.Add(new ButtonRow { y = HeroEditor.ButtonY, text = "DONE", onPress = Done });
            m_ui.onBack = () => LookPage((GhostCustom.PartCount - 1) / 2);
        }

        /// <summary>The ghost text's lines as sentences: "a\nb" -> "a. b." (no full stop doubled).</summary>
        public static string Sentences(string s)
        {
            var parts = (s ?? "").Split('\n');
            var sb = new System.Text.StringBuilder();
            foreach (var p0 in parts)
            {
                var p = p0.Trim();
                if (p.Length == 0) continue;
                if (sb.Length > 0) sb.Append(' ');
                sb.Append(p);
                if (!p.EndsWith(".") && !p.EndsWith("!") && !p.EndsWith("?")) sb.Append('.');
            }
            return sb.ToString();
        }

        void Cancel()
        {
            if (m_before == null) return;   // already cancelled / done (abort and Back can't both run it)
            for (int k = 0; k < m_before.Length && k < GhostCustom.PartCount; k++) GhostCustom.Set(m_pid, m_tier, k, m_before[k]);
            m_before = null;
            Close();
            if (m_cancel != null) m_cancel();
        }

        void Done()
        {
            m_before = null;
            Close();
            if (m_done != null) m_done();
        }
    }
}
