using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Hourglass, Turned Over: Rewind marks its spot and health; 2.5 s later it snaps back to both (health only if it was
    /// higher), and the echoes it has pending at that moment fire at the marked spot. Tell: a sand ghost of it on the mark,
    /// its sand running out.
    /// </summary>
    public class HourglassRewind : UmbraelBehaviour
    {
        public const float Delay = 2.5f;
        /// <summary>The flip it plays when it snaps back (set by the kit).</summary>
        public static exSpriteAnimClip SnapClip;

        /// <summary>Clip event: mark the spot.</summary>
        public void ModUmbRewindMark()
        {
            if (Hp == null) return;
            if (UmbraelFx.RewindMark != null) SystemPool.Spawn(UmbraelFx.RewindMark, Me);
            StopCoroutine("Rewind");
            StartCoroutine("Rewind", new Vector3(Me.x, Me.y, Hp.GetHealthCurrent()));
        }

        IEnumerator Rewind(Vector3 mark)
        {
            yield return new WaitForSeconds(Delay);
            if (!Alive) yield break;
            Vector2 back = mark, from = Me;
            if (UmbraelFx.RewindSnap != null) SystemPool.Spawn(UmbraelFx.RewindSnap, from);
            UmbraelEcho.Rewind(Monster, back - from);
            ModUtil.Teleport(gameObject, ModUtil.SafePoint(from, back, 3f));
            if (UmbraelFx.RewindSnap != null) SystemPool.Spawn(UmbraelFx.RewindSnap, Me);
            float lost = mark.z - Hp.GetHealthCurrent();
            if (lost > 0.01f) Monster.Heal(lost);
            Flourish(SnapClip);
        }
    }
}
