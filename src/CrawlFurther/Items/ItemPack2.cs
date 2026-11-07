using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Items
{
    using CrawlFurther.Art;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.BelMora;
    using CrawlFurther.Content.Gods.Jinx;
    using CrawlFurther.Content.Gods.Ossivar;
    using CrawlFurther.Content.Gods.Sylvene;
    using CrawlFurther.Content.Gods.Umbrael;
    using CrawlFurther.Content.Gods.Vhorrul;

    /// <summary>The second wave of hero items: 15 skills (spells) and 15 artifacts.</summary>
    public static class ItemPack2
    {
        public static Powerup EmberHeart, VenomGland, RimeRing, LeechSeed, LuckyDie, AshHourglass, GlassMask, BarnacleShell,
                              Tidecaller, BrineFlask, JestersBell, JokersWild, MarionetteCross;
        public static GameObject HeroWax, HeroBrine, HeroWave, HeroSporeBomb, HeroWildCard, HeroDie, HeroStrings, ShardNova, SwapToken,
                                 TideBurst, HeroCandleBolt, HeroSpikes, HeroSkull, HeroLantern, HeroBellToll, HeroRoots;
        // the items' own world art (art/out_itemfx): fire the hero wax becomes, undertow brine, spore burst, procs, ...
        public static GameObject HeroWaxFire, HeroUndertowBrine, HeroSporeBurst, SwapFlash, ShadowEcho, ChainJumpFlash,
                                 EmberProc, VenomProc, RimeProc, LeechHeal, BrineRegen, BarnacleLoop, LuckyDodge, JesterCrit,
                                 JokerFlip, MarionetteTug, HourglassTurn, GlassCrack, EmberPop, WickPop;
        public static GameObject[] CurseBursts = new GameObject[4], DieRolls = new GameObject[6];
        public static exSpriteAnimClip[] CardClips = new exSpriteAnimClip[4], JokerSuits = new exSpriteAnimClip[4];

        static List<DamageEffectData> Special(Powerup pu) { return R.Get<List<DamageEffectData>>(pu, "m_specialAttackDamageEffects"); }
        static System.Collections.IList Effects(Powerup pu) { return R.Get<System.Collections.IList>(pu, "m_effects"); }
        static void AllSpecial(Powerup pu, GameObject fx) { if (fx == null) return; foreach (var d in Special(pu)) d.m_object = fx; }
        static void FirstSpecial(Powerup pu, GameObject fx, bool atHero = false)
        {
            var sp = Special(pu);
            if (sp.Count == 0 || fx == null) return;
            sp[0].m_object = fx;
            if (atHero) { sp[0].m_offsetX = new MinMaxRange(0f); sp[0].m_offsetY = new MinMaxRange(0f); }
        }
        static PlayerModifier Mul(PlayerModifier.eType t, float v)
        {
            return new PlayerModifier { m_modify = t, m_type = ValueModifier.eModifierType.Multiply, m_value = v, m_priority = 0f };
        }
        static Action<GameObject, Powerup> Passive(Action<Powerup> keep, params PlayerModifier[] mods)
        {
            return (go, pu) => { R.Set(pu, "m_modifiers", new List<PlayerModifier>(mods)); if (keep != null) keep(pu); };
        }

        static GameObject HeroDropper(string name, GameObject trail, float trailDist, float life, float speed, string art = null)
        {
            return ItemPack.HeroDropper(name, trail, trailDist, life, speed, art);
        }

        static GameObject Dressed(GameObject template, string name, string sheet, string anim, float damageMult = 1f)
        {
            return ItemPack.Dressed(template, name, sheet, anim, damageMult);
        }

        /// <summary>Visuals the artifacts spawn (procs, heals, dodges...), all from art/out_itemfx.</summary>
        static void BuildVisuals()
        {
            EmberProc = ItemArt.Visual("ModItemEmberHeartProc", "FxItemEmberHeart", "Proc");
            VenomProc = ItemArt.Visual("ModItemVenomGlandProc", "FxItemVenomGland", "Proc");
            RimeProc = ItemArt.Visual("ModItemRimeRingProc", "FxItemRimeRing", "Proc");
            LeechHeal = ItemArt.Visual("ModItemLeechSeedHeal", "FxItemLeechSeed", "Heal");
            BrineRegen = ItemArt.Visual("ModItemBrineFlaskRegen", "FxItemBrineFlask", "Regen");
            {
                // the crust closes (On) and then holds (Loop) for as long as you stand still; despawned when you move
                var sh = SpriteSheets.Get("FxItemBarnacle");
                if (sh != null && sh.Has("On") && sh.Has("Loop"))
                {
                    BarnacleLoop = FxFactory.Visual("ModItemBarnacleShell", sh, new ClipBuilder(sh, "On", "ModItemBarnacleShellClip").Once().Then("Loop", 400).Build(), false);
                    ItemArt.Place(BarnacleLoop, "FxItemBarnacle");
                }
            }
            LuckyDodge = ItemArt.Visual("ModItemLuckyDieDodge", "FxItemLuckyDie", "Dodge");
            JesterCrit = ItemArt.Visual("ModItemJesterCrit", "FxItemJesterCrit", "Crit");
            JokerFlip = ItemArt.Visual("ModItemJokerFlip", "FxItemJokerFlip", "Flip");
            string[] suits = { "Hearts", "Spades", "Diamonds", "Clubs" };          // suit index order of the boon switch
            for (int k = 0; k < 4; k++) JokerSuits[k] = ItemArt.Clip("FxItemJokerFlip", suits[k]);
            MarionetteTug = ItemArt.Visual("ModItemMarionetteTug", "FxItemMarionetteTug", "Tug");
            HourglassTurn = ItemArt.Visual("ModItemHourglassTurn", "FxItemHourglass", "Proc");
            GlassCrack = ItemArt.Visual("ModItemGlassMaskCrack", "FxItemGlassMask", "Crack");
            ShadowEcho = ItemArt.Visual("ModItemShadowEcho", "FxItemShadowEcho", "Echo");
            SwapFlash = ItemArt.Visual("ModItemSwapFlash", "FxItemShadowSwap", "Flash");
            ChainJumpFlash = ItemArt.Visual("ModItemChainJump", "FxItemChainSpark", "Hit");
            EmberPop = ItemArt.Visual("ModItemEmberPop", "FxItemEmberVolley", "Pop");
            WickPop = ItemArt.Visual("ModItemWickPop", "FxItemWickBolt", "Pop");
            string[] curses = { "Fire", "Poison", "Frost", "Daze" };               // ChanceFx.Curses order
            for (int k = 0; k < 4; k++)
            {
                CurseBursts[k] = ItemArt.Visual("ModItemCurse" + curses[k], "FxItemWildCurse", "Curse" + curses[k]);
                CardClips[k] = ItemArt.Clip("FxItemWildCard", "Fly" + curses[k], loop: true);
            }
            for (int n = 0; n < 6; n++) DieRolls[n] = ItemArt.Visual("ModItemDieRoll" + (n + 1), "FxItemDieRoll", "Roll" + (n + 1));
        }

        /// <summary>A per-spawn instance tweak: the instance plays <paramref name="clip"/> (its Effect plays the default
        /// clip at spawn) and spawns <paramref name="hitFx"/> where it hits.</summary>
        static void Dress(GameObject inst, exSpriteAnimClip clip, GameObject hitFx)
        {
            if (clip != null)
            {
                var an = inst.GetComponent<exSpriteAnimation>();
                var eff = inst.GetComponent<Effect>();
                if (eff != null) R.Set(eff, "m_animationDefault", clip);
                ItemArt.Ensure(an, clip, true);
            }
            if (hitFx != null) ItemArt.Puffs(inst, hitFx);
            foreach (var spr in inst.GetComponents<exSprite>()) spr.color = Color.white;
        }

        static void BuildFx()
        {
            var goo = FxFactory.GetStatus("StatusLavaSteveGoo");
            var dizzy = FxFactory.GetStatus("StatusDizzy");
            BuildVisuals();
            // floor effects that slow monsters instead of the hero
            if (VhorrulFx.WaxPuddle != null)
            {
                HeroWax = MonsterFactory.ClonePrefab(VhorrulFx.WaxPuddle, "ModHeroWax");
                FxFactory.SetStatusZone(HeroWax, goo, hitsHero: false, hitsMonster: true);
                ItemArt.Wear(HeroWax, "FxItemWaxSlick", "Life");
                // lit wax burns in Wax Slick's own fire (Patch_HeroWaxIgnite), a hero copy of the burning pool
                HeroWaxFire = Dressed(VhorrulFx.BurningPool, "ModItemWaxFire", "FxItemWaxFire", "Life");
                {
                    System.Action<GameObject> baseHook;
                    FxFactory.OnSpawn.TryGetValue(VhorrulFx.WaxPuddle, out baseHook);
                    FxFactory.OnSpawn[HeroWax] = i =>
                    {
                        if (baseHook != null) baseHook(i);
                        var w = i.GetComponent<WaxPuddleFx>();
                        if (w != null) w.heroOwned = true;
                    };
                }
            }
            if (BelMoraFx.Brine != null)
            {
                HeroBrine = MonsterFactory.ClonePrefab(BelMoraFx.Brine, "ModHeroBrine");
                FxFactory.SetStatusZone(HeroBrine, goo, hitsHero: false, hitsMonster: true);
                ItemArt.Wear(HeroBrine, "FxItemRiptidePool", "Life");                        // Riptide Dash's whirlpool
                HeroUndertowBrine = MonsterFactory.ClonePrefab(BelMoraFx.Brine, "ModHeroUndertowBrine");
                FxFactory.Templates[HeroUndertowBrine.name] = HeroUndertowBrine;
                FxFactory.SetStatusZone(HeroUndertowBrine, goo, hitsHero: false, hitsMonster: true);
                ItemArt.Wear(HeroUndertowBrine, "FxItemUndertowBrine", "Life");               // what Undertow's wave leaves
            }
            if (BelMoraFx.Wave != null)
            {
                HeroWave = MonsterFactory.ClonePrefab(BelMoraFx.Wave, "ModHeroWave");
                FxFactory.SetMotion(HeroWave, 150f, trail: HeroUndertowBrine ?? HeroBrine, trailDist: 26f);
                FxFactory.SetDamage(HeroWave, 0.7f, rate: 0.5f, knockback: 2.2f, status: goo, statusChance: 0.5f, collisionAtStart: true);
                ItemArt.Wear(HeroWave, "FxItemUndertowWave", "Fly", loop: true);
                ItemArt.Puffs(HeroWave, ItemArt.Visual("ModItemUndertowSplash", "FxItemUndertowWave", "Pop"));
            }
            // Spore Bomb: its own pod in flight (was the seed's bursting anim), its own burst (a hero copy of the pod burst:
            // 0.75, always poisons, 26 x 12)
            HeroSporeBurst = Dressed(SylveneFx.PodBurst, "ModItemSporeBurst", "FxItemSporeBurst", "Burst");
            HeroSporeBomb = FxKit.Projectile("ModHeroSporeBomb", "webBall", "FxItemSporePod", "Fly", 170f, 0.7f, 0.5f, 0.3f, accel: 20f, speedMax: 8f, rotate: false);
            if (HeroSporeBomb != null)
            {
                var burst = HeroSporeBurst ?? SylveneFx.PodBurst;
                FxFactory.SetEffect(HeroSporeBomb, destroyOnAnimEnd: false, destroyAfter: 0.7f, spawnOnDestroy: burst, freeRotate: false);
                FxFactory.SetContacts(HeroSporeBomb, destroyOnHit: true, spawnOnHit: burst);
                ItemArt.Place(HeroSporeBomb, "FxItemSporePod");                               // rides 10 px over the floor point
            }
            // Wild Card: the card shows the curse it drew (fire / poison / frost / daze) and that curse bursts on the monster
            HeroWildCard = FxKit.Projectile("ModHeroWildCard", "DFX_skelMageNewProjectile", "FxItemWildCard", "Fly", 230f, 0.9f, 0.8f, 0.4f);
            if (HeroWildCard != null)
            {
                ItemArt.Place(HeroWildCard, "FxItemWildCard");
                FxFactory.OnSpawn[HeroWildCard] = i =>
                {
                    var c = i.GetComponent<ChanceFx>() ?? i.AddComponent<ChanceFx>(); c.randomCurse = true; c.enabled = false; c.enabled = true;
                    var de = i.GetComponent<DamageEffect>();
                    var st = de != null ? R.Get<Status>(de, "m_status") : null;
                    int k = ChanceFx.Curses != null && st != null ? Array.IndexOf(ChanceFx.Curses, st) : -1;
                    if (k >= 0 && k < 4) Dress(i, CardClips[k], CurseBursts[k]);
                };
            }
            // Loaded Dice: its own die; the face it rolled pops up over the monster it hits (no more red tint by roll)
            HeroDie = FxKit.Projectile("ModHeroDie", "DFX_skelMageNewProjectile", "FxItemLoadedDie", "Fly", 200f, 0.9f, 0.4f, 0.6f, rotate: false);
            if (HeroDie != null)
            {
                // drawn at full size: the old x1.3 template scale is baked into the collider (11.45 x 10 -> 14.9 x 13)
                HeroDie.transform.localScale = Vector3.one;
                foreach (var b in HeroDie.GetComponents<BoxCollider>()) { b.size = new Vector3(b.size.x * 1.3f, b.size.y * 1.3f, b.size.z); b.center = new Vector3(b.center.x * 1.3f, b.center.y * 1.3f, b.center.z); }
                ItemArt.Place(HeroDie, "FxItemLoadedDie");
                FxFactory.OnSpawn[HeroDie] = i =>
                {
                    var c = i.GetComponent<ChanceFx>() ?? i.AddComponent<ChanceFx>(); c.randomDamage = true; c.baseDamage = 0.3f; c.enabled = false; c.enabled = true;
                    int n = Mathf.Clamp(c.lastRoll, 1, 6);
                    Dress(i, null, DieRolls[n - 1]);
                    // the pips it rolled pop up as a number beside that face (gold 6, grey-red 1)
                    var rr = i.GetComponent<RollReadout>() ?? i.AddComponent<RollReadout>();
                    rr.fromSource = true; rr.max = 6; rr.besideHit = true;
                };
            }
            HeroStrings = FxKit.Projectile("ModHeroStrings", "DFX_skelMageNewProjectile", "FxItemPuppetString", "Fly", 220f, 0.75f, 0.5f, 0.1f, dizzy, 0.5f, destroyOnHit: false);
            if (HeroStrings != null)
            {
                ItemArt.Place(HeroStrings, "FxItemPuppetString");
                ItemArt.Puffs(HeroStrings, ItemArt.Visual("ModItemStringSnap", "FxItemPuppetString", "Pop"));
            }
            ItemFixes.PierceMonsters(HeroStrings);
            var novaShard = Dressed(UmbraelFx.RingShard, "ModHeroRingShard", "FxItemNovaShard", "Fly", 0.7f);
            ItemArt.Puffs(novaShard, ItemArt.Visual("ModItemNovaShardPop", "FxItemNovaShard", "Pop"));
            ShardNova = FxKit.Emitter("ModHeroShardNova", novaShard, 6);
            HeroCandleBolt = Dressed(VhorrulFx.CandleBolt, "ModHeroCandleBolt", "FxItemEmberVolley", "Fly", 0.75f);
            ItemArt.Puffs(HeroCandleBolt, EmberPop);
            HeroSpikes = Dressed(OssivarFx.SpikeBurst, "ModHeroSpikeBurst", "FxItemMarrowSpikes", "Play", 0.7f);
            if (HeroSpikes != null)
            {
                // drawn at full size: the monster ring's x1.3 scale goes into the footprint instead (40 x 16 -> 52 x 21)
                ItemArt.UnitScale(HeroSpikes);
                Strike.Collider(HeroSpikes, 52f, 20.8f);
            }
            HeroSkull = Dressed(OssivarFx.Skull, "ModHeroSkull", "FxItemBoneBoomerang", "Fly", 0.7f);
            ItemArt.Puffs(HeroSkull, ItemArt.Visual("ModItemBoomerangChips", "FxItemBoneBoomerang", "Pop"));
            HeroLantern = Dressed(VhorrulFx.LanternOrb, "ModHeroLanternOrb", "FxItemSoulLantern", "Fly", 0.75f);
            HeroBellToll = Dressed(BelMoraFx.BellToll, "ModHeroBellToll", "FxItemBellToll", "Ring", 0.6f);
            HeroRoots = FxKit.Weakened(SylveneFx.RootRunner, "ModHeroRootRunner", 0.8f);
            if (HeroRoots != null)
            {
                FxFactory.SetContacts(HeroRoots, clearSpawnOnHit: true);
                ItemArt.Runner(HeroRoots, "FxItemRootRunner");                                // the burrowing root tip
            }
            // the runner (a WebDropper) deals no damage itself: the hits come from its RootSpike trail, and the
            // lantern's main hit is the LanternBlast it bursts into. Weaken those too or the copies change nothing.
            var heroRootSpike = Dressed(SylveneFx.RootSpike, "ModHeroRootSpike", "FxItemRootSnare", "Play", 0.8f);
            if (HeroRoots != null && heroRootSpike != null)
                foreach (var m in HeroRoots.GetComponents<ParticleMotion>())
                    if (R.Get<GameObject>(m, "m_trailObject") == SylveneFx.RootSpike) R.Set(m, "m_trailObject", heroRootSpike);
            var heroBlast = FxKit.Weakened(VhorrulFx.LanternBlast, "ModHeroLanternBlast", 0.75f);
            if (heroBlast != null)
            {
                // its own 11-frame soul-fire burst (same frame times as the vanilla skydropExplode, so the same damage window)
                FxFactory.StripChildren(heroBlast);
                ItemArt.Wear(heroBlast, "FxItemSoulBurst", "Burst", loop: false);
            }
            if (HeroLantern != null && heroBlast != null)
            {
                var e = HeroLantern.GetComponent<Effect>();
                if (e != null && R.Get<GameObject>(e, "m_spawnOnDestroy") == VhorrulFx.LanternBlast) R.Set(e, "m_spawnOnDestroy", heroBlast);
                // "slows what it passes, then bursts": the monster orb bursts on the first body it touches and never
                // slowed anything. The hero lantern drifts through monsters (light hit + the mod slow on each), bursts
                // at the end of its flight, and still bursts early on a wall.
                FxFactory.SetDamage(HeroLantern, 0.3f, rate: 0.5f, knockback: 0.2f, status: goo, statusChance: 1f, collisionAtStart: true);
                var de = HeroLantern.GetComponent<DamageEffect>();
                int wall = LayerMask.NameToLayer("Wall");
                if (de != null && de.m_contactData != null)
                    foreach (var c in de.m_contactData)
                    {
                        if (c == null) continue;
                        bool isWall = wall >= 0 && (c.m_layerMask.value & (1 << wall)) != 0;
                        c.m_destroyOnHit = isWall;
                        c.m_spawnOnHit = isWall ? heroBlast : null;
                    }
                if (de != null) de.m_spawnOnHit = null;
            }
            SwapToken = FxKit.Inert("ModHeroSwapToken", "FxItemShadowSwap", "Cast");
            ItemArt.Place(SwapToken, "FxItemShadowSwap");
            if (SwapToken != null) FxFactory.OnSpawn[SwapToken] = i => { if (i.GetComponent<SwapTokenFx>() == null) i.AddComponent<SwapTokenFx>(); };
            // Tidecaller Conch: a ring of breaking water (its own art, no longer the Drowned Bell's ring), 56 x 24 on the feet
            TideBurst = FxKit.TimedHit("ModTideBurst", "TrollGroundPoundBigShockwave", "FxItemTideBurst", "Ring", 0, 3, 0.3f, 2.4f, colliderScale: 0.8f, canFlip: false);
            Strike.Collider(TideBurst, 56f, 24f);
            ItemArt.Place(TideBurst, "FxItemTideBurst");
        }

        public static readonly List<ItemDef> Items = new List<ItemDef>
        {
            // ================================================================= skills
            new ItemDef { id = "SpellEmberVolley", cloneFrom = "SpellFetidDischarge", cost = 45, group = "GroupSpellsPurchasable",
                name = "Ember Volley", description = "Fire a fan of flame bolts",
                bubbleArt = "IconEmberVolleyBubble", customize = (go, pu) => AllSpecial(pu, HeroCandleBolt) },
            new ItemDef { id = "SpellWaxSlick", cloneFrom = "SpellFetidDischarge", cost = 35, group = "GroupSpellsPurchasable",
                name = "Wax Slick", description = "Lay trails of wax that slow monsters",
                bubbleArt = "IconWaxSlickBubble", customize = (go, pu) => AllSpecial(pu, HeroDropper("ModHeroWaxRunner", HeroWax, 12f, 0.32f, 150f, "FxItemWaxRunner")) },
            new ItemDef { id = "SpellMarrowSpikes", cloneFrom = "SpellTribalShield", cost = 45, group = "GroupSpellsPurchasable",
                name = "Marrow Spikes", description = "Bone spikes erupt in front of you",
                bubbleArt = "IconMarrowSpikesBubble", customize = (go, pu) => { FirstSpecial(pu, HeroSpikes); var sp = Special(pu); if (sp.Count > 0) sp[0].m_offsetX = new MinMaxRange(18f); } },
            new ItemDef { id = "SpellBoneBoomerang", cloneFrom = "SpellCycloneSummon", cost = 40, group = "GroupSpellsPurchasable",
                name = "Bone Boomerang", description = "Throw a skull that comes back to you",
                bubbleArt = "IconBoneBoomerangBubble", customize = (go, pu) => FirstSpecial(pu, HeroSkull) },
            new ItemDef { id = "SpellSporeBomb", cloneFrom = "SpellCycloneSummon", cost = 35, group = "GroupSpellsPurchasable",
                name = "Spore Bomb", description = "Lob a pod that bursts into a poison cloud on impact",
                bubbleArt = "IconSporeBombBubble", customize = (go, pu) => FirstSpecial(pu, HeroSporeBomb) },
            new ItemDef { id = "SpellRootSnare", cloneFrom = "SpellCycloneSummon", cost = 40, group = "GroupSpellsPurchasable",
                name = "Root Snare", description = "Roots race along the floor and snare monsters",
                bubbleArt = "IconRootSnareBubble", customize = (go, pu) => FirstSpecial(pu, HeroRoots) },
            new ItemDef { id = "SpellShardNova", cloneFrom = "SpellTribalShield", cost = 50, group = "GroupSpellsPurchasable",
                name = "Shard Nova", description = "Mirror shards fly out from you in every direction",
                bubbleArt = "IconShardNovaBubble", customize = (go, pu) => FirstSpecial(pu, ShardNova, atHero: true) },
            new ItemDef { id = "SpellShadowSwap", cloneFrom = "SpellTribalShield", cost = 45, group = "GroupSpellsPurchasable",
                name = "Shadow Swap", description = "Swap places with the nearest monster",
                bubbleArt = "IconShadowSwapBubble", customize = (go, pu) => FirstSpecial(pu, SwapToken, atHero: true) },
            new ItemDef { id = "SpellSoulLantern", cloneFrom = "SpellCycloneSummon", cost = 40, group = "GroupSpellsPurchasable",
                name = "Soul Lantern", description = "Throw a lantern that bursts into flame",
                bubbleArt = "IconSoulLanternBubble", customize = (go, pu) => FirstSpecial(pu, HeroLantern) },
            new ItemDef { id = "SpellBellToll", cloneFrom = "SpellTribalShield", cost = 50, group = "GroupSpellsPurchasable",
                name = "Bell Toll", description = "A shockwave that may stun nearby monsters",
                bubbleArt = "IconBellTollBubble", customize = (go, pu) => FirstSpecial(pu, HeroBellToll, atHero: true) },
            new ItemDef { id = "SpellUndertow", cloneFrom = "SpellCycloneSummon", cost = 40, group = "GroupSpellsPurchasable",
                name = "Undertow", description = "Send a wave that knocks monsters back",
                bubbleArt = "IconUndertowBubble", customize = (go, pu) => FirstSpecial(pu, HeroWave) },
            new ItemDef { id = "SpellRiptide", cloneFrom = "SpellHyperdash", cost = 45, group = "GroupSpellsPurchasable",
                name = "Riptide Dash", description = "Dash forward, leaving a pool of brine",
                bubbleArt = "IconRiptideBubble", customize = (go, pu) => { FirstSpecial(pu, HeroBrine); ItemPack.DashArt(pu, "Riptide", "FxItemRiptideBlur", "FxItemRiptideDrop"); } },
            new ItemDef { id = "SpellWildCard", cloneFrom = "SpellCycloneSummon", cost = 35, group = "GroupSpellsPurchasable",
                name = "Wild Card", description = "Throw a card with a random curse",
                bubbleArt = "IconWildCardSpellBubble", customize = (go, pu) => FirstSpecial(pu, HeroWildCard) },
            new ItemDef { id = "SpellLoadedDice", cloneFrom = "SpellCycloneSummon", cost = 35, group = "GroupSpellsPurchasable",
                name = "Loaded Dice", description = "Throw a die that hits harder the higher it rolls",
                bubbleArt = "IconLoadedDiceBubble", customize = (go, pu) => FirstSpecial(pu, HeroDie) },
            new ItemDef { id = "SpellPuppetStrings", cloneFrom = "SpellFetidDischarge", cost = 35, group = "GroupSpellsPurchasable",
                name = "Puppet Strings", description = "Fire three piercing strings that may stun",
                bubbleArt = "IconPuppetStringsBubble", customize = (go, pu) => AllSpecial(pu, HeroStrings) },

            // ================================================================= artifacts
            new ItemDef { id = "ArtifactEmberHeart", cloneFrom = "ArtifactThornOfWrath", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Ember Heart", description = "Hits may set monsters on fire",
                bubbleArt = "IconEmberHeartBubble", hudArt = "IconEmberHeartHud", customize = Passive(pu => EmberHeart = pu) },
            new ItemDef { id = "ArtifactVenomGland", cloneFrom = "ArtifactThornOfWrath", cost = 35, group = "GroupArtifactsPurchasable",
                name = "Venom Gland", description = "Hits may poison monsters",
                bubbleArt = "IconVenomGlandBubble", hudArt = "IconVenomGlandHud", customize = Passive(pu => VenomGland = pu) },
            new ItemDef { id = "ArtifactRimeRing", cloneFrom = "ArtifactThornOfWrath", cost = 45, group = "GroupArtifactsPurchasable",
                name = "Rime Ring", description = "Hits now and then freeze monsters",
                bubbleArt = "IconRimeRingBubble", hudArt = "IconRimeRingHud", customize = Passive(pu => RimeRing = pu) },
            new ItemDef { id = "ArtifactLeechSeed", cloneFrom = "ArtifactThornOfWrath", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Leech Seed", description = "Each monster you kill heals you a little",
                bubbleArt = "IconLeechSeedBubble", hudArt = "IconLeechSeedHud", customize = Passive(pu => LeechSeed = pu) },
            new ItemDef { id = "ArtifactThornMail", cloneFrom = "PowerupAcidBlood", cost = 35, group = "GroupArtifactsPurchasable",
                name = "Thorn Mail", description = "Thorns burst from the floor when you are hit",
                bubbleArt = "IconThornMailBubble", hudArt = "IconThornMailHud",
                customize = (go, pu) =>
                {
                    var e = Effects(pu);
                    // effect 0 (at the feet) is the patch; effect 1 used to spawn a second patch on the same spot (double damage)
                    var mail = Dressed(SylveneFx.ThornPatch, "ModItemThornMail", "FxItemThornMail", "Life");   // iron thorns, same 0.5 / 0.6 s
                    for (int i = 0; i < e.Count && i < 2; i++) { var d = e[i] as DamageEffectData; if (d != null) { d.m_object = i == 0 ? (mail ?? SylveneFx.ThornPatch) : null; d.m_attach = false; } }
                } },
            new ItemDef { id = "ArtifactSaintsWick", cloneFrom = "ArtifactSpellbookTears", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Saint's Wick", description = "A floating candle shoots flames at your foes",
                bubbleArt = "IconSaintsWickBubble", hudArt = "IconSaintsWickHud",
                customize = (go, pu) =>
                {
                    // its own copy of the hero bolt, turned toward the nearest monster as it leaves the candle
                    var bolt = ItemFixes.HeroCopy(HeroCandleBolt, "ModHeroWickBolt");
                    ItemArt.Wear(bolt, "FxItemWickBolt", "Fly", loop: true);                   // a holy candle flame, not Ember Volley's
                    ItemArt.Puffs(bolt, WickPop);
                    ItemFixes.AimAtMonsters(bolt, 220f);
                    ItemFixes.Follower(go, pu, "FxItemTokenWick", 8f, bolt);
                } },
            new ItemDef { id = "ArtifactLuckyDie", cloneFrom = "ArtifactThornOfWrath", cost = 45, group = "GroupArtifactsPurchasable",
                name = "Lucky Die", description = "Now and then a hit misses you completely",
                bubbleArt = "IconLuckyDieBubble", hudArt = "IconLuckyDieHud", customize = Passive(pu => LuckyDie = pu) },
            new ItemDef { id = "ArtifactAshHourglass", cloneFrom = "ArtifactThornOfWrath", cost = 35, group = "GroupArtifactsPurchasable",
                name = "Hourglass of Ash", description = "Spells recharge faster, but you move slower",
                bubbleArt = "IconAshHourglassBubble", hudArt = "IconAshHourglassHud",
                customize = Passive(pu => AshHourglass = pu, Mul(PlayerModifier.eType.HeroSpecialChargeTime, 0.75f), Mul(PlayerModifier.eType.HeroSpeed, 0.9f)) },
            new ItemDef { id = "ArtifactGlassMask", cloneFrom = "ArtifactThornOfWrath", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Glass Mask", description = "Deal more damage, but take even more",
                bubbleArt = "IconGlassMaskBubble", hudArt = "IconGlassMaskHud",
                customize = Passive(pu => GlassMask = pu, Mul(PlayerModifier.eType.HeroDamage, 1.25f), Mul(PlayerModifier.eType.PowerupDamage, 1.25f),
                                    Mul(PlayerModifier.eType.HeroDamageResistance, 0.74f)) },
            new ItemDef { id = "ArtifactBarnacleShell", cloneFrom = "ArtifactThornOfWrath", cost = 35, group = "GroupArtifactsPurchasable",
                name = "Barnacle Shell", description = "Take less damage while standing still",
                bubbleArt = "IconBarnacleShellBubble", hudArt = "IconBarnacleShellHud", customize = Passive(pu => BarnacleShell = pu) },
            new ItemDef { id = "ArtifactTidecaller", cloneFrom = "ArtifactThornOfWrath", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Tidecaller Conch", description = "Waves burst out of you, knocking monsters back",
                bubbleArt = "IconTidecallerBubble", hudArt = "IconTidecallerHud", customize = Passive(pu => Tidecaller = pu) },
            new ItemDef { id = "ArtifactBrineFlask", cloneFrom = "ArtifactThornOfWrath", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Brine Flask", description = "Regenerate health when badly hurt",
                bubbleArt = "IconBrineFlaskBubble", hudArt = "IconBrineFlaskHud", customize = Passive(pu => BrineFlask = pu) },
            new ItemDef { id = "ArtifactJestersBell", cloneFrom = "ArtifactThornOfWrath", cost = 45, group = "GroupArtifactsPurchasable",
                name = "Jester's Bell", description = "Every few hits strike extra hard",
                bubbleArt = "IconJestersBellBubble", hudArt = "IconJestersBellHud", customize = Passive(pu => JestersBell = pu) },
            new ItemDef { id = "ArtifactJokersWild", cloneFrom = "ArtifactThornOfWrath", cost = 35, group = "GroupArtifactsPurchasable",
                name = "Joker's Wild", description = "Kills may grant you a random boon",
                bubbleArt = "IconJokersWildBubble", hudArt = "IconJokersWildHud", customize = Passive(pu => JokersWild = pu) },
            new ItemDef { id = "ArtifactMarionetteCross", cloneFrom = "ArtifactThornOfWrath", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Marionette Cross", description = "Monsters that hit you are stunned",
                bubbleArt = "IconMarionetteCrossBubble", hudArt = "IconMarionetteCrossHud", customize = Passive(pu => MarionetteCross = pu) },
        };

        public static void Register()
        {
            try { BuildFx(); } catch (Exception e) { Plugin.Log.LogError("Item FX failed: " + e); }
            foreach (var def in Items)
            {
                try { ItemRegistry.Register(def); }
                catch (Exception e) { Plugin.Log.LogError("Item " + def.id + " failed: " + e); }
            }
            ItemPack.Items.AddRange(Items);   // so the self-test counts them
        }
    }

    /// <summary>Shadow Swap: on spawn, trade the hero's place with the nearest monster and leave it dizzy.</summary>
    public class SwapTokenFx : MonoBehaviour
    {
        bool m_done;
        void OnEnable() { m_done = false; }
        void Update()
        {
            if (m_done) return;
            m_done = true;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 hp = hero.transform.position;
            Player best = null; float bd = 140f * 140f;
            foreach (var p in FindObjectsOfType<Player>())
            {
                if (p == null || p.gameObject == hero || R.Get<bool>(p, "m_isGhost")) continue;
                // any monster (in Crawl they are almost all ghost-controlled), but never a boss or boss part
                if (p.GetComponentInParent<Boss>() != null) continue;
                var h = p.GetComponent<Health>();
                if (h == null || !h.IsAlive() || h.GetHealthMax() > 30f) continue;
                float d = ((Vector2)p.transform.position - hp).sqrMagnitude;
                if (d < bd) { bd = d; best = p; }
            }
            if (best == null) return;
            Vector2 them = best.transform.position;
            var flash = ItemPack2.SwapFlash ?? UmbraelFx.SwapFlash;
            if (flash != null) { SystemPool.Spawn(flash, hp); SystemPool.Spawn(flash, them); }
            ModUtil.Teleport(best.gameObject, hp);
            ModUtil.Teleport(hero, them);
            var dizzy = FxFactory.GetStatus("StatusDizzy");
            if (dizzy != null) best.AddStatus(dizzy, ModUtil.HeroSource(), "modshadowswap");
        }
    }

    /// <summary>Hero-side logic for the v2 artifacts that need code.</summary>
    public class HeroPerks2 : MonoBehaviour
    {
        Player m_player;
        Health m_health;
        int m_hits;
        float m_still, m_tide, m_regen, m_crackAt;
        Vector3 m_lastPos;
        GameObject m_shell;
        bool m_wasSpecial;
        static readonly System.Reflection.FieldInfo s_state = HarmonyLib.AccessTools.Field(typeof(Player), "m_state");

        void Awake() { m_player = GetComponent<Player>(); m_health = GetComponent<Health>(); }
        // a Joker's Wild boon cut short (death, level change) must not leave its modifier on the player for good
        void OnEnable() { m_hits = 0; m_still = 0f; m_tide = 12f; ClearBoon(); }
        void OnDisable() { ClearBoon(); Shell(false); }

        /// <summary>Barnacle Shell: the crust closes round the hero's legs while the damage cut is live.</summary>
        void Shell(bool on)
        {
            if (m_shell != null && !m_shell.activeInHierarchy) m_shell = null;
            if (on && m_shell == null && ItemPack2.BarnacleLoop != null)
            {
                var p = transform.position + new Vector3(0f, -0.5f, 0f);        // just in front of the hero sprite
                m_shell = SystemPool.Spawn(ItemPack2.BarnacleLoop, p);
                if (m_shell != null) m_shell.transform.parent = transform;
            }
            else if (!on && m_shell != null) { if (m_shell.activeInHierarchy) SystemPool.Despawn(m_shell); m_shell = null; }
        }
        void ClearBoon() { var gd = Data != null ? Data.GameData : null; if (gd != null) gd.RemoveModifiers("modjokerswild"); }
        PlayerData Data { get { return m_player != null ? m_player.GetPlayerData() : null; } }
        bool Has(Powerup pu) { return HeroPerks.Has(Data, pu); }

        void Update()
        {
            var pd = Data;
            if (pd == null || !pd.IsHero || m_health == null || !m_health.IsAlive()) return;
            m_still = (transform.position - m_lastPos).sqrMagnitude < 0.05f ? m_still + Time.deltaTime : 0f;
            m_lastPos = transform.position;
            Shell(Has(ItemPack2.BarnacleShell) && m_still > 1f);
            // Hourglass of Ash: the glass turns over as a spell is cast
            if (s_state != null && m_player != null)
            {
                bool special = (Player.ePlayerState)s_state.GetValue(m_player) == Player.ePlayerState.AttackSpecial;
                if (special && !m_wasSpecial && Has(ItemPack2.AshHourglass)) ItemArt.Pop(ItemPack2.HourglassTurn, transform.position);
                m_wasSpecial = special;
            }
            if (Has(ItemPack2.Tidecaller))
            {
                m_tide -= Time.deltaTime;
                if (m_tide <= 0f && ModUtil.DoorsLocked())
                {
                    m_tide = 12f;
                    if (ItemPack2.TideBurst != null) FxFactory.SpawnOwned(ItemPack2.TideBurst, transform.position, ModUtil.HeroSource());
                }
            }
            if (Has(ItemPack2.BrineFlask) && m_health.GetHealthCurrent() < m_health.GetHealthMax() * 0.5f)
            {
                m_regen += Time.deltaTime * 0.06f;
                if (m_regen >= 0.1f) { m_health.Heal(m_regen); m_regen = 0f; ItemArt.Pop(ItemPack2.BrineRegen, transform.position); }
            }
        }

        /// <summary>Damage the hero is about to take: may be dodged or reduced. Returns the new amount.</summary>
        public float OnIncoming(float amount, GameObject attacker)
        {
            if (Has(ItemPack2.LuckyDie) && UnityEngine.Random.value < 0.10f)
            {
                ItemArt.Pop(ItemPack2.LuckyDodge, transform.position);
                // the readout: a gold DODGE just over the flipped die (the Dodge art reaches 33 px above the feet)
                FloatNumber.Show("DODGE", NumberTone.Max, (Vector2)transform.position + new Vector2(0f, 35f), gameObject);
                return 0f;
            }
            if (Has(ItemPack2.BarnacleShell) && m_still > 1f) amount *= 0.65f;
            if (attacker != null && Has(ItemPack2.MarionetteCross))
            {
                var p = attacker.GetComponent<Player>();
                var dizzy = FxFactory.GetStatus("StatusDizzy");
                if (p != null && dizzy != null)
                {
                    p.AddStatus(dizzy, ModUtil.HeroSource(), "modmarionette");
                    ItemArt.Pop(ItemPack2.MarionetteTug, p.transform.position);
                }
            }
            if (amount > 0f && Has(ItemPack2.GlassMask) && Time.time - m_crackAt > 0.4f)
            {
                m_crackAt = Time.time;
                ItemArt.Pop(ItemPack2.GlassCrack, transform.position);
            }
            return amount;
        }

        /// <summary>Damage the hero is about to deal to a monster: Jester's Bell crits.</summary>
        public float OnOutgoing(float amount)
        {
            if (!Has(ItemPack2.JestersBell)) return amount;
            if (++m_hits % 6 != 0) return amount;
            ItemArt.Pop(ItemPack2.JesterCrit, transform.position);
            return amount * 2f;
        }

        public void OnHitMonster(Player victim)
        {
            if (victim == null) return;
            var src = ModUtil.HeroSource();
            if (Has(ItemPack2.EmberHeart) && UnityEngine.Random.value < 0.20f) Afflict(victim, "StatusOnFire", src, ItemPack2.EmberProc);
            if (Has(ItemPack2.VenomGland) && UnityEngine.Random.value < 0.25f) Afflict(victim, "StatusPoisoned", src, ItemPack2.VenomProc);
            if (Has(ItemPack2.RimeRing) && UnityEngine.Random.value < 0.08f) Afflict(victim, "StatusFrozen", src, ItemPack2.RimeProc);
        }

        /// <summary>Apply the item's status, with the item's own flare on the monster's body.</summary>
        static void Afflict(Player p, string status, DamageSource src, GameObject flare)
        {
            var st = FxFactory.GetStatus(status);
            if (st == null) return;
            p.AddStatus(st, src, "moditem");
            ItemArt.Pop(flare, ItemFixes.AimPoint(p.gameObject));
        }

        public void OnKill()
        {
            if (Has(ItemPack2.LeechSeed) && m_health != null) { m_health.Heal(0.15f); ItemArt.Pop(ItemPack2.LeechHeal, transform.position); }
            if (Has(ItemPack2.JokersWild) && UnityEngine.Random.value < 0.20f) StartCoroutine(Boon());
        }

        System.Collections.IEnumerator Boon()
        {
            int suit = UnityEngine.Random.Range(0, 4);
            // the item's own card flips up over the hero and turns to the suit it dealt
            var fx = ItemArt.Pop(ItemPack2.JokerFlip, transform.position);
            var anim = fx != null ? fx.GetComponent<exSpriteAnimation>() : null;
            var face = ItemPack2.JokerSuits[suit];
            if (anim != null && face != null)
            {
                yield return new WaitForSeconds(0.32f);
                if (anim != null) ItemArt.Ensure(anim, face, true);
            }
            var gd = Data != null ? Data.GameData : null;
            switch (suit)
            {
                case 0: if (m_health != null) { m_health.Heal(0.5f); ModInd.Heal(gameObject); } break;
                case 2:
                    var perks = GetComponent<HeroPerks>();
                    if (perks != null) perks.AddPlate();
                    break;
                default:
                    if (gd == null) break;
                    var mod = suit == 1 ? PlayerModifier.eType.HeroDamage : PlayerModifier.eType.HeroSpeed;
                    gd.AddBaseModifier("modjokerswild", new PlayerModifier { m_modify = mod, m_type = ValueModifier.eModifierType.Multiply, m_value = suit == 1 ? 1.5f : 1.3f });
                    // the boon shows on the hero for its whole 4 s: a red chevron (damage) or a wind ring (speed)
                    if (suit == 1) ModInd.Might(gameObject, true, 4f); else ModInd.Haste(gameObject, true, 4f);
                    yield return new WaitForSeconds(4f);
                    gd.RemoveModifiers("modjokerswild");
                    if (suit == 1) ModInd.Might(gameObject, false); else ModInd.Haste(gameObject, false);
                    break;
            }
        }
    }

    /// <summary>Hero blows that connect: on-hit artifact effects.</summary>
    [HarmonyPatch(typeof(Player), "MsgOnAttackContact")]
    static class Patch_HeroAttackContact
    {
        static void Postfix(Player __instance, DamageInfo damage)
        {
            try
            {
                if (damage == null || damage.m_victim == null || damage.m_isDamageFromStatus) return;
                var perks = __instance.GetComponent<HeroPerks2>();
                if (perks == null) return;
                var victim = damage.m_victim.GetComponent<Player>();
                if (victim == null || R.Get<bool>(victim, "m_isHero")) return;
                perks.OnHitMonster(victim);
            }
            catch { }
        }
    }
}
