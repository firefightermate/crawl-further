using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// A Glassmoth's glitter cloud. Glitter Echoes: an Umbrael echo that strikes inside it hits at full damage (see
    /// <see cref="UmbraelEcho"/>). Tell: the echo sparkles.
    /// </summary>
    public class GlitterFx : Registered<GlitterFx>
    {
        public const float Radius = 14f;

        /// <summary>True if <paramref name="p"/> lies inside any glitter cloud (centred on its art, 6 px up).</summary>
        public static bool Covers(Vector2 p)
        {
            for (int i = 0; i < All.Count; i++)
                if (All[i] != null && (All[i].Pos + new Vector2(0f, 6f) - p).sqrMagnitude < Radius * Radius) return true;
            return false;
        }
    }
}
