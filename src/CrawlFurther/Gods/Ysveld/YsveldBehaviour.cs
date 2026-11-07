using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Base of every Ysveld monster's quirk: the body's parts, stance swaps (its idle and run clips), held poses, the
    /// choice of its next basic attack and of its special clip, hooks on hits from the hero (<see cref="Patch_YsvHeroHits"/>)
    /// and on the attacks it spawns (<see cref="YsveldPack"/> forwards MonsterEvents.AttackSpawned). Instances are pooled:
    /// <see cref="OnEnable"/> puts everything back.
    /// </summary>
    public abstract class YsveldBehaviour : MonsterBehaviour
    {
        protected Player Body { get; private set; }
        protected Health Hp { get; private set; }
        protected PlayerMovement Move { get; private set; }
        protected exSpriteAnimation Anim { get; private set; }
        YsvMonster m_frost;
        /// <summary>The body's ice brain (on every Ysveld monster).</summary>
        protected YsvMonster Frost { get { if (m_frost == null) m_frost = GetComponent<YsvMonster>(); return m_frost; } }
        Attacks m_attacks;
        exSpriteAnimClip m_idle, m_run, m_special;
        AttackData m_specialData;

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
        }

        protected virtual void OnDisable() { StopAllCoroutines(); }

        /// <summary>True while the body is alive.</summary>
        public bool Alive { get { return Monster != null && Monster.Alive; } }

        /// <summary>Frost pips each of this body's frost hits adds (a widowed Bride adds two).</summary>
        public virtual int PipsPerHit { get { return 1; } }

        protected Vector2 Me { get { return transform.position; } }
        protected Vector2 HeroPos { get { return Monster.HeroPos; } }
        protected DamageSource Own { get { return Monster.OwnSource(); } }
        protected bool OnIce { get { return Frost != null && Frost.OnIce; } }

        /// <summary>The direction the body faces (its aim), never zero.</summary>
        protected Vector2 Face
        {
            get { var f = Move != null ? Move.GetFaceDirection() : Vector2.right; return f.sqrMagnitude > 0.01f ? f.normalized : Vector2.right; }
        }

        protected float Side { get { return Face.x >= 0f ? 1f : -1f; } }

        protected bool InAttack { get { return Body != null && Body.GetInAttackState(); } }

        protected bool Standing
        {
            get { if (Body == null) return false; var st = Body.GetState(); return st == Player.ePlayerState.Idle || st == Player.ePlayerState.Run; }
        }

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

        /// <summary>Freeze the body for <paramref name="seconds"/> playing <paramref name="clip"/> (a pose it holds).</summary>
        protected void Hold(exSpriteAnimClip clip, float seconds)
        {
            if (Body == null || !Alive) return;
            Body.Stun(seconds, true);
            if (clip != null && Anim != null) { Ensure(clip); Anim.Play(clip.name); }
        }

        /// <summary>Play a short flourish, but only while the body is just standing or running. True if it played.</summary>
        protected bool Flourish(exSpriteAnimClip clip)
        {
            if (Body == null || clip == null || !Alive || !Standing) return false;
            Body.StartStatusAnimation(clip);
            return true;
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

        /// <summary>Spawn <paramref name="tmpl"/> owned by this body at <paramref name="at"/> (rotated <paramref name="angle"/>).</summary>
        protected GameObject Spawn(GameObject tmpl, Vector2 at, float angle = 0f)
        {
            return tmpl != null ? FxFactory.SpawnOwned(tmpl, at, Own, angle) : null;
        }

        /// <summary>A visual at <paramref name="at"/> (not owned, no damage).</summary>
        protected static GameObject Show(GameObject tmpl, Vector2 at)
        {
            return tmpl != null ? SystemPool.Spawn(tmpl, at) : null;
        }

        // ------------------------------------------------------------------------------------- hooks
        /// <summary>A hit from the hero is about to land: return true to block it outright.</summary>
        public virtual bool BlockHeroHit(DamageInfo d) { return false; }

        /// <summary>A hit from the hero is about to land: the factor its damage is multiplied by.</summary>
        public virtual float HeroHitScale(DamageInfo d) { return 1f; }

        /// <summary>A hit from the hero landed (called before its damage is applied; it may change the hit).</summary>
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
