using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Drops copies of a template in a ring around where it was spawned (owned by its spawner), optionally one
    /// more in the centre a moment later. Cold Read (the Veil Witch's crystals): the count is 1 plus the hero's frost
    /// pips (max 4), and the pips over him flash as she reads them.</summary>
    public class YsvRingFx : MonoBehaviour
    {
        GameObject m_tmpl;
        int m_count;
        float m_radius, m_centreDelay;
        bool m_done, m_coldRead;

        public void Setup(GameObject tmpl, int count, float radius, float centreDelay, bool coldRead = false)
        {
            m_tmpl = tmpl; m_count = count; m_radius = radius; m_centreDelay = centreDelay; m_coldRead = coldRead; m_done = false;
        }

        void OnEnable() { m_done = false; }

        void Update()
        {
            if (m_done || m_tmpl == null) return;
            m_done = true;
            var src = FxFactory.SourceOf(gameObject);
            Vector2 c = transform.position;
            int n = m_count;
            if (m_coldRead)
            {
                var hero = ModUtil.Hero();
                int pips = YsvRime.On(hero);
                n = Mathf.Min(4, 1 + pips);
                if (pips > 0 && hero != null && YsveldFx.PipFlash != null)
                    SystemPool.Spawn(YsveldFx.PipFlash, FloatNumber.OverHead(hero, 4f));
            }
            float start = Random.Range(0f, 360f);
            float radius = n == 1 ? 0f : m_radius;     // a single crystal grows right under him
            for (int i = 0; i < n; i++)
            {
                float a = (start + i * 360f / n) * Mathf.Deg2Rad;
                var p = c + new Vector2(Mathf.Cos(a) * radius, Mathf.Sin(a) * radius * 0.7f);
                FxFactory.SpawnOwned(m_tmpl, ModUtil.SafePoint(c, p), src);
            }
            if (m_centreDelay >= 0f) StartCoroutine(Centre(c, src));
        }

        IEnumerator Centre(Vector2 c, DamageSource src)
        {
            yield return new WaitForSeconds(m_centreDelay);
            if (m_tmpl != null) FxFactory.SpawnOwned(m_tmpl, c, src);
        }
    }
}
