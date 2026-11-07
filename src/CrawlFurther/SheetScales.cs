namespace CrawlFurther.Content
{
    using CrawlFurther.Art;

    /// <summary>
    /// How much smaller each re-rendered sheet was drawn than its kit's units (see <see cref="ArtScale"/>). Generated from
    /// the SCALE tables in tools/sprites/*_rigs.py. Sheets drawn at their final size (every redrawn god's) have no entry.
    /// </summary>
    static class SheetScales
    {
        public static void Register()
        {
            var s = ArtScale.BySheet;
            // ghost_rigs.py
            s["BlobMote"] = 0.92f; s["BlobSpitter"] = 0.8f; s["BlobGel"] = 0.8f; s["BlobBrute"] = 0.57f;
            s["BlobTitan"] = 0.58f; s["BlobKing"] = 0.5f;
        }
    }
}
