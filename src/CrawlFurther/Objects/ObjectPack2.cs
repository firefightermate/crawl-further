using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Objects
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Objects;
    using CrawlFurther.UI;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Items;
    using CrawlFurther.Content.Secrets;

    /// <summary>
    /// Fifteen fun and secret room objects built on ObjectKit (src/CrawlFurther.Core/Objects/ObjectKit.cs), art from
    /// tools/sprites/objects2_rigs.py (art/out_objects2, anchor points in its TIMING.md).
    ///
    /// Fun: Jukebox (changes the soundtrack), Disco Ball (dance floor, Groove, Disco Fever), Pinata, Confetti Cannon (party),
    /// Slot Machine, Fortune Teller, Bounce Shroom, Firework Crate.
    /// Secret: Lever Trio (+ its hatch), Cracked Wall (drops the Skeleton Key), Mysterious Keyhole (+ the reliquary with the
    /// Gilded Heart), Sculptor's Altar (summons a secret statue), Wishing Well (the Well Spirit), Watching Portrait,
    /// Golden Duck. Eight Secrets entries in group "Objects" (Slot Machine jackpot, levers, wall, keyhole, altar, well
    /// spirit, portrait, duck).
    /// </summary>
    public static class ObjectPack2
    {
        // ------------------------------------------------------------------ ids (ObjectKit prefixes "ModObj")
        public const string Jukebox = "BJukebox", Disco = "BDiscoBall", Pinata = "BPinata", Cannon = "BConfettiCannon",
                            Slots = "BSlotMachine", Fortune = "BFortuneTeller", Shroom = "BBounceShroom", Fireworks = "BFireworkCrate",
                            Levers = "BLeverTrio", Stash = "BLeverStash", Wall = "BCrackedWall", Keyhole = "BKeyhole",
                            Reliquary = "BReliquary", Altar = "BSculptorAltar", Well = "BWishingWell", Portrait = "BPortrait",
                            Duck = "BGoldenDuck";
        public static readonly string[] Ids = { Jukebox, Disco, Pinata, Cannon, Slots, Fortune, Shroom, Fireworks, Levers, Stash,
                                                Wall, Keyhole, Reliquary, Altar, Well, Portrait, Duck };

        // Secrets ids (group "Objects")
        public const string SecJackpot = "ObjBJackpot", SecLevers = "ObjBLevers", SecWall = "ObjBCrackedWall",
                            SecKeyhole = "ObjBKeyhole", SecAltar = "ObjBSculptorAltar", SecWell = "ObjBWellSpirit",
                            SecPortrait = "ObjBPortrait", SecDuck = "ObjBGoldenDuck";

        // ------------------------------------------------------------------ balance numbers (all shown in the texts)
        public const int SlotCost = 5, SlotPulls = 8, FortuneCost = 3, FortuneReads = 3, WellCoinsForSpirit = 100, WellTosses = 10;
        public const float DiscoTime = 20f, DiscoBeat = 0.6f, FeverTime = 8f, FeverSpeed = 1.2f, FeverCooldown = 0.85f;
        public const float PartyTime = 10f, PartySpeed = 1.15f, CannonReach = 46f, FuseTime = 2f;
        public const float RocketHero = 1f, RocketTrap = 0.5f, StatueLegendary = 0.05f, StillTime = 5f;
        public const float DuckRoomChance = 1f / 500f;

        // ------------------------------------------------------------------ fx templates
        static GameObject s_notes, s_confetti, s_rain, s_gold, s_blast, s_rocket, s_spores, s_coins, s_spirit, s_card, s_sparkle,
                          s_dust, s_jackpot, s_statueForm;
        static readonly Dictionary<string, GameObject> s_tiles = new Dictionary<string, GameObject>();
        static readonly Dictionary<string, GameObject> s_symbols = new Dictionary<string, GameObject>();
        static readonly Dictionary<string, GameObject> s_glyphs = new Dictionary<string, GameObject>();
        static GameObject s_leverUp, s_leverDown;
        static readonly GameObject[] s_fwHero = new GameObject[4], s_fwTrap = new GameObject[4];
        static readonly string[] FwColours = { "Pink", "Gold", "Cyan", "Lime" };
        static StatusOverlayDef[] s_groove;
        static StatusOverlayDef s_fever, s_hat;

        // the FX sheets' origin pixel (cell x, y down), see TIMING.md: the art lands with this pixel on the transform
        static readonly Dictionary<string, Vector2> Origin = new Dictionary<string, Vector2>
        {
            { "FxObjBDanceTile", new Vector2(9, 6) }, { "FxObjBSlotSymbols", new Vector2(4, 4) }, { "FxObjBLever", new Vector2(10, 9) },
            { "FxObjBGlyphs", new Vector2(4, 3) }, { "FxObjBNotes", new Vector2(13, 26) }, { "FxObjBConfetti", new Vector2(38, 31) },
            { "FxObjBConfettiBlast", new Vector2(47, 22) }, { "FxObjBRocket", new Vector2(14, 3) }, { "FxObjBFirework", new Vector2(17, 24) },
            { "FxObjBSpores", new Vector2(13, 11) }, { "FxObjBCoins", new Vector2(24, 15) }, { "FxObjBWellSpirit", new Vector2(20, 35) },
            { "FxObjBCard", new Vector2(6, 25) }, { "FxObjBSparkle", new Vector2(14, 21) }, { "FxObjBDust", new Vector2(20, 10) },
            { "FxObjBJackpot", new Vector2(28, 29) }, { "FxObjBStatueForm", new Vector2(8, 25) },
        };

        static void Pin(GameObject go, string sheet)
        {
            Vector2 o;
            if (go != null && Origin.TryGetValue(sheet, out o)) Strike.ArtAt(go, sheet, (int)o.x, (int)o.y);
        }

        /// <summary>A one-shot or looping visual pinned to its origin pixel. child = no DepthHandler (sorted by the parent's z).</summary>
        static GameObject Vis(string name, string sheet, string anim, bool loop = false, float life = 0f, bool child = false, bool thenHold = false, string hold = null)
        {
            GameObject go;
            if (hold != null)
            {
                var sh = SpriteSheets.Get(sheet);
                if (sh == null || !sh.Has(anim) || !sh.Has(hold)) { Plugin.Log.LogWarning("ObjectsB: missing " + sheet + "/" + anim); return null; }
                var clip = new ClipBuilder(sh, anim, name + "Clip").Once().Then(hold, 400).Build();
                go = FxFactory.Visual(name, sh, clip, false);
                FxFactory.SetEffect(go, destroyOnAnimEnd: false);
            }
            else go = FxKit.Visual(name, sheet, anim, loop, life);
            if (go == null) return null;
            Pin(go, sheet);
            FxFactory.SetEffect(go, destroyOnAnimEnd: !loop && life <= 0f && hold == null, destroyAfter: life, canFlip: false, freeRotate: false);
            var dh = go.GetComponent<DepthHandler>();
            if (child) { if (dh != null) UnityEngine.Object.DestroyImmediate(dh); }
            else if (dh != null) dh.m_heightOffset = -30f;      // pops out in front of the object it comes from
            FxKit.NoTint(go);
            return go;
        }

        /// <summary>Spawn a loose effect on the floor at a world point (sorted by its own DepthHandler).</summary>
        public static GameObject Fx(GameObject tmpl, Vector2 p, bool flipX = false)
        {
            if (tmpl == null) return null;
            GameObject go = null;
            try
            {
                go = tmpl.Spawn(new Vector3(p.x, p.y, 0f), Quaternion.identity);
                if (go != null && flipX) go.transform.localScale = new Vector3(-1f, 1f, 1f);
                else if (go != null) go.transform.localScale = Vector3.one;
            }
            catch (Exception e) { Plugin.Log.LogWarning("ObjectsB fx: " + e.Message); }
            return go;
        }

        /// <summary>Spawn an effect as a child of an object at a local point (x right, y up), z: just in front (or behind).</summary>
        static GameObject Child(GameObject tmpl, Transform parent, float x, float y, float z = -0.05f)
        {
            if (tmpl == null || parent == null) return null;
            GameObject go = null;
            try
            {
                go = tmpl.Spawn(parent.position, Quaternion.identity, parent);
                if (go != null)
                {
                    go.transform.localPosition = new Vector3(x, y, z);
                    go.transform.localScale = Vector3.one;
                }
            }
            catch (Exception e) { Plugin.Log.LogWarning("ObjectsB child: " + e.Message); }
            return go;
        }

        static void Kill(GameObject go)
        {
            if (go == null) return;
            try { if (go.activeSelf) go.Despawn(); } catch { }
        }

        static void BuildFx()
        {
            s_notes = Vis("ModObjBNotes", "FxObjBNotes", "Float");
            s_confetti = Vis("ModObjBConfetti", "FxObjBConfetti", "Burst");
            s_gold = Vis("ModObjBConfettiGold", "FxObjBConfetti", "Gold");
            s_rain = Vis("ModObjBConfettiRain", "FxObjBConfetti", "Rain", loop: true, life: 6f);
            s_blast = Vis("ModObjBConfettiBlast", "FxObjBConfettiBlast", "Blast");
            s_rocket = Vis("ModObjBRocket", "FxObjBRocket", "Fly", loop: true);
            s_spores = Vis("ModObjBSpores", "FxObjBSpores", "Puff");
            s_coins = Vis("ModObjBCoins", "FxObjBCoins", "Burst");
            s_spirit = Vis("ModObjBWellSpirit", "FxObjBWellSpirit", "Rise");
            s_card = Vis("ModObjBCard", "FxObjBCard", "Pop");
            s_sparkle = Vis("ModObjBSparkle", "FxObjBSparkle", "Twinkle");
            s_dust = Vis("ModObjBDust", "FxObjBDust", "Puff");
            s_jackpot = Vis("ModObjBJackpot", "FxObjBJackpot", "Flash");
            s_statueForm = Vis("ModObjBStatueForm", "FxObjBStatueForm", "Form");
            // floor decals laid under the disco ball (behind everyone, above the floor: the vanilla shadow depth)
            foreach (var c in new[] { "Off", "Pink", "Cyan", "Gold", "Lime" })
                s_tiles[c] = Vis("ModObjBTile" + c, "FxObjBDanceTile", c, loop: true, child: true);
            s_tiles["Beat"] = Vis("ModObjBTileBeat", "FxObjBDanceTile", "Beat", child: true);
            foreach (var s in new[] { "Bone", "Coin", "Heart", "Skull", "Crown" })
                s_symbols[s] = Vis("ModObjBSym" + s, "FxObjBSlotSymbols", s, loop: true, child: true);
            s_symbols["Blur"] = Vis("ModObjBSymBlur", "FxObjBSlotSymbols", "Blur", loop: true, child: true);
            foreach (var g in new[] { "Sun", "Moon", "Star" })
            {
                s_glyphs[g] = Vis("ModObjBGlyph" + g, "FxObjBGlyphs", g, loop: true, child: true);
                s_glyphs["Scratch" + g] = Vis("ModObjBScratch" + g, "FxObjBGlyphs", "Scratch" + g, loop: true, child: true);
            }
            s_leverUp = Vis("ModObjBLeverUp", "FxObjBLever", "Up", loop: true, child: true);
            s_leverDown = Vis("ModObjBLeverDown", "FxObjBLever", "Pull", child: true, hold: "Down");
            // fireworks: the burst is the damage (on its frames 1-3, a 24 x 14 blast on the ground under the sparks)
            for (int i = 0; i < 4; i++)
            {
                s_fwHero[i] = FxKit.TimedHit("ModObjBFireworkHero" + FwColours[i], "TrollGroundPoundBigShockwave", "FxObjBFirework", FwColours[i], 1, 4, RocketHero, 0.7f, canFlip: false);
                s_fwTrap[i] = FxKit.TimedHit("ModObjBFireworkTrap" + FwColours[i], "TrollGroundPoundBigShockwave", "FxObjBFirework", FwColours[i], 1, 4, RocketTrap, 0.7f, canFlip: false);
                foreach (var t in new[] { s_fwHero[i], s_fwTrap[i] })
                {
                    if (t == null) continue;
                    Strike.ArtAt(t, "FxObjBFirework", 17, 24);
                    Strike.HitBox(t, 24f, 14f);
                }
            }
            // indicators
            s_groove = new[]
            {
                ModStatus.Indicator("ModIndObjBGroove1", "FxObjBInd", "Groove1", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndObjBGroove2", "FxObjBInd", "Groove2", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndObjBGroove3", "FxObjBInd", "Groove3", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndObjBGroove4", "FxObjBInd", "Groove4", 1f, OverlayAt.Head),
            };
            s_fever = ModStatus.Indicator("ModIndObjBFever", "FxObjBIndFever", "Fever", -2f, OverlayAt.Feet);
            s_hat = ModStatus.Indicator("ModIndObjBParty", "FxObjBInd", "Hat", 1f, OverlayAt.Head);
        }

        // ------------------------------------------------------------------ small runtime helpers
        static Vector2 P(GameObject go) { return go != null ? (Vector2)go.transform.position : Vector2.zero; }

        static Room RoomOf(ModObject o)
        {
            Room r = o != null ? o.Room : null;
            if (r == null) { try { r = SystemLevel.GetCurrentRoom(); } catch { } }
            return r;
        }

        static bool InRoom(Room room, Vector2 p)
        {
            if (room == null) return true;
            try { return room.IsPointInRoom(p); } catch { return true; }
        }

        /// <summary>Hero and player monsters (alive, with a body) standing in the room.</summary>
        static List<PlayerData> LivingIn(Room room)
        {
            var list = new List<PlayerData>();
            PlayerData[] all = null;
            try { all = SystemPlayers.GetPlayers(); } catch { }
            if (all == null) return list;
            foreach (var pd in all)
            {
                if (pd == null || !pd.IsActive || !pd.IsAlive || pd.GameObject == null) continue;
                var p = pd.GameObject.GetComponent<Player>();
                if (p == null || ModUtil.IsGhost(p)) continue;
                if (!InRoom(room, pd.GameObject.transform.position)) continue;
                list.Add(pd);
            }
            return list;
        }

        /// <summary>Every monster body in the room (player-controlled or AI), never the hero or a boss.</summary>
        static List<Player> MonstersIn(Room room)
        {
            var list = new List<Player>();
            var hero = ModUtil.Hero();
            foreach (var p in UnityEngine.Object.FindObjectsOfType<Player>())
            {
                if (p == null || p.gameObject == hero || ModUtil.IsGhost(p) || !p.gameObject.activeInHierarchy) continue;
                if (p.GetComponentInParent<Boss>() != null) continue;
                var h = p.GetComponent<Health>();
                if (h == null || !h.IsAlive()) continue;
                if (!InRoom(room, p.transform.position)) continue;
                list.Add(p);
            }
            return list;
        }

        static Vector2 RandomPointIn(Room room, Vector2 near, float spread)
        {
            for (int i = 0; i < 12; i++)
            {
                var p = near + UnityEngine.Random.insideUnitCircle * spread;
                if (InRoom(room, p)) return p;
            }
            return near;
        }

        static void Say(PlayerData pd, string title, string l1, string l2, string l3 = null)
        {
            if (pd == null || pd.IsBot) return;
            try
            {
                Color c = Color.white;
                try { if (pd.Setup != null) c = pd.Setup.m_colourGUI; } catch { }
                c.a = 1f;
                string who = null;
                try { if (SystemPlayers.GetNumHumanPlayers() > 1) who = "P" + (pd.Id + 1); } catch { }
                TipView.Get().Show(pd.Id, who != null ? who + " - " + title : title, l1, l2 ?? string.Empty, l3, c);
            }
            catch (Exception e) { Plugin.Log.LogWarning("ObjectsB tip: " + e.Message); }
        }

        static void SayAllIn(Room room, string title, string l1, string l2)
        {
            PlayerData[] all = null;
            try { all = SystemPlayers.GetPlayers(); } catch { }
            if (all == null) return;
            foreach (var pd in all)
                if (pd != null && pd.IsActive && !pd.IsBot && pd.GameObject != null && InRoom(room, pd.GameObject.transform.position)) Say(pd, title, l1, l2);
        }

        static void Sound(string cue, Transform at) { ObjectKit.PlaySound(cue, at); }

        static void Gold(PlayerData pd, int n) { if (pd != null && n > 0) { try { pd.OnGoldCollected(n); } catch { } } }

        static void HealFull(GameObject body, float amount)
        {
            var h = body != null ? body.GetComponent<Health>() : null;
            if (h == null || !h.IsAlive()) return;
            h.Heal(amount);
            ModInd.Heal(body);
        }

        static bool Hurt(GameObject body)
        {
            var h = body != null ? body.GetComponent<Health>() : null;
            return h != null && h.IsAlive() && h.GetHealthCurrent() < h.GetHealthMax() - 0.01f;
        }

        static void Found(string secret, Vector2 at)
        {
            try
            {
                bool was = Secrets.IsFound(secret);
                Secrets.Found(secret);
                if (!was) Fx(s_sparkle, at);
            }
            catch { }
        }

        static T Brain<T>(GameObject go) where T : Component
        {
            var b = go.GetComponent<T>();
            return b != null ? b : go.AddComponent<T>();
        }

        /// <summary>A Health on the object + a "Damagable" child (layer DamagableProp) so the hero's attacks hit it like a vanilla
        /// barrel. It never dies (999 health); the object's brain counts the hits in OnDamaged.</summary>
        static void Hittable(GameObject go, float w, float h, float cy)
        {
            var hp = go.GetComponent<Health>() ?? go.AddComponent<Health>();
            R.Set(hp, "m_healthMax", 999f);
            R.Set(hp, "m_flashOnHit", false);
            R.Set(hp, "m_allowedDamageSource", eAllowedDamageSource.Hero);
            R.Set(hp, "m_spawnInvulnerableTime", 0.3f);
            var t = go.transform.Find("Damagable");
            GameObject d = t != null ? t.gameObject : new GameObject("Damagable");
            int layer = LayerMask.NameToLayer("DamagableProp");
            d.layer = layer >= 0 ? layer : 25;
            d.transform.SetParent(go.transform, false);
            d.transform.localPosition = Vector3.zero;
            var rb = d.GetComponent<Rigidbody>() ?? d.AddComponent<Rigidbody>();
            rb.isKinematic = true; rb.useGravity = false;
            var bc = d.GetComponent<BoxCollider>() ?? d.AddComponent<BoxCollider>();
            bc.size = new Vector3(w, h, 200f);
            bc.center = new Vector3(0f, cy, 0f);
            bc.isTrigger = false;
        }

        // ================================================================== registration
        public static void Register()
        {
            BuildFx();
            RegJukebox(); RegDisco(); RegPinata(); RegCannon(); RegSlots(); RegFortune(); RegShroom(); RegFireworks();
            RegLevers(); RegWall(); RegKeyhole(); RegAltar(); RegWell(); RegPortrait(); RegDuck();
            RegSecrets();
            Plugin.Log.LogInfo("ObjectsB: " + Ids.Length + " objects, " + Built() + " built");
        }

        static int Built()
        {
            int n = 0;
            foreach (var id in Ids) if (ObjectKit.Built.ContainsKey(id)) n++;
            return n;
        }

        static ObjSpawn Spawn(float weight, int minFloor, ObjRoom rooms, int max = 1, ObjPlace place = ObjPlace.Open)
        {
            return new ObjSpawn { weight = weight, minFloor = minFloor, rooms = rooms, maxPerFloor = max, place = place };
        }

        const ObjRoom Calm = ObjRoom.Quiet | ObjRoom.Statue | ObjRoom.Stairs;
        const ObjRoom Rooms = ObjRoom.Quiet | ObjRoom.Statue | ObjRoom.Stairs | ObjRoom.Fight | ObjRoom.Trapped;

        // ------------------------------------------------------------------ 1. Jukebox
        static int s_song = -1;
        static List<AudioCue> s_vanillaSongs;

        static void RegJukebox()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Jukebox, name = "Jukebox", art = "ObjBJukebox",
                vault = "A rattling music box",
                tip1 = "Play: change the music for the rest of the floor",
                tip2 = "Anyone can play it, as often as they like",
                kind = ObjKind.Use, users = ObjUser.Anyone, actionText = "PLAY", uses = 0, cooldown = 1.5f,
                offDuringFight = false, bounce = false, useSound = "SoundButton",
                onUse = u => NextSong(u),
                spawn = Spawn(6f, 1, Rooms),
                useBox = new Vector2(30f, 24f), bodySize = new Vector2(16f, 6f),
            });
        }

        static string Pretty(string cue)
        {
            if (string.IsNullOrEmpty(cue)) return "A dungeon song";
            switch (cue)
            {
                case "MusicGameDefault": return "Crawl: The Dungeon";
                case "MusicGameCrypt": return "Crawl: The Crypt";
                case "MusicGameMines": return "Crawl: The Mines";
                case "MusicGameCaves": return "Crawl: The Caves";
            }
            string s = cue.StartsWith("MusicGame") ? cue.Substring(9) : cue.StartsWith("Music") ? cue.Substring(5) : cue;
            var sb = new System.Text.StringBuilder("Crawl: ");
            for (int i = 0; i < s.Length; i++)
            {
                char ch = s[i];
                if (ch == '_') { sb.Append(' '); continue; }
                if (i > 0 && char.IsUpper(ch) && !char.IsUpper(s[i - 1])) sb.Append(' ');
                sb.Append(ch);
            }
            return sb.ToString();
        }

        static void NextSong(ObjUse u)
        {
            var names = new List<string>();
            var plays = new List<Action>();
            int mod = 0;
            try { mod = ModMusic.TrackCount; } catch { }
            for (int i = 0; i < mod; i++)
            {
                int k = i;
                names.Add(ModMusic.TrackName(k));
                plays.Add(() => ModMusic.ForceTrack(k));
            }
            var seen = new HashSet<string>();
            try
            {
                // the vanilla floor songs never change during a session: scan the assets once
                if (s_vanillaSongs == null || s_vanillaSongs.Count == 0 || s_vanillaSongs.Exists(x => x == null)) s_vanillaSongs = ModMusic.VanillaFloorCues();
                foreach (var cue in s_vanillaSongs)
                {
                    if (cue == null || !seen.Add(cue.name)) continue;
                    var c = cue;
                    names.Add(Pretty(c.name));
                    plays.Add(() => ModMusic.ForceVanilla(c));
                }
            }
            catch (Exception e) { Plugin.Log.LogWarning("Jukebox: " + e.Message); }
            var at = P(u.obj.gameObject);
            Fx(s_notes, at + new Vector2(8f, 34f));
            if (names.Count == 0)
            {
                Say(u.pd, "Jukebox", "The jukebox wheezes. No songs tonight.", "");
                return;
            }
            s_song = (s_song + 1) % names.Count;
            try { plays[s_song](); } catch (Exception e) { Plugin.Log.LogWarning("Jukebox play: " + e.Message); }
            u.obj.StartCoroutine(Notes(u.obj, 2));
            Say(u.pd, "Jukebox", "Now playing: " + names[s_song], "Song " + (s_song + 1) + " of " + names.Count + ". Play again for the next one.");
        }

        static IEnumerator Notes(ModObject o, int n)
        {
            for (int i = 0; i < n; i++)
            {
                yield return new WaitForSeconds(0.45f);
                if (o == null || !o.gameObject.activeInHierarchy) yield break;
                Fx(s_notes, P(o.gameObject) + new Vector2(8f + (i % 2 == 0 ? -2f : 2f), 34f));
            }
        }

        // ------------------------------------------------------------------ 2. Disco Ball
        static void RegDisco()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Disco, name = "Disco Ball", art = "ObjBDiscoBall",
                vault = "A mirror ball over a dance floor",
                tip1 = "Step on lit tiles before each beat",
                tip2 = "Four in a row: Disco Fever, a burst of speed",
                kind = ObjKind.Use, users = ObjUser.Anyone, actionText = "DANCE", uses = 0, cooldown = DiscoTime + 15f,
                offDuringFight = false, bounce = false, useSound = "SoundActicateTriforce",
                onUse = u => Brain<DiscoBrain>(u.obj.gameObject).Begin(u),
                onSpawned = go => Brain<DiscoBrain>(go).Clear(),
                spawn = Spawn(4f, 2, Rooms),
                useBox = new Vector2(26f, 22f), bodySize = Vector2.zero,
            });
        }

        public class DiscoBrain : MonoBehaviour
        {
            readonly GameObject[] m_tiles = new GameObject[9];
            readonly bool[] m_lit = new bool[9];
            readonly int[] m_groove = new int[8];
            float m_end, m_next;
            bool m_on;
            ModObject m_obj;
            static readonly string[] Cols = { "Pink", "Cyan", "Gold", "Lime" };

            public void Clear()
            {
                StopAllCoroutines();
                for (int i = 0; i < 9; i++) { Kill(m_tiles[i]); m_tiles[i] = null; m_lit[i] = false; }
                for (int i = 0; i < m_groove.Length; i++) m_groove[i] = 0;
                m_on = false;
            }

            static Vector2 Cell(int i) { return new Vector2((i % 3 - 1) * 14f, (i / 3 - 1) * 10f); }

            public void Begin(ObjUse u)
            {
                m_obj = u.obj;
                Clear();
                m_on = true;
                m_end = Time.time + DiscoTime;
                m_next = Time.time + 0.4f;
                for (int i = 0; i < 9; i++) SetTile(i, null);
                if (m_obj != null) m_obj.Play("Spin");
                SayAllIn(RoomOf(m_obj), "Disco Ball", "Step on a lit tile before the next beat.", "Four in a row: Disco Fever.");
            }

            void SetTile(int i, string col)
            {
                Kill(m_tiles[i]);
                var c = Cell(i);
                // floor decal: under every character, above the floor (vanilla prop shadows sit at local z 90)
                m_tiles[i] = Child(s_tiles[col ?? "Off"], transform, c.x, c.y, 90f);
                m_lit[i] = col != null;
            }

            void Update()
            {
                if (!m_on) return;
                if (Time.time >= m_end)
                {
                    for (int i = 0; i < 9; i++) { Kill(m_tiles[i]); m_tiles[i] = null; }
                    foreach (var pd in LivingIn(null)) ModInd.Count(pd.GameObject, s_groove, 0);
                    m_on = false;
                    if (m_obj != null && m_obj.State == "Spin") m_obj.Play("Idle");
                    return;
                }
                if (Time.time < m_next) return;
                m_next = Time.time + DiscoBeat;
                Beat();
            }

            void Beat()
            {
                // judge: who stands on a tile that was lit for this beat
                Vector2 c = transform.position;
                var room = RoomOf(m_obj);
                foreach (var pd in LivingIn(room))
                {
                    var d = (Vector2)pd.GameObject.transform.position - c;
                    int ix = Mathf.RoundToInt(d.x / 14f), iy = Mathf.RoundToInt(d.y / 10f);
                    bool onFloor = Mathf.Abs(ix) <= 1 && Mathf.Abs(iy) <= 1 && Mathf.Abs(d.x - ix * 14f) <= 7.5f && Mathf.Abs(d.y - iy * 10f) <= 5.5f;
                    int id = pd.Id;
                    if (id < 0 || id >= m_groove.Length) continue;
                    if (!onFloor) { if (m_groove[id] > 0) { m_groove[id] = 0; ModInd.Count(pd.GameObject, s_groove, 0); } continue; }
                    int k = (iy + 1) * 3 + (ix + 1);
                    if (m_lit[k])
                    {
                        m_groove[id]++;
                        if (m_groove[id] >= 4)
                        {
                            m_groove[id] = 0;
                            ModInd.Count(pd.GameObject, s_groove, 0);
                            Fever(pd);
                        }
                        else ModInd.Count(pd.GameObject, s_groove, m_groove[id]);
                    }
                    else if (m_groove[id] > 0) { m_groove[id] = 0; ModInd.Count(pd.GameObject, s_groove, 0); }
                }
                // light the next pattern: 3 or 4 tiles, never the same set twice in a row
                var pick = new List<int> { 0, 1, 2, 3, 4, 5, 6, 7, 8 };
                int n = UnityEngine.Random.value < 0.5f ? 3 : 4;
                var on = new bool[9];
                for (int j = 0; j < n; j++)
                {
                    int r = UnityEngine.Random.Range(0, pick.Count);
                    on[pick[r]] = true; pick.RemoveAt(r);
                }
                for (int i = 0; i < 9; i++)
                    if (on[i]) { SetTile(i, Cols[UnityEngine.Random.Range(0, 4)]); Child(s_tiles["Beat"], transform, Cell(i).x, Cell(i).y, 89f); }
                    else if (m_lit[i] || m_tiles[i] == null) SetTile(i, null);
            }

            static void Fever(PlayerData pd)
            {
                bool hero = pd.IsHero;
                ObjectKit.Buff(pd, "ObjBDiscoFeverSpeed", hero ? PlayerModifier.eType.HeroSpeed : PlayerModifier.eType.MonsterSpeed, FeverSpeed, FeverTime,
                    () => { if (pd.GameObject != null) ModInd.Set(pd.GameObject, s_fever, false); });
                ObjectKit.Buff(pd, "ObjBDiscoFeverAttack", hero ? PlayerModifier.eType.HeroAttackCooldown : PlayerModifier.eType.MonsterAttackCooldown, FeverCooldown, FeverTime);
                ModInd.Set(pd.GameObject, s_fever, true, FeverTime);
                Fx(s_sparkle, (Vector2)pd.GameObject.transform.position + new Vector2(0f, 10f));
                ObjectKit.PlaySound("SoundStatUpFromProp", pd.GameObject.transform);
                Say(pd, "Disco Fever", "Faster moves for a while,", "and your attacks come back sooner.");
            }

            void OnDisable() { Clear(); }
        }

        // ------------------------------------------------------------------ 3. Pinata
        static void RegPinata()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Pinata, name = "Pinata", art = "ObjBPinata",
                vault = "A papier-mache goat full of sweets and coins",
                tip1 = "Hit it three times: confetti and gold",
                tip2 = "Sometimes a candy heart falls out and heals",
                kind = ObjKind.Use, users = ObjUser.Hero, uses = 0, canUse = u => false,
                once = new HashSet<string> { "Hit", "Burst" }, then = new Dictionary<string, string> { { "Burst", "Broken" } },
                customize = go => Hittable(go, 16f, 22f, 12f),
                onSpawned = go => Brain<PinataBrain>(go).Reset(),
                spawn = Spawn(6f, 1, Calm),
                useBox = new Vector2(36f, 28f), bodySize = Vector2.zero,
            });
        }

        public class PinataBrain : MonoBehaviour
        {
            int m_hits;
            float m_last;
            ModObject m_obj;

            public void Reset() { m_hits = 0; m_last = -10f; StopAllCoroutines(); }

            void OnDamaged(DamageInfo info) { Hit(); }
            void OnKilled(DamageInfo info) { Hit(); }

            void Hit()
            {
                if (m_hits >= 3 || Time.time - m_last < 0.3f) return;
                m_last = Time.time;
                if (m_obj == null) m_obj = GetComponent<ModObject>();
                var hero = SystemPlayers.GetHeroPlayerData();
                m_hits++;
                Vector2 body = (Vector2)transform.position + new Vector2(0f, 25f);
                if (m_hits == 1 && hero != null && m_obj != null) ObjectKit.Discovered(hero, gameObject, m_obj.def);
                ObjectKit.PlaySound("SoundVaseHit", transform);
                if (m_hits < 3)
                {
                    m_obj.Play("Hit");
                    Fx(s_confetti, body);
                    StartCoroutine(After(0.28f, m_hits == 1 ? "Torn1" : "Torn2"));
                    return;
                }
                m_obj.Play("Burst");
                m_obj.Spent();
                StartCoroutine(Burst(hero, body));
            }

            IEnumerator After(float t, string state)
            {
                yield return new WaitForSeconds(t);
                if (m_obj != null) m_obj.Play(state);
            }

            IEnumerator Burst(PlayerData hero, Vector2 body)
            {
                yield return new WaitForSeconds(0.05f);
                ObjectKit.PlaySound("SoundPumpkinSmash", transform);
                Fx(s_confetti, body);
                Fx(s_coins, body - new Vector2(0f, 12f));
                ObjectKit.PlaySound("SoundGoldpickupMultiple", transform);
                int gold = UnityEngine.Random.Range(10, 19);
                Gold(hero, gold);
                bool candy = UnityEngine.Random.value < 1f / 3f;
                if (candy && hero != null) HealFull(hero.GameObject, 1f);
                Say(hero, "Pinata", "Sweets everywhere! " + gold + " gold.", candy ? "A candy heart: 1 health back." : "");
            }
        }

        // ------------------------------------------------------------------ 4. Confetti Cannon
        static void RegCannon()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Cannon, name = "Confetti Cannon", art = "ObjBConfettiCannon",
                vault = "A party cannon packed with paper",
                tip1 = "Pull: a blast knocks back and dazes all in front",
                tip2 = "Then everyone here is faster for a while",
                kind = ObjKind.Use, users = ObjUser.Hero | ObjUser.Ghost, actionText = "PULL", uses = 1,
                offDuringFight = false, bounce = false, useSound = "SoundGoblinBombFuse",
                then = new Dictionary<string, string> { { "Use", "Spent" } },
                onUse = u => u.obj.StartCoroutine(Fire(u.obj, u.pd)),
                onSpawned = go =>
                {
                    // faces a random way (the art faces right)
                    go.transform.localScale = UnityEngine.Random.value < 0.5f ? new Vector3(-1f, 1f, 1f) : Vector3.one;
                },
                spawn = Spawn(5f, 1, Rooms),
                useBox = new Vector2(34f, 22f), bodySize = new Vector2(20f, 6f),
            });
        }

        static IEnumerator Fire(ModObject o, PlayerData by)
        {
            yield return new WaitForSeconds(0.24f);
            if (o == null) yield break;
            float dir = o.transform.localScale.x < 0f ? -1f : 1f;
            Vector2 at = P(o.gameObject);
            Vector2 muzzle = at + new Vector2(11f * dir, 9f);
            Fx(s_blast, muzzle, dir < 0f);
            ObjectKit.PlaySound("SoundExplosion", o.transform);
            var room = RoomOf(o);
            // the cone: everyone (hero or monster) in front within 46 px and 35 degrees
            var daze = ModStatus.Daze;
            var hit = new HashSet<GameObject>();
            var bodies = new List<GameObject>();
            foreach (var pd in LivingIn(room)) bodies.Add(pd.GameObject);
            foreach (var m in MonstersIn(room)) if (!bodies.Contains(m.gameObject)) bodies.Add(m.gameObject);
            foreach (var b in bodies)
            {
                if (b == null || (by != null && b == by.GameObject)) continue;
                var d = (Vector2)b.transform.position - (muzzle - new Vector2(0f, 9f));
                if (d.magnitude > CannonReach || d.x * dir <= 0f) continue;
                if (Vector2.Angle(new Vector2(dir, 0f), d) > 35f) continue;
                var p = b.GetComponent<Player>();
                if (p == null || !hit.Add(b)) continue;
                try { p.KnockbackPush(d.normalized, 1.6f); } catch { }
                if (daze != null) { try { p.AddStatus(daze, new DamageSource(o.gameObject, o.gameObject, by), "objbcannon"); } catch { } }
            }
            // and the party
            yield return new WaitForSeconds(0.2f);
            for (int i = 0; i < 6; i++) Fx(s_rain, RandomPointIn(room, at, 90f));
            foreach (var pd in LivingIn(room))
            {
                var who = pd;
                ObjectKit.Buff(who, "ObjBParty", who.IsHero ? PlayerModifier.eType.HeroSpeed : PlayerModifier.eType.MonsterSpeed, PartySpeed, PartyTime,
                    () => { if (who.GameObject != null) ModInd.Set(who.GameObject, s_hat, false); });
                ModInd.Set(who.GameObject, s_hat, true, PartyTime);
            }
            SayAllIn(room, "Party Time", "Confetti! Everyone here moves faster", "for a while.");
        }

        // ------------------------------------------------------------------ 5. Slot Machine
        static void RegSlots()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Slots, name = "Slot Machine", art = "ObjBSlotMachine",
                vault = "A one-armed bandit",
                tip1 = "Pay gold to pull. Coins pay, three crowns pay most",
                tip2 = "Hearts heal, skulls feed ghosts. A few pulls",
                kind = ObjKind.Use, users = ObjUser.Hero, actionText = "PULL", uses = 0, cooldown = 1.4f,
                canUse = u => Brain<SlotBrain>(u.obj.gameObject).CanPull,
                costGold = SlotCost, bounce = false, useSound = "SoundTrapPlungerDown",
                once = new HashSet<string> { "Win" }, then = new Dictionary<string, string> { { "Win", "Idle" } },
                onUse = u => Brain<SlotBrain>(u.obj.gameObject).Pull(u),
                onSpawned = go => Brain<SlotBrain>(go).Reset(),
                spawn = Spawn(5f, 1, Calm),
                useBox = new Vector2(30f, 24f), bodySize = new Vector2(20f, 6f),
            });
        }

        public enum SlotResult { Lose, TwoCoins, TwoHearts, ThreeCoins, ThreeHearts, ThreeSkulls, Jackpot }

        /// <summary>The documented odds of one pull (sum 1): jackpot 1 in 150, 3 coins 6, 3 hearts 4, 3 skulls 4, 2 coins 18,
        /// 2 hearts 10 (percent), else nothing. Average gold back per 5 gold pull: 0.5 + 1.32 + 1.08 = 2.9, plus 0.18 health.</summary>
        public static SlotResult RollSlot(float r)
        {
            if (r < 1f / 150f) return SlotResult.Jackpot;
            r -= 1f / 150f;
            if (r < 0.06f) return SlotResult.ThreeCoins; r -= 0.06f;
            if (r < 0.04f) return SlotResult.ThreeHearts; r -= 0.04f;
            if (r < 0.04f) return SlotResult.ThreeSkulls; r -= 0.04f;
            if (r < 0.18f) return SlotResult.TwoCoins; r -= 0.18f;
            if (r < 0.10f) return SlotResult.TwoHearts;
            return SlotResult.Lose;
        }

        /// <summary>The three reel symbols that show a result.</summary>
        public static string[] ReelsFor(SlotResult res, System.Random rnd)
        {
            string[] other = { "Bone", "Skull", "Crown" };
            switch (res)
            {
                case SlotResult.Jackpot: return new[] { "Crown", "Crown", "Crown" };
                case SlotResult.ThreeCoins: return new[] { "Coin", "Coin", "Coin" };
                case SlotResult.ThreeHearts: return new[] { "Heart", "Heart", "Heart" };
                case SlotResult.ThreeSkulls: return new[] { "Skull", "Skull", "Skull" };
                case SlotResult.TwoCoins:
                case SlotResult.TwoHearts:
                {
                    string two = res == SlotResult.TwoCoins ? "Coin" : "Heart";
                    string[] odd = res == SlotResult.TwoCoins ? new[] { "Bone", "Skull", "Crown", "Heart" } : new[] { "Bone", "Skull", "Crown", "Coin" };
                    var r = new[] { two, two, two };
                    r[rnd.Next(3)] = odd[rnd.Next(odd.Length)];
                    return r;
                }
            }
            // a losing line: no pair of coins or hearts, never three of a kind
            string[] all = { "Bone", "Coin", "Heart", "Skull", "Crown" };
            for (int tries = 0; tries < 50; tries++)
            {
                var r = new[] { all[rnd.Next(5)], all[rnd.Next(5)], all[rnd.Next(5)] };
                int coins = 0, hearts = 0;
                foreach (var s in r) { if (s == "Coin") coins++; if (s == "Heart") hearts++; }
                if (coins >= 2 || hearts >= 2 || (r[0] == r[1] && r[1] == r[2])) continue;
                return r;
            }
            return new[] { "Bone", "Skull", "Crown" };
        }

        public class SlotBrain : MonoBehaviour
        {
            static readonly float[] ReelX = { -6f, 0f, 6f };
            const float ReelY = 16f;
            readonly GameObject[] m_reel = new GameObject[3];
            static readonly System.Random s_rnd = new System.Random();
            int m_pulls;
            bool m_spinning;

            public bool CanPull { get { return !m_spinning && m_pulls < SlotPulls; } }

            public void Reset() { Clear(); m_pulls = 0; }

            public void Clear()
            {
                m_spinning = false;
                StopAllCoroutines();
                for (int i = 0; i < 3; i++) { Kill(m_reel[i]); m_reel[i] = null; }
            }

            void Show(int i, string sym)
            {
                Kill(m_reel[i]);
                GameObject t;
                m_reel[i] = s_symbols.TryGetValue(sym, out t) ? Child(t, transform, ReelX[i], ReelY) : null;
            }

            public void Pull(ObjUse u)
            {
                Clear();
                m_pulls++;
                m_spinning = true;
                var res = RollSlot(UnityEngine.Random.value);
                var reels = ReelsFor(res, s_rnd);
                StartCoroutine(Spin(u.obj, u.pd, res, reels));
            }

            IEnumerator Spin(ModObject o, PlayerData pd, SlotResult res, string[] reels)
            {
                yield return new WaitForSeconds(0.15f);
                ObjectKit.PlaySound("SoundSlingSpin", transform);
                for (int i = 0; i < 3; i++) Show(i, "Blur");
                yield return new WaitForSeconds(0.6f);
                for (int i = 0; i < 3; i++)
                {
                    Show(i, reels[i]);
                    ObjectKit.PlaySound("SoundStoreTeleportUpCoinLand", transform);
                    yield return new WaitForSeconds(0.2f);
                }
                Pay(o, pd, res);
                m_spinning = false;
                if (m_pulls >= SlotPulls)
                {
                    yield return new WaitForSeconds(1.2f);
                    Clear();
                    if (o != null) o.Spent();
                }
            }

            void Pay(ModObject o, PlayerData pd, SlotResult res)
            {
                Vector2 at = transform.position;
                string l1 = "No luck.", l2 = "The bandit keeps your 5 gold.";
                switch (res)
                {
                    case SlotResult.Jackpot:
                        Gold(pd, 75);
                        Fx(s_jackpot, at + new Vector2(0f, 24f));
                        Fx(s_gold, at + new Vector2(0f, 20f));
                        Fx(s_coins, at);
                        ObjectKit.PlaySound("SoundGoldpickupMultiple", transform);
                        ObjectKit.PlaySound("SoundLevelUp", transform);
                        l1 = "TRIPLE CROWN! Jackpot: 75 gold."; l2 = "The bandit bows to you.";
                        Found(SecJackpot, at + new Vector2(0f, 30f));
                        break;
                    case SlotResult.ThreeCoins:
                        Gold(pd, 22); Fx(s_coins, at); Fx(s_confetti, at + new Vector2(0f, 20f));
                        ObjectKit.PlaySound("SoundGoldpickupMultiple", transform);
                        l1 = "Three coins: 22 gold!"; l2 = "";
                        break;
                    case SlotResult.TwoCoins:
                        Gold(pd, 6); Fx(s_coins, at);
                        ObjectKit.PlaySound("SoundGoldpickup", transform);
                        l1 = "Two coins: 6 gold."; l2 = "";
                        break;
                    case SlotResult.ThreeHearts:
                        if (pd != null) HealFull(pd.GameObject, 2f);
                        Fx(s_confetti, at + new Vector2(0f, 20f));
                        l1 = "Three hearts: 2 health back!"; l2 = "";
                        break;
                    case SlotResult.TwoHearts:
                        if (pd != null) HealFull(pd.GameObject, 0.5f);
                        l1 = "Two hearts: 0.5 health back."; l2 = "";
                        break;
                    case SlotResult.ThreeSkulls:
                        // the house feeds the dead: every ghost gets a full ectoplasm bar
                        PlayerData[] all = null;
                        try { all = SystemPlayers.GetPlayers(); } catch { }
                        if (all != null) foreach (var g in all) if (g != null && g.IsActive && !g.IsAlive) { try { g.OnEctoplasmCollected(3f); } catch { } }
                        ObjectKit.PlaySound("SoundSkeletonBark", transform);
                        l1 = "Three skulls. The dead laugh."; l2 = "Every ghost gets 3 ectoplasm.";
                        break;
                }
                if (res != SlotResult.Lose && res != SlotResult.ThreeSkulls && o != null) o.Play("Win");
                int left = SlotPulls - m_pulls;
                Say(pd, "Slot Machine", l1, l2, left > 0 ? left + (left == 1 ? " pull left." : " pulls left.") : "OUT OF ORDER");
            }

            void OnDisable() { Clear(); }
        }

        // ------------------------------------------------------------------ 6. Fortune Teller
        static readonly string[] Fortunes =
        {
            "Keep tossing coins in wells. The hundredth one counts.",
            "The bandit pays crowns to the patient.",
            "Hit the cracked wall. Keep hitting it.",
            "A ghost with ectoplasm to spare should visit the sculptor.",
            "There is a goat full of sugar. Hit it.",
            "Dance on the light, never in the dark.",
            "The one who lights the fuse should not stand near it.",
            "A ghost needs that urn more than you do.",
            "A painted man is shy. Be patient with him.",
            "Gold glitters brightest when it squeaks.",
            "Something in the next room bites.",
            "Mind the stairs.",
            "Two hearts on the reels will patch you up.",
            "Buy the potion. Trust me.",
        };

        static void RegFortune()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Fortune, name = "Fortune Teller", art = "ObjBFortuneTeller",
                vault = "Madame Ossa reads the cards, for a few coins",
                tip1 = "Pay for a fortune. Some hint at secrets",
                tip2 = "Good fortune may heal you. Only a few readings",
                kind = ObjKind.Use, users = ObjUser.Hero, actionText = "ASK", uses = FortuneReads, cooldown = 1.5f,
                costGold = FortuneCost, bounce = false, useSound = "SoundHauntCastStart",
                onUse = u => u.obj.StartCoroutine(Read(u.obj, u.pd)),
                spawn = Spawn(5f, 1, Calm),
                useBox = new Vector2(28f, 24f), bodySize = new Vector2(20f, 6f),
            });
        }

        /// <summary>Wrap a line in two at a space near the middle when it is long.</summary>
        static void Split(string s, out string a, out string b)
        {
            a = s; b = string.Empty;
            if (s == null || s.Length <= 44) return;
            int mid = s.Length / 2, best = -1;
            for (int d = 0; d < mid; d++)
            {
                if (mid + d < s.Length && s[mid + d] == ' ') { best = mid + d; break; }
                if (mid - d > 0 && s[mid - d] == ' ') { best = mid - d; break; }
            }
            if (best < 0) return;
            a = s.Substring(0, best); b = s.Substring(best + 1);
        }

        static IEnumerator Read(ModObject o, PlayerData pd)
        {
            yield return new WaitForSeconds(0.7f);
            if (o == null) yield break;
            Fx(s_card, P(o.gameObject) + new Vector2(0f, 3f));
            // 60 percent: the riddle of a secret nobody has found yet (any secret of the game), else a fortune
            string text = null, rarity = null;
            if (UnityEngine.Random.value < 0.6f)
            {
                var open = new List<SecretDef>();
                foreach (var e in Secrets.All) { try { if (!Secrets.IsFound(e.id) && !string.IsNullOrEmpty(e.riddle)) open.Add(e); } catch { } }
                if (open.Count > 0)
                {
                    var e = open[UnityEngine.Random.Range(0, open.Count)];
                    text = e.riddle; rarity = string.IsNullOrEmpty(e.rarity) ? null : "The cards say: " + e.rarity + ".";
                }
            }
            if (text == null) text = Fortunes[UnityEngine.Random.Range(0, Fortunes.Length)];
            string a, b;
            Split(text, out a, out b);
            string bless = null;
            if (UnityEngine.Random.value < 1f / 6f && pd != null)
            {
                if (Hurt(pd.GameObject)) { HealFull(pd.GameObject, 1f); bless = "Good fortune: 1 health back."; }
                else { Gold(pd, 3); bless = "Good fortune: your 3 gold back."; }
                ObjectKit.PlaySound("SoundStatUpFromProp", o.transform);
                Fx(s_sparkle, P(o.gameObject) + new Vector2(0f, 20f));
            }
            string extra = bless ?? rarity;
            Say(pd, "Fortune", a, b, extra);
        }

        // ------------------------------------------------------------------ 7. Bounce Shroom
        static void RegShroom()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Shroom, name = "Bounce Shroom", art = "ObjBBounceShroom",
                vault = "A mushroom so springy it throws you",
                tip1 = "Step on it to go flying",
                tip2 = "Heroes and monsters. A short wait between bounces",
                kind = ObjKind.Touch, users = ObjUser.Living, uses = 0, touchRadius = 6f, rearm = 1.2f,
                offDuringFight = false, useSound = "SoundShamanMask_Bounce",
                onUse = u => Bounce(u),
                spawn = Spawn(7f, 1, Rooms, max: 2),
                useBox = new Vector2(20f, 14f), bodySize = Vector2.zero,
            });
        }

        static void Bounce(ObjUse u)
        {
            var body = u.Body;
            if (body == null) return;
            var mv = body.GetComponent<PlayerMovement>();
            if (mv == null) return;
            Vector2 v = Vector2.zero;
            try { v = R.Get<Vector2>(mv, "m_velocity"); } catch { }
            Vector2 dir = v.sqrMagnitude > 4f ? v.normalized : ((Vector2)body.transform.position - u.At);
            if (dir.sqrMagnitude < 0.01f) dir = UnityEngine.Random.insideUnitCircle;
            dir.Normalize();
            try { mv.Push(dir * 240f, 0.3f); } catch { }
            Fx(s_spores, u.At + new Vector2(0f, 12f));
        }

        // ------------------------------------------------------------------ 8. Firework Crate
        static void RegFireworks()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Fireworks, name = "Firework Crate", art = "ObjBFireworkCrate",
                vault = "Six rockets and a very short fuse. Point away from face",
                tip1 = "Light it: rockets burst on foes",
                tip2 = "Hero lights hit monsters. Ghost lights hit the hero",
                kind = ObjKind.Use, users = ObjUser.Hero | ObjUser.Ghost, actionText = "LIGHT", uses = 1,
                offDuringFight = false, bounce = false, useSound = "SoundGoblinBombFuse",
                once = new HashSet<string> { "Launch" }, then = new Dictionary<string, string> { { "Launch", "Spent" } },
                onUse = u => { u.obj.Play("Lit"); u.obj.StartCoroutine(Launch(u.obj, u.pd)); },
                spawn = Spawn(5f, 2, Rooms),
                useBox = new Vector2(30f, 22f), bodySize = new Vector2(18f, 6f),
            });
        }

        static IEnumerator Launch(ModObject o, PlayerData by)
        {
            yield return new WaitForSeconds(FuseTime);
            if (o == null || !o.gameObject.activeInHierarchy) yield break;
            o.Play("Launch");
            bool heroLit = by != null && by.IsHero;
            var room = RoomOf(o);
            Vector2 from = P(o.gameObject) + new Vector2(0f, 20f);
            for (int i = 0; i < 6; i++)
            {
                Vector2 target;
                if (heroLit)
                {
                    var foes = MonstersIn(room);
                    target = foes.Count > 0 ? (Vector2)foes[UnityEngine.Random.Range(0, foes.Count)].transform.position
                                            : P(o.gameObject) + UnityEngine.Random.insideUnitCircle * 60f;
                }
                else
                {
                    var hero = ModUtil.Hero();
                    target = (hero != null ? (Vector2)hero.transform.position : P(o.gameObject)) + UnityEngine.Random.insideUnitCircle * 16f;
                }
                target = ModUtil.SafePoint(P(o.gameObject), target);
                o.StartCoroutine(Rocket(o.gameObject, by, heroLit, from, target, i));
                ObjectKit.PlaySound("SoundTrapRapidfireShoot", o.transform);
                yield return new WaitForSeconds(0.12f);
            }
        }

        static IEnumerator Rocket(GameObject crate, PlayerData by, bool heroLit, Vector2 from, Vector2 to, int n)
        {
            var r = Fx(s_rocket, from);
            float t = 0f, T = 0.7f;
            Vector2 prev = from;
            while (t < T)
            {
                t += Time.deltaTime;
                float k = Mathf.Clamp01(t / T);
                Vector2 p = Vector2.Lerp(from, to, k) + new Vector2(0f, 46f * 4f * k * (1f - k));
                if (r != null)
                {
                    r.transform.position = new Vector3(p.x, p.y, r.transform.position.z);
                    var d = p - prev;
                    if (d.sqrMagnitude > 0.0001f) r.transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
                }
                prev = p;
                yield return null;
            }
            Kill(r);
            var tmpl = (heroLit ? s_fwHero : s_fwTrap)[n % 4];
            if (tmpl == null) yield break;
            DamageSource src = heroLit ? ModUtil.HeroSource() : new DamageSource(crate, crate, by);
            try { FxFactory.SpawnOwned(tmpl, to, src); } catch (Exception e) { Plugin.Log.LogWarning("Firework: " + e.Message); }
            ObjectKit.PlaySound("SoundDeathExplosionSmall", crate != null ? crate.transform : null);
        }

        // ------------------------------------------------------------------ 9. Lever Trio + its hatch
        static void RegLevers()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Levers, name = "Lever Trio", art = "ObjBLeverTrio",
                vault = "Three levers: sun, moon and star",
                tip1 = "Pull the levers in the right order",
                tip2 = "Three wrong tries and they jam for good",
                kind = ObjKind.Use, users = ObjUser.Hero, actionText = "PULL", uses = 0, cooldown = 0.5f,
                bounce = false, useSound = "SoundTrapPlungerDown",
                once = new HashSet<string> { "Buzz" }, then = new Dictionary<string, string> { { "Buzz", "Idle" } },
                onUse = u => Brain<LeverBrain>(u.obj.gameObject).Pull(u),
                onSpawned = go => Brain<LeverBrain>(go).Setup(),
                spawn = Spawn(3f, 2, Calm),
                useBox = new Vector2(40f, 26f), bodySize = new Vector2(28f, 6f),
            });
            ObjectKit.Register(new ObjectDef
            {
                id = Stash, name = "Hidden Hatch", art = "ObjBHatch",
                vault = "A trapdoor that opens for those who read the floor",
                tip1 = "Open: gold and a ration", tip2 = "The levers opened it",
                kind = ObjKind.Use, users = ObjUser.Hero, actionText = "OPEN", uses = 1, offDuringFight = false,
                useSound = "SoundDoorCreakAnimated", then = new Dictionary<string, string> { { "Use", "Spent" } },
                onUse = u => u.obj.StartCoroutine(OpenStash(u)),
                spawn = new ObjSpawn { weight = 0f },
                useBox = new Vector2(26f, 20f), bodySize = new Vector2(16f, 8f), bodyY = 4f,
            });
        }

        static IEnumerator OpenStash(ObjUse u)
        {
            yield return new WaitForSeconds(0.3f);
            Fx(s_coins, u.At + new Vector2(0f, 4f));
            ObjectKit.PlaySound("SoundGoldpickupMultiple", u.obj != null ? u.obj.transform : null);
            Gold(u.pd, 30);
            if (u.pd != null) HealFull(u.pd.GameObject, 1f);
            Say(u.pd, "Hidden Hatch", "30 gold and a ration: 1 health back.", "");
        }

        public class LeverBrain : MonoBehaviour
        {
            static readonly float[] LeverX = { -9f, 0f, 9f };
            const float LeverY = 10f, PlaqueY = 19f, ScratchY = -8f;
            static readonly string[] Glyph = { "Sun", "Moon", "Star" };
            readonly int[] m_plaque = new int[3];      // glyph index on each lever's plaque (left to right)
            readonly int[] m_order = new int[3];       // the glyph order scratched on the floor
            readonly bool[] m_down = new bool[3];
            readonly GameObject[] m_lever = new GameObject[3];
            readonly List<GameObject> m_deco = new List<GameObject>();
            int m_step, m_mistakes;
            bool m_done;

            static void Shuffle(int[] a)
            {
                for (int i = 0; i < 3; i++) a[i] = i;
                for (int i = 2; i > 0; i--) { int j = UnityEngine.Random.Range(0, i + 1); int t = a[i]; a[i] = a[j]; a[j] = t; }
            }

            public void Setup()
            {
                StopAllCoroutines();
                Clean();
                Shuffle(m_plaque); Shuffle(m_order);
                m_step = 0; m_mistakes = 0; m_done = false;
                for (int i = 0; i < 3; i++)
                {
                    m_deco.Add(Child(s_glyphs[Glyph[m_plaque[i]]], transform, LeverX[i], PlaqueY));
                    // the clue: the order, faintly scratched into the floor in front (a floor decal)
                    m_deco.Add(Child(s_glyphs["Scratch" + Glyph[m_order[i]]], transform, LeverX[i], ScratchY, 90f));
                    m_down[i] = false;
                    m_lever[i] = Child(s_leverUp, transform, LeverX[i], LeverY);
                }
            }

            void Clean()
            {
                foreach (var g in m_deco) Kill(g);
                m_deco.Clear();
                for (int i = 0; i < 3; i++) { Kill(m_lever[i]); m_lever[i] = null; }
            }

            void SetLever(int i, bool down)
            {
                Kill(m_lever[i]);
                m_lever[i] = Child(down ? s_leverDown : s_leverUp, transform, LeverX[i], LeverY);
                m_down[i] = down;
            }

            public void Pull(ObjUse u)
            {
                if (m_done) return;
                // the lever nearest the hero (left / middle / right of the console)
                float dx = u.Body != null ? u.Body.transform.position.x - transform.position.x : 0f;
                int i = dx < -4.5f ? 0 : dx > 4.5f ? 2 : 1;
                if (m_down[i]) { Say(u.pd, "Lever Trio", "That lever is already down.", "Pull another one."); return; }
                SetLever(i, true);
                if (m_plaque[i] == m_order[m_step])
                {
                    m_step++;
                    if (m_step >= 3) StartCoroutine(Solved(u));
                    return;
                }
                m_mistakes++;
                StartCoroutine(Wrong(u, m_mistakes >= 3));
            }

            IEnumerator Wrong(ObjUse u, bool jam)
            {
                var o = u.obj;
                yield return new WaitForSeconds(0.2f);
                if (o != null) o.Play("Buzz");
                Fx(s_dust, (Vector2)transform.position + new Vector2(0f, 2f));
                ObjectKit.PlaySound("SoundPurchaseCantAfford", transform);
                yield return new WaitForSeconds(0.25f);
                for (int i = 0; i < 3; i++) SetLever(i, false);
                m_step = 0;
                if (jam)
                {
                    m_done = true;
                    if (o != null) { o.Spent(); o.Play("Jam"); }
                    Say(u.pd, "Lever Trio", "Wrong again. The levers jam for good.", "");
                }
                else Say(u.pd, "Lever Trio", "Wrong order. The levers spring back.", (3 - m_mistakes) + (3 - m_mistakes == 1 ? " try left." : " tries left."));
            }

            IEnumerator Solved(ObjUse u)
            {
                m_done = true;
                var o = u.obj;
                if (o != null) o.Spent();
                yield return new WaitForSeconds(0.35f);
                ObjectKit.PlaySound("SoundDoorOpenAnimated", transform);
                Vector2 at = (Vector2)transform.position + new Vector2(0f, -24f);
                Fx(s_dust, at);
                Found(SecLevers, (Vector2)transform.position + new Vector2(0f, 26f));
                var room = RoomOf(o);
                var hatch = room != null ? ObjectKit.SpawnAt(Stash, room, at) : null;
                if (hatch == null)
                {
                    Gold(u.pd, 30);
                    if (u.pd != null) HealFull(u.pd.GameObject, 1f);
                    Fx(s_coins, at);
                    Say(u.pd, "Lever Trio", "Click. Something falls out: 30 gold", "and 1 health back.");
                }
                else Say(u.pd, "Lever Trio", "Click, click, click. A hatch opens", "in the floor.");
            }

            void OnDisable() { Clean(); }
        }

        // ------------------------------------------------------------------ 10. Cracked Wall
        static void RegWall()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Wall, name = "Cracked Wall", art = "ObjBCrackedWall",
                vault = "An old wall with a hairline crack",
                tip1 = "Old stone. It does not look very strong",
                tip2 = "",
                kind = ObjKind.Use, users = ObjUser.Hero, uses = 0, canUse = u => false,
                once = new HashSet<string> { "Hit", "Crumble" }, then = new Dictionary<string, string> { { "Crumble", "Spent" } },
                customize = go => Hittable(go, 28f, 30f, 14f),
                onSpawned = go => Brain<WallBrain>(go).Reset(),
                spawn = Spawn(3f, 2, Rooms, place: ObjPlace.Wall),
                useBox = new Vector2(36f, 26f), bodySize = new Vector2(26f, 8f), bodyY = 3f,
            });
        }

        public class WallBrain : MonoBehaviour
        {
            int m_hits;
            float m_last;
            ModObject m_obj;

            public void Reset() { m_hits = 0; m_last = -10f; StopAllCoroutines(); }

            void OnDamaged(DamageInfo info) { Hit(); }
            void OnKilled(DamageInfo info) { Hit(); }

            void Hit()
            {
                if (m_hits >= 4 || Time.time - m_last < 0.3f) return;
                m_last = Time.time;
                if (m_obj == null) m_obj = GetComponent<ModObject>();
                if (m_obj == null) return;
                m_hits++;
                Fx(s_dust, (Vector2)transform.position + new Vector2(0f, 4f));
                if (m_hits < 4)
                {
                    ObjectKit.PlaySound("SoundTrollRockLand", transform);
                    m_obj.Play("Hit");
                    StartCoroutine(Then(0.09f, "Crack" + m_hits));
                    return;
                }
                ObjectKit.PlaySound("SoundDeathCrumbleLoud", transform);
                m_obj.Play("Crumble");
                m_obj.Spent();
                StartCoroutine(Open());
            }

            IEnumerator Then(float t, string s)
            {
                yield return new WaitForSeconds(t);
                if (m_obj != null && m_hits < 4) m_obj.Play(s);
            }

            IEnumerator Open()
            {
                yield return new WaitForSeconds(0.65f);
                var hero = SystemPlayers.GetHeroPlayerData();
                if (hero != null && m_obj != null) ObjectKit.Discovered(hero, gameObject, m_obj.def);
                Vector2 at = (Vector2)transform.position;
                Found(SecWall, at + new Vector2(0f, 20f));
                GameObject key = null;
                bool has = false;
                try { has = hero != null && SecretItems.HasSkeletonKey(hero); } catch { }
                if (!has) { try { key = SecretItems.DropSkeletonKey(new Vector3(at.x, at.y - 6f, 0f)); } catch (Exception e) { Plugin.Log.LogWarning("Cracked Wall key: " + e.Message); } }
                if (key != null)
                {
                    ObjectKit.PlaySound("SoundHealthPickupSpawn", transform);
                    Say(hero, "Cracked Wall", "The wall gives way. In the niche:", "a key made of bone.");
                }
                else
                {
                    Gold(hero, 25);
                    Fx(s_coins, at);
                    ObjectKit.PlaySound("SoundGoldpickupMultiple", transform);
                    Say(hero, "Cracked Wall", "The wall gives way. In the niche:", "an old purse, 25 gold.");
                }
            }
        }

        // ------------------------------------------------------------------ 11. Mysterious Keyhole + Reliquary
        static void RegKeyhole()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Keyhole, name = "Mysterious Keyhole", art = "ObjBKeyhole",
                vault = "A keyhole in a slab of stone, with no door around it. It hums",
                tip1 = "A keyhole with no door",
                tip2 = "It wants a key made of bone",
                kind = ObjKind.Use, users = ObjUser.Hero, actionText = "UNLOCK", uses = 0, cooldown = 1f, bounce = false,
                useSound = "",
                once = new HashSet<string> { "Locked", "Unlock" },
                then = new Dictionary<string, string> { { "Locked", "Idle" }, { "Unlock", "Spent" } },
                onUse = u => Unlock(u),
                spawn = Spawn(2.5f, 3, Calm),
                useBox = new Vector2(30f, 26f), bodySize = new Vector2(20f, 6f),
            });
            ObjectKit.Register(new ObjectDef
            {
                id = Reliquary, name = "Golden Reliquary", art = "ObjBReliquary",
                vault = "A gold box that rose out of the floor. It beats",
                tip1 = "Open: the Gilded Heart and a purse of gold", tip2 = "",
                kind = ObjKind.Use, users = ObjUser.Hero, actionText = "OPEN", uses = 1, offDuringFight = false,
                useSound = "SoundPortalOpen",
                once = new HashSet<string> { "Rise" }, then = new Dictionary<string, string> { { "Rise", "Idle" }, { "Use", "Spent" } },
                onUse = u => u.obj.StartCoroutine(OpenReliquary(u)),
                onSpawned = go => Brain<RiseBrain>(go).Arm(),
                spawn = new ObjSpawn { weight = 0f },
                useBox = new Vector2(28f, 24f), bodySize = new Vector2(18f, 6f),
            });
        }

        /// <summary>Plays "Rise" on the first Update (the state machine starts on Idle).</summary>
        public class RiseBrain : MonoBehaviour
        {
            bool m_armed;
            public void Arm() { m_armed = true; }
            void Update()
            {
                if (!m_armed) return;
                m_armed = false;
                var mo = GetComponent<ModObject>();
                if (mo != null) mo.Play("Rise");
            }
        }

        static void Unlock(ObjUse u)
        {
            bool ok = false;
            try { ok = SecretItems.ConsumeSkeletonKey(u.pd); } catch (Exception e) { Plugin.Log.LogWarning("Keyhole: " + e.Message); }
            if (!ok)
            {
                u.obj.Play("Locked");
                ObjectKit.PlaySound("SoundPurchaseCantAfford", u.obj.transform);
                Say(u.pd, "Mysterious Keyhole", "Locked. It wants a key made of bone.", "");
                return;
            }
            u.obj.Play("Unlock");
            u.obj.Spent();
            ObjectKit.PlaySound("SoundPortalActivate", u.obj.transform);
            Found(SecKeyhole, u.At + new Vector2(0f, 24f));
            Say(u.pd, "Mysterious Keyhole", "The bone key turns. The slab sinks", "into the floor...");
            u.obj.StartCoroutine(Raise(u.obj));
        }

        static IEnumerator Raise(ModObject o)
        {
            yield return new WaitForSeconds(0.95f);
            if (o == null) yield break;
            var room = RoomOf(o);
            Vector2 at = P(o.gameObject);
            var rel = room != null ? ObjectKit.SpawnAt(Reliquary, room, at) : null;
            Fx(s_dust, at);
            if (rel != null) { Kill(o.gameObject); yield break; }
            // nowhere to put it: give its contents straight away
            var hero = SystemPlayers.GetHeroPlayerData();
            GiveRelic(hero, at);
        }

        static IEnumerator OpenReliquary(ObjUse u)
        {
            yield return new WaitForSeconds(0.35f);
            GiveRelic(u.pd, u.At);
        }

        static void GiveRelic(PlayerData hero, Vector2 at)
        {
            GameObject heart = null;
            try { heart = SecretItems.DropGildedHeart(new Vector3(at.x, at.y - 4f, 0f)); } catch (Exception e) { Plugin.Log.LogWarning("Reliquary: " + e.Message); }
            int gold = heart != null ? 25 : 60;
            Gold(hero, gold);
            Fx(s_gold, at + new Vector2(0f, 16f));
            Fx(s_coins, at);
            ObjectKit.PlaySound("SoundGoldpickupMultiple", null);
            Say(hero, "Golden Reliquary", heart != null ? "Inside beats the Gilded Heart." : "Inside: a pile of old crowns.", gold + " gold as well.");
        }

        // ------------------------------------------------------------------ 12. Sculptor's Altar
        static void RegAltar()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Altar, name = "Sculptor's Altar", art = "ObjBSculptorAltar",
                vault = "Hammer, chisel and an empty plinth",
                tip1 = "Ghosts: pay ectoplasm for a secret statue",
                tip2 = "Then take it. Rarely, it is the legendary one",
                kind = ObjKind.Use, users = ObjUser.Ghost, actionText = "CARVE", uses = 1, costEcto = 3,
                offDuringFight = false, bounce = false, useSound = "SoundGargoyleTurnToStone",
                secret = SecAltar, then = new Dictionary<string, string> { { "Use", "Spent" } },
                onUse = u => u.obj.StartCoroutine(Carve(u)),
                spawn = Spawn(2f, 2, ObjRoom.Quiet | ObjRoom.Statue),
                useBox = new Vector2(32f, 26f), bodySize = new Vector2(26f, 6f),
            });
        }

        /// <summary>
        /// Where the carved statue stands: in front of the altar if there is room, else beside or behind it. Each candidate
        /// is pulled back from walls (ModUtil.SafePoint), must keep a 10 px margin inside the room and must not overlap any
        /// prop the room already reserved (its prop rects, which include the altar's own). The chosen footprint is then
        /// reserved with Room.AddPropRect so later props keep clear of it. Null when nothing fits.
        /// </summary>
        static Vector2? StatueSpot(ModObject o)
        {
            if (o == null) return null;
            var room = RoomOf(o);
            Vector2 a = P(o.gameObject);
            List<Rect> rects = null;
            try { if (room != null) rects = R.Get<List<Rect>>(room, "m_propRects"); } catch { }
            var offs = new[] { new Vector2(0f, -22f), new Vector2(-30f, -6f), new Vector2(30f, -6f), new Vector2(0f, -34f),
                               new Vector2(-30f, -22f), new Vector2(30f, -22f), new Vector2(0f, 20f) };
            foreach (var off in offs)
            {
                var want = a + off;
                var p = ModUtil.SafePoint(a, want, 12f);
                if ((p - want).sqrMagnitude > 4f) continue;                    // a wall cut it short
                bool inside = InRoom(room, p);
                foreach (var m in new[] { new Vector2(10f, 0f), new Vector2(-10f, 0f), new Vector2(0f, 10f), new Vector2(0f, -10f) })
                    inside &= InRoom(room, p + m);
                if (!inside) continue;
                var foot = new Rect(p.x - 9f, p.y - 2f, 18f, 12f);             // the statue's plinth footprint
                bool clash = false;
                if (rects != null) foreach (var r in rects) if (r.Overlaps(foot)) { clash = true; break; }
                if (clash) continue;
                try { if (room != null) room.AddPropRect(foot); } catch { }
                return p;
            }
            return null;
        }

        static IEnumerator Carve(ObjUse u)
        {
            var spot = StatueSpot(u.obj);
            if (spot == null)
            {
                u.Ecto(3f);
                if (u.obj != null) u.obj.Rearm();
                Say(u.pd, "Sculptor's Altar", "No room here for a statue. Your", "ectoplasm is returned.");
                yield break;
            }
            Vector2 at = spot.Value;
            Fx(s_statueForm, at);
            yield return new WaitForSeconds(0.75f);
            GameObject st = null;
            try { st = SecretStatues.SpawnSecretStatue(new Vector3(at.x, at.y, 0f), u.obj != null ? u.obj.transform.parent : null, StatueLegendary); }
            catch (Exception e) { Plugin.Log.LogWarning("Sculptor's Altar: " + e.Message); }
            Fx(s_dust, at);
            if (st == null)
            {
                u.Ecto(3f);
                Say(u.pd, "Sculptor's Altar", "The chisel slips. Your ectoplasm", "is returned.");
                yield break;
            }
            ObjectKit.PlaySound("SoundStatueLimbBurstSettle", u.obj != null ? u.obj.transform : null);
            Say(u.pd, "Sculptor's Altar", "A secret statue stands before you.", "Take it before someone else does!");
        }

        // ------------------------------------------------------------------ 13. Wishing Well
        static ConfigFile s_cfg;
        static ConfigEntry<int> s_wellCoins;

        static int WellCoins
        {
            get { Cfg(); return s_wellCoins != null ? s_wellCoins.Value : 0; }
            set { Cfg(); if (s_wellCoins != null) s_wellCoins.Value = value; }     // the ConfigFile saves itself on set (once)
        }

        static void Cfg()
        {
            if (s_cfg != null) return;
            try
            {
                s_cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, "CrawlFurther.ObjectsB.cfg"), true);
                s_wellCoins = s_cfg.Bind("Progress", "WellCoins", 0, "Coins tossed into wishing wells, all runs together (the Well Spirit rises at " + WellCoinsForSpirit + ").");
            }
            catch (Exception e) { Plugin.Log.LogWarning("ObjectsB config: " + e.Message); }
        }

        static void RegWell()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Well, name = "Wishing Well", art = "ObjBWishingWell",
                vault = "Toss a coin, make a wish. The well counts every coin",
                tip1 = "Toss in gold. Now and then a wish comes true",
                tip2 = "A wish heals you, or pays gold if unhurt",
                kind = ObjKind.Use, users = ObjUser.Hero, actionText = "TOSS COIN", uses = WellTosses, cooldown = 0.6f,
                costGold = 1, bounce = false, useSound = "SoundStoreTeleportUpFlipCoin",
                once = new HashSet<string> { "Wish" }, then = new Dictionary<string, string> { { "Wish", "Idle" } },
                onUse = u => u.obj.StartCoroutine(Toss(u)),
                spawn = Spawn(5f, 1, Calm),
                useBox = new Vector2(26f, 22f), bodySize = new Vector2(18f, 6f), bodyY = 3f,   // v0.10: the well was redrawn at vanilla well size
            });
        }

        static IEnumerator Toss(ObjUse u)
        {
            int coins = WellCoins + 1;
            WellCoins = coins;
            yield return new WaitForSeconds(0.3f);
            ObjectKit.PlaySound("SoundIntroWater", u.obj != null ? u.obj.transform : null);
            bool spirit = coins >= WellCoinsForSpirit && !Secrets.IsFound(SecWell);
            if (spirit)
            {
                if (u.obj != null) u.obj.Play("Wish");
                Fx(s_spirit, u.At + new Vector2(0f, 8f));
                ObjectKit.PlaySound("SoundHymn1", u.obj != null ? u.obj.transform : null);
                yield return new WaitForSeconds(0.8f);
                if (u.pd != null) HealFull(u.pd.GameObject, 99f);
                Gold(u.pd, 30);
                Found(SecWell, u.At + new Vector2(0f, 30f));
                Say(u.pd, "The Well Spirit", "A hundred coins! The Well Spirit rises:", "full health and 30 gold.");
                yield break;
            }
            if (UnityEngine.Random.value < 0.1f)
            {
                if (u.obj != null) u.obj.Play("Wish");
                ObjectKit.PlaySound("SoundStatUpFromProp", u.obj != null ? u.obj.transform : null);
                Fx(s_sparkle, u.At + new Vector2(0f, 14f));
                if (u.pd != null && Hurt(u.pd.GameObject)) { HealFull(u.pd.GameObject, 1f); Say(u.pd, "Wishing Well", "Your wish comes true: 1 health back.", coins + " coins in wells so far."); }
                else { Gold(u.pd, 3); Say(u.pd, "Wishing Well", "Your wish comes true: 3 gold back.", coins + " coins in wells so far."); }
                yield break;
            }
            Say(u.pd, "Wishing Well", u.obj != null && u.obj.IsSpent ? "Plip. The well is full of coins now." : "Plip.", coins + " coins in wells so far.");
        }

        // ------------------------------------------------------------------ 14. Watching Portrait
        static void RegPortrait()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Portrait, name = "Watching Portrait", art = "ObjBPortrait",
                vault = "A stern noble in a gilt frame",
                tip1 = "His eyes follow you around the room",
                tip2 = "He seems to be waiting for something",
                kind = ObjKind.Use, users = ObjUser.Hero, uses = 0, canUse = u => false,
                once = new HashSet<string> { "Wink", "Swing" }, then = new Dictionary<string, string> { { "Wink", "Swing" }, { "Swing", "Spent" } },
                onSpawned = go => Brain<PortraitBrain>(go).Reset(),
                spawn = Spawn(3f, 1, Calm, place: ObjPlace.Wall),
                useBox = new Vector2(30f, 26f), bodySize = new Vector2(22f, 6f),
            });
        }

        public class PortraitBrain : MonoBehaviour
        {
            ModObject m_obj;
            string m_eyes = "Idle";
            Vector2 m_lastPos;
            float m_still;
            bool m_done;

            public void Reset() { m_eyes = "Idle"; m_still = 0f; m_done = false; m_lastPos = Vector2.zero; StopAllCoroutines(); }

            void Update()
            {
                if (m_done) return;
                if (m_obj == null) m_obj = GetComponent<ModObject>();
                if (m_obj == null || m_obj.IsOff) return;
                var hero = ModUtil.Hero();
                if (hero == null) return;
                Vector2 hp = hero.transform.position, me = transform.position;
                var d = hp - me;
                bool near = d.magnitude < 70f && InRoom(RoomOf(m_obj), hp);
                string eyes = !near ? "Idle" : d.x < -8f ? "EyesL" : d.x > 8f ? "EyesR" : "Idle";
                if (eyes != m_eyes && (m_obj.State == "Idle" || m_obj.State == "EyesL" || m_obj.State == "EyesR"))
                {
                    m_eyes = eyes;
                    m_obj.Play(eyes);
                }
                // stand still in front of him (within 44 px, below him) for 5 s
                bool front = d.y < 2f && d.magnitude < 44f;
                if (front && (hp - m_lastPos).sqrMagnitude < 0.05f) m_still += Time.deltaTime;
                else m_still = 0f;
                m_lastPos = hp;
                if (m_still >= StillTime) StartCoroutine(Open());
            }

            IEnumerator Open()
            {
                m_done = true;
                m_obj.Play("Wink");
                m_obj.Spent();
                ObjectKit.PlaySound("SoundDoorCreakAnimated", transform);
                var hero = SystemPlayers.GetHeroPlayerData();
                if (hero != null) ObjectKit.Discovered(hero, gameObject, m_obj.def);
                yield return new WaitForSeconds(0.96f);
                Vector2 at = (Vector2)transform.position + new Vector2(0f, 8f);
                Gold(hero, 25);
                Fx(s_coins, at);
                ObjectKit.PlaySound("SoundGoldpickupMultiple", transform);
                Found(SecPortrait, at + new Vector2(0f, 24f));
                Say(hero, "Watching Portrait", "He winks. The frame swings open:", "25 gold on the shelf.");
            }
        }

        // ------------------------------------------------------------------ 15. Golden Duck
        static void RegDuck()
        {
            ObjectKit.Register(new ObjectDef
            {
                id = Duck, name = "Golden Duck", art = "ObjBGoldenDuck",
                vault = "A tiny golden rubber duck",
                tip1 = "Squeak it! Gold, health or ectoplasm for whoever does",
                tip2 = "Very rare",
                kind = ObjKind.Use, users = ObjUser.Anyone, actionText = "SQUEAK", uses = 1, offDuringFight = false,
                useSound = "SoundShamanMask_Squeeze", secret = SecDuck,
                onUse = u => u.obj.StartCoroutine(Squeak(u)),
                spawn = new ObjSpawn { weight = 0f, chance = DuckRoomChance, rooms = Rooms, place = ObjPlace.Anywhere },
                useBox = new Vector2(18f, 16f), bodySize = new Vector2(6f, 3f),
            });
        }

        static IEnumerator Squeak(ObjUse u)
        {
            Fx(s_gold, u.At + new Vector2(0f, 6f));
            if (u.IsHero) { Gold(u.pd, 25); Say(u.pd, "Golden Duck", "Squeak! 25 gold.", ""); }
            else if (u.IsMonster) { u.Heal(2f); Say(u.pd, "Golden Duck", "Squeak! 2 health back.", ""); }
            else { u.Ecto(3f); Say(u.pd, "Golden Duck", "Squeak! 3 ectoplasm.", ""); }
            ObjectKit.PlaySound("SoundGoldpickupMultiple", u.obj != null ? u.obj.transform : null);
            yield return new WaitForSeconds(0.45f);
            if (u.obj != null)
            {
                Fx(s_sparkle, u.At + new Vector2(0f, 4f));
                Kill(u.obj.gameObject);
            }
        }

        // ------------------------------------------------------------------ dynamic odds (before the kit fills a room)
        /// <summary>Keyhole: likely (weight 25) on the floors where the hero carries the Skeleton Key, else rare (2.5).</summary>
        internal static void BeforeRoomContent()
        {
            ObjectDef d;
            if (ObjectKit.Defs.TryGetValue(Keyhole, out d))
            {
                bool key = false;
                try { var h = SystemPlayers.GetHeroPlayerData(); key = h != null && SecretItems.HasSkeletonKey(h); } catch { }
                d.spawn.weight = key ? 25f : 2.5f;
            }
        }

        // ------------------------------------------------------------------ secrets
        static void RegSecrets()
        {
            Secrets.Add(new SecretDef
            {
                id = SecJackpot, group = "Objects", name = "Triple Crown", iconSheet = "ObjBSlotMachine",
                riddle = "Three crowns in a row and the bandit pays a king's ransom.",
                rarity = "Very rare",
                text = "Three crowns on the Slot Machine: the jackpot.",
            });
            Secrets.Add(new SecretDef
            {
                id = SecLevers, group = "Objects", name = "The Three Levers", iconSheet = "ObjBLeverTrio",
                riddle = "Before you pull, read the floor. The scratches keep the order.",
                rarity = "Rare room puzzle",
                text = "Pull the levers in the scratched order and a hidden hatch opens.",
            });
            Secrets.Add(new SecretDef
            {
                id = SecWall, group = "Objects", name = "The Cracked Wall", iconSheet = "ObjBCrackedWall",
                riddle = "One wall has a hairline crack. Strike it until it gives.",
                rarity = "Rare, floor 2 and deeper",
                text = "Four blows bring it down. In the niche behind it sleeps the Skeleton Key.",
            });
            Secrets.Add(new SecretDef
            {
                id = SecKeyhole, group = "Objects", name = "The Lock With No Door", iconSheet = "ObjBKeyhole",
                riddle = "A keyhole stands alone in a stone slab. It wants a key of bone.",
                rarity = "Rare, floor 3 and deeper",
                text = "The Skeleton Key turns, the slab sinks and a golden reliquary rises with the Gilded Heart inside.",
            });
            Secrets.Add(new SecretDef
            {
                id = SecAltar, group = "Objects", name = "The Sculptor's Altar", iconSheet = "ObjBSculptorAltar",
                riddle = "The sculptor works only for the dead, and only for a full bar.",
                rarity = "Rare, floor 2 and deeper",
                text = "A ghost pays ectoplasm and the altar carves a secret statue.",
            });
            Secrets.Add(new SecretDef
            {
                id = SecWell, group = "Objects", name = "The Well Spirit", iconSheet = "ObjBWishingWell",
                riddle = "Pennies make wishes. A hundred pennies make a friend.",
                rarity = "A hundred coins, over many runs",
                text = "A hundred coins in wishing wells raise the Well Spirit, who heals and pays.",
            });
            Secrets.Add(new SecretDef
            {
                id = SecPortrait, group = "Objects", name = "The Watching Portrait", iconSheet = "ObjBPortrait",
                riddle = "His eyes follow you. Stand still and stare back a while.",
                rarity = "Uncommon portrait, shy",
                text = "Stand still before the portrait and he winks, swings open and pays.",
            });
            Secrets.Add(new SecretDef
            {
                id = SecDuck, group = "Objects", name = "The Golden Duck", iconSheet = "ObjBGoldenDuck",
                riddle = "Somewhere a little golden duck wants squeezing.",
                rarity = "Very rare",
                text = "Squeak! Gold, health or ectoplasm for whoever squeezes it.",
            });
        }

        // ------------------------------------------------------------------ self-test
        public static void SelfCheck(Action<string> bad)
        {
            foreach (var id in Ids) if (!ObjectKit.Built.ContainsKey(id)) bad("objectsB: " + id + " not built");
            var fx = new Dictionary<string, GameObject>
            {
                { "notes", s_notes }, { "confetti", s_confetti }, { "rain", s_rain }, { "gold", s_gold }, { "blast", s_blast },
                { "rocket", s_rocket }, { "spores", s_spores }, { "coins", s_coins }, { "spirit", s_spirit }, { "card", s_card },
                { "sparkle", s_sparkle }, { "dust", s_dust }, { "jackpot", s_jackpot }, { "statueForm", s_statueForm },
                { "leverUp", s_leverUp }, { "leverDown", s_leverDown },
            };
            foreach (var kv in fx) if (kv.Value == null) bad("objectsB fx " + kv.Key + " missing");
            foreach (var kv in s_tiles) if (kv.Value == null) bad("objectsB tile " + kv.Key + " missing");
            foreach (var kv in s_symbols) if (kv.Value == null) bad("objectsB reel symbol " + kv.Key + " missing");
            foreach (var kv in s_glyphs) if (kv.Value == null) bad("objectsB glyph " + kv.Key + " missing");
            for (int i = 0; i < 4; i++) if (s_fwHero[i] == null || s_fwTrap[i] == null) bad("objectsB firework " + FwColours[i] + " missing");
            if (s_fever == null || s_hat == null || s_groove == null || Array.IndexOf(s_groove, null) >= 0) bad("objectsB indicators missing");
            // the documented slot odds add up and pay back less than they cost
            float ev = (1f / 150f) * 75f + 0.06f * 22f + 0.18f * 6f;
            if (ev >= SlotCost) bad("objectsB slot machine pays back " + ev + " per " + SlotCost);
            foreach (var e in Secrets.All)
            {
                if (e.group != "Objects" || !e.id.StartsWith("ObjB")) continue;
                if (e.riddle == null || e.riddle.Length > 75) bad("objectsB secret " + e.id + " riddle over 75");
                if (e.rarity == null || e.rarity.Length > 30) bad("objectsB secret " + e.id + " rarity over 30");
                if (e.text == null || e.text.Length > 120) bad("objectsB secret " + e.id + " text over 120");
                foreach (var t in new[] { e.name, e.riddle, e.rarity, e.text })
                    if (t != null && t.IndexOfAny("%{|}~[]".ToCharArray()) >= 0) bad("objectsB secret " + e.id + " has a forbidden character");
                if (SpriteSheets.Get(e.iconSheet) == null) bad("objectsB secret " + e.id + " picture sheet missing");
            }
            foreach (var f in Fortunes) if (f.IndexOfAny("%{|}~[]".ToCharArray()) >= 0) bad("objectsB fortune has a forbidden character: " + f);
        }
    }

    /// <summary>Before the kit rolls a room's objects: the keyhole odds of this moment.</summary>
    [HarmonyPatch(typeof(SystemLevel), "SpawnRoomContent")]
    static class Patch_ObjectsBRoomOdds
    {
        static void Prefix()
        {
            try { ObjectPack2.BeforeRoomContent(); } catch (Exception e) { Plugin.Log.LogWarning("ObjectsB odds: " + e.Message); }
        }
    }
}
