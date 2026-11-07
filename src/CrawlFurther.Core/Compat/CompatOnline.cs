using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using HarmonyLib;
using InControl;
using UnityEngine;

namespace CrawlFurther.Compat
{
    using CrawlFurther.Art;
    using CrawlFurther.Ghosts;

    /// <summary>
    /// Online Crawl compatibility (BepInEx GUID crawl.online, CrawlOnline.dll). The host runs the game; every client
    /// mirrors the host's renderers, materials, textures, cameras and sounds and sends only its controllers' seven game
    /// inputs (Left Right Up Down Action Alt Start) plus Escape. Remote players are virtual InControl pads
    /// (CrawlOnline.Host.NetGamepad) in the host's pad slots 0-3.
    ///
    /// Everything here is reflection on CrawlOnline's members: no compile-time reference, nothing runs when it is not
    /// installed, and a lookup that fails turns only its own feature off (the self-test says which).
    /// <list type="bullet">
    /// <item>The ghost button online: a client sends its own ghost button (as set on that PC) as a Left and a Right press
    /// on the same frame, which a stick cannot do. The host takes that pair out of the NetGamepad before the game sees it
    /// and <see cref="Ghosts.GhostControls.Down"/> reports it for that player. A remote mouse player's middle click is
    /// the ghost button only (Escape pauses).</item>
    /// <item>Run-time art: meshes and textures a mod changes itself are pushed to the clients with
    /// <see cref="MeshChanged"/> and <see cref="TextureChanged"/> (CrawlOnline only watches ex2D meshes and the
    /// textures ColorSwapper writes). Naming rules: <see cref="OnlineNames"/>.</item>
    /// <item>Clients load "Mod_&lt;sheet&gt;" textures from their own art folder instead of asking the host for a PNG.</item>
    /// <item>Menus: a remote mouse pointer works in the slot editors; remote players' ghost button row is hidden (it is
    /// set on their own PC).</item>
    /// <item>Unlocks: while hosting with CrawlOnline's UnlockEverything on, slot unlocks are open too
    /// (<see cref="SessionUnlockAll"/>).</item>
    /// </list>
    /// </summary>
    public static class CompatOnline
    {
        /// <summary>CrawlOnline's plugin GUID (its Harmony id too).</summary>
        public const string Guid = "crawl.online";
        /// <summary>The CrawlOnline version this was written against.</summary>
        public const string TestedVersion = "0.4.1";

        static bool s_resolved;
        static Assembly s_asm;
        static readonly List<string> s_missing = new List<string>();

        // CrawlOnline.Online
        static Func<bool> s_isHost, s_isClient;
        static PropertyInfo p_host;
        // CrawlOnline.Client.LocalInput (+ Slot)
        static FieldInfo f_capturing, f_suppress, f_slots, f_changed, f_slEngaged, f_slButtons, f_slCounters;
        // CrawlOnline.Host.NetGamepad
        static Type t_netPad;
        static FieldInfo f_npCounters, f_npApplied;
        // texture / mesh pushes
        static MethodInfo m_texBump, m_texVersion, m_meshUpdated;
        static FieldInfo f_hsClients, f_hsCapture, f_scDefs, f_clDefs, f_csSent, f_clTexReq, f_clTexVer;
        static MethodInfo m_getTexId;
        // remote menu mouse
        static MethodInfo m_forPlayer, m_menuWorldPos;
        // unlocks
        static FieldInfo f_cfgUnlockAll;
        static string s_version;

        /// <summary>CrawlOnline is loaded.</summary>
        public static bool Present { get { Resolve(); return s_asm != null; } }
        public static string Version { get { Resolve(); return s_version; } }
        public static Type NetPadType { get { Resolve(); return t_netPad; } }

        /// <summary>This PC hosts / joined an online session.</summary>
        public static bool IsHost { get { Resolve(); try { return s_isHost != null && s_isHost(); } catch { return false; } } }
        public static bool IsClient { get { Resolve(); try { return s_isClient != null && s_isClient(); } catch { return false; } } }

        static void Resolve()
        {
            if (s_resolved) return;
            s_resolved = true;
            try
            {
                foreach (var a in AppDomain.CurrentDomain.GetAssemblies())
                {
                    Type t = null;
                    try { t = a.GetType("CrawlOnline.Online", false); } catch { }
                    if (t != null) { s_asm = a; break; }
                }
                if (s_asm == null) return;
                const BindingFlags S = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
                const BindingFlags I = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;

                var plugin = T("CrawlOnline.Plugin");
                if (plugin != null)
                {
                    var fv = plugin.GetField("Version", S);
                    try { s_version = fv != null ? fv.GetValue(null) as string : null; } catch { }
                    f_cfgUnlockAll = Fld(plugin, "CfgUnlockAll", S);
                }
                var online = T("CrawlOnline.Online");
                if (online != null)
                {
                    s_isHost = Getter(online, "IsHost");
                    s_isClient = Getter(online, "IsClient");
                    p_host = online.GetProperty("Host", S);
                    if (p_host == null) s_missing.Add("Online.Host");
                }
                var li = T("CrawlOnline.Client.LocalInput");
                if (li != null)
                {
                    f_capturing = Fld(li, "Capturing", S);
                    f_suppress = Fld(li, "Suppress", S);
                    f_slots = Fld(li, "Slots", S);
                    f_changed = Fld(li, "Changed", S);
                    var slot = li.GetNestedType("Slot", BindingFlags.Public | BindingFlags.NonPublic);
                    if (slot != null)
                    {
                        f_slEngaged = Fld(slot, "Engaged", I);
                        f_slButtons = Fld(slot, "Buttons", I);
                        f_slCounters = Fld(slot, "Counters", I);
                    }
                    else s_missing.Add("LocalInput.Slot");
                }
                t_netPad = T("CrawlOnline.Host.NetGamepad");
                if (t_netPad != null)
                {
                    f_npCounters = Fld(t_netPad, "m_counters", I);
                    f_npApplied = Fld(t_netPad, "m_applied", I);
                }
                var tv = T("CrawlOnline.Host.TextureVersions");
                if (tv != null)
                {
                    m_texBump = Mth(tv, "Bump", S, typeof(Texture));
                    m_texVersion = Mth(tv, "Get", S, typeof(Texture));
                }
                var sc = T("CrawlOnline.Host.SceneCapture");
                if (sc != null)
                {
                    m_meshUpdated = Mth(sc, "OnMeshUpdated", S, typeof(Mesh));
                    f_scDefs = Fld(sc, "Defs", I);
                }
                var hs = T("CrawlOnline.Host.HostSession");
                if (hs != null)
                {
                    f_hsClients = Fld(hs, "Clients", I);
                    f_hsCapture = Fld(hs, "Capture", I);
                    var cl = hs.GetNestedType("Client", BindingFlags.Public | BindingFlags.NonPublic);
                    if (cl != null)
                    {
                        f_clDefs = Fld(cl, "Defs", I);
                        f_clTexReq = Fld(cl, "TexRequests", I);
                        f_clTexVer = Fld(cl, "TexSentVersion", I);
                    }
                    else s_missing.Add("HostSession.Client");
                }
                var hd = T("CrawlOnline.Host.HostDefs");
                if (hd != null)
                {
                    m_getTexId = Mth(hd, "GetTextureId", I, typeof(Texture));
                    var cs = hd.GetNestedType("ClientState", BindingFlags.Public | BindingFlags.NonPublic);
                    if (cs != null) f_csSent = Fld(cs, "Sent", I);
                    else s_missing.Add("HostDefs.ClientState");
                }
                var rm = T("CrawlOnline.Host.RemoteMouse");
                if (rm != null)
                {
                    m_forPlayer = Mth(rm, "ForPlayer", S, typeof(int));
                    if (t_netPad != null) m_menuWorldPos = Mth(rm, "MenuWorldPos", S, t_netPad);
                }
                FurtherCore.Log.LogInfo("Crawl Online " + (s_version ?? "?") + " detected: online compatibility on" +
                                   (s_missing.Count > 0 ? " (missing: " + string.Join(", ", s_missing.ToArray()) + ")" : ""));
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Crawl Online compat: " + e.Message); }
        }

        static Type T(string name)
        {
            Type t = null;
            try { t = s_asm.GetType(name, false); } catch { }
            if (t == null) s_missing.Add(name);
            return t;
        }

        static FieldInfo Fld(Type t, string name, BindingFlags f)
        {
            var fi = t.GetField(name, f);
            if (fi == null) s_missing.Add(t.Name + "." + name);
            return fi;
        }

        static MethodInfo Mth(Type t, string name, BindingFlags f, params Type[] args)
        {
            MethodInfo mi = null;
            try { mi = t.GetMethod(name, f, null, args, null); } catch { }
            if (mi == null) s_missing.Add(t.Name + "." + name);
            return mi;
        }

        static Func<bool> Getter(Type t, string prop)
        {
            var p = t.GetProperty(prop, BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            var g = p != null ? p.GetGetMethod(true) : null;
            if (g == null) { s_missing.Add(t.Name + "." + prop); return null; }
            try { return (Func<bool>)Delegate.CreateDelegate(typeof(Func<bool>), g); }
            catch { return () => (bool)g.Invoke(null, null); }
        }

        static float s_lastWarn = -100f;
        static void Warn(string where, Exception e)
        {
            if (Time.realtimeSinceStartup - s_lastWarn < 10f) return;
            s_lastWarn = Time.realtimeSinceStartup;
            FurtherCore.Log.LogWarning("Crawl Online compat (" + where + "): " + e.Message);
        }

        // ---------------------------------------------------------------- remote pads
        /// <summary>This InControl device is a remote player's virtual pad (host side).</summary>
        public static bool IsNetPad(InputDevice dev)
        {
            return dev != null && NetPadType != null && NetPadType.IsInstanceOfType(dev);
        }

        /// <summary>The pad in controller slot cid (0..3) belongs to a remote player.</summary>
        public static bool IsRemotePad(int cid)
        {
            return GhostControls.IsPad(cid) && IsNetPad(GhostControls.Device(cid));
        }

        // device -> the frame its Left+Right pair arrived (cleared when taken)
        static readonly Dictionary<object, int> s_chord = new Dictionary<object, int>();

        /// <summary>Host: NetGamepad.Update prefix. A Left and a Right press waiting together is the client's ghost button:
        /// take both out (the game never sees them) and remember the press for GhostControls.Down.</summary>
        internal static void OnNetPadUpdate(object pad)
        {
            try
            {
                if (pad == null || f_npCounters == null || f_npApplied == null) return;
                var c = f_npCounters.GetValue(pad) as byte[];
                var a = f_npApplied.GetValue(pad) as byte[];
                if (c == null || a == null || c.Length < 2 || a.Length < 2) return;
                int l = (byte)(c[0] - a[0]), r = (byte)(c[1] - a[1]);
                if (l <= 0 || l >= 128 || r <= 0 || r >= 128) return;
                a[0]++; a[1]++;
                s_chord[pad] = Time.frameCount;
                if (s_chord.Count > 32) s_chord.Clear();
            }
            catch (Exception e) { Warn("pad update", e); }
        }

        /// <summary>Host: the remote player on this device pressed their ghost button this frame (or the last one, when the
        /// pad updated after the caller ran). Each press is reported once.</summary>
        public static bool GhostPressed(InputDevice dev)
        {
            int f;
            if (dev == null || !s_chord.TryGetValue(dev, out f)) return false;
            s_chord.Remove(dev);
            return Time.frameCount - f <= 1;
        }

        // ---------------------------------------------------------------- client input
        /// <summary>Client: after Crawl Online read this frame's input (SystemInput.UpdateInternal postfix, run after its
        /// own), send the local ghost button of every slot in use as a Left+Right pulse pair.</summary>
        internal static void ClientInject()
        {
            if (f_capturing == null || f_slots == null || f_slCounters == null || f_slEngaged == null) return;
            try
            {
                if (!(bool)f_capturing.GetValue(null)) return;
                bool suppress = f_suppress != null && (bool)f_suppress.GetValue(null);
                if (suppress) return;
                var slots = f_slots.GetValue(null) as Array;
                if (slots == null) return;
                bool changed = false;
                int n = Mathf.Min(8, slots.Length);
                for (int i = 0; i < n; i++)
                {
                    var slot = slots.GetValue(i);
                    if (slot == null || !(bool)f_slEngaged.GetValue(slot)) continue;
                    bool press = GhostControls.LocalDown(i);
                    if (i == (int)eController.Keyboard1)
                    {
                        // the mouse rides on keyboard 1's slot; its middle click is the ghost button, not Start
                        bool middle = Input.GetMouseButton(2) && !Input.GetKey(KeyCode.Return) && !Input.GetKey(KeyCode.KeypadEnter);
                        if (middle && f_slButtons != null)
                        {
                            int b = (int)f_slButtons.GetValue(slot);
                            if ((b & 0x40) != 0) { f_slButtons.SetValue(slot, b & ~0x40); changed = true; }
                        }
                        if (middle && Input.GetMouseButtonDown(2))
                        {
                            var cs = f_slCounters.GetValue(slot) as byte[];
                            if (cs != null && cs.Length > 6) cs[6]--;    // the Start press Crawl Online just counted
                            press = true;
                        }
                    }
                    if (!press) continue;
                    var cnt = f_slCounters.GetValue(slot) as byte[];
                    if (cnt == null || cnt.Length < 2) continue;
                    cnt[0]++; cnt[1]++;
                    changed = true;
                }
                if (changed && f_changed != null) f_changed.SetValue(null, true);
            }
            catch (Exception e) { Warn("client input", e); }
        }

        // ---------------------------------------------------------------- art pushes
        /// <summary>Host: a Mesh a mod edits by hand changed; clients get the new geometry (CrawlOnline only watches ex2D meshes).</summary>
        public static void MeshChanged(Mesh m)
        {
            if (m == null || m_meshUpdated == null || !IsHost) return;
            try { m_meshUpdated.Invoke(null, new object[] { m }); }
            catch (Exception e) { Warn("mesh", e); }
        }

        static readonly Dictionary<int, float> s_texAt = new Dictionary<int, float>();

        /// <summary>Host: a texture's pixels were rewritten (call after Apply). Every client that already shows it gets the
        /// new picture, at most once per <paramref name="minInterval"/> seconds of real time.</summary>
        public static void TextureChanged(Texture tex, float minInterval = 0f)
        {
            if (tex == null || m_texBump == null || !IsHost) return;
            try
            {
                int iid = tex.GetInstanceID();
                float now = Time.realtimeSinceStartup, at;
                if (minInterval > 0f && s_texAt.TryGetValue(iid, out at) && now - at < minInterval) return;
                if (s_texAt.Count > 256) s_texAt.Clear();
                s_texAt[iid] = now;
                m_texBump.Invoke(null, new object[] { tex });
                if (p_host == null || f_hsClients == null || f_hsCapture == null || f_scDefs == null || m_getTexId == null ||
                    f_clDefs == null || f_csSent == null || f_clTexReq == null || f_clTexVer == null || m_texVersion == null) return;
                var host = p_host.GetValue(null, null);
                var clients = host != null ? f_hsClients.GetValue(host) as Array : null;
                if (clients == null) return;
                object defs = null;
                int id = 0, ver = 0;
                foreach (var c in clients)
                {
                    if (c == null) continue;
                    if (defs == null)
                    {
                        var cap = f_hsCapture.GetValue(host);
                        defs = cap != null ? f_scDefs.GetValue(cap) : null;
                        if (defs == null) return;
                        id = (int)m_getTexId.Invoke(defs, new object[] { tex });
                        ver = (int)m_texVersion.Invoke(null, new object[] { tex });
                        if (id <= 0) return;
                    }
                    var cdefs = f_clDefs.GetValue(c);
                    var sent = cdefs != null ? f_csSent.GetValue(cdefs) as HashSet<int>[] : null;
                    if (sent == null || sent.Length < 3 || sent[2] == null || !sent[2].Contains(id)) continue;   // not shown yet
                    var req = f_clTexReq.GetValue(c) as List<int>;
                    var sv = f_clTexVer.GetValue(c) as Dictionary<int, int>;
                    if (req == null || sv == null) continue;
                    sv[id] = ver;
                    if (!req.Contains(id)) req.Add(id);
                }
            }
            catch (Exception e) { Warn("texture", e); }
        }

        // ---------------------------------------------------------------- client art
        static readonly Dictionary<string, Texture2D> s_art = new Dictionary<string, Texture2D>();

        /// <summary>Client: a sheet texture (<see cref="OnlineNames.SheetTexture"/>) the mirror could not find in memory,
        /// loaded from this PC's art folders (the same mod version gives the same picture), so the host need not encode
        /// and send it.</summary>
        internal static Texture LocalArt(string name, int w, int h)
        {
            string id = OnlineNames.SheetOf(name);
            if (id == null) return null;                              // composed textures are not files
            Texture2D t;
            if (s_art.TryGetValue(name, out t)) return t != null && t.width == w && t.height == h ? t : null;
            t = null;
            try
            {
                var png = SpriteSheets.PathOf(id + ".png");
                if (File.Exists(png))
                {
                    t = new Texture2D(2, 2, TextureFormat.ARGB32, false);
                    t.LoadImage(File.ReadAllBytes(png));
                    t.filterMode = FilterMode.Point;
                    t.wrapMode = TextureWrapMode.Clamp;
                    t.name = name;
                    t.hideFlags |= HideFlags.DontUnloadUnusedAsset;
                }
            }
            catch (Exception e) { Warn("art " + name, e); t = null; }
            s_art[name] = t;
            return t != null && t.width == w && t.height == h ? t : null;
        }

        // ---------------------------------------------------------------- menus
        /// <summary>Host: the remote player in this slot is pointing with their mouse; pos is in menu-camera world space
        /// (what SystemInput.GetMousePos gives for the local mouse).</summary>
        public static bool RemoteMenuMouse(int playerId, out Vector2 pos)
        {
            pos = Vector2.zero;
            if (m_forPlayer == null || m_menuWorldPos == null || !IsHost) return false;
            try
            {
                var g = m_forPlayer.Invoke(null, new object[] { playerId });
                if (g == null) return false;
                pos = (Vector2)m_menuWorldPos.Invoke(null, new[] { g });
                return true;
            }
            catch (Exception e) { Warn("menu mouse", e); return false; }
        }

        // ---------------------------------------------------------------- unlocks
        /// <summary>Hosting with CrawlOnline's UnlockEverything on (its default): slot unlocks are open for everyone in the
        /// session, as vanilla's unlocks are. Nothing is saved; offline progress is untouched.</summary>
        public static bool SessionUnlockAll
        {
            get
            {
                if (f_cfgUnlockAll == null || !IsHost) return false;
                try
                {
                    var e = f_cfgUnlockAll.GetValue(null) as BepInEx.Configuration.ConfigEntry<bool>;
                    return e != null && e.Value;
                }
                catch { return false; }
            }
        }

        /// <summary>The key that opens Crawl Online's own menu (F1 by default), or 0: no ghost key may take it.</summary>
        public static int MenuKey
        {
            get
            {
                Resolve();
                if (s_asm == null) return 0;
                try
                {
                    var plugin = s_asm.GetType("CrawlOnline.Plugin", false);
                    var f = plugin != null ? plugin.GetField("CfgOverlayKey", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic) : null;
                    var e = f != null ? f.GetValue(null) as BepInEx.Configuration.ConfigEntry<KeyCode> : null;
                    return e != null ? (int)e.Value : (int)KeyCode.F1;
                }
                catch { return (int)KeyCode.F1; }
            }
        }

        /// <summary>Self-test section: what was found, which features are off, and every method both mods patch.</summary>
        public static void SelfCheck(Action<string> bad, Action<string> note)
        {
            Resolve();
            if (s_asm == null) { note("Crawl Online not installed: nothing to check"); return; }
            note("Crawl Online " + (s_version ?? "?") + " found (" + s_asm.GetName().Name + ")");
            if (s_version != TestedVersion)
                note("  WARNING: written against Crawl Online " + TestedVersion + "; if online play misbehaves, check this section");
            if (s_missing.Count > 0)
                bad("Crawl Online members not found (the matching online feature is off): " + string.Join(", ", s_missing.ToArray()));
            if (t_netPad == null || f_npCounters == null || f_npApplied == null || f_slCounters == null)
                bad("online ghost button unavailable: remote players cannot use it");
            if (m_meshUpdated == null || m_texBump == null) bad("online art pushes unavailable: tip panels / Lights Out may look stale on clients");

            // patch overlap: every method both mods patch, and whose prefixes could skip it
            try
            {
                int shared = 0;
                foreach (var m in Harmony.GetAllPatchedMethods())
                {
                    var info = Harmony.GetPatchInfo(m);
                    if (info == null) continue;
                    bool ours = false, theirs = false;
                    foreach (var o in info.Owners) { if (FurtherCore.IsOurHarmonyId(o)) ours = true; else if (o == Guid) theirs = true; }
                    if (!(ours && theirs)) continue;
                    shared++;
                    string line = "  shared patch: " + m.DeclaringType.Name + "." + m.Name + "  ours " + Kinds(info, FurtherCore.IsOurHarmonyId) + ", theirs " + Kinds(info, o => o == Guid);
                    note(line);
                    FurtherCore.Log.LogInfo("Crawl Online compat:" + line);
                    foreach (var p in info.Prefixes)
                        if (FurtherCore.IsOurHarmonyId(p.owner) && p.PatchMethod.ReturnType == typeof(bool))
                            bad("our prefix " + p.PatchMethod.DeclaringType.Name + " can skip " + m.DeclaringType.Name + "." + m.Name + ", which Crawl Online also patches");
                }
                note("  " + shared + " method(s) patched by both mods");
                // our own online patches went in
                if (t_netPad != null && !PatchedBy(AccessTools.Method(t_netPad, "Update", new[] { typeof(ulong), typeof(float) }), FurtherCore.IsOurHarmonyId))
                    bad("the NetGamepad.Update hook is not in: remote ghost button off");
                if (!PatchedBy(AccessTools.Method(typeof(SystemInput), "UpdateInternal"), FurtherCore.IsOurHarmonyId))
                    bad("the SystemInput.UpdateInternal hook is not in: this PC cannot send its ghost button as a client");
            }
            catch (Exception e) { bad("patch overlap scan failed: " + e.Message); }

            try
            {
                var asmName = s_asm.GetName().Name;
                if (asmName != "CrawlOnline") note("  note: assembly is named " + asmName + " (expected CrawlOnline)");
            }
            catch { }
            note("  online now: " + (IsHost ? "hosting" : IsClient ? "client" : "not in a session") + "; unlock-all while hosting: " + SessionUnlockAll);
        }

        static bool PatchedBy(MethodBase m, Func<string, bool> owner)
        {
            if (m == null) return false;
            var info = Harmony.GetPatchInfo(m);
            if (info == null) return false;
            foreach (var o in info.Owners) if (owner(o)) return true;
            return false;
        }

        static string Kinds(Patches info, Func<string, bool> owner)
        {
            var k = new List<string>();
            foreach (var p in info.Prefixes) if (owner(p.owner)) { k.Add("prefix"); break; }
            foreach (var p in info.Postfixes) if (owner(p.owner)) { k.Add("postfix"); break; }
            foreach (var p in info.Transpilers) if (owner(p.owner)) { k.Add("transpiler"); break; }
            return k.Count > 0 ? string.Join("+", k.ToArray()) : "-";
        }
    }

    /// <summary>Host: a remote pad's Left+Right pair is its player's ghost button (see CompatOnline).</summary>
    [HarmonyPatch]
    static class Patch_OnlineNetPadUpdate
    {
        static bool Prepare() { return CompatOnline.NetPadType != null; }
        static MethodBase TargetMethod() { return AccessTools.Method(CompatOnline.NetPadType, "Update", new[] { typeof(ulong), typeof(float) }); }
        static void Prefix(object __instance) { CompatOnline.OnNetPadUpdate(__instance); }
    }

    /// <summary>Client: after Crawl Online captured this frame's input, add the local ghost button.</summary>
    [HarmonyPatch(typeof(SystemInput), "UpdateInternal")]
    [HarmonyAfter(CompatOnline.Guid)]
    static class Patch_OnlineClientInput
    {
        static bool Prepare() { return CompatOnline.Present; }
        static void Postfix() { CompatOnline.ClientInject(); }
    }

    /// <summary>Client: our sheets come from this PC's own art folder (no PNG from the host, no host hitch).</summary>
    [HarmonyPatch]
    static class Patch_OnlineAssetIndex
    {
        static MethodBase s_target;
        static bool Prepare()
        {
            if (!CompatOnline.Present) return false;
            var t = AccessTools.TypeByName("CrawlOnline.Client.AssetIndex");
            s_target = t != null ? AccessTools.Method(t, "FindTexture", new[] { typeof(string), typeof(int), typeof(int) }) : null;
            return s_target != null;
        }
        static MethodBase TargetMethod() { return s_target; }
        static void Postfix(string name, int w, int h, ref Texture __result)
        {
            if (__result != null) return;
            try { __result = CompatOnline.LocalArt(name, w, h); } catch { }
        }
    }
}
