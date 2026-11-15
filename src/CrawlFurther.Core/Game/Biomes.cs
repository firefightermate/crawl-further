using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Game
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A Crawl Chaos biome: a new kind of floor, built at runtime as a new <c>Environment</c> from one of the game's
    /// (its rooms, doors, traps and props), with its own colours, props and room hook (its hazard).
    /// </summary>
    public class BiomeDef
    {
        /// <summary>Unique id (save-free, but used in names: keep it to letters).</summary>
        public string id;
        /// <summary>The name players see.</summary>
        public string name;
        /// <summary>The game environment it is built from, by its display name ("Caves", "Crypt", "Mines", ...).</summary>
        public string baseEnvironment = "Caves";
        /// <summary>Chance that a new stretch of chaos floors is this biome.</summary>
        public float chance = 0.35f;
        /// <summary>Colours for the rooms' floors.</summary>
        public Recolour.Fn floor;
        /// <summary>Colours for everything else in the rooms (walls, set pieces) and the doors.</summary>
        public Recolour.Fn wall;
        /// <summary>Extra work on each room's floor picture after <see cref="floor"/> (moss, frost, cracks):
        /// pixels bottom-up, width, height, a random source seeded by the room.</summary>
        public Action<Color32[], int, int, System.Random> floorDetail;
        /// <summary>Colours for a game prop kept in the biome, by the prop's name; null keeps it as it is.</summary>
        public Func<string, Recolour.Fn> gameProp;
        /// <summary>How much of each prop group is the game's own props (recoloured); the rest is the biome's.</summary>
        public float gamePropShare = 0.3f;
        /// <summary>The biome's props by group, with weights (templates from <c>Objects.PropKit</c>).</summary>
        public readonly List<KeyValuePair<GameObject, float>> decals = new List<KeyValuePair<GameObject, float>>(),
            small = new List<KeyValuePair<GameObject, float>>(), large = new List<KeyValuePair<GameObject, float>>(),
            feature = new List<KeyValuePair<GameObject, float>>();
        /// <summary>Names a floor of the biome can get (shown as the floor starts); null keeps the base environment's.</summary>
        public string[] floorNames;
        /// <summary>Runs on every room of the biome when it spawns (add the hazard's component here).</summary>
        public Action<GameObject> roomSpawned;
    }

    /// <summary>
    /// The chaos biomes: registry, building and choosing. A biome takes over whole stretches of floors: when a chaos
    /// game moves to a new environment (every two to four floors), each biome has its <see cref="BiomeDef.chance"/> to
    /// be that stretch instead. Each is built the first time it is picked, which takes a moment.
    /// </summary>
    public static class Biomes
    {
        /// <summary>Off: chaos floors keep the game's environments.</summary>
        public static bool Enabled = true;
        /// <summary>Test mode: every new stretch of chaos floors is this biome (null: chance as usual).</summary>
        public static BiomeDef Forced;
        /// <summary>Test mode: no biome is picked.</summary>
        public static bool Never;

        public static readonly List<BiomeDef> All = new List<BiomeDef>();
        static readonly Dictionary<BiomeDef, Environment> s_env = new Dictionary<BiomeDef, Environment>();
        static readonly Dictionary<Environment, BiomeDef> s_def = new Dictionary<Environment, BiomeDef>();
        static readonly Dictionary<int, KeyValuePair<Environment, Environment>> s_level = new Dictionary<int, KeyValuePair<Environment, Environment>>();
        static readonly Dictionary<string, GameObject> s_props = new Dictionary<string, GameObject>();
        static GameObject s_holder;

        public static void Register(BiomeDef d)
        {
            if (d == null || string.IsNullOrEmpty(d.id) || All.Exists(x => x.id == d.id)) return;
            All.Add(d);
        }

        /// <summary>The biome of the floor being played, or null.</summary>
        public static BiomeDef Current
        {
            get
            {
                Environment e = null;
                try { e = SystemLevel.GetEnvironment(); } catch { }
                BiomeDef d;
                return e != null && s_def.TryGetValue(e, out d) ? d : null;
            }
        }

        /// <summary>The biome an environment is, or null.</summary>
        public static BiomeDef Of(Environment e)
        {
            BiomeDef d;
            return e != null && s_def.TryGetValue(e, out d) ? d : null;
        }

        /// <summary>The game's environments (Dungeon, Caves, Crypt, Mines).</summary>
        public static Environment[] GameEnvironments
        {
            get { return Singleton<Constants>.HasInstance() ? Singleton<Constants>.Get.m_environments : new Environment[0]; }
        }

        /// <summary>The biome's environment, built the first time.</summary>
        public static Environment EnvironmentFor(BiomeDef d)
        {
            Environment e;
            if (d == null) return null;
            if (s_env.TryGetValue(d, out e)) return e;
            e = null;
            var t = Time.realtimeSinceStartup;
            try { e = Build(d); }
            catch (Exception ex) { FurtherCore.Log.LogError("Biome " + d.id + " could not be built: " + ex); e = null; }
            s_env[d] = e;
            if (e != null)
            {
                s_def[e] = d;
                FurtherCore.Log.LogInfo("Biome " + d.name + " built in " + (Time.realtimeSinceStartup - t).ToString("0.0") + " s");
            }
            return e;
        }

        // ------------------------------------------------------------------ choosing

        internal static Environment Choose(int level, Environment game)
        {
            if (game == null || s_def.ContainsKey(game)) return game;
            if (SystemMenu.GetAttractMode() || SystemMenu.GetChallengeMode() || SystemTutorial.GetActive()) return game;
            if (s_goNow != null)
            {
                var now = EnvironmentFor(s_goNow);
                s_goNow = null;
                if (now != null) { s_level[level] = new KeyValuePair<Environment, Environment>(game, now); return now; }
            }
            if (!Enabled || All.Count == 0 || !ChaosMode.Active) return game;
            KeyValuePair<Environment, Environment> had;
            if (s_level.TryGetValue(level, out had) && had.Key == game) return had.Value;
            Environment pick;
            if (s_level.TryGetValue(level - 1, out had) && had.Key == game) pick = had.Value;   // the same stretch goes on
            else pick = Roll(game);
            s_level[level] = new KeyValuePair<Environment, Environment>(game, pick);
            return pick;
        }

        static Environment Roll(Environment game)
        {
            if (Never) return game;
            if (Forced != null) return EnvironmentFor(Forced) ?? game;
            float r = UnityEngine.Random.value, at = 0f;
            foreach (var d in All)
            {
                at += d.chance;
                if (r < at) return EnvironmentFor(d) ?? game;
            }
            return game;
        }

        /// <summary>A new game forgets which floors were which.</summary>
        internal static void Reset() { s_level.Clear(); }

        static BiomeDef s_goNow;

        /// <summary>Test mode: the next floor loaded (and the rest of its stretch) is <paramref name="d"/>, chaos or not.
        /// Builds it now, so the wait comes here; then reload the floor.</summary>
        public static bool GoNow(BiomeDef d)
        {
            if (EnvironmentFor(d) == null) return false;
            s_goNow = d;
            if (Singleton<SystemGame>.HasInstance())
            {
                int lvl = R.Get<int>(Singleton<SystemGame>.Instance, "m_level");
                for (int i = 0; i < 4; i++) s_level.Remove(lvl + i);
            }
            return true;
        }

        // ------------------------------------------------------------------ building

        static Environment FindGame(string displayName)
        {
            foreach (var e in GameEnvironments) if (e != null && e.GetDisplayName() == displayName) return e;
            return null;
        }

        static Environment Build(BiomeDef d)
        {
            var game = FindGame(d.baseEnvironment);
            var all = GameEnvironments;
            if (game == null && all.Length > 0) game = all[0];
            if (game == null) throw new Exception("no game environment to build on");
            if (s_holder == null)
            {
                s_holder = new GameObject("CrawlMod_Biomes");
                s_holder.SetActive(false);
                UnityEngine.Object.DontDestroyOnLoad(s_holder);
            }
            var go = MonsterFactory.ClonePrefab(game.gameObject, "Biome" + d.id);
            var env = go.GetComponent<Environment>();
            R.Set(env, "m_displayName", d.name);
            if (d.floorNames != null && d.floorNames.Length > 0) R.Set(env, "m_floorNames", d.floorNames);
            // the colour the game fades props toward, moved the way the floor is
            if (d.floor != null)
            {
                Color fade = R.Get<Color>(env, "m_fadeToFloorColour");
                Color32 f32 = fade;
                Color moved = (Color)d.floor(new Color32(f32.r, f32.g, f32.b, 255));
                moved.a = fade.a;
                R.Set(env, "m_fadeToFloorColour", moved);
            }
            var rooms = new Dictionary<Room, Room>();
            foreach (var f in new[] { "m_roomGroupStarting", "m_roomGroup2p", "m_roomGroup3p", "m_roomGroup4p" })
                R.Set(env, f, RoomGroup(d, R.Get<SpawnGroup>(game, f), rooms));
            R.Set(env, "m_roomStore", Skin(d, R.Get<Room>(game, "m_roomStore"), rooms));
            R.Set(env, "m_roomPortal", Skin(d, R.Get<Room>(game, "m_roomPortal"), rooms));
            var doors = R.Get<GameObject[]>(game, "m_doors");
            if (doors != null)
            {
                var nd = new GameObject[doors.Length];
                for (int i = 0; i < doors.Length; i++)
                {
                    if (doors[i] == null) continue;
                    nd[i] = MonsterFactory.ClonePrefab(doors[i], doors[i].name);
                    Recolour.Tree(nd[i], "wall" + d.id, d.wall);
                }
                R.Set(env, "m_doors", nd);
            }
            R.Set(env, "m_propsDecal", PropGroup(d, R.Get<SpawnGroup>(game, "m_propsDecal"), d.decals, "Decal"));
            R.Set(env, "m_propsSmall", PropGroup(d, R.Get<SpawnGroup>(game, "m_propsSmall"), d.small, "Small"));
            R.Set(env, "m_propsLarge", PropGroup(d, R.Get<SpawnGroup>(game, "m_propsLarge"), d.large, "Large"));
            R.Set(env, "m_propsFeature", PropGroup(d, R.Get<SpawnGroup>(game, "m_propsFeature"), d.feature, "Feature"));
            FurtherCore.Log.LogInfo("Biome " + d.name + ": " + rooms.Count + " rooms from " + game.GetDisplayName());
            return env;
        }

        static SpawnGroup NewGroup(string name, SpawnGroup like)
        {
            var go = new GameObject(name);
            go.transform.parent = s_holder.transform;
            var g = go.AddComponent<SpawnGroup>();
            g.m_items = new List<SpawnItem>();
            if (like != null) g.m_numToSpawn = like.m_numToSpawn;
            return g;
        }

        static void Flatten(SpawnGroup g, float scale, List<KeyValuePair<GameObject, float>> into, int depth = 0)
        {
            if (g == null || g.m_items == null || depth > 4) return;
            float total = 0f;
            foreach (var it in g.m_items) if (it != null && it.m_object != null) total += it.m_chance;
            if (total <= 0f) return;
            foreach (var it in g.m_items)
            {
                if (it == null || it.m_object == null) continue;
                var nested = it.m_object.GetComponent<SpawnGroup>();
                if (nested != null && nested != g) { Flatten(nested, scale * it.m_chance / total, into, depth + 1); continue; }
                into.Add(new KeyValuePair<GameObject, float>(it.m_object, scale * it.m_chance / total));
            }
        }

        static SpawnGroup RoomGroup(BiomeDef d, SpawnGroup game, Dictionary<Room, Room> rooms)
        {
            if (game == null) return null;
            var g = NewGroup("Biome" + d.id + game.name, game);
            var items = new List<KeyValuePair<GameObject, float>>();
            Flatten(game, 1f, items);
            foreach (var it in items)
            {
                var room = it.Key.GetComponent<Room>();
                var skin = room != null ? Skin(d, room, rooms) : null;
                g.m_items.Add(new SpawnItem { m_object = skin != null ? skin.gameObject : it.Key, m_chance = it.Value });
                if (room == null || skin == null || !ChaosRooms.Enabled) continue;
                var big = ChaosRooms.Big(room);
                if (big == null) { ChaosRooms.Pair(skin, null, ChaosRooms.WhyNot(room)); continue; }
                var bigSkin = Skin(d, big, rooms);
                if (bigSkin == null) continue;
                ChaosRooms.Pair(skin, bigSkin);
                ChaosRooms.MarkBig(bigSkin.gameObject, ChaosRooms.AreaOf(big.gameObject));
            }
            return g;
        }

        /// <summary>A recoloured copy of a room: its floor picture rebuilt (colours and detail), everything else
        /// recoloured frame by frame; the biome's room hook runs on each one spawned.</summary>
        static Room Skin(BiomeDef d, Room src, Dictionary<Room, Room> done)
        {
            if (src == null) return null;
            Room r;
            if (done.TryGetValue(src, out r)) return r;
            var go = MonsterFactory.ClonePrefab(src.gameObject, src.name);
            go.transform.position = Vector3.zero;
            r = go.GetComponent<Room>();
            var floor = go.GetComponent<exSprite>();
            bool floorDone = false;
            if (floor != null && d.floor != null)
            {
                try
                {
                    var pic = ChaosRooms.Picture(floor, go.transform);
                    if (pic != null)
                    {
                        for (int i = 0; i < pic.px.Length; i++) pic.px[i] = d.floor(pic.px[i]);
                        if (d.floorDetail != null) d.floorDetail(pic.px, pic.w, pic.h, new System.Random(src.name.GetHashCode()));
                        ChaosRooms.Apply(pic, go.transform, "Biome" + d.id + "_" + src.name + "_floor");
                        floorDone = true;
                    }
                }
                catch (Exception e) { FurtherCore.Log.LogWarning("Biome " + d.id + ": " + src.name + " floor: " + e.Message); }
            }
            Recolour.Tree(go, s =>
            {
                if (s == floor) return floorDone || d.floor == null ? default(KeyValuePair<string, Recolour.Fn>) : new KeyValuePair<string, Recolour.Fn>("floor" + d.id, d.floor);
                if (IsLight(s.gameObject)) return default(KeyValuePair<string, Recolour.Fn>);
                return new KeyValuePair<string, Recolour.Fn>("wall" + d.id, d.wall);
            });
            if (d.roomSpawned != null)
            {
                Action<GameObject> prev;
                FxFactory.OnSpawn.TryGetValue(go, out prev);
                FxFactory.OnSpawn[go] = prev + d.roomSpawned;
            }
            done[src] = r;
            return r;
        }

        static bool IsLight(GameObject g)
        {
            var n = g.name;
            return n.IndexOf("light", StringComparison.OrdinalIgnoreCase) >= 0 || n.IndexOf("flicker", StringComparison.OrdinalIgnoreCase) >= 0
                || n.IndexOf("flame", StringComparison.OrdinalIgnoreCase) >= 0 || n.IndexOf("candle", StringComparison.OrdinalIgnoreCase) >= 0;
        }

        static SpawnGroup PropGroup(BiomeDef d, SpawnGroup game, List<KeyValuePair<GameObject, float>> mine, string kind)
        {
            var g = NewGroup("Biome" + d.id + "Props" + kind, game);
            float mineTotal = 0f;
            foreach (var m in mine) if (m.Key != null) mineTotal += m.Value;
            float share = mineTotal > 0f ? Mathf.Clamp01(d.gamePropShare) : 1f;
            var theirs = new List<KeyValuePair<GameObject, float>>();
            Flatten(game, 1f, theirs);
            const float Scale = 1000f;
            foreach (var t in theirs)
            {
                var p = GameProp(d, t.Key);
                if (p != null) g.m_items.Add(new SpawnItem { m_object = p, m_chance = t.Value * share * Scale });
            }
            foreach (var m in mine)
                if (m.Key != null) g.m_items.Add(new SpawnItem { m_object = m.Key, m_chance = m.Value / mineTotal * (1f - share) * Scale });
            return g;
        }

        /// <summary>A game prop in the biome: recoloured by <see cref="BiomeDef.gameProp"/>, or as it is. Ghost traps and
        /// the game's interactable props stay the game's own objects.</summary>
        static GameObject GameProp(BiomeDef d, GameObject p)
        {
            if (p == null) return null;
            var n = p.name;
            if (d.gameProp == null || n.Contains("Ghost") || n.Contains("Actionable")) return p;
            var fn = d.gameProp(n);
            if (fn == null) return p;
            string k = d.id + ":" + p.GetInstanceID();
            GameObject c;
            if (s_props.TryGetValue(k, out c)) return c;
            c = MonsterFactory.ClonePrefab(p, n);
            Recolour.Tree(c, s => IsLight(s.gameObject) ? default(KeyValuePair<string, Recolour.Fn>) : new KeyValuePair<string, Recolour.Fn>("prop" + d.id + n, fn));
            s_props[k] = c;
            return c;
        }

        /// <summary>Self-test: the game members the biomes reach by name.</summary>
        public static void SelfCheck(Action<string> bad, Action<string> note)
        {
            foreach (var f in new[] { "m_displayName", "m_roomGroupStarting", "m_roomGroup2p", "m_roomGroup3p", "m_roomGroup4p", "m_roomStore",
                                      "m_roomPortal", "m_doors", "m_floorNames", "m_fadeToFloorColour", "m_propsDecal", "m_propsSmall", "m_propsLarge", "m_propsFeature" })
                if (AccessTools.Field(typeof(Environment), f) == null) bad("biomes: Environment." + f + " missing");
            foreach (var f in new[] { "m_environmentCurr", "m_level" })
                if (AccessTools.Field(typeof(SystemGame), f) == null) bad("biomes: SystemGame." + f + " missing");
            if (AccessTools.Method(typeof(SystemGame), "CalcEnvironment") == null) bad("biomes: SystemGame.CalcEnvironment missing");
            var names = new List<string>();
            foreach (var e in GameEnvironments) if (e != null) names.Add(e.GetDisplayName());
            note("game environments: " + string.Join(", ", names.ToArray()));
            foreach (var d in All)
                if (FindGame(d.baseEnvironment) == null) bad("biome " + d.name + ": no game environment named " + d.baseEnvironment);
                else
                {
                    int n = d.decals.Count + d.small.Count + d.large.Count + d.feature.Count;
                    if (n == 0) bad("biome " + d.name + ": none of its props were built (art missing?)");
                    if (d.floor == null || d.wall == null) bad("biome " + d.name + ": no colours");
                    note("biome " + d.name + " (from " + d.baseEnvironment + "), " + n + " props");
                }
        }
    }

    [HarmonyPatch(typeof(SystemGame), "CalcEnvironment")]
    static class Patch_BiomeChoice
    {
        static void Postfix(int level, ref Environment __result)
        {
            try { __result = Biomes.Choose(level, __result); }
            catch (Exception e) { FurtherCore.Log.LogError("Biome choice: " + e); }
        }
    }
}
