using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Oracle, Seen It Coming. Her third-eye orb leads the hero (it flies at where they are going). Prophecy: a
    /// violet ghost of her appears near the hero and acts out her next move, a fan of three orbs, with harmless omen orbs;
    /// exactly <see cref="Foresight"/> s later she blinks to that spot and makes the same move: same place, same aim, same
    /// timing.
    /// </summary>
    public class OracleProphecy : JinxBehaviour
    {
        /// <summary>From the ghost's orbs to hers (the ghost looses on its frame 4 at 0.52 s; she on Prophecy frame 9,
        /// 1.52 s after the ghost appears on frame 2).</summary>
        public const float Foresight = 1.0f, GhostRelease = 0.52f, Away = 44f, FanStep = 14f, OrbSpeed = 150f;
        static readonly Vector2 Hands = new Vector2(14f, 19f);
        static readonly Vector2 Eye = new Vector2(8f, 32f);

        Vector2 m_spot;
        float m_aim, m_side = 1f;
        bool m_prophecy;

        protected override void OnEnable() { base.OnEnable(); m_prophecy = false; }

        /// <summary>Clip event (Gaze): an orb aimed where the hero will be when it gets there.</summary>
        public void ModJinxLeadOrb()
        {
            if (!Alive || JinxFx.EyeOrb == null) return;
            Vector2 from = Me + new Vector2(Eye.x * Side, Eye.y);
            var hero = ModUtil.Hero();
            Vector2 tgt = HeroPos + new Vector2(0f, 6f);
            var hm = hero != null ? hero.GetComponent<PlayerMovement>() : null;
            if (hm != null) tgt += hm.GetVelocity() * ((tgt - from).magnitude / OrbSpeed) * 0.8f;
            FxFactory.SpawnOwned(JinxFx.EyeOrb, from, Own, AngleTo(from, tgt));
        }

        /// <summary>Clip event (Prophecy frame 2): the ghost appears and acts out her next move.</summary>
        public void ModJinxProphecy()
        {
            if (!Alive) return;
            Vector2 hp = HeroPos;
            var dir = (Vector2)(Quaternion.Euler(0, 0, Random.Range(0f, 360f)) * Vector2.right);
            m_spot = ModUtil.SafePoint(hp, hp + new Vector2(dir.x * Away, dir.y * Away * 0.7f), 8f);
            m_side = hp.x >= m_spot.x ? 1f : -1f;
            Vector2 from = m_spot + new Vector2(Hands.x * m_side, Hands.y);
            m_aim = AngleTo(from, hp + new Vector2(0f, 6f));
            m_prophecy = true;
            if (JinxFx.OracleGhost != null)
            {
                var g = SystemPool.Spawn(JinxFx.OracleGhost, m_spot);
                if (g != null) { var s = g.transform.localScale; g.transform.localScale = new Vector3(Mathf.Abs(s.x) * m_side, s.y, s.z); }
            }
            StartCoroutine(Omens(from, m_aim));
        }

        IEnumerator Omens(Vector2 from, float aim)
        {
            yield return new WaitForSeconds(GhostRelease);
            if (!Alive || JinxFx.OmenOrb == null) yield break;
            for (int k = -1; k <= 1; k++) FxFactory.SpawnOwned(JinxFx.OmenOrb, from, null, aim + k * FanStep);
        }

        /// <summary>Clip event (Prophecy frame 7): she blinks to the ghost's spot.</summary>
        public void ModJinxProphecyBlink()
        {
            if (!Alive || !m_prophecy) return;
            if (JinxFx.Blink != null) { SystemPool.Spawn(JinxFx.Blink, Me); SystemPool.Spawn(JinxFx.Blink, m_spot); }
            ModUtil.Teleport(gameObject, m_spot);
            if (Move != null) Move.SetDirection(new Vector2(m_side, 0f));
        }

        /// <summary>Clip event (Prophecy frame 9): the fan the ghost showed.</summary>
        public void ModJinxProphecyCast()
        {
            if (!Alive || !m_prophecy || JinxFx.EyeOrb == null) return;
            m_prophecy = false;
            Vector2 from = m_spot + new Vector2(Hands.x * m_side, Hands.y);
            for (int k = -1; k <= 1; k++) FxFactory.SpawnOwned(JinxFx.EyeOrb, from, Own, m_aim + k * FanStep);
        }
    }
}
