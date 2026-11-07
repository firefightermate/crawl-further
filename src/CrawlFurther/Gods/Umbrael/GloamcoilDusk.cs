using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    /// <summary>
    /// Gloamcoil, Spreading Dusk: darkness it lies in grows 4 px a second, up to a radius of 30. Tell: the pool's edge
    /// creeping outward (<see cref="DarknessFx.Grow"/> draws it).
    /// </summary>
    public class GloamcoilDusk : UmbraelBehaviour
    {
        public const float Rate = 4f, Max = 30f;

        void Update()
        {
            if (!Alive) return;
            var d = DarknessFx.At(Me);
            if (d != null) d.Grow(Rate * Time.deltaTime, Max);
        }
    }
}
