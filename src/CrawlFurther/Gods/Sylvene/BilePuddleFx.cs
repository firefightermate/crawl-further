using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Util;

    /// <summary>A Bloatfly's bile puddle: a hero standing in it is spoiled (<see cref="Spoiled"/>) while he stays.</summary>
    public class BilePuddleFx : MonoBehaviour
    {
        public const float Life = 4f;
        const float HalfW = 9f, HalfH = 4f;

        void Update()
        {
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 d = (Vector2)hero.transform.position - (Vector2)transform.position;
            if ((d.x * d.x) / (HalfW * HalfW) + (d.y * d.y) / (HalfH * HalfH) <= 1f) Spoiled.Mark(hero);
        }
    }
}
