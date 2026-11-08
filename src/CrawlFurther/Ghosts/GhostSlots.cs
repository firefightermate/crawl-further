using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Ghosts;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Secrets;

    /// <summary>
    /// The silver and gold ghost slot mechanics (their ghost phase otherwise plays like the Wisp).
    ///
    /// SILVER, ASCENSION (no button): when the silver player's monster dies it drops 1-4 silver orbs (25 / 35 / 28 / 12
    /// percent) that pop out and settle near the body. Only that player's ghost picks them up, by touching them; they last
    /// 20 s (blinking for the last 3) and vanish if the room is left. Banked orbs (8 at most) carry over between ghost
    /// phases and circle the ghost as its tally (bright when all 8 are in). With 8 banked, the NEXT body the player takes
    /// (circle, statue or blob; never in a boss fight) is upgraded and the 8 are spent:
    ///   a body becomes a random monster one level deeper in its own tree (the player's god's tree, the idol's starters'
    ///   trees for an idol, the gold-secret line, else whichever god's tree holds it; vanilla trees are 4 deep, mod trees 3),
    ///   and a FINAL (nothing to evolve into: mod T3s, the Troll, Pope, Beholder...) ASCENDS: the same final at its own size, +30 percent max health
    ///   (healed to full), its own moonlit silver art (SilverVariants.cs: every tier-3 final, mod and vanilla, has
    ///   a re-rendered silver sheet), silver sparkles at its feet and silver sparks on every hit. The upgrade
    ///   is for that body only: the god's roster (the evolve screen) is not changed.
    /// The tells (visual and sound only, so bots and online play are untouched): from the eighth orb until the upgraded
    /// body is taken, a moonlit halo behind the ghost (FxSilverHalo) and a crescent moon over the player's head, ghost or
    /// monster (FxSilverMark); taking it, a column of moonlight, a silver ring and settling sparkles (FxSilverInhabit,
    /// about a second) with a chime. Art: tools/sprites/silver_tell_fx.py -> art/out_silvertell.
    ///
    /// GOLD, THRALLS: the ghost button (GhostControls.Down) while you are a monster
    /// JUMPS OUT: your ghost bursts out and the body stays as an AI thrall on the monsters' side, using its own attacks
    /// through the vanilla monster AI, tinted gold with a crown over it and a binding rune under it: its max health is
    /// halved and it is healed to 75 percent of that, and it hits at 60 percent. One thrall at a time: while it lives the
    /// button only shows a gold chain and padlock on your monster (also in boss fights). A thrall the hero kills bursts
    /// into 2 ectoplasm for you. Bots never get either form (bots always use the Wisp).
    /// </summary>
    public static class GhostSlots
    {
        // ------------------------------------------------------------------ tuning
        public const int MaxOrbs = 8;
        public static readonly float[] OrbOdds = { 0.25f, 0.35f, 0.28f, 0.12f };   // 1, 2, 3, 4 orbs (2.27 a death)
        public const float OrbLife = 20f, OrbReach = 9f, AscendScale = 1.0f, AscendHealth = 1.3f;   // no size-up (1.1x was a non-integer pixel scale); the silver art marks it
        public static readonly Color SilverTint = new Color(0.72f, 0.82f, 1f, 1f);
        public static readonly Color GoldTint = new Color(1f, 0.86f, 0.5f, 1f);
        public const float ThrallMaxHealth = 0.5f, ThrallHealTo = 0.75f, ThrallDamage = 0.6f;
        public const float ThrallBurstEcto = 2f;      // a third of a body (a body costs 6)
        public const float JumpCooldown = 1.5f;

        public static GameObject Orb, OrbCollect, Tally, TallyFull, Halo, Inhabit, AscendSpark;
        public static GameObject ThrallJump, ThrallLocked, ThrallBurst;
        public static StatusOverlayDef AscendAura, ReadyMark, Count, Mark, Sigil;
        /// <summary>The vanilla chime played with the inhabit moment (the healing rune's, at its own volume).</summary>
        public const string InhabitSound = "SoundGhostGirlHealRuneSpawn";

        public static void BuildFx()
        {
            Orb = Loop("ModGhostSilverOrb", "FxSilverOrb", "Idle", 12, 18);
            OrbCollect = GhostV11.CenteredFx("ModGhostSilverOrbCollect", "FxSilverOrb", "Collect", 12, 18);
            Tally = Loop("ModGhostOrbTally", "FxSoulWisp", "Orbit", 12, 8);
            TallyFull = Loop("ModGhostOrbTallyFull", "FxSoulWisp", "Bright", 12, 8);
            Halo = Loop("ModGhostSilverHalo", "FxSilverHalo", "Halo", 22, 37);
            Inhabit = GhostV11.CenteredFx("ModGhostSilverInhabit", "FxSilverInhabit", "Play", 36, 87);
            ReadyMark = ModStatus.Indicator("ModIndSilverReady", "FxSilverMark", "Loop", 1f, OverlayAt.Head);
            AscendSpark = GhostV11.CenteredFx("ModGhostAscendSpark", "FxAscendSpark", "Play", 14, 12);
            AscendAura = ModStatus.Indicator("ModIndAscended", "FxAscendAura", "Loop", -2f, OverlayAt.Feet);
            ThrallJump = GhostV11.CenteredFx("ModGhostThrallJump", "FxThrallJump", "Play", 17, 30);
            ThrallLocked = GhostV11.CenteredFx("ModGhostThrallLocked", "FxThrallLocked", "Play", 12, 20);
            ThrallBurst = GhostV11.CenteredFx("ModGhostThrallBurst", "FxThrallBurst", "Play", 20, 24);
            Mark = ModStatus.Indicator("ModIndThrallMark", "FxThrallMark", "Loop", 1f, OverlayAt.Head);
            Sigil = ModStatus.Indicator("ModIndThrallSigil", "FxThrallSigil", "Loop", -2f, OverlayAt.Feet);
            Count = ModStatus.Indicator("ModIndThrallCount", "FxThrallCount", "One", 1f, OverlayAt.Head);
            if (s_runner == null)
            {
                var go = new GameObject("CrawlMod_GhostSlots");
                UnityEngine.Object.DontDestroyOnLoad(go);
                s_runner = go.AddComponent<GhostSlotRunner>();
            }
        }
        static GhostSlotRunner s_runner;

        /// <summary>A looping visual the code places itself, its cell pixel (gx, gy) on the transform.</summary>
        static GameObject Loop(string name, string art, string anim, int gx, int gy)
        {
            var go = FxKit.Visual(name, art, anim, loop: true);
            if (go == null) return null;
            FxFactory.SetEffect(go, destroyOnAnimEnd: false, canFlip: false, freeRotate: false);
            Strike.ArtAt(go, art, gx, gy);
            FxKit.NoTint(go);
            return go;
        }

        public static void SelfCheck(Action<string> bad)
        {
            foreach (var go in new[] { Orb, OrbCollect, Tally, TallyFull, Halo, Inhabit, AscendSpark })
                if (go == null) bad("a silver Ascension effect failed to build");
            foreach (var go in new[] { ThrallJump, ThrallLocked, ThrallBurst })
                if (go == null) bad("a gold Thralls effect failed to build");
            if (AscendAura == null || ReadyMark == null || Mark == null || Sigil == null || Count == null) bad("silver / gold markers failed to build");
            if (s_runner == null) bad("silver / gold ghost runner missing");
            float sum = 0f; foreach (var o in OrbOdds) sum += o;
            if (Mathf.Abs(sum - 1f) > 0.001f) bad("silver orb odds do not add up to 1");
            try { CheckUpgrades(bad); } catch (Exception e) { bad("silver upgrade self-check threw: " + e.Message); }
        }

        // ------------------------------------------------------------------ per-player state
        internal class State
        {
            public float cd;
            // silver
            public int orbs;
            public bool pendingUpgrade, pendingAscend;
            public GameObject lastBody;
            public bool wasGhost;
            public readonly List<GameObject> tally = new List<GameObject>();
            public bool tallyFull;
            public GameObject halo, markOn;
            public bool markShown;
            // gold
            public ThrallMark thrall;
            public GameObject countOn;
            public bool countShown;
        }
        internal static readonly Dictionary<int, State> States = new Dictionary<int, State>();

        /// <summary>A new run: drop every player's orbs, tally, thrall reference and body memory (Patch_GhostSlotsNewRun).</summary>
        internal static void ResetRun()
        {
            foreach (var st in States.Values)
            {
                try
                {
                    ClearTally(st);
                    ClearReady(st);
                    if (st.countOn != null) ModInd.Set(st.countOn, Count, false);
                }
                catch { }
            }
            States.Clear();
            try { SilverVariants.ResetRun(); } catch { }
        }

        internal static State For(PlayerData pd)
        {
            State s;
            if (!States.TryGetValue(pd.Id, out s)) States[pd.Id] = s = new State();
            return s;
        }

        internal static bool IsSilver(PlayerData pd) { return pd != null && pd.IsHuman && GhostPack.FormOf(pd) == GhostForm.Silver; }

        /// <summary>The player is a live (non-ghost, non-hero) monster: the body they wear.</summary>
        internal static Player MonsterBody(PlayerData pd)
        {
            if (pd == null || pd.IsHero) return null;
            var go = pd.GameObject;
            var p = go != null ? go.GetComponent<Player>() : null;
            if (p == null || ModUtil.IsGhost(p) || p.GetIsAI()) return null;
            var h = p.GetComponent<Health>();
            return h != null && h.IsAlive() ? p : null;
        }

        // ------------------------------------------------------------------ silver: orbs
        /// <summary>The silver player's monster died at <paramref name="at"/>: 1-4 orbs pop out round the body.</summary>
        internal static void DropOrbs(PlayerData pd, Vector2 at)
        {
            if (Orb == null) return;
            float r = UnityEngine.Random.value, acc = 0f;
            int n = 1;
            for (int i = 0; i < OrbOdds.Length; i++) { acc += OrbOdds[i]; if (r <= acc) { n = i + 1; break; } }
            for (int i = 0; i < n; i++)
            {
                float a = UnityEngine.Random.Range(0f, 2f * Mathf.PI);
                Vector2 to = at + new Vector2(Mathf.Cos(a) * UnityEngine.Random.Range(8f, 18f), Mathf.Sin(a) * UnityEngine.Random.Range(4f, 10f));
                if (!SystemLevel.GetInCurrentRoom(to)) to = at;
                var go = SystemPool.Spawn(Orb, at);
                if (go == null) continue;
                var o = go.GetComponent<SilverOrb>() ?? go.AddComponent<SilverOrb>();
                o.Begin(pd, at, to, i * 0.06f);
            }
        }

        internal static void Collect(PlayerData pd, Vector2 at)
        {
            var st = For(pd);
            if (st.orbs < MaxOrbs) st.orbs++;
            if (OrbCollect != null) SystemPool.Spawn(OrbCollect, at);
        }

        internal static void UpdateSilver(PlayerData pd, State st)
        {
            st.tally.RemoveAll(o => o == null || !o.activeInHierarchy);   // a level change took them
            var body = pd.GameObject;
            var p = body != null ? body.GetComponent<Player>() : null;
            bool ghost = p != null && ModUtil.IsGhost(p);
            if (body != st.lastBody)
            {
                // a blob taken with 8 orbs banked: it is upgraded on the spot (circles and statues go through
                // SystemLevel.SpawnMonster, see Patch_SilverUpgrade). Not in boss fights: there the "blob" is a boss
                // part (Hydra heads, inhabitable boss bodies, other mods' boss pieces) and the orbs wait for later.
                if (st.wasGhost && !ghost && p != null && !pd.IsHero && st.orbs >= MaxOrbs && !SystemLevel.GetBossEncounterActive())
                {
                    var fodder = p.GetComponent<PropFodder>();
                    if (fodder != null && fodder.GetInhabited()) UpgradeFodder(pd, p, fodder, st);
                }
                st.lastBody = pd.GameObject; st.wasGhost = ghost;
            }
            UpdateReady(pd, st, body, ghost);
            // the tally: one orb circling the ghost per banked orb, bright when all 8 are in
            int want = ghost ? st.orbs : 0;
            bool full = st.orbs >= MaxOrbs;
            if (full != st.tallyFull) { ClearTally(st); st.tallyFull = full; }
            while (st.tally.Count > want) { var o = st.tally[st.tally.Count - 1]; st.tally.RemoveAt(st.tally.Count - 1); if (o != null) SystemPool.Despawn(o); }
            var tmpl = full ? TallyFull : Tally;
            while (st.tally.Count < want && tmpl != null)
            {
                var o = SystemPool.Spawn(tmpl, body.transform.position);
                if (o == null) break;
                st.tally.Add(o);
            }
            if (want == 0) return;
            Vector3 c = body.transform.position;
            float t = Time.time * 2.2f;
            for (int i = 0; i < st.tally.Count; i++)
            {
                var o = st.tally[i];
                if (o == null) continue;
                float a = t + i * (2f * Mathf.PI / st.tally.Count);
                float rx = 11f + st.tally.Count * 0.4f;
                o.transform.position = new Vector3(c.x + rx * Mathf.Cos(a), c.y + 12f + 4.5f * Mathf.Sin(a), c.z + (Mathf.Sin(a) > 0f ? 0.6f : -0.6f));
                o.transform.localScale = new Vector3(Mathf.Sin(a + Mathf.PI / 2f) < 0f ? -1f : 1f, 1f, 1f);
            }
        }

        static void ClearTally(State st)
        {
            foreach (var o in st.tally) if (o != null) SystemPool.Despawn(o);
            st.tally.Clear();
        }

        /// <summary>
        /// The ready tell, from the eighth orb until the upgraded body is taken: a crescent moon over the player's head
        /// (ghost or monster, so a player who took a body in a boss fight still shows it) and a moonlit halo kept a step
        /// behind the ghost, so it never covers it.
        /// </summary>
        static void UpdateReady(PlayerData pd, State st, GameObject body, bool ghost)
        {
            bool ready = st.orbs >= MaxOrbs && !pd.IsHero && body != null;
            if (body != st.markOn || ready != st.markShown)
            {
                if (st.markOn != null && (st.markOn != body || !ready)) ModInd.Set(st.markOn, ReadyMark, false);
                if (ready) ModInd.Set(body, ReadyMark, true);
                st.markOn = ready ? body : null; st.markShown = ready;
            }
            if (st.halo != null && !st.halo.activeInHierarchy) st.halo = null;      // a level change took it
            if (!ready || !ghost || Halo == null)
            {
                if (st.halo != null) { SystemPool.Despawn(st.halo); st.halo = null; }
                return;
            }
            Vector3 c = body.transform.position;
            if (st.halo == null) st.halo = SystemPool.Spawn(Halo, c);
            if (st.halo != null) st.halo.transform.position = new Vector3(c.x, c.y, c.z + 0.9f);
        }

        static void ClearReady(State st)
        {
            if (st.markOn != null) ModInd.Set(st.markOn, ReadyMark, false);
            st.markOn = null; st.markShown = false;
            if (st.halo != null) SystemPool.Despawn(st.halo);
            st.halo = null;
        }

        /// <summary>The inhabit moment of an upgraded body: moonlight falls on it, a silver ring bursts out, sparkles
        /// settle, with a chime. Visual and sound only.</summary>
        static void PlayInhabit(GameObject body, Vector2 at)
        {
            if (Inhabit != null) SystemPool.Spawn(Inhabit, at);
            if (body != null) CrawlFurther.Objects.ObjectKit.PlaySound(InhabitSound, body.transform);
        }

        // ------------------------------------------------------------------ silver: the upgrade
        /// <summary>prefab name -> tier (1 starter, 2, 3) in a god's tree.</summary>
        static Dictionary<string, int> Tree(Deity d, Dictionary<int, List<GameObject>> byTier)
        {
            if (d == null) return new Dictionary<string, int>();
            GameObject[] starters = null;
            try { starters = d.GetStartingMonsters(); } catch { }
            return Walk(starters, byTier);
        }

        /// <summary>The gold-secret line as its own tree: GoldSecret.StarterId = 1, its evolutions 2, theirs 3.</summary>
        static Dictionary<string, int> SecretTree(Dictionary<int, List<GameObject>> byTier)
        {
            var starter = string.IsNullOrEmpty(GoldSecret.StarterId) ? null : Resolve(GoldSecret.StarterId, true);
            return starter != null ? Walk(new[] { starter }, byTier) : new Dictionary<string, int>();
        }

        /// <summary>The silver uniques count as tier 3 (by id and by their prefab's name).</summary>
        static bool IsSilverUnique(string prefab)
        {
            foreach (var id in SilverUniques.Ids)
            {
                if (string.IsNullOrEmpty(id)) continue;
                if (id == prefab) return true;
                var go = Resolve(id, true);
                if (go != null && go.name == prefab) return true;
            }
            return false;
        }

        /// <summary>
        /// Every monster reachable from the starters, by depth (1 = starter). Walks the full tree: vanilla trees are
        /// four deep (starter, T2, T3 such as the Orc or Minotaur, then finals such as the Troll), mod trees three; a
        /// depth-3 walk made every vanilla final look like tier 1 and downgraded it.
        /// </summary>
        static Dictionary<string, int> Walk(IEnumerable<GameObject> starters, Dictionary<int, List<GameObject>> byTier)
        {
            var tiers = new Dictionary<string, int>();
            if (starters == null) return tiers;
            var frontier = new List<GameObject>();
            foreach (var s in starters) if (s != null) frontier.Add(s);
            for (int tier = 1; tier <= MaxDepth && frontier.Count > 0; tier++)
            {
                var next = new List<GameObject>();
                foreach (var go in frontier)
                {
                    if (go == null || tiers.ContainsKey(go.name)) continue;
                    tiers[go.name] = tier;
                    if (byTier != null)
                    {
                        List<GameObject> l;
                        if (!byTier.TryGetValue(tier, out l)) byTier[tier] = l = new List<GameObject>();
                        l.Add(go);
                    }
                    foreach (var e in Evolutions(go)) next.Add(e);
                }
                frontier = next;
            }
            return tiers;
        }
        const int MaxDepth = 8;

        static List<GameObject> Evolutions(GameObject go)
        {
            var l = new List<GameObject>();
            var p = go != null ? go.GetComponent<Player>() : null;
            Player[] ev = null;
            try { ev = p != null ? p.GetEvolveTo() : null; } catch { }
            if (ev != null) foreach (var e in ev) if (e != null) l.Add(e.gameObject);
            return l;
        }

        /// <summary>A final: nothing to evolve into (mod T3s, vanilla Troll / Pope / Beholder..., silver uniques, secret statues).</summary>
        internal static bool IsFinal(GameObject prefab, string name)
        {
            if (SecretStatues.Is(name) || IsSilverUnique(name)) return true;
            return Evolutions(prefab).Count == 0;
        }

        /// <summary>What a body becomes with 8 orbs: a random monster one level deeper in the body's own tree, or (a final) itself ascended.</summary>
        internal static GameObject UpgradeOf(PlayerData pd, GameObject prefab, out bool ascend)
        {
            Deity d = null;
            try { d = pd != null ? pd.GetDeity() : null; } catch { }
            return UpgradeFor(d, prefab, out ascend);
        }

        internal static GameObject UpgradeFor(Deity god, GameObject prefab, out bool ascend)
        {
            ascend = false;
            string name = ModUtil.PrefabName(prefab);
            // a final (any tree, mod or vanilla, or a secret statue / silver unique) ascends, or may become a silver unique
            if (IsFinal(prefab, name))
            {
                if (SecretStatues.Is(name)) { ascend = true; return prefab; }   // never trade a secret statue away
                string id = null;
                try { id = SilverUniques.RollTier3 != null ? SilverUniques.RollTier3(name) : null; }
                catch (Exception e) { Plugin.Log.LogError("SilverUniques.RollTier3 failed: " + e); }
                var unique = Resolve(id);
                // never "upgrade" into the body it already is (a unique rolling itself): ascend instead
                if (unique != null && unique.name != name && id != name) return unique;
                ascend = true; return prefab;
            }
            // the body's own tree: the gold-secret line, else the player's god's tree (an idol's: its starters' trees),
            // else any god's tree that holds it; a body in no tree (blobs, minions) counts as a starter of the player's tree
            var byTier = new Dictionary<int, List<GameObject>>();
            int tier;
            var secret = SecretTree(byTier);
            if (!secret.TryGetValue(name, out tier))
            {
                byTier = new Dictionary<int, List<GameObject>>();
                var own = Tree(god, byTier);
                if (!own.TryGetValue(name, out tier))
                {
                    tier = 0;
                    var all = SystemDeity.GetDeities();
                    if (all != null)
                        foreach (var other in all)
                        {
                            if (other == null || other == god) continue;
                            var ob = new Dictionary<int, List<GameObject>>();
                            var t = Tree(other, ob);
                            if (t.TryGetValue(name, out tier)) { byTier = ob; break; }
                            tier = 0;
                        }
                    if (tier == 0)
                    {
                        byTier = new Dictionary<int, List<GameObject>>();
                        Tree(god, byTier);
                        tier = 1;
                    }
                }
            }
            List<GameObject> pool;
            if (byTier.TryGetValue(tier + 1, out pool) && pool.Count > 0) return pool[UnityEngine.Random.Range(0, pool.Count)];
            // nothing one level deeper in that tree: one of its own evolutions
            var ev = Evolutions(prefab);
            if (ev.Count > 0) return ev[UnityEngine.Random.Range(0, ev.Count)];
            ascend = true; return prefab;
        }

        /// <summary>Self-check: every final of every god's tree (vanilla gods' four-deep trees included) ascends or becomes a
        /// silver unique, never a lower monster; every non-final goes one level deeper.</summary>
        static void CheckUpgrades(Action<string> bad)
        {
            var all = SystemDeity.GetDeities();
            if (all == null) return;
            int finals = 0, mids = 0;
            foreach (var d in all)
            {
                if (d == null) continue;
                var byTier = new Dictionary<int, List<GameObject>>();
                var tree = Tree(d, byTier);
                foreach (var kv in byTier)
                    foreach (var go in kv.Value)
                    {
                        bool asc;
                        var to = UpgradeFor(d, go, out asc);
                        string n = ModUtil.PrefabName(go);
                        if (IsFinal(go, n))
                        {
                            finals++;
                            if (!(asc && to == go) && !(to != null && IsSilverUnique(ModUtil.PrefabName(to))))
                                bad("silver: final " + n + " (" + d.GetName() + ") would become " + (to != null ? to.name : "null") + " instead of ascending");
                        }
                        else
                        {
                            mids++;
                            int tt;
                            if (asc || to == null || !tree.TryGetValue(to.name, out tt) || tt != kv.Key + 1)
                                bad("silver: " + n + " (tier " + kv.Key + ", " + d.GetName() + ") would become " + (to != null ? to.name : "null") + (asc ? " (ascended)" : ""));
                        }
                    }
            }
            Plugin.Log.LogInfo("Silver upgrade self-check: " + finals + " finals ascend, " + mids + " bodies step one level deeper");
        }

        /// <summary>A prefab id ("ModSilverX", or a vanilla prefab name) -> its prefab, or null.</summary>
        static GameObject Resolve(string id, bool quiet = false)
        {
            if (string.IsNullOrEmpty(id)) return null;
            Player p;
            if (MonsterFactory.Built.TryGetValue(id, out p) && p != null) return p.gameObject;
            if (id.StartsWith("Mod") && MonsterFactory.Built.TryGetValue(id.Substring(3), out p) && p != null) return p.gameObject;
            foreach (var kv in MonsterFactory.Built) if (kv.Value != null && kv.Value.gameObject.name == id) return kv.Value.gameObject;
            var v = MonsterFactory.FindVanilla(id);
            if (v == null && !quiet) Plugin.Log.LogWarning("Silver upgrade: no monster '" + id + "', ascending instead");
            return v != null ? v.gameObject : null;
        }

        /// <summary>Circles and statues: SystemLevel.SpawnMonster with the upgraded prefab (Patch_SilverUpgrade).</summary>
        internal static void BeforeSpawn(PlayerData pd, ref GameObject prefab)
        {
            var st = For(pd);
            st.pendingUpgrade = false;
            if (st.orbs < MaxOrbs || prefab == null || SystemLevel.GetBossEncounterActive()) return;   // as for blobs: never a boss part
            bool asc;
            prefab = UpgradeOf(pd, prefab, out asc);
            st.pendingUpgrade = true; st.pendingAscend = asc;
        }

        internal static void AfterSpawn(PlayerData pd, bool spawned)
        {
            var st = For(pd);
            if (!st.pendingUpgrade) return;
            st.pendingUpgrade = false;
            if (!spawned) return;
            st.orbs = 0;
            var body = pd.GameObject;
            if (body == null) return;
            PlayInhabit(body, body.transform.position);
            if (st.pendingAscend) Ascend(body);
            st.lastBody = body; st.wasGhost = false;
        }

        /// <summary>A blob taken with 8 orbs: the blob quietly goes and the upgraded monster stands in its place.</summary>
        static void UpgradeFodder(PlayerData pd, Player blob, PropFodder fodder, State st)
        {
            try
            {
                bool asc;
                var prefab = UpgradeOf(pd, blob.gameObject, out asc);
                Vector2 at = blob.transform.position;
                bool flip = blob.transform.localScale.x < 0f;
                // let the blob go without releasing a ghost or dying: the new body takes the player first
                R.Set(fodder, "m_actionerInside", false);
                var eff = R.Get<GameObject>(fodder, "m_ghostInhabitingEffect");
                if (eff != null) { eff.SetActive(false); eff.Despawn(); R.Set(fodder, "m_ghostInhabitingEffect", null); }
                GameObject go;
                if (asc) go = blob.gameObject;      // a blob is never tier 3; kept for safety
                else
                {
                    go = prefab.Spawn(at, Quaternion.identity);
                    var np = go.GetComponent<Player>();
                    np.InitAsPlayer(pd);           // also clears the blob's player
                    if (flip) go.transform.localScale = go.transform.localScale.WithX(-1f);
                    var room = SystemLevel.GetCurrentRoom();
                    if (room != null) room.CloseDoors();
                    blob.Despawn();
                }
                st.orbs = 0;
                PlayInhabit(go, at);
                if (asc) Ascend(go);
            }
            catch (Exception e) { Plugin.Log.LogError("Silver upgrade of a blob failed: " + e); }
        }

        internal static void Ascend(GameObject body)
        {
            var a = body.GetComponent<SilverAscended>() ?? body.AddComponent<SilverAscended>();
            a.Begin();
        }

        // ------------------------------------------------------------------ gold: Thralls
        static readonly System.Reflection.MethodInfo s_release = AccessTools.Method(typeof(PropFodder), "ReleasePlayer");

        internal static void UpdateThralls(PlayerData pd, State st)
        {
            if (st.thrall != null && !st.thrall.Live) st.thrall = null;
            // a crown over the player's own head (ghost or monster) while their thrall is out
            var body = pd.GameObject;
            bool show = st.thrall != null;
            if (body != st.countOn || show != st.countShown)
            {
                if (st.countOn != null && st.countOn != body) ModInd.Set(st.countOn, Count, false);
                if (body != null) ModInd.Set(body, Count, show);
                st.countOn = body; st.countShown = show;
            }
            var p = MonsterBody(pd);
            // in a blob with a special the ghost button is that special (BlobSpecialInput), never a jump-out
            if (p == null || st.cd > 0f || BlobSpecialInput.SpecialOnGhostButton(p) || !GhostControls.Down(pd)) return;
            st.cd = 0.4f;
            if (st.thrall != null || SystemLevel.GetBossEncounterActive() || p.GetComponent<ThrallMark>() != null)
            {
                // one thrall at a time (and none in boss fights): a gold chain and padlock flicker on the monster
                if (ThrallLocked != null) SystemPool.Spawn(ThrallLocked, p.transform.position);
                return;
            }
            JumpOut(pd, p, st);
        }

        static void JumpOut(PlayerData pd, Player p, State st)
        {
            var h = p.GetComponent<Health>();
            if (h == null || !h.IsAlive()) return;
            st.cd = JumpCooldown;
            Vector2 at = p.transform.position;
            PlayerAI added = null;
            ThrallMark.Undo restore = null;
            var fodder = p.GetComponent<PropFodder>();
            try
            {
                if (fodder != null && fodder.GetInhabited() && s_release != null)
                {
                    s_release.Invoke(fodder, null);          // the game's own way out of a body (ghost + OnUninhabitAI)
                    fodder.DisableAction();                  // nobody can take a thrall back
                }
                else
                {
                    // a body from a circle or statue has no AI of its own: give it the vanilla monster AI on its attacks
                    var ai = p.GetComponent<PlayerAI>();
                    if (ai == null) { ai = added = p.gameObject.AddComponent<PlayerAI>(); TuneAI(ai, p); }
                    // what vanilla's InitAsAI does, minus Init (the body is already set up): the player's AI, and the
                    // movement's AI (an InitAsPlayer body's movement has none, so it would never move or turn)
                    restore = new ThrallMark.Undo(p);
                    R.Set(p, "m_playerAI", ai);
                    var mv = p.GetComponent<PlayerMovement>();
                    if (mv != null) mv.InitAsAI(ai);
                    Singleton<SystemLevel>.Get.SpawnGhost(pd, p.gameObject, 0f);
                    if (pd.GameObject != null && pd.GameObject != p.gameObject)
                        pd.GameObject.SendMessage("SkipGhostSpawnDelay", SendMessageOptions.DontRequireReceiver);
                    p.SendMessage("OnUninhabitAI", SendMessageOptions.DontRequireReceiver);
                }
            }
            catch (Exception e) { Plugin.Log.LogError("Thrall jump-out failed: " + e); }
            R.Set(p, "m_spawner", pd);                      // kills it makes are credited to its gold ghost's player
            // max health halved, then healed to 75 percent of that
            float max = R.Get<float>(h, "m_healthMaxFinal");
            if (max > 0f)
            {
                float newMax = max * ThrallMaxHealth;
                R.Set(h, "m_healthMaxFinal", newMax);
                R.Set(h, "m_healthCurrent", Mathf.Max(0.5f, newMax * ThrallHealTo));
            }
            var tm = p.gameObject.AddComponent<ThrallMark>();
            tm.Init(pd, added, fodder, max, restore);
            st.thrall = tm;
            if (ThrallJump != null) SystemPool.Spawn(ThrallJump, at);
        }

        /// <summary>The vanilla monster AI on a body that never had one: chase the hero, use each of its attacks at its
        /// own reach. (The vanilla AI never uses specials: a special needs a player behind it.)</summary>
        static void TuneAI(PlayerAI ai, Player p)
        {
            try
            {
                var atk = Kit.Attacks(p);
                float reach0 = 30f;
                if (atk != null && atk.Count > 0 && atk[0] != null && atk[0].m_botData != null && atk[0].m_botData.m_rangeOuter > 0f)
                    reach0 = Mathf.Clamp(atk[0].m_botData.m_rangeOuter, 14f, 90f);
                R.Set(ai, "m_chaseStartRadius", new MinMaxRange(110f, 140f));
                R.Set(ai, "m_chaseStopRadius", new MinMaxRange(Mathf.Max(4f, reach0 * 0.4f), reach0 * 0.85f));
                R.Set(ai, "m_chaseMoveMultiplier", 1f);
                var list = R.Get<System.Collections.IList>(ai, "m_attacks");
                if (list == null || AiSpecial.AttackType == null) return;
                list.Clear();
                // Player.m_attacks has the special appended at its end once the body is set up: the AI list leaves it
                // out (ThrallMark fires it on its own timer, like a player would)
                int sid = p.GetAttackComponent() != null ? p.GetAttackComponent().GetSpecialAttackId() : -1;
                int n = atk != null ? Mathf.Max(1, atk.Count) : 1;
                if (sid >= 0 && sid < n) n = sid;
                for (int i = 0; i < n; i++)
                {
                    float reach = reach0;
                    if (atk != null && i < atk.Count && atk[i] != null && atk[i].m_botData != null && atk[i].m_botData.m_rangeOuter > 0f)
                        reach = Mathf.Clamp(atk[i].m_botData.m_rangeOuter, 14f, 90f);
                    var a = Activator.CreateInstance(AiSpecial.AttackType);
                    R.Set(a, "m_attackId", i);
                    R.Set(a, "m_attackPriority", n - i);
                    R.Set(a, "m_attackRadius", reach);
                    R.Set(a, "m_attackCooldown", new MinMaxRange(1.6f, 2.6f));
                    list.Add(a);
                }
            }
            catch (Exception e) { Plugin.Log.LogWarning("Thrall AI: " + e.Message); }
        }
    }

    /// <summary>Drives the silver / gold mechanics for every human player each frame (one object for the whole game).</summary>
    public class GhostSlotRunner : MonoBehaviour
    {
        void Update()
        {
            if (!Singleton<SystemLevel>.HasInstance() || SystemTime.Paused) return;
            try
            {
                var players = SystemPlayers.GetPlayers();
                if (players == null) return;
                foreach (var pd in players)
                {
                    if (pd == null || !pd.IsHuman) continue;
                    var form = GhostPack.FormOf(pd);
                    if (form != GhostForm.Gold && form != GhostForm.Silver) continue;
                    var st = GhostSlots.For(pd);
                    st.cd -= Time.deltaTime;
                    if (form == GhostForm.Silver) GhostSlots.UpdateSilver(pd, st);
                    else GhostSlots.UpdateThralls(pd, st);
                }
            }
            catch (Exception e) { Plugin.Log.LogError("Ghost slots: " + e); }
        }
    }

    /// <summary>A silver orb on the floor: pops out of the dead body, settles, bobs; only its owner's ghost collects it.</summary>
    public class SilverOrb : MonoBehaviour
    {
        PlayerData m_owner;
        Vector2 m_from, m_to;
        float m_t, m_delay;
        bool m_live;
        exSprite m_spr;

        public void Begin(PlayerData owner, Vector2 from, Vector2 to, float delay)
        {
            m_owner = owner; m_from = from; m_to = to; m_t = 0f; m_delay = delay; m_live = true;
            m_spr = GetComponent<exSprite>();
            if (m_spr != null) m_spr.color = Color.white;
        }

        void OnDisable() { m_live = false; m_owner = null; }

        void Update()
        {
            if (!m_live) return;
            float dt = Time.deltaTime;
            if (dt <= 0f) return;
            m_t += dt;
            // the pop: a little arc from the body to where it settles
            float k = Mathf.Clamp01((m_t - m_delay) / 0.35f);
            Vector2 at = Vector2.Lerp(m_from, m_to, k) + new Vector2(0f, Mathf.Sin(k * Mathf.PI) * 10f);
            transform.position = new Vector3(at.x, at.y, transform.position.z);
            if (m_t > GhostSlots.OrbLife || !SystemLevel.GetInCurrentRoom(m_to) || m_owner == null || !m_owner.IsActive) { End(); return; }
            if (m_spr != null)
            {
                bool blink = m_t > GhostSlots.OrbLife - 3f && ((int)(m_t * 8f)) % 2 == 0;
                m_spr.color = new Color(1f, 1f, 1f, blink ? 0.35f : 1f);
            }
            if (k < 1f) return;
            var body = m_owner.GameObject;
            var p = body != null ? body.GetComponent<Player>() : null;
            if (p == null || !ModUtil.IsGhost(p)) return;
            Vector2 d = (Vector2)body.transform.position - m_to;
            if (Mathf.Abs(d.x) < GhostSlots.OrbReach && d.y > -GhostSlots.OrbReach && d.y < GhostSlots.OrbReach + 8f)
            {
                GhostSlots.Collect(m_owner, m_to);
                End();
            }
        }

        void End()
        {
            m_live = false;
            if (m_spr != null) m_spr.color = Color.white;
            gameObject.Despawn();
        }
    }

    /// <summary>A silver ascended final: its own size, +30 percent max health (healed), silver variant art and sparkles.</summary>
    public class SilverAscended : MonoBehaviour
    {
        float m_baseX = 1f, m_baseY = 1f, m_origMax;
        bool m_on;
        exSprite m_spr;

        public void Begin()
        {
            m_baseX = Mathf.Abs(transform.localScale.x); m_baseY = transform.localScale.y;
            if (m_baseX < 0.01f) m_baseX = 1f;
            var h = GetComponent<Health>();
            if (h != null)
            {
                m_origMax = R.Get<float>(h, "m_healthMaxFinal");
                if (m_origMax > 0f)
                {
                    R.Set(h, "m_healthMaxFinal", m_origMax * GhostSlots.AscendHealth);
                    R.Set(h, "m_healthCurrent", m_origMax * GhostSlots.AscendHealth);
                }
            }
            m_spr = GetComponent<exSprite>();
            // its own moonlit silver art (SilverVariants.cs); the old tint only for a body with no silver sheet
            bool art = false;
            try { art = SilverVariants.Apply(gameObject); } catch (Exception e) { Plugin.Log.LogError("Silver variant: " + e); }
            if (m_spr != null && !art) m_spr.color = GhostSlots.SilverTint;
            ModInd.Set(gameObject, GhostSlots.AscendAura, true);
            m_on = true;
        }

        public bool On { get { return m_on; } }

        /// <summary>The game recomputed max health from its modifiers (Patch_GhostSlotHealthKeep): remember the new plain value.</summary>
        internal void Recomputed(float raw) { if (raw > 0f) m_origMax = raw; }

        void LateUpdate()
        {
            // AscendScale is 1, so leave the scale alone (forcing it every frame cancelled the hit bounce/squash)
            if (!m_on || Mathf.Approximately(GhostSlots.AscendScale, 1f)) return;
            var s = transform.localScale;
            float want = m_baseX * GhostSlots.AscendScale;
            if (Mathf.Abs(Mathf.Abs(s.x) - want) > 0.001f || Mathf.Abs(s.y - m_baseY * GhostSlots.AscendScale) > 0.001f)
                transform.localScale = new Vector3(s.x < 0f ? -want : want, m_baseY * GhostSlots.AscendScale, s.z);
        }

        void OnDisable()
        {
            if (!m_on) return;
            m_on = false;
            try
            {
                // the pooled monster comes back plain next time
                if (!Mathf.Approximately(GhostSlots.AscendScale, 1f))
                {
                    var s = transform.localScale;
                    transform.localScale = new Vector3(s.x < 0f ? -m_baseX : m_baseX, m_baseY, s.z);
                }
                var h = GetComponent<Health>();
                if (h != null && m_origMax > 0f) R.Set(h, "m_healthMaxFinal", m_origMax);
                if (m_spr != null) m_spr.color = Color.white;
                SilverVariants.Restore(gameObject);          // back to its own art
                ModInd.Set(gameObject, GhostSlots.AscendAura, false);
            }
            catch { }
            Destroy(this);
        }
    }

    /// <summary>A gold thrall: gold-tinted and marked, bursts into ectoplasm for its ghost when killed, and cleans itself
    /// off the (pooled) monster when it goes. It fights with the monster's own attacks through the vanilla AI.</summary>
    public class ThrallMark : MonoBehaviour
    {
        PlayerData m_owner;
        PlayerAI m_addedAI;
        float m_origMax;
        PropFodder m_fodder;
        Health m_health;
        exSprite m_spr;
        bool m_done;

        public bool Live { get { return !m_done && this != null && gameObject.activeInHierarchy && m_health != null && m_health.IsAlive(); } }

        /// <summary>The game recomputed max health from its modifiers (Patch_GhostSlotHealthKeep): remember the new plain value.</summary>
        internal void Recomputed(float raw) { if (raw > 0f) m_origMax = raw; }
        internal bool Halved { get { return !m_done; } }

        /// <summary>A circle / statue body's AI wiring before it became a thrall, put back when it goes to the pool (else a
        /// player later given this pooled body would be steered by a stale AI).</summary>
        public class Undo
        {
            readonly Player m_p; readonly PlayerMovement m_mv; readonly PlayerAI m_pAI, m_mvAI; readonly bool m_mvIsAI;
            public Undo(Player p)
            {
                m_p = p; m_pAI = R.Get<PlayerAI>(p, "m_playerAI");
                m_mv = p.GetComponent<PlayerMovement>();
                if (m_mv != null) { m_mvAI = R.Get<PlayerAI>(m_mv, "m_playerAI"); m_mvIsAI = R.Get<bool>(m_mv, "m_ai"); }
            }
            public void Apply()
            {
                if (m_p != null) R.Set(m_p, "m_playerAI", m_pAI);
                if (m_mv != null) { R.Set(m_mv, "m_playerAI", m_mvAI); R.Set(m_mv, "m_ai", m_mvIsAI); }
            }
        }
        Undo m_undo;

        public void Init(PlayerData owner, PlayerAI addedAI, PropFodder fodder, float origMax, Undo undo)
        {
            m_owner = owner; m_addedAI = addedAI; m_fodder = fodder; m_origMax = origMax; m_undo = undo;
            m_health = GetComponent<Health>();
            m_spr = GetComponent<exSprite>();
            if (m_spr != null) m_spr.color = GhostSlots.GoldTint;
            ModInd.Set(gameObject, GhostSlots.Mark, true);
            ModInd.Set(gameObject, GhostSlots.Sigil, true);
        }

        void Update()
        {
            if (m_done) return;
            if (m_health == null || !m_health.IsAlive())
            {
                m_done = true;
                ModInd.Set(gameObject, GhostSlots.Mark, false);
                ModInd.Set(gameObject, GhostSlots.Sigil, false);
                Burst();
                return;
            }
            DriveSpecial();
        }

        float m_specialTimer;
        Player m_player;

        void DriveSpecial()
        {
            if (m_player == null) m_player = GetComponent<Player>();
            AiSpecial.Drive(m_player, ref m_specialTimer);
        }

        void Burst()
        {
            if (GhostSlots.ThrallBurst != null) SystemPool.Spawn(GhostSlots.ThrallBurst, transform.position);
            var pd = m_owner;
            if (pd == null || !pd.IsActive || pd.IsHero) return;
            var body = pd.GameObject;
            if (body != null && body.GetComponent<Ghost>() != null)
            {
                for (int i = 0; i < (int)GhostSlots.ThrallBurstEcto; i++)
                    body.SendMessage("MsgCollectEctoplasm", new MsgParams { m_float = 1f }, SendMessageOptions.DontRequireReceiver);
            }
            else pd.OnEctoplasmCollected(GhostSlots.ThrallBurstEcto);
        }

        void OnDisable()
        {
            try
            {
                ModInd.Set(gameObject, GhostSlots.Mark, false);
                ModInd.Set(gameObject, GhostSlots.Sigil, false);
                if (m_spr != null) m_spr.color = Color.white;
                if (m_undo != null) { m_undo.Apply(); m_undo = null; }
                if (m_addedAI != null) { Destroy(m_addedAI); m_addedAI = null; }
                if (m_health != null && m_origMax > 0f) R.Set(m_health, "m_healthMaxFinal", m_origMax);
                if (m_fodder != null) m_fodder.EnableAction();
            }
            catch { }
            m_done = true;
            Destroy(this);
        }
    }

    // ====================================================================== patches
    /// <summary>Each new run starts the silver / gold state from nothing.</summary>
    [HarmonyPatch(typeof(SystemGame), "OnStartGame")]
    static class Patch_GhostSlotsNewRun
    {
        static void Postfix()
        {
            try { GhostSlots.ResetRun(); }
            catch (Exception e) { Plugin.Log.LogWarning("Ghost slots new run: " + e.Message); }
        }
    }

    /// <summary>Thralls hit at 60 percent; an ascended body's hits throw silver sparks.</summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_GhostSlotDamage
    {
        static void Prefix(DamageInfo damage)
        {
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f) return;
            // a thrall's hits carry its gold player as the source player (kill credit, untouched); the body that made
            // the hit is m_sourceOwner (kept through effects the hit spawns)
            var src = damage.m_source.m_sourceOwner;
            if (src == null) return;
            var tm = src.GetComponent<ThrallMark>();
            if (tm != null && tm.Live) damage.m_amount *= GhostSlots.ThrallDamage;
        }

        static void Postfix(Health __instance, DamageInfo damage, bool __result)
        {
            if (!__result || damage == null || damage.m_source == null || damage.m_amount <= 0f) return;
            var src = damage.m_source.m_sourceOwner ?? damage.m_source.m_sourceOwnerPlayer;
            if (src == null || src == __instance.gameObject) return;
            var asc = src.GetComponent<SilverAscended>();
            if (asc != null && asc.On && GhostSlots.AscendSpark != null)
                SystemPool.Spawn(GhostSlots.AscendSpark, (Vector2)__instance.transform.position + new Vector2(0f, 8f));
        }
    }

    /// <summary>
    /// Max health is rebuilt from the modifier stack whenever one is queued (Health.Update applies
    /// Health.ModifyHealthMax: on spawn, and on every MonsterHealth modifier change for a player body). That
    /// rebuild starts from the prefab value, so it would drop the ascended x1.3 and the thrall halving: put them
    /// back on the rebuilt value, keeping the health gained or lost the way the game does.
    /// </summary>
    [HarmonyPatch(typeof(Health), "Update")]
    static class Patch_GhostSlotHealthKeep
    {
        static readonly AccessTools.FieldRef<Health, ValueModifierStack> s_queued = AccessTools.FieldRefAccess<Health, ValueModifierStack>("m_maxHealthModifierQueued");
        static readonly AccessTools.FieldRef<Health, float> s_max = AccessTools.FieldRefAccess<Health, float>("m_healthMaxFinal");
        static readonly AccessTools.FieldRef<Health, float> s_cur = AccessTools.FieldRefAccess<Health, float>("m_healthCurrent");

        struct Before { public float max, cur, mult; public SilverAscended asc; public ThrallMark tm; }

        static void Prefix(Health __instance, out Before __state)
        {
            __state = default(Before);
            if (s_queued(__instance) == null) return;
            var asc = __instance.GetComponent<SilverAscended>();
            var tm = __instance.GetComponent<ThrallMark>();
            if (asc != null && asc.On) { __state.mult = GhostSlots.AscendHealth; __state.asc = asc; }
            else if (tm != null && tm.Halved) { __state.mult = GhostSlots.ThrallMaxHealth; __state.tm = tm; }
            else return;
            __state.max = s_max(__instance);
            __state.cur = s_cur(__instance);
        }

        static void Postfix(Health __instance, Before __state)
        {
            if (__state.mult <= 0f || s_queued(__instance) != null || !__instance.IsAlive()) return;
            try
            {
                float raw = s_max(__instance);
                float want = raw * __state.mult;
                float cur = __state.max > 0f && want > __state.max ? __state.cur + (want - __state.max) : Mathf.Min(__state.cur, want);
                s_max(__instance) = want;
                s_cur(__instance) = Mathf.Max(0.5f, cur);
                if (__state.asc != null) __state.asc.Recomputed(raw);
                if (__state.tm != null) __state.tm.Recomputed(raw);
            }
            catch (Exception e) { Plugin.Log.LogWarning("Ghost slot health keep: " + e.Message); }
        }
    }

    /// <summary>Silver: a body taken at a circle or statue with 8 orbs banked is upgraded (SystemLevel.SpawnMonster).</summary>
    [HarmonyPatch(typeof(SystemLevel), "SpawnMonster", new[] { typeof(PlayerData), typeof(GameObject), typeof(Vector2), typeof(bool) })]
    static class Patch_SilverUpgrade
    {
        static void Prefix(PlayerData plrData, ref GameObject monsterPrefab)
        {
            try
            {
                if (plrData == null || plrData.IsHero || plrData.IsAlive || !GhostSlots.IsSilver(plrData)) return;
                GhostSlots.BeforeSpawn(plrData, ref monsterPrefab);
            }
            catch (Exception e) { Plugin.Log.LogError("Silver upgrade failed: " + e); }
        }

        static void Postfix(PlayerData plrData, bool __result)
        {
            try { if (GhostSlots.IsSilver(plrData)) GhostSlots.AfterSpawn(plrData, __result); }
            catch (Exception e) { Plugin.Log.LogError("Silver upgrade failed: " + e); }
        }
    }

    /// <summary>Silver: the player's monster dies -> its orbs pop out.</summary>
    [HarmonyPatch(typeof(SystemLevel), "OnPlayerKilled")]
    static class Patch_SilverOrbs
    {
        static void Prefix(Player killed)
        {
            try
            {
                if (killed == null || ModUtil.IsGhost(killed)) return;
                var pd = killed.GetPlayerData();
                if (pd == null || pd.IsHero || !GhostSlots.IsSilver(pd) || SystemLevel.GetBossEncounterActive()) return;
                GhostSlots.DropOrbs(pd, killed.transform.position);
            }
            catch (Exception e) { Plugin.Log.LogError("Silver orbs failed: " + e); }
        }
    }
}
