using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Amber Scarab, Rolling Stock: its resin ball grows a size every <see cref="GrowTime"/> s (three sizes). Bowling or
    /// hurling uses it up and it starts a new one from a pebble; with no ball it can only headbutt. Tell: the ball's size
    /// (its stance). Basic 0 is the headbutt, basic n bowls a size n ball; the special is the hurl of the ball it holds.
    /// </summary>
    public class ScarabStock : ZhkBehaviour
    {
        public const float GrowTime = 4f / 3f, HurlRange = 170f;
        public const int MaxSize = 3;
        /// <summary>Idle, run and hurl with a ball of size 0-3 (index 0 of Hurls is the no-ball headbutt).</summary>
        public static exSpriteAnimClip[] Idles, Runs, Hurls;

        float m_t;
        int m_size = -1;

        protected override void OnEnable() { base.OnEnable(); m_t = 0f; m_size = -1; Grow(0); }

        void Grow(int size)
        {
            if (size == m_size) return;
            m_size = size;
            Stage(Idles, Runs, size);
            NextBasic(size);
            if (Hurls != null && size < Hurls.Length) SetSpecialClip(Hurls[size]);
        }

        void Update()
        {
            if (!Alive) return;
            if (!InAttack) m_t += Time.deltaTime;
            Grow(Mathf.Min(MaxSize, (int)(m_t / GrowTime)));
        }

        /// <summary>Clip event: the ball is gone (bowled or hurled).</summary>
        public void ModZhkBallUsed() { m_t = 0f; Grow(0); }

        /// <summary>Clip event (Hurl): the ball comes down on the hero's spot.</summary>
        public void ModZhkHurl()
        {
            if (!Alive || ZhekraFx.HurlLand == null) return;
            var hp = HeroPos;
            var at = (hp - Me).sqrMagnitude <= HurlRange * HurlRange ? hp : Me + Face * 60f;
            FxFactory.SpawnOwned(ZhekraFx.HurlLand, ModUtil.SafePoint(Me, at), Own);
        }
    }
}
