using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Secrets
{
    using CrawlFurther.Art;
    using CrawlFurther.Compat;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Ghosts;
    using CrawlFurther.Content.Gods.Vhorrul;
    using CrawlFurther.Content.Tips;

    /// <summary>
    /// SECRET STATUES: rare special statues between fights (a statue variant with its own carved plinth and a glint a
    /// sharp-eyed ghost can spot) hold five secret monsters that nothing else offers (no god tree, evolution, idol, bot,
    /// spawn group or silver/gold rule). See StatuePlacement below for the odds.
    /// </summary>
    public static class SecretStatues
    {
        /// <summary>Prefab ids, in order: the four normal secret statues, then the legendary.</summary>
        public static readonly List<string> Ids = new List<string>();
        public const string Grotesque = "ModStmGrotesque", Sixfold = "ModStmSixfold", Gambit = "ModStmGambit",
                            Caryatid = "ModStmCaryatid", Lachrymosa = "ModStmLachrymosa";
        public static readonly string[] Normal = { Grotesque, Sixfold, Gambit, Caryatid };

        /// <summary>Per statue room: one statue becomes a secret one. Normal (any of four): 1 in 12. Legendary: 1 in 200.</summary>
        public const float NormalRoomChance = 1f / 12f, LegendaryRoomChance = 1f / 200f;

        /// <summary>Is this prefab name one of the five secret statue monsters (works before and after registration)?</summary>
        public static bool Is(string prefabName)
        {
            if (prefabName == null) return false;
            int c = prefabName.IndexOf("(Clone)");
            if (c >= 0) prefabName = prefabName.Substring(0, c).Trim();
            return prefabName == Grotesque || prefabName == Sixfold || prefabName == Gambit || prefabName == Caryatid || prefabName == Lachrymosa;
        }

        /// <summary>
        /// Spawn one secret statue (the vanilla MonsterStatue prop wearing a secret plinth) at pos under parent: the
        /// legendary at <paramref name="legendaryChance"/> (0..1), otherwise one of the four normal ones at random. Taking
        /// it marks its secret found like a statue room's. Returns the prop, or null if the statues are not built.
        /// </summary>
        public static GameObject SpawnSecretStatue(Vector3 pos, Transform parent, float legendaryChance)
        {
            return StatuePlacement.Spawn(pos, parent, UnityEngine.Random.value < legendaryChance ? Lachrymosa : null);
        }
    }

    /// <summary>
    /// Where secret statues come from. Vanilla SystemLevel.SpawnRoomContent fills a statue room with Room.SpawnProps(
    /// m_prefabStatues = GroupStatues -> MonsterStatue, n). After that call, with NormalRoomChance one of the new
    /// statues is marked with a random normal secret, with LegendaryRoomChance with the legendary (rolled first). The mark
    /// is applied after PropMonsterStatue.Start picked its monster from EnemyGroupStatue (Start postfix, plus a
    /// LateUpdate guard if the prop is ever reused without Start): m_prefabMonster becomes the secret monster and the
    /// prop plays its carved secret plinth clip. Bots can never take one (GetCanAction is false for them). Taking one
    /// calls Secrets.Found.
    /// Debug: BepInEx/config/CrawlMod.Debug.cfg [SecretStatues] Force = Off / Normal / Legendary / Every (every statue room
    /// gets one; Every = every statue in it is a secret, cycling all five).
    /// </summary>
    public static class StatuePlacement
    {
        static GameObject s_prop;
        static SpawnGroup s_roomGroup;
        static string s_force;
        static int s_cycle;

        public static string Force
        {
            get
            {
                if (s_force == null)
                {
                    s_force = "Off";
                    try
                    {
                        var cfg = new BepInEx.Configuration.ConfigFile(System.IO.Path.Combine(BepInEx.Paths.ConfigPath, "CrawlMod.Debug.cfg"), true);
                        s_force = cfg.Bind("SecretStatues", "Force", "Off",
                            "Testing: Off (normal odds), Normal (every statue room has a normal secret statue), Legendary (every statue room has the legendary), Every (every statue is a secret one, cycling all five)").Value ?? "Off";
                    }
                    catch (Exception e) { Plugin.Log.LogWarning("SecretStatues: debug config: " + e.Message); }
                }
                return s_force;
            }
        }

        /// <summary>The vanilla MonsterStatue prop prefab.</summary>
        public static GameObject Prop
        {
            get
            {
                if (s_prop == null)
                    foreach (var p in Resources.FindObjectsOfTypeAll<PropMonsterStatue>())
                        if (p != null && p.gameObject.name == "MonsterStatue" && !p.gameObject.scene.IsValid()) { s_prop = p.gameObject; break; }
                return s_prop;
            }
        }

        static SpawnGroup RoomGroup
        {
            get
            {
                if (s_roomGroup == null)
                {
                    var lvl = Singleton<SystemLevel>.Get;
                    if (lvl != null) s_roomGroup = R.Get<SpawnGroup>(lvl, "m_prefabStatues");
                }
                return s_roomGroup;
            }
        }

        static string RandomNormal()
        {
            var built = new List<string>();
            foreach (var id in SecretStatues.Normal) if (SecretStatues.Ids.Contains(id)) built.Add(id);
            return built.Count > 0 ? built[UnityEngine.Random.Range(0, built.Count)] : null;
        }

        /// <summary>A room's roll: the secret to place, or null for none.</summary>
        public static string RollRoom()
        {
            switch (Force)
            {
                case "Normal": return RandomNormal();
                case "Legendary": return SecretStatues.Lachrymosa;
                case "Every": return SecretStatues.Ids.Count > 0 ? SecretStatues.Ids[s_cycle++ % SecretStatues.Ids.Count] : null;
            }
            float r = UnityEngine.Random.value;
            if (r < SecretStatues.LegendaryRoomChance) return SecretStatues.Ids.Contains(SecretStatues.Lachrymosa) ? SecretStatues.Lachrymosa : RandomNormal();
            if (r < SecretStatues.LegendaryRoomChance + SecretStatues.NormalRoomChance) return RandomNormal();
            return null;
        }

        public static GameObject Spawn(Vector3 pos, Transform parent, string id)
        {
            if (string.IsNullOrEmpty(id)) id = RandomNormal();
            if (id == null || !SecretStatues.Ids.Contains(id) || Prop == null) return null;
            var go = parent != null ? SystemPool.Spawn(Prop, pos, Quaternion.identity, parent) : SystemPool.Spawn(Prop, pos, Quaternion.identity);
            if (go != null) Mark(go, id);
            return go;
        }

        public static void Mark(GameObject statue, string id)
        {
            if (statue == null || id == null) return;
            var m = statue.GetComponent<SecretStatueMark>() ?? statue.AddComponent<SecretStatueMark>();
            m.Set(id);
        }

        // ---- the room hook
        [HarmonyPatch(typeof(Room), "SpawnProps")]
        static class Patch_RoomStatues
        {
            static void Prefix(Room __instance, SpawnGroup group, out int __state)
            {
                var objs = R.Get<List<GameObject>>(__instance, "m_propRectObjects");
                __state = objs != null ? objs.Count : -1;
            }

            static void Postfix(Room __instance, SpawnGroup group, int __result, int __state)
            {
                try
                {
                    if (__result <= 0 || __state < 0 || group == null || group != RoomGroup) return;
                    var objs = R.Get<List<GameObject>>(__instance, "m_propRectObjects");
                    if (objs == null) return;
                    var fresh = new List<GameObject>();
                    for (int i = __state; i < objs.Count; i++)
                        if (objs[i] != null && objs[i].GetComponent<PropMonsterStatue>() != null) fresh.Add(objs[i]);
                    if (fresh.Count == 0) return;
                    if (Force == "Every") { foreach (var s in fresh) Mark(s, RollRoom()); return; }
                    var id = RollRoom();
                    if (id == null) return;
                    Mark(fresh[UnityEngine.Random.Range(0, fresh.Count)], id);
                    Plugin.Log.LogInfo("Secret statue placed: " + id);
                }
                catch (Exception e) { Plugin.Log.LogError("Secret statue placement: " + e); }
            }
        }

        [HarmonyPatch(typeof(PropMonsterStatue), "Start")]
        static class Patch_StatueStart
        {
            static void Postfix(PropMonsterStatue __instance)
            {
                var m = __instance != null ? __instance.GetComponent<SecretStatueMark>() : null;
                if (m != null) m.Apply();
            }
        }

        /// <summary>Bots never take a secret statue; nobody takes one whose monster failed to build.</summary>
        [HarmonyPatch(typeof(PropMonsterStatue), "GetCanAction")]
        static class Patch_StatueCanAction
        {
            static void Postfix(PropMonsterStatue __instance, PlayerData actioner, ref bool __result)
            {
                if (!__result) return;
                var m = __instance.GetComponent<SecretStatueMark>();
                if (m == null) return;
                if (actioner == null || actioner.IsBot || !m.Ready) __result = false;
            }
        }

        [HarmonyPatch(typeof(PropMonsterStatue), "OnAction")]
        static class Patch_StatueAction
        {
            static void Prefix(PropMonsterStatue __instance, out string __state)
            {
                var m = __instance != null ? __instance.GetComponent<SecretStatueMark>() : null;
                if (m != null) m.Apply();
                __state = m != null ? m.Id : null;
            }

            static void Postfix(Player actioner, bool __result, string __state)
            {
                if (!__result || __state == null) return;
                try { Secrets.Found(__state); } catch (Exception e) { Plugin.Log.LogError("Secrets.Found(" + __state + "): " + e); }
                try { StatueFound.Announce(actioner, __state); } catch (Exception e) { Plugin.Log.LogError("Secret statue awaken: " + e); }
            }
        }
    }

    /// <summary>Marks a MonsterStatue prop as a secret statue: its monster and its carved secret plinth.</summary>
    public class SecretStatueMark : MonoBehaviour
    {
        public string Id { get; private set; }
        bool m_applied;

        public bool Ready
        {
            get { Player p; return Id != null && MonsterFactory.Built.TryGetValue(Id.Substring(3), out p) && p != null; }
        }

        public void Set(string id) { Id = id; m_applied = false; }

        public void Apply()
        {
            if (Id == null) return;
            var prop = GetComponent<PropMonsterStatue>();
            Player mon;
            if (prop == null || !MonsterFactory.Built.TryGetValue(Id.Substring(3), out mon) || mon == null) return;
            R.Set(prop, "m_prefabMonster", mon);
            var clip = StatueFound.PlinthClip(Id);
            var anim = GetComponent<exSpriteAnimation>();
            if (anim != null && clip != null) anim.Play(clip);
            m_applied = true;
        }

        void LateUpdate()
        {
            if (m_applied || Id == null) return;
            var prop = GetComponent<PropMonsterStatue>();
            Player mon;
            if (prop == null || !MonsterFactory.Built.TryGetValue(Id.Substring(3), out mon)) return;
            if (R.Get<Player>(prop, "m_prefabMonster") != null) Apply();   // Start has run (or the prop was reused)
        }

        void OnDisable()
        {
            // a pooled prop must come back plain
            Id = null; m_applied = false;
            Destroy(this);
        }
    }

    // ================================================================================================= FX templates
    /// <summary>
    /// Effect templates and indicators of the five secret statue monsters. Art + timing: tools/sprites/statuemon_rigs.py ->
    /// art/out_statuemon (TIMING.md). Every hit lands in the statues' own stone-chip puff (StatueImpact).
    /// </summary>
    public static class StmFx
    {
        public static GameObject HitSplat, DeathFx, Awaken, Arrival;
        // Grotesque
        public static GameObject RakeHit, RakeFx, Dust, Shard, Shell, Chip;
        public static StatusOverlayDef[] Crack;
        public static StatusOverlayDef Keystone;
        // Sixfold
        public static GameObject CutHit, CutFx, SlamHit, SlamFx, ThrustHit, ThrustFx, WhirlHit, WhirlFx, Orb, OrbSmall, Pillar;
        public static StatusOverlayDef[] Sigil;          // Ring, Fan, Spiral, Cross
        // Gambit
        public static GameObject StampHit, StampFx, KnightMark, Landing, LeapDust, Checkmate;
        public static StatusOverlayDef Check;
        // Caryatid
        public static GameObject SmashHit, CapitalFx, ColumnBurst, Column;
        public static StatusOverlayDef Shelter;
        // Lachrymosa
        public static GameObject LamentHit, LamentFx, Snuff;
        public static StatusOverlayDef Seen, Unseen;
        public static exSpriteAnimClip ColumnStand, ColumnCrumble;

        public static readonly string[] Rites = { "Ring", "Fan", "Spiral", "Cross" };

        public static void Build()
        {
            var slow = FxFactory.GetStatus("StatusLavaSteveGoo");
            var daze = FxFactory.GetStatus("StatusDizzy");
            HitSplat = GodArt.HitSplat("ModStmHitSplat", "FxStmSplat", 14, 6);
            DeathFx = FxKit.Visual("ModStmDeathFx", "FxStmDeath", "Play");
            Strike.ArtAt(DeathFx, "FxStmDeath", 21, 29);
            Awaken = FxKit.Visual("ModStmAwaken", "FxStmAwaken", "Play");
            Strike.ArtAt(Awaken, "FxStmAwaken", 25, 32);
            Arrival = FxKit.Visual("ModStmArrival", "FxStmArrival", "Play");
            Strike.ArtAt(Arrival, "FxStmArrival", 28, 45);

            // ---- Grotesque
            RakeHit = AimedMelee.Rotating(FxKit.BodyHit("ModStmRakeHit", 1.3f, 0f, 1.1f, 0.14f));   // v0.10 sweep: rake, cut, thrust and lament turn with the aim (box + slash art)
            Strike.HitBox(RakeHit, 22f, 16f);                    // at (14, 8): x 3..25, y 0..16 (talons (14, 6) on the hit frame)
            RakeFx = AimedMelee.Rotating(FxKit.Visual("ModStmRakeFx", "FxStmRake", "Slash"));
            Strike.ArtAt(RakeFx, "FxStmRake", 14, 12);
            Dust = FxKit.TimedHit("ModStmDust", "TrollGroundPoundBigShockwave", "FxStmDust", "Play", 0, 3, 0.3f, 0.2f, slow, 1f, canFlip: false);
            Strike.Ground(Dust, "FxStmDust", 24, 15, 44f, 18f);
            Shard = FxKit.Projectile("ModStmShard", "DFX_skelMageNewProjectile", "FxStmShard", "Fly", 150f, 0.6f, 0.7f, 0.5f);
            if (Shard != null) { Strike.ArtAt(Shard, "FxStmShard", 12, 3); Strike.Collider(Shard, 8f, 6f); }
            Shell = FxKit.Visual("ModStmShell", "FxStmShell", "Play");
            Strike.ArtAt(Shell, "FxStmShell", 23, 27);
            Chip = FxKit.Visual("ModStmChip", "FxStmChip", "Play");
            Strike.ArtAt(Chip, "FxStmChip", 9, 4);
            Crack = new StatusOverlayDef[6];
            for (int i = 0; i < 6; i++) Crack[i] = ModStatus.Indicator("ModIndStmCrack" + (i + 1), "FxStmCrack", (i + 1).ToString(), 1f, OverlayAt.Head);
            Keystone = ModStatus.Indicator("ModIndStmKeystone", "FxStmKeystone", "Loop", -3f, OverlayAt.Feet);

            // ---- Sixfold Idol: four melee hits (one per weapon), the rite orbs and the jade pillar
            CutHit = AimedMelee.Rotating(FxKit.BodyHit("ModStmCutHit", 1.2f, 0f, 1.0f, 0.14f));
            Strike.HitBox(CutHit, 26f, 18f);                     // at (12, 11): x -1..25, y 2..20 (sword tip arcs to x 23)
            CutFx = AimedMelee.Rotating(FxKit.Visual("ModStmCutFx", "FxStmIdolCut", "Sweep"));
            Strike.ArtAt(CutFx, "FxStmIdolCut", 15, 13);
            SlamHit = FxKit.BodyHit("ModStmSlamHit", 1.5f, 0f, 1.7f, 0.14f);
            Strike.HitBox(SlamHit, 22f, 12f);                    // at (16, 4): the mace head lands at (17, -2)
            SlamFx = FxKit.Visual("ModStmSlamFx", "FxStmIdolSlam", "Play");
            Strike.ArtAt(SlamFx, "FxStmIdolSlam", 18, 8);
            ThrustHit = AimedMelee.Rotating(FxKit.BodyHit("ModStmThrustHit", 1.1f, 0f, 0.9f, 0.12f));   // was a flat 36 x 10 bar even when aimed up
            Strike.HitBox(ThrustHit, 36f, 10f);                  // at (22, 13): x 4..40 (spear tip x 37 on the hit frame)
            ThrustFx = AimedMelee.Rotating(FxKit.Visual("ModStmThrustFx", "FxStmIdolThrust", "Play"));
            Strike.ArtAt(ThrustFx, "FxStmIdolThrust", 33, 2);
            WhirlHit = FxKit.BodyHit("ModStmWhirlHit", 0.9f, 0f, 1.2f, 0.36f);
            Strike.HitBox(WhirlHit, 44f, 24f);                   // round it: x -22..22, y -3..21 (the flail circles at 18 px)
            WhirlFx = FxKit.Visual("ModStmWhirlFx", "FxStmIdolWhirl", "Spin");
            Strike.ArtAt(WhirlFx, "FxStmIdolWhirl", 22, 15);
            Orb = FxKit.Projectile("ModStmIdolOrb", "DFX_skelMageNewProjectile", "FxStmIdolOrb", "Fly", 115f, 1.7f, 0.7f, 0.5f);
            if (Orb != null) { Strike.ArtAt(Orb, "FxStmIdolOrb", 7, 4); Strike.Collider(Orb, 7f, 7f); }
            OrbSmall = FxKit.Projectile("ModStmIdolOrbS", "DFX_skelMageNewProjectile", "FxStmIdolOrb", "Fly", 100f, 1.7f, 0.55f, 0.4f);
            if (OrbSmall != null) { Strike.ArtAt(OrbSmall, "FxStmIdolOrb", 7, 4); Strike.Collider(OrbSmall, 6f, 6f); }
            Pillar = FxKit.TimedHit("ModStmIdolPillar", "TrollGroundPoundBigShockwave", "FxStmIdolPillar", "Play", 5, 7, 1.0f, 1.2f, canFlip: false);
            Strike.Ground(Pillar, "FxStmIdolPillar", 13, 15, 12f, 8f);
            Sigil = new StatusOverlayDef[4];
            for (int i = 0; i < 4; i++) Sigil[i] = ModStatus.Indicator("ModIndStmSigil" + Rites[i], "FxStmSigil", Rites[i], 2f, OverlayAt.Head);

            // ---- Gambit
            StampHit = FxKit.BodyHit("ModStmStampHit", 1.4f, 0f, 1.4f, 0.14f);
            Strike.HitBox(StampHit, 20f, 16f);                   // at (14, 8): the nose lands at (14, 7)
            StampFx = FxKit.Visual("ModStmStampFx", "FxStmStamp", "Play");
            Strike.ArtAt(StampFx, "FxStmStamp", 13, 8);
            KnightMark = FxKit.Visual("ModStmKnightMark", "FxStmKnightMark", "Play");
            Strike.ArtAt(KnightMark, "FxStmKnightMark", 15, 7);
            Landing = FxKit.TimedHit("ModStmLanding", "TrollGroundPoundBigShockwave", "FxStmLanding", "Play", 0, 2, 1.0f, 1.3f, canFlip: false);
            Strike.Ground(Landing, "FxStmLanding", 21, 12, 30f, 14f);
            LeapDust = FxKit.Visual("ModStmLeapDust", "FxStmLeapDust", "Play");
            Strike.ArtAt(LeapDust, "FxStmLeapDust", 14, 6);
            Checkmate = FxKit.TimedHit("ModStmCheckmate", "TrollGroundPoundBigShockwave", "FxStmCheckmate", "Play", 0, 2, 0.8f, 1.0f, daze, 1f, canFlip: false);
            Strike.Ground(Checkmate, "FxStmCheckmate", 18, 27, 18f, 12f);
            Check = ModStatus.Indicator("ModIndStmCheck", "FxStmCheck", "Loop", 1f, OverlayAt.Head);

            // ---- Caryatid
            SmashHit = FxKit.BodyHit("ModStmSmashHit", 1.5f, 0f, 1.8f, 0.14f);
            Strike.HitBox(SmashHit, 24f, 14f);                   // at (15, 5): the capital comes down at (14, 4)
            CapitalFx = FxKit.Visual("ModStmCapitalFx", "FxStmCapital", "Play");
            Strike.ArtAt(CapitalFx, "FxStmCapital", 18, 13);
            ColumnBurst = FxKit.TimedHit("ModStmColumnBurst", "TrollGroundPoundBigShockwave", "FxStmColumn", "Burst", 4, 6, 1.0f, 2.2f, canFlip: false);
            Strike.Ground(ColumnBurst, "FxStmColumn", 12, 29, 16f, 10f);
            var csh = SpriteSheets.Get("FxStmColumn");
            if (csh != null)
            {
                ColumnStand = new ClipBuilder(csh, "Stand", "ModStmColumnStand").Loop().Build();
                ColumnCrumble = new ClipBuilder(csh, "Crumble", "ModStmColumnCrumble").Once().Build();
                Column = FxFactory.Visual("ModStmColumn", csh, ColumnStand, true, 0f);
                Strike.ArtAt(Column, "FxStmColumn", 12, 29);
            }
            Shelter = ModStatus.Indicator("ModIndStmShelter", "FxStmShelter", "Loop", -3f, OverlayAt.Feet);

            // ---- Lachrymosa
            LamentHit = AimedMelee.Rotating(FxKit.BodyHit("ModStmLamentHit", 1.4f, 0f, 1.2f, 0.14f));
            Strike.HitBox(LamentHit, 26f, 22f);                  // at (13, 13): her hands reach (14, 18) and (11, 14)
            LamentFx = AimedMelee.Rotating(FxKit.Visual("ModStmLamentFx", "FxStmLament", "Slash"));
            Strike.ArtAt(LamentFx, "FxStmLament", 14, 15);
            Snuff = FxKit.Visual("ModStmSnuff", "FxStmSnuff", "Play");
            Strike.ArtAt(Snuff, "FxStmSnuff", 6, 60);
            Seen = ModStatus.Indicator("ModIndStmSeen", "FxStmSeen", "Loop", 1f, OverlayAt.Head);
            Unseen = ModStatus.Indicator("ModIndStmUnseen", "FxStmUnseen", "Loop", -3f, OverlayAt.Feet);

            foreach (var go in new[] { Shard, Orb, OrbSmall, Pillar, Dust, Landing, Checkmate, ColumnBurst })
                StatueImpact.Theme(go);
            Plugin.Log.LogInfo("Secret statue FX templates built");
        }
    }

    /// <summary>The statues' impact puffs (FxStmImpact Wall/Hit): a copy of each neutral mod puff a template carries, reskinned.</summary>
    public static class StatueImpact
    {
        static readonly Dictionary<GameObject, GameObject> s_puff = new Dictionary<GameObject, GameObject>();

        public static void Theme(GameObject fx)
        {
            if (fx == null) return;
            foreach (var d in fx.GetComponentsInChildren<DamageEffect>(true))
            {
                if (d.m_contactData == null) continue;
                foreach (var c in d.m_contactData)
                {
                    if (c == null || c.m_spawnOnHit == null) continue;
                    var p = Of(c.m_spawnOnHit);
                    if (p != null) c.m_spawnOnHit = p;
                }
            }
        }

        static GameObject Of(GameObject neutral)
        {
            if (neutral == null || !neutral.name.StartsWith("ModImpactMod")) return null;
            GameObject g;
            if (s_puff.TryGetValue(neutral, out g)) return g;
            var sh = SpriteSheets.Get("FxStmImpact");
            if (sh == null) return null;
            bool wall = neutral.name.StartsWith("ModImpactModWall");
            string name = "ModImpactStm" + neutral.name.Substring("ModImpactMod".Length);
            g = MonsterFactory.ClonePrefab(neutral, name);
            FxFactory.Templates[name] = g;
            FxFactory.Reskin(g, new ClipBuilder(sh, wall ? "Wall" : "Hit", name + "Clip").Once().Build(), sh);
            var spr = g.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = exPlane.Anchor.MidCenter; spr.offset = Vector2.zero; spr.color = Color.white; }
            s_puff[neutral] = g;
            return g;
        }
    }

    // ================================================================================================= the pack
    public static class StatuePack
    {
        static ClipBuilder Cast(SpriteSheet sh, string anim, string clip, int release)
        {
            return new ClipBuilder(sh, anim, clip).Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(Mathf.Max(0, release - 1), "AnimInputMultiplyStop").Ev(Mathf.Max(0, release - 1), "AnimInputOff").Ev(release, "AnimMoveStop");
        }

        // Grotesque: a talon rake; Set in Stone: turn to stone 2 s (can't be hurt, can't move), store the hits it takes
        // and burst out in 4 + 2 per stored hit shards (max 12). Passive (brain): crumble and reform once.
        static void GrotesqueKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int hit = Kit.AddEffect(p, StmFx.RakeHit, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 8f);
            int fx = Kit.AddEffect(p, StmFx.RakeFx, attach: true, offsetX: 12f, offsetY: 9f);
            var rk = Kit.Melee(sh, "Rake", "ModStmGrotesqueRake", v, 3, hit, 55f);
            rk.Ev(3, "AnimAttack", fx);
            // StoneOn 4 + StoneHold x5 (10 frames, 2.0 s) + StoneBurst 4: stone from frame 3, bursts on frame 15
            var st = new ClipBuilder(sh, "StoneOn", "ModStmGrotesqueStone").Once().Then("StoneHold", 5).Then("StoneBurst")
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(0, "AnimInputMultiplyStop").Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop")
                .Ev(3, "StmStoneOn").EvO(3, "AnimSound", v).Ev(15, "StmStoneBurst").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rk.Build(), 1.3f, rangeInner: 10f, rangeOuter: 32f));
            Kit.SetSpecial(p, Kit.Attack(sp, st, 0f, rangeInner: 0f, rangeOuter: 60f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
        }

        // Sixfold Idol: four basic weapons, one picked at random each swing (StmIdolBrain sets the next one); the Cast is
        // a rite from a shuffled bag of four (Ring, Fan, Spiral, Cross), its sigil shown over the head beforehand.
        static void SixfoldKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int cut = Kit.AddEffect(p, StmFx.CutHit, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 11f);
            int cutFx = Kit.AddEffect(p, StmFx.CutFx, attach: true, offsetX: 10f, offsetY: 14f);
            int slam = Kit.AddEffect(p, StmFx.SlamHit, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 4f);
            int slamFx = Kit.AddEffect(p, StmFx.SlamFx, offsetX: 17f, offsetY: 1f);
            int thr = Kit.AddEffect(p, StmFx.ThrustHit, attach: true, destroyOnAnimEnd: true, offsetX: 22f, offsetY: 13f);
            int thrFx = Kit.AddEffect(p, StmFx.ThrustFx, attach: true, offsetX: 6f, offsetY: 17f);
            int wh = Kit.AddEffect(p, StmFx.WhirlHit, attach: true, destroyOnAnimEnd: true, offsetX: 0f, offsetY: 9f);
            int whFx = Kit.AddEffect(p, StmFx.WhirlFx, attach: true, offsetX: 0f, offsetY: 7f);
            var c1 = Kit.Melee(sh, "Cut", "ModStmSixfoldCut", v, 3, cut, 40f); c1.Ev(3, "AnimAttack", cutFx).Ev(0, "StmIdolReroll");
            var c2 = Kit.Melee(sh, "Slam", "ModStmSixfoldSlam", v, 3, slam, 30f); c2.Ev(3, "AnimAttack", slamFx).Ev(0, "StmIdolReroll");
            var c3 = Kit.Melee(sh, "Thrust", "ModStmSixfoldThrust", v, 3, thr, 60f); c3.Ev(3, "AnimAttack", thrFx).Ev(0, "StmIdolReroll");
            var c4 = Kit.Melee(sh, "Whirl", "ModStmSixfoldWhirl", v, 2, wh, 0f); c4.Ev(2, "AnimAttack", whFx).Ev(0, "StmIdolReroll");
            var cs = Cast(sh, "Cast", "ModStmSixfoldRite", 5).Ev(0, "StmIdolRite").Ev(5, "StmIdolFire").EvO(5, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, c1.Build(), 1.4f, rangeInner: 8f, rangeOuter: 30f));
            atk.Add(Kit.Attack(a0, c2.Build(), 1.4f, rangeInner: 8f, rangeOuter: 28f));
            atk.Add(Kit.Attack(a0, c3.Build(), 1.4f, rangeInner: 14f, rangeOuter: 44f));
            atk.Add(Kit.Attack(a0, c4.Build(), 1.4f, rangeInner: 0f, rangeOuter: 26f));
            Kit.SetSpecial(p, Kit.Attack(sp, cs, 0f, rangeInner: 30f, rangeOuter: 130f, rangeRetreat: 20f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 13f);
        }

        // Gambit: rear and slam the head down; Knight's Tour: three L-shaped leaps, each landing marked 0.4 s first.
        static void GambitKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int hit = Kit.AddEffect(p, StmFx.StampHit, attach: true, destroyOnAnimEnd: true, offsetX: 14f, offsetY: 8f);
            int fx = Kit.AddEffect(p, StmFx.StampFx, offsetX: 14f, offsetY: 1f);
            var sl = Kit.Melee(sh, "Slam", "ModStmGambitSlam", v, 3, hit, 45f);
            sl.Ev(3, "AnimAttack", fx).Ev(3, "StmGambitSlam");
            // (TourCrouch 3 + TourAir 3 + TourLand 3) x 3 = 27 frames; leap k: mark 9k, jump 9k+3, land 9k+6
            var tb = new ClipBuilder(sh, "TourCrouch", "ModStmGambitTour").Once().Then("TourAir").Then("TourLand")
                .Then("TourCrouch").Then("TourAir").Then("TourLand").Then("TourCrouch").Then("TourAir").Then("TourLand")
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(0, "AnimInputMultiplyStop").Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop");
            for (int k = 0; k < 3; k++)
            {
                int b = k * 9;
                tb.Ev(b, "StmTourMark").Ev(b + 3, "AnimStartInvincibility").Ev(b + 3, "AnimCollideOff").Ev(b + 3, "StmTourJump")
                  .Ev(b + 6, "StmTourLand").Ev(b + 6, "AnimCollideOn").Ev(b + 6, "AnimStopInvincibility");
                if (k == 0) tb.EvO(b + 3, "AnimSound", v);
            }
            var tour = tb.Ev(-1, "StmTourEnd").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl.Build(), 1.3f, rangeInner: 8f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, tour, 0f, rangeInner: 30f, rangeOuter: 140f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 9f);
        }

        // Caryatid: smash the capital down in front; Raise Column under the hero (0.6 s warning), it stands 6 s as stone.
        static void CaryatidKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int hit = Kit.AddEffect(p, StmFx.SmashHit, attach: true, destroyOnAnimEnd: true, offsetX: 15f, offsetY: 5f);
            int fx = Kit.AddEffect(p, StmFx.CapitalFx, offsetX: 15f, offsetY: 1f);
            var sm = Kit.Melee(sh, "Smash", "ModStmCaryatidSmash", v, 4, hit, 40f);
            sm.Ev(4, "AnimAttack", fx);
            var rs = Cast(sh, "Raise", "ModStmCaryatidRaise", 4).Ev(4, "StmRaiseColumn").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sm.Build(), 1.5f, rangeInner: 10f, rangeOuter: 32f));
            Kit.SetSpecial(p, Kit.Attack(sp, rs, 0f, rangeInner: 20f, rangeOuter: 140f, rangeRetreat: 30f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
        }

        // Lachrymosa: Lament (both hands rake); Lights Out: she pinches out her halo (release frame 4) and the room goes dark
        // for 2.5 s (LightsOut), with the dark cue as the hero's warning.
        static void LachrymosaKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int hit = Kit.AddEffect(p, StmFx.LamentHit, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 13f);
            int fx = Kit.AddEffect(p, StmFx.LamentFx, attach: true, offsetX: 12f, offsetY: 14f);
            var la = Kit.Melee(sh, "Lament", "ModStmLachrymosaLament", v, 4, hit, 50f);
            la.Ev(4, "AnimAttack", fx);
            var cue = LightsOut.Cue;
            var lo = Cast(sh, "Snuff", "ModStmLachrymosaLightsOut", 4).Ev(4, "StmLightsOut");
            if (cue != null) lo.EvO(4, "AnimSound", cue);
            if (v != null) lo.EvO(1, "AnimSound", v);
            var lights = lo.Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, la.Build(), 1.4f, rangeInner: 10f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, lights, 0f, rangeInner: 30f, rangeOuter: 180f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
        }

        static void Statue(GameObject go, Player p)
        {
            Kit.AddDeathSpawn(p, StmFx.DeathFx);
            Strike.DeathAtFeet(p);
            GodArt.UseHitSplat(p, StmFx.HitSplat);
            // its secret plinth is its statue pose wherever the game asks for one
            var clip = StatueFound.PlinthClip(go.name);
            if (clip != null) R.Set(p, "m_animationStatue", clip);
        }

        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            // unique finals: no parent, evolve no further, tier-3 cost so they get the T3 multipliers (0.8x damage, slower specials)
            new MonsterDef { id = "StmGrotesque", art = "StmGrotesque", basePrefab = "EnemyCapraDemon", health = 11f, speedMult = 1.05f,
                             evolveCost = 4.5f, kit = GrotesqueKit, customize = Statue },
            new MonsterDef { id = "StmSixfold", art = "StmSixfold", basePrefab = "EnemyTroll", health = 11.5f, speedMult = 0.92f,
                             evolveCost = 4.5f, kit = SixfoldKit, customize = Statue },
            new MonsterDef { id = "StmGambit", art = "StmGambit", basePrefab = "EnemyMinotaur", health = 11f, speedMult = 1.0f,
                             evolveCost = 4.5f, kit = GambitKit, customize = Statue },
            new MonsterDef { id = "StmCaryatid", art = "StmCaryatid", basePrefab = "EnemyDarkGuardian", health = 11.5f, speedMult = 0.9f,
                             evolveCost = 4.5f, kit = CaryatidKit, customize = Statue },
            new MonsterDef { id = "StmLachrymosa", art = "StmLachrymosa", basePrefab = "EnemyPriestess", health = 12.5f, speedMult = 1.0f,
                             evolveCost = 4.5f, kit = LachrymosaKit, customize = Statue },
        };

        static bool s_done;

        public static void Register()
        {
            if (s_done) return;
            s_done = true;
            StmFx.Build();
            foreach (var m in Monsters) MonsterFactory.Build(m);
            SecretStatues.Ids.Clear();
            foreach (var m in Monsters) if (MonsterFactory.Built.ContainsKey(m.id)) SecretStatues.Ids.Add(m.PrefabName);
            if (SecretStatues.Ids.Count != Monsters.Count)
                Plugin.Log.LogError("Secret statues: only " + SecretStatues.Ids.Count + " of " + Monsters.Count + " built");
            foreach (var e in StatueSecrets.Entries()) Secrets.Add(e);
            Strike.KeepAllScales();
        }

        /// <summary>Self-test (wired into SelfTest.cs).</summary>
        public static void SelfCheck(Action<string> bad)
        {
            if (SecretStatues.Ids.Count != 5) bad("secret statues: " + SecretStatues.Ids.Count + " of 5 registered");
            var parents = new HashSet<string>();
            foreach (var kv in MonsterFactory.Built)
            {
                var to = kv.Value != null ? kv.Value.GetEvolveTo() : null;
                if (to != null) foreach (var t in to) if (t != null) parents.Add(t.gameObject.name);
            }
            foreach (var m in Monsters)
            {
                Player p;
                if (!MonsterFactory.Built.TryGetValue(m.id, out p) || p == null) { bad("secret statue " + m.id + " failed to build"); continue; }
                var to = p.GetEvolveTo();
                if (to != null && to.Length > 0) bad(m.PrefabName + " evolves further (" + to.Length + ")");
                if (parents.Contains(m.PrefabName)) bad(m.PrefabName + " is offered by an evolution (secret statues have no parent)");
                if (Mathf.Abs(R.Get<float>(p, "m_evolveCost") - 4.5f) > 0.01f) bad(m.PrefabName + " is not a tier-3 cost");
                if (StatueFound.PlinthClip(m.PrefabName) == null) bad(m.PrefabName + ": no secret plinth (art/out_statuemon StmStatues)");
                MonsterTip tip;
                if (!MonsterTipsData.TryGet(m.PrefabName, out tip)) bad(m.PrefabName + " has no monster tip");
                if (!SecretStatues.Is(m.PrefabName)) bad(m.PrefabName + " is not recognised by SecretStatues.Is");
                if (!Statues.Excluded(m.PrefabName)) bad(m.PrefabName + " is not excluded from the statue group");
            }
            foreach (var kv in new Dictionary<string, object>
            {
                { "HitSplat", StmFx.HitSplat }, { "DeathFx", StmFx.DeathFx }, { "Awaken", StmFx.Awaken }, { "Arrival", StmFx.Arrival },
                { "RakeHit", StmFx.RakeHit }, { "RakeFx", StmFx.RakeFx }, { "Dust", StmFx.Dust }, { "Shard", StmFx.Shard },
                { "Shell", StmFx.Shell }, { "Chip", StmFx.Chip }, { "Keystone", StmFx.Keystone },
                { "CutHit", StmFx.CutHit }, { "CutFx", StmFx.CutFx }, { "SlamHit", StmFx.SlamHit }, { "SlamFx", StmFx.SlamFx },
                { "ThrustHit", StmFx.ThrustHit }, { "ThrustFx", StmFx.ThrustFx }, { "WhirlHit", StmFx.WhirlHit }, { "WhirlFx", StmFx.WhirlFx },
                { "Orb", StmFx.Orb }, { "OrbSmall", StmFx.OrbSmall }, { "Pillar", StmFx.Pillar },
                { "StampHit", StmFx.StampHit }, { "StampFx", StmFx.StampFx }, { "KnightMark", StmFx.KnightMark }, { "Landing", StmFx.Landing },
                { "LeapDust", StmFx.LeapDust }, { "Checkmate", StmFx.Checkmate }, { "Check", StmFx.Check },
                { "SmashHit", StmFx.SmashHit }, { "CapitalFx", StmFx.CapitalFx }, { "ColumnBurst", StmFx.ColumnBurst }, { "Column", StmFx.Column },
                { "Shelter", StmFx.Shelter }, { "LamentHit", StmFx.LamentHit }, { "LamentFx", StmFx.LamentFx }, { "Snuff", StmFx.Snuff },
                { "Seen", StmFx.Seen }, { "Unseen", StmFx.Unseen },
            })
                if (kv.Value == null || (kv.Value is UnityEngine.Object && (UnityEngine.Object)kv.Value == null)) bad("secret statue FX " + kv.Key + " missing");
            if (StmFx.Crack == null || Array.Exists(StmFx.Crack, d => d == null)) bad("Grotesque crack indicators missing");
            if (StmFx.Sigil == null || Array.Exists(StmFx.Sigil, d => d == null)) bad("Sixfold sigil indicators missing");
            // offered ONLY by secret statues. No spawn group, god tree, starter list or evolution may offer them.
            foreach (var g in Resources.FindObjectsOfTypeAll<SpawnGroup>())
            {
                if (g == null || g.gameObject.scene.IsValid()) continue;
                var items = R.Get<List<SpawnItem>>(g, "m_items");
                if (items == null) continue;
                foreach (var it in items)
                    if (it != null && it.m_object != null && SecretStatues.Is(it.m_object.name))
                        bad(it.m_object.name + " is in spawn group " + g.gameObject.name + " (secret statues only)");
            }
            var gods = SystemDeity.GetDeities();
            if (gods != null)
                foreach (var d in gods)
                {
                    var st = d != null ? d.GetStartingMonsters() : null;
                    if (st != null) foreach (var go in st) if (go != null && SecretStatues.Is(go.name)) bad(go.name + " is a starter of " + d.GetName());
                }
            if (StatuePlacement.Prop == null) bad("secret statues: the vanilla MonsterStatue prop was not found");
            // the odds: 120000 room rolls within 0.3 points of 1/12 and 1/200
            if (SecretStatues.Ids.Count == 5 && StatuePlacement.Force == "Off")
            {
                int normal = 0, legend = 0, n = 120000;
                for (int i = 0; i < n; i++)
                {
                    var r = StatuePlacement.RollRoom();
                    if (r == SecretStatues.Lachrymosa) legend++; else if (r != null) normal++;
                }
                if (Mathf.Abs(normal * 100f / n - 100f / 12f) > 0.4f) bad("secret statue odds: normal " + (normal * 100f / n) + " in 100 rooms, want 8.3");
                if (Mathf.Abs(legend * 100f / n - 0.5f) > 0.12f) bad("secret statue odds: legendary " + (legend * 100f / n) + " in 100 rooms, want 0.5");
            }
            foreach (var e in StatueSecrets.Entries())
            {
                SecretDef got = null;
                foreach (var x in Secrets.All) if (x.id == e.id) got = x;
                if (got == null) bad("secret " + e.id + " is not registered");
            }
        }
    }

    /// <summary>The five Secrets entries (group "Statues"), with riddles hinting how to find them.</summary>
    public static class StatueSecrets
    {
        public static IEnumerable<SecretDef> Entries()
        {
            yield return new SecretDef
            {
                id = SecretStatues.Grotesque, name = "Grotesque", group = "Statues", iconSheet = "StmGrotesque",
                riddle = "A statue mended with gold. This one crouches with its wings folded",
                rarity = "Rare",
                text = "A gargoyle that turns to stone and throws back the hits it took",
            };
            yield return new SecretDef
            {
                id = SecretStatues.Sixfold, name = "Sixfold Idol", group = "Statues", iconSheet = "StmSixfold",
                riddle = "A gold-seamed plinth with six pips cut in it. Six hands, and none agree",
                rarity = "Rare",
                text = "A six-armed bronze idol. Every swing is a different weapon",
            };
            yield return new SecretDef
            {
                id = SecretStatues.Gambit, name = "Gambit", group = "Statues", iconSheet = "StmGambit",
                riddle = "Gold in the cracks of a plinth carved with an L. It never walks straight",
                rarity = "Rare",
                text = "A living chess knight. It leaps in L shapes and puts the hero in check",
            };
            yield return new SecretDef
            {
                id = SecretStatues.Caryatid, name = "Caryatid", group = "Statues", iconSheet = "StmCaryatid",
                riddle = "A gold-mended plinth with a column cut in it. She holds up the ceiling",
                rarity = "Rare",
                text = "A marble maiden who raises columns of solid stone",
            };
            yield return new SecretDef
            {
                id = SecretStatues.Lachrymosa, name = "Lachrymosa", group = "Statues", iconSheet = "StmLachrymosa",
                riddle = "Legendary. A plinth gilded all round, a light above her. Keep the lights on",
                rarity = "Legendary",
                text = "A weeping angel. Stone while watched, swift when not. She puts out the lights",
            };
        }
    }

    /// <summary>The secret plinth clips (art/out_statuemon StmStatues, "Statue_&lt;sheet&gt;") and the awakening.</summary>
    public static class StatueFound
    {
        public const string PlinthSheet = "StmStatues";
        static readonly Dictionary<string, exSpriteAnimClip> s_clips = new Dictionary<string, exSpriteAnimClip>();

        /// <summary>The looping secret plinth clip of a secret monster ("ModStmX" -> anim "Statue_StmX").</summary>
        public static exSpriteAnimClip PlinthClip(string prefabId)
        {
            if (string.IsNullOrEmpty(prefabId) || !prefabId.StartsWith("Mod")) return null;
            exSpriteAnimClip c;
            if (s_clips.TryGetValue(prefabId, out c) && c != null) return c;
            var sh = SpriteSheets.Get(PlinthSheet);
            string anim = "Statue_" + prefabId.Substring(3);
            if (sh == null || !sh.Has(anim)) return null;
            c = new ClipBuilder(sh, anim, "ModSecretStatue_" + prefabId.Substring(3)).Loop().Build();
            if (c != null) SpriteSheets.Keep(c);
            s_clips[prefabId] = c;
            return c;
        }

        /// <summary>A player took a secret statue: the gold seam blazes and the stone skin bursts off.</summary>
        public static void Announce(Player actioner, string id)
        {
            var body = actioner != null ? actioner.GetPlayerData() != null ? actioner.GetPlayerData().GameObject : null : null;
            Vector2 at = body != null ? (Vector2)body.transform.position : (actioner != null ? (Vector2)actioner.transform.position : Vector2.zero);
            if (StmFx.Awaken != null) SystemPool.Spawn(StmFx.Awaken, at);
            Plugin.Log.LogInfo("Secret statue taken: " + id);
        }
    }

    // ================================================================================================= brains
    public abstract class StmBrain : MonoBehaviour
    {
        protected Health m_health;
        protected Player m_player;
        protected exSprite m_sprite;
        protected PlayerMovement m_move;
        protected virtual void Awake()
        {
            m_health = GetComponent<Health>(); m_player = GetComponent<Player>(); m_sprite = GetComponent<exSprite>(); m_move = GetComponent<PlayerMovement>();
        }
        protected bool Alive { get { return m_health != null && m_health.IsAlive(); } }
        protected Vector2 Feet { get { return (Vector2)transform.position + new Vector2(0f, m_sprite != null ? m_sprite.offset.y + 2f : 0f); } }
        protected DamageSource Own()
        {
            var pd = m_player != null ? R.Get<PlayerData>(m_player, "m_playerData") : null;
            return new DamageSource(gameObject, gameObject, pd);
        }
        protected Vector2 Facing
        {
            get
            {
                var d = m_move != null ? R.Get<Vector2>(m_move, "m_faceDirection") : Vector2.zero;
                if (d.sqrMagnitude < 0.01f) d = new Vector2(transform.localScale.x < 0f ? -1f : 1f, 0f);
                return d.normalized;
            }
        }
        protected static float Angle(Vector2 d) { return Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg; }
        protected static bool From(DamageInfo d, string prefix)
        {
            var src = d != null && d.m_source != null ? d.m_source.m_source : null;
            return src != null && src.name.StartsWith(prefix);
        }
        protected static GameObject LiveHero()
        {
            var h = ModUtil.Hero();
            var hh = h != null ? h.GetComponent<Health>() : null;
            return hh != null && hh.IsAlive() ? h : null;
        }
        /// <summary>Toward the hero if he is about, else the way it faces.</summary>
        protected Vector2 Aim()
        {
            var h = LiveHero();
            if (h == null) return Facing;
            var d = (Vector2)h.transform.position - Feet;
            return d.sqrMagnitude < 1f ? Facing : d.normalized;
        }
        /// <summary>Resistance multiplier owned by this brain (applied on top of whatever else set m_damageResistanceFinal).</summary>
        float m_resist = 1f;
        protected void Resist(float mult)
        {
            if (m_health == null || Mathf.Abs(mult - m_resist) < 0.0001f) return;
            float cur = R.Get<float>(m_health, "m_damageResistanceFinal");
            R.Set(m_health, "m_damageResistanceFinal", cur / m_resist * mult);
            m_resist = mult;
        }
        protected virtual void OnDisable() { Resist(1f); }
    }

    /// <summary>
    /// Grotesque. Set in Stone: from StmStoneOn to StmStoneBurst it is stone: no damage reaches it (Patch_StatueDamage),
    /// each hit it takes is stored (max 6, shown as cracked pips over it), and it bursts out in 4 + 2 per stored hit
    /// shards. Passive Crumble and Reform: the first killing blow of each body crumbles it to a heap of rubble (Crumble
    /// 0.56 s + Rubble 2 s + Reform 0.64 s, can't be hurt), then it stands with 3.5 health; the ember ring under it shows the
    /// reform is still to come.
    /// </summary>
    public class StmGrotesqueBrain : StmBrain
    {
        public const int MaxStored = 6, BaseShards = 4, PerHit = 2, MaxShards = 12;
        public const float ReformHealth = 3.5f, StoneMax = 3.2f, RubbleMax = 4.2f;
        public bool Stone { get; private set; }
        public bool Rubble { get; private set; }
        public bool CanReform { get { return !m_reformed; } }
        int m_stored;
        bool m_reformed;
        float m_t, m_lastStore;
        static exSpriteAnimClip s_crumble;

        void OnEnable() { Stone = false; Rubble = false; m_stored = 0; m_reformed = false; m_t = 0f; Show(); }
        protected override void OnDisable()
        {
            base.OnDisable();
            ModInd.Count(gameObject, StmFx.Crack, 0); ModInd.Set(gameObject, StmFx.Keystone, false);
            Stone = false; Rubble = false;
        }

        void Show()
        {
            ModInd.Set(gameObject, StmFx.Keystone, Alive && !m_reformed && !Rubble);
            ModInd.Count(gameObject, StmFx.Crack, Stone ? Mathf.Max(0, m_stored) : 0);
        }

        public void StmStoneOn()
        {
            if (!Alive) return;
            Stone = true; m_stored = 0; m_t = 0f;
            if (StmFx.Dust != null) FxFactory.SpawnOwned(StmFx.Dust, Feet, Own());
            Show();
        }

        public void StmStoneBurst()
        {
            if (!Stone) return;
            Stone = false;
            int n = Mathf.Min(MaxShards, BaseShards + PerHit * m_stored);
            m_stored = 0;
            Show();
            if (!Alive) return;
            Vector2 at = Feet + new Vector2(0f, 10f);
            if (StmFx.Shell != null) SystemPool.Spawn(StmFx.Shell, Feet);
            if (StmFx.Shard == null) return;
            float a0 = Angle(Aim());
            var src = Own();
            for (int i = 0; i < n; i++) FxFactory.SpawnOwned(StmFx.Shard, at, src, a0 + i * 360f / n);
        }

        /// <summary>A hit landed on the stone shell: store it (once per 0.12 s, so one swing counts once).</summary>
        public void Store(Vector2 where)
        {
            if (Time.time - m_lastStore < 0.12f) return;
            m_lastStore = Time.time;
            if (m_stored < MaxStored) m_stored++;
            if (StmFx.Chip != null) SystemPool.Spawn(StmFx.Chip, where);
            Show();
        }

        /// <summary>The first killing blow: crumble to rubble (status anim Crumble + Rubble x6 + Reform), then reform.</summary>
        public bool TryCrumble()
        {
            if (m_reformed || Rubble || m_player == null) return false;
            m_reformed = true; Rubble = true; Stone = false; m_t = 0f;
            if (m_health != null) R.Set(m_health, "m_healthCurrent", Mathf.Max(0.05f, R.Get<float>(m_health, "m_healthCurrent")));
            if (s_crumble == null)
            {
                var sh = SpriteSheets.Get("StmGrotesque");
                if (sh != null)
                    s_crumble = new ClipBuilder(sh, "Crumble", "ModStmGrotesqueCrumble").Once().Then("Rubble", 4).Then("Reform")
                        .Ev(4, "AnimCollideOff").Ev(-1, "StmReformed").Ev(-1, "AnimCollideOn").Build();
                if (s_crumble != null) SpriteSheets.Keep(s_crumble);
            }
            if (s_crumble != null) m_player.StartStatusAnimation(s_crumble);
            if (StmFx.Shell != null) SystemPool.Spawn(StmFx.Shell, Feet);
            Show();
            return true;
        }

        public void StmReformed()
        {
            if (!Rubble) return;
            Rubble = false;
            if (m_health != null && m_health.IsAlive())
            {
                float max = R.Get<float>(m_health, "m_healthMaxFinal");
                R.Set(m_health, "m_healthCurrent", Mathf.Min(max, Mathf.Max(R.Get<float>(m_health, "m_healthCurrent"), ReformHealth)));
                m_health.SendMessage(Constants.MSG_SNAPHEALTH, SendMessageOptions.DontRequireReceiver);
            }
            if (m_player != null) m_player.AnimCollideOn();
            Show();
        }

        void Update()
        {
            if (!Stone && !Rubble) return;
            m_t += Time.deltaTime;
            // safety: a cut-short clip never leaves it stone or rubble
            if (Stone && m_t > StoneMax) StmStoneBurst();
            if (Rubble && m_t > RubbleMax) StmReformed();
        }
    }

    /// <summary>
    /// Sixfold Idol. Every basic swing is one of its four weapons at random (never the same three times running): each
    /// clip's frame 0 picks the next through Attacks.SetNextAttackOverride. Its rites come from a shuffled bag of four
    /// (each shown once before any repeats); the coming rite's sigil shows over its head as soon as the special is ready
    /// and while it casts. Ring: 10 orbs all round. Fan: 5 at the hero, twice. Spiral: 3 turning arms, 18 small orbs.
    /// Cross: jade spikes along + then x (3 a line, 24 px apart).
    /// </summary>
    public class StmIdolBrain : StmBrain
    {
        public const int Basics = 4;
        readonly List<int> m_bag = new List<int>();
        int m_next = -1, m_last = -1, m_last2 = -1, m_shown = -1;
        bool m_casting;
        float m_castT;
        Attacks m_attacks;

        protected override void Awake() { base.Awake(); m_attacks = m_player != null ? R.Get<Attacks>(m_player, "m_playerAttacks") : null; }
        void OnEnable() { m_bag.Clear(); m_next = -1; m_casting = false; m_shown = -1; m_last = m_last2 = -1; StmIdolReroll(); }
        protected override void OnDisable() { base.OnDisable(); ShowSigil(-1); StopAllCoroutines(); }

        int Next()
        {
            if (m_next < 0)
            {
                if (m_bag.Count == 0) { for (int i = 0; i < 4; i++) m_bag.Insert(UnityEngine.Random.Range(0, m_bag.Count + 1), i); }
                m_next = m_bag[0]; m_bag.RemoveAt(0);
            }
            return m_next;
        }

        void ShowSigil(int rite)
        {
            if (rite == m_shown) return;
            m_shown = rite;
            if (StmFx.Sigil == null) return;
            for (int i = 0; i < StmFx.Sigil.Length; i++) ModInd.Set(gameObject, StmFx.Sigil[i], i == rite);
        }

        void Update()
        {
            if (!Alive) { ShowSigil(-1); return; }
            if (m_casting && (m_castT += Time.deltaTime) > 2f) m_casting = false;      // the cast was cut short
            bool ready = m_player != null && m_player.HasSpecialAttack() && m_player.GetSpecialReady();
            ShowSigil(ready || m_casting ? Next() : -1);
        }

        /// <summary>Frame 0 of every basic clip: choose the weapon of the NEXT swing.</summary>
        public void StmIdolReroll()
        {
            if (m_attacks == null) return;
            int pick;
            int guard = 0;
            do { pick = UnityEngine.Random.Range(0, Basics); } while (pick == m_last && m_last == m_last2 && ++guard < 8);
            m_last2 = m_last; m_last = pick;
            m_attacks.SetNextAttackOverride(pick);
        }

        public void StmIdolRite() { m_casting = true; m_castT = 0f; Next(); }

        public void StmIdolFire()
        {
            int rite = Next();
            m_next = -1; m_casting = false;
            if (!Alive) return;
            StopAllCoroutines();
            StartCoroutine(Fire(rite, Own()));
        }

        IEnumerator<object> Fire(int rite, DamageSource src)
        {
            Vector2 aim = Aim();
            float a0 = Angle(aim);
            Vector2 from = Feet + new Vector2(aim.x >= 0f ? 10f : -10f, 12f);
            switch (rite)
            {
                case 0:   // Ring: 10 orbs evenly round, one gap-free wall of jade
                    if (StmFx.Orb != null) for (int i = 0; i < 10; i++) FxFactory.SpawnOwned(StmFx.Orb, from, src, a0 + i * 36f);
                    break;
                case 1:   // Fan: 5 at the hero 15 degrees apart, then 5 more between them 0.3 s later
                    if (StmFx.Orb == null) break;
                    for (int i = -2; i <= 2; i++) FxFactory.SpawnOwned(StmFx.Orb, from, src, a0 + i * 15f);
                    yield return new WaitForSeconds(0.3f);
                    if (!Alive) yield break;
                    a0 = Angle(Aim()); from = Feet + new Vector2(aim.x >= 0f ? 10f : -10f, 12f);
                    for (int i = 0; i < 4; i++) FxFactory.SpawnOwned(StmFx.Orb, from, src, a0 - 22.5f + i * 15f);
                    break;
                case 2:   // Spiral: 3 arms turning 24 degrees a tick, 6 ticks 0.12 s apart
                    if (StmFx.OrbSmall == null) break;
                    for (int t = 0; t < 6; t++)
                    {
                        if (!Alive) yield break;
                        from = Feet + new Vector2(0f, 12f);
                        for (int k = 0; k < 3; k++) FxFactory.SpawnOwned(StmFx.OrbSmall, from, src, a0 + k * 120f + t * 24f);
                        yield return new WaitForSeconds(0.12f);
                    }
                    break;
                case 3:   // Cross: spikes along the four axes, then the diagonals 0.6 s later
                    if (StmFx.Pillar == null) break;
                    for (int pass = 0; pass < 2; pass++)
                    {
                        if (!Alive) yield break;
                        Vector2 c = Feet;
                        for (int axis = 0; axis < 4; axis++)
                        {
                            float a = (axis * 90f + pass * 45f) * Mathf.Deg2Rad;
                            var d = new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.75f);
                            for (int k = 1; k <= 3; k++)
                            {
                                var at = c + d * (24f * k);
                                if (ModUtil.SafePoint(c, at, 4f) != at) break;   // stop at a wall
                                FxFactory.SpawnOwned(StmFx.Pillar, at, src);
                            }
                        }
                        yield return new WaitForSeconds(0.6f);
                    }
                    break;
            }
        }
    }

    /// <summary>
    /// Gambit. Knight's Tour: three leaps, each an L (two squares one way and one the other, a square = 22 px; up/down
    /// squashed to 0.75 for the floor's perspective): of the eight it takes the one that lands nearest the hero (and is
    /// clear of walls), marks that square 0.4 s, jumps (0.3 s, can't be hit) and lands in a shockwave (1.0). Passive Check:
    /// a landing that hits the hero puts him in check for 4 s (a marble knight over his head); its next slam on him while
    /// in check is checkmate: an extra 0.8 that dazes.
    /// </summary>
    public class StmGambitBrain : StmBrain
    {
        public const float Square = 22f, Flight = 0.3f, CheckTime = 4f;
        static readonly Vector2[] Moves =
        {
            new Vector2(2, 1), new Vector2(2, -1), new Vector2(-2, 1), new Vector2(-2, -1),
            new Vector2(1, 2), new Vector2(1, -2), new Vector2(-1, 2), new Vector2(-1, -2),
        };
        /// <summary>Hero in check until (Time.time) per Gambit.</summary>
        public static readonly Dictionary<GameObject, float> CheckUntil = new Dictionary<GameObject, float>();
        Vector2 m_target, m_from;
        bool m_flying;
        float m_ft;

        void OnEnable() { m_flying = false; }
        protected override void OnDisable() { base.OnDisable(); m_flying = false; if (m_player != null) m_player.AnimCollideOn(); }

        public static bool InCheck(GameObject hero)
        {
            float t;
            return hero != null && CheckUntil.TryGetValue(hero, out t) && t > Time.time;
        }

        public void StmTourMark()
        {
            if (!Alive) return;
            Vector2 me = Feet;
            var hero = LiveHero();
            Vector2 goal = hero != null ? (Vector2)hero.transform.position : me + Facing * 60f;
            float best = float.MaxValue; Vector2 pick = me;
            foreach (var mv in Moves)
            {
                var at = me + new Vector2(mv.x * Square, mv.y * Square * 0.75f);
                if (ModUtil.SafePoint(me, at, 8f) != at) continue;          // a wall in the way
                float d = (at - goal).sqrMagnitude;
                if (d < best) { best = d; pick = at; }
            }
            if (best == float.MaxValue)
            {
                // boxed in: the shortest clear part of any knight move
                foreach (var mv in Moves)
                {
                    var at = ModUtil.SafePoint(me, me + new Vector2(mv.x * Square, mv.y * Square * 0.75f), 8f);
                    float d = (at - goal).sqrMagnitude;
                    if (d < best) { best = d; pick = at; }
                }
            }
            m_target = pick;
            if (StmFx.KnightMark != null) SystemPool.Spawn(StmFx.KnightMark, m_target);
            if (m_move != null && Mathf.Abs(m_target.x - me.x) > 1f) m_move.SetDirection(new Vector2(Mathf.Sign(m_target.x - me.x), 0f));
        }

        public void StmTourJump()
        {
            if (!Alive) return;
            m_from = transform.position; m_flying = true; m_ft = 0f;
            if (StmFx.LeapDust != null) SystemPool.Spawn(StmFx.LeapDust, Feet);
        }

        public void StmTourLand()
        {
            if (m_flying) { m_flying = false; ModUtil.Teleport(gameObject, m_target - (Feet - (Vector2)transform.position)); }
            if (m_move != null) m_move.Stop();
            if (Alive && StmFx.Landing != null) FxFactory.SpawnOwned(StmFx.Landing, Feet, Own());
        }

        public void StmTourEnd() { m_flying = false; }

        void Update()
        {
            if (!m_flying) return;
            m_ft += Time.deltaTime;
            float t = Mathf.Clamp01(m_ft / Flight);
            Vector2 body = m_target - (Feet - (Vector2)transform.position);
            ModUtil.Teleport(gameObject, Vector2.Lerp(m_from, body, t));
            if (m_move != null) m_move.Stop();
            if (m_ft > Flight + 0.6f) { m_flying = false; if (m_player != null) m_player.AnimCollideOn(); }   // clip was cut short
        }

        /// <summary>Slam's hit frame: checkmate a hero in check who is in front of it.</summary>
        public void StmGambitSlam()
        {
            var hero = LiveHero();
            if (hero == null || !Alive || !InCheck(hero)) return;
            Vector2 d = (Vector2)hero.transform.position - Feet;
            if (d.magnitude > 34f || Vector2.Dot(d, Facing) < 0f) return;
            CheckUntil.Remove(hero);
            ModInd.Set(hero, StmFx.Check, false);
            if (StmFx.Checkmate != null) FxFactory.SpawnOwned(StmFx.Checkmate, hero.transform.position, Own());
        }

        void MsgOnAttackContact(DamageInfo d)
        {
            var hero = ModUtil.Hero();
            if (!Alive || d == null || hero == null || d.m_victim != hero || !From(d, "ModStmLanding")) return;
            CheckUntil[hero] = Time.time + CheckTime;
            ModInd.Set(hero, StmFx.Check, true, CheckTime);
        }
    }

    /// <summary>
    /// Caryatid. Raise Column: a crack ring under the hero (0.6 s), then a marble column bursts up (1.0, throws him off)
    /// and stands 6 s as solid stone (a statue-sized footprint that blocks the way like any statue), then crumbles. At most
    /// 2 of hers stand (the oldest crumbles). Passive Shelter: within 40 px of one of her columns she takes 0.7x damage.
    /// </summary>
    public class StmCaryatidBrain : StmBrain
    {
        public const int MaxColumns = 2;
        public const float Reach = 140f, ShelterRange = 40f, ShelterResist = 1f / 0.7f, RiseDelay = 0.75f;
        public readonly List<StmColumnFx> Columns = new List<StmColumnFx>();
        bool m_shelter;
        float m_check;

        void OnEnable() { m_shelter = false; m_check = 0f; }
        protected override void OnDisable()
        {
            base.OnDisable();
            StopAllCoroutines();
            ModInd.Set(gameObject, StmFx.Shelter, false); m_shelter = false;
            foreach (var c in Columns.ToArray()) if (c != null) c.Crumble();
            Columns.Clear();
        }

        public void StmRaiseColumn()
        {
            if (!Alive || StmFx.ColumnBurst == null) return;
            Vector2 me = Feet;
            var hero = LiveHero();
            Vector2 at = hero != null ? (Vector2)hero.transform.position : me + Facing * 60f;
            var d = at - me;
            if (d.magnitude > Reach) at = me + d.normalized * Reach;
            at = ModUtil.SafePoint(me, at, 8f);
            FxFactory.SpawnOwned(StmFx.ColumnBurst, at, Own());
            StartCoroutine(Rise(at));
        }

        IEnumerator<object> Rise(Vector2 at)
        {
            yield return new WaitForSeconds(RiseDelay);
            if (!Alive || StmFx.Column == null) yield break;
            // never raise it on anyone: shift it to the nearest free spot (or not at all)
            Vector2 spot;
            if (!StmColumnFx.FreeSpot(at, out spot)) yield break;
            at = spot;
            Columns.RemoveAll(c => c == null || !c.Standing);
            while (Columns.Count >= MaxColumns) { Columns[0].Crumble(); Columns.RemoveAt(0); }
            var go = SystemPool.Spawn(StmFx.Column, at);
            if (go == null) yield break;
            var col = go.GetComponent<StmColumnFx>() ?? go.AddComponent<StmColumnFx>();
            col.Begin(this);
            Columns.Add(col);
        }

        void Update()
        {
            m_check -= Time.deltaTime;
            if (m_check > 0f) return;
            m_check = 0.15f;
            bool on = false;
            if (Alive)
            {
                Vector2 me = Feet;
                foreach (var c in Columns)
                    if (c != null && c.Standing && ((Vector2)c.transform.position - me).sqrMagnitude < ShelterRange * ShelterRange) { on = true; break; }
            }
            if (on == m_shelter) return;
            m_shelter = on;
            Resist(on ? ShelterResist : 1f);
            ModInd.Set(gameObject, StmFx.Shelter, on);
        }
    }

    /// <summary>
    /// A standing marble column (Caryatid): a statue-sized solid footprint for 6 s, then it crumbles. It only turns solid
    /// when no living player stands on its footprint (checked every frame until then); if someone is still there after
    /// 1 s it crumbles instead, so nobody (Iron Boots, invincible, walking back on) can ever be shut inside it.
    /// </summary>
    public class StmColumnFx : MonoBehaviour
    {
        public const float Life = 6f, ClearX = 9f, ClearY = 7f, SolidWait = 1f;
        public bool Standing { get; private set; }
        bool m_solid;

        /// <summary>Is a living player on (or within about 8 px of) a column footprint at p?</summary>
        public static bool Occupied(Vector2 p)
        {
            var players = SystemPlayers.GetActivePlayers();
            if (players == null) return false;
            foreach (var pd in players)
            {
                var go = pd != null ? pd.GameObject : null;
                if (go == null || !go.activeInHierarchy) continue;
                var h = go.GetComponent<Health>();
                if (h != null && !h.IsAlive()) continue;
                var d = (Vector2)go.transform.position - p;
                if (Mathf.Abs(d.x) < ClearX && Mathf.Abs(d.y) < ClearY) return true;
            }
            return false;
        }

        /// <summary>at itself if free, else the nearest free point 14 or 22 px away with no wall between; false if none.</summary>
        public static bool FreeSpot(Vector2 at, out Vector2 spot)
        {
            spot = at;
            if (!Occupied(at)) return true;
            float best = float.MaxValue;
            foreach (var r in new[] { 14f, 22f })
                for (int k = 0; k < 8; k++)
                {
                    float a = k * 45f * Mathf.Deg2Rad;
                    var c = at + new Vector2(Mathf.Cos(a) * r, Mathf.Sin(a) * r * 0.75f);
                    if (ModUtil.SafePoint(at, c, 6f) != c || Occupied(c)) continue;
                    float d = (c - at).sqrMagnitude;
                    if (d < best) { best = d; spot = c; }
                }
            return best < float.MaxValue;
        }
        StmCaryatidBrain m_owner;
        float m_t;
        GameObject m_body;
        exSpriteAnimation m_anim;

        public void Begin(StmCaryatidBrain owner)
        {
            m_owner = owner; m_t = 0f; Standing = true;
            m_anim = GetComponent<exSpriteAnimation>();
            if (m_anim != null && StmFx.ColumnStand != null) m_anim.Play(StmFx.ColumnStand);
            m_solid = false;
            if (m_body == null)
            {
                // the same footprint as a MonsterStatue's Body: WallBase, non-trigger, 12 x 6 at the foot
                m_body = new GameObject("Body");
                m_body.layer = 24;
                m_body.transform.SetParent(transform, false);
                m_body.transform.localPosition = new Vector3(0f, 2.5f, 5f);
                var bc = m_body.AddComponent<BoxCollider>();
                bc.size = new Vector3(12f, 6f, 150f);
            }
            m_body.SetActive(false);              // solid once its footprint is clear (Update)
        }

        public void Crumble()
        {
            if (!Standing) return;
            Standing = false; m_t = 0f;
            if (m_body != null) m_body.SetActive(false);
            if (m_anim != null && StmFx.ColumnCrumble != null) m_anim.Play(StmFx.ColumnCrumble);
        }

        void Update()
        {
            m_t += Time.deltaTime;
            if (Standing)
            {
                if (m_t > Life || m_owner == null || !m_owner.isActiveAndEnabled) { Crumble(); return; }
                if (!m_solid)
                {
                    if (!Occupied(transform.position)) { m_solid = true; if (m_body != null) m_body.SetActive(true); }
                    else if (m_t > SolidWait) Crumble();
                }
                return;
            }
            if (m_t > 0.6f) SystemPool.Despawn(gameObject);
        }

        void OnDisable() { Standing = false; m_solid = false; if (m_body != null) m_body.SetActive(false); }
    }

    /// <summary>
    /// Lachrymosa (legendary). Passive: Seen (the hero is within 240 px, nothing walls her off, and he faces her within 55
    /// degrees) she is stone - grey, 0.55x speed, 0.6x damage taken, an open stone eye over her. Unseen: 1.4x speed and her
    /// hits deal 1.3x, tear-light round her hem. Special Lights Out: she pinches out her halo and the room goes dark for
    /// 2.5 s (LightsOut); in the dark nobody can watch her: she moves at 1.0x, takes and deals normal damage, and neither
    /// mark shows (the darkness is the sign). She arrives in a crack of gold light.
    /// </summary>
    public class StmLachBrain : StmBrain
    {
        public const float SeeRange = 240f, SeeCos = 0.5736f, SeenSpeed = 0.55f, UnseenSpeed = 1.4f, SeenResist = 1f / 0.6f,
                           UnseenDamage = 1.3f;
        public static readonly Color StoneTint = new Color(0.62f, 0.64f, 0.70f, 1f);
        public bool IsSeen { get; private set; }
        int m_state = -1;          // -1 none (dead), 0 unseen, 1 seen, 3 dark
        float m_check;

        void OnEnable()
        {
            m_state = -1; m_check = 0f; IsSeen = false;
            if (StmFx.Arrival != null && Time.timeSinceLevelLoad > 0.5f) SystemPool.Spawn(StmFx.Arrival, Feet);
        }
        protected override void OnDisable()
        {
            base.OnDisable();
            if (m_move != null) m_move.ResetSpeedMultiplier();
            if (m_sprite != null) m_sprite.color = Color.white;
            ModInd.Set(gameObject, StmFx.Seen, false); ModInd.Set(gameObject, StmFx.Unseen, false);
            m_state = -1;
        }

        public static bool HeroSees(Vector2 at)
        {
            var hero = ModUtil.Hero();
            var hh = hero != null ? hero.GetComponent<Health>() : null;
            if (hh == null || !hh.IsAlive()) return false;
            Vector2 hp = hero.transform.position;
            var d = at - hp;
            if (d.sqrMagnitude > SeeRange * SeeRange) return false;
            if (d.sqrMagnitude < 1f) return true;
            var mv = hero.GetComponent<PlayerMovement>();
            var face = mv != null ? R.Get<Vector2>(mv, "m_faceDirection") : Vector2.right;
            if (face.sqrMagnitude < 0.01f) return false;
            if (Vector2.Dot(face.normalized, d.normalized) < SeeCos) return false;
            return ModUtil.Clear(hp + new Vector2(0f, 8f), at + new Vector2(0f, 8f));
        }

        void Update()
        {
            if (!Alive) { Apply(-1); return; }
            if (LightsOut.Active) { Apply(3); return; }
            m_check -= Time.deltaTime;
            if (m_check > 0f && m_state >= 0 && m_state != 3) { Tint(); return; }
            m_check = 0.1f;
            Apply(HeroSees(Feet + new Vector2(0f, 10f)) ? 1 : 0);
        }

        void Tint()
        {
            if (m_sprite == null) return;
            var asc = GetComponent<SilverAscended>();
            if (asc != null && asc.On) return;          // the silver sheen owns the colour then
            var want = m_state == 1 ? StoneTint : Color.white;
            if (m_sprite.color != want) m_sprite.color = want;
        }

        void Apply(int state)
        {
            if (state == m_state) { Tint(); return; }
            m_state = state;
            IsSeen = state == 1;
            if (m_move != null)
            {
                if (state < 0 || state == 3) m_move.ResetSpeedMultiplier();
                else m_move.SetSpeedMultiplier(state == 1 ? SeenSpeed : UnseenSpeed);
            }
            Resist(state == 1 ? SeenResist : 1f);
            ModInd.Set(gameObject, StmFx.Seen, state == 1);
            ModInd.Set(gameObject, StmFx.Unseen, state == 0);
            if (state < 0 && m_sprite != null) m_sprite.color = Color.white;
            Tint();
        }

        /// <summary>Unseen (and not in the dark), her hits land harder (Patch_StatueDamage asks).</summary>
        public bool Unseen { get { return m_state == 0; } }

        public void StmLightsOut()
        {
            if (!Alive) return;
            if (StmFx.Snuff != null) SystemPool.Spawn(StmFx.Snuff, Feet);
            LightsOut.Begin(gameObject);
        }
    }

    /// <summary>
    /// LIGHTS OUT (Lachrymosa's special): the room goes dark for 2.5 s. One overlay for everyone (never stacks: a second
    /// cast while dark only extends it to 2.5 s from then): a quad of soft darkness in front of the level camera's world
    /// (it draws after every world sprite, before the GUI camera), 62 percent black, with a small light pool round every
    /// living player except Lachrymosa (the hero, monsters and ghosts stay readable; everything else, hazards and shots
    /// included, is dimmed but still visible). Timeline: a flicker in (0.36 s: dark, light, dark), hold, a flicker out and
    /// a snap back to full light. The dark cue sounds on the cast. The lighting is never changed - the overlay is only
    /// hidden - and it is hidden at once if every caster is dead or gone, the hero dies, the room changes, the game
    /// pauses, or the level camera goes away.
    /// </summary>
    public static class LightsOut
    {
        public const float Duration = 2.5f, Dim = 0.62f, PoolIn = 14f, PoolOut = 32f, FlickerIn = 0.36f, FlickerOut = 0.2f;
        static LightsOutFx s_fx;
        static GameObject s_cue;
        static bool s_cueLooked;

        /// <summary>The vanilla dark-portal sound as the hero's audio cue (null if the game has none by that name).</summary>
        public static GameObject Cue
        {
            get
            {
                if (!s_cueLooked) { s_cueLooked = true; s_cue = Kit.SoundGO("SoundPortalDarkSpawn") ?? Kit.SoundGO("SoundGhostGirlDarkLightning"); }
                return s_cue;
            }
        }

        public static bool Active { get { return s_fx != null && s_fx.Dark; } }
        /// <summary>The overlay's current darkness (0 none .. Dim), for tests.</summary>
        public static float Level { get { return s_fx != null ? s_fx.Alpha : 0f; } }

        public static void Begin(GameObject caster)
        {
            try
            {
                var cam = SystemMain.GetCameraMain();
                if (cam == null) return;
                if (s_fx == null || s_fx.Cam != cam)
                {
                    if (s_fx != null) UnityEngine.Object.Destroy(s_fx.gameObject);
                    var go = new GameObject("ModStmLightsOut");
                    s_fx = go.AddComponent<LightsOutFx>();
                    if (!s_fx.Init(cam)) { UnityEngine.Object.Destroy(go); s_fx = null; return; }
                }
                s_fx.Begin(caster);
            }
            catch (Exception e) { Plugin.Log.LogError("Lights Out: " + e); }
        }

        /// <summary>Restore full light now (death, room change, pause...).</summary>
        public static void End() { if (s_fx != null) s_fx.Stop(); }

        /// <summary>Darkness of a texel: Dim times (1 - light), the light being the strongest pool round a player.</summary>
        public static float Shade(Vector2 world, List<Vector2> pools)
        {
            float light = 0f;
            for (int i = 0; i < pools.Count; i++)
            {
                var d = world - pools[i];
                float r = Mathf.Sqrt(d.x * d.x + d.y * d.y * 1.6f);
                float l = 1f - Mathf.Clamp01((r - PoolIn) / (PoolOut - PoolIn));
                if (l > light) light = l * l * (3f - 2f * l);
            }
            return 1f - light;
        }

        /// <summary>Overlay strength at time t into the effect: flicker in, hold, flicker out (1 = full Dim).</summary>
        public static float Curve(float t, float total)
        {
            if (t < 0f || t >= total) return 0f;
            if (t < FlickerIn)
            {
                float k = t / FlickerIn;
                return k < 0.25f ? 1f : k < 0.45f ? 0.15f : k < 0.6f ? 1f : k < 0.72f ? 0.45f : 1f;
            }
            float left = total - t;
            if (left < FlickerOut) { float k = left / FlickerOut; return k > 0.6f ? 0.35f : k > 0.3f ? 1f : 0.2f; }
            return 1f;
        }
    }

    public class LightsOutFx : MonoBehaviour
    {
        const int TW = 64, TH = 36;
        public Camera Cam { get; private set; }
        public bool Dark { get; private set; }
        public float Alpha { get; private set; }
        readonly List<GameObject> m_casters = new List<GameObject>();
        readonly List<Vector2> m_pools = new List<Vector2>();
        Texture2D m_tex;
        Color32[] m_buf;
        MeshRenderer m_mr;
        Material m_mat;
        float m_t, m_total;
        Room m_room;

        public bool Init(Camera cam)
        {
            Cam = cam;
            transform.SetParent(cam.transform, false);
            m_tex = new Texture2D(TW, TH, TextureFormat.ARGB32, false);
            m_tex.filterMode = FilterMode.Bilinear;
            m_tex.wrapMode = TextureWrapMode.Clamp;
            m_buf = new Color32[TW * TH];
            var sh = Shader.Find("Sprites/Default");
            if (sh != null) m_mat = new Material(sh);
            else if (SpriteSheets.TemplateMaterial != null) m_mat = new Material(SpriteSheets.TemplateMaterial);
            if (m_mat == null) { Plugin.Log.LogWarning("Lights Out: no shader for the dark overlay"); return false; }
            m_mat.mainTexture = m_tex;
            m_mat.renderQueue = 4000;
            var mesh = new Mesh();
            mesh.vertices = new[] { new Vector3(-0.5f, -0.5f, 0f), new Vector3(0.5f, -0.5f, 0f), new Vector3(0.5f, 0.5f, 0f), new Vector3(-0.5f, 0.5f, 0f) };
            mesh.uv = new[] { new Vector2(0f, 0f), new Vector2(1f, 0f), new Vector2(1f, 1f), new Vector2(0f, 1f) };
            mesh.colors = new[] { Color.white, Color.white, Color.white, Color.white };
            mesh.triangles = new[] { 0, 2, 1, 0, 3, 2 };
            gameObject.AddComponent<MeshFilter>().sharedMesh = mesh;
            m_mr = gameObject.AddComponent<MeshRenderer>();
            m_mr.sharedMaterial = m_mat;
            m_mr.enabled = false;
            // a layer the level camera draws
            int layer = 0, mask = cam.cullingMask;
            if ((mask & 1) == 0) for (int l = 0; l < 32; l++) if ((mask & (1 << l)) != 0) { layer = l; break; }
            gameObject.layer = layer;
            return true;
        }

        public void Begin(GameObject caster)
        {
            m_casters.RemoveAll(c => c == null);
            if (caster != null && !m_casters.Contains(caster)) m_casters.Add(caster);
            if (!Dark)
            {
                Dark = true; m_t = 0f; m_total = LightsOut.Duration;
                m_room = SystemLevel.GetCurrentRoom();
            }
            else m_total = Mathf.Max(m_total, m_t + LightsOut.Duration);     // never stacks: only lasts longer
        }

        public void Stop()
        {
            Dark = false; Alpha = 0f; m_t = 0f;
            m_casters.Clear();
            if (m_mr != null) m_mr.enabled = false;
        }

        bool ShouldEnd()
        {
            if (SystemTime.Paused) return true;
            if (Cam == null || !Cam.isActiveAndEnabled) return true;
            var hero = ModUtil.Hero();
            var hh = hero != null ? hero.GetComponent<Health>() : null;
            if (hh == null || !hh.IsAlive()) return true;
            if (SystemLevel.GetCurrentRoom() != m_room) return true;
            bool any = false;
            foreach (var c in m_casters)
            {
                if (c == null || !c.activeInHierarchy) continue;
                var h = c.GetComponent<Health>();
                if (h != null && h.IsAlive()) { any = true; break; }
            }
            return !any;
        }

        void LateUpdate()
        {
            if (!Dark) { if (m_mr != null && m_mr.enabled) m_mr.enabled = false; return; }
            if (ShouldEnd()) { Stop(); return; }
            m_t += Time.deltaTime;
            if (m_t >= m_total) { Stop(); return; }
            Alpha = LightsOut.Dim * LightsOut.Curve(m_t, m_total);
            // cover the camera's view, just in front of its near plane
            float h = Cam.orthographicSize * 2f * 1.04f, w = h * Cam.aspect;
            transform.localPosition = new Vector3(0f, 0f, Cam.nearClipPlane + 0.05f);
            transform.localRotation = Quaternion.identity;
            transform.localScale = new Vector3(w, h, 1f);
            // light pools round every living player except a Lachrymosa
            m_pools.Clear();
            var players = SystemPlayers.GetActivePlayers();
            if (players != null)
                foreach (var pd in players)
                {
                    var go = pd != null ? pd.GameObject : null;
                    if (go == null || !go.activeInHierarchy || go.GetComponent<StmLachBrain>() != null) continue;
                    var hl = go.GetComponent<Health>();
                    if (hl != null && !hl.IsAlive()) continue;
                    m_pools.Add((Vector2)go.transform.position + new Vector2(0f, 9f));
                }
            Vector2 c0 = Cam.transform.position;
            for (int y = 0; y < TH; y++)
            {
                float wy = c0.y + ((y + 0.5f) / TH - 0.5f) * h;
                for (int x = 0; x < TW; x++)
                {
                    float wx = c0.x + ((x + 0.5f) / TW - 0.5f) * w;
                    float a = Alpha * LightsOut.Shade(new Vector2(wx, wy), m_pools);
                    m_buf[y * TW + x] = new Color32(4, 3, 8, (byte)Mathf.RoundToInt(a * 255f));
                }
            }
            m_tex.SetPixels32(m_buf);
            m_tex.Apply(false);
            // online (Crawl Online): clients mirror this quad but only see the texture as first sent; push the new
            // picture about 12 times a second (a 64x36 PNG, a few KB). The texture stays unnamed on purpose, so a client
            // never matches a stale local copy by name and always asks the host.
            CompatOnline.TextureChanged(m_tex, 0.08f);
            if (!m_mr.enabled) m_mr.enabled = true;
        }

        void OnDisable() { Dark = false; Alpha = 0f; if (m_mr != null) m_mr.enabled = false; }
        void OnDestroy() { if (m_tex != null) Destroy(m_tex); if (m_mat != null) Destroy(m_mat); }
    }

    /// <summary>An unseen Lachrymosa's hits deal 1.3x (a multiplier: order against other multipliers does not matter).</summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_StatueDamageOut
    {
        static void Prefix(Health __instance, DamageInfo damage)
        {
            try
            {
                if (damage == null || damage.m_source == null || damage.m_isDamageFromStatus) return;
                var att = damage.m_source.m_sourceOwnerPlayer;
                if (att == null || att == __instance.gameObject) return;
                var l = att.GetComponent<StmLachBrain>();
                if (l != null && l.isActiveAndEnabled && l.Unseen) damage.m_amount *= StmLachBrain.UnseenDamage;
            }
            catch (Exception e) { Plugin.Log.LogError("Secret statue damage out: " + e.Message); }
        }
    }

    /// <summary>
    /// The Grotesque's stone and its crumble. Runs LAST among the Health.Damage prefixes (VeryLow) so every other mod
    /// multiplier (Whetstone, Wanted Poster, Taxed...) has already been applied, and does nothing if an earlier prefix
    /// already cancelled the hit. Nothing hurts it while petrified or crumbled (a hit on the stone is stored instead). The
    /// lethal test repeats Health.Damage's own maths (invincibility, CanDamage, the source's damage mod, the friendly-fire
    /// multiplier, resistance, vulnerability, the per-hit cap), so a hit that would kill it crumbles it instead.
    /// </summary>
    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_StatueDamageIn
    {
        static readonly System.Reflection.FieldInfo s_invuln = AccessTools.Field(typeof(Health), "m_invincibilityList");

        [HarmonyPriority(Priority.VeryLow)]
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            try
            {
                if (damage == null || damage.m_source == null) return true;
                var victim = __instance.gameObject;
                var g = victim.GetComponent<StmGrotesqueBrain>();
                if (g == null || !g.isActiveAndEnabled) return true;
                if (g.Stone || g.Rubble)
                {
                    if (g.Stone && damage.m_amount > 0f && !damage.m_isDamageFromStatus && damage.m_source.m_sourceOwnerPlayer != victim)
                        g.Store((Vector2)victim.transform.position + new Vector2(0f, 10f));
                    __result = false;
                    return false;
                }
                if (!g.CanReform || damage.m_amount <= 0f || !__instance.IsAlive()) return true;
                // would this hit kill it? (Health.Damage's own maths, in its order)
                var inv = s_invuln != null ? s_invuln.GetValue(__instance) : null;
                if (inv != null)
                {
                    var empty = inv.GetType().GetMethod("Empty");
                    if (empty != null && !(bool)empty.Invoke(inv, null)) return true;          // invincible: the original refuses it
                }
                if (!__instance.CanDamage(damage.m_source, hitFriendly)) return true;   // public: no reflection (a name-only lookup was ambiguous: 3 overloads)
                float amt = damage.m_amount;
                if (damage.m_source.m_damageMod != null) amt = damage.m_source.m_damageMod.Modify(amt);
                var hero = SystemPlayers.GetHeroPlayerData() != null ? SystemPlayers.GetHeroPlayerData().GameObject : null;
                if (hero != damage.m_source.m_sourceOwnerPlayer && hero != victim) amt *= SystemBalance.FriendlyDamageMultiplier;
                amt /= Mathf.Max(0.0001f, R.Get<float>(__instance, "m_damageResistanceFinal"));
                if (R.Get<bool>(__instance, "m_vulnerable")) amt *= R.Get<float>(__instance, "m_vulnerableDamageMult");
                float cap = R.Get<float>(__instance, "m_maxDamagePerHit");
                if (cap > 0f) amt = Mathf.Min(amt, cap);
                if (amt <= 0f) return true;
                if (R.Get<float>(__instance, "m_healthCurrent") - amt <= 0.0001f && g.TryCrumble()) { __result = false; return false; }
            }
            catch (Exception e) { Plugin.Log.LogError("Secret statue damage in: " + e.Message); }
            return true;
        }
    }

    /// <summary>Give the secret statue monsters their brain on every instance.</summary>
    [HarmonyPatch(typeof(Player), "Awake")]
    static class Patch_StatueAwake
    {
        static void Postfix(Player __instance)
        {
            if (__instance == null) return;
            var go = __instance.gameObject;
            switch (ModUtil.PrefabName(go))
            {
                case SecretStatues.Grotesque: if (go.GetComponent<StmGrotesqueBrain>() == null) go.AddComponent<StmGrotesqueBrain>(); break;
                case SecretStatues.Sixfold: if (go.GetComponent<StmIdolBrain>() == null) go.AddComponent<StmIdolBrain>(); break;
                case SecretStatues.Gambit: if (go.GetComponent<StmGambitBrain>() == null) go.AddComponent<StmGambitBrain>(); break;
                case SecretStatues.Caryatid: if (go.GetComponent<StmCaryatidBrain>() == null) go.AddComponent<StmCaryatidBrain>(); break;
                case SecretStatues.Lachrymosa: if (go.GetComponent<StmLachBrain>() == null) go.AddComponent<StmLachBrain>(); break;
            }
        }
    }
}
