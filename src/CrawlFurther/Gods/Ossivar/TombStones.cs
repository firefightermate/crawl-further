using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Tombwright. Raise Stones: three headstones rise in a line toward the hero, <see cref="Gap"/> px apart, each hitting
    /// whoever stands where it comes up, and stand as walls (<see cref="OssHeadstoneFx"/>). Domino: the mallet knocks over a
    /// headstone it hits; a falling stone topples the next one in its path. Tell: cracks spreading at the base first.
    /// </summary>
    public class TombStones : OssBehaviour
    {
        public const float Gap = 14f, Reach = 90f, KnockRange = 16f;

        /// <summary>Clip event (Raise frame 4).</summary>
        public void OssRaiseStones() { if (Alive) StartCoroutine(Raise()); }

        IEnumerator Raise()
        {
            Vector2 me = Me, d = HeroPos - me;
            if (Hero == null || d.sqrMagnitude < 1f) d = Face * 50f;
            float dist = Mathf.Clamp(d.magnitude, Gap + 12f, Reach);
            Vector2 dir = d.normalized;
            var src = Own;
            for (int i = -1; i <= 1; i++)
            {
                if (!Alive) yield break;
                Vector2 want = me + dir * (dist + i * Gap);
                Vector2 at = ModUtil.SafePoint(me, want, 8f);
                if ((at - want).sqrMagnitude < 4f)
                {
                    if (OssivarFx.StoneRise != null) FxFactory.SpawnOwned(OssivarFx.StoneRise, at, src);
                    var go = OssivarFx.Headstone != null ? SystemPool.Spawn(OssivarFx.Headstone, at) : null;
                    if (go != null) (go.GetComponent<OssHeadstoneFx>() ?? go.AddComponent<OssHeadstoneFx>()).Begin(src);
                }
                yield return new WaitForSeconds(0.08f);
            }
        }

        /// <summary>Clip event (Mallet frame 3): knock over any headstone the mallet head lands on.</summary>
        public void OssMalletKnock()
        {
            Vector2 head = Me + Face * 14f;
            foreach (var s in OssHeadstoneFx.Snapshot())
                if (s != null && s.Standing && (s.Pos - head).sqrMagnitude < KnockRange * KnockRange)
                    s.Topple(s.Pos - Me, Own);
        }
    }
}
