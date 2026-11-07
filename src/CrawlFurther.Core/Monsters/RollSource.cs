using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// Base for an effect component that rolls a number each time it spawns (a thrown die). A <see cref="RollReadout"/>
    /// with <see cref="RollReadout.fromSource"/> on the same object shows the roll when the effect hits.
    /// </summary>
    public abstract class RollSource : MonoBehaviour
    {
        /// <summary>The number rolled for the current spawn (0: nothing rolled).</summary>
        public int lastRoll;
    }
}
