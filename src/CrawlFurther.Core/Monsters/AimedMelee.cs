using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// Melee that strikes where the monster aims, the way vanilla does it.
    ///
    /// Engine facts (Attacks.SpawnEffect / CalculateEffectOffset / Effect.OnSpawn):
    /// - A slot's offsetX is turned by the aim (m_rotateOffsetX, on by default); its offsetY is NOT.
    /// - The effect is spawned at the aim angle, but Effect.OnSpawn zeroes that rotation unless the effect has
    ///   m_freeRotate: such a box only flips left/right and keeps its sideways shape when the monster aims up or down.
    /// - Vanilla melee boxes and swipe arts are free-rotating (DamageGnome, SkelSwipe, OrcSwipe, OrcDamageInvisible,
    ///   DamageGiantSpiderMelee, DamageBlobFishAttack, DFX_RatmanSwipe...). The only non-rotating vanilla melee box is the
    ///   giant rat's body slam (DamageGiantRatAttack), which FxKit.BodyHit clones; FxKit.TimedHit forces freeRotate off.
    /// - Vanilla body anims are side-only, except 4 monsters that have up/down attack anims through AttackData.m_animAngles
    ///   (picked by the input angle when the attack starts).
    ///
    /// API:
    /// - <see cref="Rotating"/>: make a melee template (box and any drawn slash on it) turn with the aim. Use for anything
    ///   that strikes toward the aim. Keep ground rings/pools, upright effects and body-centred auras non-rotating.
    ///   Boxes must be centred on the strike line (Strike.HitBox cx along the aim, cy 0); height goes in the slot offsetY.
    /// - <see cref="Angles"/>: add up/down variants of an attack's anim (drawn as "&lt;anim&gt;Up" / "&lt;anim&gt;Down" on the
    ///   same sheet, same frame count and event frames). Optional; for moves that are a straight thrust.
    /// </summary>
    public static class AimedMelee
    {
        /// <summary>Turn the template with the aim (box + art), flipping art that faces left so it never draws upside down.</summary>
        public static GameObject Rotating(GameObject go)
        {
            if (go == null) return null;
            var e = go.GetComponent<Effect>();
            if (e != null) { R.Set(e, "m_freeRotate", true); R.Set(e, "m_canFlip", true); }
            return go;
        }

        /// <summary>
        /// Give <paramref name="attack"/> up and down anims built like its side anim. <paramref name="build"/> makes a clip
        /// from an anim name (e.g. a => Kit.Melee(sh, a, "ModX" + a, v, 3, slot, 30f).Build()). Anims the sheet lacks are
        /// skipped (the side anim keeps playing). Up = aim within (90 - half, 90 + half), down the mirror.
        /// </summary>
        public static void Angles(AttackData attack, SpriteSheet sh, string anim, System.Func<string, exSpriteAnimClip> build, float half = 40f)
        {
            if (attack == null || sh == null || build == null) return;
            if (attack.m_animAngles == null) attack.m_animAngles = new List<AttackDataAnimAngle>();
            if (sh.Has(anim + "Up"))
            {
                var up = build(anim + "Up");
                if (up != null) attack.m_animAngles.Add(new AttackDataAnimAngle { m_animation = up, m_angleRange = new MinMaxRange(90f - half, 90f + half) });
            }
            if (sh.Has(anim + "Down"))
            {
                var dn = build(anim + "Down");
                if (dn != null) attack.m_animAngles.Add(new AttackDataAnimAngle { m_animation = dn, m_angleRange = new MinMaxRange(-90f - half, -90f + half) });
            }
        }
    }
}
