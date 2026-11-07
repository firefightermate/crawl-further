using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Testing
{
    using CrawlFurther.Util;

    /// <summary>
    /// The View page's outlines: red around the colliders of every live attack (DamageEffect, the game's hitbox
    /// component), green around every player's and monster's hurtbox (the DamagablePlayer-layer child). Boxes are the
    /// colliders' world bounds, drawn over the main camera's view.
    /// </summary>
    static class HitboxOverlay
    {
        static readonly Color Hit = new Color(1f, 0.25f, 0.2f, 0.95f);
        static readonly Color Hurt = new Color(0.3f, 1f, 0.4f, 0.9f);
        const float Rescan = 0.1f;

        static readonly List<Collider> s_hits = new List<Collider>();
        static readonly List<Collider> s_hurts = new List<Collider>();
        static float s_scannedAt = -100f;
        static Camera s_cam;

        /// <summary>Draw the outlines; call from OnGUI on the repaint event with GUI.matrix untouched.</summary>
        internal static void Draw()
        {
            var cam = Cam();
            if (cam == null) return;
            if (Time.unscaledTime - s_scannedAt > Rescan) Scan();
            foreach (var c in s_hits) if (c != null && c.enabled && c.gameObject.activeInHierarchy) Box(cam, c.bounds, Hit);
            foreach (var c in s_hurts) if (c != null && c.enabled && c.gameObject.activeInHierarchy) Box(cam, c.bounds, Hurt);
            GUI.color = Color.white;
        }

        static Camera Cam()
        {
            if (s_cam != null && s_cam.isActiveAndEnabled) return s_cam;
            var go = GameObject.Find("CameraMain");
            s_cam = go != null ? go.GetComponent<Camera>() : null;
            return s_cam;
        }

        static void Scan()
        {
            s_scannedAt = Time.unscaledTime;
            s_hits.Clear();
            s_hurts.Clear();
            foreach (var fx in Object.FindObjectsOfType<DamageEffect>())
                foreach (var c in fx.GetComponentsInChildren<Collider>()) s_hits.Add(c);
            foreach (var p in Object.FindObjectsOfType<Player>())
            {
                var c = ModUtil.Hurtbox(p.gameObject);
                if (c != null) s_hurts.Add(c);
            }
        }

        /// <summary>The bounds through the camera's viewport onto the whole screen (the game may render to a smaller
        /// texture that is then stretched over the screen).</summary>
        static void Box(Camera cam, Bounds b, Color color)
        {
            var lo = cam.WorldToViewportPoint(b.min);
            var hi = cam.WorldToViewportPoint(b.max);
            float x0 = Mathf.Min(lo.x, hi.x) * Screen.width, x1 = Mathf.Max(lo.x, hi.x) * Screen.width;
            float y0 = (1f - Mathf.Max(lo.y, hi.y)) * Screen.height, y1 = (1f - Mathf.Min(lo.y, hi.y)) * Screen.height;
            if (x1 < 0f || y1 < 0f || x0 > Screen.width || y0 > Screen.height) return;
            float t = Mathf.Max(1f, Screen.height / 540f);
            GUI.color = color;
            var tex = Texture2D.whiteTexture;
            GUI.DrawTexture(new Rect(x0, y0, x1 - x0, t), tex);
            GUI.DrawTexture(new Rect(x0, y1 - t, x1 - x0, t), tex);
            GUI.DrawTexture(new Rect(x0, y0, t, y1 - y0), tex);
            GUI.DrawTexture(new Rect(x1 - t, y0, t, y1 - y0), tex);
        }
    }
}
