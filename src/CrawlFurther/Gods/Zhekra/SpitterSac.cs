using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Acid Spitter, Acid Sac: the sac on its back fills a stage every <see cref="StageTime"/> s (three stages). A full sac
    /// makes the next glob burst into a pool twice as wide (basic 1, LobFull) and empties it. A hit from the hero on a full
    /// sac bursts it on the Spitter: 1 damage to it and an acid splash round it. Tell: the sac's size and glow (its stance).
    /// </summary>
    public class SpitterSac : ZhkBehaviour
    {
        public const float StageTime = 2f, BurstDamage = 1f;
        public const int Full = 3;
        /// <summary>Idle and run with the sac at 0-3 (set by the kit).</summary>
        public static exSpriteAnimClip[] Idles, Runs;

        float m_t;
        int m_stage;

        protected override void OnEnable() { base.OnEnable(); m_t = 0f; m_stage = -1; Show(0); }

        void Show(int stage)
        {
            if (stage == m_stage) return;
            m_stage = stage;
            Stage(Idles, Runs, stage);
            NextBasic(stage >= Full ? 1 : 0);
        }

        void Update()
        {
            if (!Alive) return;
            m_t += Time.deltaTime;
            Show(Mathf.Min(Full, (int)(m_t / StageTime)));
        }

        /// <summary>Clip event (LobFull's release): the sac pumped out.</summary>
        public void ModZhkSacEmpty() { m_t = 0f; Show(0); }

        public override void OnHeroHit(DamageInfo d)
        {
            if (m_stage < Full) return;
            m_t = 0f; Show(0);
            if (ZhekraFx.SacBurst != null) FxFactory.SpawnOwned(ZhekraFx.SacBurst, Me, Own);
            StartCoroutine(Hurt());
        }

        IEnumerator Hurt()
        {
            yield return null;   // after the hero's own hit
            if (Alive) Hp.DamageNoSource(BurstDamage);
        }
    }
}
