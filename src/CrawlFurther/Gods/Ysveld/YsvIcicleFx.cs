using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Rime Shardling's icicle. Its shadow shows blue when it falls over ice (FallIce), and Splinter: an icicle that
    /// lands on ice bursts into three shards that skid along the ice (<see cref="YsvSkidFx"/>).
    /// </summary>
    public class YsvIcicleFx : MonoBehaviour
    {
        /// <summary>On the falling mark: true plays the blue-shadow fall.</summary>
        public bool mark;
        bool m_done;

        void OnEnable() { m_done = false; }

        void Update()
        {
            if (m_done) return;
            m_done = true;
            Vector2 at = transform.position;
            if (YsvFloor.Count == 0 || !YsvFloor.Covers(at)) return;
            if (mark) { YsvUtil.Play(gameObject, YsveldFx.IcicleIceClip); return; }
            if (YsveldFx.SkidShard == null) return;
            var src = FxFactory.SourceOf(gameObject);
            float start = Random.Range(0f, 120f);
            for (int i = 0; i < 3; i++) FxFactory.SpawnOwned(YsveldFx.SkidShard, at + new Vector2(0f, 2f), src, start + i * 120f);
        }
    }
}
