using System;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.UI;

    /// <summary>
    /// A copy of the god select's starter box (dark plate + a clipped monster portrait), at any scale. Shows a monster
    /// still (its portrait frame) or running (the evolve menu's selected look), or any clip.
    /// </summary>
    public class BoxView
    {
        public GameObject root;
        public exSprite img, bg;
        exClipping m_clip;
        exSpriteAnimation m_anim;
        exSprite m_frame, m_mark;
        public Player monster;
        bool m_running;

        /// <summary>A copy of <paramref name="template"/> (a starter box) at <paramref name="local"/>, <paramref name="scale"/> times the god select's size.</summary>
        public static BoxView Create(GameObject template, Transform parent, string name, Vector3 local, float scale)
        {
            var go = UnityEngine.Object.Instantiate(template);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = local;
            go.transform.localScale = new Vector3(0.9f * scale, 0.9f * scale, 1f);   // the god select draws its boxes at 0.9
            ResetCopiedClips(go);   // its own clip plane and plain materials (not box 1's)
            go.SetActive(true);
            var b = new BoxView { root = go };
            foreach (var s in go.GetComponentsInChildren<exSprite>(true))
            {
                if (s.GetComponent<ModGem>() != null) continue;   // the template's own gem came along with it
                if (s.GetComponent<exClipping>() != null) b.img = s;
                else if (b.bg == null) b.bg = s;
            }
            if (b.img != null)
            {
                b.m_clip = b.img.GetComponent<exClipping>();
                b.m_anim = b.img.GetComponent<exSpriteAnimation>() ?? b.img.gameObject.AddComponent<exSpriteAnimation>();
                if (b.img.GetComponent<MenuDisabledAnimTags>() == null) b.img.gameObject.AddComponent<MenuDisabledAnimTags>();   // swallows clip events
                ModGem.Attach(b.img);
                b.img.gameObject.SetActive(false);
            }
            return b;
        }

        /// <summary>Show a monster: its portrait frame, or its run animation when <paramref name="run"/>. Null empties the box.</summary>
        public void SetMonster(Player p, bool run)
        {
            if (img == null) return;
            if (p == null) { monster = null; img.gameObject.SetActive(false); return; }
            if (p == monster && run == m_running && img.gameObject.activeSelf) return;
            monster = p; m_running = run;
            try
            {
                if (m_clip != null) m_clip.RemovePlane(img);
                img.gameObject.SetActive(true);
                if (run) p.SetupPortraitAnimRun(img, m_anim);
                else { m_anim.Stop(); p.SetupPortrait(img); }
                if (m_clip != null) m_clip.AddPlane(img);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Editor box " + p.name + ": " + e.Message); }
        }

        /// <summary>Show any clip in the box (null empties it).</summary>
        public void SetClip(exSpriteAnimClip c)
        {
            if (img == null) return;
            monster = null;
            if (c == null) { img.gameObject.SetActive(false); return; }
            if (m_clip != null) m_clip.RemovePlane(img);
            img.gameObject.SetActive(true);
            img.offset = Vector2.zero;
            SlotArt.Play(img, c);
            if (m_clip != null) m_clip.AddPlane(img);
        }

        /// <summary>The tier frame (selected), the dashed "slot" frame, or the taken cross; null clears.</summary>
        public void SetFrame(exSpriteAnimClip c)
        {
            if (c == null) { if (m_frame != null) m_frame.gameObject.SetActive(false); return; }
            if (m_frame == null) m_frame = SlotArt.Sprite("Frame", root.transform, new Vector3(0f, 0f, -2f), c);
            m_frame.gameObject.SetActive(true);
            m_frame.scale = new Vector2(1.11f, 1.09f);   // the 12 x 15 cell art around the 10 x 12.8 box, in the box's units
            SlotArt.Play(m_frame, c);
        }

        /// <summary>A mark over the box (the taken cross, a find's glint); null clears.</summary>
        public void SetMark(exSpriteAnimClip c)
        {
            if (c == null) { if (m_mark != null) m_mark.gameObject.SetActive(false); return; }
            if (m_mark == null) m_mark = SlotArt.Sprite("Mark", root.transform, new Vector3(0f, 0f, -2.5f), c);
            m_mark.gameObject.SetActive(true);
            m_mark.scale = new Vector2(1.11f, 1.09f);
            SlotArt.Play(m_mark, c);
        }

        /// <summary>The box plate's rectangle in world units (mouse hit tests).</summary>
        public Rect WorldRect()
        {
            var r = bg != null ? bg.GetComponent<Renderer>() : null;
            if (r == null) return new Rect(0f, 0f, 0f, 0f);
            var b = r.bounds;
            return Rect.MinMaxRect(b.min.x, b.min.y, b.max.x, b.max.y);
        }

        /// <summary>Remove the box and the clip materials its clip plane made (one per atlas texture it showed).</summary>
        public void Destroy()
        {
            if (root == null) return;
            DestroyClipMaterials(root);
            UnityEngine.Object.Destroy(root);
            root = null;
        }

        /// <summary>
        /// A copied menu object (box, button) keeps the original's renderer materials, which can be the ORIGINAL clip
        /// plane's clip material: drawn with that, the copy would be clipped to the original's window (or vanish), and
        /// its own clip plane would record it as the "plain" material. Put every sprite back on its atlas's own material
        /// and give the copy empty clip planes of its own.
        /// </summary>
        public static void ResetCopiedClips(GameObject go)
        {
            if (go == null) return;
            foreach (var cl in go.GetComponentsInChildren<exClipping>(true))
            {
                cl.planeInfoList.Clear(); cl.clipMaterialList.Clear(); cl.textureToClipMaterialTable.Clear();
            }
            foreach (var spr in go.GetComponentsInChildren<exSprite>(true))
            {
                var r = spr.GetComponent<Renderer>();
                if (r != null && spr.atlas != null && spr.atlas.material != null) r.sharedMaterial = spr.atlas.material;
                if (spr.GetComponent<exClipping>() == null) spr.clippingPlane = null;
            }
        }

        /// <summary>Destroy the clip materials of every clip plane under <paramref name="go"/>, giving each plane its plain material back first.</summary>
        public static void DestroyClipMaterials(GameObject go)
        {
            if (go == null) return;
            foreach (var cl in go.GetComponentsInChildren<exClipping>(true))
            {
                foreach (var pi in cl.planeInfoList)
                {
                    // give each plane its plain material back first, so nothing renders with a destroyed one
                    var r = pi.plane != null ? pi.plane.GetComponent<Renderer>() : null;
                    if (r != null) r.sharedMaterial = pi.material;
                }
                foreach (var m in cl.clipMaterialList) if (m != null) UnityEngine.Object.Destroy(m);
                cl.planeInfoList.Clear(); cl.clipMaterialList.Clear(); cl.textureToClipMaterialTable.Clear();
            }
        }
    }
}
