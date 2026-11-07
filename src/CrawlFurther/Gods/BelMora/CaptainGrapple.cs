using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Drowned Captain. His gaff drags a hero it rakes <see cref="Haul"/> px in. Grapple Swing: he fires his grapple into the
    /// wall beyond the hero and swings across in an arc (untouchable, passing through everything), landing just past the
    /// hero with a boot. Man Overboard: a hero he hauls or kicks into brine is held under for a root. Tell: the rope from his
    /// hand to the hook in the wall; a column of bubbles and a hand of kelp at the hero's feet.
    /// </summary>
    public class CaptainGrapple : BelBehaviour
    {
        public const float Haul = 24f, Swing = 0.5f, Bulge = 18f, Past = 18f, Watch = 0.6f;

        Vector2 m_from, m_to, m_hookAt;
        float m_swing = -1f;
        GameObject m_hook;
        readonly BelLine m_rope = new BelLine();

        protected override void OnEnable() { base.OnEnable(); m_swing = -1f; m_hook = null; }
        protected override void OnDisable() { base.OnDisable(); EndSwing(); }

        public override void OnHitHero(DamageInfo d)
        {
            var hero = ModUtil.Hero();
            if (hero == null) return;
            if (HitFrom(d, BelMoraFx.CaptainGaff)) { BelWater.Drag(this, hero, Me, Haul, 0.18f); StartCoroutine(Overboard(hero)); }
            else if (HitFrom(d, BelMoraFx.GrappleKick)) StartCoroutine(Overboard(hero));
        }

        // the haul or the kick carries the hero a little way: if he ends up in brine, the kelp holds him under
        IEnumerator Overboard(GameObject hero)
        {
            float t = 0f;
            while (t < Watch && hero != null && hero.activeInHierarchy)
            {
                t += Time.deltaTime;
                Vector2 hp = hero.transform.position;
                if (BelWater.InBrine(hp))
                {
                    var p = hero.GetComponent<Player>();
                    if (p != null && ModStatus.Root != null) p.AddStatus(ModStatus.Root, Own, "beloverboard");
                    if (BelMoraFx.KelpHand != null) SystemPool.Spawn(BelMoraFx.KelpHand, hp);
                    yield break;
                }
                yield return null;
            }
        }

        /// <summary>Clip event (Grapple): the grapple bites into the wall beyond the hero; the swing is set up.</summary>
        public void BelGrappleFire()
        {
            if (!Alive) return;
            Vector2 hp = HeroPos;
            var dir = hp - Me;
            if (dir.sqrMagnitude < 1f) dir = Face;
            dir.Normalize();
            m_from = Me;
            m_to = ModUtil.SafePoint(Me, hp + dir * Past, 8f);
            m_hookAt = ModUtil.SafePoint(hp, hp + dir * 200f, 2f) + new Vector2(0f, 14f);
            if (BelMoraFx.GrappleHook != null) m_hook = SystemPool.Spawn(BelMoraFx.GrappleHook, m_hookAt);
            m_rope.Lay(BelMoraFx.RopeLink, Me + new Vector2(0f, 24f), m_hookAt, 3f);
        }

        /// <summary>Clip event: the swing (he moves along the arc from here).</summary>
        public void BelSwing() { if (Alive) m_swing = 0f; }

        void Update()
        {
            if (m_swing < 0f) return;
            if (!Alive) { EndSwing(); return; }
            m_swing += Time.deltaTime;
            float t = Mathf.Clamp01(m_swing / Swing);
            var line = m_to - m_from;
            var side = new Vector2(-line.y, line.x).normalized;
            if (side.y < 0f) side = -side;     // the arc bows up the screen, toward the hook's wall
            var p = m_from + line * t + side * Bulge * Mathf.Sin(t * Mathf.PI);
            ModUtil.Teleport(gameObject, p);
            m_rope.Lay(BelMoraFx.RopeLink, p + new Vector2(0f, 24f), m_hookAt, 3f);
            if (t >= 1f) EndSwing();
        }

        void EndSwing()
        {
            m_swing = -1f;
            m_rope.Clear();
            if (m_hook != null && m_hook.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(m_hook);
            m_hook = null;
        }
    }
}
