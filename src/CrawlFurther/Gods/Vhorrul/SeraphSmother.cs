using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Ashen Seraph, Smother: Ash to Ash beats every fire within <see cref="Range"/> px out for good (no wax, no slick):
    /// smoke rises off each, and each rises again as an ash cloud that drifts at the hero for 3 s and dazes him.
    /// </summary>
    public class SeraphSmother : VhorrulBehaviour
    {
        public const float Range = 50f;
        public const int MaxClouds = 5;

        /// <summary>Clip event (the wings flare white).</summary>
        public void VhSmother()
        {
            if (!Alive) return;
            int n = 0;
            foreach (var f in IgniterFx.Snapshot())
            {
                var pm = f != null ? f.GetComponent<ParticleMotion>() : null;
                if (f == null || !f.isActiveAndEnabled || (pm != null && pm.enabled)) continue;   // floor fires only, not bolts in flight
                if ((f.Pos - Me).sqrMagnitude > Range * Range) continue;
                Vector2 p = f.Pos;
                IgniterFx.All.Remove(f);
                SystemPool.Despawn(f.gameObject);      // a plain despawn spawns nothing: the fire is simply gone
                if (VhorrulFx.Smother != null) FxFactory.SpawnOwned(VhorrulFx.Smother, p, Own);
                if (n++ < MaxClouds && VhorrulFx.AshCloud != null) FxFactory.SpawnOwned(VhorrulFx.AshCloud, p, Own);
            }
        }
    }
}
