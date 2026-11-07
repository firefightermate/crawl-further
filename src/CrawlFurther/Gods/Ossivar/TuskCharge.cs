using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Gravetusk, Scent Charge: a charge at a bleeding hero bends after him, up to <see cref="MaxBend"/> degrees, and bone
    /// piles it tramples burst into four shards. Tell: the scent trail (as the hound's), and piles ahead glow before it
    /// hits them.
    /// </summary>
    public class TuskCharge : HoundScent
    {
        public const float MaxBend = 40f, TurnRate = 160f, Trample = 12f, GlowAhead = 40f;
        readonly System.Collections.Generic.HashSet<BonePileFx> m_glowed = new System.Collections.Generic.HashSet<BonePileFx>();
        bool m_charging;
        float m_startAngle;

        protected override void OnEnable() { base.OnEnable(); m_charging = false; }

        /// <summary>Clip event (Charge frame 1): the run starts here.</summary>
        public void OssChargeOn() { m_charging = true; m_startAngle = AngleOf(Face); m_glowed.Clear(); }

        /// <summary>Clip event (Charge frame 7).</summary>
        public void OssChargeOff() { m_charging = false; }

        protected override void Update()
        {
            base.Update();
            if (!m_charging) return;
            if (!Alive || !InAttack) { m_charging = false; return; }
            if (HeroBleeding && Move != null)
            {
                float cur = AngleOf(Face), want = AngleOf(HeroPos - Me);
                float next = Mathf.MoveTowardsAngle(cur, want, TurnRate * Time.deltaTime);
                float off = Mathf.DeltaAngle(m_startAngle, next);
                next = m_startAngle + Mathf.Clamp(off, -MaxBend, MaxBend);
                Move.SetDirection(Dir(next));
            }
            foreach (var p in BonePileFx.Snapshot())
            {
                if (p == null || p.Locked) continue;
                Vector2 d = p.Pos - Me;
                if (d.sqrMagnitude < Trample * Trample) { Burst(p); continue; }
                if (d.sqrMagnitude < GlowAhead * GlowAhead && Vector2.Dot(d.normalized, Face) > 0.7f && OssivarFx.PileGlow != null)
                {
                    if (m_glowed.Add(p)) SystemPool.Spawn(OssivarFx.PileGlow, p.Pos);
                }
            }
        }

        void Burst(BonePileFx p)
        {
            Vector2 at = p.Pos;
            p.Consume();
            if (OssivarFx.PlateShatter != null) SystemPool.Spawn(OssivarFx.PlateShatter, at);
            if (OssivarFx.TuskShard == null) return;
            float a0 = AngleOf(Face) + 45f;
            for (int i = 0; i < 4; i++) FxFactory.SpawnOwned(OssivarFx.TuskShard, at, Own, a0 + 90f * i);
        }
    }
}
