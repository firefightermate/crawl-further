using System.Collections.Generic;

namespace CrawlFurther.Objects
{
    /// <summary>One trap attack: an anim of the trap's sheet and the effects it spawns.</summary>
    public class ObjTrapAttack
    {
        public string anim = "Action";
        /// <summary>Seconds after this attack before the next.</summary>
        public float cooldown = 1f;
        public List<ObjEffect> effects = new List<ObjEffect>();
    }
}
