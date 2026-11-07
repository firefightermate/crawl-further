using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Church Grim, Undying: once per life, a hit that would kill it drops it into a heap of bones with lit eyes instead.
    /// <see cref="Wait"/> s later it rises with <see cref="RiseHealth"/> health, unless the hero stands on the heap in that
    /// time: then it is gone for good. Ossivar can't eat this heap (it is the Grim itself). Tell: the lantern eyes in the
    /// heap and a ring round it that fills.
    /// </summary>
    public class GrimUndying : OssBehaviour
    {
        public const float Wait = 3f, RiseHealth = 3f, StandOn = 9f;
        /// <summary>Set by the kit.</summary>
        public static exSpriteAnimClip FallClip, HeapClip, RiseClip;
        bool m_used, m_down;
        GameObject m_ring;

        protected override void OnEnable() { base.OnEnable(); m_used = false; m_down = false; }

        protected override void OnDisable()
        {
            base.OnDisable();
            if (Hp != null) Hp.StopInvincibility("ossgrim");
            DropRing();
            m_down = false;
        }

        void DropRing()
        {
            if (m_ring != null && m_ring.activeInHierarchy) SystemPool.Despawn(m_ring);
            m_ring = null;
        }

        public override void BeforeDamage(DamageInfo d)
        {
            if (m_used || m_down || Hp == null || d.m_amount < Hp.GetHealthCurrent()) return;
            m_used = true;
            d.m_amount = Mathf.Max(0f, Hp.GetHealthCurrent() - 0.05f);
            d.m_knockbackMultiplier = 0f;
            StartCoroutine(Undying());
        }

        IEnumerator Undying()
        {
            m_down = true;
            yield return null;   // let the hit finish landing first
            if (Hp == null || !Hp.IsAlive()) { m_down = false; yield break; }
            Hp.StartInvincibility("ossgrim");
            Hold(FallClip, Wait + 0.6f);
            if (OssivarFx.GrimRing != null) m_ring = SystemPool.Spawn(OssivarFx.GrimRing, Me);
            float t = 0f;
            bool heap = false;
            while (t < Wait)
            {
                t += Time.deltaTime;
                if (!heap && t > 0.45f) { heap = true; Play(HeapClip); }
                if (Hero != null && (HeroPos - Me).sqrMagnitude < StandOn * StandOn)
                {
                    DropRing();
                    Hp.StopInvincibility("ossgrim");
                    m_down = false;
                    Hp.InstaKill(new DamageInfo(99f, 0f, 0f, Vector2.up, ModUtil.HeroSource()));
                    yield break;
                }
                yield return null;
            }
            DropRing();
            Play(RiseClip);
            yield return new WaitForSeconds(0.5f);
            Hp.StopInvincibility("ossgrim");
            float lack = RiseHealth - Hp.GetHealthCurrent();
            if (lack > 0f) Monster.Heal(lack);
            m_down = false;
        }
    }
}
