using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Glue Mortar, Spotters: it aims through its kin. Bombard drops a shell on the hero and one on each of the two Zhekra
    /// nearest him (they are glue-proof). With no Zhekra within <see cref="SpotRadius"/> px of the hero it fires only one
    /// shell, and its basic is slower (basic 1). Tell: a small crosshair over each ally it is spotting through.
    /// </summary>
    public class MortarSpotters : ZhkBehaviour
    {
        public const float SpotRadius = 80f, Range = 240f, Tick = 0.5f, MarkY = 26f;

        readonly List<ZhkBrain> m_spot = new List<ZhkBrain>();
        float m_tick;

        protected override void OnEnable() { base.OnEnable(); m_spot.Clear(); m_tick = 0f; }

        void Update()
        {
            if (!Alive) return;
            m_tick -= Time.deltaTime;
            if (m_tick > 0f) return;
            m_tick = Tick;
            Spot();
            NextBasic(m_spot.Count > 0 ? 0 : 1);
            if (ZhekraFx.Spot == null) return;
            foreach (var s in m_spot) ModAttach.Spawn(ZhekraFx.Spot, s.gameObject, new Vector2(0f, MarkY));
        }

        void Spot()
        {
            m_spot.Clear();
            var hp = HeroPos;
            var kin = Kin(hp, SpotRadius);
            kin.Sort((a, b) => (a.Pos - hp).sqrMagnitude.CompareTo((b.Pos - hp).sqrMagnitude));
            for (int i = 0; i < kin.Count && m_spot.Count < 2; i++) m_spot.Add(kin[i]);
        }

        /// <summary>Clip event: a shell. 0 on the hero; 1 and 2 on the allies spotting for it.</summary>
        public void ModZhkShell(int i)
        {
            var hero = ModUtil.Hero();
            if (!Alive || hero == null || ZhekraFx.GlueShell == null) return;
            Vector2 hp = hero.transform.position;
            if ((hp - Me).sqrMagnitude > Range * Range) return;
            if (i == 0) { FxFactory.SpawnOwned(ZhekraFx.GlueShell, hp, Own); return; }
            Spot();
            if (i - 1 < m_spot.Count && m_spot[i - 1] != null) FxFactory.SpawnOwned(ZhekraFx.GlueShell, m_spot[i - 1].Pos, Own);
        }
    }
}
