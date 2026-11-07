using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Reef Champion, Rounds: every <see cref="Round"/> s a ringside bell chimes. It backs off to the nearest brine pool
    /// (or <see cref="Corner"/> px away), drops its guard for <see cref="Rest"/> s and heals <see cref="Heal"/>, then comes
    /// out <see cref="Faster"/> faster for the next round (two rounds at most). Tell: the chime, a little bell over its head,
    /// its head bowed (Rest).
    /// </summary>
    public class ChampionRounds : BelBehaviour
    {
        public const float Round = 12f, Corner = 40f, Rest = 2f, Heal = 1f, Faster = 0.2f, Retreat = 1.2f;
        public const int MaxRounds = 2;
        /// <summary>The bowed rest in its corner (set by the kit).</summary>
        public static exSpriteAnimClip RestClip;

        float m_clock;
        int m_rounds;
        bool m_resting;

        protected override void OnEnable() { base.OnEnable(); m_clock = 0f; m_rounds = 0; m_resting = false; }

        void Update()
        {
            if (!Alive || m_resting || m_rounds >= MaxRounds) return;
            m_clock += Time.deltaTime;
            if (m_clock < Round || InAttack) return;
            m_clock = 0f;
            StartCoroutine(Recess());
        }

        IEnumerator Recess()
        {
            m_resting = true;
            if (BelMoraFx.RoundBell != null) ModInd.Set(gameObject, BelMoraFx.RoundBell, true, Retreat + Rest);
            Vector2 corner;
            BelPool pool;
            if (BelWater.Nearest(Me, 120f, out pool)) corner = pool.Pos;
            else corner = ModUtil.SafePoint(Me, Me - ToHero() * Corner, 6f);
            float t = 0f;
            while (t < Retreat && Alive && (corner - Me).sqrMagnitude > 25f)
            {
                t += Time.deltaTime;
                var d = corner - Me;
                Shift(d.normalized * Mathf.Min(90f * Time.deltaTime, d.magnitude));
                yield return null;
            }
            if (!Alive) yield break;
            Monster.FaceHero();
            Hold(RestClip, Rest);
            float healed = 0f;
            t = 0f;
            while (t < Rest && Alive)
            {
                t += Time.deltaTime;
                float h = Mathf.Min(Heal * Time.deltaTime / Rest, Heal - healed);
                if (h > 0f && Hp != null) { Hp.Heal(h); healed += h; }
                yield return null;
            }
            if (Alive) ModInd.Heal(gameObject);
            m_rounds++;
            SpeedScale(1f + Faster * m_rounds);
            m_resting = false;
        }
    }
}
