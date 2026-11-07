using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Spoiled (Bloatfly): while the hero stands in its bile his poison runs at half speed, so it lasts twice as long.
    /// Tell: the bubbling puddle and a green pulse at his feet.
    /// </summary>
    public class Spoiled : MonoBehaviour
    {
        const float Grace = 0.15f;
        float m_until;
        Player m_player;
        readonly Dictionary<ActiveStatus, float> m_banked = new Dictionary<ActiveStatus, float>();

        /// <summary>The hero is standing in bile this frame.</summary>
        public static void Mark(GameObject hero)
        {
            if (hero == null) return;
            var s = hero.GetComponent<Spoiled>() ?? hero.AddComponent<Spoiled>();
            if (s.m_until < Time.time && SylveneFx.SpoiledInd != null) ModInd.Set(hero, SylveneFx.SpoiledInd, true, Grace * 2f);
            s.m_until = Time.time + Grace;
            s.enabled = true;
        }

        void Awake() { m_player = GetComponent<Player>(); }

        void Update()
        {
            if (Time.time > m_until) { m_banked.Clear(); enabled = false; return; }
            if (SylveneFx.SpoiledInd != null) ModInd.Set(gameObject, SylveneFx.SpoiledInd, true, Grace * 2f);
            var mgr = m_player != null ? m_player.GetStatusManager() : null;
            var list = mgr != null ? R.Get<List<ActiveStatus>>(mgr, "m_statuses") : null;
            if (list == null) return;
            foreach (var a in list)
            {
                if (a == null || a.m_data == null || a.m_data.name.IndexOf("Poison", System.StringComparison.Ordinal) < 0) continue;
                // wind the timer back one whole tick at a time: its tick phase stays the same, so no tick lands twice
                float tick = a.m_data.m_damageRate > 0.05f ? a.m_data.m_damageRate : 0.5f, bank;
                m_banked.TryGetValue(a, out bank);
                bank += Time.deltaTime * 0.5f;
                while (bank >= tick) { a.m_timeActive -= tick; bank -= tick; }
                m_banked[a] = bank;
            }
        }
    }
}
