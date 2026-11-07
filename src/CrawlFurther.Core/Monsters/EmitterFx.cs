using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// Fires a ring of projectiles from where it was spawned, owned by whoever spawned it. Added to instances by
    /// <see cref="FxKit.Emitter"/>.
    /// </summary>
    public class EmitterFx : MonoBehaviour
    {
        /// <summary>The projectile template to fire.</summary>
        public GameObject projectile;
        /// <summary>How many, spread evenly round a circle from a random start angle.</summary>
        public int count = 8;
        bool m_done;

        void OnEnable() { m_done = false; }

        // fires on the first frame, once the spawner has handed over its damage source
        void Update()
        {
            if (m_done || projectile == null) return;
            m_done = true;
            var src = FxFactory.SourceOf(gameObject);
            float start = Random.Range(0f, 360f);
            for (int i = 0; i < count; i++)
                FxFactory.SpawnOwned(projectile, (Vector2)transform.position + new Vector2(0f, 8f), src, start + i * 360f / count);
        }
    }
}
