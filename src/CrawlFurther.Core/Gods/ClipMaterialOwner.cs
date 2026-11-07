using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>Destroys the clip materials of the clip planes under its object along with the object (copied menu
    /// buttons and boxes own theirs).</summary>
    public class ClipMaterialOwner : MonoBehaviour
    {
        void OnDestroy() { BoxView.DestroyClipMaterials(gameObject); }
    }
}
