namespace CrawlFurther.Heroes
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;

    /// <summary>
    /// The silver / gold "make your own" origins: what each player built for them. Set
    /// <see cref="HeroClasses.CustomHeroes"/> to provide them; without it those slots behave as plain origins.
    /// </summary>
    public interface ICustomHeroes
    {
        /// <summary>What the player's own hero in this slot grants (for the pip).</summary>
        OriginKind KindOf(int playerId, SlotTier tier);
        /// <summary>The menu portrait of the player's own hero (null: the slot's portraitArt).</summary>
        exSpriteAnimClip PortraitClip(int playerId, SlotTier tier);
        /// <summary>The origin to apply for the player's own hero.</summary>
        OriginDef Resolve(int playerId, SlotTier tier);
        /// <summary>The headwear and face sheets the in-game hero wears.</summary>
        void GearSheets(PlayerData pd, SlotTier tier, out SpriteSheet head, out SpriteSheet face);
        /// <summary>The hero's body colours; key identifies the scheme for caching.</summary>
        ColorSwap[] BodySwaps(PlayerData pd, SlotTier tier, out string key);
    }
}
