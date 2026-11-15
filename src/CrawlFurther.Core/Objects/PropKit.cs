using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Objects
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Room props wearing mod art: the game's floor dressing, standing props and breakable props, cloned and reskinned,
    /// for a biome's prop groups (<see cref="Game.BiomeDef"/>). Each keeps the game's placement rules
    /// (<c>SpawnConstraints</c>), depth sorting and shadow; its footprint is a low capsule at the base, as the game's
    /// own props have, so the hero walks behind a tall prop and round a wide one. Each sheet holds one prop, feet at the
    /// bottom centre of the cell; its <c>Idle</c> frame is the picture.
    /// </summary>
    public static class PropKit
    {
        /// <summary>Floor dressing with no collision, from the game's floor splotch.</summary>
        public static GameObject Decal(string name, string sheet)
        {
            var go = Clone("FloorSplotchDecal", name, sheet, true);
            if (go == null) return null;
            foreach (var c in go.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(c);
            return go;
        }

        /// <summary>A standing prop: solid at its base, <paramref name="footW"/> wide and <paramref name="footD"/> deep
        /// (game pixels), from the game's large stalagmite.</summary>
        public static GameObject Still(string name, string sheet, float footW, float footD)
        {
            var go = Clone("StalagmiteLarge1", name, sheet, false);
            if (go == null) return null;
            Foot(go, footW, footD);
            return go;
        }

        /// <summary>A prop that anything's hits break (hero or monster), from the game's large barrel:
        /// <paramref name="health"/> hits, then it spawns <paramref name="spawnOnDeath"/> and is gone.
        /// <paramref name="spawnOnHit"/> (optional) plays on each hit.</summary>
        public static GameObject Breakable(string name, string sheet, float footW, float footD, float health,
                                           GameObject spawnOnDeath, GameObject spawnOnHit = null)
        {
            var go = Clone("PropDestructibleBarrelLarge_noEcto", name, sheet, false);
            if (go == null) return null;
            Foot(go, footW, footD);
            var hp = go.GetComponent<Health>();
            if (hp != null) R.Set(hp, "m_healthMax", health);
            var ph = go.GetComponent<PropHitable>();
            if (ph != null)
            {
                R.Set(ph, "m_spawnOnDeath", spawnOnDeath);
                R.Set(ph, "m_spawnOnHit", spawnOnHit);
                R.Set(ph, "m_spawnOnHitOffset", new Vector2(0f, 4f));
            }
            // the box attacks hit: the sprite's body
            var spr = go.GetComponent<exSprite>();
            var dmg = go.transform.Find("Damagable");
            var box = dmg != null ? dmg.GetComponent<BoxCollider>() : null;
            if (box != null && spr != null)
            {
                float w = Mathf.Max(6f, spr.width * 0.7f), h = Mathf.Max(6f, spr.height * 0.6f);
                box.size = new Vector3(w, h, box.size.z);
                box.center = new Vector3(0f, h * 0.5f, box.center.z);
            }
            return go;
        }

        /// <summary>Something on the back wall (from the game's torch, which the room places against it). Its light
        /// stays; <paramref name="light"/> recolours it (null leaves it as the torch's).</summary>
        public static GameObject Wall(string name, string sheet, Recolour.Fn light = null)
        {
            var go = Clone("Torch1", name, sheet, true, 2f);
            if (go == null) return null;
            var glow = go.transform.Find("Lightsource_flicker");
            if (glow != null && light != null) Recolour.Tree(glow.gameObject, name + "Light", light);
            foreach (var c in go.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(c);
            return go;
        }

        static GameObject Clone(string vanilla, string name, string sheetId, bool animated, float offsetY = -2f)
        {
            var sh = SpriteSheets.Get(sheetId);
            if (sh == null || !sh.Has("Idle")) { FurtherCore.Log.LogWarning("Prop " + name + ": no sheet " + sheetId); return null; }
            var src = FxFactory.Vanilla(vanilla);
            if (src == null) return null;
            var go = MonsterFactory.ClonePrefab(src, name);
            Built[name] = go;
            var clip = new ClipBuilder(sh, "Idle", name + "Idle").Loop().Build();
            var spr = go.GetComponent<exSprite>();
            if (spr == null) return go;
            var anim = go.GetComponent<exSpriteAnimation>();
            if (anim != null)
            {
                if (animated) FxFactory.Reskin(go, clip, sh);
                else anim.enabled = false;
            }
            spr.enabled = true;
            spr.customSize = false;
            spr.SetSprite(sh.atlas, clip.frameInfos[0].index);
            var r = spr.GetComponent<Renderer>();
            if (r != null && sh.atlas.material != null) r.sharedMaterial = sh.atlas.material;
            spr.anchor = exPlane.Anchor.BotCenter;
            spr.offset = new Vector2(0f, offsetY);
            // the game's shadow, stretched to the prop
            var shadow = go.transform.Find("Shadow");
            if (shadow != null)
            {
                var ss = shadow.GetComponent<exSprite>();
                float baseW = ss != null && ss.width > 0f ? ss.width : 12f;
                float k = Mathf.Clamp(spr.width * 0.75f / baseW, 0.4f, 4f);
                shadow.localScale = new Vector3(k, Mathf.Clamp(k, 0.6f, 1.6f), 1f);
            }
            return go;
        }

        static void Foot(GameObject go, float footW, float footD)
        {
            var cap = go.GetComponent<CapsuleCollider>();
            if (cap == null) return;
            float r = Mathf.Max(1f, footD * 0.5f);
            cap.direction = 0;
            cap.radius = r;
            cap.height = Mathf.Max(r * 2f, footW);
            cap.center = new Vector3(0f, r * 0.5f, cap.center.z);
        }

        /// <summary>Every prop template this kit made, by name.</summary>
        public static readonly Dictionary<string, GameObject> Built = new Dictionary<string, GameObject>();
    }
}
