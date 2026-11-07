using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Rattlebones, Headless: Lob throws its skull, which stays where it lands and chatters (<see cref="OssSkullFx"/>). While
    /// the skull is out only the skull can be hurt (hits on the body pass through), the basic attack is a headless swipe,
    /// and that swipe calls the skull home along the floor. Tell: the empty neck (IdleBare / RunBare) and the grinning skull.
    /// </summary>
    public class RattleSkull : OssBehaviour
    {
        public const float AutoRecall = 6f;
        /// <summary>The headless stance (set by the kit).</summary>
        public static exSpriteAnimClip BareIdle, BareRun;

        OssSkullFx m_skull;
        bool m_out, m_forwarding;
        float m_outAt;

        /// <summary>True while the skull is off the body.</summary>
        public bool Headless { get { return m_out; } }

        protected override void OnEnable() { base.OnEnable(); m_out = false; m_skull = null; m_forwarding = false; }

        protected override void OnDisable()
        {
            base.OnDisable();
            if (m_skull != null) m_skull.Vanish();
            m_skull = null; m_out = false;
        }

        /// <summary>Clip event (Lob frame 1): the skull comes off.</summary>
        public void OssSkullOff()
        {
            m_out = true; m_outAt = Time.time;
            SetStance(BareIdle, BareRun);
            NextBasic(1);
        }

        /// <summary>The thrown skull came to rest at <paramref name="at"/>: it becomes the skull on the floor.</summary>
        public void Landed(Vector2 at)
        {
            if (!Alive || !m_out || m_skull != null || OssivarFx.SkullFloor == null) { if (Alive && m_skull == null) Home(); return; }
            var go = SystemPool.Spawn(OssivarFx.SkullFloor, at);
            if (go == null) { Home(); return; }
            m_skull = go.GetComponent<OssSkullFx>() ?? go.AddComponent<OssSkullFx>();
            m_skull.Bind(this);
        }

        /// <summary>Clip event (Swipe frame 3): call the skull home.</summary>
        public void OssCallSkull() { if (m_skull != null) m_skull.Recall(); }

        /// <summary>Clip event (Collapse frame 0): the skull snaps back at once.</summary>
        public void OssSkullSnap()
        {
            if (m_skull != null) m_skull.Vanish();
            Home();
        }

        /// <summary>The skull is back on the neck.</summary>
        public void Home()
        {
            m_skull = null; m_out = false;
            SetStance(null, null);
            NextBasic(0);
        }

        /// <summary>A hit on the skull lands on the body.</summary>
        public void HitThroughSkull(DamageInfo d)
        {
            if (!Alive || Hp == null) return;
            m_forwarding = true;
            try { Hp.Damage(new DamageInfo(d.m_amount, d.m_knockbackMultiplier, d.m_stunTime, d.m_direction, d.m_source), false); }
            finally { m_forwarding = false; }
        }

        void Update()
        {
            if (m_out && m_skull != null && Time.time - m_outAt > AutoRecall) { m_skull.Recall(); m_outAt = Time.time; }
            // thrown but never landed (the shot vanished somewhere odd): put it back
            if (m_out && m_skull == null && Time.time - m_outAt > 1.5f) Home();
        }

        public override bool BlockHeroHit(DamageInfo d) { return m_out && !m_forwarding; }

        public Vector2 Neck { get { return Me + new Vector2(Side * 3f, 0f); } }
    }
}
