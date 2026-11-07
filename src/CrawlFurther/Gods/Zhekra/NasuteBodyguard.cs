using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Nasute, Bodyguard: when the hero hits a Zhekra ally within <see cref="Guard"/> px, the Nasute turns and squirts him
    /// at once (one glue speck, 0.5, may root), once per <see cref="Cooldown"/> s. Tell: the nozzle swivels to the hero and
    /// puffs (Puff). Shore Up gives it and its kin a resin plate each.
    /// </summary>
    public class NasuteBodyguard : ZhkBehaviour
    {
        public const float Guard = 60f, Cooldown = 2f, ShoreRadius = 50f;
        /// <summary>The swivel-and-puff (set by the kit).</summary>
        public static exSpriteAnimClip PuffClip;
        static readonly List<NasuteBodyguard> s_all = new List<NasuteBodyguard>();

        float m_ready;
        ZhkBrain m_brain;

        protected override void Awake() { base.Awake(); m_brain = GetComponent<ZhkBrain>(); }
        protected override void OnEnable() { base.OnEnable(); m_ready = 0f; if (!s_all.Contains(this)) s_all.Add(this); }
        protected override void OnDisable() { base.OnDisable(); s_all.Remove(this); }

        /// <summary>The hero hit a Zhekra monster: every Nasute guarding it answers.</summary>
        public static void KinStruck(ZhkBrain victim)
        {
            if (victim == null) return;
            for (int i = s_all.Count - 1; i >= 0; i--)
            {
                var n = s_all[i];
                if (n == null || n.m_brain == victim || !n.Alive) continue;
                if ((victim.Pos - n.Me).sqrMagnitude <= Guard * Guard) n.Answer();
            }
        }

        /// <summary>Clip event (Shore Up): it and every Zhekra ally within <see cref="ShoreRadius"/> px gain a resin plate.</summary>
        public void ModZhkShoreUp()
        {
            if (!Alive) return;
            Monster.ModGainPlates(1);
            if (ZhekraFx.SealFx != null) SystemPool.Spawn(ZhekraFx.SealFx, Me);
            foreach (var k in Kin(Me, ShoreRadius))
            {
                var mm = k.GetComponent<ModMonster>();
                if (mm == null) continue;
                mm.ModGainPlates(1);
                if (ZhekraFx.SealFx != null) SystemPool.Spawn(ZhekraFx.SealFx, k.Pos);
            }
        }

        void Answer()
        {
            if (Time.time < m_ready || ZhekraFx.GlueSpeck == null) return;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            m_ready = Time.time + Cooldown;
            Monster.Face(hero.transform.position);
            Flourish(PuffClip);
            Vector2 nozzle = Me + new Vector2(16f * Side, 13f);
            FxFactory.SpawnOwned(ZhekraFx.GlueSpeck, nozzle, Own, AngleTo(nozzle, (Vector2)hero.transform.position + new Vector2(0f, 6f)));
        }
    }
}
