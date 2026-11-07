using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Base of every Bel'Mora monster's quirk. Gives the body's parts, stance swaps (its idle and run clips), held poses,
    /// the choice of its next basic attack and of its special clip, and hooks on hits from the hero, on its own hits on
    /// the hero (<see cref="Patch_BelMoraHits"/>) and on the attacks it spawns. Instances are pooled: <see cref="OnEnable"/>
    /// puts everything back.
    /// </summary>
    public abstract class BelBehaviour : MonsterBehaviour
    {
        protected Player Body { get; private set; }
        protected Health Hp { get; private set; }
        protected PlayerMovement Move { get; private set; }
        protected exSpriteAnimation Anim { get; private set; }
        protected exSprite Sprite { get; private set; }
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
        /// <summary>The art's feet (the sprite is drawn offset from the transform; the feet are 2 px above the cell bottom).</summary>
        protected Vector2 Feet { get { return Me + new Vector2(0f, Sprite != null ? Sprite.offset.y + 2f : 0f); } }
        protected Vector2 HeroPos { get { return Monster.HeroPos; } }
        protected DamageSource Own { get { return Monster.OwnSource(); } }

        /// <summary>The direction the body faces (its aim), never zero.</summary>
        protected Vector2 Face
        {
            get { var f = Move != null ? Move.GetFaceDirection() : Vector2.right; return f.sqrMagnitude > 0.01f ? f.normalized : Vector2.right; }
        }

        protected bool InAttack { get { return Body != null && Body.GetInAttackState(); } }

        /// <summary>True when a human player drives this body (bots get steered by the quirk, people never do).</summary>
        protected bool PlayerDriven
        {
            get { var pd = Body != null ? Body.GetPlayerData() : null; return pd != null && pd.IsHuman; }
        }

        protected Vector2 ToHero()
        {
            var d = HeroPos - Me;
            return d.sqrMagnitude > 0.01f ? d.normalized : Face;
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

        /// <summary>Freeze the body for <paramref name="seconds"/> playing <paramref name="clip"/> (a pose it holds itself).</summary>
        protected void Hold(exSpriteAnimClip clip, float seconds)
        {
            if (Body == null || !Alive) return;
            Body.Stun(seconds, true);
            if (clip != null && Anim != null) { Ensure(clip); Anim.Play(clip.name); }
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

        /// <summary>Step the body <paramref name="delta"/> px at once, stopping short of walls.</summary>
        protected void Shift(Vector2 delta)
        {
            var to = ModUtil.SafePoint(Me, Me + delta, 3f);
            ModUtil.Teleport(gameObject, to);
        }

        // ------------------------------------------------------------------------------------- hooks
        /// <summary>A hit from the hero is about to land: the factor its damage is multiplied by.</summary>
        public virtual float HeroHitScale(DamageInfo d) { return 1f; }

        /// <summary>A hit from the hero landed (called before its damage is applied).</summary>
        public virtual void OnHeroHit(DamageInfo d) { }

        /// <summary>One of this body's hits is about to land on the hero: the factor its damage is multiplied by.</summary>
        public virtual float HitOnHeroScale(DamageInfo d) { return 1f; }

        /// <summary>One of this body's hits landed on the hero (called before its damage is applied).</summary>
        public virtual void OnHitHero(DamageInfo d) { }

        /// <summary>One of this body's attacks spawned <paramref name="fx"/> from <paramref name="template"/>.</summary>
        public virtual void OnAttackSpawned(GameObject fx, GameObject template) { }

        /// <summary>The template a hit came from (its effect's prefab name), or null.</summary>
        protected static bool HitFrom(DamageInfo d, GameObject template)
        {
            var src = d != null && d.m_source != null ? d.m_source.m_source : null;
            return src != null && template != null && ModUtil.PrefabName(src) == template.name;
        }
    }

    /// <summary>
    /// Hits between the hero and a Bel'Mora monster: the monster's quirk may scale or react to a hit from the hero, and to
    /// one of its own hits on the hero, before the damage is applied.
    /// </summary>
    [HarmonyLib.HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_BelMoraHits
    {
        [HarmonyLib.HarmonyPriority(HarmonyLib.Priority.High)]
        static bool Prefix(Health __instance, DamageInfo damage, bool hitFriendly, bool __runOriginal)
        {
            if (!__runOriginal) return false;
            if (damage == null || damage.m_source == null || damage.m_amount <= 0f || damage.m_isDamageFromStatus) return true;
            var hero = ModUtil.Hero();
            if (hero == null || !__instance.IsAlive()) return true;
            if (__instance.gameObject == hero)
            {
                var owner = damage.m_source.m_sourceOwner;
                var mine = owner != null ? owner.GetComponent<BelBehaviour>() : null;
                if (mine == null || !mine.Alive) return true;
                damage.m_amount *= mine.HitOnHeroScale(damage);
                mine.OnHitHero(damage);
                return true;
            }
            var quirk = __instance.GetComponent<BelBehaviour>();
            if (quirk == null || !quirk.Alive || damage.m_source.m_sourceOwnerPlayer != hero) return true;
            if (!__instance.CanDamage(damage.m_source, hitFriendly)) return true;
            damage.m_amount *= quirk.HeroHitScale(damage);
            quirk.OnHeroHit(damage);
            return true;
        }
    }
}
