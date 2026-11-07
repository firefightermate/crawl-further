using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Bone Mammoth. Earthshaker: every footfall jolts the floor round that foot (<see cref="JoltDamage"/> to a hero within
    /// <see cref="JoltRange"/> px, at most once a second; tell: a dust ring under the foot). Cross Quake: after rearing it
    /// stamps, cracks run out in a cross, 60 px each way, and bone spikes burst along them 0.4 s later.
    /// </summary>
    public class MammothQuake : OssBehaviour
    {
        public const float JoltRange = 14f, JoltDamage = 0.3f, Arm = 60f, Seg = 12f, SpikeDelay = 0.4f;
        float m_lastJolt;

        protected override void OnEnable() { base.OnEnable(); m_lastJolt = -9f; }

        /// <summary>Clip event (Run frames 0 and 3).</summary>
        public void OssFootfall()
        {
            if (!Alive) return;
            Vector2 foot = Me + new Vector2(Side * 7f, 0f);
            if (OssivarFx.StepDust != null) SystemPool.Spawn(OssivarFx.StepDust, foot);
            if (Time.time - m_lastJolt < 1f || Hero == null) return;
            if ((HeroPos - foot).sqrMagnitude > JoltRange * JoltRange) return;
            m_lastJolt = Time.time;
            HurtHero(JoltDamage, 0.3f);
        }

        /// <summary>Clip event (Quake frame 4): the stamp.</summary>
        public void OssCrossQuake() { if (Alive) StartCoroutine(Cross()); }

        IEnumerator Cross()
        {
            Vector2 me = Me;
            var src = Own;
            var dirs = new[] { Vector2.right, Vector2.left, Vector2.up, Vector2.down };
            int n = Mathf.RoundToInt(Arm / Seg);
            var reach = new int[4];
            for (int k = 0; k < n; k++)
            {
                for (int a = 0; a < 4; a++)
                {
                    if (reach[a] < k) continue;
                    Vector2 at = me + dirs[a] * (Seg * (k + 0.5f) + 4f);
                    if (!ModUtil.Clear(me, at)) continue;
                    reach[a] = k + 1;
                    if (OssivarFx.Crack != null)
                        FxFactory.SpawnOwned(OssivarFx.Crack, at, src, Mathf.Atan2(dirs[a].y, dirs[a].x) * Mathf.Rad2Deg);
                }
                yield return new WaitForSeconds(0.03f);
            }
            yield return new WaitForSeconds(SpikeDelay - 0.03f * n);
            for (int k = 0; k < n; k++)
            {
                for (int a = 0; a < 4; a++)
                    if (k < reach[a] && OssivarFx.CrossSpike != null)
                        FxFactory.SpawnOwned(OssivarFx.CrossSpike, me + dirs[a] * (Seg * (k + 0.5f) + 4f), src);
                yield return new WaitForSeconds(0.04f);
            }
        }
    }
}
