using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// The main menu's branding dressing (<see cref="BrandingDef"/>), nothing that changes how the menu works:
    ///  - two little markers (menuPip) burn either side of the selected main menu item;
    ///  - slow embers and dust motes (menuMote) drift up between the backdrop and the title on the title screen and main menu;
    ///  - the mod's name and version bottom right (a copy of the game's own unused BuildNumber text, same font and anchor).
    /// </summary>
    public class MenuRefresh : MonoBehaviour
    {
        static readonly HashSet<string> TitleStates = new HashSet<string> { "TitleIntro", "TitleLoop", "TitleLoad", "MenuIntro", "MenuLoop" };

        MenuStateMachine m_states;
        MenuTextMenu m_menu;
        SpriteSheet m_pipSheet, m_moteSheet;
        exSprite m_pipL, m_pipR;
        float m_pipT; int m_pipF;
        GameObject m_footer;

        const int MoteCount = 16;
        exSprite[] m_motes;
        Vector3[] m_moteVel;
        float[] m_moteT, m_motePhase;
        int[] m_moteAnim;
        /// <summary>The menuMote anims, small to large.</summary>
        public static readonly string[] MoteAnims = { "Dust1", "Dust2", "Dust3", "Ember1", "Ember2", "Ember3" };
        Camera m_cam;

        internal static void Attach(MenuMain main)
        {
            if (main == null || main.GetComponent<MenuRefresh>() != null) return;
            main.gameObject.AddComponent<MenuRefresh>().Init(main);
        }

        void Init(MenuMain main)
        {
            m_states = GetComponent<MenuStateMachine>();
            try { m_menu = R.Get<MenuTextMenu>(main, "m_menuMain"); } catch { }
            m_pipSheet = Branding.MenuPip;
            m_moteSheet = Branding.MenuMote;
            if (m_pipSheet != null && m_menu != null)
            {
                m_pipL = Branding.MakeSprite("ModPipL", transform, m_pipSheet, Vector3.zero);
                m_pipR = Branding.MakeSprite("ModPipR", transform, m_pipSheet, Vector3.zero);
                m_pipR.HFlip();
                Show(m_pipL, false); Show(m_pipR, false);
            }
            if (m_moteSheet != null)
            {
                m_motes = new exSprite[MoteCount]; m_moteVel = new Vector3[MoteCount]; m_moteT = new float[MoteCount];
                m_motePhase = new float[MoteCount]; m_moteAnim = new int[MoteCount];
                for (int i = 0; i < MoteCount; i++)
                {
                    m_motes[i] = Branding.MakeSprite("ModMote", transform, m_moteSheet, Vector3.zero);
                    Respawn(i, true);
                    Show(m_motes[i], false);
                }
            }
            // the version line: the game's own BuildNumber text (inactive in the shipped menu), copied and retexted
            var bn = transform.Find("BuildNumber");
            if (bn != null && Branding.HasVersionLine)
            {
                m_footer = (GameObject)Instantiate(bn.gameObject, bn.parent);
                m_footer.name = "ModVersion";
                var mb = m_footer.GetComponent<MenuBuildNumber>();
                if (mb != null) DestroyImmediate(mb);
                var tm = m_footer.GetComponent<TextMesh>();
                if (tm != null)
                {
                    tm.text = Branding.Versioned;
                    tm.color = new Color(0.47f, 0.36f, 0.22f, 1f);
                }
                m_footer.SetActive(false);
            }
            FurtherCore.Log.LogInfo("Menu refresh: pips " + (m_pipL != null) + ", motes " + (m_motes != null) + ", footer " + (m_footer != null));
        }

        static void Show(exSprite s, bool on)
        {
            if (s == null) return;
            var r = s.GetComponent<Renderer>();
            if (r != null && r.enabled != on) r.enabled = on;
        }

        void Respawn(int i, bool anywhere)
        {
            float halfH = 56.25f, halfW = 100f;
            if (m_cam != null) { halfH = m_cam.orthographicSize; halfW = halfH * m_cam.aspect; }
            bool ember = UnityEngine.Random.value < 0.4f;
            int size = UnityEngine.Random.value < 0.55f ? 1 : (UnityEngine.Random.value < 0.7f ? 2 : 3);
            m_moteAnim[i] = (ember ? 3 : 0) + size - 1;
            float y = anywhere ? UnityEngine.Random.Range(-halfH, halfH) : -halfH - 4f;
            // between the backdrop (z 75) and the leaves / title (z 10 / 0)
            m_motes[i].transform.localPosition = new Vector3(UnityEngine.Random.Range(-halfW, halfW), y, 40f);
            m_moteVel[i] = new Vector3(UnityEngine.Random.Range(-1.2f, 1.2f), UnityEngine.Random.Range(2.5f, ember ? 7f : 4.5f), 0f);
            m_motePhase[i] = UnityEngine.Random.Range(0f, 6.28f);
            m_moteT[i] = UnityEngine.Random.Range(0f, 1f);
            float k = size == 3 ? 1f : 1.25f;
            m_motes[i].scale = new Vector2(k, k);
        }

        void LateUpdate()
        {
            if (!UiSettings.MenuDressing) return;
            string st = m_states != null ? m_states.GetStateName() : "";
            bool title = TitleStates.Contains(st);
            float dt = Mathf.Min(Time.unscaledDeltaTime, 0.1f);
            if (m_footer != null && m_footer.activeSelf != title) m_footer.SetActive(title);
            UpdatePips(st == "MenuLoop" || st == "MenuIntro", dt);
            UpdateMotes(title, dt);
        }

        void UpdatePips(bool on, float dt)
        {
            if (m_pipL == null) return;
            MenuTextMenuItem item = null;
            if (on && m_menu != null && m_menu.gameObject.activeInHierarchy)
            {
                try
                {
                    var items = R.Get<List<MenuTextMenuItem>>(m_menu, "m_items");
                    int sel = m_menu.GetSelectedId();
                    if (items != null && sel >= 0 && sel < items.Count) item = items[sel];
                }
                catch { }
            }
            var r = item != null ? item.GetComponent<Renderer>() : null;
            if (r == null || !r.enabled || !item.gameObject.activeInHierarchy) { Show(m_pipL, false); Show(m_pipR, false); return; }
            var b = r.bounds;
            float z = item.transform.position.z - 0.3f;
            m_pipL.transform.position = new Vector3(Mathf.Round(b.min.x - 6f), b.center.y + 0.5f, z);
            m_pipR.transform.position = new Vector3(Mathf.Round(b.max.x + 6f), b.center.y + 0.5f, z);
            var a = m_pipSheet.Anim("Burn");
            if (a != null)
            {
                m_pipT += dt;
                float d = a.durations != null && a.durations.Length > 0 ? a.durations[0] : 0.12f;
                if (m_pipT >= d) { m_pipT -= d; m_pipF = (m_pipF + 1) % a.frames.Length; }
                if (m_pipL.index != a.frames[m_pipF]) m_pipL.SetSprite(m_pipSheet.atlas, a.frames[m_pipF]);
                int fr = a.frames[(m_pipF + 2) % a.frames.Length];   // out of step with the left one
                if (m_pipR.index != fr) m_pipR.SetSprite(m_pipSheet.atlas, fr);
            }
            Show(m_pipL, true); Show(m_pipR, true);
        }

        void UpdateMotes(bool on, float dt)
        {
            if (m_motes == null) return;
            if (m_cam == null) { var mc = FindObjectOfType<MenuCamera>(); if (mc != null) m_cam = mc.GetComponent<Camera>(); }
            float top = m_cam != null ? m_cam.orthographicSize + 4f : 60f;
            for (int i = 0; i < MoteCount; i++)
            {
                Show(m_motes[i], on);
                if (!on) continue;
                var p = m_motes[i].transform.localPosition;
                m_motePhase[i] += dt;
                p += m_moteVel[i] * dt + new Vector3(Mathf.Sin(m_motePhase[i] * 0.9f) * 1.5f * dt, 0f, 0f);
                m_motes[i].transform.localPosition = p;
                if (p.y > top) { Respawn(i, false); continue; }
                var a = m_moteSheet.Anim(MoteAnims[m_moteAnim[i]]);
                if (a == null) continue;
                m_moteT[i] += dt;
                float cycle = 0f; foreach (var d in a.durations) cycle += d;
                float t = m_moteT[i] % cycle; int f = 0; float acc = 0f;
                for (; f < a.frames.Length - 1; f++) { acc += a.durations[f]; if (t < acc) break; }
                if (m_motes[i].index != a.frames[f]) m_motes[i].SetSprite(m_moteSheet.atlas, a.frames[f]);
            }
        }
    }

    [HarmonyPatch(typeof(MenuMain), "Start")]
    static class Patch_MenuRefresh
    {
        static void Postfix(MenuMain __instance)
        {
            try { ModMusic.Begin(); } catch (Exception e) { FurtherCore.Log.LogError("Music: " + e); }
            if (!UiSettings.MenuDressing) return;
            try { MenuRefresh.Attach(__instance); }
            catch (Exception e) { FurtherCore.Log.LogError("Menu refresh: " + e); }
        }
    }
}
