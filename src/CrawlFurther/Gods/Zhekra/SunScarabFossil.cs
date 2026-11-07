using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Sun Scarab, Fossil Ball: rolling, its ball picks up any larvae it touches (up to <see cref="MaxBrood"/>, wriggling
    /// inside). Release sends the ball rolling at the hero; on impact it cracks and the larvae jump out at him (they won't
    /// wither for 4 more seconds). Empty, the crack only splashes resin (roots). A new ball forms in
    /// <see cref="Regrow"/> s. Tell: the wriggling shapes in the amber (its stance).
    /// </summary>
    public class SunScarabFossil : ZhkBehaviour
    {
        public const int MaxBrood = 3;
        public const float Regrow = 3f, PickUp = 8f, BallAhead = 25f, BallY = 8f;
        /// <summary>Idle and run with 0-3 larvae in the ball, and while the ball is away (set by the kit).</summary>
        public static exSpriteAnimClip[] Idles, Runs;
        public static exSpriteAnimClip IdleEmpty, RunEmpty;

        int m_brood;
        float m_ballAt;

        protected override void OnEnable() { base.OnEnable(); m_brood = 0; m_ballAt = 0f; Stage(Idles, Runs, 0); }

        bool HasBall { get { return Time.time >= m_ballAt; } }

        Vector2 Ball { get { return Me + new Vector2(BallAhead * Side, BallY); } }

        void Update()
        {
            if (!Alive) return;
            if (!HasBall) return;
            if (m_ballAt > 0f) { m_ballAt = 0f; Stage(Idles, Runs, m_brood); }
            if (m_brood >= MaxBrood || InAttack) return;
            foreach (var b in ZhkBrain.Snapshot())
            {
                if (b == null || !b.Alive || !b.IsLarva || (b.Pos - Ball).sqrMagnitude > PickUp * PickUp) continue;
                b.SendMessage("MsgDespawn", SendMessageOptions.DontRequireReceiver);
                m_brood++;
                Stage(Idles, Runs, m_brood);
                if (m_brood >= MaxBrood) break;
            }
        }

        /// <summary>Clip event (Release): the ball rolls off at the hero.</summary>
        public void ModZhkRelease()
        {
            if (!Alive || !HasBall) return;
            var ball = ZhekraFx.FossilBall[Mathf.Clamp(m_brood, 0, MaxBrood)];
            if (ball != null) FxFactory.SpawnOwned(ball, Ball, Own, AngleTo(Ball, HeroPos + new Vector2(0f, BallY)));
            m_brood = 0;
            m_ballAt = Time.time + Regrow;
            SetStance(IdleEmpty, RunEmpty);
        }
    }
}
