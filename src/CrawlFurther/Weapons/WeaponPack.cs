using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Weapons
{
    using CrawlFurther.Art;
    using CrawlFurther.Heroes;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    // =====================================================================================================
    //  v0.7 hero weapons: ten new weapons in ten families, sold from the vanilla weapon shop group.
    //
    //  The hero's swing / shoot frames (weapon included) live in the vanilla hero atlas, so each weapon keeps
    //  the closest vanilla weapon's hero frames. Everything else is new: the hero clips are re-timed copies with
    //  their own event timelines (AnimAttack ids point at this pack's effects, vanilla magic tags dropped), the
    //  combo structure / cooldowns / damage are this pack's, every hitbox and projectile wears mod art
    //  (art/out_weapons, tools/sprites/weapon_rigs.py), and each weapon's mechanic is a MonoBehaviour attached
    //  to its effect instances. Landed hits reach those behaviours through Health.Damage's own
    //  "MsgOnAttackContact" message to the effect that dealt them, so no extra Harmony patch is needed.
    // =====================================================================================================

    // ----------------------------------------------------------------------------------------------- FX
    public static partial class WeaponFx
    {
        public static GameObject HookJab, Hook, ChainLink;
        public static GameObject GlaiveSlash, Glaive;
        public static GameObject RiftSlashA, RiftSlashB, RiftMark, RiftSnap;
        public static GameObject DiceSwing, Jackpot;
        public static readonly GameObject[] Dice = new GameObject[6];
        public static GameObject TideCleave, TideCrash, Wave, Splash;
        public static GameObject LeechStab, LeechSlash, Bead, LeechHeal;
        public static GameObject BriarArrow, ThornPatch;
        public static GameObject BellHit, BellRing, BellToll;
        public static GameObject LanternSwing, SoulBolt, SoulFire, Wisp;
        public static GameObject ArcBolt, Arc, Spark;

        // ---- builders ----------------------------------------------------------------------------------

        internal static void OnSpawn<T>(GameObject tmpl, Action<T> init) where T : Component
        {
            if (tmpl == null) return;
            Action<GameObject> prev;
            FxFactory.OnSpawn.TryGetValue(tmpl, out prev);
            FxFactory.OnSpawn[tmpl] = i =>
            {
                if (prev != null) prev(i);
                var c = i.GetComponent<T>() ?? i.AddComponent<T>();
                if (init != null) init(c);
            };
        }

        internal static void Anchor(GameObject go, exPlane.Anchor a, Vector2 offset)
        {
            if (go == null) return;
            var spr = go.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = a; spr.offset = offset; }
        }

        static void ScaleColliders(GameObject go, float k)
        {
            if (go == null || Mathf.Abs(k - 1f) < 0.01f) return;
            foreach (var c in go.GetComponents<CapsuleCollider>()) { c.radius *= k; if (c.direction != 2) c.height *= k; c.center = new Vector3(c.center.x * k, c.center.y * k, c.center.z); }
            foreach (var c in go.GetComponents<BoxCollider>()) { c.size = new Vector3(c.size.x * k, c.size.y * k, c.size.z); c.center = new Vector3(c.center.x * k, c.center.y * k, c.center.z); }
        }

        internal static void Box(GameObject go, float w, float h, float cx = 0f, float cy = 0f)
        {
            if (go == null) return;
            foreach (var c in go.GetComponents<BoxCollider>()) { c.size = new Vector3(w, h, c.size.z); c.center = new Vector3(cx, cy, c.center.z); }
        }

        /// <summary>
        /// Melee hitbox: a vanilla hero swipe (keeps its collider, layer, attach/rotate behaviour) wearing a mod
        /// swing. Damage is live on the art's first two frames. The sprite is centred on the collider centre.
        /// </summary>
        internal static GameObject Swipe(string name, string vanilla, string art, string anim, float damage, float knock, Vector2 hitCentre,
                                float colliderScale = 1f, Status status = null, float statusChance = 0f)
        {
            var sh = SpriteSheets.Get(art);
            var go = FxFactory.Clone(vanilla, name);
            if (go == null || sh == null) return go;
            FxFactory.StripChildren(go);
            var clip = new ClipBuilder(sh, anim, name + "Clip").Once().Ev(0, "AnimDamageOn").Ev(2, "AnimDamageOff").Build();
            FxFactory.Reskin(go, clip, sh);
            Anchor(go, exPlane.Anchor.MidCenter, hitCentre * colliderScale);
            FxFactory.SetEffect(go, destroyOnAnimEnd: true);
            FxFactory.SetDamage(go, damage, knockback: knock, status: status, statusChance: statusChance, collisionAtStart: false);
            ScaleColliders(go, colliderScale);
            FxKit.NoTint(go);
            return go;
        }

        /// <summary>A projectile from a vanilla hero projectile (collider, layer, contact sparks kept).</summary>
        internal static GameObject Shot(string name, string vanilla, string art, string anim, float speed, float life, float damage, float knock,
                               bool destroyOnHit = true, float accel = 0f, float speedMax = 0f)
        {
            var go = FxKit.Projectile(name, vanilla, art, anim, speed, life, damage, knock, destroyOnHit: destroyOnHit, accel: accel, speedMax: speedMax);
            return go;
        }

        /// <summary>
        /// A hero-owned area hitbox (the axe's invisible hit, which hits monsters and props) wearing mod art:
        /// damage switches on at frame `on` and off at frame `off` of the clip (negative = from the end).
        /// </summary>
        internal static GameObject Zone(string name, ClipBuilder cb, SpriteSheet sh, float damage, float rate, float knock, int on, int off,
                               Status status = null, float statusChance = 0f, bool attached = false)
        {
            var go = FxFactory.Clone("DFX_Axe_InvisibleHit", name);
            if (go == null || sh == null) return go;
            FxFactory.StripChildren(go);
            cb.Ev(on, "AnimDamageOn").Ev(off, "AnimDamageOff");
            FxFactory.Reskin(go, cb.Build(), sh);
            Anchor(go, exPlane.Anchor.MidCenter, Vector2.zero);
            if (attached) FxFactory.SetEffect(go, destroyOnAnimEnd: true);
            else FxFactory.SetEffect(go, destroyOnAnimEnd: true, canFlip: false, freeRotate: false);
            FxFactory.SetDamage(go, damage, rate: rate, knockback: knock, status: status, statusChance: statusChance, collisionAtStart: false);
            FxKit.NoTint(go);
            return go;
        }

        internal static GameObject Vis(string name, string art, string anim, bool loop = false, float life = 0f, exPlane.Anchor a = exPlane.Anchor.MidCenter)
        {
            var go = FxKit.Visual(name, art, anim, loop, life);
            Anchor(go, a, Vector2.zero);
            return go;
        }

        public static void Build()
        {
            var daze = FxFactory.GetStatus("StatusDizzy");
            var root = FxFactory.GetStatus("StatusStuckToFloor");
            var bleed = FxFactory.GetStatus("StatusBleeding");

            // ---- Gravehook (tether) --------------------------------------------------------------------
            HookJab = Swipe("ModWpnHookJab", "SpearSwipe", "FxWpnGravehook", "Jab", 1.05f, 0.5f, new Vector2(1.7f, -2.1f));
            Hook = Shot("ModWpnHook", "SpearProjectile", "FxWpnGravehook", "Hook", 340f, 0.5f, 1.0f, 0f, destroyOnHit: true, accel: 0.04f, speedMax: 0.1f);
            if (Hook != null) FxFactory.SetContacts(Hook, destroyOnHit: true);
            OnSpawn<WpnTetherFx>(Hook, null);
            ChainLink = Vis("ModWpnChainLink", "FxWpnGravehook", "Chain");

            // ---- Moonglaive (returning) ----------------------------------------------------------------
            GlaiveSlash = Swipe("ModWpnGlaiveSlash", "1HandedSwordSwipe1", "FxWpnMoonglaive", "Slash", 0.9f, 0.6f, new Vector2(8.4f, 0.4f));
            Glaive = Shot("ModWpnGlaive", "SpearProjectile", "FxWpnMoonglaive", "Glaive", 0f, 2.4f, 0.85f, 0.3f, destroyOnHit: false);
            if (Glaive != null)
            {
                FxFactory.SetMotion(Glaive, 0f, enabled: false);           // WpnGlaiveFx flies it
                FxFactory.SetDamage(Glaive, 0.85f, rate: 0.35f, knockback: 0.3f, collisionAtStart: true);
                FxFactory.SetEffect(Glaive, destroyOnAnimEnd: false, destroyAfter: 2.4f, canFlip: false, freeRotate: false);
                Box(Glaive, 14f, 14f);
                Anchor(Glaive, exPlane.Anchor.MidCenter, Vector2.zero);
            }
            OnSpawn<WpnGlaiveFx>(Glaive, g => g.Reset());

            // ---- Riftblade (delayed rift) --------------------------------------------------------------
            RiftSlashA = Swipe("ModWpnRiftSlashA", "1HandedSwordSwipe2", "FxWpnRiftblade", "SlashA", 0.9f, 0.5f, new Vector2(8.4f, -0.8f));
            RiftSlashB = Swipe("ModWpnRiftSlashB", "DamageHeroSwipeSkewed", "FxWpnRiftblade", "SlashB", 0.9f, 0.5f, new Vector2(5.5f, 1.3f));
            OnSpawn<WpnRiftFx>(RiftSlashA, null);
            OnSpawn<WpnRiftFx>(RiftSlashB, null);
            RiftMark = Vis("ModWpnRiftMark", "FxWpnRiftblade", "Mark", loop: true, life: WpnRiftMark.Delay + 0.3f);
            RiftSnap = Vis("ModWpnRiftSnap", "FxWpnRiftblade", "Snap");

            // ---- Snake-Eyes (chance) -------------------------------------------------------------------
            DiceSwing = Swipe("ModWpnDiceSwing", "1HandedSwordSwipe2", "FxWpnSnakeEyes", "Swing", 1.0f, 0.9f, new Vector2(8.4f, -0.8f));
            OnSpawn<WpnDiceFx>(DiceSwing, d => d.baseDamage = 1.0f);
            for (int i = 0; i < 6; i++) Dice[i] = Vis("ModWpnDie" + (i + 1), "FxWpnSnakeEyes", "Die" + (i + 1));
            var se = SpriteSheets.Get("FxWpnSnakeEyes");
            Jackpot = Zone("ModWpnJackpot", new ClipBuilder(se, "Jackpot", "ModWpnJackpotClip").Once(), se, 0.8f, 0f, 2.2f, 0, 3);
            Box(Jackpot, 34f, 26f);

            // ---- Tidebreaker (tide) --------------------------------------------------------------------
            TideCleave = Swipe("ModWpnTideCleave", "DamageHeroSwipeSkewed", "FxWpnTidebreaker", "Cleave", 1.0f, 0.8f, new Vector2(5.5f, 1.3f), 1.2f);
            TideCrash = Swipe("ModWpnTideCrash", "DamageHeroSwipeSkewed", "FxWpnTidebreaker", "Crash", 1.2f, 1.0f, new Vector2(5.5f, 1.3f), 1.25f);
            Wave = Shot("ModWpnWave", "SpearProjectile", "FxWpnTidebreaker", "Wave", 150f, 0.65f, 0.4f, 0f, destroyOnHit: false, accel: 0.04f, speedMax: 0.1f);
            if (Wave != null)
            {
                FxFactory.SetDamage(Wave, 0.4f, rate: 0.3f, knockback: 0f, collisionAtStart: true);
                Box(Wave, 14f, 26f);
                Anchor(Wave, exPlane.Anchor.MidCenter, Vector2.zero);
            }
            OnSpawn<WpnWaveFx>(Wave, w => w.Reset());
            Splash = Vis("ModWpnSplash", "FxWpnTidebreaker", "Splash");

            // ---- Leechfang (siphon) --------------------------------------------------------------------
            LeechStab = Swipe("ModWpnLeechStab", "DaggerDashthrough", "FxWpnLeechfang", "Stab", 0.75f, 0.4f, new Vector2(6.9f, -1.9f), 1f, bleed, 0.15f);
            LeechSlash = Swipe("ModWpnLeechSlash", "1HandedSwordSwipe1", "FxWpnLeechfang", "Slash", 0.75f, 0.5f, new Vector2(8.4f, 0.4f), 1f, bleed, 0.15f);
            OnSpawn<WpnLeechFx>(LeechStab, null);
            OnSpawn<WpnLeechFx>(LeechSlash, null);
            Bead = Vis("ModWpnBloodBead", "FxWpnLeechfang", "Bead", loop: true, life: 1.5f);
            OnSpawn<WpnBeadFx>(Bead, b => b.Reset());
            LeechHeal = Vis("ModWpnLeechHeal", "FxWpnLeechfang", "Heal");

            // ---- Briarbow (seed) -----------------------------------------------------------------------
            var br = SpriteSheets.Get("FxWpnBriarbow");
            // 0.26 s sprouting (4 frames), 5 x 0.42 s of live thorns, 0.24 s wilting (4 frames) = 2.6 s; thorns hurt from
            // the first live frame to the first wilting one
            ThornPatch = Zone("ModWpnThornPatch", new ClipBuilder(br, "Grow", "ModWpnThornPatchClip").Once().Then("Life", 5).Then("Wilt"), br,
                              0.2f, 0.5f, 0f, 4, -4, root, 0.5f);
            Box(ThornPatch, 30f, 16f);
            BriarArrow = Shot("ModWpnBriarArrow", "DFX_HeroArrow", "FxWpnBriarbow", "Arrow", 380f, 0.5f, 0.95f, 0.5f);
            if (BriarArrow != null)
            {
                FxFactory.SetContacts(BriarArrow, spawnOnHit: ThornPatch);
                FxFactory.SetEffect(BriarArrow, destroyOnAnimEnd: false, destroyAfter: 0.5f, spawnOnDestroy: ThornPatch, freeRotate: true);
            }

            // ---- Dirge Maul (bell) ---------------------------------------------------------------------
            var dm = SpriteSheets.Get("FxWpnDirgeMaul");
            BellHit = Zone("ModWpnBellHit", new ClipBuilder(dm, "Clang", "ModWpnBellHitClip").Once(), dm, 1.0f, 0f, 1.0f, 0, 2, attached: true);
            Box(BellHit, 29.5f, 20.9f, 13f, 0f);
            Anchor(BellHit, exPlane.Anchor.MidCenter, new Vector2(13f, 0f));
            BellRing = Zone("ModWpnBellRing", new ClipBuilder(dm, "Ring", "ModWpnBellRingClip").Once(), dm, 0.35f, 0f, 0.7f, 0, 4, daze, 1f);
            Box(BellRing, 52f, 32f);
            OnSpawn<WpnBellFx>(BellRing, null);
            BellToll = Zone("ModWpnBellToll", new ClipBuilder(dm, "Toll", "ModWpnBellTollClip").Once(), dm, 0.35f, 0f, 0.9f, 0, 4, daze, 1f);
            Box(BellToll, 76f, 46f);

            // ---- Wickstaff (lantern) -------------------------------------------------------------------
            var wk = SpriteSheets.Get("FxWpnWickstaff");
            LanternSwing = Swipe("ModWpnLanternSwing", "MagicStaffSwipe", "FxWpnWickstaff", "Swing", 0.2f, 0.8f, new Vector2(5.2f, -1.3f));
            SoulFire = Zone("ModWpnSoulFire", new ClipBuilder(wk, "Fire", "ModWpnSoulFireClip").Once().Repeat(6), wk, 0.12f, 0.4f, 0f, 0, -1);
            Box(SoulFire, 22f, 12f);
            OnSpawn<WpnSoulFireFx>(SoulFire, f => f.Reset());
            Wisp = Shot("ModWpnWisp", "DFX_HeroArrow", "FxWpnWickstaff", "Wisp", 0f, 1.6f, 0.5f, 0.3f);
            if (Wisp != null)
            {
                FxFactory.StripChildren(Wisp);                              // the arrow's long hit box child
                FxFactory.SetMotion(Wisp, 0f, enabled: false);             // WpnSeekFx steers it
                FxFactory.SetEffect(Wisp, destroyOnAnimEnd: false, destroyAfter: 1.6f, canFlip: false, freeRotate: true);
                Anchor(Wisp, exPlane.Anchor.MidCenter, Vector2.zero);
                Box(Wisp, 8f, 8f);
            }
            OnSpawn<WpnSeekFx>(Wisp, s => s.Reset());
            SoulBolt = Shot("ModWpnSoulBolt", "DFX_HeroArrow", "FxWpnWickstaff", "Bolt", 170f, 0.85f, 0.6f, 0.3f);
            if (SoulBolt != null)
            {
                FxFactory.SetContacts(SoulBolt, spawnOnHit: SoulFire);
                FxFactory.SetEffect(SoulBolt, destroyOnAnimEnd: false, destroyAfter: 0.85f, spawnOnDestroy: SoulFire, freeRotate: true);
            }

            // ---- Arcbolt (chain lightning) -------------------------------------------------------------
            ArcBolt = Shot("ModWpnArcBolt", "DFX_HeroArrow", "FxWpnArcbolt", "Bolt", 420f, 0.6f, 0.8f, 0.4f);
            OnSpawn<WpnChainFx>(ArcBolt, c => c.Reset());
            Arc = Vis("ModWpnArc", "FxWpnArcbolt", "Arc", a: exPlane.Anchor.MidLeft);
            Spark = Vis("ModWpnSpark", "FxWpnArcbolt", "Spark");
            Build2();
            BuildV08();
            Plugin.Log.LogInfo("Weapon FX templates built");
        }
    }

    // ----------------------------------------------------------------------------------------------- pack
    public static partial class WeaponPack
    {
        /// <summary>The weapons built so far (the same table as <see cref="ItemRegistry.Weapons"/>).</summary>
        public static Dictionary<string, Weapon> Built { get { return ItemRegistry.Weapons; } }

        static DamageEffectData Melee(GameObject o, float ox, float oy, float upX = 0f, float dnX = 0f, bool destroyOnAnimEnd = false, float angle = 0f)
        {
            return new DamageEffectData
            {
                m_angle = new MinMaxRange(angle),
                m_object = o, m_attach = true, m_destroyOnAnimEnd = destroyOnAnimEnd, m_detatchOnAnimEnd = !destroyOnAnimEnd,
                m_offsetX = new MinMaxRange(ox), m_offsetY = new MinMaxRange(oy),
                m_offsetAimUp = new Vector2(upX, 0f), m_offsetAimDown = new Vector2(dnX, 0f), m_rotateOffsetX = true
            };
        }

        static DamageEffectData Fire(GameObject o, float ox, float oy, Vector2 up = default(Vector2), Vector2 dn = default(Vector2))
        {
            return new DamageEffectData
            {
                m_object = o, m_attach = false, m_destroyOnAnimEnd = false,
                m_offsetX = new MinMaxRange(ox), m_offsetY = new MinMaxRange(oy), m_offsetAimUp = up, m_offsetAimDown = dn, m_rotateOffsetX = true
            };
        }

        static List<DamageEffectData> L(params DamageEffectData[] e) { return new List<DamageEffectData>(e); }

        // Damage numbers in the descriptions are effect damage x combo multiplier (before STR and other modifiers).
        public static readonly List<WeaponDef> Defs = new List<WeaponDef>
        {
            new WeaponDef { id = "Gravehook", name = "Gravehook", family = "Tether", baseWeapon = "WeaponSpear", baseCombo = 1,
                cost = 85, damageMult = 0.95f, comboCooldown = 0.4f,
                description = "Jab, then hook a monster and drag it to you",
                effects = () => L(Melee(WeaponFx.HookJab, 14f, 2f, 3f, 3f), Fire(WeaponFx.Hook, 0f, -2f)),
                attacks = { new WeaponAttack(0, 0.33f, 1.0f, "a1", 0), new WeaponAttack(1, 0.40f, 0.95f, "a1", 0), new WeaponAttack(5, 0.55f, 1.1f, "a0", 1) } },

            new WeaponDef { id = "Moonglaive", name = "Moonglaive", family = "Returning", baseWeapon = "WeaponThrowingKnives", baseCombo = 0,
                cost = 70, damageMult = 1.0f, comboCooldown = 0.3f,
                description = "Slash, then throw a glaive that comes back to you",
                effects = () => L(Melee(WeaponFx.GlaiveSlash, 0f, -1f, 2f, 2f), Fire(WeaponFx.Glaive, 6f, -2f)),
                attacks = { new WeaponAttack(0, 0.35f, 1.0f, "a1", 0), new WeaponAttack(1, 0.45f, 1.0f, "a0", 1) } },

            new WeaponDef { id = "Riftblade", name = "Riftblade", family = "Rift", baseWeapon = "Weapon1HandedSword", baseCombo = 1,
                cost = 60, damageMult = 0.75f, comboCooldown = 0.35f,
                description = "Quick cuts open a rift that snaps shut on your foes",
                effects = () => L(Melee(WeaponFx.RiftSlashA, 0f, 0f, 3f, 2f), Melee(WeaponFx.RiftSlashB, 0f, 0f, 4f, 3f)),
                attacks = { new WeaponAttack(0, 0.30f, 0.9f, "a1", 0), new WeaponAttack(1, 0.34f, 0.9f, "a0", 1), new WeaponAttack(2, 0.36f, 0.95f, "a1", 0) } },

            new WeaponDef { id = "SnakeEyes", name = "Snake-Eyes", family = "Chance", baseWeapon = "WeaponClub", baseCombo = 0,
                cost = 45, damageMult = 1.1f, comboCooldown = 0.25f,
                description = "Every blow rolls a die. Roll high to hit hard",
                effects = () => L(Melee(WeaponFx.DiceSwing, 0f, -1f, 3f, 6f)),
                attacks = { new WeaponAttack(0, 0.55f, 1.0f, "a1", 0), new WeaponAttack(2, 0.45f, 1.0f, "a0", 0) } },

            new WeaponDef { id = "Tidebreaker", name = "Tidebreaker", family = "Tide", baseWeapon = "Weapon2HandedSword", baseCombo = 1,
                cost = 90, damageMult = 0.92f, comboCooldown = 0.35f,
                description = "Every third swing sends a wave that sweeps monsters away",
                effects = () => L(Melee(WeaponFx.TideCleave, 4f, 0f), Melee(WeaponFx.TideCrash, 0f, 1f), Fire(WeaponFx.Wave, 10f, -4f)),
                attacks = { new WeaponAttack(4, 0.32f, 1.0f, "a1", 0), new WeaponAttack(2, 0.39f, 1.0f, "a1", 0),
                            new WeaponAttack(9, 0.45f, 1.05f, "a12", 1, "a16", 2) } },

            new WeaponDef { id = "Leechfang", name = "Leechfang", family = "Siphon", baseWeapon = "WeaponDagger", baseCombo = 2,
                cost = 55, damageMult = 0.95f, comboCooldown = 0.2f,
                description = "Fast stabs that bleed foes and heal you",
                effects = () => L(Melee(WeaponFx.LeechStab, 5f, 0f, 5f, 5f), Melee(WeaponFx.LeechSlash, 0f, 0f, 5f, 2f)),
                attacks = { new WeaponAttack(2, 0.29f, 1.0f, "a0", 1), new WeaponAttack(3, 0.29f, 1.0f, "a2", 0), new WeaponAttack(4, 0.30f, 1.0f, "a3", 1) } },

            new WeaponDef { id = "Briarbow", name = "Briarbow", family = "Seed", baseWeapon = "WeaponBow", baseCombo = 0,
                cost = 65, damageMult = 1.0f, comboCooldown = 0f,
                description = "Arrows plant thorny briars where they land",
                effects = () => L(Fire(WeaponFx.BriarArrow, 0f, -2f)),
                attacks = { new WeaponAttack(0, 1.0f, 1.0f, "a0", 0) } },

            new WeaponDef { id = "DirgeMaul", name = "Dirge Maul", family = "Bell", baseWeapon = "WeaponBattleAxe", baseCombo = 0,
                cost = 80, damageMult = 1.55f, comboCooldown = 0f,
                description = "Each slam rings a bell that stuns nearby monsters",
                effects = () => L(Melee(WeaponFx.BellHit, 2f, -9f, 0f, 0f, destroyOnAnimEnd: true),
                                  Fire(WeaponFx.BellRing, 18f, -10f, new Vector2(0f, -8f), new Vector2(0f, 8f))),
                attacks = { new WeaponAttack(0, 1.1f, 1.0f, "a3", 0, "a2", 1) } },

            new WeaponDef { id = "Wickstaff", name = "Wickstaff", family = "Lantern", baseWeapon = "WeaponMagicStaff", baseCombo = -1,
                cost = 85, damageMult = 1.0f, comboCooldown = 0f,
                description = "Lantern bolts leave soul fire that spawns seeking wisps",
                effects = () => L(Melee(WeaponFx.LanternSwing, 0f, 1f), Fire(WeaponFx.SoulBolt, 4f, -2f)),
                attacks = { new WeaponAttack(0, 1.1f, 1.0f, "a0", 0, "mprj", 1) } },

            new WeaponDef { id = "Arcbolt", name = "Arcbolt", family = "Storm", baseWeapon = "WeaponCrossbow", baseCombo = 1,
                cost = 75, damageMult = 1.0f, comboCooldown = 0.5f,
                description = "Bolts that arc lightning between foes",
                effects = () => L(Fire(WeaponFx.ArcBolt, 5f, 0f)),
                attacks = { new WeaponAttack(0, 0.6f, 1.0f, "a1", 0), new WeaponAttack(1, 0.6f, 1.0f, "a1", 0) } },
        };

        public static void Register()
        {
            WeaponFx.Build();
            Defs.AddRange(Defs2);                       // first ten keep their order (shop pedestal frames follow it)
            foreach (var def in Defs)
            {
                try { Build(def); }
                catch (Exception e) { Plugin.Log.LogError("Weapon " + def.id + " failed: " + e); }
            }
            try { WeaponLooks.Register(); } catch (Exception e) { Plugin.Log.LogError("Weapon in-hand colours failed: " + e); }
            Plugin.Log.LogInfo("Weapons built: " + Built.Count + "/" + Defs.Count);
        }

        static void Build(WeaponDef def)
        {
            // the hero frames redrawn with this weapon in hand (art/out_weapons/WpnHand_<id>, tools/sprites/weapon_hands.py)
            var hands = WeaponHands.For(def.id);
            def.heroFrames = (exAtlas atlas, int index, out exAtlas outAtlas, out int outIndex) => WeaponHands.Remap(atlas, index, hands, out outAtlas, out outIndex);
            int unmapped0 = WeaponHands.Unmapped;
            ItemRegistry.Register(def);
            if (WeaponHands.Unmapped > unmapped0)
                Plugin.Log.LogWarning(def.id + ": " + (WeaponHands.Unmapped - unmapped0) + " hero frames have no in-hand redraw (vanilla weapon shows)");
        }
    }

    // ----------------------------------------------------------------------------------------------- runtime
    /// <summary>Per-hero counters and a coroutine host that outlives the effects that start things.</summary>
    public class WeaponRuntime : MonoBehaviour
    {
        public int leechHits, bellSlams;
        public int reapStacks, guardHits;
        public float guardUntil, runTime, idleTime, grudgeTime;
        public GameObject grudge, guardFx;
        GameObject m_grudgeShown;          // the monster wearing the grudge brand overlay
        public ValueModifierStack guardMod;
        public readonly List<GameObject> stars = new List<GameObject>();
        PlayerMovement m_move;
        GameObject m_readyFx;
        int m_reapShown;
        // Reaper souls and the grudge brand are head overlays (ModInd): they stack above the head with the status
        // overlays (daze, Mark, Rime...) instead of being pinned at a fixed height where those would cover them
        static StatusOverlayDef[] s_reapInd;
        static StatusOverlayDef s_grudgeInd;

        static void BuildInd()
        {
            if (s_reapInd != null) return;
            s_reapInd = new StatusOverlayDef[WpnReapFx.MaxStacks];
            for (int n = 0; n < s_reapInd.Length; n++)
                s_reapInd[n] = ModStatus.Indicator("ModIndWpnReap" + (n + 1), "FxWpnReaperStacks", "Stacks" + (n + 1), 0f, OverlayAt.Head);
            // the brand's art sits 7 rows above its cell bottom
            s_grudgeInd = ModStatus.Indicator("ModIndWpnGrudge", "FxWpnGrudgestone", "Grudge", -6f, OverlayAt.Head);
        }

        void BrandGrudge(GameObject on)
        {
            BuildInd();
            if (m_grudgeShown == on) return;
            if (m_grudgeShown != null) ModInd.Set(m_grudgeShown, s_grudgeInd, false);
            m_grudgeShown = on;
            if (on != null) ModInd.Set(on, s_grudgeInd, true);
        }

        /// <summary>The mod weapon id this hero holds right now (null for a vanilla weapon).</summary>
        public string HeldId()
        {
            var pd = SystemPlayers.GetHeroPlayerData();
            if (pd == null || pd.GameObject != gameObject || pd.GameData == null) return null;
            var wd = pd.GameData.GetWeaponData();
            var w = wd != null ? wd.m_weapon : null;
            if (w == null) return null;
            var n = w.gameObject.name;
            return n.StartsWith("ModWeapon", StringComparison.Ordinal) ? n.Substring(9) : null;
        }

        /// <summary>Make sure the hero carries a runtime as soon as it holds a mod weapon (so running builds a lance
        /// charge and the state indicators show before the first hit). Called when a hero sprite enters a mod hand atlas.</summary>
        public static void EnsureOnHero(Component c)
        {
            var hero = ModUtil.Hero();
            if (hero == null || c == null || (c.gameObject != hero && !c.transform.IsChildOf(hero.transform))) return;
            if (hero.GetComponent<WeaponRuntime>() == null) hero.AddComponent<WeaponRuntime>();
        }

        /// <summary>The visible weapon states on the hero: Reaper's harvested souls (one wisp per stack round the head),
        /// the Charger Lance's charge (a crimson ring at the feet once running has built it), and the Grudgestone brand
        /// (only while a Grudgestone is in hand).</summary>
        void UpdateIndicators()
        {
            string held = HeldId();
            int want = held == "Reaper" ? Mathf.Clamp(reapStacks, 0, WpnReapFx.MaxStacks) : 0;
            if (want != m_reapShown || want > 0)      // cheap when unchanged; re-shows after a respawn dropped it
            {
                BuildInd();
                ModInd.Count(gameObject, s_reapInd, want);
                m_reapShown = want;
            }

            bool ready = held == "Lance" && runTime >= WpnChargeFx.RunNeeded;
            if (ready && WeaponFx.LanceReady != null && !WpnFollowFx.Follows(m_readyFx, gameObject))
                m_readyFx = WpnFollowFx.Attach(WeaponFx.LanceReady, gameObject, new Vector2(0f, 1f));
            else if (!ready && m_readyFx != null)
            {
                WpnFollowFx.Drop(m_readyFx, gameObject);
                m_readyFx = null;
            }

            if (m_grudgeShown != null && held != "Grudgestone") BrandGrudge(null);
        }

        void Update()
        {
            // running time for the Charger Lance: how long the hero has been moving near full speed
            if (m_move == null) m_move = GetComponent<PlayerMovement>();
            if (m_move != null)
            {
                bool running = m_move.GetVelocity().magnitude >= m_move.GetSpeedMax() * 0.6f;
                if (running) { runTime += Time.deltaTime; idleTime = 0f; }
                else if ((idleTime += Time.deltaTime) > WpnChargeFx.Grace) runTime = 0f;
            }
            if (guardFx != null && (Time.time > guardUntil || !guardFx.activeInHierarchy))
            {
                if (guardFx.activeInHierarchy) SystemPool.Despawn(guardFx);
                guardFx = null;
            }
            if (grudge != null && (Time.time - grudgeTime > WpnGrudgeFx.Window || !WpnUtil.Alive(grudge))) ClearGrudge();
            UpdateIndicators();
        }

        public bool GuardUp { get { return Time.time <= guardUntil; } }

        public void RaiseGuard(ValueModifierStack mod)
        {
            guardUntil = Time.time + WpnGuardFx.Duration;
            guardMod = mod;
            guardFx = WpnFollowFx.Refresh(guardFx, WeaponFx.GuardRing, gameObject, new Vector2(0f, 8f));   // new ring, full life
        }

        /// <summary>A monster hit was blocked: spend the guard and shove the attacker back with a bash.</summary>
        public void Block(GameObject attacker)
        {
            guardUntil = 0f;
            if (guardFx != null && guardFx.activeInHierarchy) SystemPool.Despawn(guardFx);
            guardFx = null;
            WpnUtil.Spawn(WeaponFx.GuardBlock, (Vector2)transform.position + new Vector2(0f, 8f));
            if (attacker == null) return;
            var dir = ((Vector2)attacker.transform.position - (Vector2)transform.position).normalized;
            WpnUtil.Hit(attacker, guardMod != null ? guardMod.Modify(WpnGuardFx.Bash) : WpnGuardFx.Bash, dir, 1.6f);
        }

        public void OnHurt(GameObject attacker)
        {
            reapStacks = 0;
            if (attacker == null || attacker == gameObject || attacker.GetComponent<Player>() == null) return;
            if (grudge != attacker)
            {
                ClearGrudge();
                grudge = attacker;
            }
            if (HeldId() == "Grudgestone") BrandGrudge(attacker);           // brand lives as long as the grudge
            grudgeTime = Time.time;
        }

        void ClearGrudge()
        {
            BrandGrudge(null);
            grudge = null;
        }

        /// <summary>True (once) when the hero has run long enough for the next lance thrust to be a charge.</summary>
        public bool ConsumeCharge()
        {
            bool c = runTime >= WpnChargeFx.RunNeeded;
            runTime = 0f;
            return c;
        }

        public int AddStar(GameObject star)
        {
            stars.RemoveAll(x => x == null || !x.activeInHierarchy);
            while (stars.Count >= WpnOrbitFx.Max) { var old = stars[0]; stars.RemoveAt(0); if (old != null && old.activeInHierarchy) SystemPool.Despawn(old); }
            stars.Add(star);
            return stars.Count - 1;
        }

        public static WeaponRuntime On(GameObject hero)
        {
            if (hero == null) return null;
            return hero.GetComponent<WeaponRuntime>() ?? hero.AddComponent<WeaponRuntime>();
        }

        public void Later(float t, Action a) { StartCoroutine(Run(t, a)); }

        IEnumerator Run(float t, Action a)
        {
            yield return new WaitForSeconds(t);
            try { a(); } catch (Exception e) { Plugin.Log.LogError("Weapon delayed action: " + e); }
        }
    }

    public static class WpnUtil
    {
        static readonly FieldInfo s_damage = AccessTools.Field(typeof(DamageEffect), "m_damage");
        static readonly FieldInfo s_ghost = AccessTools.Field(typeof(Player), "m_isGhost");
        static readonly FieldInfo s_isHero = AccessTools.Field(typeof(Player), "m_isHero");

        public static void SetDamage(DamageEffect d, float v) { if (d != null && s_damage != null) s_damage.SetValue(d, v); }
        static readonly FieldInfo s_knock = AccessTools.Field(typeof(DamageEffect), "m_knockbackMultiplier");
        public static void SetKnock(DamageEffect d, float v) { if (d != null && s_knock != null) s_knock.SetValue(d, v); }
        public static bool Alive(GameObject go)
        {
            if (go == null || !go.activeInHierarchy) return false;
            var h = go.GetComponent<Health>();
            return h != null && h.IsAlive();
        }
        public static float Angle(Vector2 d) { return Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg; }
        /// <summary>The hero-side damage modifier stack an effect was spawned with (STR, weapon multiplier...).</summary>
        public static ValueModifierStack Mod(GameObject fx)
        {
            var s = fx != null ? FxFactory.SourceOf(fx) : null;
            return s != null ? s.m_damageMod : null;
        }
        public static float Scaled(ValueModifierStack mod, float v) { return mod != null ? mod.Modify(v) : v; }

        /// <summary>Travel direction of a spawned effect, as ParticleMotion computes it (valid once spawning finished).</summary>
        public static Vector2 Facing(Transform t)
        {
            var e = t.GetComponent<Effect>();
            if (e != null) return e.GetOriginalRotation() * Vector3.right;
            return t.rotation * (t.localScale.x > 0f ? Vector3.right : Vector3.left);
        }

        public static DamageSource HeroSource(GameObject source = null)
        {
            var pd = SystemPlayers.GetHeroPlayerData();
            if (pd == null || pd.GameObject == null) return null;
            return new DamageSource(source, pd.GameObject, pd, -1, -1, null, false);
        }

        /// <summary>A derived hit from the hero (rift snaps, chain jumps, wall slams): amount is already final-ish
        /// (built from landed damage or scaled by the caller), so no damage modifier stack is attached.</summary>
        public static bool Hit(GameObject victim, float amount, Vector2 dir, float knock, Status status = null)
        {
            if (victim == null || amount <= 0f) return false;
            var h = victim.GetComponent<Health>();
            var src = HeroSource();
            if (h == null || src == null || !h.IsAlive() || !h.CanDamage(src, false)) return false;
            var info = new DamageInfo(amount, knock, 0f, dir, src) { m_victim = victim, m_status = status };
            return h.Damage(info, false);
        }

        public static bool LiveMonster(Player p, GameObject hero)
        {
            if (p == null || !p.gameObject.activeInHierarchy || p.gameObject == hero) return false;
            if (s_isHero != null && (bool)s_isHero.GetValue(p)) return false;
            if (s_ghost != null && (bool)s_ghost.GetValue(p)) return false;
            var h = p.GetComponent<Health>();
            return h != null && h.IsAlive();
        }

        /// <summary>Nearest living monster to a point (excluding some), within range.</summary>
        public static GameObject Nearest(Vector2 from, float range, ICollection<GameObject> exclude)
        {
            var hero = ModUtil.Hero();
            GameObject best = null;
            float bd = range * range;
            foreach (var p in UnityEngine.Object.FindObjectsOfType<Player>())
            {
                if (!LiveMonster(p, hero) || (exclude != null && exclude.Contains(p.gameObject))) continue;
                float d = ((Vector2)p.transform.position - from).sqrMagnitude;
                if (d < bd) { bd = d; best = p.gameObject; }
            }
            return best;
        }

        public static GameObject Spawn(GameObject tmpl, Vector2 pos, DamageSource src = null, float angle = 0f)
        {
            return tmpl == null ? null : FxFactory.SpawnOwned(tmpl, pos, src, angle);
        }

        /// <summary>A stretched visual between two points (chains, lightning arcs). Art is drawn left-anchored.</summary>
        public static void Span(GameObject tmpl, Vector2 a, Vector2 b, float artLength)
        {
            var go = Spawn(tmpl, a);
            if (go == null) return;
            var d = b - a;
            go.transform.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
            go.transform.localScale = new Vector3(Mathf.Max(0.1f, d.magnitude / artLength), 1f, 1f);
        }
    }

    /// <summary>Moves a monster to a point over a short time, ignoring its own movement (hook pulls, wave carries).</summary>
    public class WpnDragged : MonoBehaviour
    {
        Vector2 m_from, m_to;
        float m_t, m_dur;
        Action m_done;

        public void Begin(Vector2 to, float dur, Action done = null)
        {
            m_from = transform.position; m_to = to; m_t = 0f; m_dur = Mathf.Max(0.05f, dur); m_done = done;
            enabled = true;
        }

        void Update()
        {
            m_t += Time.deltaTime;
            float k = Mathf.Clamp01(m_t / m_dur);
            k = 1f - (1f - k) * (1f - k);                        // ease out
            ModUtil.Teleport(gameObject, Vector2.Lerp(m_from, m_to, k));
            if (m_t < m_dur) return;
            var d = m_done; m_done = null;
            enabled = false;
            if (d != null) { try { d(); } catch (Exception e) { Plugin.Log.LogError("Drag done: " + e); } }
        }

        // a monster despawned mid-drag comes back from the pool with this still enabled: without switching it off here
        // its first Update would teleport the fresh monster to the old drag target
        void OnDisable() { m_done = null; enabled = false; }

        public static void Drag(GameObject victim, Vector2 to, float dur, Action done = null)
        {
            if (victim == null) return;
            var d = victim.GetComponent<WpnDragged>() ?? victim.AddComponent<WpnDragged>();
            d.Begin(to, dur, done);
        }
    }

    // ---- Gravehook ------------------------------------------------------------------------------------
    /// <summary>The thrown hook: the monster it catches is hauled back to just in front of the thrower.</summary>
    public class WpnTetherFx : MonoBehaviour
    {
        public const float StopDistance = 13f, MaxPull = 110f;

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_source == null) return;
            var hero = d.m_source.m_sourceOwnerPlayer;
            var v = d.m_victim;
            var h = v.GetComponent<Health>();
            if (hero == null || h == null || !h.IsAlive() || v.GetComponent<Player>() == null) return;
            if (h.GetHealthMax() > 30f) return;                       // bosses and boss parts stay put
            Vector2 hp = hero.transform.position, vp = v.transform.position;
            var delta = vp - hp;
            float dist = delta.magnitude;
            if (dist <= StopDistance + 2f || dist > MaxPull + 40f) return;
            var target = hp + delta / dist * StopDistance;
            target = ModUtil.SafePoint(vp, target, 4f);
            WpnDragged.Drag(v, target, 0.22f);
            // the chain, link by link from hand to hook
            int n = Mathf.Clamp(Mathf.RoundToInt(dist / 9f), 2, 12);
            for (int i = 1; i < n; i++)
                WpnUtil.Spawn(WeaponFx.ChainLink, Vector2.Lerp(hp + new Vector2(0f, 8f), vp + new Vector2(0f, 6f), i / (float)n));
        }
    }

    // ---- Moonglaive -----------------------------------------------------------------------------------
    /// <summary>Flies the glaive out (decelerating), lets it hang, then homes it back to the thrower's hand.</summary>
    public class WpnGlaiveFx : MonoBehaviour
    {
        public const float OutSpeed = 330f, OutTime = 0.3f, Hang = 0.08f, BackSpeed = 120f, BackAccel = 520f;
        Vector2 m_dir;
        float m_t, m_back;
        int m_phase;
        bool m_init;
        Transform m_owner;

        public void Reset() { m_init = false; m_phase = 0; m_t = 0f; m_back = BackSpeed; m_owner = null; }

        void MsgSetSpawner(DamageSource s)
        {
            Reset();
            if (s != null && s.m_sourceOwnerPlayer != null) m_owner = s.m_sourceOwnerPlayer.transform;
        }

        void Update()
        {
            float dt = Time.deltaTime;
            Vector2 p = transform.position;
            if (!m_init) { m_dir = WpnUtil.Facing(transform).normalized; m_init = true; }
            m_t += dt;
            if (m_phase == 0)
            {
                float sp = Mathf.Lerp(OutSpeed, 30f, m_t / OutTime);
                var step = m_dir * sp * dt;
                if (!ModUtil.Clear(p, p + m_dir * 6f))
                {
                    WpnUtil.Spawn(WeaponFx.ImpWall("Moonglaive"), p + m_dir * 5f);   // it rings off the wall and turns home
                    m_phase = 2; m_t = 0f; return;
                }
                Move(p + step);
                if (m_t >= OutTime) { m_phase = 1; m_t = 0f; }
            }
            else if (m_phase == 1)
            {
                if (m_t >= Hang) { m_phase = 2; m_t = 0f; }
            }
            else
            {
                if (m_owner == null || !m_owner.gameObject.activeInHierarchy) { SystemPool.Despawn(gameObject); return; }
                var to = (Vector2)m_owner.position + new Vector2(0f, 8f) - p;
                float d = to.magnitude;
                m_back += BackAccel * dt;
                if (d < 7f) { SystemPool.Despawn(gameObject); return; }
                Move(p + to / d * Mathf.Min(d, m_back * dt));
            }
        }

        void Move(Vector2 p) { transform.position = new Vector3(p.x, p.y, transform.position.z); }
    }

    // ---- Riftblade ------------------------------------------------------------------------------------
    public class WpnRiftFx : MonoBehaviour
    {
        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null) return;
            WpnRiftMark.Add(d.m_victim, d.m_amount);
        }
    }

    /// <summary>On a monster: stores Riftblade damage for a moment, then snaps for a share of it.</summary>
    public class WpnRiftMark : MonoBehaviour
    {
        public const float Delay = 0.8f, Share = 0.35f;
        float m_stored, m_timer;
        bool m_armed;
        GameObject m_mark;

        public static void Add(GameObject v, float amount)
        {
            var h = v.GetComponent<Health>();
            if (h == null || !h.IsAlive() || amount <= 0f) return;
            var m = v.GetComponent<WpnRiftMark>() ?? v.AddComponent<WpnRiftMark>();
            m.Store(amount);
        }

        void Store(float a)
        {
            m_stored += a;
            if (m_armed) return;
            m_armed = true;
            m_timer = Delay;
            m_mark = WpnUtil.Spawn(WeaponFx.RiftMark, (Vector2)transform.position + new Vector2(0f, 7f));
            ModAttach.Front(m_mark, gameObject);
        }

        void Update()
        {
            if (!m_armed) return;
            if (m_mark != null && m_mark.activeInHierarchy)
                m_mark.transform.position = new Vector3(transform.position.x, transform.position.y + 7f, m_mark.transform.position.z);
            m_timer -= Time.deltaTime;
            if (m_timer > 0f) return;
            float dmg = m_stored * Share;
            Clear();
            WpnUtil.Spawn(WeaponFx.RiftSnap, (Vector2)transform.position + new Vector2(0f, 7f));
            WpnUtil.Hit(gameObject, dmg, Vector2.zero, 0f);
        }

        void Clear()
        {
            m_armed = false; m_stored = 0f;
            if (m_mark != null && m_mark.activeInHierarchy) SystemPool.Despawn(m_mark);
            m_mark = null;
        }

        void OnDisable() { Clear(); }
    }

    // ---- Snake-Eyes -----------------------------------------------------------------------------------
    /// <summary>Rolls a d6 for each blow as it is swung: 1 = 40%, 2-5 = full, 6 = double plus a jackpot burst.</summary>
    public class WpnDiceFx : MonoBehaviour
    {
        public float baseDamage = 1f;
        public int roll;

        void MsgSetSpawner(DamageSource s)
        {
            roll = UnityEngine.Random.Range(1, 7);
            float m = roll == 1 ? 0.4f : roll == 6 ? 2f : 1f;
            WpnUtil.SetDamage(GetComponent<DamageEffect>(), baseDamage * m);
            var owner = s != null ? s.m_sourceOwnerPlayer : null;
            Vector2 at = owner != null ? (Vector2)owner.transform.position : (Vector2)transform.position;
            WpnUtil.Spawn(WeaponFx.Dice[roll - 1], at + new Vector2(0f, 24f));
            if (roll == 6 && WeaponFx.Jackpot != null)
                WpnUtil.Spawn(WeaponFx.Jackpot, (Vector2)transform.position + (Vector2)(transform.rotation * Vector3.right) * 10f, s);   // spawn rotation = facing
            // the face pops up as a number over each monster the blow lands on (1 grey-red, 6 gold)
            var rr = GetComponent<RollReadout>() ?? gameObject.AddComponent<RollReadout>();
            rr.roll = roll; rr.max = 6; rr.fromSource = false; rr.besideHit = false;
        }
    }

    // ---- Tidebreaker ----------------------------------------------------------------------------------
    /// <summary>The rolling wave: every monster it touches is carried along; one carried into a wall is slammed.</summary>
    public class WpnWaveFx : MonoBehaviour
    {
        public const float Carry = 24f, SlamDamage = 0.9f;
        readonly HashSet<GameObject> m_slammed = new HashSet<GameObject>();
        Vector2 m_dir;
        bool m_init;
        DamageSource m_src;

        public void Reset() { m_slammed.Clear(); m_init = false; m_src = null; }
        void MsgSetSpawner(DamageSource s) { Reset(); m_src = s; }

        void Update() { if (!m_init) { m_dir = WpnUtil.Facing(transform).normalized; m_init = true; } }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null) return;
            if (!m_init) { m_dir = WpnUtil.Facing(transform).normalized; m_init = true; }
            var v = d.m_victim;
            var h = v.GetComponent<Health>();
            if (h == null || !h.IsAlive() || v.GetComponent<Player>() == null || h.GetHealthMax() > 30f) return;
            Vector2 vp = v.transform.position;
            var want = vp + m_dir * Carry;
            var safe = ModUtil.SafePoint(vp, want, 5f);
            bool wall = (want - safe).sqrMagnitude > 4f;
            var dir = m_dir;
            var mod = m_src != null ? m_src.m_damageMod : null;
            WpnDragged.Drag(v, safe, 0.25f, () =>
            {
                if (!wall || m_slammed.Contains(v)) return;
                m_slammed.Add(v);
                float amt = mod != null ? mod.Modify(SlamDamage) : SlamDamage;
                WpnUtil.Spawn(WeaponFx.Splash, (Vector2)v.transform.position + dir * 4f);
                WpnUtil.Hit(v, amt, dir, 0.3f, FxFactory.GetStatus("StatusDizzy"));
            });
        }
    }

    // ---- Leechfang ------------------------------------------------------------------------------------
    public class WpnLeechFx : MonoBehaviour
    {
        public const int Every = 5;
        public const float Heal = 0.25f;

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_source == null) return;
            var hero = d.m_source.m_sourceOwnerPlayer;
            var rt = WeaponRuntime.On(hero);
            if (rt == null) return;
            bool heal = ++rt.leechHits % Every == 0;
            var bead = WpnUtil.Spawn(WeaponFx.Bead, (Vector2)d.m_victim.transform.position + new Vector2(0f, 6f));
            var b = bead != null ? bead.GetComponent<WpnBeadFx>() : null;
            if (b != null) { b.target = hero.transform; b.heals = heal; }
            else if (heal) WpnBeadFx.Mend(hero);
        }
    }

    /// <summary>A drop of blood that flies to the hero; the healing one mends on arrival.</summary>
    public class WpnBeadFx : MonoBehaviour
    {
        public Transform target;
        public bool heals;
        public Action arrive;           // optional: run on arrival (plague spores infect their target)
        float m_speed;

        public void Reset() { target = null; heals = false; arrive = null; m_speed = 60f; }

        void Update()
        {
            if (target == null || !target.gameObject.activeInHierarchy) { if (target != null) { target = null; arrive = null; SystemPool.Despawn(gameObject); } return; }
            m_speed += 600f * Time.deltaTime;
            Vector2 p = transform.position, to = (Vector2)target.position + new Vector2(0f, 8f) - p;
            float d = to.magnitude;
            if (d < 5f)
            {
                if (heals) Mend(target.gameObject);
                var a = arrive; arrive = null;
                if (a != null) { try { a(); } catch (Exception e) { Plugin.Log.LogError("Bead arrive: " + e); } }
                target = null;
                SystemPool.Despawn(gameObject);
                return;
            }
            p += to / d * Mathf.Min(d, m_speed * Time.deltaTime);
            transform.position = new Vector3(p.x, p.y, transform.position.z);
        }

        public static void Mend(GameObject hero)
        {
            var h = hero != null ? hero.GetComponent<Health>() : null;
            if (h == null || !h.IsAlive()) return;
            h.Heal(WpnLeechFx.Heal);
            WpnUtil.Spawn(WeaponFx.LeechHeal, (Vector2)hero.transform.position + new Vector2(0f, 8f));
        }
    }

    // ---- Dirge Maul -----------------------------------------------------------------------------------
    /// <summary>Counts the hero's bell rings; every third one tolls a wider ring at the same spot shortly after.</summary>
    public class WpnBellFx : MonoBehaviour
    {
        public const int Every = 3;
        public const float TollDelay = 0.45f;

        void MsgSetSpawner(DamageSource s)
        {
            if (s == null || s.m_sourceOwnerPlayer == null) return;
            var rt = WeaponRuntime.On(s.m_sourceOwnerPlayer);
            if (rt == null || ++rt.bellSlams % Every != 0) return;
            Vector2 at = transform.position;
            var src = new DamageSource(null, s.m_sourceOwner, s.m_sourcePlayer, -1, -1, s.m_damageMod, false);
            rt.Later(TollDelay, () => WpnUtil.Spawn(WeaponFx.BellToll, at, src));
        }
    }

    // ---- Wickstaff ------------------------------------------------------------------------------------
    /// <summary>Soul fire: a monster that dies while standing in it (burnt in the last 0.6 s) lets loose a wisp
    /// at the nearest other monster, whatever landed the killing blow.</summary>
    public class WpnSoulFireFx : MonoBehaviour
    {
        public const float WispRange = 120f, Memory = 0.6f;
        readonly HashSet<GameObject> m_freed = new HashSet<GameObject>();
        readonly Dictionary<GameObject, float> m_touched = new Dictionary<GameObject, float>();
        readonly List<GameObject> m_scratch = new List<GameObject>();
        DamageSource m_src;

        public void Reset() { m_freed.Clear(); m_touched.Clear(); m_src = null; }
        void MsgSetSpawner(DamageSource s) { Reset(); m_src = s; }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_victim.GetComponent<Player>() == null) return;
            if (m_src == null) m_src = d.m_source;
            m_touched[d.m_victim] = Time.time;
            Check(d.m_victim);
        }

        void Update()
        {
            if (m_touched.Count == 0) return;
            m_scratch.Clear();
            m_scratch.AddRange(m_touched.Keys);
            foreach (var v in m_scratch)
            {
                if (v == null || Time.time - m_touched[v] > Memory) { m_touched.Remove(v); continue; }
                Check(v);
            }
        }

        void Check(GameObject v)
        {
            var h = v.GetComponent<Health>();
            if (h == null || h.IsAlive() || !m_freed.Add(v)) return;
            m_touched.Remove(v);
            ReleaseWisp(v, m_src);
        }

        public static void ReleaseWisp(GameObject from, DamageSource src)
        {
            Vector2 p = (Vector2)from.transform.position + new Vector2(0f, 8f);
            var next = WpnUtil.Nearest(p, WispRange, new[] { from });
            float ang = 90f;
            if (next != null) { var d = (Vector2)next.transform.position + new Vector2(0f, 6f) - p; ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg; }
            var w = WpnUtil.Spawn(WeaponFx.Wisp, p, src, ang);
            var s = w != null ? w.GetComponent<WpnSeekFx>() : null;
            if (s != null) s.Aim(ang, next);
        }
    }

    /// <summary>Steers a wisp toward its target (or the nearest monster) at a limited turn rate.</summary>
    public class WpnSeekFx : MonoBehaviour
    {
        public const float Speed = 150f, Turn = 300f;
        float m_heading, m_retarget;
        GameObject m_target;
        bool m_aimed;

        public void Reset() { m_aimed = false; m_target = null; m_retarget = 0f; }
        public void Aim(float heading, GameObject target) { m_heading = heading; m_target = target; m_aimed = true; }

        void Update()
        {
            if (!m_aimed) { m_heading = transform.eulerAngles.z; m_aimed = true; }
            Vector2 p = transform.position;
            m_retarget -= Time.deltaTime;
            if (m_target != null && (!m_target.activeInHierarchy || !WpnUtil.LiveMonster(m_target.GetComponent<Player>(), ModUtil.Hero())))
                m_target = null;
            // Nearest() scans every Player in the scene: look again 5 times a second, not every frame
            if (m_target == null && m_retarget <= 0f)
            {
                m_retarget = 0.2f;
                m_target = WpnUtil.Nearest(p, 140f, null);
            }
            if (m_target != null)
            {
                var d = (Vector2)m_target.transform.position + new Vector2(0f, 6f) - p;
                float want = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
                m_heading = Mathf.MoveTowardsAngle(m_heading, want, Turn * Time.deltaTime);
            }
            var dir = new Vector2(Mathf.Cos(m_heading * Mathf.Deg2Rad), Mathf.Sin(m_heading * Mathf.Deg2Rad));
            p += dir * Speed * Time.deltaTime;
            transform.position = new Vector3(p.x, p.y, transform.position.z);
            transform.rotation = Quaternion.Euler(0f, 0f, m_heading);
            var sc = transform.localScale;
            if (sc.x < 0f) transform.localScale = new Vector3(-sc.x, sc.y, sc.z);
        }
    }

    // ---- Arcbolt --------------------------------------------------------------------------------------
    /// <summary>On a landed bolt, lightning jumps to the nearest unstruck monster, up to three times, at 60% each.</summary>
    public class WpnChainFx : MonoBehaviour
    {
        public const int Jumps = 3;
        public const float Range = 48f, Falloff = 0.6f, Step = 0.07f;
        bool m_done;

        public void Reset() { m_done = false; }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (m_done || d == null || d.m_victim == null || d.m_source == null) return;
            m_done = true;
            var rt = WeaponRuntime.On(d.m_source.m_sourceOwnerPlayer);
            if (rt != null) rt.StartCoroutine(Chain(d.m_victim, d.m_amount));
        }

        static IEnumerator Chain(GameObject first, float amount)
        {
            var struck = new List<GameObject> { first };
            var cur = first;
            Vector2 curPos = first.transform.position;
            float dmg = amount;
            WpnUtil.Spawn(WeaponFx.Spark, curPos + new Vector2(0f, 7f));
            for (int k = 0; k < Jumps; k++)
            {
                yield return new WaitForSeconds(Step);
                if (cur != null && cur.activeInHierarchy) curPos = cur.transform.position;
                var next = WpnUtil.Nearest(curPos, Range, struck);
                if (next == null) yield break;
                dmg *= Falloff;
                Vector2 np = next.transform.position;
                WpnUtil.Span(WeaponFx.Arc, curPos + new Vector2(0f, 7f), np + new Vector2(0f, 7f), 48f);
                WpnUtil.Spawn(WeaponFx.Spark, np + new Vector2(0f, 7f));
                WpnUtil.Hit(next, dmg, (np - curPos).normalized, 0.2f);
                struck.Add(next);
                cur = next; curPos = np;
            }
        }
    }
}

namespace CrawlFurther.Content.Weapons
{
    using CrawlFurther.Art;
    using CrawlFurther.Heroes;
    using CrawlFurther.Items;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    // =====================================================================================================
    //  v0.7.2: fifteen more weapons, one new family each, across every vanilla weapon base.
    // =====================================================================================================
    public static partial class WeaponFx
    {
        public static GameObject FrostSlash, FrostChill, FrostChill2, FrostShatter;
        public static GameObject MercySlash, MercyX;
        public static GameObject ReapA, ReapB, ReapSoul;
        public static GameObject StarSlam, StarWell;
        public static GameObject HydraArrow, HydraShard, HydraSplit;
        public static GameObject GuardBash, GuardRing, GuardBlock;
        public static GameObject HeartBolt, HeartPierce;
        public static GameObject KrisStab, KrisBack;
        public static GameObject BlightSwing, BlightBolt, BlightCloud, BlightSpore;
        public static GameObject OrrerySwing, OrreryBolt, OrreryStar;
        public static GameObject GrudgeStone, GrudgeBrand;
        public static GameObject MidasCoin, MidasGold;
        public static GameObject LanceThrust, LanceCharge;
        public static GameObject LashBody, LashTip;
        public static GameObject Kunai, KunaiSlash, KunaiMark, KunaiPop;

        /// <summary>Projectile contacts: pass through monsters and props, still stop on walls.</summary>
        static void Pierce(GameObject go)
        {
            var d = go != null ? go.GetComponent<DamageEffect>() : null;
            if (d == null || d.m_contactData == null) return;
            foreach (var c in d.m_contactData)
                if (c != null) c.m_destroyOnHit = (c.m_layerMask.value & (1 << 9)) != 0;      // layer 9 = Wall
        }

        /// <summary>A purely visual effect that keeps its rotation (streaks that follow the aim).</summary>
        static GameObject VisRot(string name, string art, string anim)
        {
            var go = Vis(name, art, anim);
            if (go != null) FxFactory.SetEffect(go, destroyOnAnimEnd: true, canFlip: true, freeRotate: true);
            return go;
        }

        static void Build2()
        {
            var slow = FxFactory.GetStatus("StatusLavaSteveGoo");
            var daze = FxFactory.GetStatus("StatusDizzy");

            // ---- Frostbrand (frost: chill stacks, the third shatters) ----------------------------------
            FrostSlash = Swipe("ModWpnFrostSlash", "1HandedSwordSwipe1", "FxWpnFrostbrand", "Slash", 1.0f, 0.6f, new Vector2(8.4f, 0.4f), 1f, slow, 0.35f);
            OnSpawn<WpnFrostFx>(FrostSlash, null);
            FrostChill = Vis("ModWpnFrostChill", "FxWpnFrostbrand", "Chill", loop: true, life: WpnChill.Timeout + 0.2f);
            FrostChill2 = Vis("ModWpnFrostChill2", "FxWpnFrostbrand", "Chill2", loop: true, life: WpnChill.Timeout + 0.2f);
            var fb = SpriteSheets.Get("FxWpnFrostbrand");
            FrostShatter = Zone("ModWpnFrostShatter", new ClipBuilder(fb, "Shatter", "ModWpnFrostShatterClip").Once(), fb, WpnChill.ShatterDamage, 0f, 0.8f, 0, 2);
            Box(FrostShatter, 48f, 30f);

            // ---- Mercyblade (execute) ------------------------------------------------------------------
            MercySlash = Swipe("ModWpnMercySlash", "1HandedSwordSwipe2", "FxWpnMercyblade", "Slash", 1.0f, 0.6f, new Vector2(8.4f, -0.8f));
            OnSpawn<WpnMercyFx>(MercySlash, null);
            MercyX = Vis("ModWpnMercyX", "FxWpnMercyblade", "Mercy");

            // ---- Reaper (harvest: kills stack damage until you are hit) --------------------------------
            ReapA = Swipe("ModWpnReapA", "DamageHeroSwipeSkewed", "FxWpnReaper", "Reap", 1.0f, 0.8f, new Vector2(5.5f, 1.3f), 1.25f);
            ReapB = Swipe("ModWpnReapB", "DamageHeroSwipeSkewed", "FxWpnReaper", "Reap2", 1.0f, 0.9f, new Vector2(5.5f, 1.3f), 1.25f);
            OnSpawn<WpnReapFx>(ReapA, null);
            OnSpawn<WpnReapFx>(ReapB, null);
            ReapSoul = Vis("ModWpnReapSoul", "FxWpnReaper", "Soul", loop: true, life: 1.5f);
            OnSpawn<WpnBeadFx>(ReapSoul, b => b.Reset());

            // ---- Starfall Maul (gravity well) ----------------------------------------------------------
            var sf = SpriteSheets.Get("FxWpnStarfall");
            StarSlam = Zone("ModWpnStarSlam", new ClipBuilder(sf, "Slam", "ModWpnStarSlamClip").Once(), sf, 1.0f, 0f, 1.0f, 0, 2, attached: true);
            Box(StarSlam, 29.5f, 20.9f, 13f, 0f);
            Anchor(StarSlam, exPlane.Anchor.MidCenter, new Vector2(13f, 0f));
            StarWell = Zone("ModWpnStarWell", new ClipBuilder(sf, "Well", "ModWpnStarWellClip").Once(), sf, WpnGravityFx.Implode, 0f, 1.2f, 6, -1);
            Box(StarWell, 40f, 26f);
            OnSpawn<WpnGravityFx>(StarWell, g => g.Reset());

            // ---- Hydra Bow (split) ---------------------------------------------------------------------
            HydraShard = Shot("ModWpnHydraShard", "DFX_HeroArrow", "FxWpnHydraBow", "Shard", 380f, 0.35f, WpnSplitFx.ShardDamage, 0.3f);
            HydraArrow = Shot("ModWpnHydraArrow", "DFX_HeroArrow", "FxWpnHydraBow", "Arrow", 380f, 0.6f, 1.1f, 0.5f);
            OnSpawn<WpnSplitFx>(HydraArrow, a => a.Reset());
            HydraSplit = VisRot("ModWpnHydraSplit", "FxWpnHydraBow", "Split");

            // ---- Bulwark Mace (guard) ------------------------------------------------------------------
            GuardBash = Swipe("ModWpnGuardBash", "1HandedSwordSwipe2", "FxWpnBulwark", "Bash", 1.0f, 1.0f, new Vector2(8.4f, -0.8f));
            OnSpawn<WpnGuardFx>(GuardBash, null);
            GuardRing = Vis("ModWpnGuardRing", "FxWpnBulwark", "Guard", loop: true, life: WpnGuardFx.Duration + 0.5f);
            GuardBlock = Vis("ModWpnGuardBlock", "FxWpnBulwark", "Block");

            // ---- Heartseeker (piercing ramp) -----------------------------------------------------------
            HeartBolt = Shot("ModWpnHeartBolt", "DFX_HeroArrowCrossbow", "FxWpnHeartseeker", "Bolt", 500f, 0.6f, WpnPierceFx.BaseDamage, 0.8f);
            Pierce(HeartBolt);
            OnSpawn<WpnPierceFx>(HeartBolt, p => p.Reset());
            HeartPierce = Vis("ModWpnHeartPierce", "FxWpnHeartseeker", "Pierce");

            // ---- Shadow Kris (backstab) ----------------------------------------------------------------
            KrisStab = Swipe("ModWpnKrisStab", "DaggerDashthrough", "FxWpnKris", "Stab", 1.0f, 0.5f, new Vector2(6.9f, -1.9f));
            OnSpawn<WpnKrisFx>(KrisStab, null);
            KrisBack = Vis("ModWpnKrisBack", "FxWpnKris", "Backstab");

            // ---- Blightstaff (contagion) ---------------------------------------------------------------
            BlightSwing = Swipe("ModWpnBlightSwing", "MagicStaffSwipe", "FxWpnBlightstaff", "Swing", 0.2f, 0.8f, new Vector2(5.2f, -1.3f));
            BlightBolt = Shot("ModWpnBlightBolt", "DFX_HeroArrow", "FxWpnBlightstaff", "Bolt", 170f, 0.85f, 0.45f, 0.3f);
            OnSpawn<WpnBlightBoltFx>(BlightBolt, null);
            BlightCloud = Vis("ModWpnBlightCloud", "FxWpnBlightstaff", "Cloud", loop: true, life: WpnPlague.Ticks * WpnPlague.Every + 0.3f);
            BlightSpore = Vis("ModWpnBlightSpore", "FxWpnBlightstaff", "Spore", loop: true, life: 1.5f);
            OnSpawn<WpnBeadFx>(BlightSpore, b => b.Reset());

            // ---- Orrery Staff (orbiting stars) ---------------------------------------------------------
            var orr = SpriteSheets.Get("FxWpnOrrery");
            OrrerySwing = Swipe("ModWpnOrrerySwing", "MagicStaffSwipe", "FxWpnOrrery", "Swing", 0.2f, 0.8f, new Vector2(5.2f, -1.3f));
            OrreryBolt = Shot("ModWpnOrreryBolt", "DFX_HeroArrow", "FxWpnOrrery", "Bolt", 260f, 0.6f, 0.45f, 0.3f);
            OrreryStar = Zone("ModWpnOrreryStar", new ClipBuilder(orr, "Star", "ModWpnOrreryStarClip").Once().Repeat(16), orr,
                              WpnOrbitFx.Damage, WpnOrbitFx.Rate, 0.4f, 0, -1);
            Box(OrreryStar, 9f, 9f);
            OnSpawn<WpnOrbitFx>(OrreryStar, o => o.Reset());

            // ---- Grudgestone (vendetta) ----------------------------------------------------------------
            GrudgeStone = FxKit.Projectile("ModWpnGrudgeStone", "SlingProjectile", "FxWpnGrudgestone", "Stone", 0f, 0.75f, WpnGrudgeFx.BaseDamage, 0.5f,
                                           rotate: false, destroyOnHit: false);
            if (GrudgeStone != null) FxFactory.SetMotion(GrudgeStone, 0f, enabled: false);       // WpnGrudgeFx flies it
            OnSpawn<WpnGrudgeFx>(GrudgeStone, g => g.Reset());
            GrudgeBrand = Vis("ModWpnGrudgeBrand", "FxWpnGrudgestone", "Grudge", loop: true, life: WpnGrudgeFx.Window + 0.5f);

            // ---- Midas Sling (wealth) ------------------------------------------------------------------
            MidasCoin = FxKit.Projectile("ModWpnMidasCoin", "SlingProjectile", "FxWpnMidas", "Coin", 210f, 0.9f, 0.55f, 0.5f,
                                         accel: 0.28f, speedMax: 0.1f, rotate: false, destroyOnHit: false);
            OnSpawn<WpnMidasFx>(MidasCoin, m => m.Reset());
            MidasGold = Vis("ModWpnMidasGold", "FxWpnMidas", "Gold");

            // ---- Charger Lance (momentum) --------------------------------------------------------------
            LanceThrust = Swipe("ModWpnLanceThrust", "SpearSwipe", "FxWpnLance", "Thrust", 1.0f, 0.8f, new Vector2(1.7f, -2.1f));
            OnSpawn<WpnChargeFx>(LanceThrust, null);
            LanceCharge = VisRot("ModWpnLanceCharge", "FxWpnLance", "Charge");

            // ---- Viper Lash (sweet spot) ---------------------------------------------------------------
            LashBody = Swipe("ModWpnLashBody", "SpearSwipe", "FxWpnLash", "Lash", WpnLashFx.BodyDamage, 0.3f, new Vector2(WpnLashFx.BodyX, 0f));
            Box(LashBody, 26f, 8f, WpnLashFx.BodyX, 0f);
            OnSpawn<WpnLashFx>(LashBody, l => l.Reset());
            var ls = SpriteSheets.Get("FxWpnLash");
            LashTip = Zone("ModWpnLashTip", new ClipBuilder(ls, "Crack", "ModWpnLashTipClip").Once(), ls, WpnLashFx.TipDamage, 0f, 1.1f, 0, 2, daze, 0.25f);
            Box(LashTip, 14f, 12f);

            // ---- Hunter's Kunai (mark and finish) ------------------------------------------------------
            Kunai = Shot("ModWpnKunai", "KnivesProjectile", "FxWpnKunai", "Kunai", 320f, 0.4f, 0.8f, 0.3f);
            OnSpawn<WpnKunaiFx>(Kunai, null);
            KunaiSlash = Swipe("ModWpnKunaiSlash", "1HandedSwordSwipe1", "FxWpnKunai", "Slash", 0.9f, 0.6f, new Vector2(8.4f, 0.4f));
            OnSpawn<WpnHuntSlashFx>(KunaiSlash, null);
            KunaiMark = Vis("ModWpnKunaiMark", "FxWpnKunai", "Mark", loop: true, life: WpnHuntMark.Duration + 0.2f);
            KunaiPop = Vis("ModWpnKunaiPop", "FxWpnKunai", "Pop");
        }
    }

    public static partial class WeaponPack
    {
        public static readonly List<WeaponDef> Defs2 = new List<WeaponDef>
        {
            new WeaponDef { id = "Frostbrand", name = "Frostbrand", family = "Frost", baseWeapon = "Weapon1HandedSword", baseCombo = 1,
                cost = 60, damageMult = 0.7f, comboCooldown = 0.3f,
                description = "Chilling cuts that slow, then shatter frozen foes",
                effects = () => L(Melee(WeaponFx.FrostSlash, 0f, 0f, 3f, 2f)),
                attacks = { new WeaponAttack(3, 0.46f, 1.0f, "a3", 0), new WeaponAttack(4, 0.28f, 1.0f, "a2", 0), new WeaponAttack(5, 0.20f, 1.0f, "a3", 0) } },

            new WeaponDef { id = "Mercyblade", name = "Mercyblade", family = "Execute", baseWeapon = "Weapon1HandedSword", baseCombo = 0,
                cost = 50, damageMult = 0.75f, comboCooldown = 0.3f,
                description = "Strikes twice against badly hurt foes",
                effects = () => L(Melee(WeaponFx.MercySlash, 0f, 0f, 4f, 3f)),
                attacks = { new WeaponAttack(0, 0.33f, 1.0f, "a1", 0), new WeaponAttack(1, 0.38f, 1.0f, "a0", 0), new WeaponAttack(2, 0.36f, 1.0f, "a1", 0) } },

            new WeaponDef { id = "Reaper", name = "Reaper", family = "Harvest", baseWeapon = "Weapon2HandedSword", baseCombo = 2,
                cost = 90, damageMult = 0.8f, comboCooldown = 0.35f,
                description = "Each kill sharpens the scythe, until you are hit",
                effects = () => L(Melee(WeaponFx.ReapA, 4f, 0f), Melee(WeaponFx.ReapB, 0f, 1f, angle: 15f), Melee(WeaponFx.ReapB, 0f, 1f, angle: -15f)),
                attacks = { new WeaponAttack(4, 0.30f, 1.0f, "a1", 0), new WeaponAttack(1, 0.32f, 1.0f, "a1", 0), new WeaponAttack(6, 0.48f, 1.0f, "a9", 1, "a10", 2) } },

            new WeaponDef { id = "Starfall", name = "Starfall Maul", family = "Gravity", baseWeapon = "WeaponBattleAxe", baseCombo = 0,
                cost = 85, damageMult = 1.45f, comboCooldown = 0f,
                description = "Slams open a star well that drags foes in",
                effects = () => L(Melee(WeaponFx.StarSlam, 2f, -9f, 0f, 0f, destroyOnAnimEnd: true),
                                  Fire(WeaponFx.StarWell, 18f, -10f, new Vector2(0f, -8f), new Vector2(0f, 8f))),
                attacks = { new WeaponAttack(0, 1.1f, 1.0f, "a3", 0, "a2", 1) } },

            new WeaponDef { id = "HydraBow", name = "Hydra Bow", family = "Split", baseWeapon = "WeaponBow", baseCombo = 0,
                cost = 70, damageMult = 1.0f, comboCooldown = 0f,
                description = "Arrows that split into three fangs",
                effects = () => L(Fire(WeaponFx.HydraArrow, 0f, -2f)),
                attacks = { new WeaponAttack(0, 1.0f, 1.0f, "a0", 0) } },

            new WeaponDef { id = "Bulwark", name = "Bulwark Mace", family = "Guard", baseWeapon = "WeaponClub", baseCombo = 0,
                cost = 50, damageMult = 1.15f, comboCooldown = 0.3f,
                description = "Every third hit raises a ward that blocks a blow",
                effects = () => L(Melee(WeaponFx.GuardBash, 0f, -1f, 3f, 6f)),
                attacks = { new WeaponAttack(1, 0.39f, 1.0f, "a1", 0), new WeaponAttack(6, 0.46f, 1.0f, "a1", 0) } },

            new WeaponDef { id = "Heartseeker", name = "Heartseeker", family = "Pierce", baseWeapon = "WeaponCrossbow", baseCombo = 0,
                cost = 70, damageMult = 1.0f, comboCooldown = 1.3f,
                description = "Heavy bolts that pierce through foes, hitting harder as they go",
                effects = () => L(Fire(WeaponFx.HeartBolt, 5f, 0f)),
                attacks = { new WeaponAttack(3, 0.7f, 1.0f, "a0", 0) } },

            new WeaponDef { id = "Kris", name = "Shadow Kris", family = "Backstab", baseWeapon = "WeaponDagger", baseCombo = 0,
                cost = 50, damageMult = 0.7f, comboCooldown = 0.2f,
                description = "Quick stabs that hit harder from behind",
                effects = () => L(Melee(WeaponFx.KrisStab, 5f, 0f, 5f, 5f)),
                attacks = { new WeaponAttack(0, 0.27f, 1.0f, "a1", 0), new WeaponAttack(1, 0.32f, 1.0f, "a1", 0), new WeaponAttack(2, 0.31f, 1.0f, "a0", 0) } },

            new WeaponDef { id = "Blightstaff", name = "Blightstaff", family = "Contagion", baseWeapon = "WeaponMagicStaff", baseCombo = -1,
                cost = 80, damageMult = 1.0f, comboCooldown = 0f,
                description = "Plague bolts that spread sickness from foe to foe",
                effects = () => L(Melee(WeaponFx.BlightSwing, 0f, 1f), Fire(WeaponFx.BlightBolt, 4f, -2f)),
                attacks = { new WeaponAttack(0, 1.1f, 1.0f, "a0", 0, "mprj", 1) } },

            new WeaponDef { id = "Orrery", name = "Orrery Staff", family = "Orbit", baseWeapon = "WeaponMagicStaff", baseCombo = -1,
                cost = 80, damageMult = 1.0f, comboCooldown = 0f,
                description = "Shoots star bolts and gathers stars that circle you",
                effects = () => L(Melee(WeaponFx.OrrerySwing, 0f, 1f), Fire(WeaponFx.OrreryBolt, 4f, -2f), Fire(WeaponFx.OrreryStar, 0f, -2f)),
                attacks = { new WeaponAttack(0, 1.1f, 1.0f, "a0", 0, "mprj", 1, "msmn1", 2) } },

            new WeaponDef { id = "Grudgestone", name = "Grudgestone", family = "Vendetta", baseWeapon = "WeaponSling", baseCombo = 0,
                cost = 35, damageMult = 1.0f, comboCooldown = 0f,
                description = "Stones seek out the last monster that hurt you",
                effects = () => L(Fire(WeaponFx.GrudgeStone, 0f, -9f)),
                attacks = { new WeaponAttack(0, 0.3f, 1.0f), new WeaponAttack(1, 0.86f, 1.0f, "a0", 0) } },

            new WeaponDef { id = "Midas", name = "Midas Sling", family = "Wealth", baseWeapon = "WeaponSling", baseCombo = 0,
                cost = 40, damageMult = 1.0f, comboCooldown = 0f,
                description = "Throws coins that hit harder the richer you are",
                effects = () => L(Fire(WeaponFx.MidasCoin, 0f, -9f)),
                attacks = { new WeaponAttack(0, 0.3f, 1.0f), new WeaponAttack(1, 0.86f, 1.0f, "a0", 0) } },

            new WeaponDef { id = "Lance", name = "Charger Lance", family = "Momentum", baseWeapon = "WeaponSpear", baseCombo = 0,
                cost = 80, damageMult = 1.0f, comboCooldown = 0.3f,
                description = "Run, then charge to bowl monsters over",
                effects = () => L(Melee(WeaponFx.LanceThrust, 14f, 2f, 3f, 3f)),
                attacks = { new WeaponAttack(0, 0.35f, 1.0f, "a1", 0), new WeaponAttack(1, 0.46f, 1.0f, "a1", 0) } },

            new WeaponDef { id = "Lash", name = "Viper Lash", family = "Sweet spot", baseWeapon = "WeaponThrowingKnives", baseCombo = 0,
                cost = 65, damageMult = 1.0f, comboCooldown = 0.3f,
                description = "A long whip. Its tip cracks hardest",
                effects = () => L(Melee(WeaponFx.LashBody, 0f, -1f, 2f, 2f)),
                attacks = { new WeaponAttack(0, 0.35f, 1.0f, "a1", 0), new WeaponAttack(2, 0.35f, 1.0f, "a0", 0), new WeaponAttack(3, 0.45f, 1.0f, "a2", 0) } },

            new WeaponDef { id = "Kunai", name = "Hunter's Kunai", family = "Mark", baseWeapon = "WeaponThrowingKnives", baseCombo = 1,
                cost = 65, damageMult = 1.0f, comboCooldown = 0.4f,
                description = "Throw a kunai to mark a foe, then slash it for extra damage",
                effects = () => L(Fire(WeaponFx.Kunai, 0f, -2f), Melee(WeaponFx.KunaiSlash, 0f, -1f, 2f, 2f)),
                attacks = { new WeaponAttack(1, 0.35f, 1.0f, "a0", 0), new WeaponAttack(3, 0.45f, 1.0f, "a2", 1), new WeaponAttack(4, 0.25f, 1.0f, "a3", 1) } },
        };
    }

    // ----------------------------------------------------------------------------------------------- runtime (set 2)
    /// <summary>A visual that stays on a moving object (marks over monsters, the guard ring round the hero).</summary>
    public class WpnFollowFx : MonoBehaviour
    {
        public Transform target;
        public Vector2 offset;

        public static GameObject Attach(GameObject tmpl, GameObject to, Vector2 offset)
        {
            if (tmpl == null || to == null) return null;
            var go = WpnUtil.Spawn(tmpl, (Vector2)to.transform.position + offset);
            if (go == null) return null;
            var f = go.GetComponent<WpnFollowFx>() ?? go.AddComponent<WpnFollowFx>();
            f.target = to.transform; f.offset = offset;
            ModAttach.Front(go, to);      // a mark up the body would otherwise sort behind it and be hidden
            return go;
        }

        /// <summary>Replace a following visual with a fresh one (its own lifetime starts again): a mark refreshed by a
        /// new hit must not vanish when the first one's clock runs out.</summary>
        public static GameObject Refresh(GameObject old, GameObject tmpl, GameObject to, Vector2 offset)
        {
            // only if it is still ours: a stale reference may point at a pooled copy someone else is now using
            var f = old != null && old.activeInHierarchy ? old.GetComponent<WpnFollowFx>() : null;
            if (f != null && to != null && f.target == to.transform)
            {
                f.target = null;
                SystemPool.Despawn(old);
            }
            return Attach(tmpl, to, offset);
        }

        /// <summary>True while `fx` is a live visual following `to` (a pooled copy reused by someone else is not).</summary>
        public static bool Follows(GameObject fx, GameObject to)
        {
            var f = fx != null && fx.activeInHierarchy ? fx.GetComponent<WpnFollowFx>() : null;
            return f != null && to != null && f.target == to.transform;
        }

        /// <summary>Remove a following visual, but only if it is still ours.</summary>
        public static void Drop(GameObject fx, GameObject to)
        {
            if (!Follows(fx, to)) return;
            fx.GetComponent<WpnFollowFx>().target = null;
            SystemPool.Despawn(fx);
        }

        void LateUpdate()
        {
            if (target == null || !target.gameObject.activeInHierarchy) { target = null; SystemPool.Despawn(gameObject); return; }
            transform.position = new Vector3(target.position.x + offset.x, target.position.y + offset.y, transform.position.z);
        }

        void OnDisable() { target = null; }
    }

    // ---- Frostbrand -----------------------------------------------------------------------------------
    public class WpnFrostFx : MonoBehaviour
    {
        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_source == null) return;
            WpnChill.Add(d.m_victim, d.m_source);
        }
    }

    /// <summary>On a monster: Frostbrand chill stacks (2.5 s each refresh); the third shatters into an ice burst.</summary>
    public class WpnChill : MonoBehaviour
    {
        public const int Stacks = 3;
        public const float Timeout = 2.5f, ShatterDamage = 0.85f;
        int m_stacks;
        float m_t;
        GameObject m_fx;

        public static void Add(GameObject v, DamageSource src)
        {
            if (!WpnUtil.Alive(v) || v.GetComponent<Player>() == null) return;
            var c = v.GetComponent<WpnChill>() ?? v.AddComponent<WpnChill>();
            c.Stack(src);
        }

        void Stack(DamageSource src)
        {
            m_t = Timeout;
            if (++m_stacks < Stacks)
            {
                // 1 chill: three flakes; 2 chills: the frost ring (one more shatters)
                var tmpl = m_stacks >= 2 && WeaponFx.FrostChill2 != null ? WeaponFx.FrostChill2 : WeaponFx.FrostChill;
                m_fx = WpnFollowFx.Refresh(m_fx, tmpl, gameObject, new Vector2(0f, 7f));
                return;
            }
            Clear();
            var s = new DamageSource(null, src.m_sourceOwner, src.m_sourcePlayer, -1, -1, src.m_damageMod, false);
            WpnUtil.Spawn(WeaponFx.FrostShatter, (Vector2)transform.position + new Vector2(0f, 6f), s);
        }

        void Update()
        {
            if (m_stacks == 0) return;
            if ((m_t -= Time.deltaTime) <= 0f) Clear();
        }

        void Clear()
        {
            m_stacks = 0;
            if (m_fx != null && m_fx.activeInHierarchy) SystemPool.Despawn(m_fx);
            m_fx = null;
        }

        void OnDisable() { Clear(); }
    }

    // ---- Mercyblade -----------------------------------------------------------------------------------
    public class WpnMercyFx : MonoBehaviour
    {
        public const float Threshold = 0.35f;

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_amount <= 0f) return;
            var h = d.m_victim.GetComponent<Health>();
            if (h == null || !h.IsAlive() || d.m_victim.GetComponent<Player>() == null) return;
            // health before this cut landed
            if ((h.GetHealthCurrent() + d.m_amount) / Mathf.Max(0.01f, h.GetHealthMax()) > Threshold) return;
            WpnUtil.Spawn(WeaponFx.MercyX, (Vector2)d.m_victim.transform.position + new Vector2(0f, 8f));
            WpnUtil.Hit(d.m_victim, d.m_amount, d.m_direction, 0.3f);
        }
    }

    // ---- Reaper ---------------------------------------------------------------------------------------
    public class WpnReapFx : MonoBehaviour
    {
        public const int MaxStacks = 5;
        public const float PerStack = 0.1f;
        readonly HashSet<GameObject> m_reaped = new HashSet<GameObject>();
        WeaponRuntime m_rt;

        void MsgSetSpawner(DamageSource s)
        {
            m_reaped.Clear();
            m_rt = s != null ? WeaponRuntime.On(s.m_sourceOwnerPlayer) : null;
            int st = m_rt != null ? m_rt.reapStacks : 0;
            WpnUtil.SetDamage(GetComponent<DamageEffect>(), 1f + PerStack * st);
        }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || m_rt == null || WpnUtil.Alive(d.m_victim) || !m_reaped.Add(d.m_victim)) return;
            if (d.m_victim.GetComponent<Player>() == null) return;
            if (m_rt.reapStacks < MaxStacks) m_rt.reapStacks++;
            var soul = WpnUtil.Spawn(WeaponFx.ReapSoul, (Vector2)d.m_victim.transform.position + new Vector2(0f, 8f));
            var b = soul != null ? soul.GetComponent<WpnBeadFx>() : null;
            if (b != null) b.target = m_rt.transform;
        }
    }

    // ---- Starfall Maul --------------------------------------------------------------------------------
    /// <summary>The star well: on its first frame every monster within reach is dragged into its centre.</summary>
    public class WpnGravityFx : MonoBehaviour
    {
        public const float Reach = 64f, Implode = 0.45f;
        bool m_done;

        public void Reset() { m_done = false; }

        void Update()
        {
            if (m_done) return;
            m_done = true;
            Vector2 c = transform.position;
            var hero = ModUtil.Hero();
            foreach (var p in UnityEngine.Object.FindObjectsOfType<Player>())
            {
                if (!WpnUtil.LiveMonster(p, hero)) continue;
                var h = p.GetComponent<Health>();
                if (h.GetHealthMax() > 30f) continue;                     // bosses and boss parts stay put
                Vector2 vp = p.transform.position;
                var d = vp - c;
                float dist = d.magnitude;
                if (dist > Reach || dist < 8f) continue;
                var to = ModUtil.SafePoint(vp, c + d / dist * 7f, 4f);
                WpnDragged.Drag(p.gameObject, to, 0.24f);
            }
        }
    }

    // ---- Hydra Bow ------------------------------------------------------------------------------------
    /// <summary>After a short flight the arrow splits into a three-shard fan (an arrow that hits first never splits).</summary>
    public class WpnSplitFx : MonoBehaviour
    {
        public const float SplitAfter = 0.22f, Spread = 12f, ShardDamage = 0.55f;
        float m_t;

        public void Reset() { m_t = 0f; }

        void Update()
        {
            m_t += Time.deltaTime;
            if (m_t < SplitAfter) return;
            m_t = -999f;
            var src = FxFactory.SourceOf(gameObject);
            float a = WpnUtil.Angle(WpnUtil.Facing(transform));
            Vector2 p = transform.position;
            WpnUtil.Spawn(WeaponFx.HydraSplit, p, null, a);
            for (int k = -1; k <= 1; k++) WpnUtil.Spawn(WeaponFx.HydraShard, p, src, a + k * Spread);
            SystemPool.Despawn(gameObject);
        }
    }

    // ---- Bulwark Mace ---------------------------------------------------------------------------------
    public class WpnGuardFx : MonoBehaviour
    {
        public const int Every = 3;
        public const float Duration = 5f, Bash = 0.4f;

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_source == null || d.m_victim.GetComponent<Player>() == null) return;
            var rt = WeaponRuntime.On(d.m_source.m_sourceOwnerPlayer);
            if (rt == null || ++rt.guardHits % Every != 0) return;
            rt.RaiseGuard(d.m_source.m_damageMod);
        }
    }

    // ---- Heartseeker ----------------------------------------------------------------------------------
    public class WpnPierceFx : MonoBehaviour
    {
        public const float BaseDamage = 1.8f, Ramp = 0.4f;
        int m_pierced;

        public void Reset() { m_pierced = 0; WpnUtil.SetDamage(GetComponent<DamageEffect>(), BaseDamage); }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_victim.GetComponent<Player>() == null) return;
            m_pierced++;
            WpnUtil.SetDamage(GetComponent<DamageEffect>(), BaseDamage * (1f + Ramp * m_pierced));
            WpnUtil.Spawn(WeaponFx.HeartPierce, (Vector2)d.m_victim.transform.position + new Vector2(0f, 8f));
        }
    }

    // ---- Shadow Kris ----------------------------------------------------------------------------------
    public class WpnKrisFx : MonoBehaviour
    {
        public const float Bonus = 1.5f;

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_source == null || d.m_amount <= 0f) return;
            var v = d.m_victim;
            var hero = d.m_source.m_sourceOwnerPlayer;
            if (hero == null || v.GetComponent<Player>() == null || !WpnUtil.Alive(v)) return;
            float facing = v.transform.localScale.x < 0f ? -1f : 1f;       // monsters face right unless flipped
            float dx = hero.transform.position.x - v.transform.position.x;
            if (dx * facing > -2f) return;                                  // the hero is not behind it
            WpnUtil.Spawn(WeaponFx.KrisBack, (Vector2)v.transform.position + new Vector2(0f, 8f));
            WpnUtil.Hit(v, d.m_amount * Bonus, d.m_direction, 0.4f);
        }
    }

    // ---- Blightstaff ----------------------------------------------------------------------------------
    public class WpnBlightBoltFx : MonoBehaviour
    {
        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_source == null) return;
            WpnPlague.Infect(d.m_victim, d.m_source.m_damageMod, 0, new HashSet<GameObject>());
        }
    }

    /// <summary>On a monster: plague ticks, then it jumps to the nearest monster not yet sickened by this chain.</summary>
    public class WpnPlague : MonoBehaviour
    {
        public const int Ticks = 4, MaxJumps = 3;
        public const float Every = 0.5f, Tick = 0.15f, Range = 50f;
        int m_ticks, m_gen;
        float m_t;
        bool m_on;
        ValueModifierStack m_mod;
        HashSet<GameObject> m_chain;
        GameObject m_cloud;

        public static void Infect(GameObject v, ValueModifierStack mod, int gen, HashSet<GameObject> chain)
        {
            if (!WpnUtil.Alive(v) || v.GetComponent<Player>() == null) return;
            var p = v.GetComponent<WpnPlague>() ?? v.AddComponent<WpnPlague>();
            chain.Add(v);
            p.Begin(mod, gen, chain);
        }

        void Begin(ValueModifierStack mod, int gen, HashSet<GameObject> chain)
        {
            m_mod = mod; m_chain = chain; m_ticks = 0; m_t = Every;
            if (!m_on || gen < m_gen) m_gen = gen;
            m_on = true;
            m_cloud = WpnFollowFx.Refresh(m_cloud, WeaponFx.BlightCloud, gameObject, new Vector2(0f, 8f));
        }

        void Update()
        {
            if (!m_on) return;
            if (!WpnUtil.Alive(gameObject)) { Spread(); return; }
            if ((m_t -= Time.deltaTime) > 0f) return;
            m_t = Every;
            WpnUtil.Hit(gameObject, WpnUtil.Scaled(m_mod, Tick), Vector2.zero, 0f);
            if (++m_ticks >= Ticks) Spread();
        }

        void Spread()
        {
            m_on = false;
            if (m_cloud != null && m_cloud.activeInHierarchy) SystemPool.Despawn(m_cloud);
            m_cloud = null;
            if (m_gen >= MaxJumps || m_chain == null || SystemMain.GetDeloadInProgress()) return;
            Vector2 from = transform.position;
            var next = WpnUtil.Nearest(from, Range, m_chain);
            if (next == null) return;
            var chain = m_chain; var mod = m_mod; int gen = m_gen + 1;
            m_chain.Add(next);                                   // claimed now so two spores never chase one monster
            var spore = WpnUtil.Spawn(WeaponFx.BlightSpore, from + new Vector2(0f, 8f));
            var b = spore != null ? spore.GetComponent<WpnBeadFx>() : null;
            if (b != null) { b.target = next.transform; b.arrive = () => Infect(next, mod, gen, chain); }
            else Infect(next, mod, gen, chain);
        }

        void OnDisable() { if (m_on) Spread(); }
    }

    // ---- Orrery Staff ---------------------------------------------------------------------------------
    /// <summary>A star that circles its caster; at most three at once (a fourth retires the oldest).</summary>
    public class WpnOrbitFx : MonoBehaviour
    {
        public const int Max = 3;
        public const float Damage = 0.2f, Rate = 0.5f, Radius = 18f, Spin = 400f;
        WeaponRuntime m_rt;

        public void Reset() { m_rt = null; }

        void MsgSetSpawner(DamageSource s)
        {
            m_rt = s != null ? WeaponRuntime.On(s.m_sourceOwnerPlayer) : null;
            if (m_rt != null) m_rt.AddStar(gameObject);
        }

        void LateUpdate()
        {
            if (m_rt == null || !m_rt.gameObject.activeInHierarchy) { if (m_rt != null) { m_rt = null; SystemPool.Despawn(gameObject); } return; }
            int i = Mathf.Max(0, m_rt.stars.IndexOf(gameObject));
            float a = (Time.time * Spin + i * 360f / Max) * Mathf.Deg2Rad;
            var c = m_rt.transform.position;
            transform.position = new Vector3(c.x + Mathf.Cos(a) * Radius, c.y + 8f + Mathf.Sin(a) * Radius * 0.6f, transform.position.z);
        }
    }

    // ---- Grudgestone ----------------------------------------------------------------------------------
    /// <summary>Flies the stone; it bends toward the hero's grudge target and hits that monster twice.</summary>
    public class WpnGrudgeFx : MonoBehaviour
    {
        public const float Window = 8f, BaseDamage = 0.95f, Speed = 230f, Turn = 420f, Seek = 170f;
        float m_heading, m_speed;
        bool m_init;
        WeaponRuntime m_rt;

        public void Reset() { m_init = false; m_rt = null; m_speed = Speed; }

        void MsgSetSpawner(DamageSource s) { Reset(); m_rt = s != null ? WeaponRuntime.On(s.m_sourceOwnerPlayer) : null; }

        void Update()
        {
            if (!m_init) { m_heading = WpnUtil.Angle(WpnUtil.Facing(transform)); m_init = true; }
            Vector2 p = transform.position;
            var t = m_rt != null ? m_rt.grudge : null;
            if (t != null && WpnUtil.Alive(t))
            {
                var d = (Vector2)t.transform.position - p;
                if (d.sqrMagnitude < Seek * Seek)
                    m_heading = Mathf.MoveTowardsAngle(m_heading, WpnUtil.Angle(d), Turn * Time.deltaTime);
            }
            m_speed = Mathf.Max(120f, m_speed - 140f * Time.deltaTime);
            var dir = new Vector2(Mathf.Cos(m_heading * Mathf.Deg2Rad), Mathf.Sin(m_heading * Mathf.Deg2Rad));
            if (!ModUtil.Clear(p, p + dir * 5f))
            {
                WpnUtil.Spawn(WeaponFx.ImpWall("Grudgestone"), p + dir * 4f);
                SystemPool.Despawn(gameObject);
                return;
            }
            p += dir * m_speed * Time.deltaTime;
            transform.position = new Vector3(p.x, p.y, transform.position.z);
        }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || m_rt == null || d.m_victim != m_rt.grudge || !WpnUtil.Alive(d.m_victim)) return;
            WpnUtil.Hit(d.m_victim, d.m_amount, d.m_direction, 0.3f);
            SystemPool.Despawn(gameObject);                                 // vengeance done
        }
    }

    // ---- Midas Sling ----------------------------------------------------------------------------------
    public class WpnMidasFx : MonoBehaviour
    {
        public const float Base = 0.55f, PerGold = 0.0045f, MaxBonus = 0.9f, KillGold = 2f;
        readonly HashSet<GameObject> m_paid = new HashSet<GameObject>();
        PlayerData m_pd;
        int m_tier;
        bool m_tierShown;

        public void Reset() { m_paid.Clear(); m_pd = null; m_tier = 0; m_tierShown = false; }

        void MsgSetSpawner(DamageSource s)
        {
            m_paid.Clear();
            m_pd = s != null ? s.m_sourcePlayer : null;
            float gold = m_pd != null ? m_pd.Gold : 0f;
            float bonus = Mathf.Min(MaxBonus, gold * PerGold);
            WpnUtil.SetDamage(GetComponent<DamageEffect>(), Base + bonus);
            // gold power on the coin itself: plain, glinting (1/3 of the bonus), haloed (2/3 of it: about 134 gold)
            m_tier = bonus >= MaxBonus * 0.66f ? 2 : (bonus >= MaxBonus * 0.33f ? 1 : 0);
            m_tierShown = false;
        }

        void Update()
        {
            if (m_tierShown) return;
            m_tierShown = true;                                             // after the Effect played its default clip
            var clip = m_tier > 0 ? WeaponFx.MidasTiers[m_tier] : null;
            var an = GetComponent<exSpriteAnimation>();
            if (clip != null && an != null) an.Play(clip);
        }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || m_pd == null || WpnUtil.Alive(d.m_victim) || !m_paid.Add(d.m_victim)) return;
            if (d.m_victim.GetComponent<Player>() == null || m_pd.GameData == null) return;
            m_pd.GameData.OnGoldCollected(KillGold);
            WpnUtil.Spawn(WeaponFx.MidasGold, (Vector2)d.m_victim.transform.position + new Vector2(0f, 8f));
        }
    }

    // ---- Charger Lance --------------------------------------------------------------------------------
    public class WpnChargeFx : MonoBehaviour
    {
        public const float RunNeeded = 0.5f, Grace = 0.3f, Mult = 1.8f, Knock = 2.6f;
        bool m_charge, m_shown;

        void MsgSetSpawner(DamageSource s)
        {
            var rt = s != null ? WeaponRuntime.On(s.m_sourceOwnerPlayer) : null;
            m_charge = rt != null && rt.ConsumeCharge();
            m_shown = false;
            var de = GetComponent<DamageEffect>();
            WpnUtil.SetDamage(de, m_charge ? Mult : 1f);
            WpnUtil.SetKnock(de, m_charge ? Knock : 0.8f);
        }

        void Update()
        {
            if (!m_charge || m_shown) return;
            m_shown = true;
            var dir = WpnUtil.Facing(transform);
            WpnUtil.Spawn(WeaponFx.LanceCharge, (Vector2)transform.position + dir * 4f, null, WpnUtil.Angle(dir));
        }
    }

    // ---- Viper Lash -----------------------------------------------------------------------------------
    /// <summary>The lash body grazes; it throws its cracking tip hitbox out to the far end of the whip.</summary>
    public class WpnLashFx : MonoBehaviour
    {
        public const float BodyDamage = 0.45f, TipDamage = 1.2f, BodyX = 19f, TipX = 38f;
        bool m_done;

        public void Reset() { m_done = false; }
        void MsgSetSpawner(DamageSource s) { m_done = false; }

        void Update()
        {
            if (m_done) return;
            m_done = true;
            var dir = WpnUtil.Facing(transform);
            WpnUtil.Spawn(WeaponFx.LashTip, (Vector2)transform.position + dir * TipX, FxFactory.SourceOf(gameObject), WpnUtil.Angle(dir));
        }
    }

    // ---- Hunter's Kunai -------------------------------------------------------------------------------
    public class WpnKunaiFx : MonoBehaviour
    {
        void MsgOnAttackContact(DamageInfo d) { if (d != null && d.m_victim != null) WpnHuntMark.Add(d.m_victim); }
    }

    public class WpnHuntSlashFx : MonoBehaviour
    {
        public const float Bonus = 0.7f;

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_source == null || !WpnHuntMark.Consume(d.m_victim)) return;
            WpnUtil.Spawn(WeaponFx.KunaiPop, (Vector2)d.m_victim.transform.position + new Vector2(0f, 8f));
            WpnUtil.Hit(d.m_victim, WpnUtil.Scaled(d.m_source.m_damageMod, Bonus), d.m_direction, 0.5f);
        }
    }

    public class WpnHuntMark : MonoBehaviour
    {
        public const float Duration = 3f;
        float m_until;
        GameObject m_fx;

        public static void Add(GameObject v)
        {
            if (!WpnUtil.Alive(v) || v.GetComponent<Player>() == null) return;
            var m = v.GetComponent<WpnHuntMark>() ?? v.AddComponent<WpnHuntMark>();
            m.m_until = Time.time + Duration;
            m.m_fx = WpnFollowFx.Refresh(m.m_fx, WeaponFx.KunaiMark, v, new Vector2(0f, 9f));
        }

        public static bool Consume(GameObject v)
        {
            var m = v.GetComponent<WpnHuntMark>();
            if (m == null || Time.time > m.m_until) return false;
            m.Clear();
            return true;
        }

        void Update() { if (m_fx != null && Time.time > m_until) Clear(); }

        void Clear()
        {
            m_until = 0f;
            if (m_fx != null && m_fx.activeInHierarchy) SystemPool.Despawn(m_fx);
            m_fx = null;
        }

        void OnDisable() { Clear(); }
    }

    // ---- hooks: the hero's runtime, Bulwark's guard, Reaper's reset and the Grudgestone's grudge ------------
    [HarmonyPatch(typeof(Player), "Awake")]
    static class Patch_WeaponRuntimeAwake
    {
        static void Postfix(Player __instance)
        {
            try
            {
                if (__instance != null && R.Get<bool>(__instance, "m_isHero") && __instance.GetComponent<WeaponRuntime>() == null)
                    __instance.gameObject.AddComponent<WeaponRuntime>();
            }
            catch (Exception e) { Plugin.Log.LogError("WeaponRuntime awake: " + e); }
        }
    }

    [HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_WeaponHeroHit
    {
        static GameObject Attacker(Health h, DamageInfo d, bool hitFriendly)
        {
            if (h == null || d == null || d.m_source == null || d.m_amount <= 0f || d.m_isDamageFromStatus) return null;
            var hero = ModUtil.Hero();
            if (hero == null || h.gameObject != hero) return null;
            var a = d.m_source.m_sourceOwnerPlayer;
            return a != null && a != hero ? a : null;
        }

        /// <summary>The ward is the last line: it runs after every other Health.Damage prefix (Patches.cs: tier scaling,
        /// Lucky Die, Marrow Flask plates) and stands down when one of them already stopped the hit. Harmony 2 still
        /// runs later prefixes after one returns false, so without this a dodged or plated hit also spent the ward
        /// (and, at First, a warded hit also spent a Marrow plate).</summary>
        [HarmonyPriority(Priority.Last)]
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, ref bool __result, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            try
            {
                var a = Attacker(__instance, damage, hitFriendly);
                if (a == null || !__instance.CanDamage(damage.m_source, hitFriendly)) return true;
                var rt = __instance.GetComponent<WeaponRuntime>();
                if (rt == null || !rt.GuardUp) return true;
                rt.Block(a.GetComponent<Player>() != null ? a : null);
                __result = false;
                return false;
            }
            catch (Exception e) { Plugin.Log.LogError("Weapon guard: " + e); return true; }
        }

        static void Postfix(Health __instance, DamageInfo damage, bool hitFriendly, bool __result)
        {
            try
            {
                if (!__result) return;
                var a = Attacker(__instance, damage, hitFriendly);
                if (a == null) return;
                var rt = __instance.GetComponent<WeaponRuntime>();
                if (rt != null) rt.OnHurt(a);
            }
            catch (Exception e) { Plugin.Log.LogError("Weapon hero hit: " + e); }
        }
    }
}

namespace CrawlFurther.Content.Weapons
{
    using CrawlFurther.Art;
    using CrawlFurther.Heroes;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// In-hand colours. The hero's weapon is baked into the hero atlas, so a mod weapon recolours its base weapon's
    /// pixels through the hero's colour ramp. The tables are handed to HeroLooks, which composes the equipped mod
    /// weapon's scheme with the origin scheme on the same ramp and restores both when either changes. The combos keep
    /// an empty m_playerColorSwap: vanilla's own swap/unswap (which leaves neighbour slots behind and writes pink over
    /// slots the player ramps map) never touches these slots.
    /// </summary>
    public static class WeaponLooks
    {
        // <generated by tools/sprites/weapon_looks.py: do not edit by hand>
        // per weapon id: (from, to) RGB pairs; from = a hero-atlas weapon colour, its ramp slot gets 'to'
        static readonly Dictionary<string, int[]> s_raw = new Dictionary<string, int[]>
        {
            { "Gravehook", new[] { 0x653C2A, 0x3C3A44, 0x89663B, 0x6C6874, 0xCBCBCB, 0xB4642E, 0x775133, 0x54505C } },
            { "Moonglaive", new[] { 0xCBCBCB, 0xC4E2F0, 0x445574, 0x5A7AA6, 0xBBBDC1, 0x9EC4DC } },
            { "Riftblade", new[] { 0xCBCBCB, 0xB45ADC, 0x445574, 0x2A163E } },
            { "SnakeEyes", new[] { 0x6F482F, 0xB8AA86, 0x7E5936, 0xD8CCAA, 0x9A7C40, 0xF4EEDC, 0x704A31, 0xC8BC98, 0xCBCBCB, 0xC0302A } },
            { "Tidebreaker", new[] { 0xCBCBCB, 0x5FB3A8, 0x445574, 0xB08A40, 0x827F7E, 0x2F7A7A } },
            { "Leechfang", new[] { 0xCBCBCB, 0xC83434, 0x445574, 0x5C0E1A } },
            { "Briarbow", new[] { 0x6F4529, 0x2E4A1E, 0x89663B, 0x7AAE3E, 0xB5A18B, 0xD0C8A8 } },
            { "DirgeMaul", new[] { 0x634430, 0x5A3A22, 0xBEB9B6, 0xDCAC52, 0xA2978F, 0x9A6A24 } },
            { "Wickstaff", new[] { 0x653C2A, 0xB8A276, 0x89663B, 0xE8DCB4, 0xEF326D, 0xFF9A3A } },
            { "Arcbolt", new[] { 0x604525, 0x3A3844, 0x846035, 0x5C5A6A, 0xC1B186, 0x78B4F0, 0xD0BEA0, 0xD0ECFF } },
            { "Frostbrand", new[] { 0xCBCBCB, 0xA8E2F6, 0x445574, 0xE4F6FF } },
            { "Mercyblade", new[] { 0xCBCBCB, 0xF0DCA8, 0x445574, 0xA81E2C } },
            { "Reaper", new[] { 0xCBCBCB, 0xC4DCCC, 0x445574, 0x1C201E, 0x827F7E, 0x4A5E54 } },
            { "Starfall", new[] { 0x634430, 0xC89A34, 0xBEB9B6, 0x4A3C7A, 0xA2978F, 0x2C2250 } },
            { "HydraBow", new[] { 0x6F4529, 0x173A52, 0x89663B, 0x46A8BC, 0xB5A18B, 0xE8D8C0 } },
            { "Bulwark", new[] { 0x6F482F, 0x4E4E5C, 0x7E5936, 0x767686, 0x9A7C40, 0xAEAEBE, 0x704A31, 0x62626E, 0xCBCBCB, 0x4A7AC0 } },
            { "Heartseeker", new[] { 0x604525, 0x5C0E1A, 0x846035, 0x9A1A2C, 0xC1B186, 0xD0C09A, 0xD0BEA0, 0xFF8AA0 } },
            { "Kris", new[] { 0xCBCBCB, 0x4A3A72, 0x445574, 0xD8A02A } },
            { "Blightstaff", new[] { 0x653C2A, 0x4A5A1A, 0x89663B, 0x8AA632, 0xEF326D, 0xB4E03A } },
            { "Orrery", new[] { 0x653C2A, 0x2E2458, 0x89663B, 0x6A5AA8, 0xEF326D, 0xF4F8FF } },
            { "Grudgestone", new[] { 0x724E36, 0x5E2424, 0xC7B299, 0x8A3A32 } },
            { "Midas", new[] { 0x724E36, 0x8A6422, 0xC7B299, 0xF2C84A } },
            { "Lance", new[] { 0x653C2A, 0xA82830, 0x89663B, 0xE05A5A, 0xCBCBCB, 0xE6EAF0, 0x775133, 0x7A1A22 } },
            { "Lash", new[] { 0xCBCBCB, 0x5AA83A, 0x445574, 0x6E4428, 0xBBBDC1, 0x2E6E22 } },
            { "Kunai", new[] { 0xCBCBCB, 0x7A7690, 0x445574, 0xB01E30, 0xBBBDC1, 0x9A96AA } },
        };
        // </generated>

        public static void Register()
        {
            foreach (var kv in s_raw)
            {
                var a = kv.Value;
                var sw = new ColorSwap[a.Length / 2];
                for (int i = 0; i < sw.Length; i++)
                    sw[i] = new ColorSwap { m_from = Rgb(a[2 * i]), m_to = Rgb(a[2 * i + 1]) };
                HeroLooks.WeaponTables["ModWeapon" + kv.Key] = sw;
            }
            Plugin.Log.LogInfo("Weapon in-hand colours: " + s_raw.Count);
        }

        static Color Rgb(int v) { return new Color32((byte)(v >> 16), (byte)(v >> 8), (byte)v, 255); }
    }
}

namespace CrawlFurther.Content.Weapons
{
    using CrawlFurther.Art;
    using CrawlFurther.Heroes;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The mod weapons in the hero's hands. The hero's weapon is part of its frames (AtlasHero), so every hero frame a
    /// mod weapon's clips use is redrawn with the new weapon (tools/sprites/weapon_hands.py -> art/out_weapons/WpnHand_id).
    /// Each sheet becomes an exAtlas whose elements copy the vanilla frames' untrimmed size and offset, so the hero
    /// stands exactly where it did; HeroClip points the ModW_* clips at it. The new weapon pixels use colours whose
    /// _ColorRamp slots are pink in every player ramp (drawn as-is), and body pixels are the vanilla colours, so the
    /// player and origin colours keep working. exSprite.SetSprite swaps the renderer's material to the atlas material
    /// whenever the atlas changes, which would drop the player's ramp: Patch_WeaponHandsMaterial below keeps it.
    /// </summary>
    public static class WeaponHands
    {
        public sealed class Set
        {
            public exAtlas atlas;
            public readonly Dictionary<int, int> map = new Dictionary<int, int>();
        }

        static exAtlas s_hero;
        static readonly Dictionary<string, Set> s_sets = new Dictionary<string, Set>();
        public static readonly HashSet<exAtlas> Atlases = new HashSet<exAtlas>();
        /// <summary>Hero frames a mod weapon clip still shows from AtlasHero (should stay 0).</summary>
        public static int Unmapped;

        public static exAtlas HeroAtlas
        {
            get
            {
                if (s_hero == null)
                    foreach (var a in Resources.FindObjectsOfTypeAll<exAtlas>())
                        if (a.name == "AtlasHero") { s_hero = a; break; }
                return s_hero;
            }
        }

        public static Set For(string id)
        {
            Set set;
            if (s_sets.TryGetValue(id, out set)) return set;
            try { set = Load(id); }
            catch (Exception e) { Plugin.Log.LogError("Weapon hands " + id + ": " + e); set = null; }
            s_sets[id] = set;
            return set;
        }

        public static void Remap(exAtlas atlas, int index, Set set, out exAtlas outAtlas, out int outIndex)
        {
            outAtlas = atlas; outIndex = index;
            if (atlas == null || atlas != HeroAtlas) return;
            int k;
            if (set != null && set.map.TryGetValue(index, out k)) { outAtlas = set.atlas; outIndex = k; }
            else Unmapped++;
        }

        static int I(object o) { return (int)Math.Round(Convert.ToDouble(o)); }

        static Set Load(string id)
        {
            string sid = "WpnHand_" + id;
            var sh = SpriteSheets.Get(sid);
            var hero = HeroAtlas;
            if (sh == null || hero == null) { Plugin.Log.LogWarning("Weapon hands " + id + ": " + (sh == null ? "no sheet" : "no AtlasHero")); return null; }
            var d = MiniJson.Parse(System.IO.File.ReadAllText(SpriteSheets.PathOf(sid + ".json"))) as Dictionary<string, object>;
            object ro;
            if (d == null || !d.TryGetValue("hero", out ro) || !(ro is List<object>)) { Plugin.Log.LogWarning(sid + ": no frame table"); return null; }
            var rows = (List<object>)ro;
            var tex = sh.atlas.texture;
            int W = tex.width, H = tex.height, cw = sh.manifest.cellW, ch = sh.manifest.cellH, cols = Math.Max(1, sh.manifest.cols);
            var set = new Set();
            var els = new exAtlas.Element[rows.Count];
            for (int k = 0; k < rows.Count; k++)
            {
                var r = (List<object>)rows[k];
                int src = I(r[0]), cell = I(r[1]), ow = I(r[2]), oh = I(r[3]), x = I(r[4]), y = I(r[5]), w = I(r[6]), h = I(r[7]);
                int px = (cell % cols) * cw, top = (cell / cols) * ch;
                els[k] = new exAtlas.Element
                {
                    name = sid + "_" + src,
                    originalWidth = ow,
                    originalHeight = oh,
                    trimRect = new Rect(x, y, w, h),                 // same convention as the vanilla element (y from the top)
                    coords = new Rect((float)px / W, (float)(H - top - h) / H, (float)w / W, (float)h / H),
                    rotated = false
                };
                set.map[src] = k;
            }
            var atlas = ScriptableObject.CreateInstance<exAtlas>();
            atlas.name = "ModAtlas_" + sid;
            atlas.texture = tex;
            atlas.elements = els;
            var mat = new Material(hero.material) { name = "ModMat_" + sid, mainTexture = tex };
            atlas.material = mat;
            SpriteSheets.Keep(atlas);
            SpriteSheets.Keep(mat);
            set.atlas = atlas;
            Atlases.Add(atlas);
            s_textures.Add(tex);
            return set;
        }

        // ---- material: a renderer showing a mod hero frame wears a copy of its own material with the mod texture
        static readonly Dictionary<Renderer, Material> s_home = new Dictionary<Renderer, Material>();
        static readonly Dictionary<long, Material> s_clones = new Dictionary<long, Material>();
        static readonly HashSet<Material> s_cloneSet = new HashSet<Material>();
        static readonly HashSet<Texture> s_textures = new HashSet<Texture>();

        /// <summary>Does this material draw a mod weapon-hands texture (one of our clones, or a Renderer.material
        /// instance the game made of one)?</summary>
        static bool IsModMaterial(Material m)
        {
            return m != null && (s_cloneSet.Contains(m) || (m.mainTexture != null && s_textures.Contains(m.mainTexture)));
        }

        static Material CloneFor(Material home, exAtlas atlas)
        {
            long key = ((long)home.GetInstanceID() << 32) ^ (uint)atlas.GetInstanceID();
            Material m;
            if (s_clones.TryGetValue(key, out m) && m != null) return m;
            m = new Material(home) { name = home.name + "+" + atlas.name, mainTexture = atlas.texture };   // shares the _ColorRamp texture
            s_clones[key] = m;
            s_cloneSet.Add(m);
            return m;
        }

        public static void Remember(Renderer r, Material m)
        {
            if (r == null || m == null || IsModMaterial(m)) return;
            if (s_home.Count > 64)
            {
                var dead = new List<Renderer>();
                foreach (var kv in s_home) if (kv.Key == null) dead.Add(kv.Key);
                foreach (var k in dead) s_home.Remove(k);
            }
            s_home[r] = m;
        }

        public static void OnModFrame(Renderer r, exAtlas atlas)
        {
            if (r == null) return;
            var cur = r.sharedMaterial;
            if (cur != null && cur.mainTexture == atlas.texture && cur != atlas.material) return;   // ours (or a ColorSwapper instance of it)
            // something put another material on while a mod frame shows (hero init): that is the new home
            if (cur != null && cur != atlas.material && !s_cloneSet.Contains(cur)) Remember(r, cur);
            Material home;
            if (!s_home.TryGetValue(r, out home) || home == null) return;                                 // no home: atlas material fallback
            r.sharedMaterial = CloneFor(home, atlas);
        }

        public static void OnLeaveMod(Renderer r, exAtlas to)
        {
            Material home;
            if (r == null || to == null || !s_home.TryGetValue(r, out home) || home == null) return;
            if (home.mainTexture == to.texture) r.sharedMaterial = home;
        }

        /// <summary>The material vanilla frames should use on this renderer in place of <paramref name="m"/>: m itself,
        /// or the remembered home if m draws a mod texture (null when there is none).</summary>
        public static Material VanillaMaterial(Renderer r, Material m)
        {
            if (!IsModMaterial(m)) return m;
            Material home;
            return r != null && s_home.TryGetValue(r, out home) && home != null ? home : null;
        }

        /// <summary>Make the renderer's material match the atlas the sprite shows now (after the game assigned a material
        /// itself, outside SetSprite).</summary>
        public static void Sync(exSprite spr)
        {
            var r = spr != null ? spr.GetComponent<Renderer>() : null;
            var atlas = spr != null ? spr.atlas : null;
            if (r == null || atlas == null) return;
            if (Atlases.Contains(atlas)) { OnModFrame(r, atlas); return; }
            var cur = r.sharedMaterial;
            if (cur == null || !IsModMaterial(cur)) return;
            var home = VanillaMaterial(r, cur);
            if (home == null || home.mainTexture != atlas.texture) home = PlayerMaterial(r, atlas.texture);
            r.sharedMaterial = home ?? atlas.material;
        }

        /// <summary>The hero material of the player this body belongs to (it keeps their colour ramp), if it draws
        /// <paramref name="tex"/>.</summary>
        static Material PlayerMaterial(Renderer r, Texture tex)
        {
            var p = r.GetComponent<Player>();
            var pd = p != null ? p.GetPlayerData() : null;
            var m = pd != null && pd.Setup != null ? pd.Setup.m_heroMaterial : null;
            return m != null && m.mainTexture == tex ? m : null;
        }
    }

    /// <summary>
    /// Player.OnAnimationSetChanged (every weapon change) puts back the material it cached on the body's first weapon
    /// change. If that was taken while a mod weapon's frame showed, a vanilla weapon picked up later is drawn with the mod
    /// texture and the hero turns invisible. Keep the cache on the vanilla material and re-match the frame after.
    /// </summary>
    [HarmonyPatch(typeof(Player), "OnAnimationSetChanged")]
    static class Patch_WeaponHandsAnimationSet
    {
        static void Prefix(Player __instance, ref Material ___m_originalMaterial)
        {
            if (WeaponHands.Atlases.Count == 0 || ___m_originalMaterial == null) return;
            try
            {
                var fixedMat = WeaponHands.VanillaMaterial(__instance.GetComponent<Renderer>(), ___m_originalMaterial);
                if (fixedMat != ___m_originalMaterial) ___m_originalMaterial = fixedMat;
            }
            catch (Exception e) { Plugin.Log.LogError("Weapon hands (animation set): " + e); }
        }

        static void Postfix(Player __instance)
        {
            if (WeaponHands.Atlases.Count == 0) return;
            try { WeaponHands.Sync(__instance.GetComponent<exSprite>()); }
            catch (Exception e) { Plugin.Log.LogError("Weapon hands (animation set): " + e); }
        }
    }

    [HarmonyPatch(typeof(exSprite), "SetSprite", new[] { typeof(exAtlas), typeof(int), typeof(bool) })]
    static class Patch_WeaponHandsMaterial
    {
        static void Prefix(exSprite __instance, exAtlas _atlas, out exAtlas __state)
        {
            __state = __instance.atlas;
            if (_atlas == null || _atlas == __state || WeaponHands.Atlases.Count == 0) return;
            try
            {
                if (WeaponHands.Atlases.Contains(_atlas) && (__state == null || !WeaponHands.Atlases.Contains(__state)))
                {
                    WeaponHands.Remember(__instance.GetComponent<Renderer>(), __instance.GetComponent<Renderer>().sharedMaterial);
                    WeaponRuntime.EnsureOnHero(__instance);
                }
            }
            catch (Exception e) { Plugin.Log.LogError("Weapon hands (prefix): " + e); }
        }

        static void Postfix(exSprite __instance, exAtlas _atlas, exAtlas __state)
        {
            if (_atlas == null || WeaponHands.Atlases.Count == 0) return;
            try
            {
                if (WeaponHands.Atlases.Contains(_atlas)) WeaponHands.OnModFrame(__instance.GetComponent<Renderer>(), _atlas);
                else if (__state != null && __state != _atlas && WeaponHands.Atlases.Contains(__state))
                    WeaponHands.OnLeaveMod(__instance.GetComponent<Renderer>(), _atlas);
            }
            catch (Exception e) { Plugin.Log.LogError("Weapon hands (postfix): " + e); }
        }
    }
}

namespace CrawlFurther.Content.Weapons
{
    using CrawlFurther.Art;
    using CrawlFurther.Heroes;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    // =====================================================================================================
    //  v0.8: no vanilla contact art left on any weapon. Every projectile weapon spawns its own impact
    //  (FxWpn<Id>Impact: Hit on monsters, Wall on walls), the sling shots cast their own shadow, and the
    //  weapon states the descriptions talk about are drawn (chill count, harvested souls, lance charge,
    //  gold power on the Midas coin).
    // =====================================================================================================
    public static partial class WeaponFx
    {
        public const int LayerWall = 9, LayerMonster = 14;
        public static readonly Dictionary<string, GameObject> ImpactHit = new Dictionary<string, GameObject>();
        public static readonly Dictionary<string, GameObject> ImpactWall = new Dictionary<string, GameObject>();
        public static readonly GameObject[] ReapStacks = new GameObject[WpnReapFx.MaxStacks];
        public static readonly exSpriteAnimClip[] MidasTiers = new exSpriteAnimClip[3];
        public static GameObject LanceReady;

        static readonly string[] ImpactIds =
        {
            "Gravehook", "Moonglaive", "Tidebreaker", "Wickstaff", "Arcbolt", "HydraBow", "Heartseeker",
            "Blightstaff", "Orrery", "Grudgestone", "Midas", "Kunai",
        };

        public static GameObject ImpHit(string id) { GameObject g; return ImpactHit.TryGetValue(id, out g) ? g : null; }
        public static GameObject ImpWall(string id) { GameObject g; return ImpactWall.TryGetValue(id, out g) ? g : null; }

        /// <summary>
        /// Point a projectile's contacts at the weapon's own impacts: monster contacts spawn Hit, wall contacts Wall
        /// (or nothing when the shot is flown by script and makes its own wall puff), any other inherited vanilla spawn
        /// is cleared. A single catch-all contact (the sling's) is split in two so walls get the wall puff. Contacts
        /// that already spawn one of this weapon's own zones (briar patch, soul fire) are left alone. Runs after
        /// FxKit.Projectile, so it also wins over any default impact FxKit assigns there.
        /// </summary>
        static void Impacts(GameObject proj, string id, bool wallContact = true)
        {
            var de = proj != null ? proj.GetComponent<DamageEffect>() : null;
            if (de == null || de.m_contactData == null) return;
            var hit = ImpHit(id);
            var wall = wallContact ? ImpWall(id) : null;
            const int W = 1 << LayerWall, M = 1 << LayerMonster;
            var add = new List<ContactData>();
            foreach (var c in de.m_contactData)
            {
                if (c == null) continue;
                if (c.m_spawnOnHit != null && c.m_spawnOnHit.name.StartsWith("ModWpn", StringComparison.Ordinal) && !ImpactOwn(c.m_spawnOnHit)) continue;
                int m = c.m_layerMask.value;
                if ((m & M) != 0 && (m & W) != 0)
                {
                    c.m_layerMask = m & ~W;
                    c.m_spawnOnHit = hit;
                    if (wall != null)
                        add.Add(new ContactData
                        {
                            m_layerMask = W, m_destroyOnHit = c.m_destroyOnHit, m_spawnOnHit = wall,
                            m_spawnDirection = c.m_spawnDirection, m_knockbackDirection = c.m_knockbackDirection,
                            m_spawnAtMiddle = c.m_spawnAtMiddle, m_hitCorpses = c.m_hitCorpses, m_hitFriendly = c.m_hitFriendly,
                        });
                }
                else if ((m & M) != 0) c.m_spawnOnHit = hit;
                else if ((m & W) != 0) c.m_spawnOnHit = wall;
                else c.m_spawnOnHit = null;
            }
            de.m_contactData.AddRange(add);
            de.m_spawnOnHit = hit;                                          // legacy field (unused by the game): ours too
        }

        static bool ImpactOwn(GameObject go)
        {
            foreach (var kv in ImpactHit) if (kv.Value == go) return true;
            foreach (var kv in ImpactWall) if (kv.Value == go) return true;
            return false;
        }

        /// <summary>The sling's Shadow child shows a generic 14x3 blob from the boss atlas: give it the shot's own.</summary>
        static void SlingShadow(GameObject proj, string sheetId)
        {
            var t = proj != null ? proj.transform.Find("Shadow") : null;
            var sh = SpriteSheets.Get(sheetId);
            if (t == null || sh == null || !sh.Has("Shadow")) { Plugin.Log.LogWarning("Weapon shadow: missing for " + sheetId); return; }
            var spr = t.GetComponent<exSprite>();
            if (spr == null) return;
            spr.SetSprite(sh.atlas, sh.Anim("Shadow").frames[0]);
            var rr = t.GetComponent<Renderer>();
            if (rr != null && sh.atlas.material != null) rr.sharedMaterial = sh.atlas.material;
            var an = t.GetComponent<exSpriteAnimation>();
            if (an != null) an.enabled = false;
        }

        /// <summary>A wall puff: a clone of the vanilla wall contact it replaces (keeps its clink sound) wearing the
        /// weapon's Wall art, radial and unrotated like vanilla's.</summary>
        static GameObject WallPuff(string name, SpriteSheet sh, string vanilla)
        {
            var go = FxFactory.Clone(vanilla, name);
            if (go == null) return null;
            FxFactory.StripChildren(go);
            FxFactory.Reskin(go, new ClipBuilder(sh, "Wall", name + "Clip").Once().Build(), sh);
            var spr = go.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = exPlane.Anchor.MidCenter; spr.offset = Vector2.zero; spr.color = Color.white; }
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, canFlip: true, snap: 0f, freeRotate: false);
            var e = go.GetComponent<Effect>();
            if (e != null) { R.Set(e, "m_startAngle", new MinMaxRange(0f)); R.Set(e, "m_fadeOutTime", 0f); }
            FxFactory.SetMotion(go, 0f, enabled: false);
            FxKit.NoTint(go);
            var dh = go.GetComponent<DepthHandler>();
            if (dh != null) dh.m_heightOffset = -4f;
            return go;
        }

        static void BuildV08()
        {
            foreach (var id in ImpactIds)
            {
                string sid = "FxWpn" + id + "Impact";
                var sh = SpriteSheets.Get(sid);
                if (sh == null) { Plugin.Log.LogWarning("Weapon impact: missing sheet " + sid); continue; }
                var hit = VisRot("ModWpn" + id + "Hit", sid, "Hit");            // rotated to point back along the shot, like vanilla
                var dh = hit != null ? hit.GetComponent<DepthHandler>() : null;
                if (dh != null) dh.m_heightOffset = -22f;                       // a body hit at chest height sorts in front of the victim
                ImpactHit[id] = hit;
                // the knife's wall contact was ContactGenericWall, the arrows' ContactGenericSmall; script-flown shots
                // (glaive, grudge stone) clink like a thrown blade
                string van = id == "Kunai" || id == "Moonglaive" || id == "Grudgestone" ? "ContactGenericWall" : "ContactGenericSmall";
                if (sh.Has("Wall")) ImpactWall[id] = WallPuff("ModWpn" + id + "Wall", sh, van);
            }
            Impacts(Hook, "Gravehook");                                     // spear-based: no wall contact (passes walls like vanilla)
            Impacts(Glaive, "Moonglaive", wallContact: false);              // WpnGlaiveFx spawns the wall puff where it turns
            Impacts(Wave, "Tidebreaker");
            Impacts(Wisp, "Wickstaff");
            Impacts(ArcBolt, "Arcbolt");
            Impacts(HydraArrow, "HydraBow");
            Impacts(HydraShard, "HydraBow");
            Impacts(HeartBolt, "Heartseeker");
            Impacts(BlightBolt, "Blightstaff");
            Impacts(OrreryBolt, "Orrery");
            Impacts(GrudgeStone, "Grudgestone", wallContact: false);        // WpnGrudgeFx spawns the wall puff as it breaks
            Impacts(MidasCoin, "Midas");
            Impacts(Kunai, "Kunai");
            SlingShadow(GrudgeStone, "FxWpnGrudgestone");
            SlingShadow(MidasCoin, "FxWpnMidas");

            for (int n = 0; n < ReapStacks.Length; n++)
                ReapStacks[n] = Vis("ModWpnReapStacks" + (n + 1), "FxWpnReaperStacks", "Stacks" + (n + 1), loop: true);
            LanceReady = Vis("ModWpnLanceReady", "FxWpnLance", "Ready", loop: true);
            var md = SpriteSheets.Get("FxWpnMidas");
            string[] tiers = { "Coin", "Coin2", "Coin3" };
            if (md != null)
                for (int t = 0; t < tiers.Length; t++)
                    if (md.Has(tiers[t])) MidasTiers[t] = new ClipBuilder(md, tiers[t], "ModWpnMidas" + tiers[t] + "Clip").Loop().Build();
        }
    }
}
