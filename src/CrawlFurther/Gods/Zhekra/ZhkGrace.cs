using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    /// <summary>A short-lived helper that, a beat after larvae are let out, gives the ones that hatched a grace period.</summary>
    public class ZhkGrace : MonoBehaviour
    {
        static ZhkGrace s_runner;

        /// <summary>After <paramref name="delay"/> s, larvae within 16 px of <paramref name="at"/> won't wither for 4 s more.</summary>
        public static void After(Vector2 at, float delay)
        {
            if (s_runner == null)
            {
                var go = new GameObject("ModZhkGrace");
                Object.DontDestroyOnLoad(go);
                s_runner = go.AddComponent<ZhkGrace>();
            }
            s_runner.StartCoroutine(s_runner.Run(at, delay));
        }

        IEnumerator Run(Vector2 at, float delay)
        {
            yield return new WaitForSeconds(delay);
            ZhkLarvaLife.ProtectAround(at, 16f, ZhkFossilFx.LarvaGrace);
        }
    }
}
