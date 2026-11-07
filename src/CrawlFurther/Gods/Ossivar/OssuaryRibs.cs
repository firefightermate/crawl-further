using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Ossuary. Ribcage: the floor cracks round the hero for <see cref="Crack"/> s, then six huge ribs burst up round him
    /// (<see cref="OssRibFx"/>) and curve in over him for 2.5 s. He can't walk out; shots pass between them; one hit breaks a
    /// rib. Charnel Wall (its traits): it holds up to 3 plates, so it can stand by the cage and soak his way out.
    /// </summary>
    public class OssuaryRibs : OssBehaviour
    {
        public const float Crack = 0.4f, Reach = 130f, Rx = 22f, Ry = 16f;
        public const int Ribs = 6;

        /// <summary>Clip event (Rib frame 2): the floor cracks under the hero.</summary>
        public void OssRibCrack()
        {
            if (!Alive || Hero == null) return;
            Vector2 at = HeroPos;
            if ((at - Me).sqrMagnitude > Reach * Reach || !ModUtil.Clear(Me, at)) return;
            if (OssivarFx.RibCrack != null) SystemPool.Spawn(OssivarFx.RibCrack, at);
            StartCoroutine(Cage(at));
        }

        IEnumerator Cage(Vector2 at)
        {
            yield return new WaitForSeconds(Crack);
            if (!Alive || OssivarFx.Rib == null) yield break;
            for (int i = 0; i < Ribs; i++)
            {
                float a = i * 360f / Ribs;
                Vector2 spot = at + new Vector2(Mathf.Cos(a * Mathf.Deg2Rad) * Rx, Mathf.Sin(a * Mathf.Deg2Rad) * Ry);
                if (ModUtil.SafePoint(at, spot, 2f) != spot || OssFloor.Occupied(spot, 4f, 3f)) continue;
                var go = SystemPool.Spawn(OssivarFx.Rib, spot);
                if (go != null) (go.GetComponent<OssRibFx>() ?? go.AddComponent<OssRibFx>()).Begin(spot.x < at.x - 1f, a + 90f);
            }
        }
    }
}
