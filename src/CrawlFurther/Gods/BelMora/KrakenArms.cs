using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Abyss Kraken. Erupt: an arm bursts up under the hero, and one out of each of the <see cref="MaxPools"/> brine pools
    /// nearest him (root). Arms Out: every arm it sends up stays <see cref="KrakenArmFx.Stay"/> s and swats a hero who
    /// passes close; with <see cref="Open"/> or more arms out its head is open and takes x<see cref="OpenTaken"/>. Tell: the
    /// arm count, and the mantle blanches while it is open (the Open stance).
    /// </summary>
    public class KrakenArms : BelBehaviour
    {
        public const float PoolRange = 110f, Beat = 0.18f, OpenTaken = 1.35f;
        public const int MaxPools = 3, Open = 3;
        /// <summary>The open (blanched) stance (set by the kit).</summary>
        public static exSpriteAnimClip OpenIdle, OpenRun;

        readonly List<KrakenArmFx> m_arms = new List<KrakenArmFx>();
        bool m_open;

        protected override void OnEnable() { base.OnEnable(); m_arms.Clear(); m_open = false; }

        /// <summary>Clip event (Erupt): the arms burst up.</summary>
        public void BelKrakenErupt()
        {
            if (!Alive || BelMoraFx.Tentacle == null || !gameObject.activeInHierarchy) return;
            Vector2 hp = HeroPos;
            Rise(hp);
            var spots = new List<Vector2>();
            foreach (var p in BelWater.Near(hp, PoolRange))
            {
                if (spots.Count >= MaxPools) break;
                // from the edge of the pool nearest the hero, never right on top of him
                var d = hp - p.Pos;
                var at = p.Contains(hp) ? p.Pos : p.Pos + Vector2.Scale(d.normalized, new Vector2(p.Rx * 0.7f, p.Ry * 0.7f));
                if ((at - hp).sqrMagnitude < 14f * 14f) continue;
                spots.Add(at);
            }
            if (spots.Count > 0) StartCoroutine(RiseLater(spots));
        }

        IEnumerator RiseLater(List<Vector2> spots)
        {
            yield return new WaitForSeconds(Beat);
            foreach (var s in spots)
            {
                if (!Alive) yield break;
                Rise(s);
                yield return new WaitForSeconds(0.08f);
            }
        }

        void Rise(Vector2 at)
        {
            var go = FxFactory.SpawnOwned(BelMoraFx.Tentacle, at, Own);
            var a = go != null ? go.GetComponent<KrakenArmFx>() : null;
            if (a != null) m_arms.Add(a);
        }

        public override float HeroHitScale(DamageInfo d) { return m_open ? OpenTaken : 1f; }

        void Update()
        {
            if (!Alive) return;
            m_arms.RemoveAll(a => a == null || !a.Up);
            bool open = m_arms.Count >= Open;
            if (open == m_open) return;
            m_open = open;
            SetStance(open ? OpenIdle : null, open ? OpenRun : null);
        }
    }

    /// <summary>A kraken arm risen from the floor: it sways for <see cref="Stay"/> s and swats a hero within
    /// <see cref="Reach"/> px (at most once every <see cref="Every"/> s), then sinks.</summary>
    public class KrakenArmFx : MonoBehaviour
    {
        public const float Stay = 2f, Reach = 14f, Every = 0.7f, RiseTime = 0.4f;
        /// <summary>The sway, swat and sink clips (set by the kit).</summary>
        public static exSpriteAnimClip SwayClip, SwatClip, SinkClip;

        float m_age, m_swat;
        bool m_sunk;
        exSpriteAnimation m_anim;

        /// <summary>True while the arm is up (it counts toward Arms Out).</summary>
        public bool Up { get { return isActiveAndEnabled && !m_sunk; } }

        public void Arm() { m_age = 0f; m_swat = 0f; m_sunk = false; m_anim = GetComponent<exSpriteAnimation>(); }
        void OnEnable() { m_age = 0f; m_swat = 0f; m_sunk = false; }

        void Play(exSpriteAnimClip c)
        {
            if (m_anim == null || c == null) return;
            if (m_anim.GetAnimation(c.name) == null) m_anim.AddAnimation(c);
            m_anim.Play(c.name);
        }

        void Update()
        {
            float before = m_age;
            m_age += Time.deltaTime;
            if (m_sunk) return;
            if (before < RiseTime && m_age >= RiseTime) Play(SwayClip);
            if (m_age >= Stay) { m_sunk = true; Play(SinkClip); return; }
            if (m_age < RiseTime) return;
            m_swat -= Time.deltaTime;
            var hero = ModUtil.Hero();
            if (m_swat > 0f || hero == null || BelMoraFx.KrakenSwat == null) return;
            var d = (Vector2)hero.transform.position - (Vector2)transform.position;
            if (d.sqrMagnitude > Reach * Reach) return;
            m_swat = Every;
            Play(SwatClip);
            FxFactory.SpawnOwned(BelMoraFx.KrakenSwat, hero.transform.position, FxFactory.SourceOf(gameObject));
            StartCoroutine(BackToSway());
        }

        IEnumerator BackToSway()
        {
            yield return new WaitForSeconds(0.27f);
            if (!m_sunk) Play(SwayClip);
        }
    }
}
