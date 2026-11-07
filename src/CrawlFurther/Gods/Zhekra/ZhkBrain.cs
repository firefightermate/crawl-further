using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The god's perk on every Zhekra monster (and larva): the swarm buff (any other monster within 64 px, or a Marked hero
    /// within 80 px), the scent trail (1.3x on a Marked hero's prints), and the clip events every Zhekra body can call
    /// (acid rain, the frenzy call). Added in Patch_ZhekraAwake; it also keeps the live list of the brood.
    /// </summary>
    public class ZhkBrain : Registered<ZhkBrain>
    {
        public const float SwarmRadius = 64f, MarkRadius = 80f, FrenzyRadius = 110f, PrintRadius = 6f;
        Player m_player;
        Health m_health;
        float m_tick;

        void Awake() { m_player = GetComponent<Player>(); m_health = GetComponent<Health>(); }

        protected override void OnEnable() { base.OnEnable(); m_tick = Random.Range(0f, 0.25f); }

        public bool Alive { get { return m_health != null && m_health.IsAlive() && !ModUtil.IsGhost(m_player); } }

        /// <summary>True for the Hive Larva (fodder that hatches from the dead).</summary>
        public bool IsLarva { get { return ModUtil.PrefabName(gameObject) == ZhekraPack.Larva.PrefabName; } }

        DamageSource OwnSource()
        {
            var pd = m_player != null ? R.Get<PlayerData>(m_player, "m_playerData") : null;
            return new DamageSource(gameObject, gameObject, pd);
        }

        // one shared scan of the scene's players per 0.25 s for every brain
        static Player[] s_players = new Player[0];
        static float s_scanAt = -1f;
        static Player[] Players()
        {
            if (Time.time - s_scanAt >= 0.25f || Time.time < s_scanAt) { s_players = FindObjectsOfType<Player>(); s_scanAt = Time.time; }
            return s_players;
        }

        void Update()
        {
            if (!Alive) return;
            m_tick -= Time.deltaTime;
            if (m_tick > 0f) return;
            m_tick = 0.25f;
            Vector2 me = transform.position;
            var hero = ModUtil.Hero();
            // any other living monster counts (each player has one body at a time: requiring Zhekra kin almost never fired)
            bool swarm = false;
            foreach (var o in Players())
            {
                if (o == null || o.gameObject == gameObject || o.gameObject == hero || ModUtil.IsGhost(o)) continue;
                if (((Vector2)o.transform.position - me).sqrMagnitude > SwarmRadius * SwarmRadius) continue;
                var h = o.GetComponent<Health>();
                if (h == null || !h.IsAlive()) continue;
                swarm = true;
                break;
            }
            bool marked = hero != null && ZhkBehaviour.HeroMarked();
            if (marked && ((Vector2)hero.transform.position - me).sqrMagnitude <= MarkRadius * MarkRadius) swarm = true;
            if (swarm && ZhekraFx.Swarm != null && m_player != null) m_player.AddStatus(ZhekraFx.Swarm, OwnSource(), "zhkswarm");
            // the scent trail: a Marked hero's prints speed up any Zhekra walking on them
            if (ZhekraFx.Trail != null && m_player != null && ZhkPrintFx.Nearest(me, PrintRadius) != null)
                m_player.AddStatus(ZhekraFx.Trail, OwnSource(), "zhktrail");
        }

        /// <summary>Frenzy: faster and quicker to attack for 4 s.</summary>
        public void Frenzy(DamageSource src, float seconds = 0f)
        {
            if (!Alive || ZhekraFx.Frenzy == null || m_player == null) return;
            m_player.AddStatus(ZhekraFx.Frenzy, src, "zhkfrenzy");
        }

        /// <summary>Heal by <paramref name="amount"/> with the heal burst.</summary>
        public void Mend(float amount)
        {
            if (!Alive) return;
            m_health.Heal(amount);
            ModInd.Heal(gameObject);
            if (ZhekraFx.Mend != null) SystemPool.Spawn(ZhekraFx.Mend, Pos);
        }

        // ------------------------------------------------------------- clip events
        /// <summary>Brood Mother Rain (frame 3): three acid splats on and beside the hero, a beat apart.</summary>
        public void ZhkAcidRain()
        {
            var hero = ModUtil.Hero();
            if (hero == null || ZhekraFx.AcidRain == null || !Alive) return;
            if (((Vector2)hero.transform.position - Pos).sqrMagnitude > 240f * 240f) return;
            StartCoroutine(Rain(hero));
        }

        System.Collections.IEnumerator Rain(GameObject hero)
        {
            var src = OwnSource();
            float a = Random.Range(0f, 360f);
            for (int i = 0; i < 3; i++)
            {
                if (hero == null || !Alive) yield break;
                Vector2 hp = hero.transform.position;
                Vector2 off = i == 0 ? Vector2.zero : (Vector2)(Quaternion.Euler(0, 0, a + i * 150f) * Vector2.right) * 20f;
                FxFactory.SpawnOwned(ZhekraFx.AcidRain, ModUtil.SafePoint(hp, hp + off), src);
                yield return new WaitForSeconds(0.15f);
            }
        }

        /// <summary>Brood Mother Call (frame 2): she and every other monster within 110 px (any god, larvae, minions) frenzy.</summary>
        public void ZhkFrenzyCall()
        {
            if (!Alive) return;
            var src = OwnSource();
            Frenzy(src);
            var hero = ModUtil.Hero();
            foreach (var o in Players())
            {
                if (o == null || o.gameObject == gameObject || o.gameObject == hero || ModUtil.IsGhost(o)) continue;
                if (((Vector2)o.transform.position - Pos).sqrMagnitude > FrenzyRadius * FrenzyRadius) continue;
                var h = o.GetComponent<Health>();
                if (h == null || !h.IsAlive() || ZhekraFx.Frenzy == null) continue;
                o.AddStatus(ZhekraFx.Frenzy, src, "zhkfrenzy");
            }
        }
    }
}
