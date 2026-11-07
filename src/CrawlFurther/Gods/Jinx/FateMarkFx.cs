using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Fortune Teller's fate mark: its eye follows the hero for <see cref="TrackTime"/> s, then it seals in place, and
    /// at <see cref="Delay"/> its card turns: The Tower (knives fall), The Fool (confetti bombs) or The Star (she and her
    /// allies heal).
    /// </summary>
    public class FateMarkFx : MonoBehaviour
    {
        /// <summary>The card turns on the mark's flash frame (frame 9 starts at 0.92 s; the art ends at 1.02 s).</summary>
        public const float Delay = 0.92f;
        /// <summary>How long the open eye follows the hero (frames 0-4) before it shuts.</summary>
        public const float TrackTime = 0.5f;

        float m_t;
        bool m_done;
        int m_fate = -1;

        public void Arm() { m_t = 0f; m_done = false; m_fate = -1; }
        public void Seal(int fate) { m_fate = fate; }
        void OnEnable() { Arm(); }

        void Update()
        {
            if (m_done) return;
            m_t += Time.deltaTime;
            if (m_t < TrackTime)
            {
                var hero = ModUtil.Hero();
                if (hero != null)
                {
                    Vector2 to = Vector2.MoveTowards(transform.position, hero.transform.position, 120f * Time.deltaTime);
                    transform.position = new Vector3(to.x, to.y, transform.position.z);
                }
                return;
            }
            if (m_t < Delay) return;
            m_done = true;
            Vector2 pos = transform.position;
            var src = FxFactory.SourceOf(gameObject);
            int fate = m_fate >= 0 ? m_fate : Random.Range(0, 3);
            if (JinxFx.Tarot != null && JinxFx.Tarot[fate] != null) SystemPool.Spawn(JinxFx.Tarot[fate], pos + new Vector2(0f, 4f));
            switch (fate)
            {
                case 0:   // The Tower: three knives plunge into the mark
                    if (JinxFx.KnifeRain != null)
                        foreach (var o in new[] { Vector2.zero, new Vector2(-9f, 3f), new Vector2(9f, -3f) })
                            FxFactory.SpawnOwned(JinxFx.KnifeRain, ModUtil.SafePoint(pos, pos + o, 2f), src);
                    break;
                case 1:   // The Fool: confetti bombs burst across it
                    if (JinxFx.ConfettiPop != null)
                        foreach (var o in new[] { Vector2.zero, new Vector2(-12f, 0f), new Vector2(12f, 0f) })
                            FxFactory.SpawnOwned(JinxFx.ConfettiPop, ModUtil.SafePoint(pos, pos + o, 2f), src);
                    break;
                default:  // The Star: the teller heals 1, her allies nearby 0.5
                    Star(src);
                    break;
            }
        }

        static void Star(DamageSource src)
        {
            var owner = src != null ? src.m_sourceOwner : null;
            if (owner == null) return;
            Vector2 op = owner.transform.position;
            foreach (var p in FindObjectsOfType<Player>())
            {
                if (p == null || p.gameObject == ModUtil.Hero() || ModUtil.IsGhost(p)) continue;
                var h = p.GetComponent<Health>();
                if (h == null || !h.IsAlive()) continue;
                bool me = p.gameObject == owner;
                if (!me && ((Vector2)p.transform.position - op).sqrMagnitude > 60f * 60f) continue;
                h.Heal(me ? 1f : 0.5f);
                ModInd.Heal(p.gameObject);
            }
        }
    }
}
