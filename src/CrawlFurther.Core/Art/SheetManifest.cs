using System;
using System.Collections.Generic;

namespace CrawlFurther.Art
{
    using CrawlFurther.Util;

    /// <summary>
    /// The JSON file that sits next to a sheet's PNG and describes its grid and animations.
    /// <code>
    /// {
    ///   "cellW": 32, "cellH": 32,   // size of one cell in pixels; every frame of the sheet is one cell
    ///   "cols": 8,                  // cells per row; the PNG's width is normally cols * cellW
    ///   "anims": [                  // optional
    ///     { "name": "Idle",   "frames": [0, 1, 2, 1], "durations": [0.15, 0.1, 0.15, 0.1] },
    ///     { "name": "Attack", "frames": [8, 9, 10, 11] }
    ///   ]
    /// }
    /// </code>
    /// Cells are numbered from the top-left, left to right, then down. A frame's sprite is the whole cell (no trimming),
    /// so draw every frame of an animation in the same place relative to the cell. "durations" is in seconds and may be
    /// left out (0.1 s per frame). Unknown keys are ignored, so tools may add their own.
    /// </summary>
    public class SheetManifest
    {
        /// <summary>Cell width in pixels.</summary>
        public int cellW;

        /// <summary>Cell height in pixels.</summary>
        public int cellH;

        /// <summary>Cells per row.</summary>
        public int cols;

        /// <summary>The sheet's animations (never null after <see cref="Parse"/>).</summary>
        public SheetAnim[] anims;

        /// <summary>Read a manifest from its JSON text. Throws FormatException or KeyNotFoundException on a malformed file.</summary>
        public static SheetManifest Parse(string json)
        {
            var d = (Dictionary<string, object>)MiniJson.Parse(json);
            var m = new SheetManifest
            {
                cellW = Convert.ToInt32(d["cellW"]),
                cellH = Convert.ToInt32(d["cellH"]),
                cols = Convert.ToInt32(d["cols"]),
            };
            var anims = new List<SheetAnim>();
            object ao;
            if (d.TryGetValue("anims", out ao) && ao is List<object>)
            {
                foreach (Dictionary<string, object> a in (List<object>)ao)
                {
                    var fr = (List<object>)a["frames"];
                    object du;
                    var dl = a.TryGetValue("durations", out du) && du is List<object> ? (List<object>)du : new List<object>();
                    var sa = new SheetAnim { name = (string)a["name"], frames = new int[fr.Count], durations = new float[dl.Count] };
                    for (int k = 0; k < fr.Count; k++) sa.frames[k] = Convert.ToInt32(fr[k]);
                    for (int k = 0; k < dl.Count; k++) sa.durations[k] = Convert.ToSingle(dl[k]);
                    anims.Add(sa);
                }
            }
            m.anims = anims.ToArray();
            return m;
        }
    }
}
