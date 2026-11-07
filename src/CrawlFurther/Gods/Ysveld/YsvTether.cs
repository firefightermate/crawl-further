using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>The Weaver's silk line: when it reaches the hero, it ties him to the Weaver that fired it.</summary>
    public class YsvThreadFx : MonoBehaviour
    {
        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null) return;
            var hero = ModUtil.Hero();
            if (hero == null || d.m_victim != hero) return;
            var src = d.m_source ?? FxFactory.SourceOf(gameObject);
            var owner = src != null ? src.m_sourceOwner : null;
            if (owner == null) return;
            var t = hero.GetComponent<YsvTether>() ?? hero.AddComponent<YsvTether>();
            t.Begin(owner);
        }
    }

    /// <summary>
    /// On the hero while tied: a beaded silk line to the Silk Weaver. Beyond 40 px he is hauled back toward her. Strum:
    /// every 0.8 s she plucks the line (a twang at her end) and a frost bead slides down it to him and adds a pip. Lasts
    /// 2.5 s; breaks early if she dies or the line is stretched past 160 px.
    /// </summary>
    public class YsvTether : MonoBehaviour
    {
        public const float Duration = 2.5f, Leash = 40f, Break = 160f, StrumEvery = 0.8f, BeadTime = 0.3f;
        const int Beads = 7;
        GameObject m_owner;
        float m_left, m_tick, m_strum;
        readonly List<GameObject> m_beads = new List<GameObject>();
        readonly List<KeyValuePair<GameObject, float>> m_running = new List<KeyValuePair<GameObject, float>>();

        public void Begin(GameObject owner)
        {
            m_owner = owner;
            m_left = Duration;
            m_tick = 0f;
            m_strum = StrumEvery;
            if (m_beads.Count == 0 && YsveldFx.Bead != null)
                for (int i = 0; i < Beads; i++) { var b = SystemPool.Spawn(YsveldFx.Bead, transform.position); if (b != null) m_beads.Add(b); }
            enabled = true;
        }

        Vector2 From { get { return (Vector2)m_owner.transform.position + new Vector2(0f, 12f); } }
        Vector2 To { get { return (Vector2)transform.position + new Vector2(0f, 8f); } }

        void Update()
        {
            if (m_owner == null) { End(false); return; }
            var oh = m_owner.GetComponent<Health>();
            var mh = GetComponent<Health>();
            Vector2 me = transform.position, them = m_owner.transform.position;
            float dist = (me - them).magnitude;
            m_left -= Time.deltaTime;
            if (m_left <= 0f || !m_owner.activeInHierarchy || (oh != null && !oh.IsAlive()) || (mh != null && !mh.IsAlive()) || dist > Break)
            {
                End(true); return;
            }
            m_tick -= Time.deltaTime;
            if (dist > Leash && m_tick <= 0f)
            {
                m_tick = 0.1f;
                ModUtil.Pull(gameObject, them, Mathf.Min(140f, (dist - Leash) * 10f));
            }
            m_strum -= Time.deltaTime;
            if (m_strum <= 0f)
            {
                m_strum = StrumEvery;
                if (YsveldFx.StrumTwang != null) SystemPool.Spawn(YsveldFx.StrumTwang, From);
                var b = YsveldFx.StrumBead != null ? SystemPool.Spawn(YsveldFx.StrumBead, From) : null;
                if (b != null) m_running.Add(new KeyValuePair<GameObject, float>(b, 0f));
            }
            for (int i = m_running.Count - 1; i >= 0; i--)
            {
                var b = m_running[i].Key;
                float t = m_running[i].Value + Time.deltaTime / BeadTime;
                if (b == null || t >= 1f)
                {
                    if (b != null) SystemPool.Despawn(b);
                    m_running.RemoveAt(i);
                    YsvUtil.Rime(gameObject, YsvUtil.Source(m_owner));
                    continue;
                }
                m_running[i] = new KeyValuePair<GameObject, float>(b, t);
            }
        }

        void LateUpdate()
        {
            if (m_owner == null) return;
            Vector2 a = From, b = To;
            for (int i = 0; i < m_beads.Count; i++)
            {
                if (m_beads[i] == null) continue;
                float t = (i + 1f) / (m_beads.Count + 1f);
                var p = Vector2.Lerp(a, b, t) + new Vector2(0f, -Mathf.Sin(t * Mathf.PI) * 3f);   // a slight sag
                m_beads[i].transform.position = new Vector3(p.x, p.y, m_beads[i].transform.position.z);
            }
            foreach (var kv in m_running)
            {
                if (kv.Key == null) continue;
                var p = Vector2.Lerp(a, b, kv.Value) + new Vector2(0f, -Mathf.Sin(kv.Value * Mathf.PI) * 3f);
                kv.Key.transform.position = new Vector3(p.x, p.y, kv.Key.transform.position.z - 0f);
            }
        }

        void End(bool snap)
        {
            if (snap && YsveldFx.Snap != null && m_owner != null)
                SystemPool.Spawn(YsveldFx.Snap, Vector2.Lerp(m_owner.transform.position, transform.position, 0.5f) + new Vector2(0f, 9f));
            Clear();
            enabled = false;
        }

        void Clear()
        {
            foreach (var b in m_beads) if (b != null) SystemPool.Despawn(b);
            foreach (var kv in m_running) if (kv.Key != null) SystemPool.Despawn(kv.Key);
            m_beads.Clear(); m_running.Clear();
            m_owner = null;
        }

        void OnDisable() { Clear(); }
    }
}
