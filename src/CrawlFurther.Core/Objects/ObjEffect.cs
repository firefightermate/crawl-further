using UnityEngine;

namespace CrawlFurther.Objects
{
    /// <summary>One effect a trap attack spawns.</summary>
    public class ObjEffect
    {
        /// <summary>The effect template (from FxKit or FxFactory).</summary>
        public GameObject fx;
        /// <summary>Frame of the attack anim it spawns on.</summary>
        public int frame;
        /// <summary>Offset from the trap's attack node in pixels (y up), turned with the aim.</summary>
        public float x, y;
        /// <summary>Extra angle in degrees (fans).</summary>
        public float angle;
        /// <summary>Follows the trap after it spawns.</summary>
        public bool attach;
        /// <summary>Extra delay before it spawns, in seconds.</summary>
        public float delay;
    }
}
