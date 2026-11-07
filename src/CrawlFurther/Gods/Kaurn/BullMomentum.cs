using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Thunder Bull's Stampede and Momentum: after pawing it charges straight at where the hero stood, dropping a stud every
    /// <see cref="StudEvery"/> px. The charge hits harder the further it has run (0.8, 1.2 after <see cref="Hard"/> px, 1.6
    /// after <see cref="Full"/>). A charge into a wall sticks its horns in: it stands dazed <see cref="StuckTime"/> s.
    /// </summary>
    public class BullMomentum : KaurnBehaviour
    {
        public const float Speed = 230f, MaxRun = 160f, Overshoot = 24f, Hard = 50f, Full = 100f, StuckTime = 1.5f, StudEvery = 36f, Ahead = 12f;
        public static exSpriteAnimClip ChargeClip, StuckClip;
        GameObject m_ram;
        bool m_struck;

        protected override void OnDisable() { base.OnDisable(); DropRam(); }

        /// <summary>A ram hit the hero: the charge stops growing.</summary>
        public void Struck() { m_struck = true; }

        void DropRam()
        {
            if (m_ram != null && m_ram.activeInHierarchy) SystemPool.Despawn(m_ram);
            m_ram = null;
        }

        /// <summary>Clip event after the third paw: the charge.</summary>
        public void KrnStampede() { StopAllCoroutines(); StartCoroutine(Charge()); }

        IEnumerator Charge()
        {
            Vector2 target = HeroPos, start = Me;
            var d = target - start;
            var dir = d.sqrMagnitude > 1f ? d.normalized : Face;
            float goal = Mathf.Min(MaxRun, d.magnitude + Overshoot);
            Monster.Face(target);
            Hold(ChargeClip, 3f);
            m_struck = false;
            float run = 0f, nextStud = StudEvery;
            int tier = -1;
            while (run < goal && Alive)
            {
                int t = run >= Full ? 2 : run >= Hard ? 1 : 0;
                if (!m_struck && t != tier)
                {
                    tier = t;
                    DropRam();
                    var tmpl = t == 2 ? KaurnFx.RamFull : t == 1 ? KaurnFx.RamHard : KaurnFx.Ram;
                    if (tmpl != null) m_ram = FxFactory.SpawnOwned(tmpl, Me + dir * Ahead + new Vector2(0f, 9f), Own);
                }
                float step = Speed * Time.deltaTime;
                Vector2 p = Me;
                if (!ModUtil.Clear(p + new Vector2(0f, 3f), p + new Vector2(0f, 3f) + dir * (step + 14f)))
                {
                    // the horns go into the wall
                    DropRam();
                    if (KaurnFx.HitFx != null) SystemPool.Spawn(KaurnFx.HitFx, p + dir * 16f + new Vector2(0f, 10f));
                    Release();
                    Hold(StuckClip, StuckTime);
                    yield break;
                }
                Place(p + dir * step);
                run += step;
                if (m_ram != null) m_ram.transform.position = new Vector3(Me.x + dir.x * Ahead, Me.y + dir.y * Ahead + 9f, m_ram.transform.position.z);
                if (run >= nextStud)
                {
                    nextStud += StudEvery;
                    if (KaurnFx.Stud != null) FxFactory.SpawnOwned(KaurnFx.Stud, Me - dir * 6f, Own);
                }
                yield return null;
            }
            DropRam();
            Release();
        }
    }
}
