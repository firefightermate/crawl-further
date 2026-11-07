using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Crown of Thorns, Regrowth: every <see cref="Per"/> damage it takes, an arm breaks off (never below two) and crawls
    /// toward the nearest brine (<see cref="CrownArmFx"/>; one hit stamps it out). An arm that reaches brine grows back on
    /// the Crown <see cref="Regrow"/> s later and heals it <see cref="RegrowHeal"/>. Its Thorn Fling throws one thorn per arm
    /// it still has. Tell: the arm count is its shape (Idle/Run/Lash/Fling for 5, 4, 3 and 2 arms).
    /// </summary>
    public class CrownRegrowth : BelBehaviour
    {
        public const float Per = 2.5f, Regrow = 2f, RegrowHeal = 1.5f;
        public const int MaxArms = 5, MinArms = 2;
        /// <summary>Per arm count (index = arms, 2..5): the idle, run and fling clips (set by the kit).</summary>
        public static exSpriteAnimClip[] ArmIdle, ArmRun, ArmFling;

        int m_arms;
        float m_taken;

        protected override void OnEnable() { base.OnEnable(); m_arms = MaxArms; m_taken = 0f; }

        public override void OnHeroHit(DamageInfo d)
        {
            m_taken += d.m_amount;
            while (m_taken >= Per && m_arms > MinArms)
            {
                m_taken -= Per;
                SetArms(m_arms - 1);
                Shed();
            }
            if (m_arms <= MinArms) m_taken = Mathf.Min(m_taken, Per);
        }

        void SetArms(int n)
        {
            m_arms = Mathf.Clamp(n, MinArms, MaxArms);
            bool own = m_arms == MaxArms;
            SetStance(own || ArmIdle == null ? null : ArmIdle[m_arms], own || ArmRun == null ? null : ArmRun[m_arms]);
            NextBasic(MaxArms - m_arms);
            SetSpecialClip(own || ArmFling == null ? null : ArmFling[m_arms]);
        }

        void Shed()
        {
            if (BelMoraFx.CrownArm == null) return;
            var at = ModUtil.SafePoint(Me, Me + new Vector2(Random.Range(-10f, 10f), Random.Range(-4f, 4f)), 2f);
            var arm = FxFactory.SpawnOwned(BelMoraFx.CrownArm, at, Own);
            var c = arm != null ? arm.GetComponent<CrownArmFx>() : null;
            if (c != null) c.Owner = this;
        }

        /// <summary>One of its arms reached brine: it grows back a moment later.</summary>
        public void ArmHome()
        {
            if (Alive && gameObject.activeInHierarchy) StartCoroutine(GrowBack());
        }

        IEnumerator GrowBack()
        {
            yield return new WaitForSeconds(Regrow);
            if (!Alive || m_arms >= MaxArms) yield break;
            SetArms(m_arms + 1);
            Monster.Heal(RegrowHeal);
        }
    }

    /// <summary>
    /// A starfish arm broken off the Crown of Thorns: it crawls at <see cref="Speed"/> px/s toward the nearest brine,
    /// leaving a thin wet trail. One hit from the hero stamps it out; if it reaches brine it sinks in and the Crown grows
    /// it back. It dries out after <see cref="Life"/> s.
    /// </summary>
    public class CrownArmFx : MonoBehaviour
    {
        public const float Speed = 25f, Life = 9f, Seek = 220f;
        public CrownRegrowth Owner;
        float m_age;
        bool m_done;

        public void Arm() { m_age = 0f; m_done = false; Owner = null; }
        void OnEnable() { m_age = 0f; m_done = false; }

        void Update()
        {
            if (m_done) return;
            m_age += Time.deltaTime;
            Vector2 me = transform.position;
            if (Owner == null || !Owner.Alive || m_age > Life) { End(BelMoraFx.ArmDie); return; }
            if (HeroStrikes.Near(me, 7f)) { End(BelMoraFx.ArmDie); return; }
            if (BelWater.InBrine(me)) { End(BelMoraFx.ArmGrow); Owner.ArmHome(); return; }
            BelPool pool;
            if (!BelWater.Nearest(me, Seek, out pool)) return;
            var d = pool.Pos - me;
            var n = me + d.normalized * Mathf.Min(Speed * Time.deltaTime, d.magnitude);
            if (!ModUtil.Clear(me, n)) return;
            transform.position = new Vector3(n.x, n.y, transform.position.z);
            var s = transform.localScale;
            transform.localScale = new Vector3(d.x < 0f ? -Mathf.Abs(s.x) : Mathf.Abs(s.x), s.y, s.z);
        }

        void End(GameObject fx)
        {
            m_done = true;
            if (fx != null) SystemPool.Spawn(fx, transform.position);
            SystemPool.Despawn(gameObject);
        }
    }
}
