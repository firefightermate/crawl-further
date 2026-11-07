using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Content.Gods.Ossivar;
    using CrawlFurther.Content.Gods.Sylvene;

    /// <summary>Jinx's effect templates and on-body indicators: cards, dice, hoops, chips, wheels and the tells of every
    /// monster's quirk. Built once by <see cref="JinxPack.Register"/>; other packs (the boss, items) reuse some of them.</summary>
    public static class JinxFx
    {
        /// <summary>The sheet the Marionette's strings fly on (also used by the Puppet Strings item).</summary>
        public const string StringArt = "FxJinxString";

        // shared: the Wild Card perk, curses, confetti and knives
        public static GameObject WildCard, Confetti, ConfettiPop, KnifeRain, DiamondPlate, DiamondBreak, PopPuff, Shuffle, SurgeAura,
                                 Wheel, JackSpawner, Blink;
        public static exSpriteAnimClip[] Suits;
        // tier 1
        public static GameObject JackPunch, LooseJackButt, Card, Ace, Die, DieShard, DieFace;
        // tier 2
        public static GameObject Whip, Hoop, Lash, Strings, CrystalBolt, FateMark, SnakeBite, SnakeDie, PikeThrust, TrapCard, TrapSnap,
                                 DieSlam, DieRoll, Imprint;
        public static GameObject[] HoopEncore, Tarot;
        // tier 3
        public static GameObject RouletteBite, BetMark, Ram, D20Shard, CritBurst, Fumble, AdvantageStrike, GorgonLash, Gaze, ClubSlam,
                                 Riposte, Topple, WhirlSlash, OrbitCard, TierFall, Chip, ChipSpray, Pot, PotBurst, PotBust, Sabre, Crunch,
                                 PuppetJab, StringBead, EyeOrb, OmenOrb, OracleGhost, BanditSlam, Coin, JuggleBall, MarotteBash, TaDa,
                                 ChimeraMaul, FireRing, Pawprint;
        /// <summary>Roulette: the called-colour wheel (Red, Black, Zero) and the wedge eruptions of each colour.</summary>
        public static GameObject[] BetCall, WedgeBurst, Reels;
        // indicators over the head
        public static StatusOverlayDef[] Wind, Stake, Loaded;
        public static StatusOverlayDef AceReady, Lucky, Strung;

        public static void Build()
        {
            var dizzy = FxFactory.GetStatus("StatusDizzy");
            var onFire = FxFactory.GetStatus("StatusOnFire");
            var poison = FxFactory.GetStatus("StatusPoisoned");
            var root = FxFactory.GetStatus("StatusStuckToFloor");
            ChanceFx.Curses = new[] { onFire, poison, FxFactory.GetStatus("StatusFrozen"), dizzy };
            BuildShared(dizzy);
            BuildStarters(dizzy);
            BuildSeconds(dizzy, onFire, poison, root);
            BuildFinals(dizzy, onFire, root);
            BuildIndicators();
            Plugin.Log.LogInfo("Jinx FX templates built");
        }

        static GameObject Loop(string name, string art, string anim, float life = 0f)
        {
            var go = FxKit.Visual(name, art, anim, loop: true);
            if (go != null) FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: life, canFlip: false, freeRotate: false);
            return go;
        }

        static GameObject Ground(GameObject go, string art, int gx, int gy, float w, float h)
        {
            Strike.Ground(go, art, gx, gy, w, h);
            return go;
        }

        static void BuildShared(Status dizzy)
        {
            Confetti = FxKit.Visual("ModConfetti", "FxConfetti", "Play");
            ConfettiPop = FxKit.TimedHit("ModConfettiPop", "skydropExplode", "FxConfetti", "Play", 1, 3, 0.6f, 0.8f, dizzy, 0.3f,
                                         colliderScale: 0.6f, canFlip: false, durations: new[] { 0.35f, 0.08f, 0.1f, 0.1f, 0.12f, 0.12f });
            Ground(ConfettiPop, "FxConfetti", 17, 19, 26f, 14f);
            KnifeRain = FxKit.TimedHit("ModKnifeRain", "skydropExplode", "FxKnifeRain", "Play", 3, 5, 1f, 0.5f,
                                       colliderScale: 0.4f, canFlip: false, durations: new[] { 0.3f, 0.2f, 0.12f, 0.06f, 0.15f, 0.3f });
            Ground(KnifeRain, "FxKnifeRain", 11, 27, 14f, 8f);
            WildCard = FxKit.Visual("ModWildCardFlip", "FxWildCard", "Play");
            // the card hangs over the head of the monster that drew it and follows it
            if (WildCard != null) FxFactory.OnSpawn[WildCard] = i => { var c = i.GetComponent<JinxCardOverHead>() ?? i.AddComponent<JinxCardOverHead>(); c.Bind(); };
            var sh = SpriteSheets.Get("FxWildCard");
            Suits = new exSpriteAnimClip[4];
            var names = new[] { "Hearts", "Spades", "Diamonds", "Clubs" };
            for (int i = 0; i < 4; i++)
                if (sh != null && sh.Has(names[i])) Suits[i] = new ClipBuilder(sh, names[i], "ModSuit" + names[i]).Once().Durations(0.9f).Build();
            Wheel = FxKit.Visual("ModWheelOfFortune", "FxWheel", "Play");
            DiamondPlate = FxKit.Visual("ModJinxDiamondPlate", "FxJinxDiamondPlate", "Orbit", loop: true);
            if (DiamondPlate != null)
            {
                FxFactory.SetEffect(DiamondPlate, destroyOnAnimEnd: false, offsetY: 10f, canFlip: true, freeRotate: false);
                Strike.ArtAt(DiamondPlate, "FxJinxDiamondPlate", 14, 8);
            }
            DiamondBreak = FxKit.Visual("ModJinxDiamondBreak", "FxJinxDiamondBreak", "Break");
            if (DiamondBreak != null) Strike.ArtAt(DiamondBreak, "FxJinxDiamondBreak", 14, 17);
            PopPuff = FxKit.Visual("ModJinxPopPuff", "FxJinxPopPuff", "Play");
            if (PopPuff != null) Strike.ArtAt(PopPuff, "FxJinxPopPuff", 17, 27);
            Shuffle = FxKit.Visual("ModJinxShuffle", "FxJinxShuffle", "Play");
            if (Shuffle != null) Strike.ArtAt(Shuffle, "FxJinxShuffle", 17, 27);
            SurgeAura = Loop("ModJinxSurge", "FxJinxSurge", "Loop", 3f);
            if (SurgeAura != null) Strike.ArtAt(SurgeAura, "FxJinxSurge", 13, 21);
            Blink = FxKit.Visual("ModJinxBlink", "FxJinxBlink", "Play");
            if (Blink != null) Strike.ArtAt(Blink, "FxJinxBlink", 12, 31);
        }

        static void BuildStarters(Status dizzy)
        {
            // Jack-in-the-Box: the spring punch turns with the aim (16 along it x 10 across)
            JackPunch = AimedMelee.Rotating(FxKit.BodyHit("ModJackBoxPunch", 1f, 0f, 1.2f, 0.2f));
            Strike.HitBox(JackPunch, 16f, 10f);
            LooseJackButt = AimedMelee.Rotating(FxKit.BodyHit("ModLooseJackButt", 1f, 0f, 1.0f, 0.2f));
            Strike.HitBox(LooseJackButt, 13f, 10f);
            // Card Sharp: cards that carry a random curse, and the gold Ace that cuts through everything and dazes
            Card = FxKit.Projectile("ModCard", "DFX_skelMageNewProjectile", "FxCard", "Fly", 200f, 0.9f, 0.4f, 0.3f);
            if (Card != null) FxFactory.OnSpawn[Card] = i => { var c = i.GetComponent<ChanceFx>() ?? i.AddComponent<ChanceFx>(); c.randomCurse = true; c.enabled = false; c.enabled = true; };
            Ace = FxKit.Projectile("ModJinxAce", "DFX_skelMageNewProjectile", "FxJinxAce", "Fly", 300f, 0.7f, 1.0f, 0.6f, dizzy, 1f,
                                   rotate: true, destroyOnHit: false);
            // Dice Imp: a die that rolls along the floor and hits for its face; the big die's shards and face
            Die = FxKit.Projectile("ModDie", "webBall", "FxDie", "Fly", 160f, 0.8f, 0.5f, 0.6f, accel: 30f, speedMax: 10f, rotate: false);
            Strike.ArtAt(Die, "FxDie", 10, 22);   // it hits feet, so it rolls on the floor; the art is drawn at the imp's hand
            if (Die != null) FxFactory.OnSpawn[Die] = i =>
            {
                var c = i.GetComponent<ChanceFx>() ?? i.AddComponent<ChanceFx>(); c.randomDamage = true; c.baseDamage = 0.25f; c.enabled = false; c.enabled = true;
                var rr = i.GetComponent<RollReadout>() ?? i.AddComponent<RollReadout>();
                rr.fromSource = true; rr.max = 6;
            };
            DieShard = FxKit.Projectile("ModDieShard", "DFX_skelMageNewProjectile", "FxJinxDieShard", "Fly", 170f, 0.6f, 0.5f, 0.4f);
            Strike.HitBox(DieShard, 8f, 7f);
            DieFace = FxKit.Visual("ModDieFace", "FxDieFace", "Play");
        }

        static void BuildSeconds(Status dizzy, Status onFire, Status poison, Status root)
        {
            // Ringmaster: the whip and the flaming hoop (a boomerang), plus the faster white-gold hoops of an encore
            Whip = AimedMelee.Rotating(FxKit.BodyHit("ModRingmasterWhip", 1.0f, 0f, 0.8f, 0.2f));
            Strike.HitBox(Whip, 28f, 10f);
            Hoop = MakeHoop("ModFlamingHoop", "Fly", 220f, onFire);
            HoopEncore = new[] { MakeHoop("ModFlamingHoopEncore1", "Encore", 270f, onFire), MakeHoop("ModFlamingHoopEncore2", "Encore", 320f, onFire) };
            // Marionette: its ribbon lash and the thread on a needle that tugs and dazes
            Lash = GodsBArc.Swipe("ModMarionetteLash", "OrcSwipe", "FxJinxLash", "Play", 9, 14, 0.9f, 0.6f);
            Strings = FxKit.Projectile("ModPuppetString", "DFX_skelMageNewProjectile", StringArt, "Fly", 210f, 0.75f, 0.3f, 0f, dizzy, 1f, destroyOnHit: false);
            if (Strings != null) FxFactory.OnSpawn[Strings] = i => { var h = i.GetComponent<HookFx>() ?? i.AddComponent<HookFx>(); h.strength = 110f; };
            // Fortune Teller: the crystal bolt and the fate mark (FateMarkFx turns the card)
            CrystalBolt = FxKit.Projectile("ModCrystalBolt", "DFX_skelMageNewProjectile", "FxOrb", "Fly", 160f, 1.1f, 0.9f, 0.4f, dizzy, 0.25f);
            FateMark = FxKit.Inert("ModFateMark", "FxFateMark", "Play", destroyOnAnimEnd: true);
            if (FateMark != null)
            {
                Strike.ArtAt(FateMark, "FxFateMark", 12, 24);
                FxFactory.OnSpawn[FateMark] = i => { var f = i.GetComponent<FateMarkFx>() ?? i.AddComponent<FateMarkFx>(); f.Arm(); };
            }
            Tarot = new GameObject[3];
            var tn = new[] { "Tower", "Fool", "Star" };
            for (int k = 0; k < 3; k++) Tarot[k] = FxKit.Visual("ModTarot" + tn[k], "FxTarot", tn[k]);
            // Snake-Eyes: a venomous lunge and the two dice of Craps
            SnakeBite = AimedMelee.Rotating(FxKit.BodyHit("ModSnakeBite", 1.0f, 0f, 0.6f, 0.15f, poison, 0.35f));
            Strike.HitBox(SnakeBite, 14f, 10f);
            SnakeDie = FxKit.Projectile("ModSnakeDie", "webBall", "FxDie", "Fly", 175f, 0.85f, 0.5f, 0.5f, accel: 30f, speedMax: 10f, rotate: false);
            Strike.ArtAt(SnakeDie, "FxDie", 10, 13);
            // Card Soldier: the pike, and the trap cards it deals round the hero
            PikeThrust = AimedMelee.Rotating(FxKit.BodyHit("ModJinxPikeThrust", 1.1f, 0f, 0.9f, 0.15f));
            Strike.HitBox(PikeThrust, 22f, 10f);
            TrapSnap = FxKit.TimedHit("ModJinxTrapSnap", "skydropExplode", "FxJinxTrapCard", "Snap", 1, 3, 0.9f, 0.3f, root, 1f,
                                      canFlip: false, durations: new[] { 0.05f, 0.06f, 0.08f, 0.08f, 0.08f, 0.1f });
            Ground(TrapSnap, "FxJinxTrapCard", 13, 23, 14f, 10f);
            TrapCard = FxKit.Inert("ModJinxTrapCard", "FxJinxTrapCard", "Land", destroyOnAnimEnd: true, thenAnim: "Lie", thenRepeat: 9);
            if (TrapCard != null)
            {
                Strike.ArtAt(TrapCard, "FxJinxTrapCard", 13, 23);
                FxFactory.OnSpawn[TrapCard] = i => { var t = i.GetComponent<JinxTrapFx>() ?? i.AddComponent<JinxTrapFx>(); t.Arm(); };
            }
            // Loaded Die: the hop slam, the tumble, and the stamp of its loaded face
            DieSlam = AimedMelee.Rotating(FxKit.BodyHit("ModJinxDieSlam", 1.0f, 0f, 1.0f, 0.15f));
            Strike.HitBox(DieSlam, 14f, 12f);
            DieRoll = FxKit.BodyHit("ModJinxDieRoll", 0.8f, 0f, 0.9f, 0.42f);
            Strike.HitBox(DieRoll, 16f, 14f);
            Imprint = FxKit.TimedHit("ModJinxImprint", "skydropExplode", "FxJinxImprint", "Play", 1, 3, 0.15f, 1.0f, canFlip: false,
                                     durations: new[] { 0.04f, 0.06f, 0.08f, 0.1f, 0.14f, 0.16f });
            Ground(Imprint, "FxJinxImprint", 27, 15, 26f, 10f);
        }

        static GameObject MakeHoop(string name, string anim, float speed, Status onFire)
        {
            var go = FxKit.Projectile(name, "AxeThrowProjectileBoomerang", "FxHoop", anim, speed, 1.2f, 0.8f, 0.6f, onFire, 0.3f,
                                      rotate: false, destroyOnHit: false);
            if (go == null) return null;
            FxFactory.SetDamage(go, 0.8f, rate: 0.35f, knockback: 0.6f, status: onFire, statusChance: 0.3f, collisionAtStart: true);
            FxFactory.SetMotion(go, speed, accel: -speed * 1.73f);   // turns back after about 64 px at any speed
            return go;
        }

        static void BuildFinals(Status dizzy, Status onFire, Status root)
        {
            var bleed = FxFactory.GetStatus("StatusBleeding");
            // Roulette Ouroboros: the bite, the bets on the floor and the wedges that erupt
            RouletteBite = AimedMelee.Rotating(FxKit.BodyHit("ModJinxRouletteBite", 1.3f, 0f, 1.0f, 0.15f));
            Strike.HitBox(RouletteBite, 16f, 10f);
            BetMark = Loop("ModJinxBetMark", "FxJinxBetWheel", "Mark", 2.5f);
            if (BetMark != null) Strike.ArtAt(BetMark, "FxJinxBetWheel", 37, 17);
            var colours = new[] { "Red", "Black", "Zero" };
            BetCall = new GameObject[3]; WedgeBurst = new GameObject[3];
            for (int k = 0; k < 3; k++)
            {
                BetCall[k] = FxKit.Visual("ModJinxBetCall" + colours[k], "FxJinxBetWheel", colours[k]);
                if (BetCall[k] != null) Strike.ArtAt(BetCall[k], "FxJinxBetWheel", 37, 17);
                WedgeBurst[k] = FxKit.TimedHit("ModJinxWedge" + colours[k], "skydropExplode", "FxJinxWedgeBurst", colours[k], 1, 3, 1.5f, 0.8f,
                                               canFlip: false, durations: new[] { 0.04f, 0.06f, 0.08f, 0.1f, 0.1f, 0.12f });
                Ground(WedgeBurst[k], "FxJinxWedgeBurst", 10, 22, 16f, 9f);
            }
            // Natural Twenty: the ram, the d20 shards, the critical burst, the fumble and Advantage's struck-out roll
            Ram = AimedMelee.Rotating(FxKit.BodyHit("ModJinxRam", 1.2f, 0f, 1.2f, 0.2f));
            Strike.HitBox(Ram, 16f, 16f);
            D20Shard = FxKit.Projectile("ModJinxD20Shard", "DFX_skelMageNewProjectile", "FxJinxD20Shard", "Fly", 180f, 0.7f, 0.7f, 0.4f, rotate: false);
            CritBurst = FxKit.TimedHit("ModJinxCritBurst", "skydropExplode", "FxJinxCrit", "Crit", 1, 3, 1.5f, 1.4f, canFlip: false,
                                       durations: new[] { 0.04f, 0.05f, 0.06f, 0.08f, 0.1f, 0.12f, 0.14f });
            Ground(CritBurst, "FxJinxCrit", 19, 35, 40f, 18f);
            Fumble = FxKit.Visual("ModJinxFumble", "FxJinxCrit", "Fumble");
            AdvantageStrike = FxKit.Visual("ModJinxStrike", "FxJinxStrike", "Play");
            if (AdvantageStrike != null) Strike.ArtAt(AdvantageStrike, "FxJinxStrike", 8, 5);
            // Gorgon: the hair snakes' strike and the stare (a beam at eye height that turns with the aim and roots)
            GorgonLash = AimedMelee.Rotating(FxKit.BodyHit("ModJinxGorgonLash", 1.2f, 0f, 0.8f, 0.15f));
            Strike.HitBox(GorgonLash, 18f, 16f);
            Gaze = AimedMelee.Rotating(FxKit.TimedHit("ModJinxGaze", "DamageBeholderBeam", "FxJinxGaze", "Play", 2, 4, 0.9f, 0.2f, root, 1f,
                                  canFlip: true, durations: new[] { 0.05f, 0.05f, 0.12f, 0.12f, 0.08f, 0.08f }));
            if (Gaze != null) { Strike.ArtAt(Gaze, "FxJinxGaze", 65, 5); Strike.Collider(Gaze, 62f, 14f, 31f, 0f); }
            // Card King: the club quake and the cards Hold Court throws back
            ClubSlam = FxKit.TimedHit("ModJinxClubSlam", "skydropExplode", "FxJinxClubSlam", "Play", 0, 2, 1.4f, 1.2f, dizzy, 0.3f,
                                      canFlip: false, durations: new[] { 0.05f, 0.07f, 0.08f, 0.1f, 0.12f });
            Ground(ClubSlam, "FxJinxClubSlam", 15, 19, 26f, 10f);
            Riposte = FxKit.Projectile("ModJinxRiposte", "DFX_skelMageNewProjectile", "FxJinxRiposte", "Fly", 210f, 0.8f, 0.8f, 0.5f);
            // House of Cards: the toppling tier, the whirl at zero tiers, the storm cards and the tier that falls off
            Topple = AimedMelee.Rotating(FxKit.BodyHit("ModJinxTopple", 1.2f, 0f, 1.0f, 0.15f));
            Strike.HitBox(Topple, 16f, 16f);
            WhirlSlash = FxKit.BodyHit("ModJinxWhirlSlash", 1.0f, 0.2f, 0.8f, 0.3f);
            Strike.HitBox(WhirlSlash, 30f, 20f);
            OrbitCard = FxKit.Projectile("ModJinxOrbitCard", "DFX_skelMageNewProjectile", "FxJinxOrbitCard", "Fly", 0f, 6f, 0.8f, 0.4f,
                                         rotate: false, destroyOnHit: true);
            if (OrbitCard != null) { FxFactory.SetMotion(OrbitCard, 0f, enabled: false); Strike.Collider(OrbitCard, 7f, 8f); }
            TierFall = FxKit.Visual("ModJinxTierFall", "FxJinxTierFall", "Play");
            if (TierFall != null) Strike.ArtAt(TierFall, "FxJinxTierFall", 16, 34);
            // High Roller: flicked chips, the pot on the floor, its payout and its bust
            Chip = FxKit.Projectile("ModJinxChip", "DFX_skelMageNewProjectile", "FxJinxChip", "Fly", 200f, 0.8f, 1.0f, 0.4f, rotate: false);
            if (Chip != null) FxFactory.OnSpawn[Chip] = i => { if (i.GetComponent<JinxChipTag>() == null) i.AddComponent<JinxChipTag>(); };
            ChipSpray = FxKit.Projectile("ModJinxChipSpray", "DFX_skelMageNewProjectile", "FxJinxChip", "Fly", 190f, 0.8f, 1.0f, 0.4f, rotate: false);
            Pot = FxKit.Inert("ModJinxPot", "FxJinxPot", "Land", destroyOnAnimEnd: true, thenAnim: "Tick", thenRepeat: 8);
            if (Pot != null)
            {
                Strike.ArtAt(Pot, "FxJinxPot", 17, 18);
                FxFactory.OnSpawn[Pot] = i => { if (i.GetComponent<JinxPotFx>() == null) i.AddComponent<JinxPotFx>(); };
            }
            PotBurst = FxKit.Visual("ModJinxPotBurst", "FxJinxPot", "Burst");
            if (PotBurst != null) Strike.ArtAt(PotBurst, "FxJinxPot", 17, 18);
            PotBust = FxKit.Visual("ModJinxPotBust", "FxJinxPot", "Bust");
            if (PotBust != null) Strike.ArtAt(PotBust, "FxJinxPot", 17, 18);
            // Nutcracker: the sabre and the jaws' crunch
            Sabre = GodsBArc.Swipe("ModJinxSabre", "OrcSwipe", "FxJinxSabre", "Play", 9, 14, 1.2f, 0.8f);
            Crunch = FxKit.TimedHit("ModJinxCrunch", "skydropExplode", "FxJinxCrunch", "Play", 0, 1, 0.6f, 0.2f, canFlip: false,
                                    durations: new[] { 0.05f, 0.06f, 0.07f, 0.08f, 0.1f });
            Ground(Crunch, "FxJinxCrunch", 17, 21, 14f, 10f);
            // Puppeteer: the puppets' stab, and the beads that draw its strings to the allies it holds
            PuppetJab = AimedMelee.Rotating(FxKit.BodyHit("ModPuppetJab", 1.1f, 0f, 0.8f, 0.15f));
            Strike.HitBox(PuppetJab, 16f, 14f);
            StringBead = Loop("ModJinxStringBead", "FxJinxStrung", "Bead");
            if (StringBead != null) Strike.ArtAt(StringBead, "FxJinxStrung", 5, 8);
            // The Oracle: her orb, the harmless omen orbs and the ghost that acts out her prophecy
            EyeOrb = FxKit.Projectile("ModJinxEyeOrb", "DFX_skelMageNewProjectile", "FxJinxEyeOrb", "Fly", 150f, 1.2f, 1.1f, 0.4f);
            OmenOrb = FxKit.Projectile("ModJinxOmenOrb", "DFX_skelMageNewProjectile", "FxJinxEyeOrb", "Ghost", 150f, 0.9f, 0f, 0f, destroyOnHit: false);
            if (OmenOrb != null) FxFactory.SetDamage(OmenOrb, 0f, enabled: false);
            OracleGhost = FxKit.Visual("ModJinxOracleGhost", "FxJinxOracleGhost", "Act");
            var osh = SpriteSheets.Get("FxJinxOracleGhost");
            if (OracleGhost != null && osh != null) Strike.ArtAt(OracleGhost, "FxJinxOracleGhost", osh.manifest.cellW / 2, osh.manifest.cellH - 2);
            // One-Armed Bandit: the lever slam, coins and the reel results
            BanditSlam = AimedMelee.Rotating(FxKit.BodyHit("ModBanditSlam", 1.4f, 0f, 1.4f, 0.15f));
            Strike.HitBox(BanditSlam, 16f, 12f);
            Coin = FxKit.Projectile("ModJackpotCoin", "DFX_skelMageNewProjectile", "FxCoin", "Fly", 190f, 0.9f, 0.6f, 0.3f, rotate: false);
            Reels = new GameObject[4];
            var rn = new[] { "Cherry", "Bell", "Skull", "Seven" };
            for (int k = 0; k < 4; k++) Reels[k] = FxKit.Visual("ModReel" + rn[k], "FxReel", rn[k]);
            // Grand Jester: juggled balls that burst into confetti, the tragedy bash and the ta-da of a turned mask
            JuggleBall = FxKit.Projectile("ModJuggleBall", "webBall", "FxJuggleBall", "Fly", 170f, 0.9f, 0.9f, 0.8f, accel: 25f, speedMax: 10f, rotate: false);
            if (JuggleBall != null)
            {
                FxFactory.SetEffect(JuggleBall, destroyOnAnimEnd: false, destroyAfter: 0.9f, spawnOnDestroy: ConfettiPop, freeRotate: false);
                FxFactory.SetContacts(JuggleBall, destroyOnHit: true, spawnOnHit: Confetti);
                Strike.ArtAt(JuggleBall, "FxJuggleBall", 10, 30);   // rolls on the floor, drawn at his hands
            }
            MarotteBash = AimedMelee.Rotating(FxKit.BodyHit("ModJinxMarotteBash", 1.5f, 0f, 1.6f, 0.15f));
            Strike.HitBox(MarotteBash, 14f, 14f);
            TaDa = FxKit.TimedHit("ModJinxTaDa", "skydropExplode", "FxJinxTaDa", "Play", 1, 3, 0.8f, 1.0f, canFlip: false,
                                  durations: new[] { 0.04f, 0.05f, 0.06f, 0.08f, 0.1f, 0.12f });
            Ground(TaDa, "FxJinxTaDa", 26, 18, 44f, 20f);
            // Big-Top Chimera: the claws, the landing ring of fire and the burning pawprints of its last act
            ChimeraMaul = GodsBArc.Swipe("ModChimeraMaul", "OrcSwipe", "FxJinxMaul", "Play", 9, 14, 1.4f, 1.0f, bleed, 0.25f);
            FireRing = FxKit.TimedHit("ModFireRing", "skydropExplode", "FxFireRing", "Play", 1, 7, 0.7f, 0.4f, onFire, 0.4f, rate: 0.45f,
                                      canFlip: false, durations: new[] { 0.06f, 0.08f, 0.2f, 0.2f, 0.2f, 0.2f, 0.2f, 0.2f });
            Ground(FireRing, "FxFireRing", 18, 15, 30f, 12f);
            Pawprint = FxKit.TimedHit("ModJinxPawprint", "skydropExplode", "FxJinxPawprint", "Play", 1, 7, 0.5f, 0.05f, rate: 1.0f,
                                      canFlip: false, durations: new[] { 0.05f, 0.08f, 0.3f, 0.3f, 0.3f, 0.3f, 0.4f, 0.2f });
            Ground(Pawprint, "FxJinxPawprint", 7, 9, 10f, 6f);
        }

        static void BuildIndicators()
        {
            Wind = new[]
            {
                ModStatus.Indicator("ModJinxWind1", "FxJinxWind", "One", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModJinxWind2", "FxJinxWind", "Two", 1f, OverlayAt.Head),
                ModStatus.Indicator("ModJinxWind3", "FxJinxWind", "Three", 1f, OverlayAt.Head),
            };
            AceReady = ModStatus.Indicator("ModJinxAceReady", "FxJinxAce", "Over", 1f, OverlayAt.Head);
            Lucky = ModStatus.Indicator("ModJinxLucky", "FxJinxLucky", "Loop", 1f, OverlayAt.Head);
            Strung = ModStatus.Indicator("ModJinxStrung", "FxJinxStrung", "Cross", 1f, OverlayAt.Head);
            Loaded = new StatusOverlayDef[6];
            for (int k = 0; k < 6; k++) Loaded[k] = ModStatus.Indicator("ModJinxLoaded" + (k + 1), "FxJinxLoadedPips", "P" + (k + 1), 1f, OverlayAt.Head);
            Stake = new StatusOverlayDef[7];
            for (int k = 0; k < 7; k++) Stake[k] = ModStatus.Indicator("ModJinxStake" + k, "FxJinxStake", "P" + k, 1f, OverlayAt.Head);
        }
    }
}
