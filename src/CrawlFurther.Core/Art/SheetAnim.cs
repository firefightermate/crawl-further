namespace CrawlFurther.Art
{
    /// <summary>One named animation of a <see cref="SpriteSheet"/>: cell indices and how long each is shown.</summary>
    public class SheetAnim
    {
        /// <summary>The animation's name, unique within its sheet (lookups ignore case).</summary>
        public string name;

        /// <summary>Cell indices, in play order. Cells count left to right, then top to bottom, from 0.</summary>
        public int[] frames;

        /// <summary>Seconds each frame is shown, parallel to <see cref="frames"/>. Missing entries default to 0.1.</summary>
        public float[] durations;
    }
}
