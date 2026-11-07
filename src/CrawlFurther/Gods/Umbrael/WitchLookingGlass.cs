using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Mirror Witch, Looking-Glass: Standing Mirror sets a pane between her and the hero for 5 s. Her bolts that reach it
    /// bounce off it toward the hero; his shots that hit its face bounce back the way they came. Tell: the pane catching
    /// the light (its Flash anim) on every bounce.
    /// </summary>
    public class WitchLookingGlass : UmbraelBehaviour
    {
        /// <summary>How far in front of her the pane stands (at most half the way to the hero).</summary>
        public const float Reach = 28f;

        /// <summary>Clip event: set the pane.</summary>
        public void ModUmbStandingMirror()
        {
            if (UmbraelFx.Pane == null) return;
            var to = HeroPos - Me;
            float d = Mathf.Min(Reach, to.magnitude * 0.5f);
            var at = ModUtil.SafePoint(Me, Me + (to.sqrMagnitude > 1f ? to.normalized : Face) * d, 4f);
            FxFactory.SpawnOwned(UmbraelFx.Pane, at, Own);
        }
    }

    /// <summary>Marks a Mirror Witch bolt (and its echo) so a pane knows to turn it.</summary>
    public class WitchBoltFx : Registered<WitchBoltFx>
    {
        public readonly List<MirrorPaneFx> bounced = new List<MirrorPaneFx>();
        protected override void OnEnable() { base.OnEnable(); bounced.Clear(); }
    }

    /// <summary>A standing mirror pane (see <see cref="WitchLookingGlass"/>).</summary>
    public class MirrorPaneFx : Registered<MirrorPaneFx>
    {
        /// <summary>Half the pane's width, and the height of the glass above the floor.</summary>
        public const float HalfWidth = 8f, GlassTop = 18f;
        readonly List<ParticleMotion> m_near = new List<ParticleMotion>();
        readonly HashSet<ParticleMotion> m_turned = new HashSet<ParticleMotion>();
        float m_flashUntil;

        public void Arm() { m_turned.Clear(); m_flashUntil = 0f; }

        protected override void OnEnable() { base.OnEnable(); Arm(); }

        bool OnGlass(Vector2 p)
        {
            var d = p - Pos;
            return Mathf.Abs(d.x) <= HalfWidth && d.y >= -3f && d.y <= GlassTop;
        }

        void Flash()
        {
            if (UmbraelFx.PaneFlash == null || Time.time < m_flashUntil) return;
            SystemPool.Spawn(UmbraelFx.PaneFlash, Pos);
            m_flashUntil = Time.time + 0.2f;
        }

        void Update()
        {
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 chest = (Vector2)hero.transform.position + new Vector2(0f, 8f);
            // her bolts: turned toward the hero, once per pane
            for (int i = 0; i < WitchBoltFx.All.Count; i++)
            {
                var b = WitchBoltFx.All[i];
                if (b == null || b.bounced.Contains(this) || !OnGlass(b.Pos)) continue;
                b.bounced.Add(this);
                HeroShots.Turn(b.GetComponent<ParticleMotion>(), chest - b.Pos);
                Flash();
            }
            // his shots: back the way they came
            HeroShots.Near(Pos + new Vector2(0f, GlassTop * 0.5f), GlassTop, m_near);
            foreach (var pm in m_near)
            {
                if (m_turned.Contains(pm) || !OnGlass(pm.transform.position)) continue;
                m_turned.Add(pm);
                HeroShots.Turn(pm, -pm.GetVelocity());
                Flash();
            }
        }
    }
}
