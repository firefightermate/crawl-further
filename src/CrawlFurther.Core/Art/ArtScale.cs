using System.Collections.Generic;

namespace CrawlFurther.Art
{
    /// <summary>
    /// Sheets drawn smaller than the units their monster kit was written in. MonsterFactory multiplies a monster's kit
    /// offsets (attack spawn points, hitbox positions) by its sheet's factor, so a sheet can be redrawn at a new size
    /// without rewriting the kit. Sheets without an entry use 1.
    /// </summary>
    public static class ArtScale
    {
        /// <summary>Linear factor by sheet id (0.75 = the art is three quarters of the kit's size). Fill it before your packs register.</summary>
        public static readonly Dictionary<string, float> BySheet = new Dictionary<string, float>();

        /// <summary>The factor for <paramref name="sheet"/>, or 1 when it has none.</summary>
        public static float Of(string sheet)
        {
            float k;
            return sheet != null && BySheet.TryGetValue(sheet, out k) ? k : 1f;
        }
    }
}
