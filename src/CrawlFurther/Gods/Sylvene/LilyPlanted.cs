using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Carrion Lily, Planted: standing still for <see cref="Settle"/> s it roots, heals <see cref="Regen"/> a second and
    /// its lunge reaches 40 px instead of 24 (basic 1 instead of 0). Moving uproots it; it walks at 0.75x. Tell: its roots
    /// dug into the floor, or dangling.
    /// </summary>
    public class LilyPlanted : SylveneBehaviour
    {
        public const float Settle = 1f, Regen = 0.3f;
        /// <summary>The planted idle and the dig (set by the kit).</summary>
        public static exSpriteAnimClip PlantedIdle, PlantClip;

        float m_still, m_healBank;
        bool m_planted;

        protected override void OnEnable() { base.OnEnable(); m_still = 0f; m_healBank = 0f; Uproot(); }

        void Update()
        {
            if (!Alive) { if (m_planted) Uproot(); return; }
            bool moving = Move != null && Move.GetVelocity().sqrMagnitude > 4f;
            if (moving) { m_still = 0f; if (m_planted) Uproot(); }
            else if (!m_planted)
            {
                m_still += Time.deltaTime;
                if (m_still >= Settle && !InAttack) Plant();
            }
            if (!m_planted) return;
            m_healBank += Regen * Time.deltaTime;
            if (m_healBank >= 0.15f) { Monster.Heal(m_healBank); m_healBank = 0f; }
            if (!InAttack) NextBasic(1);
        }

        void Plant()
        {
            m_planted = true;
            SetStance(PlantedIdle, null);
            Flourish(PlantClip);
            ModInd.Regen(gameObject, true);
            NextBasic(1);
        }

        void Uproot()
        {
            m_planted = false;
            SetStance(null, null);
            ModInd.Regen(gameObject, false);
            NextBasic(0);
        }
    }
}
