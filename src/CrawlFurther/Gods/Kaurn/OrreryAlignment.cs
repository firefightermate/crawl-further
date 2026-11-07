using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Storm Orrery's Alignment: its three planets swing into a line pointing at the hero over <see cref="Align"/> s, then a
    /// beam fires along it (1.5, <see cref="Length"/> px). Lined Up: the line shows on the floor while they align, and it turns
    /// only <see cref="Turn"/> deg a second, so a step sideways beats it.
    /// </summary>
    public class OrreryAlignment : KaurnBehaviour
    {
        public const float Align = 0.8f, Turn = 40f, Length = 160f, Damage = 1.5f, Width = 7f, BeamTime = 0.25f;
        static readonly float[] PlanetAt = { 34f, 62f, 90f };
        readonly List<GameObject> m_line = new List<GameObject>();
        readonly GameObject[] m_planets = new GameObject[3];

        protected override void OnDisable() { base.OnDisable(); Clear(); }

        void Clear()
        {
            KaurnFx.Clear(m_line);
            for (int k = 0; k < 3; k++) { if (m_planets[k] != null && m_planets[k].activeInHierarchy) SystemPool.Despawn(m_planets[k]); m_planets[k] = null; }
        }

        /// <summary>Clip event: the rings spin up.</summary>
        public void KrnAlign() { StopAllCoroutines(); Clear(); StartCoroutine(Run()); }

        IEnumerator Run()
        {
            float ang = KaurnFx.Angle(Me, HeroPos);
            for (int k = 0; k < 3; k++) if (KaurnFx.Planets[k] != null) m_planets[k] = SystemPool.Spawn(KaurnFx.Planets[k], Me + new Vector2(0f, 23f));
            float t = 0f;
            Vector2 a = Me, b = Me;
            while (t < Align && Alive)
            {
                t += Time.deltaTime;
                ang = Mathf.MoveTowardsAngle(ang, KaurnFx.Angle(Me, HeroPos), Turn * Time.deltaTime);
                var dir = new Vector2(Mathf.Cos(ang * Mathf.Deg2Rad), Mathf.Sin(ang * Mathf.Deg2Rad));
                a = Me + dir * 6f;
                b = ModUtil.SafePoint(a, Me + dir * Length, 2f);
                KaurnFx.Chain(m_line, KaurnFx.PlanetDots, a, b, 16);
                // the planets slide down from their rings onto the line
                float k01 = Mathf.Clamp01(t / Align);
                for (int k = 0; k < 3; k++)
                {
                    if (m_planets[k] == null) continue;
                    var on = Me + dir * PlanetAt[k];
                    var p = Vector2.Lerp(Me + new Vector2((k - 1) * 10f, 23f), on, k01 * k01);
                    m_planets[k].transform.position = new Vector3(p.x, p.y, m_planets[k].transform.position.z);
                }
                yield return null;
            }
            if (!Alive) { Clear(); yield break; }
            KaurnFx.Chain(m_line, KaurnFx.PlanetBeam, a, b, 16);
            var hero = ModUtil.Hero();
            bool hit = false;
            t = 0f;
            while (t < BeamTime)
            {
                t += Time.deltaTime;
                if (!hit && hero != null)
                {
                    float s;
                    if (KaurnFx.SegDist(hero.transform.position, a, b, out s) < Width)
                    {
                        hit = true;
                        var h = hero.GetComponent<Health>();
                        var dir = b - a;
                        if (h != null && h.IsAlive()) h.Damage(new DamageInfo(Damage, 0.8f, 0f, dir.normalized, Own), false);
                        if (KaurnFx.HitFx != null) SystemPool.Spawn(KaurnFx.HitFx, KaurnFx.HeroChest(hero));
                    }
                }
                yield return null;
            }
            Clear();
        }
    }
}
