using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Content.Gods;
    using CrawlFurther.Util;

    /// <summary>A blizzard gust: slides across the room with the wind at 330 px/s while its loop plays.</summary>
    public class YsvGaleFx : MonoBehaviour
    {
        public const float Speed = 330f;
        public float wind = 1f;
        public void Arm() { wind = 1f; }
        void Update()
        {
            var p = transform.position;
            transform.position = new Vector3(p.x + wind * Speed * Time.deltaTime, p.y, p.z);
        }
    }
}
