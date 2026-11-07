using System;
using System.Collections.Generic;
using HarmonyLib;
using InControl;
using UnityEngine;

namespace CrawlFurther.Ghosts
{
    using CrawlFurther.Compat;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    // The ghost button in the game's own controls menus (GhostControls holds the choice):
    //   - a player's Controls page on the join screen (Reset / Redefine / Aim / GHOST / Back): every keyboard or pad
    //     player sets their own. The mouse has no Controls page in vanilla (it is always the middle click).
    //   - Options > Keyboards: "- Ghost Button -", then a row per keyboard and the mouse's (shown, not settable).
    // Choosing a row works like vanilla's Redefine: the same REDEFINE panel asks to hold the button, the bar fills over
    // the same 0.5 s, and a button the game already reads (or another keyboard's ghost key) is refused: the bar stays
    // empty and the panel says which. Back keeps the old one. Vanilla's resets reset the ghost button too; a vanilla
    // Redefine that takes it moves it, and the menu shows that.

    /// <summary>Drives a vanilla REDEFINE panel (MenuInputBinding: its hold text, bar and title) for one ghost button.</summary>
    public class GhostBindListener : MonoBehaviour
    {
        const int None = int.MinValue;
        TextMesh m_hold, m_title;
        GUIBar m_bar;
        string m_titleWas;
        bool m_narrow, m_anyBack, m_active;
        int m_cid;
        string m_who;
        Action<bool> m_done;
        int m_pressed = None;
        float m_held;
        string m_refused;
        float m_refusedAt;
        int m_finishFrame = -1;
        bool m_result;

        static KeyCode[] s_keys;
        static InputControlType[] s_controls;

        public bool Active { get { return m_active; } }

        public static GhostBindListener For(MenuInputBinding mib)
        {
            if (mib == null) return null;
            var l = mib.GetComponent<GhostBindListener>() ?? mib.gameObject.AddComponent<GhostBindListener>();
            l.m_hold = R.Get<TextMesh>(mib, "m_textHold");
            l.m_bar = R.Get<GUIBar>(mib, "m_barHold");
            l.m_narrow = R.Get<bool>(mib, "m_narrow");
            var t = mib.transform.Find("TextTitle");
            l.m_title = t != null ? t.GetComponent<TextMesh>() : null;
            return l;
        }

        /// <summary>Listen for controller cid's new ghost button. who: "keys 2" on the shared keyboards page, else null.
        /// anyBack: any controller's back cancels (the options page belongs to nobody in particular).</summary>
        public void Begin(int cid, string who, bool anyBack, Action<bool> done)
        {
            m_cid = cid; m_who = who; m_anyBack = anyBack; m_done = done;
            m_pressed = None; m_held = 0f; m_refused = null; m_finishFrame = -1;
            m_active = true;
            if (m_title != null)
            {
                if (m_titleWas == null) m_titleWas = m_title.text;
                m_title.text = "GHOST";
            }
            if (s_keys == null)
            {
                var keys = new List<KeyCode>();
                foreach (KeyCode k in Enum.GetValues(typeof(KeyCode)))
                    if ((int)k > 0 && (int)k < GhostControls.KeyLimit && k != KeyCode.Escape && !keys.Contains(k)) keys.Add(k);
                s_keys = keys.ToArray();
                var cs = new List<InputControlType>();
                foreach (InputControlType c in Enum.GetValues(typeof(InputControlType)))
                    if (c != InputControlType.None && c != InputControlType.Count && !cs.Contains(c)) cs.Add(c);
                s_controls = cs.ToArray();
            }
            Draw();
        }

        void Update()
        {
            if (!m_active) return;
            try
            {
                // finish a frame late: the back press that cancelled must not also step the menu back
                if (m_finishFrame >= 0)
                {
                    if (Time.frameCount > m_finishFrame) Complete();
                    return;
                }
                if (CancelPressed()) { Finish(false); return; }
                bool pad = GhostControls.IsPad(m_cid);
                InputDevice dev = pad ? GhostControls.Device(m_cid) : null;
                if (pad && dev == null) { Finish(false); return; }
                if (m_pressed == None)
                {
                    int fresh = pad ? FreshPad(dev) : FreshKey();
                    if (fresh != None)
                    {
                        string why = GhostControls.Refuse(m_cid, fresh);
                        if (why != null) { m_refused = why; m_refusedAt = Time.unscaledTime; }
                        else { m_pressed = fresh; m_held = 0f; m_refused = null; }
                    }
                }
                else if (pad ? Held(dev, m_pressed) : Input.GetKey((KeyCode)m_pressed))
                {
                    m_held += Time.unscaledDeltaTime;
                    if (m_held >= GhostControls.BindTime)
                    {
                        GhostControls.Choose(m_cid, m_pressed);
                        Finish(true);
                        return;
                    }
                }
                else { m_pressed = None; m_held = 0f; }
                if (m_refused != null && Time.unscaledTime - m_refusedAt > 2f) m_refused = null;
                Draw();
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button menu: " + e.Message); Finish(false); }
        }

        bool CancelPressed()
        {
            if (Input.GetKeyDown(KeyCode.Escape)) return true;
            if (m_anyBack) return SystemInput.InputDown(eInput.Alt);
            return SystemInput.InputDown(eInput.Alt, (eController)m_cid);
        }

        int FreshKey()
        {
            if (!Input.anyKeyDown) return None;
            foreach (var k in s_keys) if (Input.GetKeyDown(k)) return (int)k;
            return None;
        }

        /// <summary>Vanilla's pad binding test: a control past 0.65 that was not past it last frame.</summary>
        int FreshPad(InputDevice dev)
        {
            foreach (var t in s_controls)
            {
                if (!dev.HasControl(t)) continue;
                var c = dev.GetControl(t);
                float v = c.Value, last = c.LastValue;
                if (v > GhostControls.BindAt && last <= GhostControls.BindAt) return (int)t + 1;
                if (v < -GhostControls.BindAt && last >= -GhostControls.BindAt) return -((int)t + 1);
            }
            return None;
        }

        static bool Held(InputDevice dev, int code)
        {
            var c = dev.GetControl((InputControlType)(Mathf.Abs(code) - 1));
            if (c == null || c == InputControl.Null) return false;
            return code < 0 ? c.Value < -GhostControls.BindAt : c.Value > GhostControls.BindAt;
        }

        void Draw()
        {
            string now = GhostControls.NameOf(m_cid);
            if (m_hold != null) m_hold.text = Text(m_narrow, m_who, now, m_refused);
            if (m_bar != null) m_bar.SetValue(m_pressed == None ? 0f : Mathf.Clamp01(m_held / GhostControls.BindTime));
        }

        /// <summary>The hold text: vanilla's "Hold / button A" layout (narrow: one word or two a line).</summary>
        public static string Text(bool narrow, string who, string now, string refused)
        {
            if (narrow)
                return refused != null ? Split(refused) + "\n\nhold another"
                                       : "Hold\nghost button\n\nback keeps\n" + now;
            if (refused != null) return refused + "\n(hold another)";
            return "Hold " + (who != null ? who + " " : "") + "ghost button\n(back keeps " + now + ")";
        }

        /// <summary>A narrow panel's line is 44 font pixels: "full stop is taken" becomes "full stop\nis taken",
        /// "keys 2 has full stop" becomes "keys 2\nhas full stop"; "X is taken" stays one line.</summary>
        static string Split(string s)
        {
            if (PauseTips.Width(s) <= GhostJoinRow.RowWidth) return s;
            int k = s.LastIndexOf(" is ", StringComparison.Ordinal);
            if (k < 0) k = s.LastIndexOf(" has ", StringComparison.Ordinal);
            return k > 0 ? s.Substring(0, k) + "\n" + s.Substring(k + 1) : s;
        }

        void Finish(bool ok)
        {
            m_result = ok;
            m_finishFrame = Time.frameCount;
            m_pressed = None; m_held = 0f;
            if (m_bar != null) m_bar.SetValue(ok ? 1f : 0f);
        }

        void Complete()
        {
            m_active = false;
            m_finishFrame = -1;
            RestoreTitle();
            var done = m_done;
            m_done = null;
            if (done != null) done(m_result);
        }

        void RestoreTitle()
        {
            if (m_title != null && m_titleWas != null) m_title.text = m_titleWas;
        }

        void OnDisable()
        {
            // the panel went away mid-listen (the player left): nothing chosen, the menu is gone
            if (!m_active) return;
            m_active = false;
            m_finishFrame = -1;
            m_done = null;
            RestoreTitle();
        }
    }
}
