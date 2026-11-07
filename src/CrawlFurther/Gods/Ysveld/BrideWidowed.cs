using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    /// <summary>
    /// Winter Bride, Widowed: when a Ysveld ally within 100 px dies, her veil turns black for 5 s. Widowed, her breath
    /// reaches twice as far (basic 1, the black breath) and every frost hit she lands adds 2 pips (her Train Sweep too).
    /// Tell: the veil going from white to black (IdleWidow / RunWidow / BreathWidow / SweepWidow) and a burst of black lace.
    /// </summary>
    public class BrideWidowed : YsveldBehaviour
    {
        public const float Reach = 100f, Time_ = 5f;
        public static exSpriteAnimClip WidowIdle, WidowRun, WidowSweep;
        float m_left;

        public override int PipsPerHit { get { return m_left > 0f ? 2 : 1; } }

        protected override void OnEnable() { base.OnEnable(); m_left = 0f; YsvMonster.Died += OnAllyDied; }

        protected override void OnDisable() { base.OnDisable(); YsvMonster.Died -= OnAllyDied; }

        void OnAllyDied(GameObject who, Vector2 at)
        {
            if (!Alive || who == gameObject || (at - Me).sqrMagnitude > Reach * Reach) return;
            if (m_left <= 0f) Show(YsveldFx.BlackVeil, Me);
            m_left = Time_;
            SetStance(WidowIdle, WidowRun);
            SetSpecialClip(WidowSweep);
            NextBasic(1);
        }

        void Update()
        {
            if (m_left <= 0f) return;
            m_left -= Time.deltaTime;
            if (m_left > 0f && Alive) return;
            m_left = 0f;
            SetStance(null, null);
            SetSpecialClip(null);
            NextBasic(0);
        }
    }
}
