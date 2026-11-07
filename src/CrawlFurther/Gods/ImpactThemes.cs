namespace CrawlFurther.Content.Gods
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Each god's impact puff (art/out_common/FxCommonImpact&lt;key&gt;) and the effect sheet prefixes drawn for that god,
    /// god-prefixed ids first, then the older un-prefixed ids each pack drew. Ghost forms and blobs keep the neutral puff.
    /// </summary>
    public static class ImpactThemes
    {
        public static void Register()
        {
            ImpactFx.AddTheme("Vh", "FxCommonImpactVh", "Vh", "Ash", "Candle", "Cinder", "Ember", "Lantern", "Wax", "Wick", "Tallow", "Moth", "Soul");
            ImpactFx.AddTheme("Bel", "FxCommonImpactBel", "Bel", "Bell", "Brine", "Cannon", "Coral", "Hook", "Peal", "SongNote", "Spine", "Splash",
                              "Tentacle", "WaterBolt", "Wave", "Whirlpool", "Anchor", "Tide");
            ImpactFx.AddTheme("Oss", "FxCommonImpactOss", "Oss", "Bone", "Halo", "Marrow", "Saint", "Skull", "SpikeRing", "Grave");
            ImpactFx.AddTheme("Syl", "FxCommonImpactSyl", "Syl", "EggSac", "Gall", "Maggot", "Poison", "Pollen", "Root", "Seed", "Spore", "Thorn", "Briar");
            ImpactFx.AddTheme("Umb", "FxCommonImpactUmb", "Umb", "Darkness", "Decoy", "Echo", "Mirror", "Reflect", "Shadow", "Swap");
            ImpactFx.AddTheme("Jinx", "FxCommonImpactJinx", "Jinx", "Card", "Coin", "Confetti", "Die", "Dice", "FateMark", "FireRing", "Hoop",
                              "JuggleBall", "KnifeRain", "Orb", "Reel", "Tarot", "Wheel", "WildCard");
            ImpactFx.AddTheme("Zhk", "FxCommonImpactZhk", "Zhk");
            ImpactFx.AddTheme("Krn", "FxCommonImpactKrn", "Krn");
            ImpactFx.AddTheme("Ysv", "FxCommonImpactYsv", "Ysv");
            ImpactFx.AddTheme("Wpn", "FxCommonImpactWpn", "Wpn");
        }
    }
}
