using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Chain Spark (hero spell): when the spark hits a monster, a new spark leaps from it to the nearest
    /// monster not yet struck (within 80 px, clear line), up to 3 jumps.</summary>
    public class ChainSparkFx : MonoBehaviour
    {
        public const float JumpRange = 80f;
        public int jumps = 3;
        public List<GameObject> struck = new List<GameObject>();
        bool m_done;

        public void Reset() { jumps = 3; struck = new List<GameObject>(); m_done = false; }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (m_done || d == null || d.m_victim == null) return;
            var victim = d.m_victim.GetComponentInParent<Player>();
            var hero = ModUtil.Hero();
            if (victim == null || victim.gameObject == hero || struck.Contains(victim.gameObject)) return;
            m_done = true;
            struck.Add(victim.gameObject);
            if (jumps <= 0 || KaurnFx.HeroChainSpark == null) return;
            Vector2 vp = Chest(victim);
            Player best = null;
            float bd = JumpRange * JumpRange;
            foreach (var p in FindObjectsOfType<Player>())
            {
                if (p == null || p.gameObject == hero || struck.Contains(p.gameObject) || R.Get<bool>(p, "m_isGhost")) continue;
                var h = p.GetComponent<Health>();
                if (h == null || !h.IsAlive()) continue;
                var pc = Chest(p);
                float dd = (pc - vp).sqrMagnitude;
                if (dd < bd && ModUtil.Clear(vp, pc)) { bd = dd; best = p; }
            }
            if (best == null) return;
            var dir = (Chest(best) - vp).normalized;
            var from = vp + dir * 10f;
            var go = FxFactory.SpawnOwned(KaurnFx.HeroChainSpark, from, FxFactory.SourceOf(gameObject), Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg);
            var c = go != null ? go.GetComponent<ChainSparkFx>() : null;
            if (c != null) { c.jumps = jumps - 1; c.struck = new List<GameObject>(struck); }
            // the jump starts inside the monster it leaves: without this the new spark hit that monster again,
            // was used up on it, and the chain never reached a second monster
            var de = go != null ? go.GetComponent<DamageEffect>() : null;
            if (de != null)
                foreach (var s in struck)
                    if (s != null)
                        foreach (var col in s.GetComponentsInChildren<Collider>(true)) de.IgnoreCollider(col);
            if (KaurnFx.HitFx != null) SystemPool.Spawn(KaurnFx.HitFx, vp);
        }

        /// <summary>Centre of a player's hurtbox (child collider on the DamagablePlayer layer), else 8 px above it.</summary>
        static Vector2 Chest(Player p)
        {
            int layer = LayerMask.NameToLayer("DamagablePlayer");
            foreach (var b in p.GetComponentsInChildren<BoxCollider>())
                if (b.transform != p.transform && b.gameObject.layer == layer && b.enabled) return b.bounds.center;
            return (Vector2)p.transform.position + new Vector2(0f, 8f);
        }
    }
}
