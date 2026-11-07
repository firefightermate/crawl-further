using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text;
using InControl;
using UnityEngine;

namespace CrawlFurther.Ghosts
{
    using CrawlFurther.Compat;
    using CrawlFurther.Util;

    /// <summary>
    /// The ghost button: one extra button per controller that mods can give ghost and monster players an action on,
    /// without taking a button the game uses. Players set it in the game's own controls menus (see GhostControlsMenu);
    /// it is saved in BepInEx/config/CrawlFurther.Controls.cfg. Read it with <see cref="Down"/> and name it in text with
    /// <see cref="Name(PlayerData)"/> or <see cref="Personalise"/>.
    ///
    /// Each controller has a choice (a key or pad control the player picked) or "auto": the first free entry of a
    /// fallback list. Free means the game does not read it for that controller in any form:
    ///   keyboards: never Escape (back on every keyboard), Return (keyboard 1 pause), F8 to F10 (mod keys); X, Space, Z
    ///              and the arrows while keyboard 1 uses its default keys; every key bound on any keyboard (they share
    ///              one physical keyboard); another keyboard's ghost key.
    ///   pads:      the pad's bound controls (a whole stick or d-pad when any direction of it is bound), or its defaults
    ///              when unbound (A, B, the left stick and d-pad, Start / Y); the system buttons (Start, Back, Menu...).
    ///   mouse:     always the middle click, which vanilla reads as Start: a mod acting on it for a mouse player should
    ///              keep that click from pausing.
    /// Fallbacks: keyboard 1 C, V | keyboard 2 B, N | keyboard 3 M, comma | keyboard 4 full stop, slash (then G, H, J...);
    ///            pad X, RB, LB, RT, LT, R3, L3, Y.
    /// A vanilla rebind that takes a choice's key moves the ghost button to its next free fallback (<see cref="Moved"/>
    /// is set for the menus to show).
    /// </summary>
    public static class GhostControls
    {
        /// <summary>The settings file in BepInEx/config.</summary>
        public const string FILE = "CrawlFurther.Controls.cfg";
        /// <summary>The ghost button's name when no player is known.</summary>
        public const string AnyName = "C, middle click or X";
        /// <summary>Hold time to set a button, as vanilla's binding (SystemInput.BIND_TIME).</summary>
        public const float BindTime = 0.5f;
        /// <summary>A pad control counts as pressed past this (vanilla's GetInputBindWasPressed).</summary>
        const float PressAt = 0.5f;
        /// <summary>A pad control counts when binding past this (vanilla's UpdateBinding).</summary>
        public const float BindAt = 0.65f;
        const int None = int.MinValue;
        const int Unset = int.MaxValue;
        /// <summary>Keyboard keys only (vanilla's KEYCODE_MAX_VALID: mouse and joystick buttons follow).</summary>
        public const int KeyLimit = 323;

        static string Path { get { return System.IO.Path.Combine(BepInEx.Paths.ConfigPath, FILE); } }

        // per controller id (eController 0..8)
        static readonly int[] s_choice = Filled(9, None);       // the player's pick (None: auto)
        static readonly string[] s_padDevice = new string[4];    // the pad (InControl Meta) a pad pick belongs to
        static readonly int[] s_eff = Filled(9, None);           // what the button is right now
        static readonly int[] s_last = Filled(9, Unset);         // the last resolved button (to notice a move)
        static readonly bool[] s_moved = new bool[9];
        static int s_frame = -1;           // -1: re-resolve on the next ask (Changed)
        static float s_resolvedAt;
        static bool s_loaded;
        static bool s_watching;    // moves are noticed only after a menu asked (Watch): not while the game loads bindings

        static int[] Filled(int n, int v) { var a = new int[n]; for (int i = 0; i < n; i++) a[i] = v; return a; }

        static readonly KeyCode[][] KeyLists =
        {
            new[] { KeyCode.C, KeyCode.V }, new[] { KeyCode.B, KeyCode.N },
            new[] { KeyCode.M, KeyCode.Comma }, new[] { KeyCode.Period, KeyCode.Slash },
        };
        static readonly KeyCode[] KeyExtras = { KeyCode.G, KeyCode.H, KeyCode.J, KeyCode.K, KeyCode.L, KeyCode.F, KeyCode.R,
                                                KeyCode.T, KeyCode.Y, KeyCode.U, KeyCode.I, KeyCode.O, KeyCode.P, KeyCode.Q };
        static readonly KeyCode[] KeyAlways = { KeyCode.Escape, KeyCode.Return, KeyCode.F8, KeyCode.F9, KeyCode.F10 };
        static readonly KeyCode[] KeyDefaults = { KeyCode.X, KeyCode.Space, KeyCode.Z, KeyCode.LeftArrow, KeyCode.RightArrow,
                                                  KeyCode.UpArrow, KeyCode.DownArrow };
        static readonly InputControlType[] PadList =
        {
            InputControlType.Action3, InputControlType.RightBumper, InputControlType.LeftBumper, InputControlType.RightTrigger,
            InputControlType.LeftTrigger, InputControlType.RightStickButton, InputControlType.LeftStickButton, InputControlType.Action4,
        };
        static readonly InputControlType[] PadSystem =
        {
            InputControlType.Back, InputControlType.Start, InputControlType.Select, InputControlType.System, InputControlType.Options,
            InputControlType.Pause, InputControlType.Menu, InputControlType.Share, InputControlType.Home, InputControlType.View,
            InputControlType.Power, InputControlType.Command,
        };
        static readonly InputControlType[][] PadGroups =
        {
            new[] { InputControlType.LeftStickUp, InputControlType.LeftStickDown, InputControlType.LeftStickLeft,
                    InputControlType.LeftStickRight, InputControlType.LeftStickX, InputControlType.LeftStickY },
            new[] { InputControlType.RightStickUp, InputControlType.RightStickDown, InputControlType.RightStickLeft,
                    InputControlType.RightStickRight, InputControlType.RightStickX, InputControlType.RightStickY },
            new[] { InputControlType.DPadUp, InputControlType.DPadDown, InputControlType.DPadLeft, InputControlType.DPadRight,
                    InputControlType.DPadX, InputControlType.DPadY },
        };

        /// <summary>Controller id (eController) tests.</summary>
        public static bool IsKeyboard(int cid) { return cid >= (int)eController.Keyboard1 && cid <= (int)eController.Keyboard4; }
        public static bool IsPad(int cid) { return cid >= (int)eController.Controller1 && cid <= (int)eController.Controller4; }
        public static bool IsMouse(int cid) { return cid == (int)eController.Mouse; }

        /// <summary>The ghost button was pressed this frame by this (human) player. Never while the game is paused.</summary>
        public static bool Down(PlayerData pd)
        {
            try
            {
                if (pd == null || pd.IsBot || !pd.IsActive || SystemTime.Paused) return false;
                int cid = (int)pd.ControllerId;
                // an online player (Crawl Online): their own PC sends its ghost button as a Left+Right pair
                if (IsPad(cid) && CompatOnline.IsNetPad(Device(cid))) return CompatOnline.GhostPressed(Device(cid));
                return LocalDown(cid);
            }
            catch (Exception e) { Warn("Down", e); }
            return false;
        }

        /// <summary>This PC's ghost button for a controller was pressed this frame (no player needed: an online client
        /// sends it for each of its controllers in use).</summary>
        public static bool LocalDown(int cid)
        {
            try
            {
                if (IsMouse(cid)) return Input.GetMouseButtonDown(2);
                Resolve();
                if (IsKeyboard(cid)) return s_eff[cid] != None && Input.GetKeyDown((KeyCode)s_eff[cid]);
                if (IsPad(cid))
                {
                    var dev = Device(cid);
                    return dev != null && s_eff[cid] != None && !CompatOnline.IsNetPad(dev) && PadWasPressed(dev, s_eff[cid]);
                }
            }
            catch (Exception e) { Warn("LocalDown", e); }
            return false;
        }

        /// <summary>The ghost button's name for this player ("C", "middle click", "RB"...). Plain words.</summary>
        public static string Name(PlayerData pd)
        {
            try
            {
                if (pd == null || pd.ControllerId == eController.None) return AnyName;
                return NameOf((int)pd.ControllerId);
            }
            catch (Exception e) { Warn("Name", e); return AnyName; }
        }

        /// <summary>The ghost button's name for a player id.</summary>
        public static string Name(int playerId)
        {
            PlayerData pd = null;
            try { pd = SystemPlayers.GetPlayer(playerId); } catch { }
            return Name(pd);
        }

        /// <summary>The ghost button's name for a controller (eController id).</summary>
        public static string NameOf(int cid)
        {
            if (IsMouse(cid)) return "middle click";
            if (!IsKeyboard(cid) && !IsPad(cid)) return AnyName;
            if (CompatOnline.IsRemotePad(cid)) return AnyName;    // an online player's button is set on their own PC
            Resolve();
            if (s_eff[cid] == None) return "none";
            return IsKeyboard(cid) ? KeyName((KeyCode)s_eff[cid]) : PadName(s_eff[cid]);
        }

        /// <summary>
        /// Text naming the ghost button, made personal: the first "ghost button" (also inside a colour tag) gets " (name)"
        /// after it, unless a name in brackets already follows; the old fixed "C, middle click or X" becomes the name.
        /// </summary>
        public static string Personalise(string s, string name)
        {
            if (string.IsNullOrEmpty(s) || string.IsNullOrEmpty(name)) return s;
            s = s.Replace(AnyName, name);
            int k = s.IndexOf("ghost button", StringComparison.OrdinalIgnoreCase);
            if (k < 0) return s;
            int end = k + "ghost button".Length;
            if (string.CompareOrdinal(s, end, "</color>", 0, 8) == 0) end += 8;
            string rest = s.Substring(end);
            if (rest.StartsWith(" (", StringComparison.Ordinal) || rest.StartsWith("(", StringComparison.Ordinal)) return s;
            return s.Substring(0, end) + " (" + name + ")" + rest;
        }

        /// <summary>The name for everyone a page is for: one player's own, or "P1 C, P2 X" for several.</summary>
        public static string NameFor(IList<PlayerData> players)
        {
            if (players == null || players.Count == 0) return AnyName;
            if (players.Count == 1) return Name(players[0]);
            var parts = new List<string>();
            foreach (var pd in players) if (pd != null) parts.Add("P" + (pd.Id + 1) + " " + Name(pd));
            return parts.Count > 0 ? string.Join(", ", parts.ToArray()) : AnyName;
        }

        // ------------------------------------------------------------------ choosing (the menus)
        /// <summary>Why a code cannot be this controller's ghost button (null: it can). Plain words.</summary>
        public static string Refuse(int cid, int code)
        {
            Resolve();
            if (IsKeyboard(cid))
            {
                if (code <= 0 || code >= KeyLimit) return "not a key";
                var taken = KeyTakenBase();
                if (taken.Contains(code)) return KeyName((KeyCode)code) + " is taken";
                for (int o = (int)eController.Keyboard1; o <= (int)eController.Keyboard4; o++)
                {
                    if (o == cid) continue;
                    if (s_choice[o] == code || (s_eff[o] == code && KeyboardInUse(o)))
                        return "keys " + (o - 3) + " has " + KeyName((KeyCode)code);
                }
                return null;
            }
            if (IsPad(cid))
            {
                if (code == None || code == 0) return "not a button";
                if (PadTaken(cid).Contains(Mathf.Abs(code) - 1)) return PadName(code) + " is taken";
                return null;
            }
            return "fixed";
        }

        /// <summary>Set this controller's ghost button (the menus check Refuse first). Saves at once.</summary>
        public static void Choose(int cid, int code)
        {
            Load();
            if (!IsKeyboard(cid) && !IsPad(cid)) return;
            Watch();                                       // another keyboard's auto key this takes shows as moved
            s_choice[cid] = code;
            if (IsPad(cid)) s_padDevice[cid] = DeviceName(cid);
            s_moved[cid] = false; s_last[cid] = Unset;     // the player's own change is not a move
            Changed();
            Save();
        }

        /// <summary>Back to auto (the first free fallback), as vanilla's reset does for the other buttons.</summary>
        public static void Reset(int cid)
        {
            Load();
            if (cid < 0 || cid >= 9 || s_choice[cid] == None) return;
            s_choice[cid] = None;
            if (IsPad(cid)) s_padDevice[cid] = null;
            s_moved[cid] = false; s_last[cid] = Unset;
            Changed();
            Save();
        }

        /// <summary>Every keyboard back to auto.</summary>
        public static void ResetKeyboards() { for (int c = (int)eController.Keyboard1; c <= (int)eController.Keyboard4; c++) Reset(c); }
        /// <summary>Every controller back to auto.</summary>
        public static void ResetAll() { for (int c = 0; c < 9; c++) Reset(c); }

        /// <summary>The player picked this one (false: auto).</summary>
        public static bool IsChosen(int cid) { Resolve(); return cid >= 0 && cid < 9 && s_choice[cid] != None; }

        /// <summary>The ghost button moved by itself (a rebind took it) since the menus last showed it.</summary>
        public static bool Moved(int cid) { Resolve(); return cid >= 0 && cid < 9 && s_moved[cid]; }
        /// <summary>The menus have shown the move.</summary>
        public static void ClearMoved(int cid) { if (cid >= 0 && cid < 9) s_moved[cid] = false; }

        /// <summary>Re-resolve now (after a rebind or a reset).</summary>
        public static void Changed() { s_frame = -1; }

        /// <summary>A menu is about to change bindings: resolve now, and from here on a ghost button that a rebind (or
        /// another keyboard's pick) moves is flagged Moved for the menus to show.</summary>
        public static void Watch() { Changed(); Resolve(); s_watching = true; }

        // ------------------------------------------------------------------ resolving
        /// <summary>Once a frame: drop picks a rebind has taken, then fill every auto from its fallback list.</summary>
        static void Resolve()
        {
            // cached: the menus, resets and rebinds call Changed(); once a second is the safety net for anything else
            // (a pad plugged in, bindings loaded from the save), so Down() is a lookup plus an Input check
            float now = Time.realtimeSinceStartup;
            if (s_frame >= 0 && now - s_resolvedAt < 1f) return;
            s_frame = Time.frameCount;
            s_resolvedAt = now;
            Load();
            bool dirty = false;
            // keyboards: picks first (a lower keyboard wins a clash read from the file), then autos
            var baseTaken = KeyTakenBase();
            var claimed = new HashSet<int>();
            for (int c = (int)eController.Keyboard1; c <= (int)eController.Keyboard4; c++)
            {
                int k = s_choice[c];
                if (k == None) continue;
                if (k <= 0 || k >= KeyLimit || baseTaken.Contains(k) || claimed.Contains(k)) { s_choice[c] = None; dirty = true; }
                else claimed.Add(k);
            }
            for (int c = (int)eController.Keyboard1; c <= (int)eController.Keyboard4; c++)
            {
                int k = s_choice[c];
                if (k == None)
                {
                    foreach (var cand in KeyCandidates(c - (int)eController.Keyboard1))
                        if (!baseTaken.Contains((int)cand) && !claimed.Contains((int)cand)) { k = (int)cand; break; }
                    if (k != None) claimed.Add(k);
                }
                Settle(c, k);
            }
            // pads: each its own device
            for (int c = (int)eController.Controller1; c <= (int)eController.Controller4; c++)
            {
                var taken = PadTaken(c);
                int k = None;
                bool mine = s_choice[c] != None && (s_padDevice[c] == null || s_padDevice[c] == DeviceName(c) || Device(c) == null);
                if (mine && Device(c) != null)
                {
                    if (taken.Contains(Mathf.Abs(s_choice[c]) - 1)) { s_choice[c] = None; s_padDevice[c] = null; dirty = true; }
                    else k = s_choice[c];
                }
                if (k == None)
                    foreach (var t in PadList)
                        if (!taken.Contains((int)t) && (Device(c) == null || Device(c).HasControl(t) || t == InputControlType.Action3)) { k = (int)t + 1; break; }
                Settle(c, k);
            }
            s_eff[(int)eController.Mouse] = 2;
            if (dirty) Save();
        }

        static void Settle(int c, int k)
        {
            if (s_watching && s_last[c] != Unset && s_last[c] != k) s_moved[c] = true;
            s_last[c] = k;
            s_eff[c] = k;
        }

        static IEnumerable<KeyCode> KeyCandidates(int slot)
        {
            foreach (var k in KeyLists[slot]) yield return k;
            foreach (var k in KeyExtras) yield return k;
        }

        /// <summary>Keys the game (or the mod) reads on some keyboard, whatever the ghost keys are.</summary>
        static HashSet<int> KeyTakenBase()
        {
            var t = new HashSet<int>();
            foreach (var k in KeyAlways) t.Add((int)k);
            int online = CompatOnline.MenuKey;                  // Crawl Online's menu key (F1), when it is installed
            if (online > 0) t.Add(online);
            if (Binding((int)eController.Keyboard1) == null) foreach (var k in KeyDefaults) t.Add((int)k);
            for (int c = (int)eController.Keyboard1; c <= (int)eController.Keyboard4; c++)
            {
                var b = Binding(c);
                if (b != null) foreach (var v in b) if (v != None) t.Add(v);
            }
            return t;
        }

        /// <summary>A keyboard someone plays on (a human player has it) or has set up (it has bound keys).</summary>
        static bool KeyboardInUse(int cid)
        {
            if (Binding(cid) != null) return true;
            try
            {
                foreach (var pd in SystemPlayers.GetPlayers())
                    if (pd != null && pd.IsHuman && (int)pd.ControllerId == cid) return true;
            }
            catch { }
            return false;
        }

        /// <summary>The InControl controls the game reads on this pad (as InputControlType ints).</summary>
        static HashSet<int> PadTaken(int cid)
        {
            var t = new HashSet<int>();
            foreach (var s in PadSystem) t.Add((int)s);
            var b = Binding(cid);
            if (b != null)
            {
                foreach (var v in b) if (v != None && v != 0) t.Add(Mathf.Abs(v) - 1);
            }
            else
            {
                t.Add((int)InputControlType.Action1);
                t.Add((int)InputControlType.Action2);
                foreach (var x in PadGroups[0]) t.Add((int)x);
                foreach (var x in PadGroups[2]) t.Add((int)x);
                var dev = Device(cid);
                // pause: Command when the pad has one, else Y (SystemInput.UpdateInput)
                if (dev == null || dev.GetControl(InputControlType.Command) == InputControl.Null) t.Add((int)InputControlType.Action4);
            }
            foreach (var g in PadGroups)
            {
                bool any = false;
                foreach (var x in g) if (t.Contains((int)x)) { any = true; break; }
                if (any) foreach (var x in g) t.Add((int)x);
            }
            return t;
        }

        // ------------------------------------------------------------------ the game's input state
        static FieldInfo s_fInputs, s_fBinding, s_fArray;

        /// <summary>The controller's rebound inputs (SystemInput ControllerInput.m_controllerBinding.m_binding), or null
        /// when it uses the game's defaults.</summary>
        public static int[] Binding(int cid)
        {
            try
            {
                if (!Singleton<SystemInput>.HasInstance()) return null;
                var si = Singleton<SystemInput>.Get;
                if (s_fInputs == null) s_fInputs = R.F(typeof(SystemInput), "m_controllerInput");
                var arr = s_fInputs.GetValue(si) as Array;
                if (arr == null || cid < 0 || cid >= arr.Length) return null;
                var ci = arr.GetValue(cid);
                if (ci == null) return null;
                if (s_fBinding == null) s_fBinding = R.F(ci.GetType(), "m_controllerBinding");
                var cb = s_fBinding.GetValue(ci);
                if (cb == null) return null;
                if (s_fArray == null) s_fArray = R.F(cb.GetType(), "m_binding");
                return s_fArray.GetValue(cb) as int[];
            }
            catch { return null; }
        }

        /// <summary>The InControl device of pad slot cid (0-3), or null.</summary>
        public static InputDevice Device(int cid)
        {
            try
            {
                var devs = InputManager.Devices;
                if (!IsPad(cid) || devs == null || cid >= devs.Count) return null;
                return devs[cid];
            }
            catch { return null; }
        }

        static string DeviceName(int cid) { var d = Device(cid); return d != null ? d.Meta : null; }

        /// <summary>Vanilla's GetInputBindWasPressed for a code (InputControlType + 1, negative: the negative direction).</summary>
        public static bool PadWasPressed(InputDevice dev, int code)
        {
            var c = dev.GetControl((InputControlType)(Mathf.Abs(code) - 1));
            if (c == null || c == InputControl.Null) return false;
            return code < 0 ? c.LastValue > -PressAt && c.Value <= -PressAt : c.LastValue < PressAt && c.Value >= PressAt;
        }

        /// <summary>The control is held past the press threshold.</summary>
        public static bool PadIsHeld(InputDevice dev, int code)
        {
            var c = dev.GetControl((InputControlType)(Mathf.Abs(code) - 1));
            if (c == null || c == InputControl.Null) return false;
            return code < 0 ? c.Value <= -PressAt : c.Value >= PressAt;
        }

        /// <summary>A key's name in plain words ("full stop", "num 4"): the HUD fonts have no symbols.</summary>
        public static string KeyName(KeyCode k)
        {
            switch (k)
            {
                case KeyCode.Comma: return "comma";
                case KeyCode.Period: return "full stop";
                case KeyCode.Slash: return "slash";
                case KeyCode.Backslash: return "backslash";
                case KeyCode.Semicolon: return "semicolon";
                case KeyCode.Quote: return "quote";
                case KeyCode.BackQuote: return "backquote";
                case KeyCode.LeftBracket: return "left bracket";
                case KeyCode.RightBracket: return "right bracket";
                case KeyCode.Minus: return "minus";
                case KeyCode.Equals: return "equals";
                case KeyCode.Space: return "space";
                case KeyCode.Return: return "enter";
                case KeyCode.KeypadEnter: return "num enter";
                case KeyCode.KeypadPeriod: return "num point";
                case KeyCode.KeypadDivide: return "num slash";
                case KeyCode.KeypadMultiply: return "num times";
                case KeyCode.KeypadMinus: return "num minus";
                case KeyCode.KeypadPlus: return "num plus";
                case KeyCode.KeypadEquals: return "num equals";
                case KeyCode.LeftControl: return "left ctrl";
                case KeyCode.RightControl: return "right ctrl";
                case KeyCode.None: return "none";
            }
            int v = (int)k;
            if (v >= (int)KeyCode.Alpha0 && v <= (int)KeyCode.Alpha9) return ((char)('0' + v - (int)KeyCode.Alpha0)).ToString();
            if (v >= (int)KeyCode.Keypad0 && v <= (int)KeyCode.Keypad9) return "num " + (v - (int)KeyCode.Keypad0);
            if (v >= (int)KeyCode.A && v <= (int)KeyCode.Z) return ((char)('A' + v - (int)KeyCode.A)).ToString();
            string s = k.ToString();
            if (s.Length >= 2 && s[0] == 'F' && char.IsDigit(s[1])) return s;    // F1..F15
            return Words(s);
        }

        /// <summary>A pad control's name ("RB", "d-pad left") for a code (InputControlType + 1, negative: the negative direction).</summary>
        public static string PadName(int code)
        {
            var t = (InputControlType)(Mathf.Abs(code) - 1);
            bool neg = code < 0;
            switch (t)
            {
                case InputControlType.Action1: return "A";
                case InputControlType.Action2: return "B";
                case InputControlType.Action3: return "X";
                case InputControlType.Action4: return "Y";
                case InputControlType.LeftBumper: return "LB";
                case InputControlType.RightBumper: return "RB";
                case InputControlType.LeftTrigger: return "LT";
                case InputControlType.RightTrigger: return "RT";
                case InputControlType.LeftStickButton: return "L3";
                case InputControlType.RightStickButton: return "R3";
                case InputControlType.RightStickUp: return "right stick up";
                case InputControlType.RightStickDown: return "right stick down";
                case InputControlType.RightStickLeft: return "right stick left";
                case InputControlType.RightStickRight: return "right stick right";
                case InputControlType.RightStickX: return neg ? "right stick left" : "right stick right";
                case InputControlType.RightStickY: return neg ? "right stick down" : "right stick up";
                case InputControlType.LeftStickX: return neg ? "left stick left" : "left stick right";
                case InputControlType.LeftStickY: return neg ? "left stick down" : "left stick up";
                case InputControlType.DPadX: return neg ? "d-pad left" : "d-pad right";
                case InputControlType.DPadY: return neg ? "d-pad down" : "d-pad up";
                case InputControlType.DPadUp: return "d-pad up";
                case InputControlType.DPadDown: return "d-pad down";
                case InputControlType.DPadLeft: return "d-pad left";
                case InputControlType.DPadRight: return "d-pad right";
            }
            string s = Words(t.ToString());
            return neg ? s + " minus" : s;
        }

        /// <summary>"LeftShift" to "left shift", "Button12" to "button 12".</summary>
        static string Words(string s)
        {
            var sb = new StringBuilder();
            for (int i = 0; i < s.Length; i++)
            {
                char c = s[i];
                bool brk = i > 0 && ((char.IsUpper(c) && !char.IsUpper(s[i - 1])) || (char.IsDigit(c) && !char.IsDigit(s[i - 1])));
                if (brk) sb.Append(' ');
                sb.Append(char.ToLowerInvariant(c));
            }
            return sb.ToString();
        }

        // ------------------------------------------------------------------ persistence (plain "key = value" lines)
        static string[] Slots = { "Pad1", "Pad2", "Pad3", "Pad4", "Keyboard1", "Keyboard2", "Keyboard3", "Keyboard4" };

        /// <summary>Read the settings file (once).</summary>
        public static void Load()
        {
            if (s_loaded) return;
            s_loaded = true;
            try
            {
                if (!System.IO.File.Exists(Path)) return;
                foreach (var raw in System.IO.File.ReadAllLines(Path))
                {
                    var line = raw.Trim();
                    if (line.Length == 0 || line[0] == '#' || line[0] == '[') continue;
                    int eq = line.IndexOf('=');
                    if (eq <= 0) continue;
                    string k = line.Substring(0, eq).Trim(), v = line.Substring(eq + 1).Trim();
                    for (int c = 0; c < Slots.Length; c++)
                    {
                        if (k == Slots[c] + "Device" && c < 4) s_padDevice[c] = v.Length > 0 ? v : null;
                        if (k != Slots[c] || v.Length == 0 || v == "auto") continue;
                        s_choice[c] = c < 4 ? ParsePad(v) : ParseKey(v);
                    }
                }
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost controls: could not read " + FILE + ": " + e.Message); }
        }

        static int ParseKey(string v)
        {
            try { var k = (KeyCode)Enum.Parse(typeof(KeyCode), v, true); return (int)k > 0 && (int)k < KeyLimit ? (int)k : None; }
            catch { return None; }
        }

        static int ParsePad(string v)
        {
            bool neg = v.StartsWith("-", StringComparison.Ordinal);
            try { var t = (InputControlType)Enum.Parse(typeof(InputControlType), neg ? v.Substring(1) : v, true); return t == InputControlType.None ? None : (neg ? -((int)t + 1) : (int)t + 1); }
            catch { return None; }
        }

        static void Save()
        {
            try
            {
                var sb = new StringBuilder();
                sb.AppendLine("# The ghost button (Crawl Further Core). Written by the mod.");
                sb.AppendLine("# Set it in the game: Options, Keyboards (keyboards) or a player's Controls on the join screen.");
                sb.AppendLine("# auto = the first free one of the defaults: keyboard 1 C or V, 2 B or N, 3 M or Comma, 4 Period");
                sb.AppendLine("# or Slash; pads X, RB or LB. The mouse always uses the middle click. Delete the file to reset.");
                sb.AppendLine("[GhostButton]");
                for (int c = 0; c < Slots.Length; c++)
                {
                    int v = s_choice[c];
                    string s = v == None ? "auto" : c < 4 ? (v < 0 ? "-" : "") + ((InputControlType)(Mathf.Abs(v) - 1)) : ((KeyCode)v).ToString();
                    sb.AppendLine(Slots[c] + " = " + s);
                    if (c < 4) sb.AppendLine(Slots[c] + "Device = " + (v == None ? "" : s_padDevice[c] ?? ""));
                }
                System.IO.File.WriteAllText(Path, sb.ToString());
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost controls: could not write " + FILE + ": " + e.Message); }
        }

        static float s_lastWarn = -100f;
        static void Warn(string where, Exception e)
        {
            if (Time.realtimeSinceStartup - s_lastWarn < 10f) return;
            s_lastWarn = Time.realtimeSinceStartup;
            FurtherCore.Log.LogWarning("Ghost controls (" + where + "): " + e.Message);
        }

        /// <summary>Self-test: button names fit the HUD fonts, fallback lists don't clash, every controller gets a button.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            const string banned = "%{|}~[]#";
            var names = new List<string> { AnyName, NameOf((int)eController.Mouse) };
            foreach (var l in KeyLists) foreach (var k in l) names.Add(KeyName(k));
            foreach (var k in KeyExtras) names.Add(KeyName(k));
            foreach (KeyCode k in Enum.GetValues(typeof(KeyCode))) if ((int)k > 0 && (int)k < KeyLimit) names.Add(KeyName(k));
            foreach (InputControlType t in Enum.GetValues(typeof(InputControlType)))
                if (t != InputControlType.None && t != InputControlType.Count) { names.Add(PadName((int)t + 1)); names.Add(PadName(-((int)t + 1))); }
            foreach (var n in names)
            {
                if (string.IsNullOrEmpty(n)) { bad("ghost controls: an empty button name"); continue; }
                foreach (var ch in n) if (banned.IndexOf(ch) >= 0 || ch < 32 || ch > 126) { bad("ghost controls: name '" + n + "' has a character the HUD fonts lack"); break; }
            }
            if (KeyName(KeyCode.Period) != "full stop" || KeyName(KeyCode.C) != "C" || PadName((int)InputControlType.RightBumper + 1) != "RB")
                bad("ghost controls: key names changed");
            // the fallback lists never share a key, and none of them is a key the game always reads
            var seen = new HashSet<KeyCode>();
            foreach (var l in KeyLists) foreach (var k in l) if (!seen.Add(k)) bad("ghost controls: " + k + " is in two fallback lists");
            foreach (var k in KeyExtras) if (!seen.Add(k)) bad("ghost controls: extra " + k + " repeats");
            foreach (var k in KeyAlways) if (seen.Contains(k)) bad("ghost controls: " + k + " is always taken but is a fallback");
            foreach (var k in KeyDefaults) if (seen.Contains(k)) bad("ghost controls: " + k + " is a vanilla key but is a fallback");
            // wording
            string p = Personalise("Press the <color=#fff>ghost button</color> to fuse.", "C");
            if (p != "Press the <color=#fff>ghost button</color> (C) to fuse.") bad("ghost controls: Personalise gave '" + p + "'");
            if (Personalise("As a monster, ghost button: jump out", "C") != "As a monster, ghost button (C): jump out") bad("ghost controls: Personalise skipped 'ghost button:'");
            if (Personalise("C, middle click or X: fuse two blobs", "RB") != "RB: fuse two blobs") bad("ghost controls: Personalise kept the fixed names");
            if (Personalise("the ghost button (X) again", "C") != "the ghost button (X) again") bad("ghost controls: Personalise named twice");
            // a resolve with whatever is connected must give every keyboard and pad a button
            Changed();
            for (int c = 0; c < 8; c++)
                if (NameOf(c) == "none") bad("ghost controls: controller " + (eController)c + " has no free ghost button");
            for (int a = (int)eController.Keyboard1; a <= (int)eController.Keyboard4; a++)
                for (int b = a + 1; b <= (int)eController.Keyboard4; b++)
                    if (s_eff[a] != None && s_eff[a] == s_eff[b]) bad("ghost controls: keyboards " + (a - 3) + " and " + (b - 3) + " share " + KeyName((KeyCode)s_eff[a]));
            for (int c = (int)eController.Keyboard1; c <= (int)eController.Keyboard4; c++)
                if (s_eff[c] != None && KeyTakenBase().Contains(s_eff[c])) bad("ghost controls: keyboard " + (c - 3) + " ghost key is a game key");
        }
    }
}
