using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Random-outcome projectiles: on spawn a card picks a curse, a die rolls its damage.</summary>
    public class ChanceFx : RollSource
    {
        /// <summary>The curses a card can carry: fire, poison, frost, daze (in that order).</summary>
        public static Status[] Curses;
        public bool randomCurse, randomDamage;
        /// <summary>Damage per pip of a rolled die.</summary>
        public float baseDamage = 0.35f;

        void OnEnable()
        {
            var d = GetComponent<DamageEffect>();
            if (d == null) return;
            if (randomCurse && Curses != null && Curses.Length > 0)
            {
                var st = Curses[Random.Range(0, Curses.Length)];
                R.Set(d, "m_status", st);
                R.Set(d, "m_statusChance", 1f);
                R.Set(d, "m_statusFinal", st);          // hits read the *Final copies made in Awake
                R.Set(d, "m_statusChanceFinal", 1f);
            }
            if (randomDamage)
            {
                lastRoll = Random.Range(1, 7);
                R.Set(d, "m_damage", baseDamage * lastRoll);
                var spr = GetComponent<exSprite>();
                if (spr != null) spr.color = Color.Lerp(Color.white, new Color(1f, 0.55f, 0.4f), (lastRoll - 1) / 5f);
            }
        }
    }
}
