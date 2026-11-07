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
    using CrawlFurther.Content.Gods.Sylvene;
    using CrawlFurther.Content.Gods.Umbrael;
    using CrawlFurther.Content.Gods.Vhorrul;

    /// <summary>One spell and one artifact per god, sold in the hero shops alongside vanilla stock.</summary>
    public static class ItemPack
    {
        /// <summary>The shop items built so far (the same table as <see cref="ItemRegistry.Items"/>).</summary>
        public static Dictionary<string, Powerup> Built { get { return ItemRegistry.Items; } }
        public static Powerup MarrowFlask, HollowCrown;

        static List<DamageEffectData> SpecialEffects(Powerup pu) { return R.Get<List<DamageEffectData>>(pu, "m_specialAttackDamageEffects"); }
        static System.Collections.IList Effects(Powerup pu) { return R.Get<System.Collections.IList>(pu, "m_effects"); }

        static void SetObject(System.Collections.IList list, int i, GameObject go)
        {
            if (list == null || i >= list.Count || go == null) return;
            var d = list[i] as DamageEffectData;
            if (d != null) d.m_object = go;
        }

        /// <summary>A visible runner (HeroSlimeDropper clone) in the item's art that lays <paramref name="trail"/> behind it.
        /// Its vanilla specialAttackContact burst (a 69 x 55 hero spell flash on every monster it brushed) is cleared.</summary>
        public static GameObject HeroDropper(string name, GameObject trail, float trailDist, float life, float speed, string art = null)
        {
            var go = FxFactory.Clone("HeroSlimeDropper", name);
            if (go == null) return null;
            FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: life, freeRotate: true);
            FxFactory.SetMotion(go, speed, trail: trail, trailDist: trailDist, collide: true);
            FxFactory.SetContacts(go, clearSpawnOnHit: true);
            if (art != null) ItemArt.Runner(go, art);
            return go;
        }

        /// <summary>A hero copy of a template dressed in item art (same damage, collider, hooks and clip timing).</summary>
        public static GameObject Dressed(GameObject template, string name, string sheet, string anim, float damageMult = 1f)
        {
            var go = ItemFixes.HeroCopy(template, name, damageMult);
            return ItemArt.Wear(go, sheet, anim);
        }

        /// <summary>
        /// Hyperdash clones (Mirror Step, Riptide Dash): the dash streak (effect 1, vanilla DashBlur) and the particles the
        /// attached dropper sheds (effect 2, vanilla DashParticle) become the item's own art.
        /// </summary>
        public static void DashArt(Powerup pu, string id, string blurSheet, string dropSheet)
        {
            var sp = SpecialEffects(pu);
            if (sp.Count > 1 && sp[1].m_object != null)
            {
                var blur = MonsterFactory.ClonePrefab(sp[1].m_object, "ModItem" + id + "Blur");
                FxFactory.Templates[blur.name] = blur;
                ItemArt.Wear(blur, blurSheet, "Play");
                // the streak art is centred on the spawn point like the vanilla blur (MidCenter)
                sp[1].m_object = blur;
            }
            if (sp.Count > 2 && sp[2].m_object != null)
            {
                var drop = MonsterFactory.ClonePrefab(sp[2].m_object, "ModItem" + id + "Dropper");
                FxFactory.Templates[drop.name] = drop;
                var bit = ItemArt.Visual("ModItem" + id + "Bit", dropSheet, "Play");
                foreach (var m in drop.GetComponents<ParticleMotion>())
                    if (R.Get<GameObject>(m, "m_trailObject") != null) R.Set(m, "m_trailObject", bit);
                sp[2].m_object = drop;
            }
        }

        static GameObject s_marrowOrbit, s_jokerOrbit, s_marrowBreak, s_jokerBreak;
        public static GameObject MarrowOrbit { get { Plates(); return s_marrowOrbit; } }
        public static GameObject JokerOrbit { get { Plates(); return s_jokerOrbit; } }
        public static GameObject MarrowBreak { get { Plates(); return s_marrowBreak; } }
        public static GameObject JokerBreak { get { Plates(); return s_jokerBreak; } }
        public static exSpriteAnimClip[] MarrowOrbitClips, JokerOrbitClips;
        static bool s_plates;
        static void Plates()
        {
            if (s_plates) return;
            s_plates = true;
            s_marrowOrbit = ItemArt.Visual("ModItemMarrowPlates", "FxItemMarrowPlate", "Orbit1", loop: true);
            s_jokerOrbit = ItemArt.Visual("ModItemJokerPlates", "FxItemJokerShield", "Orbit1", loop: true);
            s_marrowBreak = ItemArt.Visual("ModItemMarrowPlateBreak", "FxItemMarrowPlate", "Break");
            s_jokerBreak = ItemArt.Visual("ModItemJokerPlateBreak", "FxItemJokerShield", "Break");
            MarrowOrbitClips = new[] { ItemArt.Clip("FxItemMarrowPlate", "Orbit1", true), ItemArt.Clip("FxItemMarrowPlate", "Orbit2", true) };
            JokerOrbitClips = new[] { ItemArt.Clip("FxItemJokerShield", "Orbit1", true), ItemArt.Clip("FxItemJokerShield", "Orbit2", true) };
            foreach (var t in new[] { s_marrowOrbit, s_jokerOrbit }) if (t != null) FxFactory.SetEffect(t, destroyOnAnimEnd: false, canFlip: true, freeRotate: false);
        }

        public static readonly List<ItemDef> Items = new List<ItemDef>
        {
            // ---------------------------------------------------------------- Vhorrul
            new ItemDef { id = "SpellWickwalk", cloneFrom = "SpellFetidDischarge", cost = 35, group = "GroupSpellsPurchasable",
                name = "Wickwalk", description = "Fling wax runners that leave a trail of fire",
                bubbleArt = "IconItemWickwalkBubble",
                customize = (go, pu) =>
                {
                    // its own burning floor: a hero copy of the burning pool (same 0.5 per 0.6 s, igniter, timing) in Wickwalk's art
                    var fire = Dressed(VhorrulFx.BurningPool, "ModItemWickFire", "FxItemWickFire", "Life");
                    var runner = HeroDropper("ModHeroWickRunner", fire ?? VhorrulFx.BurningPool, 11f, 0.32f, 150f, "FxItemWickRunner");
                    var sp = SpecialEffects(pu);
                    for (int i = 0; i < sp.Count; i++) sp[i].m_object = runner;
                } },
            new ItemDef { id = "ArtifactVotiveCandle", cloneFrom = "PowerupAcidBlood", cost = 40, group = "GroupArtifactsPurchasable",
                name = "Votive Candle", description = "Spill burning tallow when you are hit",
                bubbleArt = "IconItemVotiveBubble", hudArt = "IconVotiveCandleHud",
                customize = (go, pu) =>
                {
                    // hero copies: the monster pool only sets its victim alight 15% of the time
                    BuildTallow();
                    var e = Effects(pu);
                    SetObject(e, 0, HeroTallowTrail ?? VhorrulFx.WickTrail);
                    SetObject(e, 1, HeroTallow ?? VhorrulFx.BurningPool);
                } },
            // ---------------------------------------------------------------- Ossivar
            new ItemDef { id = "SpellGraveCall", cloneFrom = "SpellCycloneSummon", cost = 40, group = "GroupSpellsPurchasable",
                name = "Grave Call", description = "Hurl a piercing bone spear",
                bubbleArt = "IconGraveCallBubble",
                customize = (go, pu) =>
                {
                    var spear = FxKit.Projectile("ModHeroSpineSpear", "DFX_skelMageNewProjectile", "FxItemGraveSpear", "Fly", 270f, 0.8f, 1.5f, 1f,
                                                 destroyOnHit: false);
                    if (spear != null)
                    {
                        FxFactory.SetDamage(spear, 1.1f, rate: 0.3f, knockback: 1f, collisionAtStart: true);
                        ItemArt.Place(spear, "FxItemGraveSpear");
                        ItemArt.Puffs(spear, ItemArt.Visual("ModItemGraveChips", "FxItemGraveSpear", "Pop"));
                    }
                    ItemFixes.PierceMonsters(spear);
                    var sp = SpecialEffects(pu);
                    if (sp.Count > 0) { sp[0].m_object = spear; sp[0].m_offsetY = new MinMaxRange(8f); }
                } },
            new ItemDef { id = "ArtifactMarrowFlask", cloneFrom = "ArtifactThornOfWrath", cost = 45, group = "GroupArtifactsPurchasable",
                name = "Marrow Flask", description = "Kills grow bone plates that block hits",
                bubbleArt = "IconMarrowFlaskBubble", hudArt = "IconMarrowFlaskHud",
                customize = (go, pu) => { R.Set(pu, "m_modifiers", new List<PlayerModifier>()); MarrowFlask = pu; } },
            // ---------------------------------------------------------------- Sylvene
            new ItemDef { id = "SpellThornwall", cloneFrom = "SpellTribalShield", cost = 30, group = "GroupSpellsPurchasable",
                name = "Thornwall", description = "Plant a line of thorns that make monsters bleed",
                bubbleArt = "IconThornwallBubble",
                customize = (go, pu) =>
                {
                    var patch = Dressed(SylveneFx.ThornPatch, "ModItemThornwall", "FxItemThornwall", "Life");
                    var sower = HeroDropper("ModHeroThornSower", patch ?? SylveneFx.ThornPatch, 12f, 0.3f, 160f, "FxItemThornRunner");
                    var sp = SpecialEffects(pu);
                    if (sp.Count > 0) sp[0].m_object = sower;
                } },
            new ItemDef { id = "ArtifactRottingApple", cloneFrom = "ArtifactSpellbookTears", cost = 35, group = "GroupArtifactsPurchasable",
                name = "Rotting Apple", description = "A floating apple sends poisonous maggots at your foes",
                bubbleArt = "IconRottingAppleBubble", hudArt = "IconRottingAppleHud",
                customize = (go, pu) =>
                {
                    // The swarm template seeks the hero (its vanilla base carries ParticleMotionSeek): the hero copy
                    // seeks monsters instead, accelerates harder so it can turn, and hits a little softer.
                    var swarm = ItemFixes.HeroCopy(SylveneFx.Maggots, "ModHeroMaggotSwarm", 0.8f);   // 0.5 -> 0.4 per 0.45 s
                    if (swarm != null)
                    {
                        ItemArt.Wear(swarm, "FxItemMaggots", "Fly", loop: true);
                        ItemArt.Puffs(swarm, ItemArt.Visual("ModItemMaggotBite", "FxItemMaggots", "Pop"));
                        FxFactory.SetMotion(swarm, 45f, accel: 170f, speedMax: 75f);
                        var a = swarm.GetComponent<AudioCueSource>(); if (a != null) R.Set(a, "m_playOnSpawn", null);
                        ItemFixes.AimAtMonsters(swarm, 220f);
                        ItemFixes.SeekMonsters(swarm, 220f);
                    }
                    ItemFixes.Follower(go, pu, "FxItemTokenApple", 9f, swarm);
                } },
            // ---------------------------------------------------------------- Umbrael
            new ItemDef { id = "SpellMirrorStep", cloneFrom = "SpellHyperdash", cost = 50, group = "GroupSpellsPurchasable",
                name = "Mirror Step", description = "Dash forward, shattering the floor behind you",
                bubbleArt = "IconMirrorStepBubble",
                customize = (go, pu) =>
                {
                    // the spot you left: a pane of mirror that shatters (a hero copy of the decoy burst: 0.75, 22 x 12),
                    // and the dash itself streaks glass instead of the vanilla Hyperdash blur
                    var sp = SpecialEffects(pu);
                    var shatter = Dressed(UmbraelFx.DecoyBurst, "ModItemMirrorShatter", "FxItemMirrorShatter", "Shatter");
                    if (sp.Count > 0) sp[0].m_object = shatter ?? UmbraelFx.DecoyBurst;
                    DashArt(pu, "MirrorStep", "FxItemMirrorBlur", "FxItemMirrorGlint");
                } },
            new ItemDef { id = "ArtifactHollowCrown", cloneFrom = "ArtifactThornOfWrath", cost = 70, group = "GroupArtifactsPurchasable",
                name = "Hollow Crown", description = "Your shadow repeats your blows",
                bubbleArt = "IconHollowCrownBubble", hudArt = "IconHollowCrownHud",
                customize = (go, pu) => { R.Set(pu, "m_modifiers", new List<PlayerModifier>()); HollowCrown = pu; } },
        };

        /// <summary>Replace a follower token's state animations with mod art, keeping a firing Activate clip
        /// (one looping clip on every state left the token stuck in Activate and removed its AnimAttack events).</summary>
        static void ReskinToken(GameObject go, string art) { ItemFixes.TokenClips(go, art); }

        public static GameObject HeroTallow, HeroTallowTrail;

        /// <summary>Votive Candle: a burning pool that always sets what it burns alight, and the dropper that lays it.</summary>
        static void BuildTallow()
        {
            if (HeroTallow != null || VhorrulFx.BurningPool == null) return;
            HeroTallow = Dressed(VhorrulFx.BurningPool, "ModHeroTallowPool", "FxItemVotive", "Life");
            var d = HeroTallow.GetComponent<DamageEffect>();
            if (d != null) R.Set(d, "m_statusChance", 1f);
            if (VhorrulFx.WickTrail == null) return;
            HeroTallowTrail = ItemFixes.HeroCopy(VhorrulFx.WickTrail, "ModHeroTallowTrail");
            foreach (var m in HeroTallowTrail.GetComponents<ParticleMotion>())
                if (R.Get<GameObject>(m, "m_trailObject") == VhorrulFx.BurningPool) R.Set(m, "m_trailObject", HeroTallow);
        }

        public static void ReskinTokenPublic(GameObject go, string art) { ReskinToken(go, art); }

        public static void Register()
        {
            foreach (var def in Items)
            {
                try { ItemRegistry.Register(def); }
                catch (Exception e) { Plugin.Log.LogError("Item " + def.id + " failed: " + e); }
            }
        }
    }

    /// <summary>Hero-side item effects that need code: Marrow Flask plates and Hollow Crown echoes.</summary>
    public class HeroPerks : MonoBehaviour
    {
        public int plates;          // all plates (Marrow Flask bone + Joker's Wild cards): Patches.cs reads this
        public int cardPlates;      // of which Joker's Wild "Diamonds" card plates
        int m_kills;
        GameObject m_plateFx, m_cardFx;
        int m_shownBone = -1, m_shownCard = -1;
        float m_lastEcho;
        Player m_player;

        void Awake() { m_player = GetComponent<Player>(); }
        void OnEnable() { plates = 0; cardPlates = 0; m_kills = 0; UpdatePlateFx(); }

        PlayerData Data { get { return m_player != null ? m_player.GetPlayerData() : null; } }

        public static bool Has(PlayerData pd, Powerup pu)
        {
            return pd != null && pu != null && pd.GameData != null && pd.GameData.HasPowerup(pu);
        }

        public void OnKill()
        {
            if (!Has(Data, ItemPack.MarrowFlask)) return;
            if (++m_kills % 4 != 0 || plates >= 2) return;
            plates++;
            UpdatePlateFx();
        }

        /// <summary>Joker's Wild "Diamonds": a card plate (shown as the item's card shield, not a bone plate).</summary>
        public void AddPlate()
        {
            if (plates >= 3) return;
            plates++;
            cardPlates++;
            UpdatePlateFx();
        }

        public bool TryBlock()
        {
            if (plates <= 0) return false;
            // a poison / fire tick is not a monster hit: let it through and keep the plate
            var d = ItemFixes.Incoming;
            if (d != null && d.m_isDamageFromStatus) return false;
            plates--;
            bool card = cardPlates > 0;
            if (card) cardPlates--;
            ItemArt.Pop(card ? ItemPack.JokerBreak : ItemPack.MarrowBreak, transform.position);
            UpdatePlateFx();
            return true;
        }

        /// <summary>One orbit visual per plate kind, showing one or two plates (a third waits its turn).</summary>
        void UpdatePlateFx()
        {
            int bone = Mathf.Max(0, plates - cardPlates), card = Mathf.Min(cardPlates, plates);
            Orbit(ref m_plateFx, ref m_shownBone, bone, ItemPack.MarrowOrbit, ItemPack.MarrowOrbitClips);
            Orbit(ref m_cardFx, ref m_shownCard, card, ItemPack.JokerOrbit, ItemPack.JokerOrbitClips);
        }

        void Orbit(ref GameObject fx, ref int shown, int n, GameObject tmpl, exSpriteAnimClip[] clips)
        {
            if (n > 0 && fx == null && tmpl != null)
            {
                // half a pixel below the hero so it sorts in front of the hero sprite
                fx = SystemPool.Spawn(tmpl, transform.position + new Vector3(0f, -0.5f, 0f));
                if (fx != null) fx.transform.parent = transform;
                shown = -1;
            }
            if (n <= 0)
            {
                if (fx != null) SystemPool.Despawn(fx);
                fx = null; shown = -1;
                return;
            }
            int want = Mathf.Min(n, 2);
            if (fx == null || shown == want || clips == null) return;
            var an = fx.GetComponent<exSpriteAnimation>();
            var clip = clips[want - 1];
            ItemArt.Ensure(an, clip, true);
            shown = want;
        }

        public void TryEcho(GameObject spawned, GameObject prefab)
        {
            if (!Has(Data, ItemPack.HollowCrown) || Time.time - m_lastEcho < 0.35f) return;
            // only blows: the hero's Attacks also spawns dash dust, status visuals, shields and the like
            var de = prefab != null ? prefab.GetComponent<DamageEffect>() : null;
            if (de == null || !de.enabled || R.Get<float>(de, "m_damage") <= 0f) return;
            m_lastEcho = Time.time;
            // copy the hero's own damage modifiers (STR, weapon, powerups), then scale to 30%
            var mod = new ValueModifierStack();
            var src = FxFactory.SourceOf(spawned);
            if (src != null && src.m_damageMod != null)
            {
                var list = R.Get<List<ValueModifier>>(src.m_damageMod, "m_modifiers");
                if (list != null) foreach (var m in list) mod.Add(m);
            }
            mod.Add("hollowcrown", ValueModifier.eModifierType.Multiply, 0.3f, 100f);
            StartCoroutine(EchoLater(prefab, spawned.transform.position, spawned.transform.rotation, mod, transform.position, transform.lossyScale.x < 0f));
        }

        System.Collections.IEnumerator EchoLater(GameObject prefab, Vector3 pos, Quaternion rot, ValueModifierStack mod, Vector3 heroAt, bool left)
        {
            yield return new WaitForSeconds(0.45f);
            if (prefab == null || m_player == null) yield break;
            // the crowned shadow (Hollow Crown's own art) rises where you stood and repeats the blow
            var sh = ItemArt.Pop(ItemPack2.ShadowEcho, heroAt);
            if (sh != null && left) { var s = sh.transform.localScale; sh.transform.localScale = new Vector3(-Mathf.Abs(s.x), s.y, s.z); }
            var go = SystemPool.SpawnBegin(prefab, pos, rot);
            if (go == null) yield break;
            go.SendMessage(Constants.MSG_SETSPAWNER, new DamageSource(go, gameObject, Data, -1, -1, mod, false), SendMessageOptions.DontRequireReceiver);
            SystemPool.SpawnFinalize(go);
        }
    }

    [HarmonyPatch(typeof(PlayerData), "OnKilledPlayer", new[] { typeof(PlayerData), typeof(bool) })]
    static class Patch_HeroKill
    {
        static void Postfix(PlayerData __instance, PlayerData other)
        {
            if (__instance == null || !__instance.IsHero || other == null || other.IsHero) return;
            var go = R.Get<GameObject>(__instance, "m_playerObject");
            var perks = go != null ? go.GetComponent<HeroPerks>() : null;
            if (perks != null) perks.OnKill();
            var perks2 = go != null ? go.GetComponent<HeroPerks2>() : null;
            if (perks2 != null) perks2.OnKill();
        }
    }
}
