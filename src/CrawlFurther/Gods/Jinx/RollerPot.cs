using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// High Roller, Double or Nothing. Every flicked chip that hits the hero raises his stake by one (up to
    /// <see cref="MaxStake"/>; FxJinxStake over his fedora shows it). All In shoves the chips into a pot on the floor that
    /// ticks for <see cref="PotTime"/> s, then bursts into a fan of 2 + stake chips at the hero. Hit him while the pot is
    /// down and he busts: hat off, dazed <see cref="BustTime"/> s, the pot pays nothing and the stake is lost.
    /// </summary>
    public class RollerPot : JinxBehaviour
    {
        public const int MaxStake = 6, BaseChips = 2;
        public const float PotTime = 2.5f, BustTime = 1.5f, FanStep = 9f;
        /// <summary>The bust (set by the kit).</summary>
        public static exSpriteAnimClip BustClip;

        int m_stake;
        JinxPotFx m_pot;

        protected override void OnEnable() { base.OnEnable(); m_stake = 0; m_pot = null; StartCoroutine(ShowLater()); }

        IEnumerator ShowLater() { yield return null; Show(); }

        void Show()
        {
            if (JinxFx.Stake != null) ModInd.Count(gameObject, JinxFx.Stake, Alive ? m_stake + 1 : 0);
        }

        /// <summary>A flicked chip hit the hero (the game tells the attacker).</summary>
        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_source == null || d.m_source.m_source == null || !Alive) return;
            if (d.m_victim == null || d.m_victim != CrawlFurther.Util.ModUtil.Hero()) return;
            if (d.m_source.m_source.GetComponent<JinxChipTag>() == null || m_stake >= MaxStake) return;
            m_stake++;
            Show();
        }

        /// <summary>Clip event: the pot goes down in front of him.</summary>
        public void ModJinxAllIn()
        {
            if (!Alive || JinxFx.Pot == null) return;
            if (m_pot != null) m_pot.Bust();
            var go = FxFactory.SpawnOwned(JinxFx.Pot, CrawlFurther.Util.ModUtil.SafePoint(Me, Me + new Vector2(18f * Side, 0f), 3f), Own);
            m_pot = go != null ? go.GetComponent<JinxPotFx>() : null;
            if (m_pot != null) m_pot.Bind(this, PotTime);
        }

        /// <summary>The pot ticked out: the chips fly at the hero and the stake is spent.</summary>
        public void PotPaid(JinxPotFx pot)
        {
            if (pot != m_pot) return;
            m_pot = null;
            if (!Alive || JinxFx.ChipSpray == null) return;
            Vector2 from = (Vector2)pot.transform.position + new Vector2(0f, 4f);
            int n = BaseChips + m_stake;
            float a = AngleTo(from, HeroPos + new Vector2(0f, 6f));
            for (int k = 0; k < n; k++) FxFactory.SpawnOwned(JinxFx.ChipSpray, from, Own, a + (k - (n - 1) * 0.5f) * FanStep);
            m_stake = 0;
            Show();
        }

        public override void OnHeroHit(DamageInfo d)
        {
            if (m_pot == null) return;
            var pot = m_pot;
            m_pot = null;
            pot.Bust();
            m_stake = 0;
            Show();
            StartCoroutine(Bust());
        }

        IEnumerator Bust()
        {
            yield return null;    // after the hit's own knockback has started
            Hold(BustClip, BustTime);
        }

        protected override void OnDisable()
        {
            base.OnDisable();
            if (m_pot != null) m_pot.Bust();
            m_pot = null;
        }
    }
}
