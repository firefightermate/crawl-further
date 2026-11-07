using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Salt Siren, Tidesong: while she sings, every brine pool within <see cref="Reach"/> px of her slides toward the hero
    /// at <see cref="Slide"/> px/s and stays where it stops. Her Song also tugs the hero toward her and wells brine
    /// under him. Tell: notes ripple from her throat, and foam arrows streak across the sliding pools.
    /// </summary>
    public class SirenTidesong : BelBehaviour
    {
        public const float Reach = 90f, Slide = 30f, Length = 1.2f, Tug = 26f;

        readonly List<BelLine> m_streaks = new List<BelLine>();

        protected override void OnDisable() { base.OnDisable(); ClearStreaks(); }

        /// <summary>Clip event: the song starts.</summary>
        public void BelSong()
        {
            if (!Alive || !gameObject.activeInHierarchy) return;
            StopAllCoroutines();
            StartCoroutine(Sing());
            var hero = ModUtil.Hero();
            if (hero != null && ModUtil.Clear(Me, hero.transform.position)) BelWater.Drag(this, hero, Me, Tug, Length);
        }

        IEnumerator Sing()
        {
            float t = 0f;
            var pools = BelWater.Near(Me, Reach);
            while (t < Length && Alive)
            {
                t += Time.deltaTime;
                var hero = ModUtil.Hero();
                if (hero == null) break;
                Vector2 hp = hero.transform.position;
                while (m_streaks.Count < pools.Count) m_streaks.Add(new BelLine());
                for (int i = 0; i < pools.Count; i++)
                {
                    var p = pools[i];
                    if (p.Source == null || !p.Source.gameObject.activeInHierarchy) { m_streaks[i].Clear(); continue; }
                    p.Pos = p.Source.transform.position;
                    var d = hp - p.Pos;
                    if (d.sqrMagnitude < 4f) { m_streaks[i].Clear(); continue; }
                    var step = d.normalized * Mathf.Min(Slide * Time.deltaTime, d.magnitude);
                    if (!ModUtil.Clear(p.Pos, p.Pos + step * 4f)) { m_streaks[i].Clear(); continue; }
                    p.Move(step);
                    m_streaks[i].Lay(BelMoraFx.Lane, p.Pos - d.normalized * 8f, p.Pos + d.normalized * 8f, 8f, rotate: true);
                }
                yield return null;
            }
            ClearStreaks();
        }

        void ClearStreaks() { foreach (var s in m_streaks) s.Clear(); }
    }
}
