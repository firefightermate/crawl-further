using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Carrion Saint, The Flock: up to <see cref="MaxCrows"/> crows perch on its arms, one coming back every
    /// <see cref="Regrow"/> s; a bone pile that reaches it adds a crow at once (in place of a plate). Its basic sends the next
    /// perched crow at the hero (with none perched, it calls one back instead); Murder looses the whole flock, the perched
    /// crows and more from the sky, <see cref="Flock"/> in all: they burst from its shoulders one after another in a fan
    /// <see cref="Fan"/> degrees wide aimed at the hero and bend a little toward him. Tell: the crows on its arms (the
    /// IdleN / RunN stances).
    /// <para>Before 1.3.3 Murder sent only the perched crows (often two) side by side from points 20 px either side of it
    /// with no seek, which looked like crows appearing out of thin air beside it.</para>
    /// </summary>
    public class SaintFlock : OssBehaviour
    {
        public const int MaxCrows = 4;
        public const float Regrow = 2f;
        /// <summary>Crows in a Murder, the perched ones included.</summary>
        public const int Flock = 5;
        /// <summary>Murder's fan, degrees edge to edge, and the gap between crows, seconds.</summary>
        public const float Fan = 50f, Gap = 0.05f;
        /// <summary>Stances by crow count (index 0..4), set by the kit.</summary>
        public static exSpriteAnimClip[] Idles, Runs;
        int m_crows;
        float m_regrow;

        public int Crows { get { return m_crows; } }

        protected override void OnEnable() { base.OnEnable(); Set(MaxCrows); m_regrow = 0f; }

        void Set(int n)
        {
            m_crows = Mathf.Clamp(n, 0, MaxCrows);
            if (Idles != null && Runs != null) SetStance(Idles[m_crows], Runs[m_crows]);
        }

        /// <summary>A pile became a crow.</summary>
        public void AddCrow() { Set(m_crows + 1); if (OssivarFx.Caw != null) SystemPool.Spawn(OssivarFx.Caw, Me); }

        void Update()
        {
            if (!Alive || m_crows >= MaxCrows) { m_regrow = 0f; return; }
            m_regrow += Time.deltaTime;
            if (m_regrow >= Regrow) { m_regrow = 0f; Set(m_crows + 1); }
        }

        Vector2 Hand { get { return Me + new Vector2(Side * 16f, 2f); } }

        /// <summary>Clip event (Send frame 2).</summary>
        public void OssSendCrow()
        {
            if (!Alive) return;
            if (m_crows <= 0) { AddCrow(); return; }
            Set(m_crows - 1);
            if (OssivarFx.CrowShot != null) FxFactory.SpawnOwned(OssivarFx.CrowShot, Hand, Own, AngleOf(HeroPos - Hand));
        }

        /// <summary>Clip event (Murder frame 3): the whole flock at once.</summary>
        public void OssMurder()
        {
            if (!Alive || OssivarFx.CrowWall == null) return;
            Set(0);
            StartCoroutine(Loose(Mathf.Max(Flock, m_crows), Own));
        }

        IEnumerator Loose(int n, DamageSource src)
        {
            // middle first, then out to the edges, alternating sides
            for (int i = 0; i < n; i++)
            {
                if (!Alive) yield break;
                int step = (i + 1) / 2;
                float sign = i % 2 == 1 ? -1f : 1f;
                float k = n <= 1 ? 0f : step / (float)((n - 1) / 2 + (n % 2 == 0 ? 1 : 0)) * sign;   // -1 .. 1
                Vector2 shoulder = Me + new Vector2(Side * 6f + k * 5f, 14f);
                float ang = AngleOf(HeroPos + new Vector2(0f, 5f) - shoulder) + k * Fan * 0.5f;
                FxFactory.SpawnOwned(OssivarFx.CrowWall, ModUtil.SafePoint(Me, shoulder, 3f), src, ang);
                if (OssivarFx.Caw != null && i == 0) SystemPool.Spawn(OssivarFx.Caw, Me);
                yield return new WaitForSeconds(Gap);
            }
        }
    }
}
