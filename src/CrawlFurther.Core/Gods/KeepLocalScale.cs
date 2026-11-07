using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>Holds its transform at a set local scale (menu code that resets scales cannot undo it).</summary>
    public class KeepLocalScale : MonoBehaviour
    {
        public Vector3 scale = Vector3.one;
        void LateUpdate() { if (transform.localScale != scale) transform.localScale = scale; }
    }
}
