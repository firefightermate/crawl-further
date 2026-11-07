using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A Wick Hag's wax poppet of the hero. For <see cref="Life"/> s he takes <see cref="Share"/> of any fire damage the
    /// poppet takes (her flames, a pool, a pyre it stands in); a red thread of light runs from it to him and it flinches
    /// when it burns. A hit from him near it, or a step on it, breaks it; at the end it melts into a burning pool.
    /// </summary>
    public class VhPoppetFx : MonoBehaviour
    {
        public const float Life = 4f, Share = 0.6f, Tick = 0.6f, StepOn = 7f, HitReach = 14f;
        public const int Motes = 5;
        static readonly List<VhPoppetFx> s_live = new List<VhPoppetFx>();

        readonly List<GameObject> m_motes = new List<GameObject>();
        readonly HashSet<GameObject> m_flamesSeen = new HashSet<GameObject>();
        DamageSource m_src;
        float m_t, m_tick;
        bool m_done;

        public static VhPoppetFx Of(GameObject owner)
        {
            s_live.RemoveAll(p => p == null || !p.isActiveAndEnabled);
            foreach (var p in s_live) if (p.m_src != null && p.m_src.m_sourceOwner == owner) return p;
            return null;
        }

        public Vector2 Pos { get { return transform.position; } }

        public void Restart() { m_t = 0f; m_tick = 0f; m_done = false; m_src = null; m_flamesSeen.Clear(); if (!s_live.Contains(this)) s_live.Add(this); }
        void OnDisable() { s_live.Remove(this); ClearMotes(); }

        /// <summary>The hero's attack landed at <paramref name="at"/>: a hit near the poppet breaks it.</summary>
        public static void HeroStruck(Vector2 at)
        {
            foreach (var p in s_live.ToArray())
                if (p != null && p.isActiveAndEnabled && !p.m_done && (p.Pos - at).sqrMagnitude < HitReach * HitReach) p.Break();
        }

        void Update()
        {
            if (m_done) return;
            if (m_src == null) m_src = FxFactory.SourceOf(gameObject);
            m_t += Time.deltaTime;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 h = (Vector2)hero.transform.position + new Vector2(0f, 8f);
            DrawThread(h);
            if (((Vector2)hero.transform.position - Pos).sqrMagnitude < StepOn * StepOn) { Break(); return; }
            if (m_t >= Life) { Melt(); return; }
            // her hex flames: each one that reaches the poppet burns it once
            foreach (var f in IgniterFx.All)
            {
                if (f == null || !f.isActiveAndEnabled || m_flamesSeen.Contains(f.gameObject)) continue;
                if (!f.gameObject.name.StartsWith("ModVhHexFlame") || (f.Pos - Pos).sqrMagnitude > 8f * 8f) continue;
                m_flamesSeen.Add(f.gameObject);
                Burn(1.0f);
            }
            // a pool or pyre under it burns it on the pool's own beat
            m_tick -= Time.deltaTime;
            if (m_tick <= 0f && IgniterFx.Nearest(Pos, 9f, f => !f.gameObject.name.StartsWith("ModVhHexFlame")) != null) { m_tick = Tick; Burn(0.5f); }
        }

        void Burn(float fire)
        {
            var hero = ModUtil.Hero();
            var hp = hero != null ? hero.GetComponent<Health>() : null;
            if (hp != null && hp.IsAlive() && m_src != null)
            {
                var dir = ((Vector2)hero.transform.position - Pos).normalized;
                hp.Damage(new DamageInfo(fire * Share, 0f, 0f, dir, m_src), false);
            }
            Play(VhorrulFx.PoppetFlinch);
        }

        void Break()
        {
            m_done = true;
            ClearMotes();
            if (VhorrulFx.Glance != null) SystemPool.Spawn(VhorrulFx.Glance, Pos);
            SystemPool.Despawn(gameObject);
        }

        void Melt()
        {
            m_done = true;
            ClearMotes();
            if (VhorrulFx.BurningPool != null) FxFactory.SpawnOwned(VhorrulFx.BurningPool, Pos, m_src);
            SystemPool.Despawn(gameObject);
        }

        void Play(exSpriteAnimClip clip)
        {
            var anim = GetComponent<exSpriteAnimation>();
            if (anim == null || clip == null) return;
            if (anim.GetAnimation(clip.name) == null) anim.AddAnimation(clip);
            anim.Play(clip.name);
        }

        void DrawThread(Vector2 to)
        {
            if (VhorrulFx.Thread == null) return;
            while (m_motes.Count < Motes) m_motes.Add(SystemPool.Spawn(VhorrulFx.Thread, Pos));
            Vector2 from = Pos + new Vector2(0f, 6f);
            for (int i = 0; i < m_motes.Count; i++)
            {
                var m = m_motes[i];
                if (m == null) continue;
                float k = (i + 1f) / (Motes + 1f) + Mathf.Repeat(m_t * 0.6f, 1f / (Motes + 1f));
                var p = Vector2.Lerp(from, to, k);
                m.transform.position = new Vector3(p.x, p.y, -9f);
            }
        }

        void ClearMotes()
        {
            foreach (var m in m_motes) if (m != null && m.activeInHierarchy) SystemPool.Despawn(m);
            m_motes.Clear();
        }
    }
}
