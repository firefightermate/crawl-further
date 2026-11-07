using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Briar Champion, Growing Lance: each hit its lance lands grows it <see cref="Step"/> px (up to <see cref="MaxGrown"/>
    /// lengths) and each hit it takes from the hero trims it back one. Tell: the lance's length and its fresh green tips
    /// (a stance per length), and the trimmed tip falling.
    /// </summary>
    public class ChampionLance : SylveneBehaviour
    {
        public const int MaxGrown = 3;
        public const float Base = 20f, Step = 6f;
        /// <summary>Per length: the idle, run and lunge clips (index 0 is the body's own; set by the kit).</summary>
        public static readonly exSpriteAnimClip[] Idle = new exSpriteAnimClip[4], Run = new exSpriteAnimClip[4], Lunge = new exSpriteAnimClip[4];

        int m_grown;

        /// <summary>The lance's reach past the hand at <paramref name="grown"/> lengths.</summary>
        public static float LanceLength(int grown) { return Base + Step * grown; }

        protected override void OnEnable() { base.OnEnable(); m_grown = 0; Apply(); }

        void Update()
        {
            // the basic thrust and the lunge always match the lance it holds now
            if (Alive && !InAttack) { NextBasic(m_grown); SetSpecialClip(m_grown == 0 ? null : Lunge[m_grown]); }
        }

        protected override void OnHitHero(DamageInfo d)
        {
            var n = Dealt(d);
            if ((n.StartsWith("ModSylLance") || n.StartsWith("ModSylLunge")) && m_grown < MaxGrown) { m_grown++; Apply(); }
        }

        public override void OnHeroHit(DamageInfo d)
        {
            if (m_grown <= 0) return;
            m_grown--;
            if (SylveneFx.LanceTrim != null) SystemPool.Spawn(SylveneFx.LanceTrim, Me + new Vector2((10f + LanceLength(m_grown)) * Side, 14f));
            Apply();
        }

        void Apply()
        {
            SetStance(m_grown == 0 ? null : Idle[m_grown], m_grown == 0 ? null : Run[m_grown]);
        }
    }
}
