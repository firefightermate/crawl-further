using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    /// <summary>
    /// Rime Warden. Challenge: when the hero comes within 90 px it bangs mace on shield (the Challenge flourish) and for
    /// 3 s his hits on anything but the Warden do half damage (<see cref="YsvChallenged"/>); once every 10 s. Tell: a frost
    /// sigil over the Warden and a matching brand over the hero. Shield Rush (its special): while the shield is up
    /// (YsvShieldUp .. YsvShieldDown) shots from the front stop on it.
    /// </summary>
    public class WardenChallenge : YsveldBehaviour
    {
        public const float Reach = 90f, Every = 10f, BangAt = 0.54f;
        public static exSpriteAnimClip ChallengeClip;
        float m_next, m_bang;
        bool m_shield;
        GameObject m_sigil;

        protected override void OnEnable() { base.OnEnable(); m_next = Time.time + 2f; m_bang = -1f; m_shield = false; }

        protected override void OnDisable() { base.OnDisable(); DropSigil(); }

        public void YsvShieldUp() { m_shield = true; }
        public void YsvShieldDown() { m_shield = false; }

        public override bool BlockHeroHit(DamageInfo d)
        {
            if (!m_shield || !IsShot(d)) return false;
            var shot = d.m_source.m_source;
            if (shot == null || Vector2.Dot((Vector2)shot.transform.position - Me, Face) <= 0f) return false;
            Show(YsveldFx.ShieldBlock, Me + Face * 12f + new Vector2(0f, 12f));
            return true;
        }

        void DropSigil() { if (m_sigil != null) { CrawlFurther.Monsters.ModAttach.Drop(m_sigil, gameObject); m_sigil = null; } }

        void Update()
        {
            if (!Alive) { DropSigil(); m_shield = false; return; }
            if (m_shield && !InAttack) m_shield = false;
            if (m_bang > 0f)
            {
                m_bang -= Time.deltaTime;
                if (m_bang <= 0f)
                {
                    var hero = YsvUtil.LiveHero();
                    if (hero != null)
                    {
                        YsvChallenged.Begin(hero, gameObject);
                        Show(YsveldFx.ChallengeBang, Me + new Vector2(10f * Side, 20f));
                        DropSigil();
                        if (YsveldFx.Sigil != null) m_sigil = CrawlFurther.Monsters.ModAttach.Spawn(YsveldFx.Sigil, gameObject, new Vector2(0f, 46f));
                    }
                }
            }
            if (m_sigil != null && (YsvUtil.LiveHero() == null || !YsvChallenged.Any)) DropSigil();
            if (Time.time < m_next) return;
            var h = YsvUtil.LiveHero();
            if (h == null || ((Vector2)h.transform.position - Me).sqrMagnitude > Reach * Reach) return;
            if (!Flourish(ChallengeClip)) return;
            m_next = Time.time + Every;
            m_bang = BangAt;
        }
    }
}
