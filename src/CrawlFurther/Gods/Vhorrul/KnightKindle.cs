namespace CrawlFurther.Content.Gods.Vhorrul
{
    /// <summary>
    /// Waxen Knight, Kindled Armour: walking through fire sets its wax coat burning for 5 s (the Kindled status: flames
    /// running up the armour, +25 % damage taken). Kindled, its cuts burn and the third spills burning wax; Sealing
    /// while it burns throws the ring out lit (it burns and lights wax) and puts the knight out.
    /// </summary>
    public class KnightKindle : VhorrulBehaviour
    {
        public const float TouchRange = 8f;
        /// <summary>Effect slots, set by the kit: the wax spill, the burning spill, the Seal ring, the lit ring.</summary>
        public static int SpillSlot = -1, BurnSpillSlot = -1, RingSlot = -1, LitRingSlot = -1;
        float m_t;

        bool Kindled { get { return HasStatus(VhorrulFx.Kindled); } }

        void Update()
        {
            m_t -= UnityEngine.Time.deltaTime;
            if (m_t > 0f || !Alive) return;
            m_t = 0.1f;
            if (!Kindled && FireNear(TouchRange) != null) AddStatus(VhorrulFx.Kindled, "vhkindled");
        }

        /// <summary>Clip event (the overhead): spill wax, burning while Kindled.</summary>
        public void VhKnightSpill() { Attack(Kindled ? BurnSpillSlot : SpillSlot); }

        /// <summary>Clip event (Seal cracks): the ring, thrown out lit while Kindled (which puts the knight out).</summary>
        public void VhKnightRing()
        {
            if (Kindled) { Attack(LitRingSlot); RemoveStatus(VhorrulFx.Kindled); }
            else Attack(RingSlot);
        }

        public override void OnHitHero(DamageInfo d)
        {
            if (Kindled && (From(d, VhorrulFx.KnightCut) || From(d, VhorrulFx.KnightCut3))) d.m_status = VhorrulFx.OnFire;
        }
    }
}
