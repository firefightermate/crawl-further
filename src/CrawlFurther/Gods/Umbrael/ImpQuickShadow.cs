using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Shade Imp, Quick Shadow: in darkness its echoes come after 0.3 s instead of 0.6. Tell: the echo's claw outline is
    /// already forming where it will land as the claw strikes. Smoke Step blinks it 40 px toward the hero and leaves a puff
    /// of darkness at both ends.
    /// </summary>
    public class ImpQuickShadow : UmbraelBehaviour
    {
        public const float QuickDelay = 0.3f, StepLength = 40f;

        public override void PlanEcho(EchoPlan plan)
        {
            if (!DarknessFx.Covers(Me)) return;
            plan.delay = QuickDelay;
            if (UmbraelFx.EchoQuick != null)
                foreach (var s in plan.sites) SystemPool.Spawn(UmbraelFx.EchoQuick, s);
        }

        /// <summary>Clip event: the blink.</summary>
        public void ModUmbSmokeStep()
        {
            Vector2 from = Me;
            var to = HeroPos - from;
            float d = Mathf.Min(StepLength, Mathf.Max(0f, to.magnitude - 10f));
            if (UmbraelFx.SmokeStep != null) FxFactory.SpawnOwned(UmbraelFx.SmokeStep, from, Own);
            if (d > 1f) ModUtil.Teleport(gameObject, ModUtil.SafePoint(from, from + to.normalized * d, 4f));
            if (UmbraelFx.SmokeStep != null) FxFactory.SpawnOwned(UmbraelFx.SmokeStep, Me, Own);
            Monster.FaceHero();
        }
    }
}
