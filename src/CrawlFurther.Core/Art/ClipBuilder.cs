using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Art
{
    /// <summary>
    /// Builds an exSpriteAnimClip from a sheet animation plus events. Each event is pinned to a frame (the moment that
    /// frame starts, plus an optional offset in seconds), so retiming the frames never moves gameplay away from the art.
    /// <code>
    /// var bite = new ClipBuilder(sheet, "Bite", "MyBeastBite")
    ///     .Ev(2, "AnimAttack", 0)      // attack 0 lands as frame 2 appears
    ///     .Ev(-1, "AnimRun")           // negative frames count from the end: control returns on the last frame
    ///     .Build();
    /// </code>
    /// Monsters receive events through SendMessage: the game's Player handles AnimAttack(int index) and AnimRun(), among others.
    /// </summary>
    public class ClipBuilder
    {
        readonly SpriteSheet m_sheet;
        readonly string m_anim;
        readonly string m_name;
        WrapMode m_wrap = WrapMode.Once;
        float m_speed = 1f;
        float[] m_durations;
        int m_repeat = 1;
        bool m_handOff;
        static readonly HashSet<exSpriteAnimClip> s_handOffs = new HashSet<exSpriteAnimClip>();
        readonly List<KeyValuePair<string, int>> m_then = new List<KeyValuePair<string, int>>();
        readonly List<exSpriteAnimClip.EventInfo> m_events = new List<exSpriteAnimClip.EventInfo>();
        readonly List<KeyValuePair<int, float>> m_eventAnchors = new List<KeyValuePair<int, float>>();

        /// <summary>Start a clip named <paramref name="clipName"/> from animation <paramref name="anim"/> of <paramref name="sheet"/>.
        /// Animation components find clips by name, so make it unique.</summary>
        public ClipBuilder(SpriteSheet sheet, string anim, string clipName)
        {
            m_sheet = sheet; m_anim = anim; m_name = clipName;
        }

        /// <summary>
        /// The clip ends by handing the body to a behaviour (a charge, a carry, a dig) that gives control back itself, so it
        /// has no AnimRun of its own. The self-test accepts it; without this it reports the clip as never returning control.
        /// </summary>
        public ClipBuilder HandOff() { m_handOff = true; return this; }

        /// <summary>Was <paramref name="clip"/> built with <see cref="HandOff"/>?</summary>
        public static bool HandsOff(exSpriteAnimClip clip) { return clip != null && s_handOffs.Contains(clip); }

        /// <summary>Play the clip in a loop (idle, run). The default is once.</summary>
        public ClipBuilder Loop() { m_wrap = WrapMode.Loop; return this; }

        /// <summary>Play the clip once (attacks, deaths). This is the default.</summary>
        public ClipBuilder Once() { m_wrap = WrapMode.Once; return this; }

        /// <summary>Playback speed multiplier (1 = the frame durations as written).</summary>
        public ClipBuilder Speed(float s) { m_speed = s; return this; }

        /// <summary>Override the main animation's per-frame durations, in seconds.</summary>
        public ClipBuilder Durations(params float[] d) { m_durations = d; return this; }

        /// <summary>Repeat the main animation's frames <paramref name="n"/> times (a long-lived effect played once).</summary>
        public ClipBuilder Repeat(int n) { m_repeat = Mathf.Max(1, n); return this; }

        /// <summary>Append another animation of the same sheet, <paramref name="repeat"/> times, after the main one.</summary>
        public ClipBuilder Then(string anim, int repeat = 1) { m_then.Add(new KeyValuePair<string, int>(anim, Mathf.Max(1, repeat))); return this; }

        /// <summary>Frame count of the finished clip, for anchoring events relative to the end.</summary>
        public int FrameCount
        {
            get
            {
                var a = m_sheet == null ? null : m_sheet.Anim(m_anim);
                int n = a == null ? 0 : a.frames.Length * m_repeat;
                foreach (var kv in m_then) { var b = m_sheet.Anim(kv.Key); if (b != null) n += b.frames.Length * kv.Value; }
                return n;
            }
        }

        /// <summary>Send <paramref name="method"/>() when <paramref name="frame"/> starts. A negative frame counts from the end
        /// (-1 = the last frame).</summary>
        public ClipBuilder Ev(int frame, string method) { return Add(frame, 0f, method, exSpriteAnimClip.EventInfo.ParamType.NONE); }

        /// <summary>Send <paramref name="method"/>(int) at <paramref name="frame"/> plus <paramref name="offset"/> seconds.</summary>
        public ClipBuilder Ev(int frame, string method, int p, float offset = 0f) { return Add(frame, offset, method, exSpriteAnimClip.EventInfo.ParamType.INT, i: p); }

        /// <summary>Send <paramref name="method"/>(float) at <paramref name="frame"/> plus <paramref name="offset"/> seconds.</summary>
        public ClipBuilder EvF(int frame, string method, float p, float offset = 0f) { return Add(frame, offset, method, exSpriteAnimClip.EventInfo.ParamType.FLOAT, f: p); }

        /// <summary>Send <paramref name="method"/>(string) at <paramref name="frame"/> plus <paramref name="offset"/> seconds.</summary>
        public ClipBuilder EvS(int frame, string method, string p, float offset = 0f) { return Add(frame, offset, method, exSpriteAnimClip.EventInfo.ParamType.STRING, s: p); }

        /// <summary>Send <paramref name="method"/>(Object) at <paramref name="frame"/> plus <paramref name="offset"/> seconds.
        /// A null object adds no event.</summary>
        public ClipBuilder EvO(int frame, string method, Object p, float offset = 0f)
        {
            // a null object parameter reaches SendMessage as "no parameter" and Unity logs an error
            if (p == null) return this;
            return Add(frame, offset, method, exSpriteAnimClip.EventInfo.ParamType.OBJECT, o: p);
        }

        /// <summary>Send <paramref name="method"/>(bool) at <paramref name="frame"/> plus <paramref name="offset"/> seconds.</summary>
        public ClipBuilder EvB(int frame, string method, bool p, float offset = 0f) { return Add(frame, offset, method, exSpriteAnimClip.EventInfo.ParamType.BOOL, b: p); }

        ClipBuilder Add(int frame, float offset, string method, exSpriteAnimClip.EventInfo.ParamType type,
                        int i = 0, float f = 0f, string s = "", Object o = null, bool b = false)
        {
            m_events.Add(new exSpriteAnimClip.EventInfo
            {
                methodName = method, paramType = type, intParam = i, floatParam = f, stringParam = s ?? "",
                objectParam = o, boolParam = b, msgOptions = SendMessageOptions.DontRequireReceiver
            });
            m_eventAnchors.Add(new KeyValuePair<int, float>(frame, offset));
            return this;
        }

        /// <summary>Make the clip (kept for the session). Returns null, with an error in the log, if the main animation is missing.</summary>
        public exSpriteAnimClip Build()
        {
            var a = m_sheet == null ? null : m_sheet.Anim(m_anim);
            if (a == null)
            {
                FurtherCore.Log.LogError("ClipBuilder: missing animation '" + m_anim + "' in sheet " + (m_sheet == null ? "null" : m_sheet.id));
                return null;
            }
            var c = ScriptableObject.CreateInstance<exSpriteAnimClip>();
            c.name = m_name;
            c.wrapMode = m_wrap;
            c.speed = m_speed;
            var segs = new List<KeyValuePair<SheetAnim, int>> { new KeyValuePair<SheetAnim, int>(a, m_repeat) };
            foreach (var kv in m_then)
            {
                var b = m_sheet.Anim(kv.Key);
                if (b == null) { FurtherCore.Log.LogError("ClipBuilder: missing animation '" + kv.Key + "' in sheet " + m_sheet.id); continue; }
                segs.Add(new KeyValuePair<SheetAnim, int>(b, kv.Value));
            }
            int n = 0;
            foreach (var sg in segs) n += sg.Key.frames.Length * sg.Value;
            var starts = new float[n + 1];
            float t = 0f;
            int k = 0;
            bool first = true;
            foreach (var sg in segs)
            {
                var sa = sg.Key;
                for (int r = 0; r < sg.Value; r++)
                    for (int j = 0; j < sa.frames.Length; j++)
                    {
                        float len = first && m_durations != null && j < m_durations.Length ? m_durations[j]
                                  : (sa.durations != null && j < sa.durations.Length ? sa.durations[j] : 0.1f);
                        c.frameInfos.Add(new exSpriteAnimClip.FrameInfo { atlas = m_sheet.atlas, index = sa.frames[j], length = len, textureGUID = "" });
                        starts[k++] = t;
                        t += len;
                    }
                first = false;
            }
            starts[n] = t;
            c.length = t;
            for (int e = 0; e < m_events.Count; e++)
            {
                int fr = m_eventAnchors[e].Key < 0 ? n + m_eventAnchors[e].Key : m_eventAnchors[e].Key;
                fr = Mathf.Clamp(fr, 0, n);
                m_events[e].time = Mathf.Clamp(starts[fr] + m_eventAnchors[e].Value, 0f, t);
            }
            m_events.Sort((x, y) => x.time.CompareTo(y.time));
            c.eventInfos = new List<exSpriteAnimClip.EventInfo>(m_events);
            if (m_handOff) s_handOffs.Add(c);
            SpriteSheets.Keep(c);
            return c;
        }
    }
}
