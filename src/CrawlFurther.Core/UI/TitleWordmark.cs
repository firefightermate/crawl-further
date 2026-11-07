using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;

    /// <summary>The animated wordmark (<see cref="BrandingDef.wordmark"/>). Title mode follows the title's CRAWL sprite
    /// frame by frame; static mode just idles (credits).</summary>
    public class TitleWordmark : MonoBehaviour
    {
        // the wordmark's centre relative to the Title transform (world units, Title sprite scale 1.25), measured on the
        // logo frames: high logo (frame 347) letters end at x 53.75, bottom y 5; low logo (378) bottom y -20, and
        // "insert coin" sits at y -26 .. -31 between x -29 and 25, so the low mark is lifted to clear it. Drawn for a
        // 76 x 28 wordmark cell that reads from the logo's bottom right.
        static readonly Vector3 HighPos = new Vector3(41f, 10f, -0.5f);
        static readonly Vector3 LowPos = new Vector3(42f, -12.5f, -0.5f);

        exSprite m_title;          // null in Static mode
        exSprite m_spr;
        Renderer m_r;
        SpriteSheet m_sheet;
        SheetAnim m_anim;
        int m_frame;
        float m_t;
        bool m_visible;
        Vector3 m_lastPos;

        // sparks drifting up off the letters
        const int Sparks = 4;
        exSprite[] m_sparks;
        float[] m_sparkAge;
        Vector3[] m_sparkVel;
        float m_nextSpark = 1.5f;

        internal static void AttachTitle(exSprite title)
        {
            if (title == null || title.GetComponentInChildren<TitleWordmark>() != null || Branding.Wordmark == null) return;
            var s = Branding.MakeSprite("ModWordmark", title.transform, Branding.Wordmark, HighPos);
            var m = s.gameObject.AddComponent<TitleWordmark>();
            m.Init(s, title);
            FurtherCore.Log.LogInfo("Branding: wordmark on the title logo");
        }

        internal static void AttachStatic(Transform parent, Vector3 localPos, float scale)
        {
            if (parent == null || parent.GetComponentInChildren<TitleWordmark>() != null || Branding.Wordmark == null) return;
            var s = Branding.MakeSprite("ModWordmark", parent, Branding.Wordmark, localPos);
            s.scale = new Vector2(scale, scale);
            var m = s.gameObject.AddComponent<TitleWordmark>();
            m.Init(s, null);
            m.Play("Idle");
        }

        void Init(exSprite s, exSprite title)
        {
            m_spr = s; m_r = s.GetComponent<Renderer>(); m_sheet = Branding.Wordmark; m_title = title;
            m_r.enabled = title == null;
            m_visible = title == null;
            var sp = Branding.Spark;
            if (sp != null)
            {
                m_sparks = new exSprite[Sparks]; m_sparkAge = new float[Sparks]; m_sparkVel = new Vector3[Sparks];
                for (int i = 0; i < Sparks; i++)
                {
                    m_sparks[i] = Branding.MakeSprite("ModWordmarkSpark", transform, sp, new Vector3(0f, 0f, -0.05f));
                    m_sparks[i].scale = s.scale;
                    m_sparks[i].GetComponent<Renderer>().enabled = false;
                    m_sparkAge[i] = -1f;
                }
            }
        }

        void Play(string anim)
        {
            var a = m_sheet.Anim(anim);
            if (a == null || a.frames == null || a.frames.Length == 0) return;
            if (m_anim == a) return;
            m_anim = a; m_frame = 0; m_t = 0f;
            m_spr.SetSprite(m_sheet.atlas, a.frames[0]);
        }

        float Dur(int i) { return m_anim.durations != null && i < m_anim.durations.Length ? Mathf.Max(0.02f, m_anim.durations[i]) : 0.1f; }

        enum Logo { None, High, Low, HighGlitch, LowGlitch }

        static Logo Classify(exSprite t)
        {
            if (t == null || t.atlas == null || t.atlas.name != "AtlasMenuMain") return Logo.None;
            int i = t.index;
            if (i >= 347 && i <= 361) return (i == 347 || i == 351 || i == 361) ? Logo.High : Logo.HighGlitch;
            if (i >= 378 && i <= 391) return (i == 378 || i == 379 || i == 391) ? Logo.Low : Logo.LowGlitch;
            return Logo.None;   // spawn-in, transitions, outro, Powerhoof splash
        }

        void LateUpdate()
        {
            float dt = Mathf.Min(Time.unscaledDeltaTime, 0.1f);
            if (m_title != null)
            {
                var tr = m_title.GetComponent<Renderer>();
                Logo l = (tr != null && tr.enabled && m_title.gameObject.activeInHierarchy) ? Classify(m_title) : Logo.None;
                bool show = l != Logo.None;
                if (show)
                {
                    var p = (l == Logo.Low || l == Logo.LowGlitch) ? LowPos : HighPos;
                    if (p != m_lastPos) { transform.localPosition = p; m_lastPos = p; }
                    if (!m_visible) { Play("In"); m_visible = true; }
                    else if (l == Logo.HighGlitch || l == Logo.LowGlitch) Play("Glitch");
                    else if (m_anim != null && m_anim.name == "Glitch") Play("Idle");
                }
                else if (m_visible)
                {
                    m_visible = false;
                    m_anim = null;
                }
                if (m_r.enabled != m_visible) m_r.enabled = m_visible;
                if (!m_visible) { HideSparks(); return; }
            }
            if (m_anim == null) Play("Idle");
            if (m_anim == null) return;
            m_t += dt;
            while (m_t >= Dur(m_frame))
            {
                m_t -= Dur(m_frame);
                m_frame++;
                if (m_frame >= m_anim.frames.Length)
                {
                    if (m_anim.name == "In") { Play("Idle"); break; }
                    m_frame = 0;
                }
                m_spr.SetSprite(m_sheet.atlas, m_anim.frames[m_frame]);
            }
            UpdateSparks(dt);
        }

        void HideSparks()
        {
            if (m_sparks == null) return;
            for (int i = 0; i < Sparks; i++) { m_sparkAge[i] = -1f; m_sparks[i].GetComponent<Renderer>().enabled = false; }
        }

        void UpdateSparks(float dt)
        {
            if (m_sparks == null) return;
            var sa = Branding.Spark.Anim("Rise");
            if (sa == null) return;
            float k = m_spr.scale.x;
            m_nextSpark -= dt;
            if (m_nextSpark <= 0f && m_anim != null && m_anim.name == "Idle")
            {
                m_nextSpark = UnityEngine.Random.Range(0.9f, 2.6f);
                for (int i = 0; i < Sparks; i++)
                {
                    if (m_sparkAge[i] >= 0f) continue;
                    m_sparkAge[i] = 0f;
                    // somewhere along the letters' tops (the word rises to the right)
                    float x = UnityEngine.Random.Range(-28f, 28f);
                    m_sparks[i].transform.localPosition = new Vector3(x * k, (x * 0.12f + 6f) * k, -0.05f);
                    m_sparkVel[i] = new Vector3(UnityEngine.Random.Range(-1.5f, 2.5f), UnityEngine.Random.Range(5f, 8f), 0f) * k;
                    m_sparks[i].GetComponent<Renderer>().enabled = true;
                    break;
                }
            }
            float life = 0f;
            foreach (var d in sa.durations) life += d;
            for (int i = 0; i < Sparks; i++)
            {
                if (m_sparkAge[i] < 0f) continue;
                m_sparkAge[i] += dt;
                if (m_sparkAge[i] >= life) { m_sparkAge[i] = -1f; m_sparks[i].GetComponent<Renderer>().enabled = false; continue; }
                m_sparks[i].transform.localPosition += m_sparkVel[i] * dt;
                float acc = 0f; int f = 0;
                for (; f < sa.frames.Length - 1; f++) { acc += sa.durations[f]; if (m_sparkAge[i] < acc) break; }
                if (m_sparks[i].index != sa.frames[f]) m_sparks[i].SetSprite(Branding.Spark.atlas, sa.frames[f]);
            }
        }
    }
}
