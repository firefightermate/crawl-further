using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>The Loom Widow's line: when its hook reaches the hero, it ties him to the widow that cast it.</summary>
    public class YsvSpoolHookFx : MonoBehaviour
    {
        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null) return;
            var hero = ModUtil.Hero();
            if (hero == null || d.m_victim != hero) return;
            var src = d.m_source ?? FxFactory.SourceOf(gameObject);
            var owner = src != null ? src.m_sourceOwner : null;
            if (owner == null) return;
            var t = hero.GetComponent<YsvSpoolLine>() ?? hero.AddComponent<YsvSpoolLine>();
            t.Begin(owner);
        }
    }

    /// <summary>
    /// On the hero while the Loom Widow spools him: a silver line to her loom. Every 0.5 s for 3 s one of his frost pips
    /// runs up the line into her (she heals 0.8 and winds it onto her loom, see <see cref="LoomSpool"/>); a hero with no
    /// pip gets one put on him instead. Breaks if she dies or he gets more than 120 px away.
    /// </summary>
    public class YsvSpoolLine : MonoBehaviour
    {
        public const float Duration = 3f, Tick = 0.5f, Heal = 0.8f, Break = 120f, BeadTime = 0.3f;
        const int Beads = 6;
        GameObject m_owner;
        float m_left, m_tick;
        readonly List<GameObject> m_line = new List<GameObject>();
        readonly List<KeyValuePair<GameObject, float>> m_running = new List<KeyValuePair<GameObject, float>>();

        public void Begin(GameObject owner)
        {
            m_owner = owner; m_left = Duration; m_tick = Tick * 0.5f;
            if (m_line.Count == 0 && YsveldFx.Bead != null)
                for (int i = 0; i < Beads; i++) { var b = SystemPool.Spawn(YsveldFx.Bead, transform.position); if (b != null) m_line.Add(b); }
            enabled = true;
        }

        Vector2 Hero { get { return (Vector2)transform.position + new Vector2(0f, 9f); } }
        Vector2 Loom
        {
            get
            {
                var q = m_owner.GetComponent<LoomSpool>();
                return q != null ? q.SpoolPoint : (Vector2)m_owner.transform.position + new Vector2(0f, 20f);
            }
        }

        void Update()
        {
            if (m_owner == null) { End(false); return; }
            Vector2 me = transform.position, them = m_owner.transform.position;
            m_left -= Time.deltaTime;
            var mh = GetComponent<Health>();
            if (m_left <= 0f || !YsvUtil.Alive(m_owner) || (mh != null && !mh.IsAlive()) || (me - them).magnitude > Break) { End(true); return; }
            m_tick -= Time.deltaTime;
            if (m_tick <= 0f)
            {
                m_tick = Tick;
                var r = YsvRime.Of(gameObject);
                if (r.Take())
                {
                    var b = YsveldFx.SpoolBead != null ? SystemPool.Spawn(YsveldFx.SpoolBead, Hero) : null;
                    m_running.Add(new KeyValuePair<GameObject, float>(b, 0f));
                }
                else r.Add(YsvUtil.Source(m_owner), 1, true);
            }
            for (int i = m_running.Count - 1; i >= 0; i--)
            {
                var b = m_running[i].Key;
                float t = m_running[i].Value + Time.deltaTime / BeadTime;
                if (t < 1f) { m_running[i] = new KeyValuePair<GameObject, float>(b, t); continue; }
                if (b != null) SystemPool.Despawn(b);
                m_running.RemoveAt(i);
                var oh = m_owner.GetComponent<Health>();
                if (oh != null) { oh.Heal(Heal); ModInd.Heal(m_owner); }
                var q = m_owner.GetComponent<LoomSpool>();
                if (q != null) q.Wind();
            }
        }

        void LateUpdate()
        {
            if (m_owner == null) return;
            Vector2 a = Hero, b = Loom;
            for (int i = 0; i < m_line.Count; i++)
            {
                if (m_line[i] == null) continue;
                float t = (i + 1f) / (m_line.Count + 1f);
                var p = Vector2.Lerp(a, b, t) + new Vector2(0f, -Mathf.Sin(t * Mathf.PI) * 4f);
                m_line[i].transform.position = new Vector3(p.x, p.y, m_line[i].transform.position.z);
            }
            foreach (var kv in m_running)
            {
                if (kv.Key == null) continue;
                var p = Vector2.Lerp(a, b, kv.Value) + new Vector2(0f, -Mathf.Sin(kv.Value * Mathf.PI) * 4f);
                kv.Key.transform.position = new Vector3(p.x, p.y, kv.Key.transform.position.z);
            }
        }

        void End(bool snap)
        {
            if (snap && YsveldFx.SpoolSnap != null && m_owner != null) SystemPool.Spawn(YsveldFx.SpoolSnap, Vector2.Lerp(Hero, Loom, 0.5f));
            Clear();
            enabled = false;
        }

        void Clear()
        {
            foreach (var b in m_line) if (b != null) SystemPool.Despawn(b);
            foreach (var kv in m_running) if (kv.Key != null) SystemPool.Despawn(kv.Key);
            m_line.Clear(); m_running.Clear();
            m_owner = null;
        }

        void OnDisable() { Clear(); }
    }
}
