using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Marrow Wyrm, Red Marrow: bone piles within <see cref="Range"/> px of it fill with marrow; an Ossivar monster that eats
    /// one gets two plates, not one (<see cref="OssivarMonster"/>). Tell: red-veined piles and a thin red line from each to
    /// the wyrm.
    /// </summary>
    public class WyrmMarrow : OssBehaviour
    {
        public const float Range = 60f;
        public const int MaxLines = 4;
        readonly Dictionary<BonePileFx, List<GameObject>> m_lines = new Dictionary<BonePileFx, List<GameObject>>();
        readonly List<BonePileFx> m_drop = new List<BonePileFx>();
        float m_scan;

        protected override void OnDisable() { base.OnDisable(); foreach (var l in m_lines.Values) OssFloor.Clear(l); m_lines.Clear(); }

        Vector2 Chest { get { return Me + new Vector2(Side * 2f, 9f); } }

        void Update()
        {
            m_scan -= Time.deltaTime;
            if (m_scan <= 0f && Alive)
            {
                m_scan = 0.2f;
                foreach (var p in BonePileFx.Snapshot())
                {
                    if (p == null || (p.Pos - Me).sqrMagnitude > Range * Range) continue;
                    p.FillMarrow();
                    if (!m_lines.ContainsKey(p) && m_lines.Count < MaxLines) m_lines[p] = new List<GameObject>();
                }
            }
            m_drop.Clear();
            foreach (var kv in m_lines)
            {
                var p = kv.Key;
                if (!Alive || p == null || !p.isActiveAndEnabled || (p.Pos - Me).sqrMagnitude > Range * Range) { OssFloor.Clear(kv.Value); m_drop.Add(p); continue; }
                OssFloor.Line(kv.Value, OssivarFx.MarrowLine, Chest, p.Pos + new Vector2(0f, 2f), 6);
            }
            foreach (var p in m_drop) m_lines.Remove(p);
        }
    }
}
