using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Charnel Rider. Unhorsed: at <see cref="FallAt"/> health the horse falls apart into three bone piles and the rider fights
    /// on foot: the sweep becomes a lance throw, the joust a short running thrust, and its hurtbox shrinks to the rider. Tell:
    /// from <see cref="CrackAt"/> health the horse cracks and limps. The joust gallops straight until a wall (or its full
    /// 110 px) and wheels round to face the hero.
    /// </summary>
    public class RiderUnhorse : OssBehaviour
    {
        public const float CrackAt = 7f, FallAt = 5f, FootW = 12f, FootH = 26f;
        /// <summary>Set by the kit.</summary>
        public static exSpriteAnimClip CrackIdle, CrackRun, UnhorseClip, FootIdle, FootRun, FootThrust, FootDeath;

        bool m_cracked, m_foot, m_jousting;
        BoxCollider m_hurt;
        Vector3 m_hurtSize, m_hurtCentre;

        protected override void OnEnable()
        {
            base.OnEnable();
            m_cracked = false; m_foot = false; m_jousting = false;
            if (m_hurt == null)
            {
                var c = ModUtil.Hurtbox(gameObject) as BoxCollider;
                if (c != null) { m_hurt = c; m_hurtSize = c.size; m_hurtCentre = c.center; }
            }
            else { m_hurt.size = m_hurtSize; m_hurt.center = m_hurtCentre; }
        }

        void Update()
        {
            if (!Alive || Hp == null) return;
            float hp = Hp.GetHealthCurrent();
            if (!m_cracked && !m_foot && hp <= CrackAt) { m_cracked = true; SetStance(CrackIdle, CrackRun); }
            if (!m_foot && hp <= FallAt && !InAttack) Unhorse();
            if (m_jousting)
            {
                if (!InAttack) { m_jousting = false; return; }
                if (!ModUtil.Clear(Me, Me + Face * 20f) && Move != null) { Move.AnimMoveStop(); m_jousting = false; }
            }
        }

        void Unhorse()
        {
            m_foot = true;
            Hold(UnhorseClip, 0.8f);
            float s = Side;
            foreach (var dx in new[] { -12f, -4f, 9f }) OssFloor.DropPile(Me, Me + new Vector2(dx * s, -1f), Own);
            SetStance(FootIdle, FootRun);
            SetSpecialClip(FootThrust);
            SetDeathClip(FootDeath);
            NextBasic(1);
            if (m_hurt != null) { m_hurt.size = new Vector3(FootW, FootH, m_hurtSize.z); m_hurt.center = new Vector3(0f, FootH * 0.5f, m_hurtCentre.z); }
        }

        /// <summary>Clip event (Joust frame 3).</summary>
        public void OssJoustOn() { m_jousting = true; }

        /// <summary>Clip event (Joust frame 9): stop and wheel round.</summary>
        public void OssJoustOff() { m_jousting = false; Monster.FaceHero(); }
    }
}
