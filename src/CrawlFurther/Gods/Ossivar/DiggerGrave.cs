using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Gravedigger. Shallow Grave: two spade hits within <see cref="Window"/> seconds bury the hero to the knees (Buried:
    /// 40 % slower for 1.5 s; tell: a dirt mound round his legs). Unearth digs two bone piles out of the floor near it.
    /// </summary>
    public class DiggerGrave : OssBehaviour
    {
        public const float Window = 2f, DigMin = 12f, DigMax = 30f;
        float m_lastHit;

        protected override void OnEnable() { base.OnEnable(); m_lastHit = -9f; }

        public override void OnHitHero(DamageInfo d)
        {
            if (!From(d, OssivarFx.DigSpade)) return;
            if (Time.time - m_lastHit <= Window)
            {
                m_lastHit = -9f;
                var hp = Hero != null ? Hero.GetComponent<Player>() : null;
                if (hp != null && OssivarFx.Buried != null) hp.AddStatus(OssivarFx.Buried, Own, "ossburied");
            }
            else m_lastHit = Time.time;
        }

        /// <summary>Clip event (Unearth frame 5): two piles come up out of the floor.</summary>
        public void OssUnearth()
        {
            if (!Alive) return;
            float a0 = Random.Range(0f, 360f);
            for (int i = 0; i < 2; i++)
            {
                Vector2 at = Me + Dir(a0 + 140f * i + Random.Range(-30f, 30f)) * Random.Range(DigMin, DigMax);
                var pile = OssFloor.DropPile(Me, at, Own);
                if (pile != null && OssivarFx.DigHole != null) SystemPool.Spawn(OssivarFx.DigHole, pile.Pos);
            }
        }
    }
}
