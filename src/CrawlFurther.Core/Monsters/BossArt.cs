namespace CrawlFurther.Monsters
{
    /// <summary>
    /// New pixel art for a vanilla boss atlas, loaded by <see cref="BossFactory.LoadArt"/>. Every redrawn element keeps
    /// its vanilla element index, original cell and pivot (the trim inside the cell may grow a few px). The mod atlas has
    /// one element per vanilla element; only the redrawn ones are valid, and only frames whose element was redrawn are
    /// pointed at it (everything else stays on the vanilla atlas).
    /// </summary>
    public sealed class BossArt
    {
        /// <summary>The art sheet id (art/&lt;sheet&gt;.png + .json).</summary>
        public string sheet;
        /// <summary>The vanilla atlas it redraws.</summary>
        public string vanillaName;
        /// <summary>The mod atlas, parallel to the vanilla one.</summary>
        public exAtlas atlas;
        /// <summary>Per vanilla element: was it redrawn.</summary>
        public bool[] has;
        /// <summary>How many elements were redrawn.</summary>
        public int count;

        /// <summary>True if frame <paramref name="index"/> of <paramref name="a"/> was redrawn here.</summary>
        public bool Has(exAtlas a, int index)
        {
            return a != null && a.name == vanillaName && index >= 0 && index < has.Length && has[index];
        }
    }
}
