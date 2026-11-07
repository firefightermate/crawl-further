using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Unblinking, The Eye Opens: Lights Out shuts its eye under a darkness of r 90 for 3.5 s (every Umbrael monster
    /// in it is hidden). When the dark ends a flash rings out (r 90): a hero moving inside it is dazed; a hero standing
    /// still is not. Tell: the lid cracks open with light for 0.5 s first.
    /// </summary>
    public class UnblinkingEye : UmbraelBehaviour
    {
        public const float Dark = 3.5f, Warn = 0.5f, Radius = 90f;
        /// <summary>The shut eye and the cracking lid (set by the kit).</summary>
        public static exSpriteAnimClip ShutClip, CrackClip;

        /// <summary>Clip event: the eye is shut.</summary>
        public void ModUmbLightsOut() { StopCoroutine("LightsOut"); StartCoroutine("LightsOut"); }

        IEnumerator LightsOut()
        {
            Vector2 at = Me;
            if (UmbraelFx.Blackout != null) FxFactory.SpawnOwned(UmbraelFx.Blackout, at, Own);
            Hold(ShutClip, Dark - Warn);
            yield return new WaitForSeconds(Dark - Warn);
            if (!Alive) yield break;
            Hold(CrackClip, Warn);
            yield return new WaitForSeconds(Warn);
            if (!Alive) yield break;
            if (UmbraelFx.EyeFlash != null) SystemPool.Spawn(UmbraelFx.EyeFlash, at);
            var hero = ModUtil.Hero();
            if (hero == null || ((Vector2)hero.transform.position - at).sqrMagnitude > Radius * Radius) yield break;
            var rb = hero.GetComponent<Rigidbody>();
            bool moving = rb != null && rb.velocity.sqrMagnitude > 25f;
            var hp = hero.GetComponent<Player>();
            if (moving && hp != null && ModStatus.Daze != null) hp.AddStatus(ModStatus.Daze, Own, "umbeyeopens");
        }
    }
}
