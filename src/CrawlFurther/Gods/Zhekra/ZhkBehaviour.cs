using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Base of every Zhekra monster's signature. Gives the body's parts, stance swaps (its idle and run clips), held poses,
    /// the choice of its next basic attack and of its special clip, the brood around it, and hooks on hits from the hero
    /// (<see cref="Patch_ZhkHeroHits"/>) and on its own hits landing on the hero. Instances are pooled:
    /// <see cref="OnEnable"/> puts everything back.
    /// </summary>
    public abstract class ZhkBehaviour : MonsterBehaviour
    {
        protected Player Body { get; private set; }
        protected Health Hp { get; private set; }
        protected PlayerMovement Move { get; private set; }
        protected exSpriteAnimation Anim { get; private set; }
        Attacks m_attacks;
        exSpriteAnimClip m_idle, m_run, m_special;
        AttackData m_specialData;
        bool m_override, m_wasInit, m_hasPending;
        exSpriteAnimClip m_pending;
        int m_basic;

        protected override void Awake()
        {
            base.Awake();
            Body = GetComponent<Player>();
            Hp = GetComponent<Health>();
            Move = GetComponent<PlayerMovement>();
            Anim = GetComponent<exSpriteAnimation>();
            m_attacks = Body != null ? R.Get<Attacks>(Body, "m_playerAttacks") : null;
            if (Body != null)
            {
                m_idle = R.Get<exSpriteAnimClip>(Body, "m_animationIdle");
                m_run = R.Get<exSpriteAnimClip>(Body, "m_animationRun");
            }
        }

        protected virtual void OnEnable()
        {
            m_wasInit = false; m_hasPending = false; m_pending = null;
            SetStance(null, null);
            if (m_specialData != null && m_special != null) m_specialData.m_animationFront = m_special;
            m_specialData = null;   // looked up again: a pooled body is re-inhabited with fresh attack data
            NextBasic(0);
            SpeedScale(1f);
        }

        protected virtual void OnDisable()
        {
            StopAllCoroutines();
            Steer(null);
        }

        /// <summary>True while the body is alive.</summary>
        public bool Alive { get { return Monster != null && Monster.Alive; } }

        protected Vector2 Me { get { return transform.position; } }
        protected Vector2 HeroPos { get { return Monster.HeroPos; } }
        protected DamageSource Own { get { return Monster.OwnSource(); } }

        /// <summary>The direction the body faces (its aim), never zero.</summary>
        protected Vector2 Face
        {
            get { var f = Move != null ? Move.GetFaceDirection() : Vector2.right; return f.sqrMagnitude > 0.01f ? f.normalized : Vector2.right; }
        }

        protected float Side { get { return transform.localScale.x >= 0f ? 1f : -1f; } }

        protected static float AngleTo(Vector2 from, Vector2 to)
        {
            var d = to - from;
            return d.sqrMagnitude < 0.01f ? 0f : Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
        }

        protected bool InAttack { get { return Body != null && Body.GetInAttackState(); } }

        /// <summary>The hero's distance, or a large number when there is no hero.</summary>
        protected float HeroDist
        {
            get { var h = ModUtil.Hero(); return h != null ? ((Vector2)h.transform.position - Me).magnitude : 9999f; }
        }

        /// <summary>True if the hero is under the Hornet's Mark.</summary>
        public static bool HeroMarked()
        {
            var hero = ModUtil.Hero();
            var p = hero != null ? hero.GetComponent<Player>() : null;
            var sm = p != null ? p.GetStatusManager() : null;
            return sm != null && sm.GetHasStatusWithClass("ModZhkMark");
        }

        /// <summary>True if the hero is Corroded (acid-coated).</summary>
        public static bool HeroCorroded()
        {
            var hero = ModUtil.Hero();
            var p = hero != null ? hero.GetComponent<Player>() : null;
            var sm = p != null ? p.GetStatusManager() : null;
            return sm != null && sm.GetHasStatusWithClass("ModZhkAcid");
        }

        /// <summary>Living Zhekra monsters (larvae included) within <paramref name="radius"/> px of <paramref name="at"/>,
        /// this body left out.</summary>
        protected List<ZhkBrain> Kin(Vector2 at, float radius)
        {
            var list = new List<ZhkBrain>();
            foreach (var b in ZhkBrain.Snapshot())
                if (b != null && b.gameObject != gameObject && b.Alive && (b.Pos - at).sqrMagnitude <= radius * radius) list.Add(b);
            return list;
        }

        // ------------------------------------------------------------------------------------- clips and stances
        /// <summary>Make <paramref name="clip"/> playable on this body (added once).</summary>
        protected void Ensure(exSpriteAnimClip clip)
        {
            if (clip != null && Anim != null && Anim.GetAnimation(clip.name) == null) Anim.AddAnimation(clip);
        }

        /// <summary>Swap the idle and run clips (null puts the body's own back) and show the new one at once.</summary>
        protected void SetStance(exSpriteAnimClip idle, exSpriteAnimClip run)
        {
            if (Body == null) return;
            idle = idle ?? m_idle; run = run ?? m_run;
            if (idle == null || run == null) return;
            var curIdle = R.Get<exSpriteAnimClip>(Body, "m_animationIdle");
            var curRun = R.Get<exSpriteAnimClip>(Body, "m_animationRun");
            if (curIdle == idle && curRun == run) return;
            Ensure(idle); Ensure(run);
            R.Set(Body, "m_animationIdle", idle);
            R.Set(Body, "m_animationRun", run);
            var st = Body.GetState();
            if (Anim == null || !gameObject.activeInHierarchy) return;
            if (st == Player.ePlayerState.Idle && curIdle != null && Anim.IsPlaying(curIdle.name)) Anim.Play(idle.name);
            else if (st == Player.ePlayerState.Run && curRun != null && Anim.IsPlaying(curRun.name)) Anim.Play(run.name);
        }

        /// <summary>Pick a stance from per-stage clip arrays (index clamped).</summary>
        protected void Stage(exSpriteAnimClip[] idles, exSpriteAnimClip[] runs, int i)
        {
            if (idles == null || runs == null || idles.Length == 0) return;
            i = Mathf.Clamp(i, 0, idles.Length - 1);
            SetStance(idles[i], runs[i]);
        }

        /// <summary>Freeze the body for <paramref name="seconds"/> playing <paramref name="clip"/> (a stun it brought on itself).</summary>
        protected void Hold(exSpriteAnimClip clip, float seconds)
        {
            if (Body == null || !Alive) return;
            Body.Stun(seconds, true);
            if (clip != null && Anim != null) { Ensure(clip); Anim.Play(clip.name); }
        }

        /// <summary>Play a short flourish, but only while the body is just standing or running.</summary>
        protected bool Flourish(exSpriteAnimClip clip)
        {
            if (Body == null || clip == null || !Alive) return false;
            var st = Body.GetState();
            if (st != Player.ePlayerState.Idle && st != Player.ePlayerState.Run) return false;
            Body.StartStatusAnimation(clip);
            return true;
        }

        /// <summary>Which basic attack (index in the kit's list) the body throws next, until changed.</summary>
        protected void NextBasic(int index)
        {
            m_basic = index;
            if (m_attacks != null) m_attacks.SetNextAttackOverride(index);
        }

        // a body's attack data arrives when a player (or the AI) inhabits it: apply the stored choices then
        protected virtual void LateUpdate()
        {
            bool init = m_attacks != null && m_attacks.GetInitialised();
            if (init && !m_wasInit)
            {
                m_attacks.SetNextAttackOverride(m_basic);
                if (!m_hasPending) m_hasPending = m_pending != null;
            }
            m_wasInit = init;
            if (init && m_hasPending) { m_hasPending = false; SetSpecialClip(m_pending); }
        }

        /// <summary>Swap the clip the special plays (null puts the kit's own back).</summary>
        protected void SetSpecialClip(exSpriteAnimClip clip)
        {
            m_pending = clip;
            if (m_attacks == null || !m_attacks.GetInitialised()) { m_hasPending = true; return; }
            if (m_specialData == null)
            {
                m_specialData = m_attacks.GetSpecialAttackData();
                if (m_specialData == null) return;
                if (m_special == null) m_special = m_specialData.m_animationFront;
            }
            clip = clip ?? m_special;
            Ensure(clip);
            m_specialData.m_animationFront = clip;
        }

        /// <summary>Scale the body's top speed (1 = its own).</summary>
        protected void SpeedScale(float k)
        {
            if (Move == null) return;
            if (Mathf.Abs(k - 1f) < 0.001f) Move.ResetSpeedMultiplier(); else Move.SetSpeedMultiplier(k);
        }

        /// <summary>Drive the body as if its stick were held at <paramref name="input"/> (length up to 1); null hands it back.</summary>
        protected void Steer(Vector2? input)
        {
            if (Move == null) return;
            if (input.HasValue) { Move.SetInputOverride(Vector2.ClampMagnitude(input.Value, 1f)); m_override = true; }
            else if (m_override) { Move.ResetInputOverride(); m_override = false; }
        }

        /// <summary>Spawn a heal burst and heal <paramref name="amount"/>.</summary>
        protected void HealSelf(float amount)
        {
            if (!Alive) return;
            Monster.Heal(amount);
        }

        // ------------------------------------------------------------------------------------- hooks
        /// <summary>A hit from the hero is about to land: return true to block it outright.</summary>
        public virtual bool BlockHeroHit(DamageInfo d) { return false; }

        /// <summary>A hit from the hero is about to land: the factor its damage is multiplied by.</summary>
        public virtual float HeroHitScale(DamageInfo d) { return 1f; }

        /// <summary>A hit from the hero landed (called before its damage is applied).</summary>
        public virtual void OnHeroHit(DamageInfo d) { }

        /// <summary>One of this body's attacks hit the hero (after its damage). <paramref name="effect"/>: the prefab name of
        /// the effect that hit (e.g. "ModZhkGrubBite").</summary>
        protected virtual void OnHeroContact(DamageInfo d, string effect) { }

        /// <summary>The game tells the attacker each time its attack lands (protected so the message reaches it on subclasses).</summary>
        protected void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_source == null || d.m_source.m_source == null || !Alive) return;
            if (d.m_victim == null || d.m_victim != ModUtil.Hero()) return;
            OnHeroContact(d, ModUtil.PrefabName(d.m_source.m_source));
        }

        /// <summary>True if the hit came from a moving projectile (a shot, a thrown blade) rather than a swing.</summary>
        protected static bool IsShot(DamageInfo d)
        {
            var src = d != null && d.m_source != null ? d.m_source.m_source : null;
            if (src == null) return false;
            var pm = src.GetComponent<ParticleMotion>();
            return pm != null && pm.enabled && pm.GetVelocity().sqrMagnitude > 400f;
        }
    }
}
