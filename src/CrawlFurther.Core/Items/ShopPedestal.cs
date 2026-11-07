using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Items
{
    using CrawlFurther.Art;
    using CrawlFurther.UI;

    /// <summary>
    /// The picture of a mod purchasable standing on its shop pedestal (PropPurchasable). Vanilla looks the purchasable's
    /// bubble clip name up in its own atlas, AtlasPurchasable, whose elements are 35 x 33 canvases with a small item at
    /// the bottom; a mod bubble is not in it. Mods draw their pedestal pictures on the same 35 x 33 canvas, one anim per
    /// purchasable, and register the sheet with <see cref="AddSheet"/>. The anim is named after the prefab: an item
    /// "Mod&lt;id&gt;" uses "&lt;id&gt;", a weapon "ModWeapon&lt;id&gt;" uses "Wpn&lt;id&gt;". A purchasable with no picture shows
    /// a vanilla stand-in of its kind (and a warning in the log).
    /// </summary>
    public static class ShopPedestal
    {
        const string VanillaAtlasName = "AtlasPurchasable";
        static readonly List<string> s_sheets = new List<string>();

        static exAtlas s_vanilla;
        static readonly HashSet<string> s_warned = new HashSet<string>();
        static readonly FieldInfo s_tintMat = AccessTools.Field(typeof(ColorTinterBase), "m_materialCached");
        static readonly FieldInfo s_tintHas = AccessTools.Field(typeof(ColorTinterBase), "m_hasProperty");
        static readonly MethodInfo s_tintUpdate = AccessTools.Method(typeof(ColorTinterBase), "UpdateTint", new[] { typeof(bool) });

        /// <summary>
        /// Add a sheet of pedestal pictures (each anim's first frame is one purchasable's picture, drawn on a 35 x 33
        /// canvas with the feet at the bottom centre, like AtlasPurchasable). Call it once when your mod starts; sheets
        /// added earlier win when two have the same anim.
        /// </summary>
        public static void AddSheet(string sheetId)
        {
            if (!string.IsNullOrEmpty(sheetId) && !s_sheets.Contains(sheetId)) s_sheets.Add(sheetId);
        }

        /// <summary>The pedestal anim name for a mod purchasable ("&lt;id&gt;" or "Wpn&lt;id&gt;"), or null for vanilla ones.</summary>
        public static string KeyFor(IPurchasable p)
        {
            GameObject go = null;
            var wd = p as WeaponData;
            if (wd != null) { if (wd.m_weapon != null) go = wd.m_weapon.gameObject; }
            else
            {
                var pu = p as Powerup;
                if (pu != null) go = pu.gameObject;
            }
            if (go == null) return null;
            string n = go.name;
            if (n.EndsWith("(Clone)")) n = n.Substring(0, n.Length - 7).TrimEnd();
            if (n.StartsWith("ModWeapon")) return "Wpn" + n.Substring(9);
            if (n.StartsWith("Mod")) return n.Substring(3);
            return null;
        }

        static exAtlas Vanilla
        {
            get
            {
                if (s_vanilla == null)
                    foreach (var a in Resources.FindObjectsOfTypeAll<exAtlas>())
                        if (a.name == VanillaAtlasName) { s_vanilla = a; break; }
                return s_vanilla;
            }
        }

        static bool IsPedestalAtlas(exAtlas a)
        {
            foreach (var id in s_sheets) { var sh = SpriteSheets.Get(id); if (sh != null && sh.atlas == a) return true; }
            return false;
        }

        static SpriteSheet SheetWith(string key, out SheetAnim anim)
        {
            anim = null;
            if (key == null) return null;
            foreach (var id in s_sheets)
            {
                var sh = SpriteSheets.Get(id);
                anim = sh != null ? sh.Anim(key) : null;
                if (anim != null && anim.frames != null && anim.frames.Length > 0) return sh;
            }
            anim = null;
            return null;
        }

        static void Remember(exSprite spr)
        {
            if (s_vanilla == null && spr.atlas != null && spr.atlas.name == VanillaAtlasName) s_vanilla = spr.atlas;
        }

        /// <summary>The tinter caches the renderer's material instance: after an atlas (material) swap, point it at the new
        /// one and re-apply the current tint (the can't-afford darkening). ColorTinterBase.ReapplyTint without
        /// ColorTinter's extra AddTint.</summary>
        static void Retint(exSprite spr)
        {
            var t = spr.GetComponent<ColorTinterBase>();
            if (t == null || s_tintMat == null || s_tintHas == null || s_tintUpdate == null) return;
            s_tintMat.SetValue(t, null);
            s_tintHas.SetValue(t, false);
            s_tintUpdate.Invoke(t, new object[] { true });
        }

        static void Show(exSprite spr, exAtlas atlas, int index)
        {
            spr.SetSprite(atlas, index, true);
            var r = spr.GetComponent<Renderer>();
            if (r != null && atlas.material != null && r.sharedMaterial != atlas.material) r.sharedMaterial = atlas.material;
            Retint(spr);
        }

        /// <summary>Before SetPurchasable: a pooled prop that last showed a mod item still holds a pedestal sheet's atlas,
        /// where the vanilla name lookup would fail. Put it back on AtlasPurchasable first.</summary>
        internal static void Before(PropPurchasable prop)
        {
            var spr = prop.GetComponent<exSprite>();
            if (spr == null) return;
            Remember(spr);
            if (spr.atlas == null || Vanilla == null || !IsPedestalAtlas(spr.atlas)) return;
            Show(spr, Vanilla, 0);
        }

        /// <summary>After SetPurchasable: a mod purchasable shows its pedestal picture; any purchasable whose bubble name is
        /// not in AtlasPurchasable (a mod clip without a picture) shows a vanilla stand-in of its kind, never a stale sprite.</summary>
        internal static void After(PropPurchasable prop, IPurchasable p)
        {
            if (p == null) return;
            var spr = prop.GetComponent<exSprite>();
            if (spr == null) return;
            Remember(spr);

            string key = KeyFor(p);
            SheetAnim anim;
            var sheet = SheetWith(key, out anim);
            if (sheet != null)
            {
                Show(spr, sheet.atlas, anim.frames[0]);
                ModMark.Follow(spr);   // the item's one mark (the shop popup leaves its picture bare)
                return;
            }

            var bubble = p.GetPurchasableAnim();
            var van = Vanilla;
            if (bubble == null || van == null || van.GetIndexByName(bubble.name) >= 0) return;   // vanilla lookup worked
            string stand = StandIn(p.GetPurchasableType());
            int idx = van.GetIndexByName(stand);
            if (idx < 0) return;
            Show(spr, van, idx);
            string tag = key ?? bubble.name;
            if (s_warned.Add(tag)) FurtherCore.Log.LogWarning("Shop pedestal: no picture for " + tag + ", showing " + stand);
        }

        /// <summary>This purchasable stands on its pedestal in its own (mod) picture, which carries its gem.</summary>
        public static bool HasPicture(IPurchasable p)
        {
            SheetAnim anim;
            return p != null && SheetWith(KeyFor(p), out anim) != null;
        }

        static string StandIn(ePurchasableType t)
        {
            switch (t)
            {
                case ePurchasableType.Weapon: return "Weapon_1hSword";
                case ePurchasableType.Spell: return "Spell1";
                case ePurchasableType.Potion: return "PotionLargeRed";
                default: return "Book";
            }
        }
    }

    [HarmonyPatch(typeof(PropPurchasable), "SetPurchasable", new[] { typeof(IPurchasable) })]
    static class Patch_ShopPedestalSprite
    {
        static void Prefix(PropPurchasable __instance)
        {
            try { ShopPedestal.Before(__instance); }
            catch (System.Exception e) { FurtherCore.Log.LogError("Shop pedestal (before) failed: " + e); }
        }

        static void Postfix(PropPurchasable __instance, IPurchasable purchasable)
        {
            try { ShopPedestal.After(__instance, purchasable); }
            catch (System.Exception e) { FurtherCore.Log.LogError("Shop pedestal failed: " + e); }
        }
    }

    /// <summary>The shop popup opens over the pedestal it describes: its picture of a mod purchasable (the bubble) gets
    /// the gem only when that pedestal shows a vanilla stand-in, so the item never wears two.</summary>
    [HarmonyPatch(typeof(GUIStore), "Show")]
    static class Patch_ShopPopupGem
    {
        static void Postfix(exSpriteAnimation ___m_portrait, IPurchasable purchasable)
        {
            try
            {
                bool pedestalMarks = ShopPedestal.HasPicture(purchasable);   // per popup: each player has their own
                var spr = ___m_portrait != null ? ___m_portrait.GetComponent<exSprite>() : null;
                if (spr != null) ModMark.Follow(spr, GemCorner.Art, () => !pedestalMarks && ModMark.IsModArt(spr.atlas));
            }
            catch (System.Exception e) { FurtherCore.Log.LogWarning("Shop popup gem: " + e.Message); }
        }
    }
}
