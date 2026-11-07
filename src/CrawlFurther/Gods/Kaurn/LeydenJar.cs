using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    /// <summary>
    /// Leyden Golem's Leyden Jar: it stores up to <see cref="Jar"/> sparks, not 3, and the jar shows them (it fills with light,
    /// one lit mark per spark). Its Shock Ring fires them all, then fills every Kaurn ally within 100 px to 3 sparks.
    /// </summary>
    public class LeydenJar : KaurnBehaviour
    {
        public const int Jar = 6;
        public const float AllyReach = 100f;
        public static readonly exSpriteAnimClip[] JarIdle = new exSpriteAnimClip[Jar + 1], JarRun = new exSpriteAnimClip[Jar + 1];
        int m_shown;

        protected override void OnEnable() { base.OnEnable(); Unit.maxPips = Jar; Unit.showMeter = false; m_shown = 0; }

        void Update()
        {
            int lv = Mathf.Clamp(Unit.pips, 0, Jar);
            if (lv == m_shown) return;
            m_shown = lv;
            SetStance(JarIdle[lv], JarRun[lv]);
        }

        /// <summary>Clip event after the ring: Kaurn allies near it get 3 sparks.</summary>
        public void KrnFillAllies()
        {
            foreach (var u in KaurnUnit.Snapshot())
            {
                if (u == null || u == Unit || !u.Alive || (u.FeetPos - Me).sqrMagnitude > AllyReach * AllyReach) continue;
                u.pips = Mathf.Max(u.pips, Mathf.Min(u.maxPips, KaurnUnit.MaxPips));
                u.Pop();
                if (KaurnFx.HitFx != null) SystemPool.Spawn(KaurnFx.HitFx, u.Top);
            }
        }
    }
}
