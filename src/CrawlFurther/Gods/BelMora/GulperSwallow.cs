using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Gulper Eel. Swallow Whole: it unhinges its jaw (a long tell, the floor ahead rippling), then gulps
    /// <see cref="Gulp"/> px forward. A hero in the mouth is swallowed: hidden inside for <see cref="Inside"/> s, chewed
    /// twice, then spat out <see cref="Spit"/> px with a splash of brine. Full Pouch: while it digests and
    /// <see cref="After"/> s after, its swollen throat takes x<see cref="Weak"/> damage and it crawls at half speed. A gulp
    /// that catches nothing leaves it gagging. Tell: the pouch bulges pale and its tail-light flickers (Full).
    /// </summary>
    public class GulperSwallow : BelBehaviour
    {
        public const float Gulp = 30f, Inside = 0.8f, Spit = 50f, After = 2f, Weak = 1.5f, Slow = 0.5f, Gag = 1f, MouthLen = 30f, MouthW = 12f;
        /// <summary>The full-pouch stance and the gag (set by the kit).</summary>
        public static exSpriteAnimClip FullIdle, FullRun, GagClip;

        float m_full;
        GameObject m_held;
        readonly List<Renderer> m_hidden = new List<Renderer>();

        protected override void OnEnable() { base.OnEnable(); m_full = 0f; m_held = null; }
        protected override void OnDisable() { base.OnDisable(); Release(false); }

        /// <summary>Clip event (Unhinge, the gulp): lunge forward and shut the jaw on whatever is in it.</summary>
        public void BelGulp()
        {
            if (!Alive) return;
            var f = Face;
            Shift(f * Gulp);
            var hero = ModUtil.Hero();
            bool caught = false;
            if (hero != null && m_held == null)
            {
                var d = (Vector2)hero.transform.position - Me;
                float along = Vector2.Dot(d, f), across = Mathf.Abs(d.x * f.y - d.y * f.x);
                caught = along > -4f && along < MouthLen && across < MouthW && ModStatus.AllowCrowdControl(hero);
            }
            if (caught) StartCoroutine(Digest(hero));
            else Hold(GagClip, Gag);
        }

        IEnumerator Digest(GameObject hero)
        {
            m_held = hero;
            SetFull(Inside + After);
            Hide(hero, true);
            var hp = hero.GetComponent<Player>();
            if (hp != null) hp.Stun(Inside, true);
            var src = Own;
            float t = 0f;
            int chews = 0;
            while (t < Inside && Alive && hero != null && hero.activeInHierarchy)
            {
                t += Time.deltaTime;
                ModUtil.Teleport(hero, Mouth());
                if (chews < 2 && t >= (chews == 0 ? 0.25f : 0.6f) && BelMoraFx.GulperChew != null)
                {
                    chews++;
                    FxFactory.SpawnOwned(BelMoraFx.GulperChew, hero.transform.position, src);
                }
                yield return null;
            }
            Release(true);
        }

        Vector2 Mouth() { return ModUtil.SafePoint(Me, Me + Face * 12f, 2f); }

        void Release(bool spit)
        {
            var hero = m_held;
            m_held = null;
            if (hero == null) return;
            Hide(hero, false);
            if (!spit || !hero.activeInHierarchy) return;
            var to = ModUtil.SafePoint(Me, Me + Face * Spit, 6f);
            ModUtil.Teleport(hero, to);
            if (BelMoraFx.Splash != null) SystemPool.Spawn(BelMoraFx.Splash, to);
            if (BelMoraFx.Brine != null) FxFactory.SpawnOwned(BelMoraFx.Brine, to, Own);
        }

        // the hero is inside the eel: his sprite (and everything drawn on him) is hidden until he is spat out
        void Hide(GameObject hero, bool hide)
        {
            if (hide)
            {
                m_hidden.Clear();
                foreach (var r in hero.GetComponentsInChildren<Renderer>())
                    if (r.enabled) { r.enabled = false; m_hidden.Add(r); }
            }
            else
            {
                foreach (var r in m_hidden) if (r != null) r.enabled = true;
                m_hidden.Clear();
            }
        }

        void SetFull(float seconds)
        {
            bool was = m_full > 0f;
            m_full = seconds;
            if (was) return;
            SetStance(FullIdle, FullRun);
            SpeedScale(Slow);
        }

        public override float HeroHitScale(DamageInfo d) { return m_full > 0f ? Weak : 1f; }

        void Update()
        {
            if (m_full <= 0f) return;
            m_full -= Time.deltaTime;
            if (m_full > 0f) return;
            SetStance(null, null);
            SpeedScale(1f);
        }
    }
}
