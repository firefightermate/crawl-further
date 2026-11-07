using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;

    /// <summary>
    /// Zhekra's effect templates, statuses and indicators. Threads that run through the pack:
    ///  - Acid ("Corroded"): the victim takes 20% more damage for 3 s (refreshes, never stacks).
    ///  - Resin: sticky amber that roots (the mod's 0.8 s root, with diminishing returns).
    ///  - The swarm: a Zhekra monster with any other monster within 64 px moves 15% faster and hits 10% harder.
    ///  - Mark: a Marked hero draws the brood (Zhekra within 80 px of him swarm) and leaves a scent trail.
    /// Art origins (the Strike.ArtAt pixels) are listed in art/out_zhekra/TIMING.md.
    /// </summary>
    public static class ZhekraFx
    {
        public static Status Acid, Swarm, Frenzy, Mark, Implant, Trail, Root, Slow, Daze, Bleed;
        public static StatusOverlayDef JellyGlow;
        public static StatusOverlayDef[] Eggs;

        // tier 1 and the larva
        public static GameObject AcidSpit, GrubBite, LarvaBite, Stinger, DroneDive, DroneDiveLast, BeetleSnap, ResinGlob, Resin,
                                 ResinPop, Skid, Splash, LarvaHatch, LarvaEgg, LarvaFree, GrublingSpawner;
        // tier 2
        public static GameObject AcidGlob, AcidGlobWide, AcidPool, AcidPoolWide, SacBurst, Scythe, GuardStrike, HornetStinger,
                                 MarkDart, Prints, Stab, FeedStab, Mend, GlueSpeck, SealFx, Plate, Butt, HurlLand;
        public static GameObject[] RollBall = new GameObject[4];
        // tier 3
        public static GameObject AcidRain, Pheromone, JellyBead, Droplet, ZipHit, Mist, Reap, ScissorHit, ReflexCut, Reach,
                                 Clamp, Pit, SandFlick, FlickHit, Dirt, Slam, SwarmCloud, Drip, Lance, CarryShadow, Drill,
                                 PumpBead, Ram, EggDart, ImplantBurst, Gore, BullHit, GlueShell, GlueField, Spot, Pinch,
                                 StagButt, TossLand, Shove, CrackEmpty, CrackBrood;
        public static GameObject[] Bubble = new GameObject[3];
        public static GameObject[] FossilBall = new GameObject[4];

        // ------------------------------------------------------------------ statuses
        static Status MakeStatus(string name, string cls, float duration, Color tint, params PlayerModifier[] mods)
        {
            var src = ModStatus.Slow;      // the mod's timed status: no anims, no damage, never blocks attacks
            if (src == null) { Plugin.Log.LogWarning("Zhekra: no base status for " + name); return null; }
            var go = MonsterFactory.ClonePrefab(src.gameObject, name);
            var s = go.GetComponent<Status>();
            s.m_class = cls;
            s.m_duration = duration;
            s.m_stacks = true;             // re-applying refreshes the timer (same source), the effect never stacks
            s.m_damage = 0f;
            s.m_preventAttack = false;
            s.m_preventMove = false;
            s.m_modifiers = new List<PlayerModifier>(mods);
            s.m_tintColour = tint;
            s.m_tintFlashTime = 0f;
            s.m_effects = new DamageEffectData[0];
            return s;
        }

        static PlayerModifier Mul(PlayerModifier.eType t, float v)
        {
            return new PlayerModifier { m_modify = t, m_type = ValueModifier.eModifierType.Multiply, m_value = v, m_priority = 500f };
        }

        static GameObject Melee(string name, float damage, float knock, float w, float h, Status status = null, float chance = 1f)
        {
            var go = AimedMelee.Rotating(FxFactory.Clone("DamageGiantRatAttack", name));
            FxFactory.SetDamage(go, damage, knockback: knock, status: status, statusChance: chance);
            Strike.HitBox(go, w, h);
            return go;
        }

        static GameObject Body(string name, float damage, float rate, float knock, float life, float w, float h, Status status = null,
                               float chance = 1f, bool aimed = true)
        {
            var go = FxKit.BodyHit(name, damage, rate, knock, life, status, chance);
            if (aimed) go = AimedMelee.Rotating(go);
            Strike.HitBox(go, w, h);
            return go;
        }

        static GameObject Vis(string name, string sheet, string anim, int gx, int gy, bool loop = false, float life = 0f)
        {
            var go = FxKit.Visual(name, sheet, anim, loop, life);
            if (go != null) Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        static GameObject Dart(string name, string sheet, string anim, int gx, int gy, float speed, float life, float damage, float knock,
                               Status status = null, float chance = 1f, bool rotate = true, string vanilla = "DFX_skelMageNewProjectile")
        {
            var go = FxKit.Projectile(name, vanilla, sheet, anim, speed, life, damage, knock, status, chance, rotate: rotate);
            if (go != null) Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        /// <summary>A floor puddle that roots or slows whoever stands in it (a reskinned lava zone, so it lives as long as its art).</summary>
        static GameObject Zone(string name, string sheet, int gx, int gy, float w, float h, Status status, bool resin)
        {
            var go = FxFactory.Clone("LavaEffectLongerReworkZone", name);
            if (go == null) return null;
            var sh = SpriteSheets.Get(sheet);
            var clip = new ClipBuilder(sh, "Life", name + "Life").Once().Ev(1, "AnimDamageOn").Ev(-3, "AnimDamageOff").Build();
            FxFactory.Reskin(go, clip, sh);
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, snap: 1f);
            FxFactory.SetStatusZone(go, status, hitsHero: true, hitsMonster: false);
            Strike.Ground(go, sheet, gx, gy, w, h);
            FxKit.NoTint(go);
            if (resin) FxFactory.OnSpawn[go] = i => { if (i.GetComponent<ZhkResinFx>() == null) i.AddComponent<ZhkResinFx>(); };
            return go;
        }

        static GameObject Pool(string name, string sheet, int gx, int gy, float w, float h)
        {
            var go = FxKit.TimedHit(name, "SkMageSlimeEffect", sheet, "Life", 2, 15, 0.25f, 0.02f, Acid, 1f, rate: 0.6f, canFlip: false);
            Strike.Ground(go, sheet, gx, gy, w, h);
            return go;
        }

        static GameObject Lob(string name, string sheet, int gx, int gy, float speed, float life, float damage, GameObject spawn)
        {
            var go = FxKit.Projectile(name, "webBall", sheet, "Fly", speed, life, damage, 0.4f, Acid, 1f, accel: 20f, speedMax: 8f, rotate: false);
            if (go == null) return null;
            FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: life, spawnOnDestroy: spawn, freeRotate: false);
            FxFactory.SetContacts(go, destroyOnHit: true, spawnOnHit: spawn);
            Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        /// <summary>A shell that drops from the sky: the ring blooms while it falls, it lands on frame 4.</summary>
        static GameObject Drop(string name, string sheet, int gx, int gy, float damage, Status status, GameObject leave)
        {
            var go = FxKit.TimedHit(name, "skydropExplode", sheet, "Play", 4, 5, damage, 0.6f, status, 1f, canFlip: false);
            if (go == null) return null;
            Strike.Ground(go, sheet, gx, gy, 18f, 8f);
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, spawnOnDestroy: leave, canFlip: false, freeRotate: false);
            return go;
        }

        public static void Build()
        {
            Root = FxFactory.GetStatus("StatusStuckToFloor");
            Slow = FxFactory.GetStatus("StatusLavaSteveGoo");
            Daze = FxFactory.GetStatus("StatusDizzy");
            Bleed = FxFactory.GetStatus("StatusBleeding");
            Acid = MakeStatus("ModStatusZhkAcid", "ModZhkAcid", 3f, new Color(0.55f, 1f, 0.2f, 0.22f),
                              Mul(PlayerModifier.eType.HeroDamageResistance, 0.83f), Mul(PlayerModifier.eType.MonsterDamageResistance, 0.83f));
            Swarm = MakeStatus("ModStatusZhkSwarm", "ModZhkSwarm", 0.6f, Color.black,
                               Mul(PlayerModifier.eType.MonsterSpeed, 1.15f), Mul(PlayerModifier.eType.MonsterDamage, 1.1f));
            Frenzy = MakeStatus("ModStatusZhkFrenzy", "ModZhkFrenzy", 4f, new Color(1f, 0.7f, 0.15f, 0.15f),
                                Mul(PlayerModifier.eType.MonsterSpeed, 1.2f), Mul(PlayerModifier.eType.MonsterAttackCooldown, 0.8f));
            Mark = MakeStatus("ModStatusZhkMark", "ModZhkMark", 4f, new Color(1f, 0.75f, 0.2f, 0.2f));
            Implant = MakeStatus("ModStatusZhkImplant", "ModZhkImplant", 4f, new Color(0.9f, 0.85f, 0.7f, 0.18f));
            Trail = MakeStatus("ModStatusZhkTrail", "ModZhkTrail", 0.4f, Color.black, Mul(PlayerModifier.eType.MonsterSpeed, 1.3f));

            ModStatus.RegisterOverlay("ModStatusZhkAcid", "FxZhkAcidMark", "Loop", 1f, OverlayAt.Head);
            ModStatus.RegisterOverlay("ModStatusZhkFrenzy", "FxZhkFrenzy", "Loop", -3.5f, OverlayAt.Feet);
            ModStatus.RegisterOverlay("ModStatusZhkSwarm", "FxZhkSwarm", "Loop", 1f, OverlayAt.Head);
            ModStatus.RegisterOverlay("ModStatusZhkMark", "FxZhkMark", "Loop", 1f, OverlayAt.Head);
            JellyGlow = ModStatus.Indicator("ModIndZhkJelly", "FxZhkJellyGlow", "Loop", -2f, OverlayAt.Feet);
            Eggs = new[]
            {
                ModStatus.Indicator("ModIndZhkEggs1", "FxZhkImplantLumps", "L1", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndZhkEggs2", "FxZhkImplantLumps", "L2", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModIndZhkEggs3", "FxZhkImplantLumps", "L3", 1f, OverlayAt.Head),
            };

            BuildCommon();
            BuildTier2();
            BuildTier3();
            Plugin.Log.LogInfo("Zhekra FX templates built");
        }

        static void BuildCommon()
        {
            Splash = Vis("ModZhkSplash", "FxZhkSplash", "Play", 15, 10);
            ResinPop = Vis("ModZhkResinPop", "FxZhkResinBurst", "Play", 16, 8);
            Skid = Vis("ModZhkSkid", "FxZhkSkid", "Play", 12, 7);
            Mend = Vis("ModZhkMend", "FxZhkMend", "Play", 8, 23);
            Plate = FxKit.Visual("ModZhkPlate", "FxZhkPlate", "Play", loop: true);
            if (Plate != null) { Strike.ArtAt(Plate, "FxZhkPlate", 16, 15); FxFactory.SetEffect(Plate, destroyOnAnimEnd: false, canFlip: true, freeRotate: false); }

            AcidSpit = Dart("ModZhkAcidSpit", "FxZhkAcidSpit", "Fly", 12, 4, 170f, 0.7f, 0.6f, 0.3f, Acid, 1f);
            if (AcidSpit != null) FxFactory.SetContacts(AcidSpit, destroyOnHit: true, spawnOnHit: Splash);
            GrubBite = Melee("ModZhkGrubBite", 0.8f, 0.5f, 12f, 12f, Acid, 0.35f);
            LarvaBite = Melee("ModZhkLarvaBite", 0.4f, 0.2f, 8f, 8f);
            Stinger = Dart("ModZhkStinger", "FxZhkStinger", "Fly", 13, 3, 230f, 0.6f, 0.6f, 0.3f, Acid, 0.35f);
            DroneDive = Body("ModZhkDroneDive", 0.8f, 0f, 0.6f, 0.35f, 14f, 14f, Acid, 1f);
            DroneDiveLast = Body("ModZhkDroneDiveLast", 1.6f, 0f, 1.0f, 0.35f, 16f, 16f, Acid, 1f);
            BeetleSnap = Melee("ModZhkBeetleSnap", 0.8f, 0.3f, 12f, 12f);

            Resin = Zone("ModZhkResin", "FxZhkResin", 13, 6, 22f, 10f, Root, true);
            ResinGlob = Lob("ModZhkResinGlob", "FxZhkResinGlob", 9, 10, 150f, 0.75f, 0.5f, Resin);
            if (ResinGlob != null) FxFactory.SetDamage(ResinGlob, 0.5f, knockback: 0.2f, status: Root, statusChance: 1f, collisionAtStart: true);
        }

        static void BuildTier2()
        {
            // Acid Spitter: the lobbed glob (a pool where it bursts), the full sac's wide pool, the sac bursting on itself
            AcidPool = Pool("ModZhkAcidPool", "FxZhkAcidPool", 13, 6, 22f, 10f);
            AcidPoolWide = Pool("ModZhkAcidPoolWide", "FxZhkAcidPoolWide", 24, 9, 44f, 16f);
            AcidGlob = Lob("ModZhkAcidGlob", "FxZhkAcidGlob", 14, 22, 150f, 0.85f, 1f, AcidPool);
            AcidGlobWide = Lob("ModZhkAcidGlobWide", "FxZhkAcidGlob", 14, 22, 150f, 0.85f, 1f, AcidPoolWide);
            SacBurst = FxKit.TimedHit("ModZhkSacBurst", "skydropExplode", "FxZhkSacBurst", "Play", 0, 3, 0.3f, 0.5f, Acid, 1f, canFlip: false);
            Strike.Ground(SacBurst, "FxZhkSacBurst", 22, 17, 40f, 24f);
            // Hive Soldier: two sweeps, and the 0.1 s ambush strike that roots
            Scythe = Body("ModZhkScythe", 0.9f, 0f, 0.7f, 0.15f, 20f, 18f);
            GuardStrike = Body("ModZhkGuardStrike", 1.2f, 0f, 0.8f, 0.15f, 26f, 22f, Root, 1f);
            // Hive Hornet: a fan of stingers and the Mark dart; the prints a Marked hero leaves
            HornetStinger = Dart("ModZhkHornetStinger", "FxZhkHornetStinger", "Fly", 13, 3, 240f, 0.6f, 0.8f, 0.25f, Acid, 0.35f);
            MarkDart = Dart("ModZhkMarkDart", "FxZhkMarkDart", "Fly", 14, 3, 210f, 0.8f, 0.4f, 0.2f, Mark, 1f);
            Prints = Vis("ModZhkPrints", "FxZhkPrints", "Life", 4, 3);
            if (Prints != null) FxFactory.OnSpawn[Prints] = i => { if (i.GetComponent<ZhkPrintFx>() == null) i.AddComponent<ZhkPrintFx>(); };
            // Blood Siphon: the needle stab and the three feeding stabs
            Stab = Melee("ModZhkStab", 0.9f, 0.5f, 12f, 10f);
            FeedStab = Body("ModZhkFeedStab", 0.5f, 0f, 0.1f, 0.12f, 14f, 14f, aimed: false);
            // Nasute: glue specks (each may root); Shore Up's plates
            GlueSpeck = Dart("ModZhkGlueSpeck", "FxZhkGlueJet", "Fly", 9, 3, 240f, 0.35f, 0.5f, 0.2f, Root, 0.3f);
            SealFx = Vis("ModZhkSealFx", "FxZhkSeal", "Play", 10, 14);
            // Amber Scarab: the ball by size (the biggest roots), the hurled ball, the headbutt with no ball
            for (int s = 1; s <= 3; s++)
            {
                var b = Dart("ModZhkRollBall" + s, "FxZhkRollBall", "Fly" + s, 13, 12, 160f, 1.4f, 0.6f + 0.2f * s, 0.6f + 0.2f * s,
                             s == 3 ? Root : null, 1f, rotate: false);
                if (b != null)
                {
                    FxFactory.SetEffect(b, destroyOnAnimEnd: false, destroyAfter: 1.4f, spawnOnDestroy: Resin, freeRotate: false);
                    FxFactory.SetContacts(b, destroyOnHit: true, spawnOnHit: Resin);
                }
                RollBall[s] = b;
            }
            HurlLand = Drop("ModZhkHurlLand", "FxZhkHurl", 12, 43, 1.2f, Root, Resin);
            Butt = Melee("ModZhkButt", 0.5f, 0.8f, 12f, 10f);
        }

        static void BuildTier3()
        {
            // Brood Mother: the acid rain, the frenzy call, the royal jelly thread
            AcidRain = Drop("ModZhkAcidRain", "FxZhkAcidRain", 11, 40, 1.1f, Acid, AcidPool);
            Pheromone = Vis("ModZhkPheromone", "FxZhkPheromone", "Play", 38, 22);
            JellyBead = Vis("ModZhkJellyBead", "FxZhkJelly", "Bead", 2, 2, true, 0.22f);
            // Acid Bloater: bubbles that pop into 2 / 4 / 6 drops by its size; the zip's body hit and the mist it leaves
            Droplet = Dart("ModZhkDroplet", "FxZhkDroplet", "Fly", 4, 2, 150f, 0.45f, 0.5f, 0.2f, Acid, 0.5f);
            for (int s = 0; s < 3; s++)
            {
                int drops = 2 + 2 * s;
                var pop = FxKit.Inert("ModZhkBubblePop" + drops, "FxZhkBubblePop", "Play");
                if (pop != null)
                {
                    Strike.ArtAt(pop, "FxZhkBubblePop", 15, 16);
                    FxFactory.OnSpawn[pop] = i => { var r = i.GetComponent<ZhkRingFx>() ?? i.AddComponent<ZhkRingFx>(); r.projectile = Droplet; r.count = drops; };
                }
                var b = Dart("ModZhkBubble" + drops, "FxZhkBubble", "Fly", 9, 6, 60f, 1.8f, 1.0f, 0.3f, Acid, 1f, rotate: false);
                if (b != null)
                {
                    FxFactory.SetEffect(b, destroyOnAnimEnd: false, destroyAfter: 1.8f, spawnOnDestroy: pop, freeRotate: false);
                    FxFactory.SetContacts(b, destroyOnHit: true, spawnOnHit: pop);
                }
                Bubble[s] = b;
            }
            ZipHit = Body("ModZhkZipHit", 1.2f, 0.3f, 1.0f, 0.3f, 22f, 22f, aimed: false);
            Mist = FxKit.TimedHit("ModZhkMist", "skydropExplode", "FxZhkSpiracleMist", "Play", 1, 7, 0.01f, 0f, Acid, 1f, rate: 0.3f, canFlip: false);
            Strike.Ground(Mist, "FxZhkSpiracleMist", 9, 11, 16f, 12f);
            // Acid Mantis: the blades (worth 1.4x on a Corroded target), the scissor X, the reflex cut and its reach ring
            Reap = Body("ModZhkReap", 1.2f, 0f, 0.8f, 0.15f, 20f, 20f, Acid, 0.5f);
            ScissorHit = Body("ModZhkScissor", 1.3f, 0f, 0.9f, 0.15f, 12f, 14f);
            ReflexCut = Body("ModZhkReflexCut", 0.8f, 0f, 0.6f, 0.12f, 16f, 16f, aimed: false);
            Reach = Vis("ModZhkReach", "FxZhkReach", "Loop", 30, 30, true);
            // Pit Antlion: the clamp, the pit, the sand it flicks
            Clamp = Melee("ModZhkClamp", 1.3f, 0.6f, 16f, 12f, Bleed, 0.4f);
            Pit = Vis("ModZhkPit", "FxZhkPit", "Loop", 33, 15, true, 5f);
            SandFlick = Vis("ModZhkSandFlick", "FxZhkSandFlick", "Play", 10, 14);
            FlickHit = Body("ModZhkFlickHit", 0.3f, 0f, 0f, 0.1f, 14f, 14f, aimed: false);
            Dirt = Vis("ModZhkDirt", "FxZhkDirt", "Play", 23, 9);
            // Amber Hive: the slam, the swarms it sends, the amber its cracked cells drip
            Slam = Body("ModZhkSlam", 1.2f, 0f, 1.2f, 0.18f, 22f, 18f);
            SwarmCloud = Dart("ModZhkSwarmCloud", "FxZhkSwarmCloud", "Loop", 9, 13, 55f, 3f, 0.5f, 0.1f, Mark, 1f, rotate: false);
            if (SwarmCloud != null)
            {
                FxFactory.SetDamage(SwarmCloud, 0.5f, rate: 0.5f, knockback: 0.1f, status: Mark, statusChance: 1f, collisionAtStart: true);
                FxFactory.SetContacts(SwarmCloud, destroyOnHit: false);
                Strike.Collider(SwarmCloud, 14f, 12f, 0f, 6f);
            }
            Drip = Vis("ModZhkDrip", "FxZhkDrip", "Life", 7, 3);
            if (Drip != null) FxFactory.OnSpawn[Drip] = i => { if (i.GetComponent<ZhkResinFx>() == null) i.AddComponent<ZhkResinFx>(); };
            // Hunting Wasp: the lance, the lifted hero's shadow
            Lance = Melee("ModZhkLance", 1.2f, 0.8f, 14f, 10f, Daze, 0.3f);
            CarryShadow = Vis("ModZhkCarryShadow", "FxZhkCarry", "Loop", 7, 3, true);
            // Blood Gorger: the drill and the beads of blood it pumps
            Drill = Melee("ModZhkDrill", 1.2f, 0.6f, 16f, 14f, Bleed, 0.3f);
            PumpBead = Vis("ModZhkPumpBead", "FxZhkPump", "Bead", 2, 2, true, 0.2f);
            // Botfly Matron: the ram and the egg dart that implants
            Ram = Melee("ModZhkRam", 1.2f, 1.2f, 14f, 16f);
            EggDart = Dart("ModZhkEggDart", "FxZhkEggDart", "Fly", 11, 3, 200f, 0.8f, 0.6f, 0.2f, Implant, 1f);
            ImplantBurst = Vis("ModZhkImplantBurst", "FxZhkImplantBurst", "Play", 11, 11);
            // Chitin Colossus: the gore (a heavy throw back) and the end of the bulldozer
            Gore = Body("ModZhkGore", 1.4f, 0f, 1.8f, 0.18f, 20f, 20f);
            BullHit = Body("ModZhkBullHit", 1.2f, 0f, 1.6f, 0.15f, 20f, 18f);
            // Glue Mortar: the shell, its glue field, the spotter's crosshair
            GlueField = Zone("ModZhkGlueField", "FxZhkGlueField", 16, 7, 28f, 10f, Slow, false);
            GlueShell = Drop("ModZhkGlueShell", "FxZhkGlueShell", 12, 43, 1.0f, Slow, GlueField);
            Spot = Vis("ModZhkSpot", "FxZhkSpot", "Loop", 6, 12, true, 0.6f);
            // Stag Titan: the tips of the jaws, the close-in headbutt, the landing after the toss
            Pinch = Body("ModZhkPinch", 1.4f, 0f, 0.9f, 0.12f, 10f, 12f);
            StagButt = Melee("ModZhkStagButt", 0.6f, 0.8f, 12f, 10f);
            TossLand = FxKit.TimedHit("ModZhkTossLand", "skydropExplode", "FxZhkTossLand", "Play", 0, 2, 0.6f, 0.4f, canFlip: false);
            Strike.Ground(TossLand, "FxZhkTossLand", 24, 12, 18f, 10f);
            // Sun Scarab: the shove, the fossil ball (0-3 larvae inside), its crack
            Shove = Body("ModZhkShove", 1.3f, 0f, 1.8f, 0.15f, 20f, 18f);
            CrackEmpty = FxKit.TimedHit("ModZhkCrackEmpty", "skydropExplode", "FxZhkFossilCrack", "Play", 0, 3, 0.5f, 0.4f, Root, 1f, canFlip: false);
            Strike.Ground(CrackEmpty, "FxZhkFossilCrack", 17, 18, 24f, 14f);
            CrackBrood = Vis("ModZhkCrackBrood", "FxZhkFossilCrack", "Play", 17, 18);
            for (int n = 0; n < 4; n++)
            {
                int brood = n;
                var b = Dart("ModZhkFossilBall" + n, "FxZhkFossilBall", "Fly" + n, 16, 16, 150f, 1.2f, 1.0f, 0.8f, rotate: false);
                if (b != null) FxFactory.OnSpawn[b] = i => { var f = i.GetComponent<ZhkFossilFx>() ?? i.AddComponent<ZhkFossilFx>(); f.Arm(brood); };
                FossilBall[n] = b;
            }
        }

        /// <summary>The larva's own effects, once its prefab exists (it hatches from eggs, corpses, implants and amber).</summary>
        public static void BuildLarva(GameObject larva, GameObject grubling)
        {
            if (larva != null)
            {
                LarvaHatch = FxKit.MinionSpawner("ModZhkLarvaHatch", larva, "FxZhkEgg", "Hatch");
                LarvaEgg = FxKit.MinionSpawner("ModZhkLarvaEgg", larva, "FxZhkEgg", "Life");
                LarvaFree = FxKit.MinionSpawner("ModZhkLarvaFree", larva, null, null, 0.3f);
            }
            if (grubling != null) GrublingSpawner = FxKit.MinionSpawner("ModZhkGrublingSpawner", grubling, null, null, 0.05f);
        }
    }
}
