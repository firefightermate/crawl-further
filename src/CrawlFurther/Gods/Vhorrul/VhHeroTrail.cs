using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Util;

    /// <summary>The hero's footsteps, recorded while any Fuse Scorpion spark runs (a point every <see cref="Step"/> px).</summary>
    public class VhHeroTrail : MonoBehaviour
    {
        public const float Step = 3f;
        public readonly List<Vector2> points = new List<Vector2>();
        /// <summary>Index of points[0] since recording began, so a spark keeps its place when old points are dropped.</summary>
        public int baseIndex;
        int m_users;

        public static VhHeroTrail On(GameObject hero)
        {
            if (hero == null) return null;
            return hero.GetComponent<VhHeroTrail>() ?? hero.AddComponent<VhHeroTrail>();
        }

        public int Begin() { if (m_users++ == 0) { points.Clear(); baseIndex = 0; points.Add(transform.position); } return baseIndex + points.Count - 1; }
        public void End() { m_users = Mathf.Max(0, m_users - 1); }

        /// <summary>The recorded point at absolute index <paramref name="i"/> (clamped to what is kept).</summary>
        public Vector2 At(int i) { return points.Count == 0 ? (Vector2)transform.position : points[Mathf.Clamp(i - baseIndex, 0, points.Count - 1)]; }
        public int Last { get { return baseIndex + points.Count - 1; } }

        void Update()
        {
            if (m_users <= 0) return;
            Vector2 p = transform.position;
            if (points.Count == 0 || (p - points[points.Count - 1]).sqrMagnitude >= Step * Step) points.Add(p);
            if (points.Count > 600) { points.RemoveRange(0, 100); baseIndex += 100; }
        }
    }
}
