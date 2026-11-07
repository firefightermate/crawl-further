using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Heroes
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Util;

    /// <summary>
    /// The origin's headwear (helm, hood, hat, mane...) on the in-game hero: a child sprite that follows the head, in the
    /// player's colours (sheet <see cref="OriginDef.gearArt"/> + "_P1".."_P4", else gearArt itself). A silver / gold slot
    /// hero wears the sheets <see cref="ICustomHeroes.GearSheets"/> gives (headwear and a face piece).
    ///
    /// Gear sheets have 16 cells of 15 x 15 pixels: 8 head poses (4 quarter turns, mirrored), then the same 8 with the
    /// face hidden. HeroGearData (tools/sprites/hero_gear.py) holds, per AtlasHero frame, the pose and the top-left of
    /// the gear cell in the frame's untrimmed canvas. Mod weapon frames (atlases "ModAtlas_WpnHand_&lt;id&gt;", elements
    /// "WpnHand_&lt;id&gt;_&lt;source index&gt;") keep their AtlasHero source frame's canvas, so they use its entry.
    ///
    /// Every LateUpdate (after exSpriteAnimation picked the frame) the gear copies the hero sprite's placement: ex2D
    /// puts canvas pixel (px, py) of a BotCenter sprite at local ((px - W/2) * scale.x + offset.x,
    /// (H - py) * scale.y + offset.y), and the gear is TopLeft-anchored there with the same scale, so flips, hit bounces
    /// and grabs carry over. Frames without a visible head (smears, beams, unknown atlases) hide it. It copies the hero's
    /// alpha and shader tint (hit flash, corpse tint) and sits just in front of the hero.
    ///
    /// Added per hero instance from Player.InitAsPlayer: components added to prefabs by a plugin do not survive
    /// Instantiate. Ghosts never get one.
    /// </summary>
    public class HeroGear : MonoBehaviour
    {
        const string TINT = "_Tint";
        const float DEPTH = -0.01f;            // just in front of the hero (DepthHandler spaces 1 px of height ~0.02)
        /// <summary>Keep the gear on the hero's corpse (death animation and the body left on the floor).</summary>
        public static bool ShowOnCorpse = true;

        static readonly AccessTools.FieldRef<Player, PlayerData> s_pd = AccessTools.FieldRefAccess<Player, PlayerData>("m_playerData");
        static readonly AccessTools.FieldRef<Player, Player.ePlayerState> s_state = AccessTools.FieldRefAccess<Player, Player.ePlayerState>("m_state");
        static readonly Dictionary<exAtlas, int[]> s_tables = new Dictionary<exAtlas, int[]>();
        static bool s_errorLogged;

        Player m_player;
        exSprite m_hero;
        Renderer m_heroR;
        Layer m_head, m_face;
        exAtlas m_lastAtlas;
        int[] m_lastTable;
        Color m_lastTint = new Color(-1f, 0f, 0f, 0f);

        /// <summary>One gear sprite on the head: the headwear (origin gear or custom hat/hair) and, for the custom hero,
        /// a face piece (beard, eyepatch, war paint...) just behind it. Each has its own material copy for the tint.</summary>
        sealed class Layer
        {
            public exSprite spr;
            public Renderer r;
            public Material mat;
            public SpriteSheet sheet;
            public float depth;
        }

        /// <summary>Give a hero body its gear follower (or point an existing one at this body).</summary>
        public static void Attach(Player p)
        {
            if (p == null) return;
            var g = p.GetComponent<HeroGear>();
            if (g == null) g = p.gameObject.AddComponent<HeroGear>();
            g.Init(p);
        }

        void Init(Player p)
        {
            m_player = p;
            m_version = -1;                       // resolve the sheets again for the body's (new) player
            m_hero = p.GetComponent<exSprite>();
            m_heroR = p.GetComponent<Renderer>();
            if (m_head != null) return;
            m_face = NewLayer(p, "ModHeroGearFace", DEPTH + 0.002f);
            m_head = NewLayer(p, "ModHeroGear", DEPTH);
        }

        static Layer NewLayer(Player p, string name, float depth)
        {
            var go = new GameObject(name);
            go.layer = p.gameObject.layer;
            go.transform.SetParent(p.transform, false);
            go.transform.localPosition = new Vector3(0f, 0f, depth);
            go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();
            var l = new Layer { spr = go.AddComponent<exSprite>(), depth = depth };
            l.spr.anchor = exPlane.Anchor.TopLeft;
            l.r = go.GetComponent<Renderer>();
            l.r.enabled = false;
            return l;
        }

        /// <summary>The gear sheets a player's hero wears: the origin's gear in the player's colours, or the silver /
        /// gold hero's headwear and face piece.</summary>
        public static void SheetsFor(PlayerData pd, out SpriteSheet head, out SpriteSheet face)
        {
            head = face = null;
            var def = HeroClasses.For(pd);
            if (def == null) return;
            if (def.tier != SlotTier.Normal) { if (HeroClasses.CustomHeroes != null) HeroClasses.CustomHeroes.GearSheets(pd, def.tier, out head, out face); return; }
            if (string.IsNullOrEmpty(def.gearArt)) return;
            int slot = HeroLooks.SlotOf(pd);
            string key = def.gearArt + "#" + slot;
            if (s_slotSheets.TryGetValue(key, out head)) return;
            head = SpriteSheets.Get(def.gearArt + "_P" + (slot + 1)) ?? SpriteSheets.Get(def.gearArt);
            if (head != null && head.atlas == null) head = null;
            s_slotSheets[key] = head;
        }
        static readonly Dictionary<string, SpriteSheet> s_slotSheets = new Dictionary<string, SpriteSheet>();

        /// <summary>Bump when what a hero wears may have changed (HeroLooks.Refresh does on deity / origin set, a new hero
        /// body and colour swaps). Gear re-resolves its sheets only then, never every frame.</summary>
        public static int Version;
        int m_version = -1;
        PlayerData m_pd;

        /// <summary>Sheets of the player this body belongs to (kept on the corpse after the player moves on). Cheap when
        /// nothing changed: one int compare and one field read per frame, no allocation.</summary>
        void UpdateOrigin()
        {
            var pd = s_pd(m_player);
            if (m_version == Version && pd == m_pd) return;
            m_version = Version;
            m_pd = pd;
            if (pd == null || pd.GameObject != gameObject) return;
            SpriteSheet head, face;
            SheetsFor(pd, out head, out face);
            SetSheet(m_head, head);
            SetSheet(m_face, face);
        }

        void SetSheet(Layer l, SpriteSheet sh)
        {
            if (sh == l.sheet) return;
            l.sheet = sh != null && sh.atlas != null ? sh : null;
            if (l.mat != null) Destroy(l.mat);
            l.mat = null;
            if (l.sheet == null) return;
            l.spr.SetSprite(l.sheet.atlas, 0);
            l.mat = new Material(l.sheet.atlas.material) { name = "ModHeroGearMat" };
            l.r.sharedMaterial = l.mat;
            m_lastTint = new Color(-1f, 0f, 0f, 0f);
        }

        void LateUpdate()
        {
            bool head = false, face = false;
            try { Place(out head, out face); }
            catch (Exception e)
            {
                if (!s_errorLogged) { s_errorLogged = true; FurtherCore.Log.LogError("HeroGear: " + e); }
            }
            if (m_head != null && m_head.r.enabled != head) m_head.r.enabled = head;
            if (m_face != null && m_face.r.enabled != face) m_face.r.enabled = face;
        }

        void Place(out bool showHead, out bool showFace)
        {
            showHead = showFace = false;
            if (m_player == null || m_hero == null || m_head == null) return;
            UpdateOrigin();
            if ((m_head.sheet == null && m_face.sheet == null) || m_heroR == null || !m_heroR.enabled) return;
            if (ModUtil.IsGhost(m_player)) return;
            if (!ShowOnCorpse && s_state(m_player) == Player.ePlayerState.Dead) return;
            var col = m_hero.color;
            if (col.a <= 0.01f) return;

            var atlas = m_hero.atlas;
            int idx = m_hero.index;
            if (atlas == null || atlas.elements == null || idx < 0 || idx >= atlas.elements.Length) return;
            if (atlas != m_lastAtlas) { m_lastAtlas = atlas; m_lastTable = TableFor(atlas); }
            var tab = m_lastTable;
            if (tab == null || idx >= tab.Length) return;
            int v = tab[idx];
            if (v == 0) return;
            int cell = (v & 31) - 1;
            int gx = ((v >> 5) & 1023) - 512, gy = ((v >> 15) & 1023) - 512;
            if (cell < 0) return;

            var el = atlas.elements[idx];
            Vector2 sc = m_hero.scale, ppf = m_hero.ppfScale, off = m_hero.offset;
            float sx = sc.x * ppf.x, sy = sc.y * ppf.y;
            float lx = (gx - el.originalWidth * 0.5f) * sx + off.x, ly = (el.originalHeight - gy) * sy + off.y;
            var gc = new Color(1f, 1f, 1f, col.a);
            // ex2D commits mesh changes from the render camera's exSpriteMng (OnPreRender, after every LateUpdate):
            // follow the hero's camera so the gear is committed in the same frame as the hero
            var cam = m_hero.renderCamera;
            showHead = PlaceLayer(m_head, cell, lx, ly, sc, ppf, gc, cam);
            showFace = PlaceLayer(m_face, cell, lx, ly, sc, ppf, gc, cam);
            CopyTint();
        }

        static bool PlaceLayer(Layer l, int cell, float lx, float ly, Vector2 sc, Vector2 ppf, Color gc, Camera cam)
        {
            if (l.sheet == null || cell >= l.sheet.atlas.elements.Length) return false;
            var lp = new Vector3(lx, ly, l.depth);
            var t = l.spr.transform;
            if (t.localPosition != lp) t.localPosition = lp;
            if (l.spr.index != cell) l.spr.SetSprite(l.sheet.atlas, cell);
            if (l.spr.scale != sc) l.spr.scale = sc;
            if (l.spr.ppfScale != ppf) l.spr.ppfScale = ppf;
            if (l.spr.color != gc) l.spr.color = gc;
            if (l.r.sharedMaterial != l.mat && l.mat != null) l.r.sharedMaterial = l.mat;
            if (cam != null && l.spr.renderCameraForPrefab != cam) l.spr.renderCamera = cam;
            return true;
        }

        /// <summary>Hit flash, corpse and status tints are a _Tint colour on the hero's material (ColorTinterBase).</summary>
        void CopyTint()
        {
            var hm = m_heroR.sharedMaterial;
            var c = hm != null && hm.HasProperty(TINT) ? hm.GetColor(TINT) : new Color(1f, 1f, 1f, 0f);
            if (c == m_lastTint) return;
            m_lastTint = c;
            if (m_head.mat != null && m_head.mat.HasProperty(TINT)) m_head.mat.SetColor(TINT, c);
            if (m_face.mat != null && m_face.mat.HasProperty(TINT)) m_face.mat.SetColor(TINT, c);
        }

        /// <summary>Per atlas: the gear entry of each element (null = never show gear on this atlas).</summary>
        static int[] TableFor(exAtlas atlas)
        {
            int[] tab;
            if (s_tables.TryGetValue(atlas, out tab)) return tab;
            tab = null;
            string n = atlas.name ?? "";
            if (n == "AtlasHero")
            {
                if (atlas.elements.Length == HeroGearData.AtlasHero.Length) tab = HeroGearData.AtlasHero;
                else FurtherCore.Log.LogWarning("HeroGear: AtlasHero has " + atlas.elements.Length + " elements, table " + HeroGearData.AtlasHero.Length + ": gear off");
            }
            else if (n.StartsWith("ModAtlas_WpnHand_", StringComparison.Ordinal))
            {
                // WeaponHands elements are named "WpnHand_<id>_<AtlasHero source index>"
                var src = HeroGearData.AtlasHero;
                tab = new int[atlas.elements.Length];
                for (int k = 0; k < tab.Length; k++)
                {
                    var en = atlas.elements[k] != null ? atlas.elements[k].name : null;
                    int us = en != null ? en.LastIndexOf('_') : -1;
                    int s;
                    if (us >= 0 && int.TryParse(en.Substring(us + 1), out s) && s >= 0 && s < src.Length) tab[k] = src[s];
                }
            }
            s_tables[atlas] = tab;
            return tab;
        }

        void OnDestroy()
        {
            if (m_head != null && m_head.mat != null) Destroy(m_head.mat);
            if (m_face != null && m_face.mat != null) Destroy(m_face.mat);
        }
    }

    /// <summary>A body becomes a player's hero: give it the gear follower.</summary>
    [HarmonyPatch(typeof(Player), "InitAsPlayer")]
    static class Patch_HeroGearInitAsPlayer
    {
        static void Postfix(Player __instance, bool ___m_isHero, bool ___m_isGhost)
        {
            if (!___m_isHero || ___m_isGhost) return;
            try { HeroGear.Attach(__instance); }
            catch (Exception e) { FurtherCore.Log.LogError("HeroGear attach: " + e); }
        }
    }
}
