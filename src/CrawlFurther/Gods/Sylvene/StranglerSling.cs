using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Strangler Vine, Sling: its lasso catches the nearest pod or seed within <see cref="Reach"/> px, whirls it overhead
    /// (the tell) and slings it at the hero: a ripe pod bursts on him, a seed lands at his feet. With nothing near, the
    /// special is a plain lash at the hero instead (the Lash clip).
    /// </summary>
    public class StranglerSling : SylveneBehaviour
    {
        public const float Reach = 50f;
        static readonly Vector2 Release = new Vector2(17f, 19f);
        /// <summary>The two specials (set by the kit).</summary>
        public static exSpriteAnimClip LassoClip, LashClip;

        bool m_ripe, m_caught;

        protected override void OnEnable() { base.OnEnable(); m_caught = false; }

        void Update()
        {
            if (!Alive || InAttack) return;
            SetSpecialClip(Nearest() != null ? LassoClip : LashClip);
        }

        SeedFx Nearest() { return SeedFx.Nearest(Me, Reach); }

        /// <summary>Clip event: the loop closes on the nearest pod or seed.</summary>
        public void ModSylCatch()
        {
            var s = SeedFx.Nearest(Me, Reach + 10f);
            m_caught = s != null;
            m_ripe = m_caught && s.Pluck();
        }

        /// <summary>Clip event (Lash): nothing was near, so the loop cracks at the hero.</summary>
        public void ModSylLash() { m_caught = false; ModSylSling(); }

        /// <summary>Clip event: let go. Without a catch the loop lashes at the hero.</summary>
        public void ModSylSling()
        {
            if (!Alive) return;
            Vector2 from = Me + new Vector2(Release.x * Side, Release.y);
            Vector2 at = HeroPos;
            float ang = AngleTo(from, at);
            if (!m_caught)
            {
                if (SylveneFx.LassoLash != null) FxFactory.SpawnOwned(SylveneFx.LassoLash, from, Own, AngleTo(Me + new Vector2(0f, 8f), at));
                return;
            }
            var t = m_ripe ? SylveneFx.PodSling : SylveneFx.SeedSling;
            var go = t != null ? FxFactory.SpawnOwned(t, from, Own, ang) : null;
            // it flies just as far as the hero stands, so a seed lands at his feet
            var e = go != null ? go.GetComponent<Effect>() : null;
            if (e != null) R.Set(e, "m_destroyAfterTime", Mathf.Clamp((at - from).magnitude / 190f, 0.08f, 0.9f));
            m_caught = false;
        }
    }
}
