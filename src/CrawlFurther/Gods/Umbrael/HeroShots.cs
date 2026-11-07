using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The hero's projectiles in flight (bolts, thrown blades), for the monsters that turn, catch or stop them: the Mirror
    /// Witch's pane, the Argus Moth's wings and the Pendulum's ring of slowed time.
    /// </summary>
    public static class HeroShots
    {
        static readonly List<ParticleMotion> s_live = new List<ParticleMotion>();

        /// <summary>Subscribed to MonsterEvents.AttackSpawned by <see cref="UmbraelPack"/>.</summary>
        public static void OnAttackSpawned(Player owner, GameObject fx, GameObject template)
        {
            if (owner == null || fx == null || owner.gameObject != ModUtil.Hero()) return;
            var pm = fx.GetComponent<ParticleMotion>();
            if (pm != null && pm.enabled && !s_live.Contains(pm)) s_live.Add(pm);
        }

        /// <summary>Hero shots in flight now (or held still) within <paramref name="r"/> px of <paramref name="p"/>.</summary>
        public static void Near(Vector2 p, float r, List<ParticleMotion> into)
        {
            into.Clear();
            var hero = ModUtil.Hero();
            for (int i = s_live.Count - 1; i >= 0; i--)
            {
                var pm = s_live[i];
                if (pm == null || !pm.gameObject.activeInHierarchy) { s_live.RemoveAt(i); continue; }
                var src = FxFactory.SourceOf(pm.gameObject);
                if (src == null || src.m_sourceOwner != hero) { s_live.RemoveAt(i); continue; }   // pooled and reused elsewhere
                if (((Vector2)pm.transform.position - p).sqrMagnitude <= r * r) into.Add(pm);
            }
        }

        /// <summary>Send a shot along <paramref name="dir"/>.</summary>
        public static void Turn(ParticleMotion pm, Vector2 dir)
        {
            if (pm == null || dir.sqrMagnitude < 0.0001f) return;
            pm.SetDirection(dir.normalized);
            pm.SetDirection(dir.normalized);   // the first call turns the sprite to the old velocity
        }
    }
}
