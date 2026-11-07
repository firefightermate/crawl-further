using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Carrion Queen, Drone: every <see cref="Period"/> s a ring of sound rolls out from her to <see cref="Radius"/> px and
    /// dazes a hero its edge passes over. Tell: her wings blur for <see cref="Warn"/> s before (IdleBlur / RunBlur), and the
    /// ring itself. Up close, inside the ring's start, the hero is never caught.
    /// </summary>
    public class QueenDrone : SylveneBehaviour
    {
        public const float Period = 2.5f, Warn = 0.3f, Radius = 50f, Roll = 0.42f, Start = 8f;
        /// <summary>The blurring wings (set by the kit).</summary>
        public static exSpriteAnimClip BlurIdle, BlurRun;

        float m_clock;
        bool m_warned;

        protected override void OnEnable() { base.OnEnable(); m_clock = 0f; m_warned = false; }

        void Update()
        {
            if (!Alive) return;
            m_clock += Time.deltaTime;
            if (!m_warned && m_clock >= Period - Warn) { m_warned = true; SetStance(BlurIdle, BlurRun); }
            if (m_clock < Period) return;
            m_clock = 0f; m_warned = false;
            SetStance(null, null);
            StartCoroutine(Ring());
        }

        IEnumerator Ring()
        {
            Vector2 c = Me;
            if (SylveneFx.DroneRing != null) SystemPool.Spawn(SylveneFx.DroneRing, c);
            bool caught = false;
            float t = 0f;
            while (t < Roll && !caught)
            {
                t += Time.deltaTime;
                float r = Mathf.Lerp(Start, Radius, t / Roll);
                var hero = ModUtil.Hero();
                if (hero != null)
                {
                    // the ring lies flat on the floor: half as tall as it is wide
                    Vector2 d = (Vector2)hero.transform.position - c;
                    float e = Mathf.Sqrt(d.x * d.x + 4f * d.y * d.y);
                    if (e > Start && Mathf.Abs(e - r) < 6f)
                    {
                        caught = true;
                        var hp = hero.GetComponent<Player>();
                        if (hp != null && ModStatus.Daze != null) hp.AddStatus(ModStatus.Daze, Own, "syldrone");
                    }
                }
                yield return null;
            }
        }
    }
}
