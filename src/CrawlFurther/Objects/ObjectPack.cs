using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Objects
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Objects;
    using CrawlFurther.Util;

    /// <summary>
    /// Fifteen room objects built on ObjectKit (art: tools/sprites/objects_rigs.py -> art/out_objects,
    /// timings and spawn points in art/out_objects/TIMING.md).
    ///
    /// Traps (a ghost steps in, aims and fires; bots use them like vanilla traps; damage is the ghost player's trap damage):
    ///   Chain Winch, Steam Vent, Tar Spout, Pendulum Blade, Rune Plate, Toll Bell, Scatter Idol.
    /// Floor hazards (walk onto them): Iron Snare, Warp Stones (a linked pair).
    /// Interactables (press action): Mending Spring, Weapon Rack, Cursed Altar, Ward Shrine, Spirit Urn, Strongbox.
    ///
    /// Balance against vanilla traps (dart turret: 1 damage, 0.5 s cooldown; floor spikes 1; trap budget 1 per dart turret):
    /// these hit 0.4-1.2, have 1.2-4.5 s cooldowns because each adds a control effect (pull, push, slow, daze), and cost
    /// 1.0-1.5 of the room's trap budget. Hero-side interactables are one-use, outside fights, and each has a cost or a
    /// risk; the strongest (Ward Shrine) costs gold.
    /// </summary>
    public static class ObjectPack
    {
        // effect templates
        public static GameObject Hook, Steam, TarGlob, TarPool, PendHit, RuneCharge, RuneBurst, TollWave, Dart;
        public static GameObject HookYank, WarpFlash, UrnBurst, MimicCoins;
        public static StatusOverlayDef IndCurse, IndWard;
        static bool s_done;

        public const float HookDamage = 0.4f, HookRange = 80f;
        public const float SteamDamage = 0.6f, SteamKnock = 1.8f;
        public const float TarDamage = 0.4f;
        public const float PendDamage = 1.0f;
        public const float RuneDamage = 1.2f;
        public const float TollDamage = 0.3f;
        public const float DartDamage = 0.6f;
        public const float SnareDamage = 0.5f, SnareRearm = 6f;
        public const float SpringHeal = 3f, SpringTime = 6f;
        public const float CurseMult = 1.3f;
        public const float WardTime = 15f;
        public const int WardCost = 30;
        public const int UrnGold = 20;
        public const int BoxGoldMin = 30, BoxGoldMax = 55, MimicGold = 15;
        public const float MimicBite = 1f, MimicChance = 0.25f;

        public static void Register()
        {
            if (s_done) return;
            s_done = true;
            BuildFx();
            foreach (var d in Defs())
            {
                try { ObjectKit.Register(d); }
                catch (Exception e) { Plugin.Log.LogError("ObjectPack " + d.id + ": " + e); }
            }
            Strike.KeepAllScales();
            Plugin.Log.LogInfo("ObjectPack: " + ObjectKit.Built.Count + " objects registered so far");
        }

        // ================================================================================================= effects
        static void BuildFx()
        {
            var slow = FxFactory.GetStatus("StatusLavaSteveGoo");   // the mod's timed slow (1 s, diminishing)
            var daze = FxFactory.GetStatus("StatusDizzy");          // the mod's daze (0.6 s, diminishing)

            // Chain Winch hook: a floor-level projectile (like the vanilla dart) that yanks the hero to the winch
            Hook = FxKit.Projectile("ModObjHook", "DFXTrapProjectile1", "FxObjHook", "Fly", 210f, HookRange / 210f, HookDamage, 0.05f);
            if (Hook != null)
            {
                FxFactory.StripChildren(Hook);
                Strike.ArtAt(Hook, "FxObjHook", 12, 7);
                FxFactory.OnSpawn[Hook] = i => { var h = i.GetComponent<ObjHookFx>() ?? i.AddComponent<ObjHookFx>(); h.Arm(); };
            }
            HookYank = FxKit.Visual("ModObjHookYank", "FxObjHook", "Yank");
            if (HookYank != null) { var s = HookYank.GetComponent<exSprite>(); if (s != null) { s.anchor = exPlane.Anchor.MidCenter; s.offset = Vector2.zero; } }

            // Steam Vent jet: a floor hitbox 38 x 10 running out from the vent mouth, turned with the aim
            Steam = FxKit.TimedHit("ModObjSteam", "TrollGroundPoundBigShockwave", "FxObjSteam", "Blast", 1, 5, SteamDamage, SteamKnock, canFlip: false);
            if (Steam != null)
            {
                Strike.Ground(Steam, "FxObjSteam", 4, 15, 36f, 10f);
                Strike.Collider(Steam, 36f, 10f, 20f, 0f);
                FxFactory.SetEffect(Steam, destroyOnAnimEnd: true, canFlip: false, freeRotate: true);
            }

            // Tar Spout: a glob along the floor that splats into a slowing tar puddle
            TarPool = FxFactory.Clone("LavaEffectLongerReworkZone", "ModObjTarPool");
            if (TarPool != null)
            {
                var sh = SpriteSheets.Get("FxObjTar");
                var clip = new ClipBuilder(sh, "Pool", "ModObjTarPoolLife").Once().Then("Fade")
                    .Ev(1, "AnimDamageOn").Ev(-3, "AnimDamageOff").Build();
                FxFactory.Reskin(TarPool, clip, sh);
                FxFactory.SetEffect(TarPool, destroyOnAnimEnd: true, offsetX: 0f, snap: 1f);
                FxFactory.SetStatusZone(TarPool, slow, hitsHero: true, hitsMonster: false);
                FxKit.NoTint(TarPool);
                Strike.Ground(TarPool, "FxObjTar", 16, 7, 24f, 9f);
            }
            TarGlob = FxFactory.Clone("webBall", "ModObjTarGlob");
            if (TarGlob != null)
            {
                var sh = SpriteSheets.Get("FxObjTar");
                FxFactory.Reskin(TarGlob, new ClipBuilder(sh, "Fly", "ModObjTarGlobFly").Repeat(4).Once().Build(), sh);
                FxFactory.SetEffect(TarGlob, destroyOnAnimEnd: true, spawnOnDestroy: TarPool, freeRotate: false);
                FxFactory.SetMotion(TarGlob, speed: 180f, accel: 20f, speedMax: 8f, collide: true, bounce: 0.2f);
                FxFactory.SetDamage(TarGlob, TarDamage, knockback: 0.2f, collisionAtStart: true);
                FxFactory.SetContacts(TarGlob, destroyOnHit: true, spawnOnHit: TarPool);
                Strike.ArtAt(TarGlob, "FxObjTar", 16, 7 + 6);   // the glob rides 6 px over its floor point
                FxKit.NoTint(TarGlob);
            }

            // Pendulum: the blade (drawn in the trap's own swing) cuts an invisible 24 x 8 strip of floor under the frame
            PendHit = FxFactory.Clone("DFX_InvisibleFloorSpikes", "ModObjPendulumCut");
            if (PendHit != null)
            {
                FxFactory.SetEffect(PendHit, destroyOnAnimEnd: false, destroyAfter: 0.22f, freeRotate: false, canFlip: false);
                FxFactory.SetDamage(PendHit, PendDamage, rate: 0f, knockback: 0.9f, collisionAtStart: true, nullifyable: true);
                Strike.HitBox(PendHit, 24f, 8f, 0f, 0f);
            }

            // Rune Plate: runes rise for 0.7 s, then a ring of fire bursts out (36 x 16 footprint)
            RuneBurst = FxKit.TimedHit("ModObjRuneBurst", "TrollGroundPoundBigShockwave", "FxObjRune", "Burst", 1, 4, RuneDamage, 0.8f, canFlip: false);
            if (RuneBurst != null) Strike.Ground(RuneBurst, "FxObjRune", 22, 14, 36f, 16f);
            RuneCharge = FxKit.Inert("ModObjRuneCharge", "FxObjRune", "Charge", destroyOnAnimEnd: true, spawnOnDestroy: RuneBurst);
            if (RuneCharge != null) Strike.ArtAt(RuneCharge, "FxObjRune", 22, 14);

            // Toll Bell: a wave of sound over the floor round the bell (60 x 28): a little damage and a daze
            TollWave = FxKit.TimedHit("ModObjTollWave", "TrollGroundPoundBigShockwave", "FxObjToll", "Wave", 1, 5, TollDamage, 0.4f, daze, 1f, canFlip: false);
            if (TollWave != null) Strike.Ground(TollWave, "FxObjToll", 36, 18, 60f, 28f);

            // Scatter Idol dart
            Dart = FxKit.Projectile("ModObjDart", "DFXTrapProjectile1", "FxObjDart", "Fly", 190f, 0.9f, DartDamage, 0.2f);
            if (Dart != null) { FxFactory.StripChildren(Dart); Strike.ArtAt(Dart, "FxObjDart", 8, 4); }

            // visuals
            WarpFlash = FxKit.Visual("ModObjWarpFlash", "FxObjWarp", "Flash");
            if (WarpFlash != null) Strike.ArtAt(WarpFlash, "FxObjWarp", 12, 36);
            UrnBurst = FxKit.Visual("ModObjUrnBurst", "FxObjUrn", "Burst");
            if (UrnBurst != null) Strike.ArtAt(UrnBurst, "FxObjUrn", 14, 18 + 8);
            MimicCoins = FxKit.Visual("ModObjMimicCoins", "FxObjMimic", "Coins");
            if (MimicCoins != null) Strike.ArtAt(MimicCoins, "FxObjMimic", 18, 22 + 10);

            IndCurse = ModStatus.Indicator("ModIndObjCurse", "FxObjIndCurse", "Loop", 1f, OverlayAt.Head);
            IndWard = ModStatus.Indicator("ModIndObjWard", "FxObjIndWard", "Loop", -4f, OverlayAt.Feet);
        }

        static ObjEffect Fx(GameObject fx, int frame, float x, float y, float angle = 0f, float delay = 0f)
        {
            return new ObjEffect { fx = fx, frame = frame, x = x, y = y, angle = angle, delay = delay };
        }

        static ObjTrapAttack Attack(string anim, float cooldown, params ObjEffect[] fx)
        {
            var a = new ObjTrapAttack { anim = anim, cooldown = cooldown };
            a.effects.AddRange(fx);
            return a;
        }

        const float Floor = -7.5f;   // effect y from the trap node (0, 7): the floor, where vanilla trap darts fly

        static readonly float[] Eight = { 0f, 45f, 90f, 135f, 180f, 225f, 270f, 315f };

        // ================================================================================================= defs
        static IEnumerable<ObjectDef> Defs()
        {
            // ---------------------------------------------------------------- traps
            yield return new ObjectDef
            {
                id = "ChainHook", name = "Chain Winch", art = "ObjChainHook", kind = ObjKind.Trap,
                vault = "An iron winch that reels in what its hook catches",
                tip1 = "Hook: drags the hero back to the winch",
                tip2 = "Aim with movement. Long reach, slow reload",
                attacks = { Attack("Action", 2.5f, Fx(Hook, 1, 2f, Floor)) },
                snap = 7.5f, difficulty = 1.2f, enterArrowY = 18f,
                bodySize = new Vector2(12f, 4f), bodyY = 1f,
                spawn = new ObjSpawn { weight = 8f, minFloor = 1, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Trapped | ObjRoom.Statue | ObjRoom.Stairs, place = ObjPlace.Wall, maxPerFloor = 1 },
            };
            yield return new ObjectDef
            {
                id = "SteamVent", name = "Steam Vent", art = "ObjSteamVent", kind = ObjKind.Trap,
                vault = "A boiler grate full of scalding steam",
                tip1 = "Blast: a scalding jet and a hard shove",
                tip2 = "Aims in eight directions",
                attacks = { Attack("Action", 2f, Fx(Steam, 1, 4f, Floor)) },
                angles = Eight, difficulty = 1.0f, enterArrowY = 14f,
                bodySize = new Vector2(16f, 4f), bodyY = 1f,
                spawn = new ObjSpawn { weight = 8f, minFloor = 1, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Trapped | ObjRoom.Stairs, place = ObjPlace.Anywhere, env = ObjEnv.Dungeon | ObjEnv.Mines | ObjEnv.Caves },
            };
            yield return new ObjectDef
            {
                id = "TarSpout", name = "Tar Spout", art = "ObjTarSpout", kind = ObjKind.Trap,
                vault = "A pot of boiling tar",
                tip1 = "Glob: leaves a pool of tar where it lands",
                tip2 = "The pool slows the hero",
                attacks = { Attack("Action", 3f, Fx(TarGlob, 1, 6f, Floor)) },
                snap = 15f, difficulty = 1.0f, enterArrowY = 18f,
                bodySize = new Vector2(12f, 4f), bodyY = 1f,
                spawn = new ObjSpawn { weight = 7f, minFloor = 2, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Trapped | ObjRoom.Stairs, place = ObjPlace.Wall },
            };
            yield return new ObjectDef
            {
                id = "Pendulum", name = "Pendulum Blade", art = "ObjPendulum", kind = ObjKind.Trap,
                vault = "A crescent blade on a gallows frame",
                tip1 = "Swing: a heavy blade under the frame",
                tip2 = "Swings back the other way",
                attacks = { Attack("SwingL", 1.2f, Fx(PendHit, 3, 0f, Floor)), Attack("SwingR", 1.2f, Fx(PendHit, 3, 0f, Floor)) },
                aims = false, difficulty = 1.3f, enterArrowY = 27f, node = new Vector2(0f, 7f),
                bodySize = new Vector2(4f, 3f), bodyY = 0.5f,   // the posts are solid; the space under the beam is open
                spawn = new ObjSpawn { weight = 6f, minFloor = 2, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Trapped | ObjRoom.Corridor, place = ObjPlace.Open },
                customize = PendulumPosts,
            };
            yield return new ObjectDef
            {
                id = "RunePlate", name = "Rune Plate", art = "ObjRunePlate", kind = ObjKind.Trap,
                vault = "A floor plate carved with fire runes",
                tip1 = "Rune: a pause, then a ring of fire",
                tip2 = "The fire rings the plate",
                attacks = { Attack("Action", 3f, Fx(RuneCharge, 0, 0f, Floor)) },
                aims = false, difficulty = 1.2f, enterArrowY = 8f,
                bodySize = Vector2.zero,
                spawn = new ObjSpawn { weight = 7f, minFloor = 1, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Trapped | ObjRoom.Corridor, place = ObjPlace.Open, env = ObjEnv.Crypt | ObjEnv.Dungeon | ObjEnv.Caves },
            };
            yield return new ObjectDef
            {
                id = "TollBell", name = "Toll Bell", art = "ObjTollBell", kind = ObjKind.Trap,
                vault = "A cracked bronze bell. Its toll rattles skulls",
                tip1 = "Toll: dazes a hero close by",
                tip2 = "Ring it as the hero comes close",
                attacks = { Attack("Action", 4.5f, Fx(TollWave, 1, 0f, Floor)) },
                aims = false, difficulty = 1.5f, enterArrowY = 24f,
                bodySize = new Vector2(10f, 4f), bodyY = 1f,
                spawn = new ObjSpawn { weight = 6f, minFloor = 2, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Trapped | ObjRoom.Statue, place = ObjPlace.Open },
            };
            yield return new ObjectDef
            {
                id = "ScatterIdol", name = "Scatter Idol", art = "ObjScatterIdol", kind = ObjKind.Trap,
                vault = "A grinning stone head that spits bone darts",
                tip1 = "Spit: three bone darts in a fan",
                tip2 = "Aim with movement",
                attacks = { Attack("Action", 1.6f, Fx(Dart, 2, 3f, Floor, -16f), Fx(Dart, 2, 3f, Floor), Fx(Dart, 2, 3f, Floor, 16f)) },
                snap = 15f, difficulty = 1.4f, enterArrowY = 22f,
                bodySize = new Vector2(8f, 4f), bodyY = 1f,
                spawn = new ObjSpawn { weight = 7f, minFloor = 2, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Trapped | ObjRoom.Statue | ObjRoom.Stairs, place = ObjPlace.Wall },
            };

            // ---------------------------------------------------------------- hazards
            var snare = new ObjectDef
            {
                id = "IronSnare", name = "Iron Snare", art = "ObjIronSnare", kind = ObjKind.Touch,
                vault = "Steel jaws hidden in the dust",
                tip1 = "Step in: it bites and holds you",
                tip2 = "Catches heroes and monsters, then resets",
                users = ObjUser.Living, uses = 0, rearm = 1f, touchRadius = 5f, offDuringFight = false,
                useSound = "SoundPropAction", bodySize = Vector2.zero, bounce = false,
                spawn = new ObjSpawn { weight = 8f, minFloor = 1, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Corridor | ObjRoom.Trapped | ObjRoom.Stairs, place = ObjPlace.Anywhere, maxPerFloor = 2 },
                onUse = u =>
                {
                    u.obj.Play("Snap");
                    u.obj.Spent();
                    u.Hurt(SnareDamage);
                    u.Status(ModStatus.Root ?? FxFactory.GetStatus("StatusStuckToFloor"), "modobjsnare");
                    var o = u.obj;
                    o.After(SnareRearm, () => o.Rearm("Reset"));
                },
            };
            snare.once.Add("Snap"); snare.once.Add("Reset");
            snare.then["Snap"] = "Sprung"; snare.then["Reset"] = "Idle";
            yield return snare;

            yield return new ObjectDef
            {
                id = "WarpStone", name = "Warp Stones", art = "ObjWarpStone", kind = ObjKind.Touch,
                vault = "Two sister stones",
                tip1 = "Step on a stone to appear on its twin",
                tip2 = "Heroes and monsters. A short wait to go back",
                users = ObjUser.Living, uses = 0, rearm = 1.5f, touchRadius = 5f, offDuringFight = false,
                useSound = "SoundPropActivate", bodySize = Vector2.zero, bounce = false,
                spawn = new ObjSpawn { weight = 6f, minFloor = 2, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Statue, place = ObjPlace.Open, pair = true },
                canUse = u => u.obj != null && u.obj.partner != null && u.obj.partner.gameObject.activeInHierarchy,
                onUse = Warp,
            };

            // ---------------------------------------------------------------- interactables
            yield return new ObjectDef
            {
                id = "MendSpring", name = "Mending Spring", art = "ObjMendSpring", kind = ObjKind.Use,
                vault = "A mossy basin of cold spring water",
                tip1 = "Drink: heal over time",
                tip2 = "One drink, for the hero, outside a fight",
                users = ObjUser.Hero, actionText = "DRINK", uses = 1, useSound = "SoundPropActivate",
                useBox = new Vector2(30f, 22f), bodySize = new Vector2(14f, 5f),
                spawn = new ObjSpawn { weight = 9f, minFloor = 2, rooms = ObjRoom.Quiet | ObjRoom.Statue | ObjRoom.Stairs, place = ObjPlace.Open },
                onUse = u => ObjectKit.Run(HealOverTime(u.Body, SpringHeal, SpringTime)),
            };
            yield return new ObjectDef
            {
                id = "WeaponRack", name = "Weapon Rack", art = "ObjWeaponRack", kind = ObjKind.Use,
                vault = "A rack of old arms nobody came back for",
                tip1 = "Swap for a random weapon of like worth",
                tip2 = "It may be a little worse, or a lot better",
                users = ObjUser.Hero, actionText = "SWAP", uses = 1, useSound = "SoundPropActivate",
                useBox = new Vector2(30f, 22f), bodySize = new Vector2(16f, 4f),
                spawn = new ObjSpawn { weight = 6f, minFloor = 2, rooms = ObjRoom.Quiet | ObjRoom.Stairs | ObjRoom.Statue, place = ObjPlace.Open },
                canUse = u => u.player != null,
                onUse = SwapWeapon,
            };
            yield return new ObjectDef
            {
                id = "CursedAltar", name = "Cursed Altar", art = "ObjCursedAltar", kind = ObjKind.Use,
                vault = "A black altar under a horned skull",
                tip1 = "Deal more damage, and take more",
                tip2 = "Lasts the rest of the floor. One offering",
                users = ObjUser.Hero, actionText = "OFFER", uses = 1, useSound = "SoundPropActivate",
                useBox = new Vector2(30f, 22f), bodySize = new Vector2(16f, 5f),
                spawn = new ObjSpawn { weight = 5f, minFloor = 3, rooms = ObjRoom.Quiet | ObjRoom.Statue, place = ObjPlace.Open },
                onUse = Curse,
            };
            yield return new ObjectDef
            {
                id = "WardShrine", name = "Ward Shrine", art = "ObjWardShrine", kind = ObjKind.Use,
                vault = "A wayside shrine. One coin, one blessing",
                tip1 = "Pay gold to take less damage",
                tip2 = "Lasts into your next fight",
                users = ObjUser.Hero, actionText = "PRAY", uses = 1, costGold = WardCost, useSound = "SoundPropActivate",
                useBox = new Vector2(30f, 22f), bodySize = new Vector2(12f, 4f),
                spawn = new ObjSpawn { weight = 6f, minFloor = 2, rooms = ObjRoom.Quiet | ObjRoom.Fight | ObjRoom.Statue, notRooms = ObjRoom.Stairs, place = ObjPlace.Open },   // not Stairs: a new floor clears object buffs
                onUse = Ward,
            };
            yield return new ObjectDef
            {
                id = "SpiritUrn", name = "Spirit Urn", art = "ObjSpiritUrn", kind = ObjKind.Use,
                vault = "A sealed funeral urn, humming with ectoplasm",
                tip1 = "Ghosts: smash it to fill your ectoplasm",
                tip2 = "The hero can smash it first for gold",
                users = ObjUser.Hero | ObjUser.Ghost, actionText = "SMASH", uses = 1, offDuringFight = false,
                useSound = "SoundPropAction", bounce = true,
                useBox = new Vector2(26f, 20f), bodySize = new Vector2(8f, 4f),
                spawn = new ObjSpawn { weight = 8f, minFloor = 1, rooms = ObjRoom.Fight | ObjRoom.Quiet | ObjRoom.Statue | ObjRoom.Corridor | ObjRoom.Trapped, place = ObjPlace.Anywhere, maxPerFloor = 2 },
                // the hero's action button is his attack: never let the urn swallow a swing in a fight
                canUse = u => u.pd == null || !u.pd.IsHero || !ModUtil.DoorsLocked(),
                onUse = SmashUrn,
            };
            var box = new ObjectDef
            {
                id = "Strongbox", name = "Strongbox", art = "ObjStrongbox", kind = ObjKind.Use,
                vault = "An iron-bound box of coin. Now and then it bites",
                tip1 = "Open: a pile of gold",
                tip2 = "Some are mimics: they bite, then spit up gold",
                users = ObjUser.Hero, actionText = "OPEN", uses = 1, useSound = "SoundPropActivate",
                useBox = new Vector2(28f, 20f), bodySize = new Vector2(14f, 4f),
                spawn = new ObjSpawn { weight = 8f, minFloor = 1, rooms = ObjRoom.Quiet | ObjRoom.Fight | ObjRoom.Statue | ObjRoom.Stairs, place = ObjPlace.Anywhere, maxPerFloor = 2 },
                onUse = OpenBox,
            };
            box.once.Add("Bite");
            box.then["Bite"] = "Spent";
            yield return box;
        }

        // ================================================================================================= behaviours
        /// <summary>The pendulum's two posts are solid (two small blocks at x -9.5 and 9.5), the swing space is open.</summary>
        static void PendulumPosts(GameObject go)
        {
            var body = go.transform.Find("Body");
            if (body == null) return;
            var cols = body.GetComponents<BoxCollider>();
            if (cols.Length >= 2) return;
            var a = cols.Length > 0 ? cols[0] : body.gameObject.AddComponent<BoxCollider>();
            a.size = new Vector3(4f, 3f, 150f); a.center = new Vector3(-9.5f, 0.5f, 0f);
            var b = body.gameObject.AddComponent<BoxCollider>();
            b.size = new Vector3(4f, 3f, 150f); b.center = new Vector3(9.5f, 0.5f, 0f);
        }

        static void Warp(ObjUse u)
        {
            var other = u.obj.partner;
            var body = u.Body;
            if (other == null || body == null) return;
            Vector2 from = u.obj.transform.position, to = other.transform.position;
            if (WarpFlash != null) { SystemPool.Spawn(WarpFlash, (Vector3)from); SystemPool.Spawn(WarpFlash, (Vector3)to); }
            ModUtil.Teleport(body, to + new Vector2(0f, -1f));
            other.HoldOff(u.pd.Id, 1.5f);
            other.Play("Use");
            ObjectKit.PlaySound("SoundPropActivate", other.transform);
        }

        static IEnumerator HealOverTime(GameObject who, float total, float seconds)
        {
            if (who == null) yield break;
            var h = who.GetComponent<Health>();
            if (h == null) yield break;
            ModInd.Heal(who);
            ModInd.Regen(who, true);
            int ticks = Mathf.RoundToInt(seconds);
            for (int i = 0; i < ticks; i++)
            {
                yield return new WaitForSeconds(seconds / ticks);
                if (who == null || h == null || !h.IsAlive() || !who.activeInHierarchy) break;
                h.Heal(total / ticks);
            }
            if (who != null) ModInd.Regen(who, false);
        }

        static void SwapWeapon(ObjUse u)
        {
            var pd = u.pd;
            var cur = pd.GameData.GetWeaponData();
            float cost = cur != null ? cur.GetBaseCost() : 0f;
            string curName = cur != null ? cur.GetDisplayName() : string.Empty;
            SpawnGroup group = null;
            try { group = SystemLevel.GetWeaponsGroup(); } catch { }
            if (group == null) return;
            WeaponData pick = null, any = null;
            for (int i = 0; i < 40 && pick == null; i++)
            {
                var go = group.GetObject();
                var w = go != null ? go.GetComponent<Weapon>() : null;
                if (w == null) continue;
                var wd = new WeaponData();
                wd.Init(w);
                if (wd.GetDisplayName() == curName) continue;
                if (any == null) any = wd;
                float c = wd.GetBaseCost();
                if (c >= cost * 0.8f && c <= cost + 60f) pick = wd;
            }
            pick = pick ?? any;
            if (pick == null) return;
            u.player.ChangeWeapon(pick);   // EquipWeapon marks the new weapon found in the vault, as a shop purchase does
        }

        static void Curse(ObjUse u)
        {
            var pd = u.pd;
            var body = u.Body;
            ObjectKit.Buff(pd, "modobjcurse_dmg", PlayerModifier.eType.HeroDamage, CurseMult, 0f,
                () => { if (body != null) { ModInd.Might(body, false); ModInd.Set(body, IndCurse, false); } });
            ObjectKit.Buff(pd, "modobjcurse_res", PlayerModifier.eType.HeroDamageResistance, 1f / CurseMult, 0f);
            if (body != null) { ModInd.Might(body, true); ModInd.Set(body, IndCurse, true); }
        }

        /// <summary>
        /// v0.10 sweep: the shrine can only be used outside a fight, so a 15 s ward from the moment of prayer had mostly
        /// run out before the next fight began. The ward now holds (half damage already) until the next fight's doors lock,
        /// then lasts 15 s more from there.
        /// </summary>
        static void Ward(ObjUse u)
        {
            var body = u.Body;
            ObjectKit.Buff(u.pd, WardSource, PlayerModifier.eType.HeroDamageResistance, 2f, 0f,
                () => { if (body != null) ModInd.Set(body, IndWard, false); });
            if (body == null) return;
            ModInd.Set(body, IndWard, true);
            var w = body.GetComponent<WardWait>() ?? body.AddComponent<WardWait>();
            w.pd = u.pd; w.body = body; w.enabled = true;
        }
        internal const string WardSource = "modobjward";

        /// <summary>Starts the ward's 15 s when the hero's next fight begins.</summary>
        class WardWait : MonoBehaviour
        {
            public PlayerData pd;
            public GameObject body;
            bool m_started;
            void OnEnable() { m_started = false; }
            void Update()
            {
                // the hero body passes to the killer on this same object: if the one who prayed is no longer the hero,
                // the blessing goes with him (drop it and the ring, so the new hero's body doesn't show a ward it lacks)
                if (pd == null || !pd.IsHero)
                {
                    ObjectKit.Unbuff(pd, WardSource);
                    if (body != null) ModInd.Set(body, IndWard, false);
                    enabled = false; return;
                }
                if (m_started)
                {
                    // the 15 s are running: stay until the buff ends, so a hero change above still clears the ring
                    if (!ObjectKit.HasBuff(pd, WardSource)) enabled = false;
                    return;
                }
                if (!ModUtil.DoorsLocked()) return;
                var b = body;
                ObjectKit.Buff(pd, WardSource, PlayerModifier.eType.HeroDamageResistance, 2f, WardTime,
                    () => { if (b != null) ModInd.Set(b, IndWard, false); });
                if (b != null) { ModInd.Set(b, IndWard, false); ModInd.Set(b, IndWard, true, WardTime); }
                m_started = true;
            }
        }

        static void SmashUrn(ObjUse u)
        {
            Vector2 at = u.obj.transform.position;
            if (UrnBurst != null) SystemPool.Spawn(UrnBurst, (Vector3)at);
            if (u.IsGhost)
            {
                // fill the bar: the game caps a pickup at the player's EctoplasmMax, so ask for plenty and show what it took
                float before = u.pd.Ectoplasm;
                u.Ecto(999f);
                int got = Mathf.RoundToInt(u.pd.Ectoplasm - before);
                if (got > 0) u.Say(got.ToString(), NumberTone.Max);
            }
            else { u.Gold(UrnGold); u.Say(UrnGold.ToString(), NumberTone.Max); }
            u.obj.Spent();
        }

        static void OpenBox(ObjUse u)
        {
            Vector2 at = u.obj.transform.position;
            if (UnityEngine.Random.value < MimicChance)
            {
                u.obj.Play("Bite");
                u.Hurt(MimicBite);
                u.Gold(MimicGold);
                if (MimicCoins != null) SystemPool.Spawn(MimicCoins, (Vector3)at);
                u.Say(MimicGold.ToString(), NumberTone.Min);
            }
            else
            {
                int g = UnityEngine.Random.Range(BoxGoldMin, BoxGoldMax + 1);
                u.Gold(g);
                if (MimicCoins != null) SystemPool.Spawn(MimicCoins, (Vector3)at);
                u.Say(g.ToString(), NumberTone.Max);
            }
        }

        // ================================================================================================= self-test
        public static void SelfCheck(Action<string> bad)
        {
            ObjectKit.SelfCheck(bad);
            foreach (var id in new[] { "ChainHook", "SteamVent", "TarSpout", "Pendulum", "RunePlate", "TollBell", "ScatterIdol",
                                       "IronSnare", "WarpStone", "MendSpring", "WeaponRack", "CursedAltar", "WardShrine", "SpiritUrn", "Strongbox" })
                if (!ObjectKit.Built.ContainsKey(id)) bad("object " + id + " was not built");
            foreach (var kv in new Dictionary<string, GameObject> { { "Hook", Hook }, { "Steam", Steam }, { "TarGlob", TarGlob }, { "TarPool", TarPool },
                { "PendHit", PendHit }, { "RuneCharge", RuneCharge }, { "RuneBurst", RuneBurst }, { "TollWave", TollWave }, { "Dart", Dart },
                { "HookYank", HookYank }, { "WarpFlash", WarpFlash }, { "UrnBurst", UrnBurst }, { "MimicCoins", MimicCoins } })
                if (kv.Value == null) bad("object effect " + kv.Key + " missing");
            if (IndCurse == null || IndWard == null) bad("object indicators missing");
        }
    }

    /// <summary>On a Chain Winch hook: when it reaches the hero, haul him back to where it was thrown from.</summary>
    public class ObjHookFx : MonoBehaviour
    {
        Vector2 m_origin;
        bool m_done;

        public void Arm() { m_origin = transform.position; m_done = false; }

        void Update()
        {
            if (m_done) return;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 h = hero.transform.position;
            if (((Vector2)transform.position - h).sqrMagnitude > 11f * 11f) return;
            var hp = hero.GetComponent<Health>();
            if (hp == null || !hp.IsAlive()) return;
            m_done = true;
            if (ObjectPack.HookYank != null) SystemPool.Spawn(ObjectPack.HookYank, (Vector3)(h + new Vector2(0f, 6f)));
            ObjectKit.Run(Haul(hero, m_origin));
        }

        static IEnumerator Haul(GameObject hero, Vector2 to)
        {
            for (int i = 0; i < 6; i++)
            {
                if (hero == null || !hero.activeInHierarchy) yield break;
                Vector2 d = to - (Vector2)hero.transform.position;
                if (d.sqrMagnitude < 12f * 12f) yield break;   // stop just short of the winch
                ModUtil.Pull(hero, to, 140f);
                yield return new WaitForSeconds(0.05f);
            }
        }
    }
}
