using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Base of every Vhorrul monster's quirk: body helpers (stances, holds, speed, steering a bot), the floor around the
    /// feet (wax, fire), holy fire from a Votive Reliquary's Anoint, the clip events several monsters share, and hooks on
    /// hits from the hero and on hits it lands (<see cref="Patch_VhorrulHits"/>). Instances are pooled: <see cref="OnEnable"/>
    /// puts everything back.
    /// </summary>
    public abstract class VhorrulBehaviour : MonsterBehaviour
    {
        /// <summary>Hits that burn and light wax, left from an Anoint.</summary>
        public const int AnointHits = 2;

        protected Player Body { get; private set; }
        protected Health Hp { get; private set; }
        protected PlayerMovement Move { get; private set; }
        protected exSpriteAnimation Anim { get; private set; }
        exSpriteAnimClip m_idle, m_run;
        bool m_steering;
        int m_anointed;

        protected override void Awake()
        {
            base.Awake();
            Body = GetComponent<Player>();
            Hp = GetComponent<Health>();
            Move = GetComponent<PlayerMovement>();
            Anim = GetComponent<exSpriteAnimation>();
            if (Body != null)
            {
                m_idle = R.Get<exSpriteAnimClip>(Body, "m_animationIdle");
                m_run = R.Get<exSpriteAnimClip>(Body, "m_animationRun");
            }
        }

        protected virtual void OnEnable()
        {
            SetStance(null, null);
            SpeedScale(1f);
            SetAnointed(0);
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
        protected bool IsBot { get { return Body != null && Body.GetIsAI(); } }
        protected bool InAttack { get { return Body != null && Body.GetInAttackState(); } }
        protected float HeroDist { get { return (HeroPos - Me).magnitude; } }

        /// <summary>The direction the body faces (its aim), never zero.</summary>
        protected Vector2 Face
        {
            get { var f = Move != null ? Move.GetFaceDirection() : Vector2.right; return f.sqrMagnitude > 0.01f ? f.normalized : Vector2.right; }
        }

        protected static float AngleOf(Vector2 d) { return d.sqrMagnitude < 0.01f ? 0f : Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg; }

        // ------------------------------------------------------------------------------------- the floor
        /// <summary>Unlit monster wax under the feet.</summary>
        protected bool InWax { get { return WaxPuddleFx.HealsAt(Me); } }

        /// <summary>The nearest fire within <paramref name="r"/> px of the feet (pools, pyres, flames), or null.</summary>
        protected IgniterFx FireNear(float r) { return IgniterFx.Nearest(Me, r); }

        /// <summary>Clip event: light every wax puddle within <paramref name="radius"/> px.</summary>
        public void VhLightWax(float radius)
        {
            foreach (var w in WaxPuddleFx.Snapshot())
                if (w != null && w.isActiveAndEnabled && (w.Pos - Me).sqrMagnitude <= radius * radius) w.Ignite(Own);
        }

        /// <summary>Clip event: the wax this body pours from now on is a new touch-paper line.</summary>
        public void VhNewLine() { WaxPuddleFx.NewLine(gameObject); }

        /// <summary>Clip event: turn to face the hero.</summary>
        public void VhFaceHero() { Monster.FaceHero(); }

        // ------------------------------------------------------------------------------------- body
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

        /// <summary>Freeze the body for <paramref name="seconds"/> playing <paramref name="clip"/>; its clip events still fire.</summary>
        protected void Hold(exSpriteAnimClip clip, float seconds)
        {
            if (Body == null || !Alive) return;
            Body.Stun(seconds, true);
            if (clip != null && Anim != null) { Ensure(clip); Anim.Play(clip.name); }
        }

        /// <summary>Scale the body's top speed (1 = its own).</summary>
        protected void SpeedScale(float k)
        {
            if (Move == null) return;
            if (Mathf.Abs(k - 1f) < 0.001f) Move.ResetSpeedMultiplier(); else Move.SetSpeedMultiplier(k);
        }

        /// <summary>Drive a bot's stick toward <paramref name="target"/> (null hands it back). Never touches a player's body.</summary>
        protected void Steer(Vector2? target)
        {
            if (Move == null) return;
            if (target.HasValue && IsBot)
            {
                var d = target.Value - Me;
                Move.SetInputOverride(d.sqrMagnitude > 1f ? d.normalized : Vector2.zero);
                m_steering = true;
            }
            else if (m_steering) { Move.ResetInputOverride(); m_steering = false; }
        }

        /// <summary>Spawn attack slot <paramref name="slot"/> (as a clip's AnimAttack would).</summary>
        protected void Attack(int slot) { if (slot >= 0) SendMessage("AnimAttack", slot, SendMessageOptions.DontRequireReceiver); }

        /// <summary>Hurt this body (fire burning it out of the wax).</summary>
        protected void HurtSelf(float amount)
        {
            if (Hp == null || !Alive) return;
            Hp.Damage(new DamageInfo(amount, 0.2f, 0f, Vector2.up, new DamageSource(gameObject, null, null)), true);
        }

        protected void AddStatus(Status s, string name) { if (s != null && Body != null && Alive) Body.AddStatus(s, Own, name); }

        protected void RemoveStatus(Status s)
        {
            var sm = Body != null ? Body.GetStatusManager() : null;
            if (s != null && sm != null) sm.RemoveStatus(s);
        }

        protected bool HasStatus(Status s)
        {
            var sm = Body != null ? Body.GetStatusManager() : null;
            return s != null && sm != null && sm.GetHasStatusWithClass(s.m_class);
        }

        // ------------------------------------------------------------------------------------- holy fire
        /// <summary>Hits left that burn and light wax (a Votive Reliquary's Anoint).</summary>
        public int Anointed { get { return m_anointed; } }

        public void SetAnointed(int hits)
        {
            m_anointed = Mathf.Max(0, hits);
            if (VhorrulPack.AnointInd != null) ModInd.Set(gameObject, VhorrulPack.AnointInd, m_anointed > 0);
        }

        // ------------------------------------------------------------------------------------- hooks
        /// <summary>A hit from the hero is about to land: return true to block it outright.</summary>
        public virtual bool BlockHeroHit(DamageInfo d) { return false; }

        /// <summary>A hit from the hero is about to land: the factor its damage is multiplied by.</summary>
        public virtual float HeroHitScale(DamageInfo d) { return 1f; }

        /// <summary>A hit from the hero landed (before its damage is applied).</summary>
        public virtual void OnHeroHit(DamageInfo d) { }

        /// <summary>One of this body's hits is about to land on the hero: change it here (damage, status, knockback).</summary>
        public virtual void OnHitHero(DamageInfo d) { }

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

        /// <summary>True if the hit came from an effect spawned from <paramref name="template"/>.</summary>
        protected static bool From(DamageInfo d, GameObject template)
        {
            var src = d != null && d.m_source != null ? d.m_source.m_source : null;
            return src != null && template != null && src.name.StartsWith(template.name);
        }

        /// <summary>True if the hit carries fire (a burning status, or one of the floor's fires).</summary>
        protected static bool IsFire(DamageInfo d)
        {
            if (d == null) return false;
            if (d.m_status != null && VhorrulFx.OnFire != null && d.m_status.m_class == VhorrulFx.OnFire.m_class) return true;
            var src = d.m_source != null ? d.m_source.m_source : null;
            return src != null && src.GetComponent<IgniterFx>() != null;
        }
    }

    /// <summary>A Vhorrul monster with no quirk of its own: the shared clip events, holy fire and the hooks.</summary>
    public class VhorrulMonster : VhorrulBehaviour { }
}
