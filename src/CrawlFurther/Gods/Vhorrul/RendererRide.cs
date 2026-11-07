namespace CrawlFurther.Content.Gods.Vhorrul
{
    /// <summary>
    /// Tallow Renderer, Surf the Boil: Boil Over tips the cauldron and it rides the front of its own wave the whole way,
    /// unmoved by knockback, then swings the ladle at the end (all in the clip; this keeps it planted).
    /// </summary>
    public class RendererRide : VhorrulBehaviour
    {
        bool m_riding;

        protected override void OnEnable() { base.OnEnable(); m_riding = false; }

        /// <summary>Clip event: the ride begins (no knockback).</summary>
        public void VhRide() { m_riding = true; }

        /// <summary>Clip event: off the wave.</summary>
        public void VhRideEnd() { m_riding = false; }

        public override void OnHeroHit(DamageInfo d) { if (m_riding) d.m_knockbackMultiplier = 0f; }
    }
}
