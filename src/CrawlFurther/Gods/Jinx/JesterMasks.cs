using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// The Grand Jester, Two Faces. In the white Comedy mask he moves <see cref="ComedySpeed"/>x and juggles at range
    /// (basic 0); in the blue Tragedy mask he takes <see cref="TragedyDamage"/>x damage and smashes up close with his
    /// marotte (basic 1). Turn the Mask whips his head round and swaps them with a ta-da of bell sparks round him.
    /// Tell: the face itself, and the marotte wearing the other one.
    /// </summary>
    public class JesterMasks : JinxBehaviour
    {
        public const float ComedySpeed = 1.15f, TragedyDamage = 0.75f;
        /// <summary>The tragedy stance and the Tragedy-to-Comedy turn (set by the kit).</summary>
        public static exSpriteAnimClip SadIdle, SadRun, FlipBack;

        bool m_tragedy;

        protected override void OnEnable() { base.OnEnable(); Wear(false); }

        void Wear(bool tragedy)
        {
            m_tragedy = tragedy;
            SetStance(tragedy ? SadIdle : null, tragedy ? SadRun : null);
            NextBasic(tragedy ? 1 : 0);
            SetSpecialClip(tragedy ? FlipBack : null);
            SpeedScale(tragedy ? 1f : ComedySpeed);
        }

        /// <summary>Clip event (the turn's ta-da): the other mask is on.</summary>
        public void ModJinxTurnMask()
        {
            if (!Alive) return;
            Wear(!m_tragedy);
            if (JinxFx.TaDa != null) FxFactory.SpawnOwned(JinxFx.TaDa, Me, Own);
        }

        public override float HeroHitScale(DamageInfo d) { return m_tragedy ? TragedyDamage : 1f; }
    }
}
