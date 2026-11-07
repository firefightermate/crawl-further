using System.Collections;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Util;

    /// <summary>
    /// Runtime brain of every mod monster instance (any Player whose prefab name starts with "Mod"), added on
    /// Player.Awake. Applies the monster's <see cref="MonsterTraits"/>, adds its <see cref="MonsterBehaviour"/>s, and
    /// receives the generic clip events below (ModGainPlates, ModSprint, ModPullHero, ModStepBehindHero, ModAmbush).
    /// </summary>
    public class ModMonster : MonoBehaviour
    {
        const float StillToHide = 0.9f, HiddenAlpha = 0.12f, SprintMult = 1.7f;

        static readonly MonsterTraits s_noTraits = new MonsterTraits();

        Player m_player;
        Health m_health;
        exSprite m_sprite;
        PlayerMovement m_move;
        Rigidbody m_rb;
        int m_plates;
        float m_still;
        float m_age;
        float m_regenAcc;
        bool m_regenOn;
        GameObject m_plateFx;
        float m_baseSpeed = -1f;

        /// <summary>This monster's traits (an empty set when none were registered).</summary>
        public MonsterTraits Traits { get; private set; }

        /// <summary>Hit-blocking plates it holds now.</summary>
        public int Plates { get { return m_plates; } }

        /// <summary>True while stealth or <see cref="MonsterTraits.hiddenAt"/> has it nearly invisible.</summary>
        public bool Unseen { get; private set; }

        /// <summary>True while its Health is alive.</summary>
        public bool Alive { get { return m_health != null && m_health.IsAlive(); } }

        /// <summary>The hero's position, or this monster's when there is no hero.</summary>
        public Vector2 HeroPos { get { var h = ModUtil.Hero(); return h != null ? (Vector2)h.transform.position : (Vector2)transform.position; } }

        void Awake()
        {
            m_player = GetComponent<Player>();
            m_health = GetComponent<Health>();
            m_sprite = GetComponent<exSprite>();
            m_move = GetComponent<PlayerMovement>();
            m_rb = GetComponent<Rigidbody>();
            Traits = MonsterTraits.Of(ModUtil.PrefabName(gameObject)) ?? s_noTraits;
            foreach (var t in Traits.behaviours)
                if (GetComponent(t) == null) gameObject.AddComponent(t);
        }

        void OnEnable()
        {
            m_plates = 0; Unseen = false; m_age = 0f; m_regenOn = false; m_still = 0f; DropPlateFx();
            // a pooled body that despawned while unseen must come back fully visible
            if (m_sprite != null) { var c = m_sprite.color; if (c.a < 1f) m_sprite.color = new Color(c.r, c.g, c.b, 1f); }
        }

        void OnDisable() { if (m_move != null && m_baseSpeed > 0f) R.Set(m_move, "m_speedMax", m_baseSpeed); }

        void Update()
        {
            if (!Alive)
            {
                SetAlpha(1f);
                if (m_plateFx != null) { m_plates = 0; DropPlateFx(); }
                return;
            }
            Vector2 me = transform.position;

            bool regen = false;
            if (Traits.regenAt != null && Traits.regenAt(me))
            {
                regen = m_health.GetHealthCurrent() < m_health.GetHealthMax();
                m_regenAcc += Time.deltaTime * Traits.regenPerSecond;
                if (m_regenAcc >= 0.25f) { m_health.Heal(m_regenAcc); m_regenAcc = 0f; }
            }
            if (regen != m_regenOn) { m_regenOn = regen; ModInd.Regen(gameObject, regen); }

            if (Traits.stealth || Traits.hiddenAt != null)
            {
                if (m_rb == null) m_rb = GetComponent<Rigidbody>();
                bool moving = m_move != null && m_rb != null && m_rb.velocity.sqrMagnitude > 4f;
                m_still = moving ? 0f : m_still + Time.deltaTime;
                Unseen = (Traits.hiddenAt != null && Traits.hiddenAt(me)) || (Traits.stealth && m_still > StillToHide);
                SetAlpha(Unseen ? HiddenAlpha : 1f);
            }

            if (Traits.lifetime > 0f)
            {
                m_age += Time.deltaTime;
                if (m_age >= Traits.lifetime)
                {
                    m_age = -999f;
                    if (Traits.expireFx != null) FxFactory.SpawnOwned(Traits.expireFx, me, OwnSource());
                    SendMessage("MsgDespawn", SendMessageOptions.DontRequireReceiver);
                }
            }
        }

        void SetAlpha(float a)
        {
            if (m_sprite == null) return;
            var c = m_sprite.color;
            if (Mathf.Abs(c.a - a) > 0.01f) m_sprite.color = new Color(c.r, c.g, c.b, Mathf.MoveTowards(c.a, a, Time.deltaTime * 4f));
        }

        // ------------------------------------------------------------------------------------------------ plates
        /// <summary>Add one plate if it holds fewer than <paramref name="cap"/>. Returns true if a plate was added.</summary>
        public bool AddPlate(int cap)
        {
            if (m_plates >= cap) return false;
            m_plates++;
            UpdatePlateFx();
            return true;
        }

        /// <summary>Clip event: gain <paramref name="n"/> plates, up to the larger of n and the traits' maxPlates.</summary>
        public void ModGainPlates(int n)
        {
            m_plates = Mathf.Min(Mathf.Max(n, Traits.maxPlates), m_plates + n);
            UpdatePlateFx();
        }

        /// <summary>A hero hit is about to land (Health.Damage prefix): true if a plate absorbed it.</summary>
        internal bool TryBlock(DamageInfo d)
        {
            if (m_plates <= 0 || d == null || d.m_amount <= 0f) return false;
            m_plates--;
            var brk = Traits.plateBreakFx ?? MonsterTraits.DefaultPlateBreakFx;
            if (brk != null) SystemPool.Spawn(brk, transform.position);
            UpdatePlateFx();
            return true;
        }

        void UpdatePlateFx()
        {
            var fx = Traits.plateFx ?? MonsterTraits.DefaultPlateFx;
            if (fx == null) { ShowPlateCount(); return; }
            if (m_plates > 0 && m_plateFx == null)
            {
                m_plateFx = SystemPool.Spawn(fx, transform.position);
                if (m_plateFx != null) { m_plateFx.transform.parent = transform; ModAttach.Front(m_plateFx, gameObject); }
            }
            if (m_plates <= 0 && m_plateFx != null) { SystemPool.Despawn(m_plateFx); m_plateFx = null; }
            ShowPlateCount();
        }

        // one shield per plate over the head wherever the count matters (it can hold more than one)
        void ShowPlateCount()
        {
            bool counts = Traits.maxPlates > 1 || Traits.showPlateCount || m_plates > 1;
            ModInd.Plates(gameObject, counts ? m_plates : 0);
        }

        // the orbiting plate is parented to us: never let it outlive the plates (death by a non-hero source keeps
        // plates > 0) or come back with a pooled instance
        void DropPlateFx()
        {
            if (m_plateFx == null) return;
            if (m_plateFx.transform.parent == transform) m_plateFx.transform.parent = null;
            if (m_plateFx.activeInHierarchy) SystemPool.Despawn(m_plateFx);
            m_plateFx = null;
        }

        // ------------------------------------------------------------------------------------------------ helpers
        /// <summary>Heal <paramref name="amount"/> and show the heal burst.</summary>
        public void Heal(float amount)
        {
            if (m_health == null) return;
            m_health.Heal(amount);
            ModInd.Heal(gameObject);
        }

        /// <summary>A damage source owned by this monster, credited as its own attacks are (<see cref="ModUtil.BodySource"/>),
        /// for <see cref="FxFactory.SpawnOwned"/>.</summary>
        public DamageSource OwnSource()
        {
            return ModUtil.BodySource(gameObject);
        }

        /// <summary>Turn to face the hero.</summary>
        public void FaceHero() { Face(HeroPos); }

        /// <summary>Turn to face <paramref name="target"/>.</summary>
        public void Face(Vector2 target)
        {
            if (m_move == null) return;
            var d = target - (Vector2)transform.position;
            if (d.sqrMagnitude < 0.01f) return;
            m_move.SetDirection(d.normalized);
        }

        // ------------------------------------------------------------------------------------------------ clip events
        /// <summary>Clip event: run 1.7x faster for <paramref name="seconds"/>.</summary>
        public void ModSprint(float seconds) { StopCoroutine("Sprint"); StartCoroutine("Sprint", seconds); }

        IEnumerator Sprint(float seconds)
        {
            if (m_move == null) yield break;
            if (m_baseSpeed < 0f) m_baseSpeed = R.Get<float>(m_move, "m_speedMax");
            R.Set(m_move, "m_speedMax", m_baseSpeed * SprintMult);
            ModInd.Haste(gameObject, true, seconds);
            yield return new WaitForSeconds(seconds);
            R.Set(m_move, "m_speedMax", m_baseSpeed);
            ModInd.Haste(gameObject, false);
        }

        /// <summary>Clip event: one tug of the hero toward this monster (fire it on several frames for a lure).</summary>
        public void ModPullHero(float strength)
        {
            var h = ModUtil.Hero();
            if (h == null || (h.transform.position - transform.position).sqrMagnitude > 150f * 150f) return;
            ModUtil.Pull(h, transform.position, strength);
        }

        /// <summary>Clip event: teleport 16 px behind the hero and turn to face them.</summary>
        public void ModStepBehindHero()
        {
            var h = ModUtil.Hero();
            if (h == null) return;
            var mv = h.GetComponent<PlayerMovement>();
            var face = mv != null ? mv.GetFaceDirection() : Vector2.right;
            var hero = (Vector2)h.transform.position;
            ModUtil.Teleport(gameObject, ModUtil.SafePoint(hero, hero - face.normalized * 16f));
            FaceHero();
        }

        /// <summary>Trade places with the hero, spawning <paramref name="flash"/> (optional) at both spots.</summary>
        public void SwapWithHero(GameObject flash)
        {
            var h = ModUtil.Hero();
            if (h == null) return;
            Vector2 me = transform.position, hero = h.transform.position;
            if (flash != null) { SystemPool.Spawn(flash, me); SystemPool.Spawn(flash, hero); }
            ModUtil.Teleport(h, me);
            ModUtil.Teleport(gameObject, hero);
            FaceHero();
        }

        /// <summary>Clip event: spawn attack effect <paramref name="normalEffect"/>, or the one after it when the monster was
        /// unseen (an ambush). Ends the stealth.</summary>
        public void ModAmbush(int normalEffect)
        {
            SendMessage("AnimAttack", Unseen ? normalEffect + 1 : normalEffect, SendMessageOptions.DontRequireReceiver);
            Unseen = false; m_still = 0f;
        }

        // ------------------------------------------------------------------------------------------------ echoes
        /// <summary>An echoing attack just spawned: leave an afterimage now and repeat the attack after the echo delay.</summary>
        internal void QueueEcho(GameObject echoTemplate, Vector3 pos, Quaternion rot, Vector3 scale, DamageSource src)
        {
            AfterimageFx.Spawn(m_sprite, transform.position, Traits.echoDelay + 0.15f);
            if (Traits.echoFx != null) SystemPool.Spawn(Traits.echoFx, transform.position);
            StartCoroutine(EchoLater(echoTemplate, pos, rot, scale, src));
        }

        IEnumerator EchoLater(GameObject tmpl, Vector3 pos, Quaternion rot, Vector3 scale, DamageSource src)
        {
            yield return new WaitForSeconds(Traits.echoDelay);
            if (tmpl == null) yield break;
            var go = SystemPool.SpawnBegin(tmpl, pos, rot);
            if (go == null) yield break;
            go.transform.localScale = scale;
            if (src != null)
                go.SendMessage(Constants.MSG_SETSPAWNER, ModUtil.HandOn(src, go), SendMessageOptions.DontRequireReceiver);
            SystemPool.SpawnFinalize(go);
        }
    }
}
