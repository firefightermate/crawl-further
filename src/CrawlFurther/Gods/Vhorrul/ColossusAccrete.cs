using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Tallow Colossus, Accrete: walking over unlit wax soaks it up, one layer per puddle (up to <see cref="MaxLayers"/>).
    /// Each layer makes it bigger (its layered stances), adds <see cref="FistPerLayer"/> to its fists and 10 px to Topple.
    /// Fire under it, or a burning hit, melts a layer off as a burning pool. Topple rears over a body-shaped shadow (as long
    /// as the fall), lands flat on its face, lies a second taking +25 % damage (Prone) and leaves a wax slick.
    /// </summary>
    public class ColossusAccrete : VhorrulBehaviour
    {
        public const int MaxLayers = 3;
        public const float FistPerLayer = 0.1f, SoakRange = 10f, MeltCooldown = 1f;
        /// <summary>Set by the kit: the stance per layer count (index 0 = none), and the Topple hit slot per layer.</summary>
        public static exSpriteAnimClip[] Idles = new exSpriteAnimClip[4], Runs = new exSpriteAnimClip[4];
        public static int[] ToppleSlots = new int[0];
        int m_layers;
        float m_melt, m_t;

        public int Layers { get { return m_layers; } }

        protected override void OnEnable() { base.OnEnable(); m_layers = 0; m_melt = 0f; }

        void Update()
        {
            if (!Alive) return;
            m_melt -= Time.deltaTime;
            m_t -= Time.deltaTime;
            if (m_t > 0f) return;
            m_t = 0.1f;
            if (m_layers > 0 && m_melt <= 0f && FireNear(SoakRange) != null) { MeltOne(); return; }
            if (m_layers >= MaxLayers || InAttack) return;
            var w = WaxPuddleFx.Nearest(Me, SoakRange, x => !x.heroOwned);
            if (w == null) return;
            WaxPuddleFx.All.Remove(w);
            SystemPool.Despawn(w.gameObject);
            SetLayers(m_layers + 1);
        }

        void SetLayers(int n)
        {
            m_layers = Mathf.Clamp(n, 0, MaxLayers);
            SetStance(m_layers > 0 ? Idles[m_layers] : null, m_layers > 0 ? Runs[m_layers] : null);
        }

        void MeltOne()
        {
            m_melt = MeltCooldown;
            SetLayers(m_layers - 1);
            if (VhorrulFx.BurningPool != null) FxFactory.SpawnOwned(VhorrulFx.BurningPool, Me, Own);
        }

        /// <summary>Clip event (Topple rears): the body-shaped shadow, as long as this fall will be.</summary>
        public void VhToppleShadow()
        {
            if (VhorrulFx.ToppleShadow == null) return;
            var s = FxFactory.SpawnOwned(VhorrulFx.ToppleShadow, Me + new Vector2(0f, 1f), Own, AngleOf(Face));
            var anim = s != null ? s.GetComponent<exSpriteAnimation>() : null;
            var clip = m_layers < VhorrulFx.ShadowLengths.Length ? VhorrulFx.ShadowLengths[m_layers] : null;
            if (anim != null && clip != null) { if (anim.GetAnimation(clip.name) == null) anim.AddAnimation(clip); anim.Play(clip.name); }
        }

        /// <summary>Clip event (Topple lands): the hit along its length, the lunge onto its face, Prone, the wax slick.</summary>
        public void VhToppleLand()
        {
            if (!Alive) return;
            float len = 28f + 10f * m_layers;
            var face = Face;
            if (m_layers < ToppleSlots.Length) Attack(ToppleSlots[m_layers]);
            CrawlFurther.Util.ModUtil.Teleport(gameObject, CrawlFurther.Util.ModUtil.SafePoint(Me, Me + face * (len - 14f)));
            AddStatus(VhorrulFx.Prone, "vhprone");
            if (VhorrulFx.WaxPuddle == null) return;
            for (float d = -len + 14f; d <= -12f; d += 12f) FxFactory.SpawnOwned(VhorrulFx.WaxPuddle, Me + face * d, Own);
        }

        public override void OnHitHero(DamageInfo d)
        {
            if (From(d, VhorrulFx.ColossusFist)) d.m_amount += FistPerLayer * m_layers;
        }

        public override void OnHeroHit(DamageInfo d)
        {
            if (m_layers > 0 && m_melt <= 0f && IsFire(d)) MeltOne();
        }
    }
}
