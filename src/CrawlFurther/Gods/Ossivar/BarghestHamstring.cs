using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Barghest. Hamstring: a bite while the hero's back is turned to it hits +50 % and slows him for a second (tell: its
    /// eyes flare over its head while it is behind him). Pounce leaps (untouchable) and lands <see cref="Past"/> px past
    /// the hero, facing him, so the next bite comes from behind.
    /// </summary>
    public class BarghestHamstring : OssBehaviour
    {
        public const float Past = 20f, Reach = 90f, Bonus = 1.5f, AirTime = 0.24f;
        bool m_behind;
        float m_check;

        protected override void OnEnable() { base.OnEnable(); m_behind = false; m_check = 0f; }
        protected override void OnDisable() { base.OnDisable(); if (OssivarFx.EyeFlare != null) ModInd.Set(gameObject, OssivarFx.EyeFlare, false); }

        /// <summary>True while the hero faces away from it.</summary>
        bool Behind()
        {
            var h = Hero;
            var mv = h != null ? h.GetComponent<PlayerMovement>() : null;
            if (mv == null) return false;
            Vector2 to = Me - (Vector2)h.transform.position;
            if (to.sqrMagnitude > 60f * 60f) return false;
            var f = mv.GetFaceDirection();
            return f.sqrMagnitude > 0.01f && Vector2.Dot(f.normalized, to.normalized) < -0.2f;
        }

        void Update()
        {
            m_check -= Time.deltaTime;
            if (m_check > 0f) return;
            m_check = 0.1f;
            bool b = Alive && Behind();
            if (b == m_behind) return;
            m_behind = b;
            if (OssivarFx.EyeFlare != null) ModInd.Set(gameObject, OssivarFx.EyeFlare, b);
        }

        public override float HitHeroScale(DamageInfo d) { return From(d, OssivarFx.BarghestBite) && Behind() ? Bonus : 1f; }

        public override void OnHitHero(DamageInfo d)
        {
            if (!From(d, OssivarFx.BarghestBite) || !Behind()) return;
            var hp = Hero != null ? Hero.GetComponent<Player>() : null;
            if (hp != null && ModStatus.Slow != null) hp.AddStatus(ModStatus.Slow, Own, "osshamstring");
        }

        /// <summary>Clip event (Pounce frame 2): the leap.</summary>
        public void OssPounce() { if (Alive) StartCoroutine(Leap()); }

        IEnumerator Leap()
        {
            Vector2 start = Me, hero = HeroPos, d = hero - start;
            if (d.sqrMagnitude > Reach * Reach) d = d.normalized * Reach;
            Vector2 dir = d.sqrMagnitude > 0.01f ? d.normalized : Face;
            Vector2 end = ModUtil.SafePoint(start, start + d + dir * Past, 6f);
            for (float t = 0f; t < 1f; t += Time.deltaTime / AirTime)
            {
                if (!Alive) yield break;
                ModUtil.Teleport(gameObject, Vector2.Lerp(start, end, t));
                yield return null;
            }
            ModUtil.Teleport(gameObject, end);
            Monster.FaceHero();
        }
    }
}
