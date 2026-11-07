using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Base of every Ossivar monster's own mechanic. Gives the body's parts, stance swaps (its idle and run clips), held poses,
    /// the choice of its next basic attack and of its special clip, and hooks on hits both ways (<see cref="Patch_OssHits"/>)
    /// and on the attacks it spawns (<see cref="OssivarPack"/> forwards MonsterEvents.AttackSpawned). Instances are pooled:
    /// <see cref="OnEnable"/> puts everything back.
    /// </summary>
    public abstract class OssBehaviour : MonsterBehaviour
    {
        protected Player Body { get; private set; }
        protected Health Hp { get; private set; }
        protected PlayerMovement Move { get; private set; }
        protected exSpriteAnimation Anim { get; private set; }
        Attacks m_attacks;
        exSpriteAnimClip m_idle, m_run, m_dead, m_special;
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
                m_dead = R.Get<exSpriteAnimClip>(Body, "m_animationDead");
            }
        }

        protected virtual void OnEnable()
        {
            SetStance(null, null);
            if (Body != null && m_dead != null) R.Set(Body, "m_animationDead", m_dead);
            if (m_specialData != null && m_special != null) m_specialData.m_animationFront = m_special;
            NextBasic(0);
            SpeedScale(1f);
        }

        protected virtual void OnDisable() { StopAllCoroutines(); }

        /// <summary>True while the body is alive.</summary>
        public bool Alive { get { return Monster != null && Monster.Alive && Hp != null && Hp.IsAlive(); } }

        protected Vector2 Me { get { return transform.position; } }
        protected Vector2 HeroPos { get { return Monster.HeroPos; } }
        protected DamageSource Own { get { return Monster.OwnSource(); } }
        protected static GameObject Hero { get { return ModUtil.Hero(); } }

        /// <summary>The direction the body faces (its aim), never zero.</summary>
        protected Vector2 Face
        {
            get { var f = Move != null ? Move.GetFaceDirection() : Vector2.right; return f.sqrMagnitude > 0.01f ? f.normalized : Vector2.right; }
        }

        protected float Side { get { return Face.x >= 0f ? 1f : -1f; } }
        protected bool InAttack { get { return Body != null && Body.GetInAttackState(); } }

        protected static float AngleOf(Vector2 d) { return d.sqrMagnitude < 0.0001f ? 0f : Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg; }
        protected static Vector2 Dir(float degrees) { float a = degrees * Mathf.Deg2Rad; return new Vector2(Mathf.Cos(a), Mathf.Sin(a)); }

        /// <summary>True while the hero carries the vanilla bleeding status.</summary>
        protected static bool HeroBleeding
        {
            get { var h = Hero; var p = h != null ? h.GetComponent<Player>() : null; return p != null && p.GetBleeding(); }
        }

        /// <summary>The hero's health as a share of its maximum (1 with no hero).</summary>
        protected static float HeroHealth
        {
            get
            {
                var h = Hero; var hp = h != null ? h.GetComponent<Health>() : null;
                return hp == null || hp.GetHealthMax() <= 0f ? 1f : hp.GetHealthCurrent() / hp.GetHealthMax();
            }
        }

        /// <summary>Hit the hero directly for <paramref name="amount"/> (a tick that is no attack effect of its own).</summary>
        public void HurtHero(float amount, float knock = 0f, Status status = null)
        {
            var h = Hero;
            var hh = h != null ? h.GetComponent<Health>() : null;
            if (hh == null || !hh.IsAlive()) return;
            Vector2 d = (Vector2)h.transform.position - Me;
            hh.Damage(new DamageInfo(amount, knock, 0f, d.sqrMagnitude > 0.01f ? d.normalized : Face, Own), false);
            if (status != null)
            {
                var hp = h.GetComponent<Player>();
                if (hp != null) hp.AddStatus(status, Own, "oss");
            }
        }

        /// <summary>True if the damage came from an effect spawned from <paramref name="template"/>.</summary>
        protected static bool From(DamageInfo d, GameObject template)
        {
            var src = d != null && d.m_source != null ? d.m_source.m_source : null;
            return src != null && template != null && ModUtil.PrefabName(src) == template.name;
        }

        // ------------------------------------------------------------------------------------- clips and stances
        /// <summary>Make <paramref name="clip"/> playable on this body (added once).</summary>
        protected void Ensure(exSpriteAnimClip clip)
        {
            if (clip != null && Anim != null && Anim.GetAnimation(clip.name) == null) Anim.AddAnimation(clip);
        }

        /// <summary>Play <paramref name="clip"/> now (an attack's next stage).</summary>
        protected void Play(exSpriteAnimClip clip)
        {
            if (clip == null || Anim == null) return;
            Ensure(clip);
            Anim.Play(clip.name);
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
            if (Anim == null || !gameObject.activeInHierarchy) return;
            var st = Body.GetState();
            if (st == Player.ePlayerState.Idle && curIdle != null && Anim.IsPlaying(curIdle.name)) Anim.Play(idle.name);
            else if (st == Player.ePlayerState.Run && curRun != null && Anim.IsPlaying(curRun.name)) Anim.Play(run.name);
        }

        /// <summary>Swap the death clip (the body's own comes back with the next life).</summary>
        protected void SetDeathClip(exSpriteAnimClip clip)
        {
            if (Body == null || clip == null) return;
            Ensure(clip);
            R.Set(Body, "m_animationDead", clip);
        }

        /// <summary>Freeze the body for <paramref name="seconds"/> playing <paramref name="clip"/> (a stun it brought on itself).</summary>
        protected void Hold(exSpriteAnimClip clip, float seconds)
        {
            if (Body == null || !Alive) return;
            Body.Stun(seconds, true);
            Play(clip);
        }

        /// <summary>Which basic attack (index in the kit's list) the body throws next, until set again.</summary>
        protected void NextBasic(int index) { if (m_attacks != null) m_attacks.SetNextAttackOverride(index); }

        /// <summary>Swap the clip the special plays (null puts the kit's own back).</summary>
        protected void SetSpecialClip(exSpriteAnimClip clip)
        {
            if (m_attacks == null) return;
            if (m_specialData == null)
            {
                m_specialData = m_attacks.GetSpecialAttackData();
                if (m_specialData == null) return;
                m_special = m_specialData.m_animationFront;
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

        /// <summary>Slide the body by <paramref name="step"/> unless a wall is in the way. Returns false if blocked.</summary>
        protected bool Slide(Vector2 step)
        {
            Vector2 me = Me;
            if (!ModUtil.Clear(me, me + step + step.normalized * 5f)) return false;
            ModUtil.Teleport(gameObject, me + step);
            return true;
        }

        // ------------------------------------------------------------------------------------- hooks
        /// <summary>A hit from the hero is about to land: return true to block it outright.</summary>
        public virtual bool BlockHeroHit(DamageInfo d) { return false; }

        /// <summary>A hit from the hero is about to land: the factor its damage is multiplied by.</summary>
        public virtual float HeroHitScale(DamageInfo d) { return 1f; }

        /// <summary>Any hit (from anyone) is about to land, after the scaling above: change it here.</summary>
        public virtual void BeforeDamage(DamageInfo d) { }

        /// <summary>One of this body's hits is about to land on the hero: the factor its damage is multiplied by.</summary>
        public virtual float HitHeroScale(DamageInfo d) { return 1f; }

        /// <summary>One of this body's hits landed on the hero.</summary>
        public virtual void OnHitHero(DamageInfo d) { }

        /// <summary>One of this body's attacks spawned <paramref name="fx"/> from <paramref name="template"/>.</summary>
        public virtual void OnAttackSpawned(GameObject fx, GameObject template) { }
    }
}
