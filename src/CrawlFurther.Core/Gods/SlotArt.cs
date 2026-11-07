using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Art;
    using CrawlFurther.Heroes;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>
    /// Art and text helpers for the slot framework, shared by the pick lists, the slot editors and the evolve screen.
    /// The slot art lives in art/core (tools/sprites/ui_slots.py): pips, the lock overlay, editor arrows, cells,
    /// corners and ticks, and the evolve screen's brackets and ribbon, each with "Silver" and "Gold" anims.
    /// </summary>
    public static class SlotArt
    {
        static readonly Dictionary<string, exSpriteAnimClip> s_clips = new Dictionary<string, exSpriteAnimClip>();

        /// <summary>The anim name for a tier's metal in the slot art ("Silver" or "Gold").</summary>
        public static string Anim(SlotTier t) { return t == SlotTier.Gold ? "Gold" : "Silver"; }

        /// <summary>A cached clip of <paramref name="anim"/> on sheet <paramref name="sheet"/> (null if the art is missing).</summary>
        public static exSpriteAnimClip Clip(string sheet, string anim, bool loop = true)
        {
            string key = sheet + "/" + anim + (loop ? "" : "/once");
            exSpriteAnimClip c;
            if (s_clips.TryGetValue(key, out c) && c != null) return c;
            var sh = SpriteSheets.Get(sheet);
            if (sh == null || !sh.Has(anim)) return null;
            var b = new ClipBuilder(sh, anim, "ModUi_" + sheet + "_" + anim + (loop ? "" : "_Once"));
            c = (loop ? b.Loop() : b.Once()).Build();
            s_clips[key] = c;
            return c;
        }

        /// <summary>The pip of a silver / gold slot (animated when open, dull when locked).</summary>
        public static exSpriteAnimClip TierPip(SlotTier t, bool unlocked)
        {
            if (t == SlotTier.Gold) return Clip(unlocked ? "SlotPipGold" : "SlotPipGoldLocked", "Idle");
            return Clip(unlocked ? "SlotPipSilver" : "SlotPipSilverLocked", "Idle");
        }

        /// <summary>
        /// The origin list's pip: the vanilla pip for the vanilla hero, silver / gold for the slots, otherwise by what the
        /// origin grants: a weapon (or only stats / items) violet, a spell azure, a weapon and a spell the rose prism.
        /// </summary>
        public static exSpriteAnimClip OriginPip(OriginDef def, MenuDeitySelectPlayer panel, string unlockId)
        {
            if (def == null || def.isVanilla) return ModIcons.VanillaPip(panel);
            if (def.tier != SlotTier.Normal) return TierPip(def.tier, Unlocks.IsUnlocked(unlockId));
            switch (def.Kind)
            {
                case OriginKind.Spell: return Clip("ModSpellPip", "Idle") ?? ModIcons.VioletPip(panel);
                case OriginKind.WeaponAndSpell: return Clip("ModBothPip", "Idle") ?? ModIcons.VioletPip(panel);
                default: return ModIcons.VioletPip(panel);
            }
        }

        /// <summary>A sprite GameObject playing <paramref name="clip"/> (layer and parent as given).</summary>
        public static exSprite Sprite(string name, Transform parent, Vector3 local, exSpriteAnimClip clip, exPlane.Anchor anchor = exPlane.Anchor.MidCenter)
        {
            var go = new GameObject(name);
            go.layer = parent.gameObject.layer;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = local;
            go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();
            var spr = go.AddComponent<exSprite>();
            spr.anchor = anchor;
            if (Alive(clip))
            {
                var f = clip.frameInfos[0];
                spr.SetSprite(f.atlas, f.index);
                go.GetComponent<Renderer>().sharedMaterial = f.atlas.material;
                var an = go.AddComponent<exSpriteAnimation>();
                an.Play(clip);
            }
            else go.GetComponent<Renderer>().enabled = false;   // missing art: draw nothing rather than a magenta quad
            return spr;
        }

        static readonly AccessTools.FieldRef<exSpriteAnimation, Dictionary<string, exSpriteAnimState>> s_states =
            AccessTools.FieldRefAccess<exSpriteAnimation, Dictionary<string, exSpriteAnimState>>("nameToState");

        /// <summary>A clip that can be drawn: not destroyed, has frames, every frame's atlas and texture alive.</summary>
        public static bool Alive(exSpriteAnimClip c)
        {
            if (c == null || c.frameInfos == null || c.frameInfos.Count == 0) return false;
            foreach (var f in c.frameInfos)
                if (f == null || f.atlas == null || f.atlas.texture == null || f.atlas.material == null) return false;
            return true;
        }

        /// <summary>
        /// Play <paramref name="clip"/> on <paramref name="an"/> without ever touching a destroyed clip: states whose clip
        /// was destroyed are dropped first (ex2D's RemoveAnimation reads the clip's name and throws on a destroyed one),
        /// then the clip is added under its name (replacing an older clip of the same name) and played. False if the clip
        /// itself is not drawable (nothing changes then).
        /// </summary>
        public static bool SafePlay(exSpriteAnimation an, exSpriteAnimClip clip)
        {
            if (an == null || !Alive(clip)) return false;
            try
            {
                an.GetAnimation(clip.name);                      // makes ex2D build its name table
                an.animations.RemoveAll(c => c == null);
                var d = s_states(an);
                if (d != null)
                {
                    List<string> dead = null;
                    foreach (var kv in d) if (kv.Value == null || kv.Value.clip == null) (dead ?? (dead = new List<string>())).Add(kv.Key);
                    if (dead != null) foreach (var k in dead) d.Remove(k);
                    exSpriteAnimState st;
                    if (!d.TryGetValue(clip.name, out st) || st.clip != clip) d[clip.name] = new exSpriteAnimState(clip.name, clip);
                }
                if (!an.animations.Contains(clip)) an.animations.Add(clip);
                var cur = an.GetCurrentAnimation();
                if (cur == null || cur.clip != clip || !an.IsPlaying()) an.Play(clip.name);
                return true;
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("SafePlay " + clip.name + ": " + e.Message); return false; }
        }

        /// <summary>Show <paramref name="clip"/> on a sprite (adds an animation component when it has none).</summary>
        public static void Play(exSprite s, exSpriteAnimClip clip)
        {
            if (s == null || !Alive(clip)) return;
            s.GetComponent<Renderer>().enabled = true;
            var an = s.GetComponent<exSpriteAnimation>() ?? s.gameObject.AddComponent<exSpriteAnimation>();
            var st = an.GetCurrentAnimation();
            if (st != null && st.clip == clip && an.IsPlaying()) return;
            s.SetSprite(clip.frameInfos[0].atlas, clip.frameInfos[0].index);
            s.GetComponent<Renderer>().sharedMaterial = clip.frameInfos[0].atlas.material;
            an.Play(clip);
        }

        /// <summary>A copy of a menu TextMesh object (font, size, material, spawn flash) holding its own text.</summary>
        public static TextMesh Text(GameObject template, Transform parent, string name, Vector3 local, Color col, TextAnchor anchor)
        {
            var go = UnityEngine.Object.Instantiate(template);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = local;
            go.transform.localScale = Vector3.one;
            foreach (var c in go.GetComponents<MenuPlayerColour>()) UnityEngine.Object.Destroy(c);
            foreach (Transform t in go.transform) UnityEngine.Object.Destroy(t.gameObject);
            go.SetActive(true);
            var tm = go.GetComponent<TextMesh>();
            tm.anchor = anchor;
            tm.alignment = anchor == TextAnchor.MiddleLeft || anchor == TextAnchor.UpperLeft ? TextAlignment.Left : TextAlignment.Center;
            tm.color = col;
            tm.text = "";
            return tm;
        }

        static readonly Dictionary<TextMesh, float> s_nameSize = new Dictionary<TextMesh, float>();

        /// <summary>
        /// Set a panel's name line, shrinking it when the text is wider than the 50-unit panel holds (a long name in
        /// CrawlMedium runs into the next player's panel). The width comes from the font's own advances (TextMesh: one
        /// advance unit at the mesh's font size = characterSize / 10 world units). ResetName puts the size back.
        /// </summary>
        public static void FitName(TextMesh tm, string s, float maxWidth = 46f)
        {
            if (tm == null) return;
            float baseSize;
            if (!s_nameSize.TryGetValue(tm, out baseSize)) s_nameSize[tm] = baseSize = tm.characterSize;
            tm.text = s ?? "";
            float w = 0f;
            try
            {
                var f = tm.font;
                int size = tm.fontSize > 0 ? tm.fontSize : f.fontSize;
                f.RequestCharactersInTexture(tm.text, size, tm.fontStyle);
                foreach (char c in tm.text)
                {
                    CharacterInfo ci;
                    if (f.GetCharacterInfo(c, out ci, size, tm.fontStyle)) w += ci.advance;
                }
                w *= baseSize * 0.1f;
            }
            catch { w = 0f; }
            if (w <= 0f) w = tm.text.Length * 5.5f * baseSize;   // CrawlMedium is about 5.5 px a letter
            tm.characterSize = w > maxWidth ? baseSize * maxWidth / w : baseSize;
        }

        /// <summary>Put a name line shrunk by <see cref="FitName"/> back to its own size.</summary>
        public static void ResetName(TextMesh tm)
        {
            float baseSize;
            if (tm != null && s_nameSize.TryGetValue(tm, out baseSize)) tm.characterSize = baseSize;
        }

        /// <summary>Width in world units of thin-font text at the menu's 0.8 character size.</summary>
        public static float Width(string s) { return PauseTips.Width(s ?? "") * 0.8f; }

        /// <summary>Editor text colours: labels (the menus' tab colour), body text (their highlight colour), the tiers, refusals.</summary>
        public static readonly Color Dim = new Color(0.557f, 0.463f, 0.314f, 1f);         // #8e7650
        public static readonly Color Body = new Color(0.83f, 0.745f, 0.61f, 1f);          // #d4be9c
        public static readonly Color Silver = new Color(0.86f, 0.9f, 0.96f, 1f);
        public static readonly Color Gold = new Color(1f, 0.86f, 0.42f, 1f);
        public static readonly Color Bad = new Color(0.85f, 0.38f, 0.32f, 1f);
        /// <summary>The text colour of a tier.</summary>
        public static Color Tier(SlotTier t) { return t == SlotTier.Gold ? Gold : Silver; }

        /// <summary>A display name for a monster prefab: its tip name, or the prefab name tidied up.</summary>
        public static string MonsterName(GameObject prefab)
        {
            if (prefab == null) return "";
            MonsterTip tip;
            if (TipRegistry.TryGet(prefab.name, out tip) && !string.IsNullOrEmpty(tip.name)) return tip.name.ToUpper();
            string n = prefab.name;
            foreach (var pre in new[] { "Enemy", "Mod" }) if (n.StartsWith(pre)) n = n.Substring(pre.Length);
            int u = n.IndexOf('_'); if (u > 0) n = n.Substring(0, u);
            var sb = new System.Text.StringBuilder();
            for (int i = 0; i < n.Length; i++)
            {
                if (i > 0 && char.IsUpper(n[i]) && !char.IsUpper(n[i - 1])) sb.Append(' ');
                sb.Append(n[i]);
            }
            return sb.ToString().ToUpper();
        }

        /// <summary>The slot framework's sheets (art/core), for the self-test.</summary>
        public static readonly string[] Sheets = { "SlotPipSilver", "SlotPipGold", "SlotPipSilverLocked", "SlotPipGoldLocked",
            "ModSpellPip", "ModBothPip", "SlotLockOverlay", "EdArrow", "EdMark", "EdCell", "EdCorner", "EdCheck", "EvoBracket",
            "EvoHeader", "UnlockBanner" };

        /// <summary>Self-test: report missing slot art through <paramref name="bad"/>.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            foreach (var s in Sheets) if (SpriteSheets.Get(s) == null) bad("slot art missing: " + s);
            if (Clip("EdArrow", "Silver") == null || Clip("EdArrow", "Gold") == null) bad("slot art: EdArrow anims");
        }
    }
}
