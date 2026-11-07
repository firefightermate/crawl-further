using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Card Soldier, Paper Thin: once the hero has aimed at it for <see cref="AimTime"/> s it turns edge-on for up to
    /// <see cref="EdgeTime"/> s: shots pass it by, but a swing knocks it flat and does +50 %. Then it stays flat for
    /// <see cref="RestTime"/> s. Tell: it narrows to a 2 px line (the Edge idle and run). Also deals the trap cards.
    /// </summary>
    public class SoldierPaper : JinxBehaviour
    {
        public const float AimTime = 0.25f, EdgeTime = 1.5f, RestTime = 1.5f, SwingBonus = 1.5f;
        public const int MaxTraps = 9;
        /// <summary>The edge-on stance (set by the kit).</summary>
        public static exSpriteAnimClip EdgeIdle, EdgeRun;

        float m_aimed, m_edgeUntil, m_restUntil;

        bool Edge { get { return m_edgeUntil > Time.time; } }

        protected override void OnEnable() { base.OnEnable(); m_aimed = 0f; m_edgeUntil = 0f; m_restUntil = 0f; }

        void Update()
        {
            if (!Alive) return;
            if (m_edgeUntil > 0f && Time.time >= m_edgeUntil) Flatten();
            if (Edge || Time.time < m_restUntil) return;
            m_aimed = HeroAimsAtMe(18f, 180f) ? m_aimed + Time.deltaTime : 0f;
            if (m_aimed < AimTime) return;
            m_aimed = 0f;
            m_edgeUntil = Time.time + EdgeTime;
            SetStance(EdgeIdle, EdgeRun);
        }

        void Flatten()
        {
            m_edgeUntil = 0f;
            m_restUntil = Time.time + RestTime;
            SetStance(null, null);
        }

        public override bool BlockHeroHit(DamageInfo d) { return Edge && IsShot(d); }

        public override float HeroHitScale(DamageInfo d)
        {
            if (!Edge) return 1f;
            Flatten();
            return SwingBonus;
        }

        /// <summary>Clip event: three face-down trap cards land round the hero's feet.</summary>
        public void ModJinxDealTraps()
        {
            if (JinxFx.TrapCard == null || !Alive) return;
            Vector2 hp = HeroPos;
            float start = Random.Range(0f, 360f);
            for (int i = 0; i < 3; i++)
            {
                if (JinxTrapFx.Count() >= MaxTraps) break;
                var off = (Vector2)(Quaternion.Euler(0, 0, start + i * 120f) * Vector2.right) * Random.Range(10f, 18f);
                FxFactory.SpawnOwned(JinxFx.TrapCard, ModUtil.SafePoint(hp, hp + new Vector2(off.x, off.y * 0.6f), 3f), Own);
            }
        }
    }
}
