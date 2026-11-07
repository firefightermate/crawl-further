using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Heroes
{
    using CrawlFurther.Gods;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Ghosts;

    // =====================================================================================================================
    // The silver / gold hero editor (HeroCustom) and ghost editor (GhostCustom) on the SlotEditorUI kit.
    // Both edit a copy and store it only on DONE; Back steps a page back, and from the first page cancels.
    // =====================================================================================================================

    /// <summary>
    /// Custom hero: three look pages (outfit, main colour, trim colour / skin, hair / head, face), then GEAR: any weapon,
    /// and for gold a second page with any spell; each shows the pick's text and the total stat cost. The panel portrait
    /// shows the hero being edited, in this player's colours, rebuilt the same frame a row changes.
    /// </summary>
    public class HeroEditor : ISlotEditor
    {
        // one per player id (panels come and go with scenes; an editor object holds no panel between opens)
        static readonly Dictionary<int, HeroEditor> s_by = new Dictionary<int, HeroEditor>();
        public static ISlotEditor For(MenuDeitySelectPlayer panel)
        {
            int pid = panel != null ? R.Get<int>(panel, "m_playerId") : -1;
            HeroEditor e;
            if (!s_by.TryGetValue(pid, out e)) s_by[pid] = e = new HeroEditor();
            return e;
        }

        SlotEditorUI m_ui;
        int m_pid;
        SlotTier m_tier;
        Action m_done, m_cancel;
        HeroCustom.Choice m_c;
        int m_focusPick;   // 0 weapon row, 1 spell row (which pick the info text describes)

        public bool IsOpen { get { return m_ui != null && m_ui.IsOpen; } }
        public void Close() { if (m_ui != null) m_ui.End(); }

        public void Open(MenuDeitySelectPlayer panel, int playerId, SlotTier tier, Action onDone, Action onCancel)
        {
            m_pid = playerId; m_tier = tier; m_done = onDone; m_cancel = onCancel;
            m_c = HeroCustom.Get(playerId, tier).Clone();
            m_ui = SlotEditorUI.For(panel);
            m_ui.Begin(panel, playerId, tier, tier == SlotTier.Gold ? "GOLD HERO" : "SILVER HERO");
            m_ui.onAbort = () => { if (m_cancel != null) m_cancel(); };   // nothing was stored: the copy is dropped
            Look(0);
        }

        void Portrait() { m_ui.SetPortraitFrom(() => HeroCustom.PortraitClip(m_c, m_pid, m_tier)); }

        CycleRow PartRow(string partId, float y)
        {
            int p = HeroCustom.PartIndex(partId);
            var part = HeroCustom.Parts[p];
            return new CycleRow
            {
                y = y, label = part.name,
                count = () => part.Count,
                get = () => Mathf.Clamp(m_c.look[p], 0, part.Count - 1),
                set = i => { m_c.look[p] = i; Portrait(); },
                name = i => part.options[i].name,
            };
        }

        // three look pages of up to three rows each (rows CycleRow.Pitch apart), then GEAR
        static readonly string[][] LookPages =
        {
            new[] { HeroCustom.PartOutfit, HeroCustom.PartColour, HeroCustom.PartTrim },
            new[] { HeroCustom.PartSkin, HeroCustom.PartHair },
            new[] { HeroCustom.PartHead, HeroCustom.PartFace },
        };

        void Look(int page)
        {
            m_ui.Clear();
            Portrait();
            var ids = LookPages[page];
            for (int i = 0; i < ids.Length; i++) m_ui.Add(PartRow(ids[i], CycleRow.FirstY - i * CycleRow.Pitch));
            bool last = page == LookPages.Length - 1;
            m_ui.Add(new ButtonRow { y = ButtonY, text = last ? "GEAR" : "NEXT " + (page + 2) + "/" + LookPages.Length,
                                     onPress = () => { if (last) Gear(); else Look(page + 1); } });
            m_ui.onBack = () => { if (page > 0) Look(page - 1); else { Close(); if (m_cancel != null) m_cancel(); } };
        }

        public const float ButtonY = -108.5f;

        HeroCustom.Pick FocusedPick
        {
            get { return m_focusPick == 1 && HeroCustom.AllowsSpell(m_tier) ? HeroCustom.SpellOf(m_c, m_tier) : HeroCustom.WeaponOf(m_c); }
        }

        void Gear() { Gear(0); }

        /// <summary>GEAR: the weapon page, and for gold a second page for the spell. Each shows the pick, the total stat
        /// cost of both picks, and what the pick does (up to three lines).</summary>
        void Gear(int page)
        {
            m_ui.Clear();
            Portrait();
            bool spellPage = page == 1;
            m_focusPick = spellPage ? 1 : 0;
            if (!spellPage)
            {
                var weapons = HeroCustom.Weapons;
                m_ui.Add(new CycleRow
                {
                    y = CycleRow.FirstY, label = "WEAPON",
                    count = () => weapons.Count,
                    get = () => HeroCustom.WeaponIndex(m_c.weapon),
                    set = i => { int cur = HeroCustom.WeaponIndex(m_c.weapon); m_c.StepWeapon(Step(cur, i, weapons.Count)); Portrait(); },
                    name = i => weapons[i].name,
                    locked = i => !weapons[i].Available,
                });
            }
            else
            {
                var spells = HeroCustom.Spells;
                m_ui.Add(new CycleRow
                {
                    y = CycleRow.FirstY, label = "SPELL",
                    count = () => spells.Count,
                    get = () => HeroCustom.SpellIndex(m_c.spell),
                    set = i => { int cur = HeroCustom.SpellIndex(m_c.spell); m_c.StepSpell(Step(cur, i, spells.Count)); Portrait(); },
                    name = i => spells[i].name,
                    locked = i => !spells[i].Available,
                });
            }
            m_ui.Add(new InfoRow
            {
                y = CycleRow.FirstY - 9f,
                line1 = () => { var d = HeroCustom.TotalDebuff(m_c, m_tier); return d.IsEmpty ? "No stat cost" : "Total " + d.Text; },
            });
            m_ui.Add(new InfoRow { y = CycleRow.FirstY - 13.5f, paragraph = true, wrap = 46f, line1 = () => GhostEditor.Sentences(FocusedPick.text) });
            bool more = !spellPage && HeroCustom.AllowsSpell(m_tier);
            m_ui.Add(new ButtonRow { y = ButtonY, text = more ? "SPELL" : "DONE", onPress = () => { if (more) Gear(1); else Done(); } });
            m_ui.onBack = () => { if (spellPage) Gear(0); else Look(LookPages.Length - 1); };
        }

        /// <summary>CycleRow hands us the target index; the hero API steps (skipping picks that did not load).</summary>
        static int Step(int cur, int target, int n)
        {
            int d = ((target - cur) % n + n) % n;
            return d == 0 ? 0 : d <= n / 2 ? 1 : -1;
        }

        void Done()
        {
            HeroCustom.Set(m_pid, m_tier, m_c);
            Close();
            if (m_done != null) m_done();
        }
    }
}
