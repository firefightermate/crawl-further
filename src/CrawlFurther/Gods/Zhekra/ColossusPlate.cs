using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Chitin Colossus, Front Plate and Bulldozer: hits from the front do <see cref="FrontDamage"/>x, from behind
    /// <see cref="BackDamage"/>x, and it turns slowly (<see cref="TurnRate"/> degrees a second: it steers its own stick
    /// toward where its driver wants to go). Bulldozer lowers the head plate and charges, shoving the hero along in front
    /// of it. Tell: the head plate gleams toward the hero; the soft pale back end.
    /// </summary>
    public class ColossusPlate : ZhkBehaviour
    {
        public const float FrontDamage = 0.5f, BackDamage = 1.5f, TurnRate = 100f, ArcCos = 0.34f, ShoveReach = 18f;

        float m_heading;
        bool m_init, m_shoving;
        PlayerData m_data;

        protected override void OnEnable() { base.OnEnable(); m_init = false; m_shoving = false; m_data = null; }

        Vector2 Heading { get { return new Vector2(Mathf.Cos(m_heading * Mathf.Deg2Rad), Mathf.Sin(m_heading * Mathf.Deg2Rad)); } }

        /// <summary>Where the body's driver (a player or the AI) is pushing its stick.</summary>
        Vector2 Wanted()
        {
            if (Move == null) return Vector2.zero;
            if (R.Get<bool>(Move, "m_ai"))
            {
                var ai = R.Get<PlayerAI>(Move, "m_playerAI");
                return ai != null ? ai.GetFaceDirection() * ai.GetMoveRatio() : Vector2.zero;
            }
            if (m_data == null) m_data = R.Get<PlayerData>(Move, "m_playerData");
            return m_data != null ? m_data.GetInputMove() : Vector2.zero;
        }

        void Update()
        {
            if (!Alive) { Steer(null); return; }
            if (!m_init) { m_init = true; var f = Face; m_heading = Mathf.Atan2(f.y, f.x) * Mathf.Rad2Deg; }
            var want = Wanted();
            float mag = Mathf.Clamp01(want.magnitude);
            if (mag > 0.1f)
                m_heading = Mathf.MoveTowardsAngle(m_heading, Mathf.Atan2(want.y, want.x) * Mathf.Rad2Deg, TurnRate * Time.deltaTime);
            // in an attack the stick only aims (the clip holds it still); out of one it walks the slow-turning heading
            Steer(Heading * (InAttack ? 1f : mag));
        }

        public override float HeroHitScale(DamageInfo d)
        {
            var hero = ModUtil.Hero();
            if (hero == null) return 1f;
            var to = (Vector2)hero.transform.position - Me;
            if (to.sqrMagnitude < 1f) return 1f;
            float c = Vector2.Dot(to.normalized, Face);
            return c > ArcCos ? FrontDamage : c < -ArcCos ? BackDamage : 1f;
        }

        /// <summary>Clip event (Bulldoze): the charge starts; a hero in front of the plate is shoved along.</summary>
        public void ModZhkBulldoze(float seconds)
        {
            var hero = ModUtil.Hero();
            if (!Alive || hero == null || m_shoving) return;
            StartCoroutine(Shove(hero, seconds));
        }

        IEnumerator Shove(GameObject hero, float seconds)
        {
            m_shoving = true;
            bool caught = false;
            for (float t = 0f; t < seconds; t += Time.deltaTime)
            {
                if (!Alive || hero == null || !hero.activeInHierarchy) break;
                Vector2 hp = hero.transform.position, to = hp - Me;
                var f = Face;
                if (!caught && to.sqrMagnitude <= ShoveReach * ShoveReach && Vector2.Dot(to.normalized, f) > 0.5f)
                    caught = ModStatus.AllowCrowdControl(hero);
                if (caught) ModUtil.Teleport(hero, ModUtil.SafePoint(Me, Me + f * 15f));
                yield return null;
            }
            m_shoving = false;
        }
    }
}
