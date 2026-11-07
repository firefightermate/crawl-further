using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Util;

    /// <summary>
    /// Marionette, Mirror Step: for <see cref="MirrorTime"/> s after Strings it is the hero's reflection: it moves as the
    /// hero moves, mirrored across the line between them (the hero steps left, it steps right; the hero steps in, it steps
    /// in). Tell: its strings burn violet and its head tilts (the Mirror idle and run).
    /// </summary>
    public class MarionetteMirror : JinxBehaviour
    {
        public const float MirrorTime = 2.5f;
        /// <summary>The mirror stance (set by the kit).</summary>
        public static exSpriteAnimClip MirrorIdle, MirrorRun;

        float m_until;

        protected override void OnEnable() { base.OnEnable(); m_until = 0f; }

        /// <summary>Clip event (end of Strings): start mirroring.</summary>
        public void ModJinxMirror()
        {
            if (!Alive) return;
            m_until = Time.time + MirrorTime;
            SetStance(MirrorIdle, MirrorRun);
        }

        void Update()
        {
            if (m_until <= 0f) return;
            var hero = ModUtil.Hero();
            if (!Alive || Time.time >= m_until || hero == null)
            {
                m_until = 0f;
                Steer(null);
                SetStance(null, null);
                return;
            }
            var hm = hero.GetComponent<PlayerMovement>();
            if (hm == null) return;
            Vector2 v = hm.GetVelocity();
            float top = Mathf.Max(20f, hm.GetSpeedMax());
            Vector2 n = Me - (Vector2)hero.transform.position;
            n = n.sqrMagnitude > 0.01f ? n.normalized : Vector2.right;
            Vector2 m = v - 2f * Vector2.Dot(v, n) * n;
            Steer(m.sqrMagnitude > 25f ? m / top : Vector2.zero);
        }
    }
}
