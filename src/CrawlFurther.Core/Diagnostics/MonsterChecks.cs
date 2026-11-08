using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

namespace CrawlFurther.Diagnostics
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The self-test's "monsters" and "menu pictures" sections: every monster built through MonsterFactory, whatever mod
    /// it came from, is checked for art, attacks, clip events and how the menus will draw it.
    /// </summary>
    static class MonsterChecks
    {
        static void Bad(string msg) { SelfTest.Bad(msg); }
        static void Note(string msg) { SelfTest.Note(msg); }

        static HashSet<string> s_modMethods;

        /// <summary>Every method name a mod MonoBehaviour can receive (they are added to instances at Awake, so the
        /// prefab can't be asked).</summary>
        static HashSet<string> ModMethods()
        {
            if (s_modMethods != null) return s_modMethods;
            s_modMethods = new HashSet<string>();
            foreach (var asm in FurtherCore.Assemblies)
                foreach (var t in asm.GetTypes())
                    if (typeof(MonoBehaviour).IsAssignableFrom(t)) AddMethods(t, s_modMethods);
            return s_modMethods;
        }

        static void AddMethods(Type t, HashSet<string> into)
        {
            for (var tt = t; tt != null && tt != typeof(MonoBehaviour); tt = tt.BaseType)
                foreach (var m in tt.GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.DeclaredOnly))
                    into.Add(m.Name);
        }

        static void CheckClip(string who, Player p, SpriteSheet sheet, string field, bool required)
        {
            var c = R.Get<exSpriteAnimClip>(p, field);
            if (c == null) { if (required) Bad(who + " has no " + field); return; }
            if (c.frameInfos == null || c.frameInfos.Count == 0) { Bad(who + " " + field + " (" + c.name + ") has no frames"); return; }
            var a = c.frameInfos[0].atlas;
            if (a == null) { Bad(who + " " + field + " has a frame with no atlas"); return; }
            if (field == "m_animationStatue")
            {
                if (SpriteSheets.ByAtlas(a) == null) Bad(who + " statue clip " + c.name + " still shows vanilla art");
                return;
            }
            if (sheet != null && a != sheet.atlas) Bad(who + " " + field + " (" + c.name + ") is not drawn from its own sheet " + sheet.id);
        }

        public static void CheckMonsters()
        {
            var methods = ModMethods();
            foreach (var kv in MonsterFactory.Built)
            {
                var p = kv.Value;
                if (p == null) { Bad(kv.Key + " is null"); continue; }
                string who = kv.Key;
                Note(who + "  hp=" + R.Get<float>(p.GetComponent<Health>(), "m_healthMax") + "  evolveCost=" + R.Get<float>(p, "m_evolveCost"));

                // art: every slot the game plays outside attacks, from this monster's own sheet, and the menus' material
                var spr = p.GetComponent<exSprite>();
                var sheet = spr != null ? SpriteSheets.ByAtlas(spr.atlas) : null;
                if (sheet == null) Bad(who + " prefab sprite is not on a mod sheet (" + (spr != null && spr.atlas != null ? spr.atlas.name : "none") + ")");
                foreach (var f in new[] { "m_animationIdle", "m_animationRun", "m_animationDead", "m_animationStatue", "m_portraitAnim" })
                    CheckClip(who, p, sheet, f, true);
                var kb = R.Get<exSpriteAnimClip>(p, "m_animationKnockback");
                if (kb != null && kb.wrapMode == WrapMode.Loop) Bad(who + " has a looping knockback clip (stun-lock)");
                var rend = p.GetComponent<Renderer>();
                if (spr != null && rend != null && spr.atlas != null && rend.sharedMaterial != spr.atlas.material)
                    Bad(who + " renderer material is not its atlas material (menus would show wrong art)");

                // attacks: the special only counts when the monster has one (fodder bases carry an empty special slot)
                var effects = Kit.Effects(p);
                var attacks = new List<AttackData>(Kit.Attacks(p));
                if (attacks.Count == 0) Bad(who + " has no attacks");
                if (R.Get<bool>(p, "m_hasSpecialAttack"))
                {
                    var sp = R.Get<AttackData>(p, "m_specialAttack");
                    if (sp == null) Bad(who + " has a special flag but no special attack"); else attacks.Add(sp);
                }
                var receivers = new HashSet<string>(methods);
                foreach (var mb in p.GetComponents<MonoBehaviour>()) if (mb != null) AddMethods(mb.GetType(), receivers);
                foreach (var a in attacks)
                {
                    if (a == null) { Bad(who + " has a null attack entry"); continue; }
                    var c = a.m_animationFront;
                    if (c == null) { Bad(who + " attack with no clip"); continue; }
                    if (c.frameInfos.Count == 0) Bad(who + " clip " + c.name + " has no frames");
                    bool run = false;
                    foreach (var e in c.eventInfos)
                    {
                        if (e.methodName == "AnimRun") run = true;
                        if ((e.methodName == "AnimAttack" || e.methodName == "ModAmbush") &&
                            (e.intParam < 0 || e.intParam >= effects.Count || effects[e.intParam].m_object == null))
                            Bad(who + " clip " + c.name + " AnimAttack(" + e.intParam + ") has no effect");
                        if (!string.IsNullOrEmpty(e.methodName) && !receivers.Contains(e.methodName))
                            Bad(who + " clip " + c.name + " sends '" + e.methodName + "', which nothing on the monster receives");
                    }
                    if (!run && !ClipBuilder.HandsOff(c)) Bad(who + " clip " + c.name + " never returns control (no AnimRun)");
                    Note("    " + c.name + "  " + c.frameInfos.Count + " frames, " + c.length.ToString("0.00") + "s, cd " + a.m_cooldown);
                }
                Note("    portrait offset " + p.m_portraitOffset + " evolve " + p.m_portraitOffsetEvolve);
            }
        }

        static string Name(Player p) { return p == null ? "null" : p.gameObject.name; }

        // Evolve-menu monster button: 38.09 x 12.1 clip window centred on the sprite (level5 "Monster"), scale 1, evolve offsets.
        // God-select / HUD portrait: 10 x 12.8 window, clip offset -1, sprite scale 0.8 (level2 "PortraitImage").
        static readonly Rect ButtonWindow = new Rect(-19.045f, -6.05f, 38.09f, 12.1f);
        static readonly Rect PortraitWindow = new Rect(-4f, -6.4f, 10f, 12.8f);

        /// <summary>Area of a frame's opaque bounds that lands inside a menu window, as SetupPortrait places it.</summary>
        static float InWindow(Player p, SpriteSheet sh, exSprite spr, int index, Vector2 portraitOffset, float scale, Rect win, out float artArea)
        {
            artArea = 0f;
            int bx, by, bw, bh;
            if (!MonsterFactory.Bounds(sh, index, out bx, out by, out bw, out bh)) return 0f;
            var off = (spr.offset - portraitOffset) * scale;
            var art = new Rect(off.x + (bx - sh.manifest.cellW * 0.5f) * scale, off.y + by * scale, bw * scale, bh * scale);
            artArea = art.width * art.height;
            float w = Mathf.Min(art.xMax, win.xMax) - Mathf.Max(art.xMin, win.xMin);
            float h = Mathf.Min(art.yMax, win.yMax) - Mathf.Max(art.yMin, win.yMin);
            return w > 0f && h > 0f ? w * h : 0f;
        }

        /// <summary>
        /// Everything that decides what picture the game draws for a mod monster: the prefab sprite and its material, the
        /// textures of the idle / run / portrait frames, where the portrait lands in the evolve button and god-select
        /// windows, clip names (exSpriteAnimation resolves clips by name), and that no two monsters draw the same frame.
        /// Then, for every evolution link, the real menu code path (SetupPortrait + exClipping.AddPlane +
        /// SetPalettedClipShader on one reused sprite, plus the clip plane's disable/enable material swap) must end with
        /// the new monster's texture under a clip material that receives the clip rect.
        /// </summary>
        public static void CheckPictures()
        {
            var clipOwner = new Dictionary<string, string>();
            var frameOwner = new Dictionary<string, string>();
            int n = 0;
            foreach (var kv in MonsterFactory.Built)
            {
                var p = kv.Value;
                if (p == null) continue;
                string who = kv.Key;
                var spr = p.GetComponent<exSprite>();
                var rend = p.GetComponent<Renderer>();
                var sh = spr != null ? SpriteSheets.ByAtlas(spr.atlas) : null;
                if (spr == null || rend == null || sh == null) { Bad(who + ": prefab sprite/renderer missing or not on a mod sheet"); continue; }
                n++;
                var tex = sh.atlas.texture;
                if (rend.sharedMaterial == null || rend.sharedMaterial.mainTexture != tex)
                    Bad(who + ": renderer material texture is not its sheet's (" + (rend.sharedMaterial == null ? "none" : rend.sharedMaterial.name) + ")");
                if (spr.color.a < 0.5f) Bad(who + ": prefab sprite colour alpha " + spr.color.a);
                if (!rend.enabled || !spr.enabled) Bad(who + ": prefab renderer or sprite disabled");
                if (spr.index < 0 || spr.index >= sh.atlas.elements.Length) Bad(who + ": prefab sprite index " + spr.index + " outside its sheet");
                var feet = MonsterFactory.FeetOffset(sh);
                if ((spr.offset - feet).sqrMagnitude > 0.001f) Bad(who + ": sprite offset " + spr.offset + " does not put the feet on the transform " + feet);
                foreach (var f in new[] { "m_animationIdle", "m_animationRun", "m_portraitAnim", "m_animationDead", "m_animationKnockback", "m_animationSpawn" })
                {
                    var c = R.Get<exSpriteAnimClip>(p, f);
                    if (c == null) continue;
                    foreach (var fi in c.frameInfos)
                        if (fi.atlas == null || fi.atlas.texture != tex) { Bad(who + ": " + f + " (" + c.name + ") has a frame on another texture (" + (fi.atlas == null ? "none" : fi.atlas.name) + ")"); break; }
                    string owner;
                    if (clipOwner.TryGetValue(c.name, out owner) && owner != who) Bad(who + ": clip name '" + c.name + "' (" + f + ") is also used by " + owner);
                    else clipOwner[c.name] = who;
                    if (f == "m_animationIdle" || f == "m_portraitAnim" || f == "m_animationRun")
                    {
                        string key = c.frameInfos.Count == 0 ? "empty" : tex.GetInstanceID() + ":" + c.frameInfos[0].index + ":" + f;
                        if (frameOwner.TryGetValue(key, out owner) && owner != who) Bad(who + ": " + f + " first frame is the same picture as " + owner + "'s");
                        else frameOwner[key] = who;
                    }
                }
                var idle = R.Get<exSpriteAnimClip>(p, "m_animationIdle");
                // a kit may swap the body's idle for a stance (the Sundered fights as its dark half alone) and keep the
                // sheet's own Idle for the menus: either picture is right
                var sheetIdle = sh.Anim("Idle");
                bool sheetPicture = sheetIdle != null && sheetIdle.frames.Length > 0 && spr.atlas == sh.atlas && spr.index == sheetIdle.frames[0];
                if (idle != null && idle.frameInfos.Count > 0 && !sheetPicture && (spr.atlas != idle.frameInfos[0].atlas || spr.index != idle.frameInfos[0].index))
                    Bad(who + ": the evolve hands draw the prefab sprite (" + spr.index + "), which is not its Idle frame " + idle.frameInfos[0].index);
                var por = R.Get<exSpriteAnimClip>(p, "m_portraitAnim") ?? idle;
                var run = R.Get<exSpriteAnimClip>(p, "m_animationRun");
                float area, inside;
                foreach (var pair in new[] { new KeyValuePair<string, exSpriteAnimClip>("portrait", por), new KeyValuePair<string, exSpriteAnimClip>("run", run) })
                {
                    if (pair.Value == null || pair.Value.frameInfos.Count == 0) continue;
                    inside = InWindow(p, sh, spr, pair.Value.frameInfos[0].index, p.m_portraitOffsetEvolve, 1f, ButtonWindow, out area);
                    if (inside < 0.25f * Mathf.Min(area, ButtonWindow.width * ButtonWindow.height))
                        Bad(who + ": evolve-menu button shows only " + inside.ToString("0") + " px2 of its " + pair.Key + " art inside the 38x12 window");
                }
                if (por != null && por.frameInfos.Count > 0)
                {
                    inside = InWindow(p, sh, spr, por.frameInfos[0].index, p.m_portraitOffset, 0.8f, PortraitWindow, out area);
                    if (inside < 0.25f * Mathf.Min(area, PortraitWindow.width * PortraitWindow.height))
                        Bad(who + ": god-select/HUD portrait shows only " + inside.ToString("0") + " px2 of its art inside the 10x13 window");
                }
            }
            Note(n + " mod monsters: material, frames, clip names, portrait windows checked");
            MenuRoundTrip();
        }

        /// <summary>Runs the game's own portrait code on one reused, clipped menu sprite through every evolution link.</summary>
        static void MenuRoundTrip()
        {
            var holder = new GameObject("CrawlMod_SelfTestMenu");
            holder.SetActive(false);   // no Awake/OnEnable: exClipping would need the menu camera
            var mats = new List<Material>();
            int links = 0;
            try
            {
                var go = new GameObject("Monster");
                go.transform.SetParent(holder.transform, false);
                go.AddComponent<MeshFilter>();
                var mr = go.AddComponent<MeshRenderer>();
                var spr = go.AddComponent<exSprite>();
                spr.anchor = exPlane.Anchor.BotCenter;
                var clip = go.AddComponent<exClipping>();
                clip.width = ButtonWindow.width; clip.height = ButtonWindow.height;
                foreach (var god in DeityFactory.BuiltNames)
                {
                    var d = SystemDeity.GetDeity(god);
                    if (d == null) continue;
                    var chain = new List<Player>();
                    foreach (var s in d.GetStartingMonsters() ?? new GameObject[0])
                        if (s != null && s.GetComponent<Player>() != null) chain.Add(s.GetComponent<Player>());
                    for (int i = 0; i < chain.Count && i < 64; i++)
                    {
                        var from = chain[i];
                        var evo = from.GetEvolveTo() ?? new Player[0];
                        for (int hand = 0; hand < evo.Length; hand++)
                        {
                            var to = evo[hand];
                            if (to == null) continue;
                            // the hand layout (EvolveHands): in its own column, inside the panel, under the cost
                            var tsp = to.GetComponent<exSprite>();
                            var tsh = tsp != null ? SpriteSheets.ByAtlas(tsp.atlas) : null;
                            int hbx, hby, hbw, hbh; float hk, hover; Vector2 hoff;
                            float curH = EvolveHands.ArtHeight(from.GetComponent<exSprite>());
                            if (tsh != null && MonsterFactory.Bounds(tsh, tsp.index, out hbx, out hby, out hbw, out hbh))
                            {
                                if (!EvolveHands.Fit(tsh.manifest.cellW, hbx, hby, hbw, hbh, hand == 0 ? -16f : 16.9f, curH, out hk, out hoff, out hover))
                                    Bad(god + ": " + Name(to) + " does not fit the evolve menu's " + (hand == 0 ? "left" : "right") + " hand");
                                else if (hk < 1f && hbh * hk < curH - 0.01f)
                                    Bad(god + ": " + Name(to) + " is drawn shorter (" + (hbh * hk).ToString("0.0") + ") than " + Name(from) + " (" + curH + ") in the evolve menu");
                                else
                                    Note("    " + Name(from) + " -> " + Name(to) + ": hand scale " + hk.ToString("0.###") + (hover > 0f ? ", crosses the centre by " + hover.ToString("0.0") : ""));
                            }
                            if (!chain.Contains(to)) chain.Add(to);
                            links++;
                            ShowInButton(from, spr, clip, mr, mats);
                            ShowInButton(to, spr, clip, mr, mats);                // evolved in the same menu visit
                            Expect(god, from, to, "after evolving", spr, clip, mr);
                            // the menu closes and reopens: exClipping.OnDisable / OnEnable swap materials by what AddPlane recorded
                            var info = clip.planeInfoList.Find(x => x.plane == spr);
                            if (info != null && info.material != null && info.material.mainTexture is Texture2D)
                            {
                                mr.sharedMaterial = info.material;
                                Material cm;
                                if (clip.textureToClipMaterialTable.TryGetValue(info.material.mainTexture as Texture2D, out cm)) mr.material = cm;
                            }
                            ShowInButton(to, spr, clip, mr, mats);
                            Expect(god, from, to, "after reopening the menu", spr, clip, mr);
                            // the hands: MenuEvolvePlayerEvolve.SetMonsterSprite draws the prefab sprite with the prefab material
                            var ts = to.GetComponent<exSprite>(); var tr = to.GetComponent<Renderer>();
                            var fs = from.GetComponent<exSprite>();
                            if (ts == null || tr == null || tr.sharedMaterial == null || tr.sharedMaterial.mainTexture != ts.atlas.texture)
                                Bad(god + ": the evolve hand for " + Name(to) + " would draw another texture");
                            else if (fs != null && fs.atlas == ts.atlas && fs.index == ts.index)
                                Bad(god + ": the evolve hand for " + Name(to) + " shows " + Name(from) + "'s picture");
                        }
                    }
                }
                foreach (var m in clip.clipMaterialList) if (m != null && !mats.Contains(m)) mats.Add(m);
            }
            finally
            {
                foreach (var m in mats) if (m != null) UnityEngine.Object.Destroy(m);
                UnityEngine.Object.Destroy(holder);
            }
            Note(links + " evolution links shown through the evolve-menu button path");
        }

        static void ShowInButton(Player p, exSprite spr, exClipping clip, Renderer mr, List<Material> mats)
        {
            p.SetupPortrait(spr, true);
            clip.AddPlane(spr);
            if (Singleton<Constants>.Get != null) Utils.SetPalettedClipShader(p.GetComponent<Renderer>(), mr);
            var m = mr.sharedMaterial;
            if (m != null && !mats.Contains(m)) mats.Add(m);
        }

        static void Expect(string god, Player from, Player to, string when, exSprite spr, exClipping clip, Renderer mr)
        {
            var ts = to.GetComponent<exSprite>();
            var m = mr.sharedMaterial;
            if (ts == null || spr.atlas != ts.atlas) { Bad(god + ": " + Name(from) + " -> " + Name(to) + " " + when + ": menu sprite is on " + (spr.atlas == null ? "no atlas" : spr.atlas.name)); return; }
            if (m == null || m.mainTexture != ts.atlas.texture)
                Bad(god + ": " + Name(from) + " -> " + Name(to) + " " + when + ": button draws texture " + (m == null || m.mainTexture == null ? "none" : m.mainTexture.name) + " (shows another monster)");
            else if (!clip.clipMaterialList.Contains(m))
                Bad(god + ": " + Name(from) + " -> " + Name(to) + " " + when + ": button material gets no clip rect (blank picture)");
        }
    }
}
