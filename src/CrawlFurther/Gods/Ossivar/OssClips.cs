namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Art;

    /// <summary>Clip-building shorthands the Ossivar kits share.</summary>
    static class OssClips
    {
        /// <summary>Aim freely through the wind-up, then lock the aim (and the controls) on <paramref name="frame"/>.</summary>
        public static ClipBuilder AimLock(this ClipBuilder c, int frame)
        {
            return c.EvF(0, "AnimInputMultiplyFreeFace", 0f).Ev(frame, "AnimInputMultiplyStop").Ev(frame, "AnimInputOff");
        }

        /// <summary>Stand still with the controls off, fire <paramref name="ev"/> (and the voice) on <paramref name="frame"/>,
        /// and hand control back at the end.</summary>
        public static ClipBuilder Channel(this ClipBuilder c, UnityEngine.Object voice, int frame, string ev)
        {
            c.Ev(0, "AnimInputOff").Ev(0, "AnimMoveStop").Ev(frame, ev);
            if (voice != null) c.EvO(frame, "AnimSound", voice);
            return c.Ev(-1, "AnimRun");
        }
    }
}
