using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Acid Mantis, Lightning Reflex: anything that enters its <see cref="Reach"/> px reach, the hero or one of his shots,
    /// is struck at once; a shot is cut out of the air. At most one strike every <see cref="Cooldown"/> s. Tell: a faint
    /// green crescent on the floor shows its reach, and the blades twitch (Reflex).
    /// </summary>
    public class MantisReflex : ZhkBehaviour
    {
        public const float Reach = 28f, Cooldown = 1f, ChestY = 10f;
        /// <summary>The flick of the blade (set by the kit).</summary>
        public static exSpriteAnimClip ReflexClip;

        float m_ready;
        GameObject m_ring;

        protected override void OnEnable() { base.OnEnable(); m_ready = Time.time + 0.5f; }

        protected override void OnDisable() { base.OnDisable(); ModAttach.Drop(m_ring, gameObject); m_ring = null; }

        void Update()
        {
            if (!Alive) { ModAttach.Drop(m_ring, gameObject); m_ring = null; return; }
            if (m_ring == null && ZhekraFx.Reach != null) m_ring = ModAttach.Spawn(ZhekraFx.Reach, gameObject, Vector2.zero, -0.05f);
            if (Time.time < m_ready || InAttack) return;
            Vector2 c = Me + new Vector2(0f, ChestY);
            foreach (var s in ZhkHeroShot.All)
            {
                if (s == null || !s.isActiveAndEnabled) continue;
                var pm = s.GetComponent<ParticleMotion>();
                if (pm == null || !pm.enabled || pm.GetVelocity().sqrMagnitude < 400f) continue;
                if ((s.Pos - c).sqrMagnitude > Reach * Reach) continue;
                Cut(s.Pos);
                if (ZhekraFx.Splash != null) SystemPool.Spawn(ZhekraFx.Splash, s.Pos);
                SystemPool.Despawn(s.gameObject);
                return;
            }
            var hero = ModUtil.Hero();
            if (hero == null || ((Vector2)hero.transform.position - Me).sqrMagnitude > Reach * Reach) return;
            Cut(hero.transform.position);
            if (ZhekraFx.ReflexCut != null) FxFactory.SpawnOwned(ZhekraFx.ReflexCut, (Vector2)hero.transform.position + new Vector2(0f, 6f), Own);
        }

        void Cut(Vector2 at)
        {
            m_ready = Time.time + Cooldown;
            Monster.Face(at);
            Flourish(ReflexClip);
        }
    }
}
