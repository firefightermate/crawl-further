using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The hero's frost pips (Rime): a three-slot meter over his head. The third pip pins him in ice (the mod root) and
    /// clears the meter. Pips melt <see cref="MeltTime"/> s after the last frost hit, and one monster adds at most one pip
    /// every <see cref="PerSourceGap"/> s unless a move says otherwise.
    /// </summary>
    public class YsvRime : MonoBehaviour
    {
        public const float MeltTime = 3.5f, PerSourceGap = 0.35f;

        /// <summary>Raised when frost pins the hero: the hero and the source of the pip that pinned him.</summary>
        public static event Action<GameObject, DamageSource> Pinned;

        int m_stacks;
        float m_lastHit = -99f;
        readonly Dictionary<GameObject, float> m_lastBySource = new Dictionary<GameObject, float>();

        /// <summary>Pips on the hero right now (0-2).</summary>
        public int Stacks { get { return m_stacks; } }

        /// <summary>The hero's meter (added on first use), or null without a hero.</summary>
        public static YsvRime Of(GameObject hero)
        {
            if (hero == null) return null;
            return hero.GetComponent<YsvRime>() ?? hero.AddComponent<YsvRime>();
        }

        /// <summary>The hero's pip count, 0 if he has no meter yet.</summary>
        public static int On(GameObject hero)
        {
            var r = hero != null ? hero.GetComponent<YsvRime>() : null;
            return r != null ? r.m_stacks : 0;
        }

        /// <summary>Add <paramref name="pips"/> pips from <paramref name="src"/>. ignoreGap skips the per-monster limit.</summary>
        public void Add(DamageSource src, int pips = 1, bool ignoreGap = false)
        {
            var owner = src != null ? (src.m_sourceOwner ?? src.m_source) : null;
            float now = Time.time, last;
            if (!ignoreGap && owner != null && m_lastBySource.TryGetValue(owner, out last) && now - last < PerSourceGap) return;
            if (owner != null)
            {
                if (m_lastBySource.Count > 32) m_lastBySource.Clear();   // dead monsters' entries: keep the map small
                m_lastBySource[owner] = now;
            }
            m_lastHit = now;
            m_stacks += Mathf.Max(1, pips);
            if (m_stacks >= 3) Pin(src);
            Refresh();
        }

        /// <summary>Take one pip off the hero (the Loom Widow's spool). False if he had none.</summary>
        public bool Take()
        {
            if (m_stacks <= 0) return false;
            m_stacks--;
            Refresh();
            return true;
        }

        /// <summary>Pin the hero at once, whatever his pips.</summary>
        public void Pin(DamageSource src)
        {
            m_stacks = 0;
            var p = GetComponent<Player>();
            var root = FxFactory.GetStatus("StatusStuckToFloor");
            if (p != null && root != null) p.AddStatus(root, src, "modysvrime");
            if (YsveldFx.Bind != null) SystemPool.Spawn(YsveldFx.Bind, transform.position);
            Refresh();
            if (Pinned == null) return;
            try { Pinned(gameObject, src); }
            catch (Exception e) { Plugin.Log.LogError("Rime pin handler failed: " + e); }
        }

        void Refresh() { ModInd.Count(gameObject, YsveldFx.IndRime, Mathf.Min(m_stacks, 2)); }

        void Update()
        {
            if (m_stacks > 0 && Time.time - m_lastHit > MeltTime) { m_stacks = 0; Refresh(); }
            var h = GetComponent<Health>();
            if (m_stacks > 0 && h != null && !h.IsAlive()) { m_stacks = 0; Refresh(); }
        }

        void OnDisable() { m_stacks = 0; m_lastBySource.Clear(); ModInd.Count(gameObject, YsveldFx.IndRime, 0); }
    }

    /// <summary>On a frost-tagged effect instance: when it damages the hero, add pips. Cold Snap (the Rimeling's bite) adds
    /// two to a hero already carrying two, so it pins at once; a widowed Bride's frost adds two per hit.</summary>
    public class YsvRimeFx : MonoBehaviour
    {
        /// <summary>Set on the Rimeling's bite.</summary>
        public bool coldSnap;

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null || d.m_isDamageFromStatus) return;
            var hero = ModUtil.Hero();
            if (hero == null || d.m_victim != hero) return;
            var r = YsvRime.Of(hero);
            if (coldSnap && r.Stacks == 2) { r.Add(d.m_source, 2, true); return; }
            var owner = d.m_source != null ? d.m_source.m_sourceOwner : null;
            var q = owner != null ? owner.GetComponent<YsveldBehaviour>() : null;
            int pips = q != null ? q.PipsPerHit : 1;
            r.Add(d.m_source, pips, pips > 1);
        }
    }
}
