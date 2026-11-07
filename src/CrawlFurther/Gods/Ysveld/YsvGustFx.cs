using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>The Hoarmoth's gust. Sleet Gust: while the hero stands on ice the gust turns white with snow (the Sleet
    /// clip), and a hero it catches on ice is shoved a second time, so the ice carries him twice as far.</summary>
    public class YsvGustFx : MonoBehaviour
    {
        public const float Shove = 180f;
        bool m_sleet;

        void OnEnable() { m_sleet = false; }

        void Update()
        {
            var hero = ModUtil.Hero();
            bool sleet = hero != null && YsvFloor.Count > 0 && YsvFloor.Covers(hero.transform.position);
            if (sleet == m_sleet) return;
            m_sleet = sleet;
            YsvUtil.Play(gameObject, sleet ? YsveldFx.GustSleetClip : YsveldFx.GustClip);
        }

        void MsgOnAttackContact(DamageInfo d)
        {
            var hero = ModUtil.Hero();
            if (d == null || hero == null || d.m_victim != hero) return;
            var slide = hero.GetComponent<YsvSlide>();
            if (slide == null || !slide.OnIce) return;
            var mv = GetComponent<ParticleMotion>();
            var dir = mv != null && mv.GetVelocity().sqrMagnitude > 1f ? mv.GetVelocity() : d.m_direction;
            slide.Glide(dir, Shove);
        }
    }
}
