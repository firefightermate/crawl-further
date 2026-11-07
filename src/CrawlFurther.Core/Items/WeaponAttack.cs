using System.Collections.Generic;

namespace CrawlFurther.Items
{
    /// <summary>One hero attack: a vanilla attack of the base weapon, re-timed and pointed at this weapon's effects.</summary>
    public class WeaponAttack
    {
        /// <summary>Index into the base weapon's attacks (its hero clip and angle clips).</summary>
        public int src;
        /// <summary>Frame-time multiplier; the clip's events move with their frames.</summary>
        public float scale = 1f;
        /// <summary>Seconds after this attack before the next.</summary>
        public float cooldown;
        /// <summary>"a{id}" = vanilla AnimAttack(id), "m{tag}" = vanilla AnimMagic(tag) -> an index into the weapon's
        /// effects (-1 drops it). Unmapped events are dropped.</summary>
        public Dictionary<string, int> map = new Dictionary<string, int>();

        /// <param name="pairs">Event key and effect index pairs: "a1", 0, "mprj", 1.</param>
        public WeaponAttack(int src, float cooldown, float scale, params object[] pairs)
        {
            this.src = src; this.cooldown = cooldown; this.scale = scale;
            for (int i = 0; i + 1 < pairs.Length; i += 2) map[(string)pairs[i]] = (int)pairs[i + 1];
        }
    }
}
