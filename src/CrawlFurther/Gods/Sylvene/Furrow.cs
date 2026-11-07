using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// The Sower's furrows: the seeds of one Strafe, joined by a thin vine (the tell). They ripen together (each one
    /// starts again when the pass ends) and burst together (<see cref="Orchard.BurstFurrow"/>).
    /// </summary>
    public static class Furrow
    {
        const float VineStep = 12f;

        static readonly Dictionary<int, List<SeedFx>> s_rows = new Dictionary<int, List<SeedFx>>();
        static readonly Dictionary<int, List<GameObject>> s_vines = new Dictionary<int, List<GameObject>>();

        /// <summary>Add a seed to a furrow and grow the vine to it from the last one.</summary>
        public static void Add(int id, SeedFx seed)
        {
            if (seed == null || id == 0) return;
            seed.furrow = id;
            List<SeedFx> row;
            if (!s_rows.TryGetValue(id, out row)) s_rows[id] = row = new List<SeedFx>();
            row.RemoveAll(s => s == null || !s.isActiveAndEnabled || s.furrow != id);
            if (row.Count > 0) Lay(id, row[row.Count - 1].Pos, seed.Pos);
            row.Add(seed);
        }

        /// <summary>The pass is over: the furrow's seeds start ripening together.</summary>
        public static void Close(int id) { Orchard.RipenTogether(id); }

        /// <summary>The furrow burst (or its pods rotted away): the vine goes.</summary>
        public static void Wither(int id)
        {
            List<GameObject> vines;
            if (s_vines.TryGetValue(id, out vines))
                foreach (var v in vines) if (v != null && v.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(v);
            s_vines.Remove(id);
            s_rows.Remove(id);
        }

        static void Lay(int id, Vector2 a, Vector2 b)
        {
            if (SylveneFx.FurrowVine == null) return;
            var d = b - a;
            float len = d.magnitude;
            if (len < 2f || len > 60f) return;
            float ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
            List<GameObject> vines;
            if (!s_vines.TryGetValue(id, out vines)) s_vines[id] = vines = new List<GameObject>();
            int n = Mathf.Max(1, Mathf.RoundToInt(len / VineStep));
            for (int i = 0; i < n; i++)
            {
                var go = FxFactory.SpawnOwned(SylveneFx.FurrowVine, a + d * ((i + 0.5f) / n), null, ang);
                if (go != null) vines.Add(go);
            }
        }
    }
}
