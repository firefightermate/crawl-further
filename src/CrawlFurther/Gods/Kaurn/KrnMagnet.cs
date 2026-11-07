using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Polarity Warg's Magnetize: for 3 s the hero is dragged toward the nearest Kaurn iron (a Kaurn monster or post) within
    /// 150 px, shown by a field line and the magnet over his head. Iron Grip: if he reaches it he clamps to it (a short
    /// root) and every arc joined to that iron hits him once.
    /// </summary>
    public class KrnMagnet : MonoBehaviour
    {
        public const float Reach = 150f, Pull = 30f, Every = 0.15f, Grip = 9f, ArcHit = 0.3f;
        static KrnMagnet s_inst;
        readonly List<GameObject> m_segs = new List<GameObject>();
        float m_left, m_pull;
        GameObject m_hero;
        DamageSource m_src;

        public static void Begin(float seconds, DamageSource src)
        {
            if (s_inst == null)
            {
                var go = new GameObject("CrawlMod_KrnMagnet");
                DontDestroyOnLoad(go);
                s_inst = go.AddComponent<KrnMagnet>();
            }
            s_inst.m_left = seconds;
            s_inst.m_src = src;
            s_inst.m_hero = ModUtil.Hero();
            if (s_inst.m_hero != null && KaurnFx.MagnetInd != null) ModInd.Set(s_inst.m_hero, KaurnFx.MagnetInd, true, seconds);
        }

        void Stop()
        {
            KaurnFx.Clear(m_segs);
            if (m_hero != null && KaurnFx.MagnetInd != null) ModInd.Set(m_hero, KaurnFx.MagnetInd, false);
            m_hero = null;
        }

        void Update()
        {
            if (m_hero == null) { if (m_segs.Count > 0) KaurnFx.Clear(m_segs); return; }
            m_left -= Time.deltaTime;
            var hh = m_hero.GetComponent<Health>();
            if (m_left <= 0f || hh == null || !hh.IsAlive() || m_hero != ModUtil.Hero()) { Stop(); return; }
            Vector2 hp = m_hero.transform.position;
            Vector2 best = hp; float bd = Reach * Reach; Component iron = null;
            foreach (var u in KaurnUnit.All)
            {
                if (u == null || !u.Alive) continue;
                float d = (u.FeetPos - hp).sqrMagnitude;
                if (d < bd) { bd = d; best = u.FeetPos; iron = u; }
            }
            foreach (var n in KrnNode.All)
            {
                if (n == null || !n.gameObject.activeInHierarchy || !n.Conducts || n.kind == KrnNode.Kind.Orb) continue;
                Vector2 np = n.transform.position;
                float d = (np - hp).sqrMagnitude;
                if (d < bd) { bd = d; best = np; iron = n; }
            }
            if (iron == null) { KaurnFx.Clear(m_segs); return; }
            if (bd <= Grip * Grip) { Clamp(iron, hp); return; }
            KaurnFx.Chain(m_segs, KaurnFx.LodeSeg, hp + new Vector2(0f, 8f), best + new Vector2(0f, 6f), 12);
            m_pull -= Time.deltaTime;
            if (m_pull <= 0f) { m_pull = Every; ModUtil.Pull(m_hero, best, Pull); }
        }

        // Iron Grip: stuck to the iron, and every arc from it hits once
        void Clamp(Component iron, Vector2 hp)
        {
            var hero = m_hero;
            Stop();
            if (KaurnFx.Clamp != null) SystemPool.Spawn(KaurnFx.Clamp, hp);
            var pl = hero.GetComponent<Player>();
            if (pl != null && ModStatus.Root != null) pl.AddStatus(ModStatus.Root, m_src, "krnirongrip");
            var h = hero.GetComponent<Health>();
            foreach (var l in KaurnConduction.LinksOf(iron))
            {
                if (h == null || !h.IsAlive() || l.ToHero) continue;
                var o = l.Other(iron);
                var dir = hp - o.Feet;
                h.Damage(new DamageInfo(ArcHit, 0f, 0f, dir.sqrMagnitude > 0.01f ? dir.normalized : Vector2.right, m_src), false);
            }
        }
    }
}
