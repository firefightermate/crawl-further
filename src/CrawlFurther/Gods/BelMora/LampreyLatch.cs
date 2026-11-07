using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Brine Lamprey. Its Undercurrent Lunge hits <see cref="WetHit"/> times as hard if it passed through brine. Latch: a
    /// lunge that lands latches on: for <see cref="Length"/> s it hangs on the hero's side, moving with him, then rasps once
    /// more. A dodge (a burst of speed) or one hit from the hero shakes it off. Tell: the lamprey stuck to his side, its
    /// tail thrashing (Latched).
    /// </summary>
    public class LampreyLatch : BelBehaviour
    {
        public const float WetHit = 1.5f, Length = 1f, Side = 7f, DodgeSpeed = 150f;
        /// <summary>The latched loop (set by the kit).</summary>
        public static exSpriteAnimClip LatchedClip;

        bool m_wet, m_lunging;
        float m_latched;
        GameObject m_hero;
        Vector2 m_heroLast;

        protected override void OnEnable() { base.OnEnable(); m_wet = false; m_lunging = false; m_latched = 0f; m_hero = null; }
        protected override void OnDisable() { base.OnDisable(); m_latched = 0f; }

        /// <summary>Clip event: the lunge starts (brine it crosses from here on powers it up).</summary>
        public void BelLungeOn() { m_lunging = true; m_wet = BelWater.InBrine(Feet); }
        /// <summary>Clip event: the lunge ends.</summary>
        public void BelLungeOff() { m_lunging = false; }

        public override float HitOnHeroScale(DamageInfo d) { return HitFrom(d, BelMoraFx.LampreyLunge) && m_wet ? WetHit : 1f; }

        public override void OnHitHero(DamageInfo d)
        {
            if (!HitFrom(d, BelMoraFx.LampreyLunge) || m_latched > 0f) return;
            m_hero = ModUtil.Hero();
            if (m_hero == null) return;
            m_heroLast = m_hero.transform.position;
            m_latched = Length;
            Hold(LatchedClip, Length + 0.1f);
        }

        public override void OnHeroHit(DamageInfo d) { if (m_latched > 0f) Release(false); }

        void Update()
        {
            if (!Alive) return;
            if (m_lunging && !m_wet && BelWater.InBrine(Feet)) m_wet = true;
            if (m_latched <= 0f) return;
            if (m_hero == null || !m_hero.activeInHierarchy) { Release(false); return; }
            Vector2 hp = m_hero.transform.position;
            float speed = (hp - m_heroLast).magnitude / Mathf.Max(0.001f, Time.deltaTime);
            m_heroLast = hp;
            if (speed > DodgeSpeed) { Release(false); return; }
            float side = Me.x <= hp.x ? -1f : 1f;
            ModUtil.Teleport(gameObject, ModUtil.SafePoint(hp, hp + new Vector2(side * Side, 0f), 1f));
            Monster.Face(hp);
            m_latched -= Time.deltaTime;
            if (m_latched <= 0f) Release(true);
        }

        void Release(bool rasp)
        {
            m_latched = 0f;
            if (rasp && m_hero != null && BelMoraFx.LampreyRasp != null) FxFactory.SpawnOwned(BelMoraFx.LampreyRasp, m_hero.transform.position, Own);
            if (Body != null && Alive) Body.Stun(0f, true);
            if (!rasp && Alive) Shift(-ToHero() * 10f);
        }
    }
}
