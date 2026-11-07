using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Util;

    /// <summary>
    /// A hook, lasso or line: when it reaches the hero it hauls them toward whoever threw it, then despawns. Add it to
    /// projectile instances from a spawn hook (<see cref="FxFactory.OnSpawn"/>).
    /// </summary>
    public class HookFx : MonoBehaviour
    {
        /// <summary>Pull strength handed to <see cref="ModUtil.Pull"/>.</summary>
        public float strength = 230f;
        bool m_done;

        void OnEnable() { m_done = false; }

        void Update()
        {
            if (m_done) return;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 me = transform.position, hp = hero.transform.position;
            if ((hp - me).sqrMagnitude > 11f * 11f) return;
            m_done = true;
            var src = FxFactory.SourceOf(gameObject);
            var owner = src != null ? src.m_sourceOwner : null;
            Vector2 to = owner != null ? (Vector2)owner.transform.position : me;
            ModUtil.Pull(hero, to, strength);
            SystemPool.Despawn(gameObject);
        }
    }
}
