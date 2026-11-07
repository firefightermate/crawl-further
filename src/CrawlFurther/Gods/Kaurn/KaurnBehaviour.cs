using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Base of every Kaurn monster's own mechanic: the body's parts, its static charge (<see cref="Unit"/>), stance swaps
    /// (its idle and run clips), self-held poses, the special's clip, speed and steering, and a hook on the attacks it spawns
    /// (<see cref="KaurnPack"/> forwards MonsterEvents.AttackSpawned). Instances are pooled: <see cref="OnEnable"/> resets.
    /// </summary>
    public abstract class KaurnBehaviour : MonsterBehaviour
    {
        protected Player Body { get; private set; }
        protected Health Hp { get; private set; }
        protected PlayerMovement Move { get; private set; }
        protected exSpriteAnimation Anim { get; private set; }
        protected KaurnUnit Unit { get; private set; }
        exSpriteAnimClip m_idle, m_run;
        bool m_override;

        protected override void Awake()
        {
            base.Awake();
            Body = GetComponent<Player>();
            Hp = GetComponent<Health>();
            Move = GetComponent<PlayerMovement>();
            Anim = GetComponent<exSpriteAnimation>();
            Unit = GetComponent<KaurnUnit>() ?? gameObject.AddComponent<KaurnUnit>();
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
        }

        protected virtual void OnDisable()
        {
            StopAllCoroutines();
            Steer(null);
        }

        /// <summary>True while the body is alive.</summary>
        public bool Alive { get { return Monster != null && Monster.Alive; } }

        protected Vector2 Me { get { return Unit != null ? Unit.FeetPos : (Vector2)transform.position; } }
        protected Vector2 HeroPos { get { return Monster.HeroPos; } }
        protected DamageSource Own { get { return Monster.OwnSource(); } }
        protected bool InAttack { get { return Body != null && Body.GetInAttackState(); } }

        /// <summary>The direction the body faces, never zero.</summary>
        protected Vector2 Face
        {
            get { var f = Move != null ? Move.GetFaceDirection() : Vector2.right; return f.sqrMagnitude > 0.01f ? f.normalized : Vector2.right; }
        }

        protected float Side { get { return Face.x >= 0f ? 1f : -1f; } }

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

        /// <summary>Freeze the body for <paramref name="seconds"/> playing <paramref name="clip"/> (a pose it holds itself).</summary>
        protected void Hold(exSpriteAnimClip clip, float seconds)
        {
            if (Body == null || !Alive) return;
            Body.Stun(seconds, true);
            if (clip != null && Anim != null) { Ensure(clip); Anim.Play(clip.name); }
        }

        /// <summary>End a <see cref="Hold"/> early.</summary>
        protected void Release()
        {
            if (Body != null && Body.GetState() == Player.ePlayerState.Stun) R.Set(Body, "m_stunTime", 0.01f);
        }

        /// <summary>Which basic attack (index in the kit's list) the body throws next, from now on.</summary>
        protected void NextBasic(int index)
        {
            var atk = Body != null ? R.Get<Attacks>(Body, "m_playerAttacks") : null;
            if (atk != null) atk.SetNextAttackOverride(index);
        }

        /// <summary>Swap the clip the special plays (null puts the kit's own back).</summary>
        protected void SetSpecialClip(exSpriteAnimClip clip)
        {
            var atk = Body != null ? R.Get<Attacks>(Body, "m_playerAttacks") : null;
            if (atk == null || !atk.GetInitialised()) return;   // its data arrives when the body is inhabited
            var data = atk.GetSpecialAttackData();
            if (data == null) return;
            if (m_special == null || m_specialData != data) { m_specialData = data; m_special = data.m_animationFront; }
            clip = clip ?? m_special;
            if (data.m_animationFront == clip) return;
            Ensure(clip);
            data.m_animationFront = clip;
        }
        exSpriteAnimClip m_special;
        AttackData m_specialData;

        /// <summary>Scale the body's top speed (1 = its own).</summary>
        protected void SpeedScale(float k)
        {
            if (Move == null) return;
            if (Mathf.Abs(k - 1f) < 0.001f) Move.ResetSpeedMultiplier(); else Move.SetSpeedMultiplier(k);
        }

        /// <summary>Drive the body as if its stick were held at <paramref name="input"/>; null hands it back.</summary>
        protected void Steer(Vector2? input)
        {
            if (Move == null) return;
            if (input.HasValue) { Move.SetInputOverride(Vector2.ClampMagnitude(input.Value, 1f)); m_override = true; }
            else if (m_override) { Move.ResetInputOverride(); m_override = false; }
        }

        /// <summary>Move the body to <paramref name="p"/> (its feet) at once.</summary>
        protected void Place(Vector2 feet)
        {
            ModUtil.Teleport(gameObject, feet - (Me - (Vector2)transform.position));
        }

        /// <summary>One of this body's attacks spawned <paramref name="fx"/> from <paramref name="template"/>.</summary>
        public virtual void OnAttackSpawned(GameObject fx, GameObject template) { }
    }
}
