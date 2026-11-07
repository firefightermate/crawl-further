using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Carrion Saint, The Flock: up to <see cref="MaxCrows"/> crows perch on its arms, one coming back every
    /// <see cref="Regrow"/> s; a bone pile that reaches it adds a crow at once (in place of a plate). Its basic sends the next
    /// perched crow at the hero (with none perched, it calls one back instead); Murder sends every perched crow at once as a
    /// wall <see cref="Wall"/> px wide. Tell: the crows on its arms (the IdleN / RunN stances).
    /// </summary>
    public class SaintFlock : OssBehaviour
    {
        public const int MaxCrows = 4;
        public const float Regrow = 2f, Wall = 40f;
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
            int n = m_crows;
            Set(0);
            Vector2 f = Face, across = new Vector2(-f.y, f.x);
            Vector2 c = Me + f * 10f + new Vector2(0f, 2f);
            float ang = AngleOf(f);
            var src = Own;
            for (int i = 0; i < n; i++)
            {
                float k = n == 1 ? 0f : (i / (float)(n - 1) - 0.5f);
                FxFactory.SpawnOwned(OssivarFx.CrowWall, ModUtil.SafePoint(Me, c + across * k * Wall, 3f), src, ang);
            }
        }
    }
}
