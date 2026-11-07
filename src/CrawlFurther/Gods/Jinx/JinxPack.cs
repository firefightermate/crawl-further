using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods.Ossivar;

    /// <summary>
    /// Jinx, the Grinning Jester: chance, cards, dice, carnival and puppets. Every special draws a Wild Card (the god's
    /// perk, <see cref="JinxMonster"/>), and every monster has a quirk of its own (a <see cref="JinxBehaviour"/>) with a
    /// tell the hero can read. Offsets below are the sprite's sync points (art/out_jinx/TIMING.md), x forward, y up.
    /// </summary>
    public static class JinxPack
    {
        static ClipBuilder Special(SpriteSheet sh, string anim, string clip)
        {
            return new ClipBuilder(sh, anim, clip).Once().Ev(0, "ModWildCard").Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop");
        }

        static exSpriteAnimClip Looped(SpriteSheet sh, string anim, string clip)
        {
            return sh.Has(anim) ? new ClipBuilder(sh, anim, clip).Loop().Build() : null;
        }

        static exSpriteAnimClip Once(SpriteSheet sh, string anim, string clip)
        {
            return sh.Has(anim) ? new ClipBuilder(sh, anim, clip).Once().Build() : null;
        }

        // ---------------------------------------------------------------------------------------------- tier 1
        // Jack-in-the-Box: the head boxes out on its spring (it turns with the aim; aimed down it slams the floor beside
        // the box); Pop hides in the box and springs out beside the hero. Quirk: JackWindUp.
        static void JackKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int punch = Kit.AddEffect(p, JinxFx.JackPunch, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 10f);   // head at (16, -10)
            Kit.Effects(p)[punch].m_offsetAimDown = new Vector2(5f, 0f);
            int pop = Kit.AddEffect(p, JinxFx.ConfettiPop, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var pu = Kit.Melee(sh, "Punch", "ModJackPunch", v, 3, punch, 30f).Build();
            var pp = new ClipBuilder(sh, "Pop", "ModJackPop").Once()
                .Ev(0, "ModWildCard").Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(1, "AnimStartInvincibility")
                .Ev(4, "AnimCollideOff").Ev(4, "ModPopNearHero").Ev(5, "AnimCollideOn")
                .Ev(5, "AnimAttack", pop).EvO(5, "AnimSound", v).Ev(6, "AnimStopInvincibility").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, pu, 1.3f, rangeInner: 8f, rangeOuter: 20f));
            AimedMelee.Angles(atk[0], sh, "Punch", a => Kit.Melee(sh, a, "ModJack" + a, v, 3, punch, 30f).Build());
            Kit.SetSpecial(p, Kit.Attack(sp, pp, 0f, rangeInner: 40f, rangeOuter: 160f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 7f);
            JackWindUp.WindIdle = Looped(sh, "Wind", "ModJackWind");
        }

        // Card Sharp: three cards, each with a random curse (basic 0), or on every third deal the gold Ace (basic 1);
        // Shuffle swaps it with the ally nearest the hero. Quirk: SharpAce.
        static void SharpKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            var cards = new List<int>();
            foreach (var a in new[] { -12f, 0.01f, 12f }) cards.Add(Kit.AddEffect(p, JinxFx.Card, offsetX: 13f, offsetY: 8f, angle: a));
            int ace = Kit.AddEffect(p, JinxFx.Ace, offsetX: 13f, offsetY: 8f, angle: 0.01f);
            var dl = Kit.Shot(sh, "Deal", "ModSharpDeal", 3, v, 0.05f, cards.ToArray()).Ev(4, "ModJinxDealt").Build();
            var ac = Kit.Shot(sh, "Ace", "ModSharpAce", 3, v, 0f, ace).Ev(4, "ModJinxAceThrown").Build();
            var sf = Special(sh, "Shuffle", "ModSharpShuffle").Ev(3, "ModShuffle").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, dl, 1.4f, rangeInner: 45f, rangeOuter: 90f, rangeRetreat: 35f));
            atk.Add(Kit.Attack(a0, ac, 1.4f, rangeInner: 45f, rangeOuter: 110f, rangeRetreat: 35f));
            Kit.SetSpecial(p, Kit.Attack(sp, sf, 0f, rangeInner: 0f, rangeOuter: 200f, rangeRetreat: 30f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
        }

        // Dice Imp: tosses a die that rolls along the floor and hits for 1-6 x 0.25 (basic 0), two in a V after a six
        // (basic 1); Roll slams the big die, which bursts into 1-6 shards. Quirk: ImpLuck.
        static void ImpKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int die = Kit.AddEffect(p, JinxFx.Die, offsetX: 12f, offsetY: 1f);   // leaves the hand at (12, -11), rolls on the floor
            int twinA = Kit.AddEffect(p, JinxFx.Die, offsetX: 12f, offsetY: 1f, angle: -12f);
            int twinB = Kit.AddEffect(p, JinxFx.Die, offsetX: 12f, offsetY: 1f, angle: 12f);
            int face = Kit.AddEffect(p, JinxFx.DieFace, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var ts = Kit.Shot(sh, "Toss", "ModDiceToss", 3, v, 0f, die).Build();
            var tw = Kit.Shot(sh, "TossTwin", "ModDiceTossTwin", 3, v, 0f, twinA, twinB).Ev(4, "ModJinxTwinThrown").Build();
            var rl = Special(sh, "Roll", "ModDiceRoll").Ev(6, "AnimAttack", face).Ev(6, "ModRollDice").EvO(6, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            // a die rolls about 53 px (160 px/s with drag) before it stops
            atk.Add(Kit.Attack(a0, ts, 1.4f, rangeInner: 32f, rangeOuter: 55f, rangeRetreat: 24f));
            atk.Add(Kit.Attack(a0, tw, 1.4f, rangeInner: 32f, rangeOuter: 55f, rangeRetreat: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, rl, 0f, rangeInner: 20f, rangeOuter: 70f, rangeRetreat: 0f), 5.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 9f);
            ImpLuck.LuckyIdle = Looped(sh, "IdleLucky", "ModDiceIdleLucky");
            ImpLuck.LuckyRun = Looped(sh, "RunLucky", "ModDiceRunLucky");
        }

        // ---------------------------------------------------------------------------------------------- tier 2
        // Ringmaster: a long whip crack; Hoop throws a flaming hoop that spins out and comes back. Quirk: RingmasterEncore.
        static void RingmasterKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int whip = Kit.AddEffect(p, JinxFx.Whip, attach: true, destroyOnAnimEnd: true, offsetX: 20f, offsetY: 12f);   // tip (33, -12): x 6..34
            int hoop = Kit.AddEffect(p, JinxFx.Hoop, offsetX: 11f, offsetY: 15f);
            var wh = Kit.Melee(sh, "Whip", "ModRingmasterWhip", v, 3, whip, 20f).Build();
            var hp = Kit.Shot(sh, "Hoop", "ModRingmasterHoop", 4, v, 0f, hoop).Ev(0, "ModWildCard").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, wh, 1.2f, rangeInner: 22f, rangeOuter: 38f));
            // the hoop turns back after about 64 px
            Kit.SetSpecial(p, Kit.Attack(sp, hp, 0f, rangeInner: 35f, rangeOuter: 66f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
            RingmasterEncore.EncoreClip = Once(sh, "Encore", "ModRingmasterEncore");
        }

        // Marionette: a lash of its jerked arm; Strings fires three threads that tug the hero and daze. Quirk: MarionetteMirror.
        static void MarionetteKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lash = Kit.AddEffect(p, JinxFx.Lash, attach: true, offsetX: -1f, offsetY: 10f);   // the hand reaches (14, -10)
            var strings = new List<int>();
            foreach (var a in new[] { -18f, 0.01f, 18f }) strings.Add(Kit.AddEffect(p, JinxFx.Strings, offsetX: 12f, offsetY: 14f, angle: a));
            var ls = Kit.Melee(sh, "Lash", "ModMarionetteLash", v, 3, lash, 40f).Build();
            var st = Kit.Shot(sh, "Strings", "ModMarionetteStrings", 3, v, 0.05f, strings.ToArray()).Ev(0, "ModWildCard").Ev(7, "ModJinxMirror").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ls, 1.2f, rangeInner: 10f, rangeOuter: 22f));
            Kit.SetSpecial(p, Kit.Attack(sp, st, 0f, rangeInner: 40f, rangeOuter: 120f, rangeRetreat: 20f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
            MarionetteMirror.MirrorIdle = Looped(sh, "MirrorIdle", "ModMarionetteMirrorIdle");
            MarionetteMirror.MirrorRun = Looped(sh, "MirrorRun", "ModMarionetteMirrorRun");
        }

        // Fortune Teller: a crystal bolt that can daze; Foretell lays a fate mark under the hero. Quirk: TellerFate.
        static void TellerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bolt = Kit.AddEffect(p, JinxFx.CrystalBolt, offsetX: 11f, offsetY: 13f);
            var gz = Kit.Shot(sh, "Gaze", "ModTellerGaze", 3, v, 0f, bolt).Build();
            Func<string, exSpriteAnimClip> foretell = anim =>
                Special(sh, anim, "ModTeller" + anim).Ev(4, "ModJinxForetell").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, gz, 1.4f, rangeInner: 50f, rangeOuter: 130f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, foretell("Foretell"), 0f, rangeInner: 30f, rangeOuter: 150f, rangeRetreat: 30f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 13f);
            var fates = new[] { "Tower", "Fool", "Star" };
            TellerFate.FateIdle = new exSpriteAnimClip[3]; TellerFate.FateRun = new exSpriteAnimClip[3]; TellerFate.FateCast = new exSpriteAnimClip[3];
            for (int k = 0; k < 3; k++)
            {
                TellerFate.FateIdle[k] = Looped(sh, "Idle" + fates[k], "ModTellerIdle" + fates[k]);
                TellerFate.FateRun[k] = Looped(sh, "Run" + fates[k], "ModTellerRun" + fates[k]);
                TellerFate.FateCast[k] = sh.Has("Foretell" + fates[k]) ? foretell("Foretell" + fates[k]) : null;
            }
        }

        // Snake-Eyes: a poison lunge; Craps flicks two dice. Quirk: SnakeCraps.
        static void SnakeKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, JinxFx.SnakeBite, attach: true, destroyOnAnimEnd: true, offsetX: 17f, offsetY: 7f);   // jaws (17, -7)
            var st = Kit.Melee(sh, "Strike", "ModSnakeStrike", v, 3, bite, 60f).Build();
            var cr = Special(sh, "Craps", "ModSnakeCraps").Ev(3, "ModJinxCraps").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, st, 1.3f, rangeInner: 14f, rangeOuter: 30f));
            // a die rolls about 55 px before it stops
            Kit.SetSpecial(p, Kit.Attack(sp, cr, 0f, rangeInner: 25f, rangeOuter: 65f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 7f);
            SnakeCraps.DazedClip = Looped(sh, "Dazed", "ModSnakeDazed");
        }

        // Card Soldier: a long pike thrust; Deal flicks three face-down trap cards round the hero. Quirk: SoldierPaper.
        static void SoldierKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int pike = Kit.AddEffect(p, JinxFx.PikeThrust, attach: true, destroyOnAnimEnd: true, offsetX: 22f, offsetY: 9f);   // blade x 27..33
            var th = Kit.Melee(sh, "Thrust", "ModJinxSoldierThrust", v, 3, pike, 40f).Build();
            var dl = Special(sh, "Deal", "ModJinxSoldierDeal").Ev(3, "ModJinxDealTraps").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, th, 1.3f, rangeInner: 18f, rangeOuter: 34f));
            Kit.SetSpecial(p, Kit.Attack(sp, dl, 0f, rangeInner: 30f, rangeOuter: 120f, rangeRetreat: 20f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
            SoldierPaper.EdgeIdle = Looped(sh, "EdgeIdle", "ModJinxSoldierEdgeIdle");
            SoldierPaper.EdgeRun = Looped(sh, "EdgeRun", "ModJinxSoldierEdgeRun");
        }

        // Loaded Die: hops and slams; Tumble rolls at the hero and lands on the face it keeps. Quirk: LoadedDieFace.
        static void LoadedDieKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, JinxFx.DieSlam, attach: true, destroyOnAnimEnd: true, offsetX: 8f, offsetY: 6f);   // the cube lands x 1..15
            int roll = Kit.AddEffect(p, JinxFx.DieRoll, attach: true, destroyOnAnimEnd: true, offsetX: 3f, offsetY: 9f);
            var sl = Kit.Melee(sh, "Slam", "ModJinxDieSlam", v, 4, slam, 35f).Ev(4, "ModJinxLoadedSlam").Build();
            var rl = new ClipBuilder(sh, "Roll", "ModJinxDieRoll").Once()
                .Ev(0, "ModWildCard").EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff").EvF(1, "AnimMove", 210f).Ev(1, "AnimAttack", roll).EvO(1, "AnimSound", v)
                .Ev(7, "AnimMoveStop").Ev(7, "ModJinxLoad").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.3f, rangeInner: 8f, rangeOuter: 20f));
            // 210 px/s for the 0.36 s tumble = 76 px
            Kit.SetSpecial(p, Kit.Attack(sp, rl, 0f, rangeInner: 25f, rangeOuter: 80f, rangeRetreat: 0f), 6f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 8f);
        }

        // ---------------------------------------------------------------------------------------------- tier 3
        // Roulette Ouroboros: lets go of its tail to bite; Place Your Bets spins it as a wheel. Quirk: RouletteBets.
        static void RouletteKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int bite = Kit.AddEffect(p, JinxFx.RouletteBite, attach: true, destroyOnAnimEnd: true, offsetX: 22f, offsetY: 19f);   // jaws x 24..30
            var bt = Kit.Melee(sh, "Bite", "ModJinxRouletteBite", v, 3, bite, 30f).Build();
            var spin = Special(sh, "Spin", "ModJinxRouletteSpin").Ev(1, "ModJinxBets").EvO(1, "AnimSound", v).Ev(8, "ModJinxBallDrop")
                .Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, bt, 1.5f, rangeInner: 14f, rangeOuter: 32f));
            Kit.SetSpecial(p, Kit.Attack(sp, spin, 0f, rangeInner: 0f, rangeOuter: 140f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 19f);
        }

        // Gorgon: the hair snakes strike; Stone Stare fires a beam from her eyes along the aim that roots. Quirk: GorgonGaze.
        static void GorgonKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int lash = Kit.AddEffect(p, JinxFx.GorgonLash, attach: true, destroyOnAnimEnd: true, offsetX: 16f, offsetY: 16f);   // heads x 7..25
            int gaze = Kit.AddEffect(p, JinxFx.Gaze, offsetX: 6f, offsetY: 30f);   // eyes at (5, -30)
            var ls = Kit.Melee(sh, "Lash", "ModJinxGorgonLash", v, 3, lash, 25f).Build();
            var st = new ClipBuilder(sh, "Stare", "ModJinxGorgonStare").Once()
                .Ev(0, "ModWildCard").EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(0, "AnimMoveStop").Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(4, "AnimAttack", gaze).Ev(4, "ModJinxStareFires").EvO(4, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ls, 1.4f, rangeInner: 10f, rangeOuter: 26f));
            Kit.SetSpecial(p, Kit.Attack(sp, st, 0f, rangeInner: 20f, rangeOuter: 66f, rangeRetreat: 10f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 22f);
        }

        // Card King: the club smashes a quake in front; Hold Court raises the Diamonds card. Quirk: KingCourt.
        static void KingKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int quake = Kit.AddEffect(p, JinxFx.ClubSlam, offsetX: 26f, offsetY: 0.01f);   // the club lands at x 24..30
            Kit.AimReach(p, quake, 4f, 3f);
            var sm = new ClipBuilder(sh, "Smash", "ModJinxKingSmash").Once().EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").EvF(3, "AnimMoveStick", 20f).Ev(3, "AnimAttack", quake)
                .EvO(3, "AnimSound", v).Ev(4, "AnimMoveStop").Ev(-1, "AnimRun").Build();
            var ct = Special(sh, "Court", "ModJinxKingCourt").Ev(3, "ModJinxHoldCourt").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sm, 1.7f, rangeInner: 16f, rangeOuter: 36f));
            Kit.SetSpecial(p, Kit.Attack(sp, ct, 0f, rangeInner: 0f, rangeOuter: 90f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
            KingCourt.CourtIdle = Looped(sh, "CourtIdle", "ModJinxKingCourtIdle");
            KingCourt.CourtRun = Looped(sh, "CourtRun", "ModJinxKingCourtRun");
        }

        // House of Cards: the top tier topples onto the hero (one clip per tier count, a whirl at none); Card Storm
        // sends six cards round it, then at the hero. Quirk: HouseTiers.
        static void HouseKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int top = Kit.AddEffect(p, JinxFx.Topple, attach: true, destroyOnAnimEnd: true, offsetX: 12f, offsetY: 10f);   // the tier slaps x 4..20
            int whirl = Kit.AddEffect(p, JinxFx.WhirlSlash, attach: true, destroyOnAnimEnd: true, offsetX: 0f, offsetY: 10f);
            Func<string, int, exSpriteAnimClip> storm = (anim, frame) =>
                Special(sh, anim, "ModJinxHouse" + anim).Ev(frame, "ModJinxCardStorm").EvO(frame, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            foreach (var t in new[] { "Topple", "Topple2", "Topple1" })
                atk.Add(Kit.Attack(a0, Kit.Melee(sh, t, "ModJinxHouse" + t, v, 3, top, 25f).Build(), 1.5f, rangeInner: 10f, rangeOuter: 24f));
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "WhirlSlash", "ModJinxHouseWhirlSlash", v, 2, whirl, 0f).Build(), 1.1f, rangeInner: 0f, rangeOuter: 18f));
            Kit.SetSpecial(p, Kit.Attack(sp, storm("Storm", 4), 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
            HouseTiers.TierIdle = new[] { Looped(sh, "Whirl", "ModJinxHouseWhirl"), Looped(sh, "Idle1", "ModJinxHouseIdle1"), Looped(sh, "Idle2", "ModJinxHouseIdle2") };
            HouseTiers.TierRun = new[] { Looped(sh, "WhirlRun", "ModJinxHouseWhirlRun"), Looped(sh, "Run1", "ModJinxHouseRun1"), Looped(sh, "Run2", "ModJinxHouseRun2") };
            HouseTiers.TierStorm = new[] { storm("Storm0", 3), storm("Storm1", 4), storm("Storm2", 4) };
        }

        // High Roller: flicks a poker chip; All In shoves his chips into a pot on the floor. Quirk: RollerPot.
        static void RollerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int chip = Kit.AddEffect(p, JinxFx.Chip, offsetX: 17f, offsetY: 20f);   // off the thumb at (17, -20)
            var fl = Kit.Shot(sh, "Flick", "ModJinxRollerFlick", 2, v, 0f, chip).Build();
            var ai = Special(sh, "AllIn", "ModJinxRollerAllIn").Ev(5, "ModJinxAllIn").EvO(5, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, fl, 1.2f, rangeInner: 40f, rangeOuter: 110f, rangeRetreat: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, ai, 0f, rangeInner: 20f, rangeOuter: 90f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 18f);
            RollerPot.BustClip = sh.Has("Bust") ? new ClipBuilder(sh, "Bust", "ModJinxRollerBust").Once().Durations(0.12f, 0.16f, 0.2f, 0.4f, 0.4f, 0.22f).Build() : null;
        }

        // Natural Twenty: rams with its facets; Crit leaps and rolls itself on landing. Quirk: TwentyCrit.
        static void TwentyKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int ram = Kit.AddEffect(p, JinxFx.Ram, attach: true, destroyOnAnimEnd: true, offsetX: 13f, offsetY: 12f);   // facets to x 19
            var rm = Kit.Melee(sh, "Ram", "ModJinxTwentyRam", v, 3, ram, 45f).Build();
            var cr = new ClipBuilder(sh, "Crit", "ModJinxTwentyCrit").Once()
                .Ev(0, "ModWildCard").EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(1, "AnimInputMultiplyStop").Ev(1, "AnimInputOff").EvF(1, "AnimMove", 170f).EvO(1, "AnimSound", v)
                .Ev(6, "AnimMoveStop").Ev(6, "ModJinxCrit").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, rm, 1.5f, rangeInner: 12f, rangeOuter: 28f));
            // 170 px/s for the 0.35 s in the air = 60 px
            Kit.SetSpecial(p, Kit.Attack(sp, cr, 0f, rangeInner: 30f, rangeOuter: 70f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
            TwentyCrit.FumbleClip = Looped(sh, "Fumble", "ModJinxTwentyFumble");
        }

        // Nutcracker: a sabre cut; Crack lunges jaws first, holds and crunches twice. Quirk: NutKey.
        static void NutKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int cut = Kit.AddEffect(p, JinxFx.Sabre, attach: true, offsetX: 4f, offsetY: 14f);   // the blade sweeps x 1..23, y -25..-3
            var sb = Kit.Melee(sh, "Sabre", "ModJinxNutSabre", v, 3, cut, 25f).Build();
            var ck = new ClipBuilder(sh, "Crack", "ModJinxNutCrack").Once()
                .Ev(0, "ModWildCard").EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff")
                .EvF(3, "AnimMoveStick", 60f).EvO(3, "AnimSound", v).Ev(4, "AnimMoveStop")
                .Ev(4, "ModJinxCrackGrab").Ev(6, "ModJinxCrackBite").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sb, 1.4f, rangeInner: 10f, rangeOuter: 24f));
            Kit.SetSpecial(p, Kit.Attack(sp, ck, 0f, rangeInner: 8f, rangeOuter: 30f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 16f);
            NutKey.SlowIdle = Looped(sh, "IdleSlow", "ModJinxNutIdleSlow");
            NutKey.SlowRun = Looped(sh, "RunSlow", "ModJinxNutRunSlow");
            NutKey.RewindClip = Looped(sh, "Rewind", "ModJinxNutRewind");
        }

        // Puppeteer: both puppets stab; Curtain Call hauls allies round the hero. Quirk: PuppeteerStrings.
        static void PuppeteerKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int jab = Kit.AddEffect(p, JinxFx.PuppetJab, attach: true, destroyOnAnimEnd: true, offsetX: 17f, offsetY: 8f);   // knives (15-23, -4..-13)
            var dn = Kit.Melee(sh, "Dance", "ModPuppeteerDance", v, 3, jab, 30f).Build();
            var cc = Special(sh, "Curtain", "ModPuppeteerCurtain").Ev(3, "ModJinxCurtainCall").EvO(3, "AnimSound", v).Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, dn, 1.4f, rangeInner: 14f, rangeOuter: 30f));
            Kit.SetSpecial(p, Kit.Attack(sp, cc, 0f, rangeInner: 0f, rangeOuter: 160f, rangeRetreat: 30f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 14f);
        }

        // The Oracle: a third-eye orb that leads the hero; Prophecy shows her next move first. Quirk: OracleProphecy.
        static void OracleKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            var gz = Kit.Shot(sh, "Gaze", "ModJinxOracleGaze", 3, v, 0f).Ev(3, "ModJinxLeadOrb").Build();
            var pr = Special(sh, "Prophecy", "ModJinxOracleProphecy").Ev(2, "ModJinxProphecy").EvO(2, "AnimSound", v)
                .Ev(7, "ModJinxProphecyBlink").Ev(9, "ModJinxProphecyCast").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, gz, 1.4f, rangeInner: 50f, rangeOuter: 130f, rangeRetreat: 40f));
            Kit.SetSpecial(p, Kit.Attack(sp, pr, 0f, rangeInner: 0f, rangeOuter: 160f, rangeRetreat: 30f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
        }

        // One-Armed Bandit: the lever slams the floor; Jackpot spins three reels and pays each out. Quirk: BanditReels.
        static void BanditKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int slam = Kit.AddEffect(p, JinxFx.BanditSlam, attach: true, destroyOnAnimEnd: true, offsetX: 19f, offsetY: 4f);   // knob at (20, -3)
            var sl = Kit.Melee(sh, "Slam", "ModBanditSlam", v, 3, slam, 25f).Build();
            var jp = Special(sh, "Jackpot", "ModBanditJackpot").Ev(1, "ModJinxReelsSpin").EvO(2, "AnimSound", v).Ev(8, "ModJinxJackpot")
                .Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, sl, 1.6f, rangeInner: 14f, rangeOuter: 28f));
            Kit.SetSpecial(p, Kit.Attack(sp, jp, 0f, rangeInner: 20f, rangeOuter: 140f, rangeRetreat: 0f), 7.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 12f);
            BanditReels.JamClip = Looped(sh, "Jam", "ModBanditJam");
        }

        // The Grand Jester: juggles three bursting balls in the Comedy mask (basic 0) or smashes his marotte in the
        // Tragedy mask (basic 1); Turn the Mask swaps them. Quirk: JesterMasks.
        static void JesterKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            // the balls hit feet: launched along the floor under the hands (12, -20), drawn up there
            int b1 = Kit.AddEffect(p, JinxFx.JuggleBall, offsetX: 12f, offsetY: 1f, angle: -16f);
            int b2 = Kit.AddEffect(p, JinxFx.JuggleBall, offsetX: 12f, offsetY: 1f, angle: 0.01f);
            int b3 = Kit.AddEffect(p, JinxFx.JuggleBall, offsetX: 12f, offsetY: 1f, angle: 16f);
            int bash = Kit.AddEffect(p, JinxFx.MarotteBash, attach: true, destroyOnAnimEnd: true, offsetX: 18f, offsetY: 7f);
            var jg = new ClipBuilder(sh, "Juggle", "ModJesterJuggle").Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(3, "AnimInputMultiplyStop").Ev(3, "AnimInputOff")
                .Ev(3, "AnimAttack", b1).EvO(3, "AnimSound", v).Ev(4, "AnimAttack", b2).Ev(5, "AnimAttack", b3).Ev(-1, "AnimRun").Build();
            var bs = Kit.Melee(sh, "Bash", "ModJesterBash", v, 3, bash, 30f).Build();
            Func<string, exSpriteAnimClip> turn = anim =>
                Special(sh, anim, "ModJester" + anim).EvO(1, "AnimSound", v).Ev(7, "ModJinxTurnMask").Ev(-1, "AnimRun").Build();
            atk.Clear();
            // a ball rolls about 66 px before it bursts
            atk.Add(Kit.Attack(a0, jg, 1.8f, rangeInner: 42f, rangeOuter: 72f, rangeRetreat: 30f));
            atk.Add(Kit.Attack(a0, bs, 1.6f, rangeInner: 10f, rangeOuter: 26f));
            Kit.SetSpecial(p, Kit.Attack(sp, turn("Flip"), 0f, rangeInner: 0f, rangeOuter: 120f, rangeRetreat: 0f), 6.5f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 20f);
            JesterMasks.SadIdle = Looped(sh, "IdleSad", "ModJesterIdleSad");
            JesterMasks.SadRun = Looped(sh, "RunSad", "ModJesterRunSad");
            JesterMasks.FlipBack = sh.Has("FlipBack") ? turn("FlipBack") : null;
        }

        // Big-Top Chimera: a raking maul; Ring of Fire leaps at the hero (untouchable in the air) and lands in a ring of
        // flames. Quirk: ChimeraLastAct.
        static void ChimeraKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0]; var sp = Kit.Special(p); var v = Kit.Voice(p);
            int n0 = Strike.Mark(p);
            int maul = Kit.AddEffect(p, JinxFx.ChimeraMaul, attach: true, offsetX: 8f, offsetY: 6f);   // claws x 15..24, y -9..-2
            int ring = Kit.AddEffect(p, JinxFx.FireRing, offsetX: 3f, offsetY: 0.01f, spawnPoint: DamageEffectData.eSpawnPoint.Position);
            var ml = Kit.Melee(sh, "Maul", "ModChimeraMaul", v, 3, maul, 40f).Build();
            var lp = new ClipBuilder(sh, "Leap", "ModChimeraLeap").Once()
                .Ev(0, "ModWildCard").EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").Ev(2, "AnimStartInvincibility")
                .EvF(2, "AnimMove", 250f).EvO(2, "AnimSound", v)
                .Ev(5, "AnimMoveStop").Ev(5, "AnimAttack", ring).Ev(6, "AnimStopInvincibility").Ev(-1, "AnimRun").Build();
            atk.Clear();
            atk.Add(Kit.Attack(a0, ml, 1.5f, rangeInner: 16f, rangeOuter: 30f));
            // 250 px/s for the 0.26 s in the air = 65 px, then the ring reaches 14 px past the feet
            Kit.SetSpecial(p, Kit.Attack(sp, lp, 0f, rangeInner: 30f, rangeOuter: 80f, rangeRetreat: 0f), 7f);
            Kit.Order(p, Attacks.eAttackOrderType.InOrder);
            Strike.Feet(p, n0, 10f);
            ChimeraLastAct.BurnIdle = Looped(sh, "IdleBurn", "ModChimeraIdleBurn");
            ChimeraLastAct.BurnRun = Looped(sh, "RunBurn", "ModChimeraRunBurn");
        }

        // The AI-driven Jack that the Puppeteer and the boss let loose (fodder base: it has an AI brain)
        static void JackMinionKit(Player p, SpriteSheet sh)
        {
            var atk = Kit.Attacks(p); var a0 = atk[0];
            int n0 = Strike.Mark(p);
            int punch = Kit.AddEffect(p, JinxFx.LooseJackButt, attach: true, destroyOnAnimEnd: true, offsetX: 8f, offsetY: 9f);   // head to (8, -9)
            Kit.Effects(p)[punch].m_offsetAimDown = new Vector2(5f, 0f);
            var vo = Kit.Voice(p);
            atk.Clear();
            atk.Add(Kit.Attack(a0, Kit.Melee(sh, "Punch", "ModJackMinionPunch", vo, 3, punch, 30f).Build(), 1.6f, rangeInner: 6f, rangeOuter: 16f));
            AimedMelee.Angles(atk[0], sh, "Punch", a => Kit.Melee(sh, a, "ModJackMinion" + a, vo, 3, punch, 30f).Build());
            R.Set(p, "m_hasSpecialAttack", false);
            Strike.Feet(p, n0, 7f);
            MinionAI.Tune(p, 140f, 14f, 18f, 1.6f, 2.2f);
        }

        public static readonly MonsterDef JackMinion = new MonsterDef
        {
            id = "JackMinion", art = "JinxJackMinion", basePrefab = "EnemyFodderMushroom", health = 2f, kit = JackMinionKit, keepEvolutions = true
        };

        // Evolution tree: every evolution has exactly one parent.
        //   JackInTheBox -> Ringmaster, Marionette            Ringmaster        -> Chimera, GrandJester
        //                                                     Marionette        -> Puppeteer, Nutcracker
        //   CardSharp    -> FortuneTeller, CardSoldier        FortuneTeller     -> Oracle, Bandit
        //                                                     CardSoldier       -> CardKing, HouseOfCards
        //   DiceImp      -> SnakeEyes, LoadedDie              SnakeEyes         -> Gorgon, Roulette
        //                                                     LoadedDie         -> HighRoller, Twenty
        public static readonly List<MonsterDef> Monsters = new List<MonsterDef>
        {
            new MonsterDef { id = "JackInTheBox", art = "JinxJackBox", basePrefab = "EnemyMushroom", health = 4f, evolveCost = 0f,
                             evolveTo = new[] { "Ringmaster", "Marionette" }, kit = JackKit },
            new MonsterDef { id = "CardSharp", art = "JinxCardSharp", basePrefab = "EnemyGoblin", health = 3.5f, evolveCost = 0f,
                             evolveTo = new[] { "JinxFortuneTeller", "JinxCardSoldier" }, kit = SharpKit },
            new MonsterDef { id = "DiceImp", art = "JinxDiceImp", basePrefab = "EnemyFlyingEye_Dodge", health = 3f, evolveCost = 0f,
                             evolveTo = new[] { "JinxSnakeEyes", "JinxLoadedDie" }, kit = ImpKit },
            new MonsterDef { id = "Ringmaster", art = "JinxRingmaster", basePrefab = "EnemyOrc", health = 7f, evolveCost = 2.5f,
                             evolveTo = new[] { "JinxChimera", "GrandJester" }, kit = RingmasterKit },
            new MonsterDef { id = "Marionette", art = "JinxMarionette", basePrefab = "EnemyWitch", health = 5.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "JinxPuppeteer", "JinxNutcracker" }, kit = MarionetteKit },
            new MonsterDef { id = "JinxFortuneTeller", art = "JinxFortuneTeller", basePrefab = "EnemySkeletonMage", health = 6f, evolveCost = 2.5f,
                             evolveTo = new[] { "JinxOracle", "JinxBandit" }, kit = TellerKit },
            new MonsterDef { id = "JinxSnakeEyes", art = "JinxSnakeEyes", basePrefab = "EnemyScorpion", health = 6.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "JinxGorgon", "JinxRoulette" }, kit = SnakeKit },
            new MonsterDef { id = "JinxCardSoldier", art = "JinxCardSoldier", basePrefab = "EnemyOrc", health = 6.5f, evolveCost = 2.5f,
                             evolveTo = new[] { "JinxCardKing", "JinxHouseOfCards" }, kit = SoldierKit },
            new MonsterDef { id = "JinxLoadedDie", art = "JinxLoadedDie", basePrefab = "EnemyRatman", health = 6f, evolveCost = 2.5f,
                             evolveTo = new[] { "JinxHighRoller", "JinxTwenty" }, kit = LoadedDieKit },
            new MonsterDef { id = "JinxCardKing", art = "JinxCardKing", basePrefab = "EnemyTroll", health = 12f, speedMult = 0.85f,
                             evolveCost = 4.5f, kit = KingKit },
            new MonsterDef { id = "JinxHouseOfCards", art = "JinxHouseOfCards", basePrefab = "EnemyPriestess", health = 10.5f, speedMult = 0.9f,
                             evolveCost = 4.5f, kit = HouseKit },
            new MonsterDef { id = "JinxHighRoller", art = "JinxHighRoller", basePrefab = "EnemyCapraDemon", health = 11f,
                             evolveCost = 4.5f, kit = RollerKit },
            new MonsterDef { id = "JinxTwenty", art = "JinxTwenty", basePrefab = "EnemyMinotaur", health = 11f,
                             evolveCost = 4.5f, kit = TwentyKit },
            new MonsterDef { id = "JinxGorgon", art = "JinxGorgon", basePrefab = "EnemyFacelessShaman", health = 10.5f,
                             evolveCost = 4.5f, kit = GorgonKit },
            new MonsterDef { id = "JinxRoulette", art = "JinxRoulette", basePrefab = "EnemySmallDragon", health = 11.5f, speedMult = 0.9f,
                             evolveCost = 4.5f, kit = RouletteKit },
            new MonsterDef { id = "JinxNutcracker", art = "JinxNutcracker", basePrefab = "EnemyGhoul", health = 11.5f,
                             evolveCost = 4.5f, kit = NutKit },
            new MonsterDef { id = "JinxOracle", art = "JinxOracle", basePrefab = "EnemyBeholder", health = 10.5f,
                             evolveCost = 4.5f, kit = OracleKit },
            new MonsterDef { id = "GrandJester", art = "JinxGrandJester", basePrefab = "EnemyPriestess", health = 12f, evolveCost = 4.5f,
                             kit = JesterKit },
            new MonsterDef { id = "JinxChimera", art = "JinxChimera", basePrefab = "EnemyMinotaur", health = 11.5f, speedMult = 1.15f,
                             evolveCost = 4.5f, kit = ChimeraKit },
            new MonsterDef { id = "JinxPuppeteer", art = "JinxPuppeteer", basePrefab = "EnemySkeletonPope", health = 10.5f, speedMult = 0.9f,
                             evolveCost = 4.5f, kit = PuppeteerKit },
            new MonsterDef { id = "JinxBandit", art = "JinxBandit", basePrefab = "EnemyTroll", health = 12f, speedMult = 0.85f,
                             evolveCost = 4.5f, kit = BanditKit },
        };

        /// <summary>Each monster's quirk.</summary>
        static readonly Dictionary<string, Type> Quirks = new Dictionary<string, Type>
        {
            { "JackInTheBox", typeof(JackWindUp) }, { "CardSharp", typeof(SharpAce) }, { "DiceImp", typeof(ImpLuck) },
            { "Ringmaster", typeof(RingmasterEncore) }, { "Marionette", typeof(MarionetteMirror) }, { "JinxFortuneTeller", typeof(TellerFate) },
            { "JinxSnakeEyes", typeof(SnakeCraps) }, { "JinxCardSoldier", typeof(SoldierPaper) }, { "JinxLoadedDie", typeof(LoadedDieFace) },
            { "JinxCardKing", typeof(KingCourt) }, { "JinxHouseOfCards", typeof(HouseTiers) }, { "JinxHighRoller", typeof(RollerPot) },
            { "JinxTwenty", typeof(TwentyCrit) }, { "JinxGorgon", typeof(GorgonGaze) }, { "JinxRoulette", typeof(RouletteBets) },
            { "JinxNutcracker", typeof(NutKey) }, { "JinxOracle", typeof(OracleProphecy) }, { "GrandJester", typeof(JesterMasks) },
            { "JinxChimera", typeof(ChimeraLastAct) }, { "JinxPuppeteer", typeof(PuppeteerStrings) }, { "JinxBandit", typeof(BanditReels) },
        };

        public static readonly GodDef God = new GodDef
        {
            name = "Jinx",
            text = "Specials give a random boon",
            flavour = "Every roll is loaded.\nNobody told you which way.",
            winText = "THE CURTAIN FALLS",
            portraitArt = "DeityJinx",
            startingMonsters = new[] { "JackInTheBox", "CardSharp", "DiceImp" },
        };

        public static void Register()
        {
            JinxFx.Build();
            foreach (var m in Monsters)
            {
                // Wild Card "Diamonds" shows Jinx's own diamond-card shield
                var t = new JinxTraits { plateFx = JinxFx.DiamondPlate, plateBreakFx = JinxFx.DiamondBreak };
                Type q;
                if (Quirks.TryGetValue(m.id, out q)) t.behaviours.Add(q);
                MonsterTraits.Register(m.PrefabName, t);
            }
            foreach (var m in Monsters) MonsterFactory.Build(m);
            MonsterFactory.LinkEvolutions(Monsters);
            var jack = MonsterFactory.Build(JackMinion);
            if (jack != null) JinxFx.JackSpawner = FxKit.MinionSpawner("ModJackSpawner", jack.gameObject, "FxConfetti", "Play");
            MonsterEvents.AttackSpawned += OnAttackSpawned;
            s_deity = DeityFactory.Register(God);
            // the gold idol carved in the jester's likeness
            var prev = SlotGods.PortraitFor;
            SlotGods.PortraitFor = (tier, perk) =>
                tier == SlotTier.Gold && perk != null && perk == s_deity ? Idol() : (prev != null ? prev(tier, perk) : null);
            Strike.KeepAllScales();
        }

        static Deity s_deity;
        static exSpriteAnimClip s_idol;

        static exSpriteAnimClip Idol()
        {
            if (s_idol == null) s_idol = SlotArt.Clip("DeityGoldIdolJinx", "Idle");
            return s_idol;
        }

        static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
        {
            var q = owner != null && fx != null ? owner.GetComponent<JinxBehaviour>() : null;
            if (q != null) q.OnAttackSpawned(fx, template);
        }
    }
}
