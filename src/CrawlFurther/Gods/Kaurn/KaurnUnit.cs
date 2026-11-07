using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Every Kaurn monster's static charge and its place in the arc network. A basic attack (clip event KrnCharge) stores a
    /// spark, up to <see cref="maxPips"/>, shown as a bolt meter over the head and crackles on the body; the special
    /// (KrnDischarge) fires every stored spark at the hero (0.4 each).
    /// </summary>
    public class KaurnUnit : Registered<KaurnUnit>
    {
        public static readonly Dictionary<string, float> BodyHeight = new Dictionary<string, float>
        {
            { "ModKrnRivetImp", 8f }, { "ModKrnSparkBeetle", 6f }, { "ModKrnCoilWisp", 9f }, { "ModKrnAnvilSmith", 13f },
            { "ModKrnStormcaller", 13f }, { "ModKrnForgeColossus", 22f }, { "ModKrnStormHerald", 22f },
            { "ModKrnLodeHound", 11f }, { "ModKrnLeydenGolem", 12f }, { "ModKrnThunderBull", 16f }, { "ModKrnStormOrrery", 23f },
            { "ModKrnWireGremlin", 13f }, { "ModKrnArcLantern", 12f }, { "ModKrnForgemaster", 24f }, { "ModKrnWireWyvern", 18f },
            { "ModKrnFuseSapper", 14f }, { "ModKrnPolarityWarg", 14f }, { "ModKrnScarabMagus", 20f }, { "ModKrnVoltaicPile", 22f },
            { "ModKrnTeslaSpire", 30f }, { "ModKrnStaticMoth", 20f },
        };
        public const int MaxPips = 3;
        public const float SparkDamageSpread = 16f;

        public int pips;
        /// <summary>Sparks it can hold (the Leyden Golem's jar holds 6).</summary>
        public int maxPips = MaxPips;
        /// <summary>How far its arcs reach (the Coil Wisp's relay reaches 110).</summary>
        public float linkRange = KaurnConduction.Range;
        /// <summary>Show the 3-slot bolt meter over the head (off where the art shows the charge itself).</summary>
        public bool showMeter = true;
        public float height = 8f;
        Player m_player;
        Health m_health;
        exSprite m_sprite;
        float m_crackle;
        int m_shown;

        /// <summary>The art's feet (the sprite is offset from the transform; feet = cell bottom + 2).</summary>
        public Vector2 FeetPos { get { return (Vector2)transform.position + new Vector2(0f, m_sprite != null ? m_sprite.offset.y + 2f : 0f); } }
        public Vector2 Top { get { return FeetPos + new Vector2(0f, height); } }

        void Awake()
        {
            m_player = GetComponent<Player>();
            m_health = GetComponent<Health>();
            m_sprite = GetComponent<exSprite>();
            float h;
            if (BodyHeight.TryGetValue(ModUtil.PrefabName(gameObject), out h)) height = h;
        }

        protected override void OnEnable()
        {
            base.OnEnable();
            pips = 0; m_shown = 0; m_crackle = 0f;
            KaurnConduction.Ensure();
        }

        public bool Alive { get { return m_health != null && m_health.IsAlive() && isActiveAndEnabled; } }

        public DamageSource OwnSource()
        {
            var pd = m_player != null ? R.Get<PlayerData>(m_player, "m_playerData") : null;
            return new DamageSource(gameObject, gameObject, pd);
        }

        void ShowPips()
        {
            int n = Alive && showMeter ? Mathf.Clamp(pips, 0, MaxPips) : 0;
            if (n == m_shown) return;
            m_shown = n;
            ModInd.Charge(gameObject, n);
        }

        void Update()
        {
            ShowPips();
            if (pips <= 0 || !Alive) return;
            m_crackle -= Time.deltaTime;
            if (m_crackle > 0f) return;
            m_crackle = Mathf.Max(0.12f, 0.55f - pips * 0.12f);
            Pop();
        }

        /// <summary>A crackle somewhere on the body.</summary>
        public void Pop()
        {
            if (KaurnFx.Crackle == null) return;
            var at = FeetPos + new Vector2(Random.Range(-0.45f, 0.45f) * height, Random.Range(0.4f, 1.5f) * height);
            ModAttach.Front(SystemPool.Spawn(KaurnFx.Crackle, at), gameObject);
        }

        /// <summary>Store <paramref name="n"/> sparks (up to the cap).</summary>
        public void Store(int n)
        {
            pips = Mathf.Min(maxPips, pips + n);
            Pop();
        }

        /// <summary>Clip event on a basic attack's hit or release frame.</summary>
        public void KrnCharge() { Store(1); }

        /// <summary>Clip event on the special's release frame: every stored spark flies at the hero.</summary>
        public void KrnDischarge()
        {
            int n = pips;
            pips = 0;
            var hero = ModUtil.Hero();
            if (n <= 0 || hero == null || KaurnFx.StaticSpark == null) return;
            var from = Top;
            float baseAng = KaurnFx.Angle(from, KaurnFx.HeroChest(hero));
            var src = OwnSource();
            for (int i = 0; i < n; i++)
                FxFactory.SpawnOwned(KaurnFx.StaticSpark, from, src, baseAng + (i - (n - 1) * 0.5f) * SparkDamageSpread);
        }
    }
}
