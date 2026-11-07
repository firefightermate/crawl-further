using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Rot Mother, The Orchard Feeds Her: every pod that bursts on the hero, anywhere in the room, heals her
    /// <see cref="Heal"/>. Tell: the pod's husk drifts to her as a green wisp, and the buds on her hair open (Feed).
    /// </summary>
    public class MotherFeed : SylveneBehaviour
    {
        public const float Heal = 0.5f;
        /// <summary>The buds opening (set by the kit).</summary>
        public static exSpriteAnimClip FeedClip;

        static readonly List<MotherFeed> s_live = new List<MotherFeed>();

        protected override void OnEnable() { base.OnEnable(); if (!s_live.Contains(this)) s_live.Add(this); }

        protected override void OnDisable() { base.OnDisable(); s_live.Remove(this); }

        /// <summary>A pod burst on the hero at <paramref name="at"/>: feed every Rot Mother alive.</summary>
        public static void Fed(Vector2 at)
        {
            for (int i = s_live.Count - 1; i >= 0; i--)
            {
                var m = s_live[i];
                if (m == null || !m.Alive) continue;
                m.Monster.Heal(Heal);
                ModInd.Heal(m.gameObject);
                m.Flourish(FeedClip);
                var w = SylveneFx.Wisp != null ? SystemPool.Spawn(SylveneFx.Wisp, at + new Vector2(0f, 4f)) : null;
                var fx = w != null ? w.GetComponent<WispFx>() : null;
                if (fx != null) fx.Seek(m.transform);
            }
        }
    }
}
