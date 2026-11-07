using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Base of every Jinx monster's quirk. Gives the body's parts, stance swaps (its idle and run clips), held poses,
    /// the choice of its next basic attack and of its special clip, and three hooks on hits from the hero
    /// (<see cref="Patch_JinxHeroHits"/>) and one on the attacks it spawns (<see cref="JinxPack"/> forwards
    /// MonsterEvents.AttackSpawned). Instances are pooled: <see cref="OnEnable"/> puts everything back.
    /// </summary>
    public abstract class JinxBehaviour : MonsterBehaviour
    {
        protected Player Body { get; private set; }
        protected Health Hp { get; private set; }
        protected PlayerMovement Move { get; private set; }
        protected exSpriteAnimation Anim { get; private set; }
        Attacks m_attacks;
        exSpriteAnimClip m_idle, m_run, m_special;
        AttackData m_specialData;
        bool m_override;

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

        protected float Side { get { return Face.x >= 0f ? 1f : -1f; } }

        protected static float AngleTo(Vector2 from, Vector2 to)
        {
            var d = to - from;
            return d.sqrMagnitude < 0.01f ? 0f : Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
        }

        protected bool InAttack { get { return Body != null && Body.GetInAttackState(); } }

        /// <summary>True when the hero stands within <paramref name="range"/> px and aims within <paramref name="degrees"/>
        /// of this body.</summary>
        protected bool HeroAimsAtMe(float degrees, float range)
        {
            var hero = ModUtil.Hero();
            var hp = hero != null ? hero.GetComponent<Player>() : null;
            if (hp == null) return false;
            Vector2 to = Me - (Vector2)hero.transform.position;
            if (to.sqrMagnitude > range * range || to.sqrMagnitude < 1f) return false;
            float a = Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg;
            return Mathf.Abs(Mathf.DeltaAngle(a, hp.GetFaceAngle())) <= degrees;
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

        /// <summary>Freeze the body for <paramref name="seconds"/> playing <paramref name="clip"/> (a stun it brought on itself).</summary>
        protected void Hold(exSpriteAnimClip clip, float seconds)
        {
            if (Body == null || !Alive) return;
            Body.Stun(seconds, true);
            if (clip != null && Anim != null) { Ensure(clip); Anim.Play(clip.name); }
        }

        /// <summary>Play a short flourish, but only while the body is just standing or running.</summary>
        protected void Flourish(exSpriteAnimClip clip)
        {
            if (Body == null || clip == null || !Alive) return;
            var st = Body.GetState();
            if (st == Player.ePlayerState.Idle || st == Player.ePlayerState.Run) Body.StartStatusAnimation(clip);
        }

        /// <summary>Which basic attack (index in the kit's list) the body throws next.</summary>
        protected void NextBasic(int index) { if (m_attacks != null) m_attacks.SetNextAttackOverride(index); }

        /// <summary>Swap the clip the special plays (null puts the kit's own back).</summary>
        protected void SetSpecialClip(exSpriteAnimClip clip)
        {
            if (m_attacks == null || !m_attacks.GetInitialised()) return;   // its data arrives when the body is inhabited
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

        // ------------------------------------------------------------------------------------- hooks
        /// <summary>A hit from the hero is about to land: return true to block it outright.</summary>
        public virtual bool BlockHeroHit(DamageInfo d) { return false; }

        /// <summary>A hit from the hero is about to land: the factor its damage is multiplied by.</summary>
        public virtual float HeroHitScale(DamageInfo d) { return 1f; }

        /// <summary>A hit from the hero landed (called before its damage is applied).</summary>
        public virtual void OnHeroHit(DamageInfo d) { }

        /// <summary>One of this body's attacks spawned <paramref name="fx"/> from <paramref name="template"/>.</summary>
        public virtual void OnAttackSpawned(GameObject fx, GameObject template) { }

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
