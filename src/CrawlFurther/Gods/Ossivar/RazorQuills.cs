using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Razorback, Bristling: each second it runs raises one quill (up to <see cref="Max"/>); each second it stands still lowers
    /// one. Skid ends a short burst in a skid that fires every raised quill ahead in a fan. Tell: the quills standing on its
    /// back, one by one (the IdleN / RunN stances).
    /// </summary>
    public class RazorQuills : OssBehaviour
    {
        public const int Max = 5;
        public const float Spread = 12f;
        /// <summary>Stances by quill count (index 0 = none), set by the kit.</summary>
        public static exSpriteAnimClip[] Idles, Runs;
        int m_quills;
        float m_run, m_still;

        protected override void OnEnable() { base.OnEnable(); m_quills = 0; m_run = 0f; m_still = 0f; }

        void Set(int q)
        {
            m_quills = Mathf.Clamp(q, 0, Max);
            if (Idles != null && Runs != null) SetStance(Idles[m_quills], Runs[m_quills]);
        }

        void Update()
        {
            if (!Alive || Body == null) return;
            var st = Body.GetState();
            if (st == Player.ePlayerState.Run) { m_still = 0f; m_run += Time.deltaTime; if (m_run >= 1f) { m_run = 0f; if (m_quills < Max) Set(m_quills + 1); } }
            else if (st == Player.ePlayerState.Idle) { m_run = 0f; m_still += Time.deltaTime; if (m_still >= 1f) { m_still = 0f; if (m_quills > 0) Set(m_quills - 1); } }
        }

        /// <summary>Clip event (Skid frame 4): every raised quill flies ahead.</summary>
        public void OssQuillFire()
        {
            if (!Alive || OssivarFx.Quill == null) { Set(0); return; }
            int n = m_quills;
            float a0 = AngleOf(Face) - Spread * (n - 1) * 0.5f;
            Vector2 from = Me + Face * 6f;
            var src = Own;
            for (int i = 0; i < n; i++) FxFactory.SpawnOwned(OssivarFx.Quill, from, src, a0 + Spread * i);
            Set(0);
        }
    }
}
