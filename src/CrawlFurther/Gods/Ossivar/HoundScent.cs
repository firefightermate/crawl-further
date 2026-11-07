using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Marrow Hound, Blood Scent: it runs <see cref="Faster"/> x as fast while the hero bleeds. Tell: a trail of red scent
    /// drops from the hero to the hound. (Its pile heal is the healOnBones trait.) The Gravetusk hunts by the same scent.
    /// </summary>
    public class HoundScent : OssBehaviour
    {
        public const float Faster = 1.2f, TrailEvery = 0.3f, TrailRange = 170f;
        float m_trail;
        bool m_on;

        protected override void OnEnable() { base.OnEnable(); m_on = false; m_trail = 0f; }

        protected virtual void Update()
        {
            bool on = Alive && HeroBleeding;
            if (on != m_on) { m_on = on; SpeedScale(on ? Faster : 1f); }
            if (!on) return;
            m_trail -= Time.deltaTime;
            if (m_trail > 0f || OssivarFx.Scent == null) return;
            m_trail = TrailEvery;
            Vector2 hero = HeroPos, d = Me - hero;
            if (d.sqrMagnitude > TrailRange * TrailRange) return;
            for (int i = 0; i < 2; i++)
                SystemPool.Spawn(OssivarFx.Scent, hero + d * Random.Range(0.15f, 0.9f) + Random.insideUnitCircle * 2f);
        }
    }
}
