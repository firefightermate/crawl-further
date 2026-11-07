using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Util;

    /// <summary>
    /// The Geode, Split: at half health it cracks in two along its seam. This body becomes one half-geode with half of what
    /// was left (HalfIdle / HalfRun, its basic 1 and the HalfBurst special) and a second half (YsvGeodeHalf, a monster of
    /// its own) breaks off beside it. Halves are smaller, 1.2x faster, and their crystal insides take +25% from the hero.
    /// Tell: the seam glows from 60% health (IdleSeam / RunSeam), then the Split pose and a burst of crystal.
    /// </summary>
    public class GeodeSplit : YsveldBehaviour
    {
        public const float SeamAt = 0.6f, SplitAt = 0.5f, Speed = 1.2f, Taken = 1.25f, SplitTime = 0.48f, HitZone = 0.72f;
        public static exSpriteAnimClip SeamIdle, SeamRun, SplitClip, HalfIdle, HalfRun, HalfBurst;
        public static GameObject OtherHalf;
        bool m_seam, m_split;
        float m_splitIn;
        Transform m_hitZone;
        Vector3 m_hitScale = Vector3.one;

        protected override void OnEnable()
        {
            base.OnEnable();
            m_seam = m_split = false; m_splitIn = -1f;
            SetSpecialClip(null);
            if (m_hitZone == null) { m_hitZone = transform.Find("HitZone"); if (m_hitZone != null) m_hitScale = m_hitZone.localScale; }
            if (m_hitZone != null) m_hitZone.localScale = m_hitScale;
        }

        public override float HeroHitScale(DamageInfo d) { return m_split ? Taken : 1f; }

        void Update()
        {
            if (!Alive || Hp == null) return;
            if (m_splitIn > 0f)
            {
                m_splitIn -= Time.deltaTime;
                if (m_splitIn <= 0f) Crack();
                return;
            }
            if (m_split) return;
            float ratio = Hp.GetHealthRatio();
            if (!m_seam && ratio <= SeamAt) { m_seam = true; SetStance(SeamIdle, SeamRun); }
            if (ratio <= SplitAt && !InAttack)
            {
                m_splitIn = SplitTime;
                Hold(SplitClip, SplitTime);
            }
        }

        void Crack()
        {
            m_split = true;
            Hp.ChangeHealth(Hp.GetHealthCurrent() * 0.5f);
            Show(YsveldFx.GeodeCrack, Me);
            Spawn(OtherHalf, ModUtil.SafePoint(Me, Me + new Vector2(-14f * Side, 0f)));
            SetStance(HalfIdle, HalfRun);
            SetSpecialClip(HalfBurst);
            NextBasic(1);
            if (Frost != null) Frost.SetBaseSpeed(Speed);
            if (m_hitZone != null) m_hitZone.localScale = m_hitScale * HitZone;
        }
    }
}
