namespace CrawlFurther.Content.Heroes
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Heroes;

    /// <summary>Core's view of the silver / gold custom heroes (<see cref="HeroCustom"/>).</summary>
    public class CustomHeroSlots : ICustomHeroes
    {
        public OriginKind KindOf(int playerId, SlotTier tier) { return HeroCustom.KindOf(HeroCustom.Get(playerId, tier), tier); }
        public exSpriteAnimClip PortraitClip(int playerId, SlotTier tier) { return HeroCustom.PortraitClip(playerId, tier); }
        public OriginDef Resolve(int playerId, SlotTier tier) { return HeroCustom.Resolve(playerId, tier); }
        public void GearSheets(PlayerData pd, SlotTier tier, out SpriteSheet head, out SpriteSheet face) { HeroCustom.GearSheets(pd, tier, out head, out face); }
        public ColorSwap[] BodySwaps(PlayerData pd, SlotTier tier, out string key) { return HeroCustom.BodySwaps(pd, tier, out key); }
    }
}
