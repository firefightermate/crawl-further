using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Blood Gorger, Blood Bank and Transfuse: each drill that lands stores a stage in its sac (three). Hits from the hero on
    /// a full sac do <see cref="FullDamage"/>x and spill it. Transfuse plunges its proboscis into the nearest Zhekra within
    /// <see cref="PumpRange"/> px and pumps: the ally heals <see cref="PerStage"/> a stage and frenzies. Tell: the sac's
    /// level (its stance) and a line of blood beads to the ally while it pumps.
    /// </summary>
    public class GorgerBank : ZhkBehaviour
    {
        public const int Full = 3;
        public const float FullDamage = 1.5f, PumpRange = 60f, PerStage = 0.8f, PumpTime = 0.6f;
        /// <summary>Idle and run with the sac at 0-3 (set by the kit).</summary>
        public static exSpriteAnimClip[] Idles, Runs;

        int m_stage;

        protected override void OnEnable() { base.OnEnable(); Fill(0); }

        void Fill(int n) { m_stage = Mathf.Clamp(n, 0, Full); Stage(Idles, Runs, m_stage); }

        protected override void OnHeroContact(DamageInfo d, string effect) { if (effect == "ModZhkDrill") Fill(m_stage + 1); }

        public override float HeroHitScale(DamageInfo d) { return m_stage >= Full ? FullDamage : 1f; }

        public override void OnHeroHit(DamageInfo d)
        {
            if (m_stage < Full) return;
            Fill(0);
            if (ZhekraFx.Mend != null) SystemPool.Spawn(ZhekraFx.Mend, Me + new Vector2(-4f * Side, 14f));
        }

        /// <summary>Clip event (Pump): the transfusion.</summary>
        public void ModZhkTransfuse()
        {
            if (!Alive) return;
            ZhkBrain pick = null; float best = PumpRange * PumpRange;
            foreach (var k in Kin(Me, PumpRange))
            {
                float d = (k.Pos - Me).sqrMagnitude;
                if (d < best) { best = d; pick = k; }
            }
            if (pick == null) return;
            Monster.Face(pick.Pos);
            float heal = PerStage * m_stage;
            Fill(0);
            StartCoroutine(Pump(pick, heal));
        }

        IEnumerator Pump(ZhkBrain to, float heal)
        {
            float bead = 0f;
            for (float t = 0f; t < PumpTime; t += Time.deltaTime)
            {
                if (!Alive || to == null || !to.Alive) yield break;
                bead -= Time.deltaTime;
                if (bead <= 0f && ZhekraFx.PumpBead != null)
                {
                    bead = 0.05f;
                    SystemPool.Spawn(ZhekraFx.PumpBead, Vector2.Lerp(Me + new Vector2(18f * Side, 12f), to.Pos + new Vector2(0f, 8f), (t * 4f) % 1f));
                }
                yield return null;
            }
            if (to == null || !to.Alive) yield break;
            if (heal > 0f) to.Mend(heal);
            to.Frenzy(Own);
        }
    }
}
