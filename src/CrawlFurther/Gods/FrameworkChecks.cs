using System;

namespace CrawlFurther.Content.Gods
{
    using CrawlFurther.Gods;
    using CrawlFurther.Heroes;
    using CrawlFurther.UI;
    using CrawlFurther.Content.Ghosts;
    using CrawlFurther.Content.Heroes;

    /// <summary>Self-test of the silver / gold slots: slot art, unlocks, custom gods and the order of the origin and ghost lists.</summary>
    public static class FrameworkChecks
    {
        public static void SelfCheck(Action<string> bad)
        {
            SlotArt.SelfCheck(bad);
            if (SlotArt.Clip("DeitySilverIdol", "Idle") == null || SlotArt.Clip("DeityGoldIdol", "Idle") == null) bad("slot art missing: DeitySilverIdol / DeityGoldIdol");
            if (SlotArt.Clip("DeitySilverIdol", "Locked") == null || SlotArt.Clip("DeityGoldIdol", "Locked") == null) bad("slot art: idol Locked anims");
            UnlockHooks.SelfCheck(bad);
            CustomGod.SelfCheck(bad);
            if (SlotEditors.God == null) SlotEditors.God = CustomGodEditor.For;
            int hero = SlotCompat.HeroRegular, ghost = SlotCompat.GhostRegular;
            // the silver and gold entries must be the last two of their lists
            for (int i = 0; i < HeroClasses.All.Count; i++)
            {
                var t = HeroClasses.All[i].tier;
                if (t != SlotTier.Normal && i < HeroClasses.All.Count - 2) bad("origin list: " + t + " slot at " + i + " is not one of the last two");
                if (t == SlotTier.Normal && i >= hero) bad("origin list: a normal origin after the silver / gold slots");
            }
            for (int i = 0; i < GhostPack.Forms.Count; i++)
            {
                var t = SlotCompat.GhostTier(GhostPack.Forms[i]);
                if (t != SlotTier.Normal && i < GhostPack.Forms.Count - 2) bad("ghost list: " + t + " slot at " + i + " is not one of the last two");
                if (t == SlotTier.Normal && i >= ghost) bad("ghost list: a normal form after the silver / gold slots");
            }
            if (SlotArt.Clip("ModSpellPip", "Idle") == null || SlotArt.Clip("ModBothPip", "Idle") == null) bad("origin spell / both pips missing");
        }
    }
}
