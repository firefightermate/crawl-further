using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Candle Wyrm, Closing Ring: Wick Coil races a full circle round the hero (radius <see cref="Radius"/>) in
    /// <see cref="Lap"/> s, laying lit wax. The unfinished arc is the way out. When the ring closes it glows white for
    /// <see cref="Warn"/> s, then tightens to the centre over <see cref="Tighten"/> s. It still swims in wax.
    /// </summary>
    public class WyrmCoil : WaxSwimmer
    {
        public const float Radius = 34f, Lap = 1.2f, Warn = 0.3f, Tighten = 0.6f, FlameEvery = 20f;
        /// <summary>Set by the kit: the racing coil, and the Wyrm's own swim stance.</summary>
        public static exSpriteAnimClip CoilLoop, WyrmSwim, WyrmSwimRun;
        readonly List<GameObject> m_ring = new List<GameObject>();

        protected override exSpriteAnimClip SwimIdleClip { get { return WyrmSwim; } }
        protected override exSpriteAnimClip SwimRunClip { get { return WyrmSwimRun; } }

        bool m_coiling;

        protected override void OnDisable()
        {
            m_ring.Clear();
            // put away mid-coil (the coroutine is gone): the pooled body must not keep its collision off
            if (m_coiling && Body != null) Body.AnimCollideOn();
            m_coiling = false;
            base.OnDisable();
        }

        /// <summary>Clip event: begin the coil round where the hero stands now.</summary>
        public void VhCoil()
        {
            if (!Alive) return;
            Surface();
            StopAllCoroutines();
            StartCoroutine(Coil(HeroPos));
        }

        IEnumerator Coil(Vector2 centre)
        {
            m_ring.Clear();
            var src = Own;
            float a0 = AngleOf(Me - centre);
            float dir = Random.value < 0.5f ? 1f : -1f;
            SendMessage("AnimCollideOff", SendMessageOptions.DontRequireReceiver);
            m_coiling = true;
            Hold(CoilLoop, Lap + 0.1f);
            float t = 0f, laid = -FlameEvery;
            while (t < Lap && Alive)
            {
                t += Time.deltaTime;
                float a = a0 + dir * 360f * Mathf.Clamp01(t / Lap);
                var p = centre + new Vector2(Mathf.Cos(a * Mathf.Deg2Rad) * Radius, Mathf.Sin(a * Mathf.Deg2Rad) * Radius * 0.7f);
                ModUtil.Teleport(gameObject, ModUtil.SafePoint(centre, p));
                if (Mathf.Abs(a - a0) - laid >= FlameEvery && VhorrulFx.CoilFlame != null)
                {
                    laid += FlameEvery;
                    var f = FxFactory.SpawnOwned(VhorrulFx.CoilFlame, transform.position, src);
                    if (f != null) m_ring.Add(f);
                }
                yield return null;
            }
            SendMessage("AnimCollideOn", SendMessageOptions.DontRequireReceiver);
            m_coiling = false;
            if (!Alive) yield break;
            Monster.Face(centre);
            foreach (var f in m_ring) if (f != null && f.activeInHierarchy) { var c = f.GetComponent<VhCoilFx>(); if (c != null) c.Glow(); }
            yield return new WaitForSeconds(Warn);
            foreach (var f in m_ring) if (f != null && f.activeInHierarchy) { var c = f.GetComponent<VhCoilFx>(); if (c != null) c.Close(centre, Tighten, src); }
            m_ring.Clear();
        }
    }
}
