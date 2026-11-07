using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Storm Herald's Eye of the Storm: it blows its horn, and for <see cref="Duration"/> s lightning strikes at random
    /// <see cref="Inner"/>..<see cref="Outer"/> px round it, <see cref="PerSecond"/> a second (1.0 each). Calm Centre: nothing
    /// strikes within 50 px of it. A ring of storm-cloud shadow on the floor (half depth, like every floor circle) marks the
    /// band and follows it.
    /// </summary>
    public class HeraldStorm : KaurnBehaviour
    {
        public const float Duration = 3f, Inner = 60f, Outer = 110f, PerSecond = 4f, Depth = 0.5f;
        GameObject m_band;

        protected override void OnDisable() { base.OnDisable(); DropBand(); }

        void DropBand()
        {
            if (m_band != null && m_band.activeInHierarchy) SystemPool.Despawn(m_band);
            m_band = null;
        }

        /// <summary>Clip event: the horn sounds.</summary>
        public void KrnStorm() { StopAllCoroutines(); DropBand(); StartCoroutine(Storm()); }

        IEnumerator Storm()
        {
            if (KaurnFx.StormBand != null) m_band = SystemPool.Spawn(KaurnFx.StormBand, Me);
            float t = 0f, next = 0f;
            while (t < Duration && Alive)
            {
                t += Time.deltaTime;
                if (m_band != null) m_band.transform.position = new Vector3(Me.x, Me.y, m_band.transform.position.z);
                next -= Time.deltaTime;
                if (next <= 0f)
                {
                    next = 1f / PerSecond;
                    float a = Random.Range(0f, Mathf.PI * 2f), r = Random.Range(Inner, Outer);
                    var to = Me + new Vector2(Mathf.Cos(a), Mathf.Sin(a) * Depth) * r;
                    if (ModUtil.Clear(Me, to) && KaurnFx.StormBolt != null) FxFactory.SpawnOwned(KaurnFx.StormBolt, to, Own);
                }
                yield return null;
            }
            DropBand();
        }
    }
}
