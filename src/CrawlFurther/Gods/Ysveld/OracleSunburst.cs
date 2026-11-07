using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    /// <summary>
    /// Prism Oracle, Sunburst (her special, the YsvSunburst clip event): the prism flares for 0.6 s, then every ice slab
    /// within 80 px of her flashes in turn, nearest first, 0.15 s apart; a hero standing on a slab as it flashes takes 1.0
    /// and a pip. With fewer than two slabs near her, her light first freezes three short-lived slabs in a line toward the
    /// hero. Ice Lens (her bolts bending over ice) lives on the bolt (<see cref="YsvLensFx"/>).
    /// </summary>
    public class OracleSunburst : YsveldBehaviour
    {
        public const float Reach = 80f, Flare = 0.6f, Gap = 0.15f, Damage = 1.0f, SeedLife = 4f;

        public void YsvSunburst()
        {
            if (!Alive) return;
            StopAllCoroutines();
            StartCoroutine(Burst());
        }

        IEnumerator Burst()
        {
            var slabs = YsvFloor.Near(Me, Reach);
            if (slabs.Count < 2)
            {
                var to = HeroPos - Me;
                var dir = to.sqrMagnitude > 1f ? to.normalized : Face;
                for (int i = 0; i < 3; i++)
                {
                    var p = CrawlFurther.Util.ModUtil.SafePoint(Me, Me + dir * (24f + i * 14f), 4f);
                    YsvFloor.Lay(p, -1, SeedLife, 0);
                }
                slabs = YsvFloor.Near(Me, Reach);
            }
            yield return new WaitForSeconds(Flare);
            bool struck = false;
            foreach (var s in slabs)
            {
                if (!Alive) yield break;
                YsvUtil.Floor(YsveldFx.SlabFlash, s);
                var hero = YsvUtil.LiveHero();
                if (hero != null && !struck)
                {
                    var d = (Vector2)hero.transform.position - s;
                    if ((d.x * d.x) / (YsvFloor.RX * YsvFloor.RX) + (d.y * d.y) / (YsvFloor.RY * YsvFloor.RY) <= 1f)
                    {
                        struck = true;      // once per burst: the light runs on, the first slab that catches him strikes
                        YsvUtil.Hurt(hero, Damage, d, Own);
                        YsvUtil.Rime(hero, Own, 1, true);
                    }
                }
                yield return new WaitForSeconds(Gap);
            }
        }
    }
}
