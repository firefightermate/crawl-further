using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Base of every Umbrael monster's quirk. Gives the body's parts, stance swaps, held poses, the choice of its next basic
    /// attack, and hooks on its echoes (<see cref="UmbraelEcho"/>), on the attacks it spawns, on hits from the hero and on
    /// its own hits on the hero (<see cref="Patch_UmbraelHits"/>). Instances are pooled: <see cref="OnEnable"/> puts
    /// everything back.
    /// </summary>
    public abstract class UmbraelBehaviour : MonsterBehaviour
    {
        protected Player Body { get; private set; }
        protected Health Hp { get; private set; }
        protected PlayerMovement Move { get; private set; }
        protected exSpriteAnimation Anim { get; private set; }
        protected exSprite Sprite { get; private set; }
        Attacks m_attacks;
        exSpriteAnimClip m_idle, m_run;
        int m_basic;

        protected override void Awake()
        {
            base.Awake();
            Body = GetComponent<Player>();
            Hp = GetComponent<Health>();
            Move = GetComponent<PlayerMovement>();
            Anim = GetComponent<exSpriteAnimation>();
            Sprite = GetComponent<exSprite>();
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
            NextBasic(0);
            SpeedScale(1f);
        }

        protected virtual void OnDisable() { StopAllCoroutines(); }

        /// <summary>True while the body is alive.</summary>
        public bool Alive { get { return Monster != null && Monster.Alive; } }

        protected Vector2 Me { get { return transform.position; } }
        protected Vector2 HeroPos { get { return Monster.HeroPos; } }
        protected DamageSource Own { get { return Monster.OwnSource(); } }
        protected bool InAttack { get { return Body != null && Body.GetInAttackState(); } }

        /// <summary>The direction the body faces, never zero.</summary>
        protected Vector2 Face
        {
            get { var f = Move != null ? Move.GetFaceDirection() : Vector2.right; return f.sqrMagnitude > 0.01f ? f.normalized : Vector2.right; }
        }

        protected static float AngleTo(Vector2 from, Vector2 to)
        {
            var d = to - from;
            return d.sqrMagnitude < 0.01f ? 0f : Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
        }

        // ------------------------------------------------------------------------------------- clips and stances
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
            if (Anim == null || !gameObject.activeInHierarchy) return;
            var st = Body.GetState();
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

        /// <summary>Which basic attack (index in the kit's list) the body throws from now on.</summary>
        protected void NextBasic(int index)
        {
            m_basic = index;
            if (m_attacks != null) m_attacks.SetNextAttackOverride(index);
        }

        // the override covers one attack: put it back between attacks so the choice holds until changed
        protected virtual void LateUpdate()
        {
            if (m_attacks != null && !InAttack) m_attacks.SetNextAttackOverride(m_basic);
        }

        /// <summary>Scale the body's top speed (1 = its own).</summary>
        protected void SpeedScale(float k)
        {
            if (Move == null) return;
            if (Mathf.Abs(k - 1f) < 0.001f) Move.ResetSpeedMultiplier(); else Move.SetSpeedMultiplier(k);
        }

        /// <summary>Send a body clip event (invincibility, collision, shadow) from code.</summary>
        protected void BodyEvent(string method) { SendMessage(method, SendMessageOptions.DontRequireReceiver); }

        // ------------------------------------------------------------------------------------- hooks
        /// <summary>One of this body's basic attacks is about to echo: change when, where or how hard.</summary>
        public virtual void PlanEcho(EchoPlan plan) { }

        /// <summary>One of this body's echoes just struck at <paramref name="site"/>.</summary>
        public virtual void EchoFired(GameObject echo, Vector2 site, EchoPlan plan) { }

        /// <summary>One of this body's attacks spawned <paramref name="fx"/> from <paramref name="template"/>.</summary>
        public virtual void OnAttackSpawned(GameObject fx, GameObject template) { }

        /// <summary>A hit from the hero is about to land: return true to block it outright.</summary>
        public virtual bool BlockHeroHit(DamageInfo d) { return false; }

        /// <summary>A hit from the hero is about to land: the factor its damage is multiplied by.</summary>
        public virtual float HeroHitScale(DamageInfo d) { return 1f; }

        /// <summary>A hit from the hero landed (called before its damage is applied).</summary>
        public virtual void OnHeroHit(DamageInfo d) { }

        /// <summary>One of this body's hits is about to land on the hero: return true to hold it back (it does nothing now).</summary>
        public virtual bool HoldHitOnHero(DamageInfo d) { return false; }

        /// <summary>One of this body's hits landed on the hero (called before its damage is applied).</summary>
        public virtual void OnHitHero(DamageInfo d) { }

        /// <summary>True if the hit came from an effect made from <paramref name="template"/> (or its echoes).</summary>
        protected static bool From(DamageInfo d, GameObject template)
        {
            var src = d != null && d.m_source != null ? d.m_source.m_source : null;
            return src != null && template != null && src.name.StartsWith(template.name);
        }

        /// <summary>True if the hit came from a moving projectile rather than a swing.</summary>
        protected static bool IsShot(DamageInfo d)
        {
            var src = d != null && d.m_source != null ? d.m_source.m_source : null;
            if (src == null) return false;
            var pm = src.GetComponent<ParticleMotion>();
            return pm != null && pm.enabled && pm.GetVelocity().sqrMagnitude > 400f;
        }
    }
}
