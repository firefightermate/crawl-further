using System;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;

    /// <summary>
    /// The unlock announcement: a silver or gold banner slides in at the top of the next menu screen (god select or the
    /// evolve screen, whichever menu camera comes up first) with the slot's name, holds 3.5 s and slides out. One at a
    /// time if several unlocked together. Also drives Unlocks.Tick (batched saves).
    /// </summary>
    public class UnlockToast : MonoBehaviour
    {
        static UnlockToast s_inst;
        GameObject m_root;
        exSpriteAnimation m_anim;
        TextMesh m_text, m_sub;
        UnlockDef m_cur;
        float m_t;
        Camera m_cam;
        const float Hold = 3.6f, Slide = 0.18f;
        /// <summary>The banner's inside (128 px with its frame and end caps), one unit per pixel.</summary>
        const float TextRoom = 112f;

        public static void Ensure()
        {
            if (s_inst != null) return;
            var go = new GameObject("CrawlFurther.Unlocks");
            DontDestroyOnLoad(go);
            s_inst = go.AddComponent<UnlockToast>();
            Unlocks.Load();
        }

        float m_nextLook;
        int m_fails;
        const float LookEvery = 0.25f;   // looking for a menu camera allocates (Camera.allCameras): a few times a second

        void Update()
        {
            Unlocks.Tick();
            if (m_cur == null)
            {
                if (Unlocks.Announce.Count == 0 || Time.unscaledTime < m_nextLook) return;
                m_nextLook = Time.unscaledTime + LookEvery;
                var cam = MenuCamera();
                if (cam == null) return;
                var next = Unlocks.Announce.Peek();
                m_t = 0f;
                if (!Build(cam, next))
                {
                    // stays queued and is tried again on a later look; a banner that can never be built is dropped
                    if (++m_fails >= 3) { Unlocks.Announce.Dequeue(); m_fails = 0; }
                    return;
                }
                m_fails = 0;
                m_cur = Unlocks.Announce.Dequeue();
            }
            if (m_root == null || m_cam == null || !m_cam.isActiveAndEnabled)
            {
                // the menu went away under the banner: show the whole announcement again on the next menu
                Requeue(m_cur);
                Hide();
                return;
            }
            m_t += Time.unscaledDeltaTime;
            float k = m_t < Slide ? m_t / Slide : m_t > Hold - Slide ? Mathf.Max(0f, (Hold - m_t) / Slide) : 1f;
            Place(k);
            if (m_t >= Hold) Hide();
        }

        void OnApplicationQuit() { Unlocks.Save(); }

        /// <summary>Put an interrupted announcement back at the front of the queue.</summary>
        static void Requeue(UnlockDef c)
        {
            if (c == null) return;
            var rest = Unlocks.Announce.ToArray();
            Unlocks.Announce.Clear();
            Unlocks.Announce.Enqueue(c);
            foreach (var r in rest) if (r != c) Unlocks.Announce.Enqueue(r);
        }

        static Camera MenuCamera()
        {
            foreach (var c in Camera.allCameras)
                if (c != null && c.isActiveAndEnabled && c.orthographic && c.name == "CameraMenu") return c;
            return null;
        }

        static TextMesh FindFont(string want)
        {
            TextMesh any = null;
            foreach (var t in FindObjectsOfType<TextMesh>())
            {
                if (t.font == null) continue;
                if (t.font.name.Contains(want)) return t;
                if (any == null) any = t;
            }
            return any;
        }

        TextMesh MakeText(TextMesh src, string name, float y, Color col)
        {
            var go = new GameObject(name);
            go.layer = m_root.layer;
            go.transform.SetParent(m_root.transform, false);
            go.transform.localPosition = new Vector3(0f, y, -0.5f);
            var tm = go.AddComponent<TextMesh>();
            tm.font = src.font;
            tm.fontSize = src.fontSize;
            tm.characterSize = src.characterSize;
            tm.anchor = TextAnchor.MiddleCenter;
            tm.alignment = TextAlignment.Center;
            tm.color = col;
            go.GetComponent<MeshRenderer>().sharedMaterial = src.GetComponent<MeshRenderer>().sharedMaterial;
            return tm;
        }

        bool Build(Camera cam, UnlockDef c)
        {
            try
            {
                Hide();
                m_cam = cam;
                var cur = c;
                var sheet = SpriteSheets.Get("UnlockBanner");
                if (sheet == null) return false;
                string anim = cur.tier == SlotTier.Gold ? "Gold" : "Silver";
                m_root = new GameObject("ModUnlockBanner");
                m_root.layer = cam.gameObject.layer;
                m_root.transform.SetParent(cam.transform, false);
                m_root.AddComponent<MeshFilter>();
                m_root.AddComponent<MeshRenderer>();
                var spr = m_root.AddComponent<exSprite>();
                spr.anchor = exPlane.Anchor.MidCenter;
                var clip = new ClipBuilder(sheet, anim, "ModUnlockBanner" + anim).Loop().Build();
                spr.SetSprite(sheet.atlas, clip.frameInfos[0].index);
                m_root.GetComponent<Renderer>().sharedMaterial = sheet.atlas.material;
                m_anim = m_root.AddComponent<exSpriteAnimation>();
                m_anim.Play(clip);
                var big = FindFont("CrawlMedium");
                var small = FindFont("CrawlTextBodyThin") ?? big;
                if (big != null)
                {
                    Color col = cur.tier == SlotTier.Gold ? new Color(1f, 0.91f, 0.55f) : new Color(0.92f, 0.95f, 1f);
                    m_text = MakeText(big, "Title", 4.2f, col);
                    m_text.text = cur.slot + " UNLOCKED";
                    m_sub = MakeText(small, "Sub", -4.8f, new Color(0.83f, 0.75f, 0.61f));
                    m_sub.text = cur.text;
                    // both lines stay inside the banner's frame, whatever size the borrowed font style has
                    SlotArt.ShrinkToWidth(m_text, TextRoom);
                    SlotArt.ShrinkToWidth(m_sub, TextRoom);
                }
                Place(0f);
                return true;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Unlock banner: " + e.Message); Hide(); return false; }
        }

        void Place(float k)
        {
            if (m_root == null || m_cam == null) return;
            float top = m_cam.orthographicSize;
            // just under the top edge, in front of every menu sprite
            m_root.transform.localPosition = new Vector3(0f, top - 16f + (1f - k) * 30f, m_cam.nearClipPlane + 2f);
            m_root.transform.localScale = new Vector3(1f, Mathf.Max(0.05f, k), 1f);
        }

        /// <summary>Remove the banner (the announcement in hand, if any, is done with: callers re-queue it first).</summary>
        void Hide()
        {
            if (m_root != null) Destroy(m_root);
            m_root = null; m_anim = null; m_text = null; m_sub = null; m_cur = null;
        }
    }
}
