namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Monsters;

    /// <summary>The Binder's blobs. Only Gels fuse: 2 make a Brute, 3 a Titan, and a fused blob never fuses again.</summary>
    public class BlobTraits : MonsterTraits
    {
        /// <summary>A Gel, which can go into a fusion.</summary>
        public bool gel;
    }
}
