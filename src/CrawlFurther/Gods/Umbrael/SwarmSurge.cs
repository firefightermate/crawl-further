using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Glitterswarm, Echoed Surge: Surge rushes through the hero along a line it steers, biting three times; 0.6 s after
    /// it, a glass ghost of the swarm runs the same path again at half damage, so a hero who dodged back into the line is
    /// caught. Tell: moths left glinting along the path.
    /// </summary>
    public class SwarmSurge : UmbraelBehaviour
    {
        public const float Echo = 0.6f, GlintStep = 9f;
        readonly List<Vector2> m_path = new List<Vector2>();
        float m_start;
        bool m_surging;

        protected override void OnEnable() { base.OnEnable(); m_surging = false; }

        /// <summary>Clip event: the rush begins.</summary>
        public void ModUmbSurgeStart() { m_path.Clear(); m_path.Add(Me); m_start = Time.time; m_surging = true; }

        /// <summary>Clip event: the rush ends; the ghost follows.</summary>
        public void ModUmbSurgeEnd()
        {
            if (!m_surging) return;
            m_surging = false;
            m_path.Add(Me);
            StartCoroutine(Ghost(new List<Vector2>(m_path), Mathf.Max(0.15f, Time.time - m_start)));
        }

        void Update()
        {
            if (!m_surging) return;
            if ((Me - m_path[m_path.Count - 1]).sqrMagnitude < GlintStep * GlintStep) return;
            m_path.Add(Me);
            if (UmbraelFx.SwarmGlint != null) SystemPool.Spawn(UmbraelFx.SwarmGlint, Me);
        }

        IEnumerator Ghost(List<Vector2> path, float length)
        {
            yield return new WaitForSeconds(Echo);
            if (!Alive || path.Count < 2) yield break;
            var src = Own;
            var ghost = UmbraelFx.SwarmGhost != null ? SystemPool.Spawn(UmbraelFx.SwarmGhost, path[0]) : null;
            int bites = 0;
            for (float t = 0f; t <= length; t += Time.deltaTime)
            {
                float u = t / length * (path.Count - 1);
                int i = Mathf.Min(path.Count - 2, (int)u);
                var p = Vector2.Lerp(path[i], path[i + 1], u - i);
                if (ghost != null) ghost.transform.position = new Vector3(p.x, p.y, ghost.transform.position.z);
                if (UmbraelFx.GhostBite != null && t / length >= bites / 3f && bites < 3) { FxFactory.SpawnOwned(UmbraelFx.GhostBite, p, src); bites++; }
                yield return null;
            }
            if (ghost != null && ghost.activeInHierarchy) SystemPool.Despawn(ghost);
        }
    }
}
