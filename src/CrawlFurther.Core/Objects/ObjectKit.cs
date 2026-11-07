using System;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Objects
{
    using CrawlFurther.Art;
    using CrawlFurther.Compat;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>
    /// Room objects. <see cref="Register"/> builds an object's prefab from its <see cref="ObjectDef"/> (Use / Touch objects
    /// from the vanilla fountain, traps from the vanilla dart turret), its vault page and its spawn rule. Call it from a
    /// content pack.
    ///
    /// Random placement: after the game fills a room (SystemLevel.SpawnRoomContent), each eligible room rolls once
    /// (<see cref="RoomChance"/>, then <see cref="SecondChance"/> for a second object) and picks a def by
    /// <see cref="ObjSpawn.weight"/> among those whose rule allows this floor, room kind and environment and whose
    /// per-floor cap is not reached. Never in the start room, shops, boss rooms, hero-battle rooms, the tutorial or the
    /// attract demo. <see cref="SpawnIn"/> and <see cref="SpawnAt"/> place one by code.
    /// Settings: BepInEx/config/CrawlFurther.Objects.cfg (Enabled, RoomChance, SecondChance, and Force for testing).
    /// </summary>
    public static class ObjectKit
    {
        /// <summary>Registered defs and their prefabs, by id.</summary>
        public static readonly Dictionary<string, ObjectDef> Defs = new Dictionary<string, ObjectDef>();
        public static readonly Dictionary<string, GameObject> Built = new Dictionary<string, GameObject>();
        static readonly Dictionary<GameObject, ObjectDef> s_byPrefab = new Dictionary<GameObject, ObjectDef>();
        static readonly Dictionary<string, ObjectDef> s_byName = new Dictionary<string, ObjectDef>();

        // ------------------------------------------------------------------ config
        static ConfigFile s_cfg;
        static ConfigEntry<bool> s_enabled;
        static ConfigEntry<float> s_chance, s_second;
        static ConfigEntry<string> s_force;
        public static bool Enabled { get { Cfg(); return s_enabled == null || s_enabled.Value; } }
        public static float RoomChance { get { Cfg(); return s_chance != null ? Mathf.Clamp01(s_chance.Value) : 0.38f; } }
        public static float SecondChance { get { Cfg(); return s_second != null ? Mathf.Clamp01(s_second.Value) : 0.12f; } }

        static void Cfg()
        {
            if (s_cfg != null) return;
            try
            {
                s_cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, "CrawlFurther.Objects.cfg"), true);
                s_enabled = s_cfg.Bind("Spawning", "Enabled", true, "Place the room objects mods add (traps, shrines, fonts...) in rooms.");
                s_chance = s_cfg.Bind("Spawning", "RoomChance", 0.38f, "Chance that a room gets one mod object (0 to 1).");
                s_second = s_cfg.Bind("Spawning", "SecondChance", 0.12f, "Chance that a room that got one gets a second one (0 to 1).");
                s_force = s_cfg.Bind("Debug", "Force", "", "Testing: comma-separated object ids (e.g. HealFont,ChainHook). Every room that can hold " +
                                     "an object gets one of these, ignoring floors, room kinds and caps. Empty = normal play.");
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Objects config: " + e.Message); }
        }

        /// <summary>True for a registered object's prefab or instance.</summary>
        public static bool IsMod(GameObject go) { return DefOf(go) != null; }

        /// <summary>The def of a registered object's prefab or instance, or null.</summary>
        public static ObjectDef DefOf(GameObject go)
        {
            if (go == null) return null;
            ObjectDef d;
            if (s_byPrefab.TryGetValue(go, out d)) return d;
            return s_byName.TryGetValue(ModUtil.PrefabName(go), out d) ? d : null;
        }

        // ------------------------------------------------------------------ registration
        /// <summary>Build the object, its vault page and its spawn rule. Returns the prefab, or null if its art is missing or
        /// the build failed (logged). Registering an id twice returns the first prefab.</summary>
        public static GameObject Register(ObjectDef d)
        {
            if (d == null || string.IsNullOrEmpty(d.id)) return null;
            if (Built.ContainsKey(d.id)) return Built[d.id];
            var sheet = SpriteSheets.Get(d.art ?? ("Obj" + d.id));
            if (sheet == null) { FurtherCore.Log.LogError("Object " + d.id + ": art " + d.art + " missing, not built"); return null; }
            GameObject go;
            try { go = d.kind == ObjKind.Trap ? BuildTrap(d, sheet) : BuildProp(d, sheet); }
            catch (Exception e) { FurtherCore.Log.LogError("Object " + d.id + " build failed: " + e); return null; }
            if (go == null) return null;
            Placement(go, d, sheet);
            if (d.customize != null)
            {
                try { d.customize(go); } catch (Exception e) { FurtherCore.Log.LogError("Object " + d.id + " customize: " + e); }
            }
            Defs[d.id] = d; Built[d.id] = go; s_byPrefab[go] = d; s_byName[go.name] = d;
            FxFactory.OnSpawn[go] = inst =>
            {
                if (d.kind != ObjKind.Trap)
                {
                    var mo = inst.GetComponent<ModObject>() ?? inst.AddComponent<ModObject>();
                    mo.Init(d);
                }
                if (d.onSpawned != null) d.onSpawned(inst);
            };
            // vault page (works before or after the vault is built)
            try
            {
                var pic = sheet.Has("Vault") ? "Vault" : sheet.Has("Idle") ? "Idle" : sheet.Has("Active") ? "Active" : null;
                var clip = pic != null ? new ClipBuilder(sheet, pic, go.name + "VaultClip").Loop().Build() : null;
                // the vault line, then the numbers (the tip lines), like vanilla item pages
                string desc = d.vault;
                if (!string.IsNullOrEmpty(d.tip1)) desc += "\n" + d.tip1 + (string.IsNullOrEmpty(d.tip2) ? string.Empty : ". " + d.tip2);
                Vault.AddObject(go, d.name, desc, clip);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Object " + d.id + " vault page: " + e.Message); }
            FurtherCore.Log.LogInfo("Object built: " + go.name + " (" + d.kind + ")");
            return go;
        }

        static exSpriteAnimClip Clip(SpriteSheet sh, string anim, string name, bool loop)
        {
            if (!sh.Has(anim)) return null;
            var cb = new ClipBuilder(sh, anim, name);
            if (loop) cb.Loop(); else cb.Once();
            return cb.Build();
        }

        static AnimState State(string name, exSpriteAnimClip clip, string next, AudioCue sound = null, float time = 0f)
        {
            var s = new AnimState
            {
                m_name = name, m_animation = clip, m_sound = sound,
                m_transitionOnFinish = !string.IsNullOrEmpty(next) && time <= 0f, m_nextState = next ?? string.Empty,
                m_turnOn = new List<GameObject>(), m_turnOff = new List<GameObject>(), m_animate = new List<AnimStateActionAnimate>(),
                m_actions = new List<AnimStateAction>(),
            };
            s.m_transitionOnTime = new MinMaxRange(time);
            return s;
        }

        static void Skin(GameObject go, SpriteSheet sh, exSpriteAnimClip first)
        {
            var spr = go.GetComponent<exSprite>();
            if (spr != null && first != null)
            {
                spr.SetSprite(sh.atlas, first.frameInfos[0].index);
                var r = go.GetComponent<Renderer>();
                if (r != null) r.sharedMaterial = sh.atlas.material;
                spr.anchor = exPlane.Anchor.BotCenter;
                spr.useTextureOffset = false;
                spr.offset = MonsterFactory.FeetOffset(sh);
                spr.color = Color.white;
            }
            var tint = go.GetComponent<ColorTinter>();
            if (tint != null) R.Set(tint, "m_tint", eColour.None);   // m_tint is an eColour, not a float
        }

        /// <summary>Use / Touch: the vanilla fountain without its PropActionable and vanilla shadow, wearing the mod sheet.</summary>
        static GameObject BuildProp(ObjectDef d, SpriteSheet sh)
        {
            var go = FxFactory.Clone("PropActionable_Fountain", d.PrefabName);
            if (go == null) return null;
            FxFactory.Templates.Remove(d.PrefabName);
            foreach (var pa in go.GetComponents<PropActionable>()) UnityEngine.Object.DestroyImmediate(pa);
            var sh0 = go.transform.Find("Shadow");
            if (sh0 != null) UnityEngine.Object.DestroyImmediate(sh0.gameObject);
            var states = new List<AnimState>();
            var idle = Clip(sh, "Idle", go.name + "Idle", true);
            states.Add(State("Idle", idle, null));
            var anims = new List<exSpriteAnimClip> { idle };
            foreach (var a in sh.manifest.anims)
            {
                if (a.name == "Idle" || a.name == "Vault") continue;
                bool once = a.name == "Use" || d.once.Contains(a.name);
                string next;
                if (!d.then.TryGetValue(a.name, out next)) next = a.name == "Use" ? "Idle" : null;
                var c = Clip(sh, a.name, go.name + a.name, !once);
                anims.Add(c);
                states.Add(State(a.name, c, next));
            }
            var asm = go.GetComponent<AnimStateMachine>();
            asm.m_states = states;
            var anim = go.GetComponent<exSpriteAnimation>();
            anim.animations = anims;
            anim.defaultAnimation = idle;
            anim.playAutomatically = false;
            Skin(go, sh, idle);
            // action range (trigger, layer Zone) and the solid footprint (child "Body", layer Prop)
            var box = go.GetComponent<BoxCollider>();
            if (box != null) { box.size = new Vector3(d.useBox.x, d.useBox.y, 200f); box.center = new Vector3(0f, 2f, 0f); box.enabled = d.kind == ObjKind.Use; }
            var body = go.transform.Find("Body");
            if (body != null)
            {
                if (d.bodySize.x <= 0f) UnityEngine.Object.DestroyImmediate(body.gameObject);
                else
                {
                    foreach (var c in body.GetComponents<Collider>()) UnityEngine.Object.DestroyImmediate(c);
                    var bc = body.gameObject.AddComponent<BoxCollider>();
                    bc.size = new Vector3(d.bodySize.x, d.bodySize.y, 200f);
                    bc.center = new Vector3(0f, d.bodyY, 0f);
                }
            }
            var ret = go.transform.Find("Select_Reticule");
            if (ret != null)
            {
                float h = TopOf(sh, "Idle");
                ret.localPosition = new Vector3(0f, h + 4f, ret.localPosition.z);
                ret.gameObject.SetActive(false);
            }
            return go;
        }

        /// <summary>Opaque height above the floor point of an anim's first frame (for indicators).</summary>
        public static float TopOf(SpriteSheet sh, string anim)
        {
            try
            {
                var a = sh.Anim(anim);
                if (a == null || a.frames.Length == 0) return 16f;
                var tex = sh.atlas.texture;
                int cols = sh.manifest.cols, cw = sh.manifest.cellW, ch = sh.manifest.cellH;
                int f = a.frames[0];
                int x0 = (f % cols) * cw, yTop = (f / cols) * ch;
                for (int row = 0; row < ch; row++)
                    for (int x = 0; x < cw; x++)
                        if (tex.GetPixel(x0 + x, tex.height - 1 - (yTop + row)).a > 0.1f) return (ch - 2) - row;
            }
            catch { }
            return 16f;
        }

        /// <summary>Trap: a vanilla dart turret clone (PropTrap + BotTrap + the vanilla indicators) with new states and attacks.</summary>
        static GameObject BuildTrap(ObjectDef d, SpriteSheet sh)
        {
            var go = FxFactory.Clone("TrapProjectileSingle", d.PrefabName);
            if (go == null) return null;
            FxFactory.Templates.Remove(d.PrefabName);
            var trap = go.GetComponent<PropTrap>();
            var asm = go.GetComponent<AnimStateMachine>();
            var old = asm.m_states;
            Func<string, AudioCue> snd = n => { var s = old.Find(x => x.m_name == n); return s != null ? s.m_sound : null; };
            var inactive = Clip(sh, "Inactive", go.name + "Inactive", true);
            var activate = Clip(sh, "Activate", go.name + "Activate", false);
            var active = Clip(sh, "Active", go.name + "Active", true);
            var deactivate = Clip(sh, "Deactivate", go.name + "Deactivate", false);
            var disabled = Clip(sh, "Disabled", go.name + "Disabled", true) ?? inactive;
            // attacks: one clip per attack (with its AnimAttack events), every effect in one flat list
            var vAttacks = R.Get<List<AttackData>>(trap, "m_attacks");
            var vEffects = R.Get<List<DamageEffectData>>(trap, "m_attackDamageEffects");
            var attacks = new List<AttackData>();
            var effects = new List<DamageEffectData>();
            var clips = new List<exSpriteAnimClip> { inactive, activate, active, deactivate };
            if (disabled != inactive) clips.Add(disabled);
            if (d.attacks.Count == 0) d.attacks.Add(new ObjTrapAttack());
            for (int ai = 0; ai < d.attacks.Count; ai++)
            {
                var at = d.attacks[ai];
                var cb = new ClipBuilder(sh, at.anim, go.name + at.anim + ai).Once();
                foreach (var e in at.effects)
                {
                    var ed = R.Clone(vEffects[0]);
                    ed.m_object = e.fx;
                    ed.m_attach = e.attach;
                    ed.m_detatchOnAnimEnd = false;
                    ed.m_destroyOnAnimEnd = false;
                    ed.m_offsetX = new MinMaxRange(e.x);
                    ed.m_offsetY = new MinMaxRange(e.y);     // y up, from the node (vanilla dart: node 0,7 + offset -7.5 = the floor)
                    ed.m_angle = new MinMaxRange(e.angle);
                    ed.m_spawnDelay = new MinMaxRange(e.delay);
                    ed.m_rotateOffsetX = true;
                    ed.m_spawnPoint = DamageEffectData.eSpawnPoint.Node;
                    cb.Ev(e.frame, "AnimAttack", effects.Count);
                    effects.Add(ed);
                }
                var clip = cb.Build();
                clips.Add(clip);
                var ad = R.Clone(vAttacks[0]);
                ad.m_animationFront = clip;
                ad.m_animAngles = new List<AttackDataAnimAngle>();
                ad.m_cooldown = at.cooldown;
                attacks.Add(ad);
            }
            R.Set(trap, "m_attacks", attacks);
            R.Set(trap, "m_attackDamageEffects", effects);
            R.Set(trap, "m_attackOrderType", Attacks.eAttackOrderType.InOrder);
            R.Set(trap, "m_comboResetTime", 0f);
            R.Set(trap, "m_directional", d.aims);
            R.Set(trap, "m_attackAnglesList", d.angles ?? new float[0]);
            R.Set(trap, "m_attackAngleSnap", d.snap);
            R.Set(trap, "m_attackAngleInitial", d.startAngle);
            R.Set(trap, "m_attackSpawnNode", d.node);
            R.Set(trap, "m_difficulty", d.difficulty);
            R.Set(trap, "m_actionableIndicatorOffset", d.enterArrowY);
            R.Set(trap, "m_directionAttackOverride", new MinMaxRange[0]);
            R.Set(trap, "m_directionIndicatorOverride", new GameObject[0]);
            R.Set(trap, "m_showIndicator", d.aims);
            asm.m_states = new List<AnimState>
            {
                State("Inactive", inactive, null),
                State("Activate", activate, "Active", snd("Activate")),
                State("Active", active, null),
                State("Action", attacks[0].m_animationFront, "Active", snd("Action")),
                State("Deactivate", deactivate, "Inactive", snd("Deactivate")),
                State("Disabled", disabled, null),
            };
            var anim = go.GetComponent<exSpriteAnimation>();
            anim.animations = clips;
            anim.defaultAnimation = inactive;
            anim.playAutomatically = false;
            Skin(go, sh, inactive);
            var body = go.transform.Find("Body");
            if (body != null)
            {
                var bc = body.GetComponent<BoxCollider>();
                if (d.bodySize.x <= 0f) UnityEngine.Object.DestroyImmediate(body.gameObject);
                else if (bc != null)
                {
                    body.localPosition = new Vector3(0f, 0f, body.localPosition.z);
                    bc.size = new Vector3(d.bodySize.x, d.bodySize.y, 150f);
                    bc.center = new Vector3(0f, d.bodyY, 0f);
                }
            }
            return go;
        }

        /// <summary>Half-width and height above the floor point of an anim's first frame (opaque pixels only, no shadow).</summary>
        public static Vector2 ArtExtent(SpriteSheet sh, string anim)
        {
            try
            {
                var a = sh != null ? sh.Anim(anim) : null;
                if (a == null || a.frames.Length == 0) return new Vector2(8f, 16f);
                var tex = sh.atlas.texture;
                int cols = sh.manifest.cols, cw = sh.manifest.cellW, ch = sh.manifest.cellH;
                int f = a.frames[0], x0 = (f % cols) * cw, yTop = (f / cols) * ch;
                float half = 0f, top = 0f, fx = cw / 2;
                for (int row = 0; row < ch; row++)
                    for (int x = 0; x < cw; x++)
                        if (tex.GetPixel(x0 + x, tex.height - 1 - (yTop + row)).a > 0.75f)
                        {
                            half = Mathf.Max(half, Mathf.Abs(x + 0.5f - fx));
                            top = Mathf.Max(top, (ch - 2) - row);
                        }
                return new Vector2(Mathf.Ceil(half), top);
            }
            catch { return new Vector2(8f, 16f); }
        }

        /// <summary>
        /// The vanilla SpawnConstraints: the four minimum wall distances are also the footprint the room reserves for the
        /// object (Room.SpawnInRoom adds GetBoundsRect to its prop rects, so nothing else is placed over it, and other
        /// rects keep it off). They always cover the whole art plus a 2 px margin, whatever the placement.
        /// </summary>
        static void Placement(GameObject go, ObjectDef d, SpriteSheet sh)
        {
            var sc = go.GetComponent<SpawnConstraints>();
            if (sc == null) return;
            sc.enabled = true;
            var ext = ArtExtent(sh, d.kind == ObjKind.Trap ? "Inactive" : "Idle");
            float half = Mathf.Max(ext.x, d.bodySize.x * 0.5f) + 2f;               // art half-width + margin
            float down = Mathf.Max(3f, d.bodyY + d.bodySize.y * 0.5f + 2f);          // the footprint below the floor point
            float up = Mathf.Max(ext.y * 0.6f, d.bodyY + d.bodySize.y) + 2f;         // depth sorting lets the top overlap a little
            float useHalf = d.kind == ObjKind.Use ? d.useBox.x * 0.5f : 0f;
            R.Set(sc, "m_maxDuplicates", 0);
            R.Set(sc, "m_snap", 1f);
            R.Set(sc, "m_zDepth", 0f);
            switch (d.spawn.place)
            {
                case ObjPlace.Wall:      // hugging a wall like the vanilla turrets
                    R.Set(sc, "m_cornerWeight", 7); R.Set(sc, "m_centerWeight", 0);
                    R.Set(sc, "m_distLeft", new MinMaxRange(Mathf.Max(6f, half), 50f));
                    R.Set(sc, "m_distRight", new MinMaxRange(Mathf.Max(6f, half), 50f));
                    R.Set(sc, "m_distTop", new MinMaxRange(Mathf.Max(6f, up), 50f));
                    R.Set(sc, "m_distBottom", new MinMaxRange(Mathf.Max(6f, down), 50f));
                    R.Set(sc, "m_nonSquareMaxDist", 45f);
                    break;
                case ObjPlace.Open:      // in the open like the vanilla fountain (30 / 18): away from the walls and doors
                    R.Set(sc, "m_cornerWeight", 0); R.Set(sc, "m_centerWeight", 5);
                    R.Set(sc, "m_distLeft", new MinMaxRange(Mathf.Max(24f, half + 12f, useHalf + 4f), 1000f));
                    R.Set(sc, "m_distRight", new MinMaxRange(Mathf.Max(24f, half + 12f, useHalf + 4f), 1000f));
                    R.Set(sc, "m_distTop", new MinMaxRange(Mathf.Max(18f, up + 6f), 1000f));
                    R.Set(sc, "m_distBottom", new MinMaxRange(Mathf.Max(18f, down + 6f), 1000f));
                    R.Set(sc, "m_nonSquareMaxDist", 970f);
                    break;
                default:
                    R.Set(sc, "m_cornerWeight", 2); R.Set(sc, "m_centerWeight", 2);
                    R.Set(sc, "m_distLeft", new MinMaxRange(Mathf.Max(12f, half), 1000f));
                    R.Set(sc, "m_distRight", new MinMaxRange(Mathf.Max(12f, half), 1000f));
                    R.Set(sc, "m_distTop", new MinMaxRange(Mathf.Max(12f, up), 1000f));
                    R.Set(sc, "m_distBottom", new MinMaxRange(Mathf.Max(12f, down), 1000f));
                    R.Set(sc, "m_nonSquareMaxDist", 970f);
                    break;
            }
            R.Set(sc, "m_spawnFromTopLeft", true); R.Set(sc, "m_spawnFromTopRight", true);
            R.Set(sc, "m_spawnFromBottomLeft", true); R.Set(sc, "m_spawnFromBottomRight", true);
            R.Set(sc, "m_nonSquareAngleAllowed", new MinMaxRange(0f, 360f));
            R.Set(sc, "m_debugRoomShape", null);
        }

        // ------------------------------------------------------------------ helpers for packs
        static readonly Dictionary<string, AudioCue> s_cues = new Dictionary<string, AudioCue>();
        /// <summary>A vanilla AudioCue by name, or null.</summary>
        public static AudioCue Cue(string name)
        {
            if (string.IsNullOrEmpty(name)) return null;
            AudioCue c;
            if (s_cues.TryGetValue(name, out c)) return c;           // misses are cached too: one scan per name, ever
            foreach (var a in Resources.FindObjectsOfTypeAll<AudioCue>()) if (a.name == name) { c = a; break; }
            if (c == null) FurtherCore.Log.LogWarning("ObjectKit: no vanilla sound " + name);
            s_cues[name] = c;
            return c;
        }

        /// <summary>Play a vanilla AudioCue by name at a transform.</summary>
        public static void PlaySound(string cue, Transform at)
        {
            var c = Cue(cue);
            if (c == null) return;
            try { SystemAudio.Play(c, at); } catch { }
        }

        /// <summary>A player met this object: its vault page is found, and its secret if it has one. Bots find nothing.</summary>
        public static void Discovered(PlayerData pd, GameObject inst, ObjectDef d)
        {
            if (pd == null || pd.IsBot) return;
            try { SystemLibrary.OnEntryFound(pd, inst); } catch { }
            if (!string.IsNullOrEmpty(d.secret)) { try { Secrets.Found(d.secret); } catch { } }
        }

        static readonly HashSet<string>[] s_tipped = new HashSet<string>[8];
        static Room s_tipRoom;
        /// <summary>The object's two tip lines in the HUD tip panel, once per player per object kind per room.</summary>
        public static void TipOnce(PlayerData pd, ObjectDef d, Component near)
        {
            if (pd == null || pd.IsBot || d == null || string.IsNullOrEmpty(d.tip1) || !MonsterTips.Enabled) return;
            int id = pd.Id;
            if (id < 0 || id >= s_tipped.Length) return;
            Room room = null;
            try { room = SystemLevel.GetCurrentRoom(); } catch { }
            if (room != s_tipRoom) { s_tipRoom = room; foreach (var s in s_tipped) if (s != null) s.Clear(); }
            var set = s_tipped[id] ?? (s_tipped[id] = new HashSet<string>());
            if (!set.Add(d.id)) return;
            Color colour = Color.white;
            try { if (pd.Setup != null) colour = pd.Setup.m_colourGUI; } catch { }
            colour.a = 1f;
            string who = null;
            try { if (SystemPlayers.GetNumHumanPlayers() > 1) who = "P" + (id + 1); } catch { }
            try { TipView.Get().Show(id, who != null ? who + " - " + d.name : d.name, d.tip1, d.tip2 ?? string.Empty, null, colour); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Object tip: " + e.Message); }
        }

        // ------------------------------------------------------------------ timed and floor-long buffs on a player
        /// <summary>
        /// A multiplier on one of the player's modifiers, removed after <paramref name="seconds"/> (0 = until the next floor),
        /// and always when this player stops being the hero or the game ends. <paramref name="source"/> names it (re-adding
        /// replaces it). onEnd runs when it is removed (switch indicators off there).
        /// </summary>
        public static void Buff(PlayerData pd, string source, PlayerModifier.eType type, float mult, float seconds, Action onEnd = null)
        {
            if (pd == null || pd.GameData == null) return;
            pd.GameData.RemoveModifiers(source);
            pd.GameData.AddBaseModifier(source, new PlayerModifier { m_modify = type, m_type = ValueModifier.eModifierType.Multiply, m_value = mult });
            var b = new BuffRec { pd = pd, source = source, until = seconds > 0f ? Time.time + seconds : -1f, onEnd = onEnd };
            s_buffs.RemoveAll(x => x.pd == pd && x.source == source);
            s_buffs.Add(b);
            BuffTicker.Ensure();
        }

        class BuffRec { public PlayerData pd; public string source; public float until; public Action onEnd; }
        static readonly List<BuffRec> s_buffs = new List<BuffRec>();

        internal static void TickBuffs()
        {
            for (int i = s_buffs.Count - 1; i >= 0; i--)
                if (s_buffs[i].until > 0f && Time.time >= s_buffs[i].until) End(i);
        }

        static void End(int i)
        {
            var b = s_buffs[i];
            s_buffs.RemoveAt(i);
            try { if (b.pd != null && b.pd.GameData != null) b.pd.GameData.RemoveModifiers(b.source); } catch { }
            if (b.onEnd != null) { try { b.onEnd(); } catch { } }
        }

        /// <summary>A coroutine that outlives the object that started it (heal-over-time, pulls...).</summary>
        public static Coroutine Run(System.Collections.IEnumerator e) { return e == null ? null : BuffTicker.Inst.StartCoroutine(e); }

        /// <summary>Is this buff (by source name) on this player now?</summary>
        public static bool HasBuff(PlayerData pd, string source) { return s_buffs.Exists(x => x.pd == pd && x.source == source); }

        /// <summary>Drop one buff of one player now (its onEnd runs).</summary>
        public static void Unbuff(PlayerData pd, string source)
        {
            for (int i = s_buffs.Count - 1; i >= 0; i--) if (s_buffs[i].pd == pd && s_buffs[i].source == source) End(i);
        }

        /// <summary>Drop every buff of one player (null = all).</summary>
        public static void ClearBuffs(PlayerData pd)
        {
            for (int i = s_buffs.Count - 1; i >= 0; i--) if (pd == null || s_buffs[i].pd == pd) End(i);
        }

        // ------------------------------------------------------------------ spawning
        static int s_floor = -1;
        static readonly Dictionary<string, int> s_floorCount = new Dictionary<string, int>();

        /// <summary>A new game: forget the last game's floor caps and buffs (it may start on the same floor number).</summary>
        internal static void OnGameStart()
        {
            s_floor = -1;
            s_floorCount.Clear();
            ClearBuffs(null);
        }

        internal static void OnFloorStart()
        {
            int lvl = 0;
            try { lvl = SystemGame.GetLevel(); } catch { }
            if (lvl == s_floor) return;
            s_floor = lvl;
            s_floorCount.Clear();
            ClearBuffs(null);
        }

        /// <summary>The current floor's environment, and its object name.</summary>
        public static string EnvOf(out ObjEnv env)
        {
            env = ObjEnv.Dungeon;
            string n = string.Empty;
            try
            {
                var e = R.Get<Environment>(Singleton<SystemLevel>.Get, "m_environment");
                n = e != null ? e.gameObject.name : string.Empty;
            }
            catch { }
            if (n.Contains("Crypt")) env = ObjEnv.Crypt;
            else if (n.Contains("Mines")) env = ObjEnv.Mines;
            else if (n.Contains("Caves")) env = ObjEnv.Caves;
            return n;
        }

        /// <summary>What kind of room this is, for spawn rules.</summary>
        public static ObjRoom KindOf(Room room)
        {
            ObjRoom k = 0;
            if (room.m_corridor) k |= ObjRoom.Corridor;
            if (room.m_hasEnemies) k |= ObjRoom.Fight;
            if (room.GetComponentInChildren<PropMonsterStatue>() != null) k |= ObjRoom.Statue;
            if (room.m_hasTraps) k |= ObjRoom.Trapped;
            if (room.HasStairs()) k |= ObjRoom.Stairs;
            if ((k & (ObjRoom.Corridor | ObjRoom.Fight | ObjRoom.Statue)) == 0) k |= ObjRoom.Quiet;
            return k;
        }

        internal static void OnRoomContent(SystemLevel lvl, Room room)
        {
            if (!Enabled || room == null || Built.Count == 0) return;
            try { if (SystemMenu.GetAttractMode() || SystemMenu.GetChallengeMode()) return; } catch { }
            if (CompatBosses.IsBossArena(room) || room.m_isPowerupRoom || room.m_isPortalRoom) return;
            try
            {
                var gen = R.Get<MapGenerator>(lvl, "m_mapGenerator");
                if (gen != null && gen.GetRootRoom() == room) return;
            }
            catch { }
            OnFloorStart();
            var kind = KindOf(room);
            ObjEnv env;
            EnvOf(out env);
            int lvlNo = 1;
            try { lvlNo = SystemGame.GetLevel(); } catch { }

            Cfg();
            var forced = new List<ObjectDef>();
            if (s_force != null && !string.IsNullOrEmpty(s_force.Value))
                foreach (var part in s_force.Value.Split(','))
                {
                    ObjectDef fd;
                    if (Defs.TryGetValue(part.Trim(), out fd)) forced.Add(fd);
                }
            if (forced.Count > 0)
            {
                Place(room, forced[UnityEngine.Random.Range(0, forced.Count)]);
                return;
            }
            foreach (var d in new List<ObjectDef>(Defs.Values))
                if (d.spawn != null && d.spawn.chance > 0f && Allowed(d, kind, env, lvlNo) && UnityEngine.Random.value < d.spawn.chance)
                {
                    Place(room, d);
                    return;
                }
            if (UnityEngine.Random.value >= RoomChance) return;
            int n = UnityEngine.Random.value < SecondChance ? 2 : 1;
            for (int i = 0; i < n; i++)
            {
                var pick = Pick(kind, env, lvlNo);
                if (pick == null) return;
                Place(room, pick);
            }
        }

        /// <summary>Whether the def's spawn rule allows this room kind, environment and floor, and its floor cap has room.</summary>
        static bool Allowed(ObjectDef d, ObjRoom kind, ObjEnv env, int floor)
        {
            var s = d.spawn;
            if (floor < s.minFloor || floor > s.maxFloor) return false;
            if ((s.env & env) == 0) return false;
            if ((s.rooms & kind) == 0) return false;
            if ((s.notRooms & kind) != 0) return false;
            if ((kind & ObjRoom.Corridor) != 0 && (s.rooms & ObjRoom.Corridor) == 0) return false;   // corridors only for corridor objects
            int c;
            s_floorCount.TryGetValue(d.id, out c);
            return s.maxPerFloor <= 0 || c < s.maxPerFloor;
        }

        static ObjectDef Pick(ObjRoom kind, ObjEnv env, int floor)
        {
            float total = 0f;
            var list = new List<ObjectDef>();
            foreach (var d in Defs.Values)
            {
                if (d.spawn == null || d.spawn.weight <= 0f || !Allowed(d, kind, env, floor)) continue;
                list.Add(d); total += d.spawn.weight;
            }
            if (list.Count == 0) return null;
            float r = UnityEngine.Random.Range(0f, total);
            foreach (var d in list) { r -= d.spawn.weight; if (r <= 0f) return d; }
            return list[list.Count - 1];
        }

        static GameObject Place(Room room, ObjectDef d)
        {
            var go = SpawnIn(d.id, room);
            if (go == null) return null;
            int c;
            s_floorCount.TryGetValue(d.id, out c);
            s_floorCount[d.id] = c + 1;
            if (d.spawn.pair)
            {
                var b = SpawnIn(d.id, room);
                var ma = go.GetComponent<ModObject>();
                var mb = b != null ? b.GetComponent<ModObject>() : null;
                if (ma != null && mb != null) { ma.partner = mb; mb.partner = ma; }
                else if (b == null) { go.Despawn(); return null; }   // a pad without its twin would do nothing
            }
            return go;
        }

        /// <summary>Place a registered object somewhere free in a room (the vanilla prop placement). Null if no room for it,
        /// and always null in a boss room (any mod's arena included: their layouts and pathfinding are not ours to change).</summary>
        public static GameObject SpawnIn(string id, Room room)
        {
            GameObject prefab;
            if (room == null || CompatBosses.IsBossArena(room) || !Built.TryGetValue(id, out prefab)) return null;
            try { return room.SpawnInRoom(prefab); }
            catch (Exception e) { FurtherCore.Log.LogError("Object " + id + " spawn: " + e); return null; }
        }

        /// <summary>Place a registered object at a point in a room (never in a boss room, as <see cref="SpawnIn"/>).</summary>
        public static GameObject SpawnAt(string id, Room room, Vector2 pos)
        {
            GameObject prefab;
            if (room == null || CompatBosses.IsBossArena(room) || !Built.TryGetValue(id, out prefab)) return null;
            try { return room.SpawnInRoom(prefab, new Vector3(pos.x, pos.y, 0f)); }
            catch (Exception e) { FurtherCore.Log.LogError("Object " + id + " spawn: " + e); return null; }
        }

        // ------------------------------------------------------------------ self-test
        /// <summary>Self-test: every def built, named, tipped within limits, and its prefab well formed.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            foreach (var kv in Defs)
            {
                var d = kv.Value;
                GameObject go;
                if (!Built.TryGetValue(kv.Key, out go) || go == null) { bad("object " + kv.Key + " has no prefab"); continue; }
                if (string.IsNullOrEmpty(d.name) || string.IsNullOrEmpty(d.vault)) bad("object " + kv.Key + " has no name or vault line");
                if (go.GetComponent<SpawnConstraints>() == null) bad("object " + kv.Key + " has no SpawnConstraints");
                foreach (var t in new[] { d.name, d.vault, d.tip1, d.tip2, d.actionText })
                {
                    if (t == null) continue;
                    if (t.IndexOfAny("%{|}~[]".ToCharArray()) >= 0) bad("object " + kv.Key + " text has a forbidden character: " + t);
                }
                if (d.tip1 != null && d.tip1.Length > 60) bad("object " + kv.Key + " tip1 longer than 60");
                if (d.tip2 != null && d.tip2.Length > 60) bad("object " + kv.Key + " tip2 longer than 60");
                if (d.kind == ObjKind.Trap)
                {
                    var trap = go.GetComponent<PropTrap>();
                    if (trap == null) { bad("trap " + kv.Key + " lost its PropTrap"); continue; }
                    var fx = R.Get<List<DamageEffectData>>(trap, "m_attackDamageEffects");
                    if (fx == null || fx.Count == 0 || fx.Exists(e => e.m_object == null)) bad("trap " + kv.Key + " has a missing effect");
                    if (go.GetComponent<BotTrap>() == null) bad("trap " + kv.Key + " has no BotTrap (bots could not use it)");
                }
                else
                {
                    if (go.GetComponent<PropActionable>() != null) bad("object " + kv.Key + " still has the vanilla PropActionable");
                    var asm = go.GetComponent<AnimStateMachine>();
                    if (asm == null || asm.GetStateId("Idle") < 0) bad("object " + kv.Key + " has no Idle state");
                }
            }
        }
    }

    // ------------------------------------------------------------------ hooks
    /// <summary>After the game fills a room on first entry: maybe add mod objects.</summary>
    [HarmonyPatch(typeof(SystemLevel), "SpawnRoomContent")]
    static class Patch_ObjectsRoomContent
    {
        static void Postfix(SystemLevel __instance, Room room)
        {
            try { ObjectKit.OnRoomContent(__instance, room); }
            catch (Exception e) { FurtherCore.Log.LogError("Objects room spawn failed: " + e); }
        }
    }

    /// <summary>A new floor: per-floor caps and floor-long buffs reset.</summary>
    [HarmonyPatch(typeof(PlayerData), "OnLevelStart")]
    static class Patch_ObjectsLevelStart
    {
        static void Postfix() { try { ObjectKit.OnFloorStart(); } catch { } }
    }

    [HarmonyPatch(typeof(SystemGame), "OnStartGame")]
    static class Patch_ObjectsGameStart
    {
        static void Postfix() { try { ObjectKit.OnGameStart(); } catch { } }
    }

    /// <summary>Losing (or gaining) the hero, or the game ending, drops that player's object buffs.</summary>
    [HarmonyPatch(typeof(PlayerData), "OnHeroChange")]
    static class Patch_ObjectsHeroChange
    {
        static void Postfix(PlayerData __instance) { try { ObjectKit.ClearBuffs(__instance); } catch { } }
    }

    [HarmonyPatch(typeof(PlayerData), "OnGameComplete")]
    static class Patch_ObjectsGameEnd
    {
        static void Postfix() { try { ObjectKit.ClearBuffs(null); } catch { } }
    }

    /// <summary>A ghost entering a mod trap: its tip, and its secret.</summary>
    [HarmonyPatch(typeof(PropTrap), "OnAction")]
    static class Patch_ObjectsTrapEnter
    {
        static void Postfix(PropTrap __instance, Player actioner, bool __result)
        {
            if (!__result || actioner == null) return;
            try
            {
                var d = ObjectKit.DefOf(__instance.gameObject);
                if (d == null) return;
                var pd = actioner.GetPlayerData();
                ObjectKit.TipOnce(pd, d, __instance);
                if (!string.IsNullOrEmpty(d.secret) && pd != null && !pd.IsBot) Secrets.Found(d.secret);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Object trap tip: " + e.Message); }
        }
    }
}
