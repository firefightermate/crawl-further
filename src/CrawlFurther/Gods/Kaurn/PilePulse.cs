using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Voltaic Pile's Pulse: every <see cref="Every"/> s (with a tick from the pile) a bright bead runs out along each arc
    /// joined to it. A hero touching an arc as a bead passes takes <see cref="BeadDamage"/>, not 0.3. Surge: every arc joined
    /// to it flashes white for <see cref="FlashTime"/> s (1.0 to a hero touching one).
    /// </summary>
    public class PilePulse : KaurnBehaviour
    {
        public const float Every = 2f, Run = 0.45f, BeadDamage = 0.8f, BeadDist = 7f, FlashTime = 0.3f, FlashDamage = 1.0f, Touch = 6f;

        class Bead { public KaurnConduction.End from, to; public float t; public GameObject vis; }

        readonly List<Bead> m_beads = new List<Bead>();
        readonly List<List<GameObject>> m_flash = new List<List<GameObject>>();
        float m_next;

        protected override void OnEnable() { base.OnEnable(); m_next = Every; }

        protected override void OnDisable()
        {
            base.OnDisable();
            foreach (var b in m_beads) if (b.vis != null && b.vis.activeInHierarchy) SystemPool.Despawn(b.vis);
            m_beads.Clear();
            ClearFlash();
        }

        void ClearFlash() { foreach (var s in m_flash) KaurnFx.Clear(s); m_flash.Clear(); }

        void Update()
        {
            if (!Alive) return;
            m_next -= Time.deltaTime;
            if (m_next <= 0f)
            {
                m_next = Every;
                if (KaurnFx.PileTick != null) SystemPool.Spawn(KaurnFx.PileTick, Unit.Top + new Vector2(0f, 4f));
                foreach (var l in KaurnConduction.LinksOf(Unit))
                {
                    if (l.ToHero) continue;
                    var b = new Bead { from = l.a.c == Unit ? l.a : l.b, to = l.Other(Unit), t = 0f };
                    if (KaurnFx.Bead != null) b.vis = SystemPool.Spawn(KaurnFx.Bead, b.from.Top);
                    m_beads.Add(b);
                }
            }
            var hero = ModUtil.Hero();
            for (int i = m_beads.Count - 1; i >= 0; i--)
            {
                var b = m_beads[i];
                b.t += Time.deltaTime / Run;
                if (b.t >= 1f || !b.to.Valid)
                {
                    if (b.vis != null && b.vis.activeInHierarchy) SystemPool.Despawn(b.vis);
                    m_beads.RemoveAt(i);
                    continue;
                }
                var top = Vector2.Lerp(b.from.Top, b.to.Top, b.t);
                if (b.vis != null) b.vis.transform.position = new Vector3(top.x, top.y, b.vis.transform.position.z);
                var floor = Vector2.Lerp(b.from.Feet, b.to.Feet, b.t);
                if (hero != null && ((Vector2)hero.transform.position - floor).sqrMagnitude < BeadDist * BeadDist)
                    KaurnConduction.HurtHero(BeadDamage, Own, floor);
            }
        }

        /// <summary>Clip event when the last disc lights: every arc joined to it flashes.</summary>
        public void KrnSurge() { StartCoroutine(Surge()); }

        IEnumerator Surge()
        {
            var links = KaurnConduction.LinksOf(Unit);
            var hero = ModUtil.Hero();
            bool hit = false;
            float t = 0f;
            while (t < FlashTime && Alive)
            {
                t += Time.deltaTime;
                for (int i = 0; i < links.Count; i++)
                {
                    var l = links[i];
                    if (!l.a.Valid || !l.b.Valid) continue;
                    while (m_flash.Count <= i) m_flash.Add(new List<GameObject>());
                    KaurnFx.Chain(m_flash[i], KaurnFx.ArcWhite, l.a.Top, l.b.Top);
                    float s;
                    if (!hit && hero != null && !l.ToHero && KaurnFx.SegDist(hero.transform.position, l.a.Feet, l.b.Feet, out s) < Touch && s > 0.1f && s < 0.9f)
                    {
                        hit = true;
                        var h = hero.GetComponent<Health>();
                        var dir = (Vector2)hero.transform.position - Me;
                        if (h != null && h.IsAlive()) h.Damage(new DamageInfo(FlashDamage, 0.4f, 0f, dir.sqrMagnitude > 0.01f ? dir.normalized : Vector2.right, Own), false);
                        if (KaurnFx.HitFx != null) SystemPool.Spawn(KaurnFx.HitFx, KaurnFx.HeroChest(hero));
                    }
                }
                yield return null;
            }
            ClearFlash();
        }
    }
}
