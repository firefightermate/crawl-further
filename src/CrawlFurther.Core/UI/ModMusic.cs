using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    /// <summary>
    /// Extra music: tracks mods add are rotated in with the game's own gameplay music. A mod adds a folder of .ogg / .wav
    /// files with <see cref="AddFolder"/>; every file in every added folder is loaded (kept compressed in memory) the
    /// first time the main menu opens.
    ///
    /// How Crawl plays music (decompiled): every track is an AudioCue (type Music) handed to SystemMain.PlayMusic or
    /// PlayMusicSynced. PlayMusic only restarts when the cue differs from the one playing; SystemAudio.PlayMusic fades the
    /// old track out and the new one in, PlayMusicSynced starts the new cue at the old one's position (used when the hero
    /// changes). The volume is cue volume x clip volume x the Music volume setting. Gameplay music is the floor's
    /// Environment.GetMusic() (or Constants.m_musicGame); title, boss lead-in, boss, level-10, win, lose and the tutorial
    /// have their own cues.
    ///
    /// Each track is wrapped in a copy of the vanilla cue it stands in for (same volume, filters and loop settings, so
    /// fades and transitions behave like vanilla). When the game asks for gameplay music (and title music, if switched on)
    /// a CustomMusicChance roll swaps in one of the tracks, never the same one twice in a row. The pick sticks for as long
    /// as the game keeps asking for that same cue, so a track is never restarted; boss, level-10, win, lose and story
    /// music are never replaced. Player settings: CrawlFurther.UI.cfg (CustomMusic, CustomMusicChance,
    /// CustomMusicOnTitle, CustomMusicVolume).
    /// </summary>
    public static class ModMusic
    {
        static readonly List<string> s_folders = new List<string>();

        /// <summary>Add every .ogg / .wav file in <paramref name="folder"/> to the tracks. Call it when your mod starts
        /// (before the main menu first opens).</summary>
        public static void AddFolder(string folder)
        {
            if (string.IsNullOrEmpty(folder)) return;
            foreach (var f in s_folders) if (string.Equals(f, folder, StringComparison.OrdinalIgnoreCase)) return;
            s_folders.Add(folder);
        }

        static readonly List<AudioClip> s_clips = new List<AudioClip>();
        static readonly Dictionary<AudioClip, AudioCue> s_cues = new Dictionary<AudioClip, AudioCue>();
        static readonly List<string> s_failed = new List<string>();
        static readonly HashSet<AudioCue> s_mine = new HashSet<AudioCue>();
        static HashSet<AudioCue> s_envMusic;
        static bool s_started;
        public static bool Loading { get; private set; }
        public static int Count { get { return s_clips.Count; } }
        static AudioCue s_lastRequest, s_lastChoice;
        static AudioClip s_lastTrack;
        // a pinned pick (ForceTrack): stays for the rest of this floor, until boss / level-10 / win / lose music
        static AudioCue s_pinned;
        static int s_pinnedFloor = int.MinValue;

        /// <summary>Start loading the tracks (once). Safe to call any time after the game has booted.</summary>
        public static void Begin()
        {
            if (s_started || !UiSettings.CustomMusic) return;
            s_started = true;
            try
            {
                var files = new List<string>();
                foreach (var dir in s_folders)
                {
                    if (!Directory.Exists(dir)) { FurtherCore.Log.LogInfo("Music: no music folder (" + dir + ")"); continue; }
                    foreach (var f in Directory.GetFiles(dir))
                    {
                        string ext = Path.GetExtension(f).ToLowerInvariant();
                        if (ext == ".ogg" || ext == ".wav") files.Add(f);
                    }
                }
                files.Sort(StringComparer.OrdinalIgnoreCase);
                if (files.Count == 0) { FurtherCore.Log.LogInfo("Music: no .ogg / .wav files to add"); return; }
                var go = new GameObject("CrawlMod_Music");
                UnityEngine.Object.DontDestroyOnLoad(go);
                go.AddComponent<Runner>().StartCoroutine(Load(files));
            }
            catch (Exception e) { FurtherCore.Log.LogError("Music: " + e); }
        }

        class Runner : MonoBehaviour { }

        static IEnumerator Load(List<string> files)
        {
            Loading = true;
            foreach (var f in files)
            {
                bool ogg = f.EndsWith(".ogg", StringComparison.OrdinalIgnoreCase);
                var www = new WWW("file:///" + f.Replace('\\', '/'));
                yield return www;
                AudioClip clip = null;
                try
                {
                    if (!string.IsNullOrEmpty(www.error)) throw new Exception(www.error);
                    // compressed in memory (Vorbis / ADPCM decoded while playing): a few MB per track, not 30+
                    clip = www.GetAudioClipCompressed(false, ogg ? AudioType.OGGVORBIS : AudioType.WAV);
                }
                catch (Exception e) { s_failed.Add(Path.GetFileName(f) + ": " + e.Message); }
                if (clip != null)
                {
                    float wait = 0f;
                    while (clip.loadState == AudioDataLoadState.Unloaded || clip.loadState == AudioDataLoadState.Loading)
                    {
                        if (clip.loadState == AudioDataLoadState.Unloaded) clip.LoadAudioData();
                        wait += Time.unscaledDeltaTime;
                        if (wait > 20f) break;
                        yield return null;
                    }
                    if (clip.loadState == AudioDataLoadState.Loaded && clip.length > 1f)
                    {
                        clip.name = "ModMusic_" + Path.GetFileNameWithoutExtension(f);
                        // an asset, not a scene object: DontDestroyOnLoad would only log "only work for root
                        // GameObjects" in Unity 5.4; this keeps it through scene loads and UnloadUnusedAssets
                        clip.hideFlags |= HideFlags.DontUnloadUnusedAsset;
                        s_clips.Add(clip);
                        FurtherCore.Log.LogInfo(string.Format("Music: loaded {0} ({1:0.0} s, {2} Hz, {3} ch)", Path.GetFileName(f), clip.length, clip.frequency, clip.channels));
                    }
                    else s_failed.Add(Path.GetFileName(f) + ": could not be decoded (" + clip.loadState + ")");
                }
                www.Dispose();
            }
            Loading = false;
            foreach (var x in s_failed) FurtherCore.Log.LogWarning("Music: " + x);
        }

        // ------------------------------------------------------------------ choosing
        static bool Eligible(AudioCue cue)
        {
            if (cue == null || s_mine.Contains(cue)) return false;
            var k = Singleton<Constants>.Get;
            if (k != null)
            {
                if (cue == k.m_musicTitle) return UiSettings.CustomMusicOnTitle;
                if (cue == k.m_musicGame) return true;
                if (cue == k.m_musicLevel10 || cue == k.m_musicBoss || cue == k.m_musicBossLeadIn || cue == k.m_musicWin || cue == k.m_musicLose) return false;
            }
            if (s_envMusic == null)
            {
                s_envMusic = new HashSet<AudioCue>();
                foreach (var env in Resources.FindObjectsOfTypeAll<Environment>())
                    if (env != null && env.GetMusic() != null) s_envMusic.Add(env.GetMusic());
            }
            if (s_envMusic.Contains(cue)) return true;
            try { var env = SystemGame.GetEnvironment(); if (env != null && env.GetMusic() == cue) { s_envMusic.Add(cue); return true; } } catch { }
            return false;
        }

        // ------------------------------------------------------------------ forcing a track (a jukebox)
        /// <summary>How many mod tracks can be forced (0 when CustomMusic is off or nothing loaded).</summary>
        public static int TrackCount { get { return UiSettings.CustomMusic ? s_clips.Count : 0; } }

        /// <summary>A track's title from its file name ("Further Down" for further_down.ogg); "" out of range.</summary>
        public static string TrackName(int i)
        {
            if (i < 0 || i >= TrackCount) return string.Empty;
            string n = s_clips[i].name;
            if (n.StartsWith("ModMusic_", StringComparison.Ordinal)) n = n.Substring(9);
            var parts = n.Replace('-', '_').Split('_');
            for (int k = 0; k < parts.Length; k++) if (parts[k].Length > 0) parts[k] = char.ToUpperInvariant(parts[k][0]) + parts[k].Substring(1);
            return string.Join(" ", parts).Trim();
        }

        /// <summary>Play mod track i now (cross-fading like vanilla) and keep it for the rest of this floor.
        /// Does nothing when CustomMusic is off. Boss, level-10, win and lose music still take over.</summary>
        public static void ForceTrack(int i)
        {
            if (i < 0 || i >= TrackCount) return;
            var template = FloorCue();
            if (template == null) return;
            var cue = CueFor(s_clips[i], template);
            if (cue == null) return;
            s_lastTrack = s_clips[i];
            Pin(cue, template);
        }

        /// <summary>Play a vanilla floor track now (an AudioCue, or its name, e.g. "MusicCrypt") and keep it for the rest
        /// of this floor. Works with CustomMusic off too.</summary>
        public static void ForceVanilla(object cueOrName)
        {
            var cue = cueOrName as AudioCue;
            if (cue == null && cueOrName is string)
                foreach (var c in VanillaFloorCues()) if (c != null && string.Equals(c.name, (string)cueOrName, StringComparison.OrdinalIgnoreCase)) { cue = c; break; }
            if (cue == null) return;
            Pin(cue, FloorCue() ?? cue);
        }

        /// <summary>Drop the pinned track; the next music request picks as usual.</summary>
        public static void ClearForce() { s_pinned = null; s_pinnedFloor = int.MinValue; s_lastRequest = null; s_lastChoice = null; }

        /// <summary>The vanilla floor tracks a jukebox can offer: every Environment's music plus the general game music.</summary>
        public static List<AudioCue> VanillaFloorCues()
        {
            var l = new List<AudioCue>();
            foreach (var env in Resources.FindObjectsOfTypeAll<Environment>())
                if (env != null && env.GetMusic() != null && !l.Contains(env.GetMusic())) l.Add(env.GetMusic());
            var k = Singleton<Constants>.Get;
            if (k != null && k.m_musicGame != null && !l.Contains(k.m_musicGame)) l.Add(k.m_musicGame);
            return l;
        }

        static int Floor() { try { return SystemGame.GetLevel(); } catch { return 0; } }

        /// <summary>The cue the game wants for this floor right now (what a pin stands in for).</summary>
        static AudioCue FloorCue()
        {
            if (s_lastRequest != null && Eligible(s_lastRequest)) return s_lastRequest;
            try { var env = SystemGame.GetEnvironment(); if (env != null && env.GetMusic() != null) return env.GetMusic(); } catch { }
            var k = Singleton<Constants>.Get;
            return k != null ? k.m_musicGame : null;
        }

        static void Pin(AudioCue cue, AudioCue request)
        {
            s_pinned = cue; s_pinnedFloor = Floor();
            s_lastRequest = request; s_lastChoice = cue;
            FurtherCore.Log.LogInfo("Music: jukebox pinned " + cue.name + " for floor " + s_pinnedFloor);
            // the request maps to the pinned cue (Map), and PlayMusic cross-fades because it differs from what plays
            SystemMain.PlayMusic(request, 1.5f);
        }

        /// <summary>SystemMain.PlayMusic / PlayMusicSynced prefix: the cue to actually play.</summary>
        internal static AudioCue Map(AudioCue cue)
        {
            if (cue == null) return cue;
            if (s_pinned != null)
            {
                // a pin holds while the game keeps asking for floor music on the same floor; anything else ends it
                if (Floor() == s_pinnedFloor && (cue == s_lastRequest || Eligible(cue))) { s_lastRequest = cue; s_lastChoice = s_pinned; return s_pinned; }
                ClearForce();
            }
            if (!UiSettings.CustomMusic) return cue;
            if (!s_started) Begin();
            if (cue == s_lastRequest && s_lastChoice != null) return s_lastChoice;   // same request: keep the same track
            s_lastRequest = cue;
            s_lastChoice = cue;
            if (s_clips.Count > 0 && Eligible(cue) && UnityEngine.Random.value < UiSettings.CustomMusicChance)
            {
                var pool = new List<AudioClip>(s_clips);
                if (pool.Count > 1 && s_lastTrack != null) pool.Remove(s_lastTrack);
                var clip = pool[UnityEngine.Random.Range(0, pool.Count)];
                var mine = CueFor(clip, cue);
                if (mine != null)
                {
                    s_lastChoice = mine; s_lastTrack = clip;
                    FurtherCore.Log.LogInfo("Music: playing " + clip.name + " in place of " + cue.name);
                }
            }
            return s_lastChoice;
        }

        /// <summary>A copy of the vanilla cue it replaces, playing the mod track (looped).</summary>
        static AudioCue CueFor(AudioClip clip, AudioCue template)
        {
            AudioCue cue;
            if (s_cues.TryGetValue(clip, out cue) && cue != null) return cue;
            try
            {
                var go = (GameObject)UnityEngine.Object.Instantiate(template.gameObject);
                go.name = clip.name;
                go.SetActive(false);
                UnityEngine.Object.DontDestroyOnLoad(go);
                cue = go.GetComponent<AudioCue>();
                var t = template.m_sounds != null && template.m_sounds.Count > 0 ? template.m_sounds[0] : null;
                float v = (t != null ? t.m_volume.Max : 1f) * Mathf.Clamp(UiSettings.CustomMusicVolume, 0f, 2f);
                cue.m_type = (int)AudioCue.eAudioType.Music;
                cue.m_chance = 1f;
                cue.m_alsoPlay = null;
                cue.m_sounds = new List<AudioCue.Clip>
                {
                    new AudioCue.Clip { m_sound = clip, m_weight = 100f, m_loop = true, m_volume = new MinMaxRange(v), m_pitch = new MinMaxRange(1f) }
                };
                cue.UpdateWeights();
                s_cues[clip] = cue;
                s_mine.Add(cue);
                return cue;
            }
            catch (Exception e) { FurtherCore.Log.LogError("Music cue: " + e); return null; }
        }

        public static void SelfCheck(Action<string> bad)
        {
            foreach (var f in s_failed) bad("music " + f);
            if (AccessTools.Method(typeof(SystemMain), "PlayMusic") == null) bad("SystemMain.PlayMusic not found");
            if (AccessTools.Method(typeof(SystemMain), "PlayMusicSynced") == null) bad("SystemMain.PlayMusicSynced not found");
        }
    }

    [HarmonyPatch(typeof(SystemMain), "PlayMusic")]
    static class Patch_ModMusicPlay
    {
        static void Prefix(ref AudioCue cue)
        {
            try { cue = ModMusic.Map(cue); } catch (Exception e) { FurtherCore.Log.LogWarning("Music: " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(SystemMain), "PlayMusicSynced")]
    static class Patch_ModMusicSynced
    {
        static void Prefix(ref AudioCue cue)
        {
            try { cue = ModMusic.Map(cue); } catch (Exception e) { FurtherCore.Log.LogWarning("Music: " + e.Message); }
        }
    }
}
