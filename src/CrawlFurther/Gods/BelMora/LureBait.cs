using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Util;

    /// <summary>
    /// Lurefish, Bright Bait: each second it goes without attacking, its lure brightens one step (up to three), and its
    /// next Lure tugs the hero in from <see cref="PerStep"/> px further per step (<see cref="BaseReach"/> to 85 px).
    /// Tell: the lure grows in three sizes and throws a light cone on the floor (the Lit idles and runs).
    /// </summary>
    public class LureBait : BelBehaviour
    {
        public const float BaseReach = 40f, PerStep = 15f, Tug = 24f, StepTime = 1f;
        public const int MaxSteps = 3;
        /// <summary>The idle and run at each step, 1..3 (set by the kit).</summary>
        public static exSpriteAnimClip[] LitIdle, LitRun;

        int m_steps;
        float m_quiet;

        protected override void OnEnable() { base.OnEnable(); m_steps = 0; m_quiet = 0f; }

        void Update()
        {
            if (!Alive) return;
            if (InAttack) { m_quiet = 0f; return; }
            m_quiet += Time.deltaTime;
            if (m_steps < MaxSteps && m_quiet >= StepTime) { m_quiet = 0f; SetSteps(m_steps + 1); }
        }

        void SetSteps(int n)
        {
            m_steps = n;
            bool lit = n > 0 && LitIdle != null && LitRun != null;
            SetStance(lit ? LitIdle[n - 1] : null, lit ? LitRun[n - 1] : null);
        }

        /// <summary>Clip event (Lure, the cast): a hero within reach is tugged <see cref="Tug"/> px toward the jaws.</summary>
        public void BelLureTug()
        {
            var hero = ModUtil.Hero();
            float reach = BaseReach + PerStep * m_steps;
            SetSteps(0);
            m_quiet = 0f;
            if (hero == null || !Alive) return;
            Vector2 hp = hero.transform.position;
            if ((hp - Me).sqrMagnitude > reach * reach || !ModUtil.Clear(Me, hp)) return;
            BelWater.Drag(this, hero, Me + Face * 10f, Tug, 0.2f);
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template) { m_quiet = 0f; if (template != null) SetSteps(0); }
    }
}
