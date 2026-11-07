using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// A component that keeps a live list of its enabled instances, for things monsters look for on the floor (puddles,
    /// piles, pools). Derive as <c>class Puddle : Registered&lt;Puddle&gt;</c> and query <see cref="All"/> or
    /// <see cref="Nearest"/>. Pool-safe: an instance leaves the list when it is disabled or destroyed.
    /// </summary>
    public abstract class Registered<T> : MonoBehaviour where T : Registered<T>
    {
        /// <summary>Every enabled instance. May hold destroyed entries for a frame; check for null.</summary>
        public static readonly List<T> All = new List<T>();

        protected virtual void OnEnable() { if (!All.Contains((T)this)) All.Add((T)this); }
        protected virtual void OnDisable() { All.Remove((T)this); }
        protected virtual void OnDestroy() { All.Remove((T)this); }

        /// <summary>The instance's position (pixels).</summary>
        public Vector2 Pos { get { return transform.position; } }

        /// <summary>The instance nearest <paramref name="p"/> within <paramref name="maxDist"/> pixels that passes
        /// <paramref name="filter"/>, or null.</summary>
        public static T Nearest(Vector2 p, float maxDist = 9999f, System.Predicate<T> filter = null)
        {
            T best = null; float bd = maxDist * maxDist;
            for (int i = 0; i < All.Count; i++)
            {
                var w = All[i];
                if (w == null || (filter != null && !filter(w))) continue;
                float d = (w.Pos - p).sqrMagnitude;
                if (d < bd) { bd = d; best = w; }
            }
            return best;
        }

        /// <summary>A copy of <see cref="All"/> without destroyed entries, safe to iterate while instances despawn.</summary>
        public static List<T> Snapshot() { All.RemoveAll(x => x == null); return new List<T>(All); }
    }
}
