using CrawlFurther.Monsters;

namespace ExampleGod
{
    /// <summary>
    /// The Glimmer Grub's quirk. A clip event calls the method of its name on every component of the body, so the
    /// grub's Rise clip sends EvF(frame, "GlimmerHeal", 0.5f) and this method runs. Listed in the grub's traits with
    /// <c>new MonsterTraits().Add&lt;GlimmerGlow&gt;()</c>; Core adds it to every grub that spawns.
    /// </summary>
    public class GlimmerGlow : MonsterBehaviour
    {
        /// <summary>Clip event: heal <paramref name="amount"/> and show the heal burst.</summary>
        void GlimmerHeal(float amount)
        {
            if (Monster != null && Monster.Alive) Monster.Heal(amount);
        }
    }
}
