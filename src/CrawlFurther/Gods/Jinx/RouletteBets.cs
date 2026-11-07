using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Roulette Ouroboros, Place Your Bets: as it spins, eight red and black wedges mark the floor round the hero. When
    /// the ball drops, the wedges of the called colour flash for <see cref="CallTime"/> s and erupt. The House Always
    /// Wins: one drop in eight lands on the green zero: every wedge erupts and it heals <see cref="ZeroHeal"/>.
    /// </summary>
    public class RouletteBets : JinxBehaviour
    {
        public const int Wedges = 8;
        public const float CallTime = 0.4f, ZeroHeal = 1f, ZeroChance = 1f / 8f;
        /// <summary>Where wedge i's centre sits from the centre of the bets: the art's ellipse (34 x 15 px, the inner quarter
        /// empty) halfway out.</summary>
        public const float WedgeRx = 21f, WedgeRy = 9.4f;

        Vector2 m_centre;
        GameObject m_mark;

        protected override void OnDisable() { base.OnDisable(); ClearMark(); }

        void ClearMark()
        {
            if (m_mark != null && m_mark.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(m_mark);
            m_mark = null;
        }

        /// <summary>Clip event: the bets go down round the hero.</summary>
        public void ModJinxBets()
        {
            if (!Alive) return;
            ClearMark();
            m_centre = HeroPos;
            if (JinxFx.BetMark != null) m_mark = SystemPool.Spawn(JinxFx.BetMark, m_centre);
        }

        /// <summary>Clip event: the ball drops into a pocket and calls a colour (0 red, 1 black, 2 the green zero).</summary>
        public void ModJinxBallDrop()
        {
            if (!Alive) { ClearMark(); return; }
            int call = Random.value < ZeroChance ? 2 : Random.Range(0, 2);
            ClearMark();
            if (JinxFx.BetCall != null && JinxFx.BetCall[call] != null) SystemPool.Spawn(JinxFx.BetCall[call], m_centre);
            if (call == 2 && Hp != null) { Hp.Heal(ZeroHeal); ModInd.Heal(gameObject); }
            StartCoroutine(Erupt(call, m_centre, Own));
        }

        IEnumerator Erupt(int call, Vector2 centre, DamageSource src)
        {
            yield return new WaitForSeconds(CallTime);
            var tmpl = JinxFx.WedgeBurst != null ? JinxFx.WedgeBurst[call] : null;
            if (tmpl == null) yield break;
            for (int i = 0; i < Wedges; i++)
            {
                bool red = i % 2 == 0;
                if (call == 0 && !red || call == 1 && red) continue;
                float a = (i * 45f - 90f) * Mathf.Deg2Rad;
                // the art's y runs down the screen: wedge 0 (angle -90) is the far one, above the centre
                Vector2 p = centre + new Vector2(WedgeRx * Mathf.Cos(a), -WedgeRy * Mathf.Sin(a));
                FxFactory.SpawnOwned(tmpl, ModUtil.SafePoint(centre, p, 2f), src);
            }
        }
    }
}
