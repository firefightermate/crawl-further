using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// The one way to put the violet mod mark (<see cref="ModGem"/>) on something. Every mark goes through here and each
    /// picture has exactly one owner, so a mod entry wears one mark and a vanilla one none:
    ///  - <see cref="Follow"/>: a gem riding a picture (a portrait, a shop bubble, an evolve hand), shown while that
    ///    picture shows mod art. One per sprite: calling again only updates it.
    ///  - <see cref="Pin"/>: a gem at a fixed spot of a list cell (the vault's cells). One per cell; the cell owns every
    ///    picture inside it (a follow gem found under it is removed) and the gem turns off when the cell shows vanilla.
    ///  - <see cref="OwnedBy{T}"/>: pictures inside a T are marked by T's owner, so <see cref="Follow"/> leaves them
    ///    alone (vault cells get their pictures through Player.SetupPortrait, like every other menu picture).
    ///  - <see cref="SelectionShowsMark"/>: when a list button is itself violet (the mod pip of the god and origin
    ///    lists), the list owns the mark and the big picture of that entry stays bare.
    ///  - <see cref="MarkArt"/>: art made at run time (composed portraits) that counts as mod art.
    /// CrawlFurther.UI.cfg ModGem = false hides every mark.
    /// </summary>
    public static class ModMark
    {
        /// <summary>Art that is itself the violet mark: a list button drawn with it needs no other mark.</summary>
        static readonly string[] s_markSheets = { "ModVioletPip", "ModBadgeGem" };
        static readonly List<Type> s_owners = new List<Type>();
        static readonly HashSet<exAtlas> s_runtimeArt = new HashSet<exAtlas>();

        /// <summary>Marks are shown at all (CrawlFurther.UI.cfg ModGem).</summary>
        public static bool Enabled { get { return UiSettings.ModGem; } }

        /// <summary>A gem on <paramref name="target"/> while it shows mod art (or while <paramref name="show"/> says so).
        /// Does nothing for a picture inside an owner registered with <see cref="OwnedBy{T}"/> (and takes away a gem it
        /// had).</summary>
        public static void Follow(exSprite target, GemCorner corner = GemCorner.Art, Func<bool> show = null)
        {
            if (target == null) return;
            if (OwnerOf(target.transform) != null) { Remove(target.transform); return; }
            ModGem.Attach(target, corner, show);
        }

        /// <summary>The gem of a list cell at <paramref name="localPos"/>, on while <paramref name="on"/> and the
        /// <paramref name="follow"/> renderer (the cell's background) is drawn. The cell owns all of its pictures: any
        /// other gem under it goes. Safe to call on every refresh and on a reused cell.</summary>
        public static void Pin(Transform cell, Vector3 localPos, Renderer follow, bool on)
        {
            if (cell == null) return;
            ModGem pinned = null;
            foreach (var g in cell.GetComponentsInChildren<ModGem>(true))
            {
                if (g.transform.parent == cell && g.Pinned && pinned == null) { pinned = g; continue; }
                Drop(g);
            }
            if (!on)
            {
                if (pinned != null) pinned.On = false;
                return;
            }
            pinned = ModGem.AttachAt(cell, localPos, follow);
            if (pinned != null) pinned.On = true;
        }

        /// <summary>Pictures inside a <typeparamref name="T"/> are marked by T's own code (<see cref="Pin"/>), never by
        /// <see cref="Follow"/>.</summary>
        public static void OwnedBy<T>() where T : Component
        {
            if (!s_owners.Contains(typeof(T))) s_owners.Add(typeof(T));
        }

        /// <summary>The registered owner <paramref name="t"/> sits in (itself excluded), or null. Walks the parents
        /// directly, so it also works while the hierarchy is inactive (GetComponentInParent skips inactive objects).</summary>
        public static Component OwnerOf(Transform t)
        {
            if (t == null || s_owners.Count == 0) return null;
            for (var p = t.parent; p != null; p = p.parent)
                foreach (var type in s_owners)
                {
                    var c = p.GetComponent(type);
                    if (c != null) return c;
                }
            return null;
        }

        /// <summary>Take away the gem following <paramref name="target"/>, if any.</summary>
        public static void Remove(Transform target)
        {
            if (target == null) return;
            for (int i = target.childCount - 1; i >= 0; i--)
            {
                var g = target.GetChild(i).GetComponent<ModGem>();
                if (g != null && !g.Pinned) Drop(g);
            }
        }

        static void Drop(ModGem g)
        {
            g.gameObject.SetActive(false);   // Destroy waits for the end of the frame
            UnityEngine.Object.Destroy(g.gameObject);
        }

        /// <summary>Run-time art (a portrait composed from layers) that counts as mod art, like a sheet loaded through
        /// Core. Destroyed atlases drop out on their own.</summary>
        public static void MarkArt(exAtlas atlas)
        {
            if (atlas == null) return;
            s_runtimeArt.RemoveWhere(a => a == null);
            s_runtimeArt.Add(atlas);
        }

        internal static bool IsRuntimeArt(exAtlas atlas) { return atlas != null && s_runtimeArt.Contains(atlas); }

        /// <summary>Mod art: a sheet loaded through Core (not excluded) or art given to <see cref="MarkArt"/>.</summary>
        public static bool IsModArt(exAtlas atlas) { return ModGem.IsModArt(atlas); }

        /// <summary>This atlas is the violet mark itself (the mod list pip, the gem).</summary>
        public static bool IsMark(exAtlas atlas)
        {
            if (atlas == null) return false;
            foreach (var id in s_markSheets)
            {
                var sh = SpriteSheets.Get(id);
                if (sh != null && sh.atlas == atlas) return true;
            }
            return false;
        }

        /// <summary>
        /// The selected button of the list now in use under <paramref name="root"/> (the active, enabled MenuTextMenu) is
        /// drawn with the violet mark: that entry is already marked in its list, so its big picture needs no gem.
        /// </summary>
        public static bool SelectionShowsMark(Component root)
        {
            if (root == null) return false;
            foreach (var m in root.GetComponentsInChildren<MenuTextMenu>(false))
            {
                if (!m.enabled) continue;
                var items = R.Get<List<MenuTextMenuItem>>(m, "m_items");
                int i = m.GetSelectedId();
                if (items == null || i < 0 || i >= items.Count || items[i] == null) continue;
                var spr = items[i].GetComponent<exSprite>();
                if (spr != null && IsMark(spr.atlas)) return true;
            }
            return false;
        }

        /// <summary>Self-test: the mark art and the menu fields the owners read.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            ModGem.SelfCheck(bad);
            foreach (var id in s_markSheets) if (SpriteSheets.Get(id) == null) bad(id + " art missing (it is the violet mod mark)");
            if (HarmonyLib.AccessTools.Field(typeof(MenuTextMenu), "m_items") == null) bad("MenuTextMenu.m_items not found (list marks)");
        }
    }
}
