using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Drowned Bell. Cast the Bell: he hurls the bell at the hero; its shadow grows on the spot for
    /// <see cref="Flight"/> s, then it lands mouth-down (a hit) and stands there in a brine pool of its own. Bare Back:
    /// until he heaves it back on he is light and quick (x<see cref="BareSpeed"/>), punches instead of tolling, and
    /// takes x<see cref="BareTaken"/> damage. The lift takes <see cref="LiftTime"/> s at the bell and ends in a toll round
    /// him. Tell: the bell standing in its pool, his raw hunched back with the tentacles hanging loose (the Bare stance).
    /// </summary>
    public class BellCast : BelBehaviour
    {
        public const float Flight = 0.8f, BareSpeed = 1.3f, BareTaken = 1.4f, LiftTime = 2f, Reach = 22f, FightFirst = 1.5f, MaxBare = 8f;
        /// <summary>The bare stance, the bare special (a punch) and the lift (set by the kit).</summary>
        public static exSpriteAnimClip BareIdle, BareRun, BareSpecial, LiftClip;

        bool m_bare, m_lifting, m_landed;
        float m_bareFor;
        Vector2 m_bellAt;
        GameObject m_bell;

        protected override void OnEnable() { base.OnEnable(); m_bare = false; m_lifting = false; m_landed = false; m_bell = null; }
        protected override void OnDisable() { base.OnDisable(); DropBell(); }

        /// <summary>Clip event (Cast): the bell leaves his hands toward where the hero stands.</summary>
        public void BelCastBell()
        {
            if (!Alive || m_bare) return;
            var target = ModUtil.SafePoint(Me, HeroPos, 8f);
            m_bellAt = target;
            SetBare(true);
            StartCoroutine(Fly(target, Own));
        }

        IEnumerator Fly(Vector2 at, DamageSource src)
        {
            if (BelMoraFx.BellShadow != null) SystemPool.Spawn(BelMoraFx.BellShadow, at);
            if (BelMoraFx.CastBellFly != null) SystemPool.Spawn(BelMoraFx.CastBellFly, at);
            yield return new WaitForSeconds(Flight);
            if (!Alive) yield break;
            if (BelMoraFx.CastBellLand != null) FxFactory.SpawnOwned(BelMoraFx.CastBellLand, at, src);
            BelTide.Well(at, src);
            yield return new WaitForSeconds(0.3f);
            if (!Alive || !m_bare) yield break;
            if (BelMoraFx.BellStand != null) m_bell = FxFactory.SpawnOwned(BelMoraFx.BellStand, at, src);
            m_landed = true;
        }

        void SetBare(bool bare)
        {
            m_bare = bare;
            m_bareFor = 0f;
            m_landed = false;
            SetStance(bare ? BareIdle : null, bare ? BareRun : null);
            NextBasic(bare ? 1 : 0);
            SetSpecialClip(bare ? BareSpecial : null);
            SpeedScale(bare ? BareSpeed : 1f);
            if (!bare) Steer(null);
        }

        public override float HeroHitScale(DamageInfo d) { return m_bare ? BareTaken : 1f; }

        void Update()
        {
            if (!Alive || !m_bare || m_lifting) return;
            m_bareFor += Time.deltaTime;
            var d = m_bellAt - Me;
            bool near = m_landed && Mathf.Abs(d.y) < 10f && d.magnitude < Reach;
            if (near || m_bareFor > MaxBare) { StartCoroutine(Lift()); return; }
            // a bot goes back for its bell after a moment of bare fighting; a person walks there themselves
            if (m_landed && m_bareFor > FightFirst && !PlayerDriven && !InAttack)
            {
                var stand = m_bellAt + new Vector2(Me.x <= m_bellAt.x ? -16f : 16f, 0f);
                var s = stand - Me;
                Steer(s.sqrMagnitude > 4f ? (Vector2?)s.normalized : null);
            }
        }

        IEnumerator Lift()
        {
            m_lifting = true;
            Steer(null);
            Monster.Face(m_bellAt);
            DropBell();
            Hold(LiftClip, LiftTime);
            yield return new WaitForSeconds(LiftTime - 0.2f);
            m_lifting = false;
            if (!Alive) yield break;
            SetBare(false);
        }

        /// <summary>Clip event (Lift, last frame): the bell is back on and tolls round him.</summary>
        public void BelLiftToll()
        {
            if (Alive && BelMoraFx.LiftToll != null) FxFactory.SpawnOwned(BelMoraFx.LiftToll, Feet, Own);
        }

        void DropBell()
        {
            if (m_bell != null && m_bell.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(m_bell);
            m_bell = null;
        }
    }
}
