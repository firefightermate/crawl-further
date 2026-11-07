using UnityEngine;

namespace CrawlFurther.Objects
{
    /// <summary>Times the object buffs and runs their coroutines (one hidden object for the session).</summary>
    internal class BuffTicker : MonoBehaviour
    {
        static BuffTicker s_inst;
        internal static BuffTicker Inst { get { Ensure(); return s_inst; } }
        internal static void Ensure()
        {
            if (s_inst != null) return;
            var go = new GameObject("CrawlFurther_ObjectBuffs");
            UnityEngine.Object.DontDestroyOnLoad(go);
            s_inst = go.AddComponent<BuffTicker>();
        }
        void Update() { ObjectKit.TickBuffs(); }
    }
}
