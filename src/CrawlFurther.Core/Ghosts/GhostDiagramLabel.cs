using System;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Ghosts
{
    using CrawlFurther.Gods;
    using CrawlFurther.Util;

    /// <summary>
    /// The join screen's controls picture (MenuJoinPlayer, state "InputDiagram": one picture each for keyboard, mouse and
    /// pad, drawn into the art) gets one more line under it for the ghost button, which the picture cannot show:
    /// "Ghost power, blob special: C" with the player's own key, middle click or pad button (GhostControls.Name, so it
    /// follows a changed binding; an Online Crawl player's reads "C, middle click or X"). It is a copy of the god page's
    /// own label text (fonts a translation mod swaps come along), a child of the picture so it shows and hides with it,
    /// and shrunk to the picture's width when it is wider. The pause menu has no controls picture.
    /// </summary>
    [HarmonyPatch(typeof(MenuJoinPlayer), "OnEnterState")]
    static class Patch_GhostDiagramLabel
    {
        /// <summary>The line's words after the button's name.</summary>
        public const string Label = "Ghost power, blob special";
        const string Name = "ModGhostButtonLine";

        static void Postfix(MenuJoinPlayer __instance)
        {
            try
            {
                var states = R.Get<MenuStateMachine>(__instance, "m_states");
                var diagram = R.Get<exSpriteAnimation>(__instance, "m_inputDiagram");
                if (states == null || diagram == null) return;
                var line = diagram.transform.Find(Name);
                bool show = states.GetStateName() == "InputDiagram" && !SystemInput.GetCabinetMode();
                var pd = R.Get<PlayerData>(__instance, "m_data");
                if (!show || pd == null || pd.IsBot)
                {
                    if (line != null) line.gameObject.SetActive(false);
                    return;
                }
                var tm = line != null ? line.GetComponent<TextMesh>() : Make(__instance, diagram);
                if (tm == null) return;
                tm.gameObject.SetActive(true);
                Place(tm, diagram);
                var r = diagram.GetComponent<Renderer>();
                float width = r != null && r.bounds.size.x > 1f ? r.bounds.size.x + 6f : 46f;
                SlotArt.FitName(tm, Label + ": " + GhostControls.Name(pd), Mathf.Min(46f, width));
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Ghost button line on the controls picture: " + e.Message); }
        }

        static TextMesh Make(MenuJoinPlayer join, exSpriteAnimation diagram)
        {
            var deity = R.Get<MenuDeitySelectPlayer>(join, "m_deitySelect");
            GameObject template = null;
            if (deity != null)
            {
                var tw = deity.transform.Find("TextWorships");
                template = tw != null ? tw.gameObject : (R.Get<TextMesh>(deity, "m_name") != null ? R.Get<TextMesh>(deity, "m_name").gameObject : null);
            }
            if (template == null) return null;
            var tm = SlotArt.Text(template, diagram.transform, Name, Vector3.zero, SlotArt.Body, TextAnchor.UpperCenter);
            tm.gameObject.layer = diagram.gameObject.layer;
            // drawn at the label's own size on screen, whatever the picture's scale
            Vector3 want = template.transform.lossyScale, ds = diagram.transform.lossyScale;
            tm.transform.localScale = new Vector3(ds.x != 0f ? Mathf.Abs(want.x / ds.x) : 1f, ds.y != 0f ? Mathf.Abs(want.y / ds.y) : 1f, 1f);
            FurtherCore.Log.LogInfo("Controls picture: ghost button line added for " + join.name);
            return tm;
        }

        /// <summary>Just under the picture, centred on it, a little in front.</summary>
        static void Place(TextMesh tm, exSpriteAnimation diagram)
        {
            var r = diagram.GetComponent<Renderer>();
            Vector3 at = diagram.transform.position;
            if (r != null && r.bounds.size.y > 1f) at = new Vector3(r.bounds.center.x, r.bounds.min.y - 2f, at.z);
            tm.transform.position = new Vector3(at.x, at.y, diagram.transform.position.z - 0.5f);
        }
    }
}
