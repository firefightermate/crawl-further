using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// One-Armed Bandit, Jackpot and Tilt. Its three reels each pay one symbol: cherry heals 1, bell drops a confetti bomb
    /// on the hero, skull drops a knife on the hero, seven fires three coins; three alike adds a ring of ten coins.
    /// Tilt: hit it while the reels spin (the SPIN lamp is lit) and they jam on three skulls: the knives fall on the bandit
    /// instead, and it stands jammed for <see cref="JamTime"/> s.
    /// </summary>
    public class BanditReels : JinxBehaviour
    {
        public const float JamTime = 1.0f, ReelGap = 0.15f;
        public const int RingCoins = 10;
        /// <summary>The jammed loop (set by the kit).</summary>
        public static exSpriteAnimClip JamClip;

        bool m_spinning;
        float m_spinSince;

        protected override void OnEnable() { base.OnEnable(); m_spinning = false; }

        /// <summary>Clip event: the lever is pulled, the reels spin.</summary>
        public void ModJinxReelsSpin() { m_spinning = true; m_spinSince = Time.time; }

        public override void OnHeroHit(DamageInfo d)
        {
            if (!m_spinning || Time.time - m_spinSince > 1.2f) { m_spinning = false; return; }
            m_spinning = false;
            Vector2 top = Me + new Vector2(0f, 30f);
            if (JinxFx.Reels != null && JinxFx.Reels[2] != null)
                for (int i = 0; i < 3; i++) SystemPool.Spawn(JinxFx.Reels[2], top + new Vector2((i - 1) * 10f, 0f));
            var hero = ModUtil.HeroSource();
            if (JinxFx.KnifeRain != null && hero != null)
                foreach (var o in new[] { new Vector2(-6f, 2f), new Vector2(6f, -1f), Vector2.zero })
                    FxFactory.SpawnOwned(JinxFx.KnifeRain, Me + o, hero);
            StartCoroutine(Jam());
        }

        IEnumerator Jam()
        {
            yield return null;    // after the hit's knockback has started
            Hold(JamClip, JamTime);
        }

        /// <summary>Clip event: the reels stop and pay out.</summary>
        public void ModJinxJackpot()
        {
            if (!m_spinning) return;
            m_spinning = false;
            StartCoroutine(Pay());
        }

        IEnumerator Pay()
        {
            var r = new int[3];
            for (int i = 0; i < 3; i++) r[i] = Random.Range(0, 4);
            Vector2 top = Me + new Vector2(0f, 30f);
            for (int i = 0; i < 3; i++)
            {
                if (!Alive) yield break;
                if (JinxFx.Reels != null && JinxFx.Reels[r[i]] != null) SystemPool.Spawn(JinxFx.Reels[r[i]], top + new Vector2((i - 1) * 10f, 0f));
                PayOne(r[i]);
                yield return new WaitForSeconds(ReelGap);
            }
            if (r[0] == r[1] && r[1] == r[2] && Alive && JinxFx.Coin != null)
            {
                if (JinxFx.Confetti != null) SystemPool.Spawn(JinxFx.Confetti, Me);
                float s = Random.Range(0f, 36f);
                for (int k = 0; k < RingCoins; k++) FxFactory.SpawnOwned(JinxFx.Coin, Me + new Vector2(0f, 10f), Own, s + k * 360f / RingCoins);
            }
        }

        void PayOne(int sym)
        {
            Vector2 hero = HeroPos;
            switch (sym)
            {
                case 0: if (Hp != null) { Hp.Heal(1f); ModInd.Heal(gameObject); } break;
                case 1: if (JinxFx.ConfettiPop != null) FxFactory.SpawnOwned(JinxFx.ConfettiPop, hero, Own); break;
                case 2: if (JinxFx.KnifeRain != null) FxFactory.SpawnOwned(JinxFx.KnifeRain, hero, Own); break;
                default:
                    if (JinxFx.Coin == null) break;
                    Vector2 from = Me + new Vector2(13f * Side, 12f);
                    float a = AngleTo(from, hero + new Vector2(0f, 8f));
                    for (int k = -1; k <= 1; k++) FxFactory.SpawnOwned(JinxFx.Coin, from, Own, a + k * 10f);
                    break;
            }
        }
    }
}
