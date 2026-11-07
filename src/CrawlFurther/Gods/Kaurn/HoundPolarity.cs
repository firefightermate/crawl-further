using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Util;

    /// <summary>
    /// Lodestone Hound's Polarity: its collar flips after each howl. A red collar's howl drags the hero toward it, a blue
    /// collar's shoves him away (about 40 px either way). The collar shows on every pose (the Blue stance and moves).
    /// </summary>
    public class HoundPolarity : KaurnBehaviour
    {
        public const float Reach = 130f;
        public static exSpriteAnimClip BlueIdle, BlueRun, BlueHowl;
        bool m_blue, m_applied;

        protected override void OnEnable() { base.OnEnable(); m_blue = false; m_applied = false; }

        void Update() { if (!m_applied && !InAttack) Apply(); }

        void Apply()
        {
            m_applied = true;
            SetStance(m_blue ? BlueIdle : null, m_blue ? BlueRun : null);
            SetSpecialClip(m_blue ? BlueHowl : null);
            NextBasic(m_blue ? 1 : 0);
        }

        /// <summary>Clip event, once per howl frame: one tug of the field (in on red, out on blue).</summary>
        public void KrnMagField(float strength)
        {
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 hp = hero.transform.position;
            var d = hp - Me;
            if (d.sqrMagnitude > Reach * Reach) return;
            if (!m_blue) ModUtil.Pull(hero, Me, strength);
            else ModUtil.Pull(hero, hp + (d.sqrMagnitude > 0.01f ? d.normalized : Vector2.right) * 60f, strength);
        }

        /// <summary>Clip event at the end of the howl: the collar flips.</summary>
        public void KrnFlipCollar() { m_blue = !m_blue; m_applied = false; }
    }
}
