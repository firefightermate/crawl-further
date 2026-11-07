using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A seed on the floor. It ripens into a pod over <see cref="growTime"/> s (its Life anim lasts as long) and a ripe pod
    /// bursts when the hero comes within <see cref="triggerRadius"/> px (40 px while the hero is dusted with pollen). The
    /// orchard works on it: a Sporeling tends it (ripens twice as fast), a Spore Husk shakes it loose, a Nightshade hides
    /// it, and the seeds of one Sower pass share a furrow: they ripen together and burst together.
    /// </summary>
    public class SeedFx : Registered<SeedFx>
    {
        public float growTime = 2.5f;
        public float triggerRadius = 20f;
        /// <summary>The furrow this seed belongs to (0: none).</summary>
        public int furrow;

        const float ShimmerRange = 30f;

        float m_age, m_tendUntil, m_hiddenUntil, m_shakeUntil;
        bool m_burst, m_shaking;
        Vector3 m_rest;
        exSprite m_sprite;
        exSpriteAnimation m_anim;
        GameObject m_shimmer;

        public bool Ripe { get { return m_age >= growTime; } }
        public bool Hidden { get { return Time.time < m_hiddenUntil; } }

        void Awake()
        {
            m_sprite = GetComponent<exSprite>();
            m_anim = GetComponent<exSpriteAnimation>();
        }

        protected override void OnEnable()
        {
            base.OnEnable();
            m_age = 0f; m_tendUntil = 0f; m_hiddenUntil = 0f; m_shaking = false; m_burst = false; furrow = 0;
            SetAlpha(1f);
        }

        protected override void OnDisable()
        {
            base.OnDisable();
            DropShimmer();
        }

        void Update()
        {
            if (m_burst) return;
            float rate = Time.time < m_tendUntil ? 2f : 1f;
            if (!Ripe) m_age += Time.deltaTime * rate;
            // the Life anim keeps pace with the ripening; the Ripe loop (how long the pod lasts) always plays at 1x
            var st = m_anim != null ? m_anim.GetCurrentAnimation() : null;
            if (st != null) st.speed = Ripe ? 1f : rate;
            if (m_shaking)
            {
                transform.position = m_rest + new Vector3((Time.frameCount / 2) % 2 == 0 ? 0.6f : -0.6f, 0f, 0f);
                if (Time.time >= m_shakeUntil) { transform.position = m_rest; Burst(); }
                return;
            }
            UpdateHidden();
            if (!Ripe) return;
            var hero = ModUtil.Hero();
            float r = Orchard.HeroDusted ? Mathf.Max(triggerRadius, Orchard.DustedRadius) : triggerRadius;
            if (hero != null && ((Vector2)hero.transform.position - Pos).sqrMagnitude < r * r) Burst();
        }

        /// <summary>Ripen twice as fast for the next <paramref name="seconds"/> (a Sporeling is tending it).</summary>
        public void Tend(float seconds) { m_tendUntil = Mathf.Max(m_tendUntil, Time.time + seconds); }

        /// <summary>Start ripening again from a fresh seed (the seeds of one furrow ripen together).</summary>
        public void Replant()
        {
            if (m_burst) return;
            m_age = 0f;
            var st = m_anim != null ? m_anim.GetCurrentAnimation() : null;
            if (st != null && st.clip != null) m_anim.Play(st.clip, 0);
        }

        /// <summary>Unseen for <paramref name="seconds"/> (Nightshade): only a faint shimmer shows, and only up close.</summary>
        public void Hide(float seconds)
        {
            m_hiddenUntil = Mathf.Max(m_hiddenUntil, Time.time + seconds);
            SetAlpha(0f);
        }

        /// <summary>Shake for <paramref name="seconds"/>, then burst, ripe or not (the Spore Husk's smash).</summary>
        public void ShakeLoose(float seconds)
        {
            if (m_burst || m_shaking) return;
            m_shaking = true;
            m_rest = transform.position;
            m_shakeUntil = Time.time + seconds;
            m_hiddenUntil = 0f;
            SetAlpha(1f);
            DropShimmer();
        }

        /// <summary>Pick it off the floor without bursting it (the Strangler's lasso). Returns whether it was ripe.</summary>
        public bool Pluck()
        {
            bool ripe = Ripe;
            if (m_burst) return false;
            m_burst = true;
            All.Remove(this);
            SystemPool.Despawn(gameObject);
            return ripe;
        }

        /// <summary>Burst into a spore pod cloud (the whole furrow goes with it).</summary>
        public void Burst()
        {
            if (m_burst) return;
            m_burst = true;
            if (m_shaking) transform.position = m_rest;
            var src = FxFactory.SourceOf(gameObject);
            if (SylveneFx.PodBurstBig != null) FxFactory.SpawnOwned(SylveneFx.PodBurstBig, Pos, src);
            Orchard.PodBurst(Pos);
            int f = furrow;
            All.Remove(this);
            SystemPool.Despawn(gameObject);
            if (f != 0) Orchard.BurstFurrow(f);
        }

        void UpdateHidden()
        {
            if (!Hidden)
            {
                if (m_sprite != null && m_sprite.color.a < 1f) SetAlpha(1f);
                DropShimmer();
                return;
            }
            var hero = ModUtil.Hero();
            bool near = hero != null && ((Vector2)hero.transform.position - Pos).sqrMagnitude < ShimmerRange * ShimmerRange;
            if (near && m_shimmer == null && SylveneFx.Shimmer != null) m_shimmer = ModAttach.Spawn(SylveneFx.Shimmer, gameObject, new Vector2(0f, 2f));
            else if (!near) DropShimmer();
        }

        void DropShimmer()
        {
            if (m_shimmer == null) return;
            ModAttach.Drop(m_shimmer, gameObject);
            m_shimmer = null;
        }

        void SetAlpha(float a)
        {
            if (m_sprite != null) m_sprite.color = new Color(1f, 1f, 1f, a);
        }
    }
}
