using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// Builds mod monsters from <see cref="MonsterDef"/>s: clones the vanilla base prefab, swaps every clip for one cut
    /// from the mod sheet, fits the portrait, hurtbox and health bar to the art, applies the stats, and runs the kit.
    /// </summary>
    public static class MonsterFactory
    {
        static GameObject s_holder;
        static readonly Dictionary<string, Player> s_vanilla = new Dictionary<string, Player>();

        /// <summary>Every built mod monster by def id (not prefab name).</summary>
        public static readonly Dictionary<string, Player> Built = new Dictionary<string, Player>();
        /// <summary>Multiplier on hits against the hero, by prefab name: the tier rule times the def's own
        /// <see cref="MonsterDef.damageMult"/>. Every evolved monster has an entry.</summary>
        public static readonly Dictionary<string, float> DamageMult = new Dictionary<string, float>();
        /// <summary>The tier of every built monster (1 to 3, see <see cref="TierRules.Of"/>), by prefab name.</summary>
        public static readonly Dictionary<string, int> Tier = new Dictionary<string, int>();

        // inactive and never destroyed: clones parked under it act as prefabs (no Awake, not in any scene)
        internal static GameObject Holder
        {
            get
            {
                if (s_holder == null)
                {
                    s_holder = new GameObject("CrawlMod_Prefabs");
                    s_holder.SetActive(false);
                    UnityEngine.Object.DontDestroyOnLoad(s_holder);
                }
                return s_holder;
            }
        }

        /// <summary>Index vanilla monster prefabs. Returns false until they are loaded.</summary>
        internal static bool TryIndexVanilla()
        {
            if (s_vanilla.ContainsKey("EnemyGnome")) return true;
            s_vanilla.Clear();
            foreach (var p in Resources.FindObjectsOfTypeAll<Player>())
            {
                // prefabs live outside scenes; skip instances ("(Clone)") and anything parented (our own holder)
                if (p.gameObject.name.EndsWith("(Clone)")) continue;
                if (p.transform.parent != null) continue;
                if (!s_vanilla.ContainsKey(p.gameObject.name)) s_vanilla[p.gameObject.name] = p;
            }
            if (s_vanilla.ContainsKey("EnemyGnome"))
            {
                FurtherCore.Log.LogInfo("Indexed " + s_vanilla.Count + " vanilla Player prefabs");
                return true;
            }
            return false;
        }

        /// <summary>The vanilla monster prefab named <paramref name="name"/> (e.g. "EnemyGnome"), or null.</summary>
        public static Player FindVanilla(string name)
        {
            Player r;
            s_vanilla.TryGetValue(name, out r);
            return r;
        }

        /// <summary>
        /// Copy a prefab without running its Awake, parked under an inactive holder so the copy acts as a prefab of its
        /// own (spawn it with SystemPool). Name mod prefabs "Mod..." so Online Crawl and the rest of Core recognise them.
        /// </summary>
        public static GameObject ClonePrefab(GameObject prefab, string newName)
        {
            bool was = prefab.activeSelf;
            prefab.SetActive(false);
            var clone = UnityEngine.Object.Instantiate(prefab);
            prefab.SetActive(was);
            clone.name = newName;
            clone.transform.SetParent(Holder.transform, false);
            clone.SetActive(was);
            return clone;
        }

        /// <summary>Build the monster described by <paramref name="def"/>. Returns its prefab's Player, or null (logged).</summary>
        public static Player Build(MonsterDef def)
        {
            var basePlayer = FindVanilla(def.basePrefab);
            if (basePlayer == null) { FurtherCore.Log.LogError("Base prefab not found: " + def.basePrefab); return null; }
            var go = ClonePrefab(basePlayer.gameObject, def.PrefabName);
            var p = go.GetComponent<Player>();

            // ---- art ----
            var sheet = SpriteSheets.Get(def.art ?? def.id);
            var map = new Dictionary<UnityEngine.Object, UnityEngine.Object>();
            if (sheet != null)
            {
                Reskin(p, sheet, map, def.aliases, def.kit != null);
                int n = R.RemapReferences(go, map);
                FurtherCore.Log.LogInfo(def.id + ": remapped " + n + " clip references");
                var spr = go.GetComponent<exSprite>();
                var idle = R.Get<exSpriteAnimClip>(p, "m_animationIdle");
                if (spr != null && idle != null && idle.frameInfos.Count > 0)
                {
                    spr.SetSprite(sheet.atlas, idle.frameInfos[0].index);
                    // menus (the evolution hands, previews) copy the prefab renderer's material directly;
                    // on an inactive prefab SetSprite may leave the vanilla atlas material in place
                    var rend = go.GetComponent<Renderer>();
                    if (rend != null && sheet.atlas.material != null) rend.sharedMaterial = sheet.atlas.material;
                    spr.anchor = exPlane.Anchor.BotCenter;
                    spr.offset = FeetOffset(sheet);
                }
                ReportUnmappedSprites(go, sheet);
                FitPortrait(p, sheet);
            }

            // ---- stats ----
            if (def.health > 0f)
            {
                var h = go.GetComponent<Health>();
                if (h != null) R.Set(h, "m_healthMax", def.health);
            }
            if (TierRules.IsStarter(def.evolveCost) && TierRules.StarterMinHealth > 0f)
            {
                var h = go.GetComponent<Health>();
                if (h != null && R.Get<float>(h, "m_healthMax") < TierRules.StarterMinHealth) R.Set(h, "m_healthMax", TierRules.StarterMinHealth);
            }
            float healthMult = TierRules.Health(def.evolveCost);
            if (Math.Abs(healthMult - 1f) > 0.001f)
            {
                var h = go.GetComponent<Health>();
                if (h != null) R.Set(h, "m_healthMax", Mathf.Round(R.Get<float>(h, "m_healthMax") * healthMult * 2f) / 2f);
            }
            if (Math.Abs(def.speedMult - 1f) > 0.001f)
            {
                var mv = go.GetComponent<PlayerMovement>();
                if (mv != null) R.Set(mv, "m_speedMax", R.Get<float>(mv, "m_speedMax") * def.speedMult);
            }
            if (def.evolveCost >= 0f) R.Set(p, "m_evolveCost", def.evolveCost);

            if (!def.keepEvolutions) R.Set(p, "m_evolveTo", new Player[0]);
            if (!def.keepEvolutions) R.Set(p, "m_evolveToCostOverride", Array.CreateInstance(R.F(typeof(Player), "m_evolveToCostOverride").FieldType.GetElementType(), 0));

            if (def.kit != null && sheet != null)
            {
                try { def.kit(p, sheet); FurtherCore.Log.LogInfo(def.id + ": authored moveset installed"); }
                catch (Exception e) { FurtherCore.Log.LogError(def.id + " kit failed: " + e); }
            }
            if (sheet != null)
            {
                float k;
                if (ArtScale.BySheet.TryGetValue(sheet.id, out k) && Math.Abs(k - 1f) > 0.001f) ScaleOffsets(p, k);
                FitHurtbox(p, sheet);
            }
            ApplyTuning(def, p);
            if (def.customize != null)
            {
                try { def.customize(go, p); }
                catch (Exception e) { FurtherCore.Log.LogError(def.id + " customize failed: " + e); }
            }
            // mod clips play sounds with AnimSound(cue GameObject): make sure something on the body receives it
            // (a customize that strips components, or a base prefab without one, would leave its moves silent)
            if (go.GetComponent<AudioCueSource>() == null) go.AddComponent<AudioCueSource>();
            if (def.traits != null) MonsterTraits.Register(def.PrefabName, def.traits);
            if (def.challenge != null) Challenges.Register(def.PrefabName, def.challenge);
            Built[def.id] = p;
            FurtherCore.Log.LogInfo("Built monster " + def.PrefabName + " from " + def.basePrefab);
            return p;
        }

        // The tier rule, then the def's own numbers, after the kit so the def line has the last word.
        static void ApplyTuning(MonsterDef def, Player p)
        {
            int tier = TierRules.Of(def.evolveCost);   // a def that keeps its base's cost (minions, blobs) stays tier 1
            Tier[def.PrefabName] = tier;
            float dmg = (TierRules.IsStarter(def.evolveCost) ? TierRules.StarterDamage : TierRules.Damage(tier)) * def.damageMult;
            if (tier >= 2 || Math.Abs(dmg - 1f) > 0.001f) DamageMult[def.PrefabName] = dmg;
            float ct = R.Get<float>(p, "m_specialAttackChargeTime");
            if (ct > 0f) R.Set(p, "m_specialAttackChargeTime", ct * TierRules.SpecialCharge(tier));
            if (def.specialChargeTime > 0f) R.Set(p, "m_specialAttackChargeTime", def.specialChargeTime);
            if (Math.Abs(def.attackCooldownMult - 1f) > 0.001f)
                foreach (var a in R.Get<List<AttackData>>(p, "m_attacks")) a.m_cooldown *= def.attackCooldownMult;
        }

        /// <summary>Point each built monster at its <see cref="MonsterDef.evolveTo"/> targets. Call after building the whole tree.</summary>
        public static void LinkEvolutions(IEnumerable<MonsterDef> defs)
        {
            foreach (var d in defs)
            {
                Player p;
                if (!Built.TryGetValue(d.id, out p)) continue;
                var list = new List<Player>();
                foreach (var to in d.evolveTo)
                {
                    Player t;
                    if (!Built.TryGetValue(to, out t)) t = FindVanilla(to);
                    if (t == null) { FurtherCore.Log.LogError(d.id + ": evolution target missing: " + to); continue; }
                    if (list.Contains(t)) { FurtherCore.Log.LogError(d.id + ": evolution target listed twice: " + to); continue; }
                    list.Add(t);
                }
                R.Set(p, "m_evolveTo", list.ToArray());
            }
        }

        static readonly string[] s_animFields =
        {
            "m_animationIdle", "m_animationRun", "m_animationDead", "m_animationKnockback", "m_animationStatue", "m_portraitAnim", "m_animationSpawn"
        };

        static void Reskin(Player p, SpriteSheet sheet, Dictionary<UnityEngine.Object, UnityEngine.Object> map, Dictionary<string, string> aliases, bool hasKit)
        {
            foreach (var f in s_animFields)
            {
                var old = R.Get<exSpriteAnimClip>(p, f);
                // The game leaves Knockback after the clip stops playing and skips the state entirely when the
                // base has no clip. A looping clip made here kept monsters in Knockback forever (no attacks).
                if (old == null && (f == "m_animationSpawn" || f == "m_animationKnockback")) continue;
                if (f == "m_animationStatue" && !sheet.Has("Statue")) continue;   // statue props only; never fall back to a moving pose
                string anim = f == "m_portraitAnim" ? "Portrait" : f.Substring("m_animation".Length);
                if (anim == "Dead" && sheet.Has("Death")) anim = "Death";   // multi-frame death that holds on the corpse
                if (!sheet.Has(anim) && f == "m_portraitAnim") anim = "Idle";
                if (!sheet.Has(anim) && f == "m_animationKnockback") anim = "Idle";
                if (!sheet.Has(anim) && f == "m_animationStatue") anim = "Idle";
                if (!sheet.Has(anim) && f == "m_animationSpawn") anim = "Idle";
                // exSpriteAnimation resolves clips BY NAME (Play(clip) plays whatever state already has that name; pooled statue
                // props and menu sprites keep their states). Vanilla names ("idle", "run") were shared by every monster built on
                // the same base, so each slot gets a name of its own: Mod<sheet>_<slot>.
                string slot = f == "m_portraitAnim" ? "Portrait" : f.Substring("m_animation".Length);
                string clipName = ClipName(sheet, slot);
                var nc = SpriteSheets.MakeClip(sheet, anim, old, clipName);
                if (nc == null) continue;
                if (anim == "Death") { nc.wrapMode = WrapMode.Once; nc.stopAction = exSpriteAnimClip.StopAction.DoNothing; }
                if (f == "m_animationKnockback") { nc.wrapMode = WrapMode.Once; nc.stopAction = exSpriteAnimClip.StopAction.DoNothing; }
                if (old != null) map[old] = nc;
                R.Set(p, f, nc);
            }
            var attacks = R.Get<List<AttackData>>(p, "m_attacks");
            string al;
            if (hasKit) return;   // the kit replaces every attack; nothing to alias
            for (int i = 0; i < attacks.Count; i++)
                RemapAttack(attacks[i], sheet, aliases.TryGetValue("Attack" + i, out al) ? al : "Attack" + i, map);
            if (R.Get<bool>(p, "m_hasSpecialAttack"))
                RemapAttack(R.Get<AttackData>(p, "m_specialAttack"), sheet, aliases.TryGetValue("Special", out al) ? al : "Special", map);
        }

        /// <summary>The name of a mod monster's Idle/Run/Dead/Knockback/Portrait/Spawn/Statue clip: unique per sheet and slot.</summary>
        internal static string ClipName(SpriteSheet sheet, string slot) { return "Mod" + sheet.id + "_" + slot; }

        /// <summary>
        /// The prefab sprite offset that puts the art's feet pixel (cellW/2, cellH-2) on the transform, as <see cref="Strike"/> does
        /// for effects. The base's own offset was fitted to its trimmed vanilla frames: a Skeleton Mage base (offset y -7) drew a
        /// mod monster 6 px below its shadow, a Giant Spider base (x 0.5) 1 px off the turn axis.
        /// </summary>
        public static Vector2 FeetOffset(SpriteSheet sheet)
        {
            int w = sheet.manifest.cellW;
            return new Vector2(w * 0.5f - w / 2 - 0.5f, -1f);
        }

        static void RemapAttack(AttackData a, SpriteSheet sheet, string anim, Dictionary<UnityEngine.Object, UnityEngine.Object> map)
        {
            if (a == null || a.m_animationFront == null) return;
            var old = a.m_animationFront;
            if (!sheet.Has(anim))
            {
                FurtherCore.Log.LogWarning(sheet.id + ": no '" + anim + "' animation, keeping vanilla frames");
                return;
            }
            var nc = SpriteSheets.MakeClip(sheet, anim, old, old.name);
            map[old] = nc;
            a.m_animationFront = nc;
            // aimed variants (up/down) fall back to the front animation re-timed to their own events
            if (a.m_animAngles != null)
            {
                int k = 0;
                foreach (var ang in a.m_animAngles)
                {
                    var angClip = ang.m_animation;
                    if (angClip == null) { k++; continue; }
                    var key = anim + "_angle" + k++;
                    var src = sheet.Has(key) ? key : anim;
                    var vc = SpriteSheets.MakeClip(sheet, src, angClip, angClip.name);
                    map[angClip] = vc;
                    ang.m_animation = vc;
                }
            }
        }

        /// <summary>
        /// Our cells are untrimmed, so the base monster's portrait offsets point at empty space.
        /// Menus (HUD portrait, evolution menu, god preview) frame a monster through m_portraitOffset: vanilla
        /// centres the window about two thirds of the way up the body, so do the same from the art's real bounds.
        /// </summary>
        static void FitPortrait(Player p, SpriteSheet sheet)
        {
            try
            {
                var spr = p.GetComponent<exSprite>();
                if (spr == null || sheet == null) return;
                var clip = R.Get<exSpriteAnimClip>(p, "m_portraitAnim") ?? R.Get<exSpriteAnimClip>(p, "m_animationIdle");
                if (clip == null || clip.frameInfos.Count == 0 || clip.frameInfos[0].atlas != sheet.atlas) return;
                int bx, by, bw, bh;
                if (!Bounds(sheet, clip.frameInfos[0].index, out bx, out by, out bw, out bh)) return;
                float cx = bx + bw * 0.5f, cy = by + bh * 0.68f;
                float px = Mathf.Round(spr.offset.x + cx - sheet.manifest.cellW * 0.5f);
                float py = Mathf.Round(spr.offset.y + cy);
                p.m_portraitOffset = new Vector2(px, py);
                // the evolve-menu button shows the Portrait frame, and the Run cycle once selected, through the same offset:
                // aim between the two so a monster whose run pose is much lower (a slithering snake) stays in the window
                var run = R.Get<exSpriteAnimClip>(p, "m_animationRun");
                int rx, ry, rw, rh;
                if (run != null && run.frameInfos.Count > 0 && run.frameInfos[0].atlas == sheet.atlas &&
                    Bounds(sheet, run.frameInfos[0].index, out rx, out ry, out rw, out rh))
                {
                    cx = (cx + rx + rw * 0.5f) * 0.5f;
                    cy = (cy + ry + rh * 0.68f) * 0.5f;
                }
                p.m_portraitOffsetEvolve = new Vector2(Mathf.Round(spr.offset.x + cx - sheet.manifest.cellW * 0.5f), Mathf.Round(spr.offset.y + cy) - 1f);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("FitPortrait " + sheet.id + ": " + e.Message); }
        }

        static readonly Dictionary<string, GameObject> s_scaled = new Dictionary<string, GameObject>();

        static bool Invisible(GameObject t)
        {
            foreach (var r in t.GetComponentsInChildren<Renderer>(true))
                if (r.enabled) { var sp = r.GetComponent<exSprite>(); if (sp == null || sp.enabled) return false; }
            return true;
        }

        /// <summary>A copy of an effect template shrunk by k (spawn hooks and echo links carried over).</summary>
        static GameObject ScaledTemplate(GameObject t, float k)
        {
            if (t == null) return null;
            string key = t.GetInstanceID() + "|" + k.ToString("0.000");
            GameObject c;
            if (s_scaled.TryGetValue(key, out c) && c != null) return c;
            c = ClonePrefab(t, t.name + "_x" + Mathf.RoundToInt(k * 100f));
            var ls = t.transform.localScale;
            c.transform.localScale = new Vector3(ls.x * k, ls.y * k, ls.z);
            FxFactory.Templates[c.name] = c;
            Action<GameObject> hook;
            if (FxFactory.OnSpawn.TryGetValue(t, out hook)) FxFactory.OnSpawn[c] = hook;
            s_scaled[key] = c;
            GameObject echo;
            if (Patch_SpawnEffectEcho.EchoOf.TryGetValue(t, out echo) && echo != null)
                Patch_SpawnEffectEcho.EchoOf[c] = ScaledTemplate(echo, k);
            Strike.KeepScale(c);
            return c;
        }

        static MinMaxRange Scaled(MinMaxRange r, float k)
        {
            if (r == null) return null;
            var c = new MinMaxRange(r);
            c.m_min *= k; c.m_max *= k;
            return c;
        }

        /// <summary>Kit offsets were authored against the art before it was re-rendered smaller: shrink them to match.</summary>
        static void ScaleOffsets(Player p, float k)
        {
            var seen = new HashSet<DamageEffectData>();
            Action<IEnumerable<DamageEffectData>> scale = list =>
            {
                if (list == null) return;
                foreach (var d in list)
                {
                    if (d == null || !seen.Add(d)) continue;
                    d.m_offsetX = Scaled(d.m_offsetX, k);
                    d.m_offsetY = Scaled(d.m_offsetY, k);
                    // melee hitboxes (attached, or invisible) shrink with the body; projectiles and art effects keep their size
                    if (d.m_object != null && (d.m_attach || Invisible(d.m_object))) d.m_object = ScaledTemplate(d.m_object, k);
                }
            };
            scale(Kit.Effects(p));
            R.Set(p, "m_attackSpawnNode", R.Get<Vector2>(p, "m_attackSpawnNode") * k);
            FurtherCore.Log.LogInfo(p.gameObject.name + ": effect offsets scaled x" + k.ToString("0.00"));
        }

        /// <summary>
        /// The base monster's hurtbox (child "HitZone", layer DamagablePlayer) is sized for the base art: a gnome-sized box
        /// on a crab twice its width is hard to hit. Refit it to the mod art's Idle bounds (90% wide, 90% tall).
        /// </summary>
        static void FitHurtbox(Player p, SpriteSheet sheet)
        {
            try
            {
                var spr = p.GetComponent<exSprite>();
                var idle = R.Get<exSpriteAnimClip>(p, "m_animationIdle");
                if (spr == null || idle == null || idle.frameInfos.Count == 0 || idle.frameInfos[0].atlas != sheet.atlas) return;
                int bx, by, bw, bh;
                if (!Bounds(sheet, idle.frameInfos[0].index, out bx, out by, out bw, out bh)) return;
                // hovering art: reach down to just above the floor so low swings and feet-level hits still connect
                if (by > 4) { bh += by - 2; by = 2; }
                int layer = LayerMask.NameToLayer("DamagablePlayer");
                foreach (var box in p.GetComponentsInChildren<BoxCollider>(true))
                {
                    var t = box.transform;
                    if (t == p.transform || (layer >= 0 && box.gameObject.layer != layer)) continue;
                    var ls = t.localScale; var lp = t.localPosition;
                    if (Mathf.Abs(ls.x) < 0.001f || Mathf.Abs(ls.y) < 0.001f) continue;
                    float cx = spr.offset.x + bx + bw * 0.5f - sheet.manifest.cellW * 0.5f;
                    float cy = spr.offset.y + by + bh * 0.5f;
                    float w = Mathf.Max(4f, bw * 0.9f), h = Mathf.Max(4f, bh * 0.9f);
                    var oldWorld = new Vector2(box.size.x * ls.x, box.size.y * ls.y);
                    box.size = new Vector3(w / ls.x, h / ls.y, box.size.z);
                    box.center = new Vector3((cx - lp.x) / ls.x, (cy - lp.y) / ls.y, box.center.z);
                    FurtherCore.Log.LogInfo(p.gameObject.name + ": hurtbox " + oldWorld.x.ToString("0.0") + "x" + oldWorld.y.ToString("0.0") + " -> " + w.ToString("0.0") + "x" + h.ToString("0.0"));
                }
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("FitHurtbox " + sheet.id + ": " + e.Message); }
        }

        /// <summary>
        /// Opaque bounds of every cell of a sheet ({x, y, w, h} from the cell's bottom-left; null = empty cell), worked out
        /// once per texture. Keeping the whole Color32[] of each sheet instead held ~2 MB per big monster sheet for the
        /// life of the game, and the menu badge asks again for every frame it shows.
        /// </summary>
        static readonly Dictionary<Texture2D, int[][]> s_cellBounds = new Dictionary<Texture2D, int[][]>();

        static int[][] CellBounds(SpriteSheet sheet, Texture2D tex)
        {
            int[][] cells;
            if (s_cellBounds.TryGetValue(tex, out cells)) return cells;
            var m = sheet.manifest;
            int cols = m.cols, rows = m.cellH > 0 ? tex.height / m.cellH : 0;
            cells = new int[Mathf.Max(0, cols * rows)][];
            var px = tex.GetPixels32(0);
            for (int i = 0; i < cells.Length; i++)
            {
                int col = i % cols, row = i / cols;
                int x0 = col * m.cellW, y0 = tex.height - (row + 1) * m.cellH;
                if (x0 < 0 || y0 < 0 || x0 + m.cellW > tex.width) continue;
                int minX = int.MaxValue, minY = int.MaxValue, maxX = -1, maxY = -1;
                for (int y = 0; y < m.cellH; y++)
                {
                    int rowStart = (y0 + y) * tex.width + x0;
                    for (int x = 0; x < m.cellW; x++)
                        if (px[rowStart + x].a > 8)
                        {
                            if (x < minX) minX = x; if (x > maxX) maxX = x;
                            if (y < minY) minY = y; if (y > maxY) maxY = y;
                        }
                }
                if (maxX >= 0) cells[i] = new[] { minX, minY, maxX - minX + 1, maxY - minY + 1 };
            }
            s_cellBounds[tex] = cells;
            return cells;
        }

        /// <summary>The opaque bounds of cell <paramref name="index"/> of a mod sheet, in pixels from the cell's bottom-left.
        /// False for an empty cell or a sheet without pixels.</summary>
        public static bool Bounds(SpriteSheet sheet, int index, out int bx, out int by, out int bw, out int bh)
        {
            bx = by = bw = bh = 0;
            if (sheet == null || sheet.atlas == null) return false;
            var m = sheet.manifest;
            var tex = sheet.atlas.texture as Texture2D;
            if (tex == null || m.cols <= 0 || m.cellW <= 0 || m.cellH <= 0 || index < 0) return false;
            var cells = CellBounds(sheet, tex);
            if (index >= cells.Length || cells[index] == null) return false;
            var c = cells[index];
            bx = c[0]; by = c[1]; bw = c[2]; bh = c[3];
            return true;
        }

        static void ReportUnmappedSprites(GameObject go, SpriteSheet sheet)
        {
            foreach (var s in go.GetComponentsInChildren<exSprite>(true))
            {
                if (s.gameObject == go) continue;
                if (s.atlas != null && s.atlas.name == "AtlasEnemies")
                    FurtherCore.Log.LogWarning(sheet.id + ": child sprite '" + s.gameObject.name + "' still uses vanilla enemy art");
            }
        }
    }
}
