using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Brood Urchin, Clutch: three eggs lobbed onto marked spots by the hero (<see cref="BroodEggFx"/>). Spawning Tide:
    /// the eggs wait for the tide.
    /// </summary>
    public class BroodClutch : BelBehaviour
    {
        public const float Spread = 20f;

        /// <summary>Clip event (Clutch, the lob): the three spots are marked and the eggs come down on them.</summary>
        public void BelClutch()
        {
            if (!Alive || BelMoraFx.BroodEgg == null) return;
            Vector2 hp = HeroPos;
            var src = Own;
            var spots = new List<Vector2> { hp };
            float a0 = Random.Range(0f, 360f);
            for (int i = 0; i < 2; i++)
            {
                var off = (Vector2)(Quaternion.Euler(0, 0, a0 + i * 140f) * Vector2.right) * Spread;
                spots.Add(ModUtil.SafePoint(hp, hp + new Vector2(off.x, off.y * 0.5f), 4f));
            }
            foreach (var s in spots)
            {
                if (BelMoraFx.EggMark != null) SystemPool.Spawn(BelMoraFx.EggMark, s);
                FxFactory.SpawnOwned(BelMoraFx.BroodEgg, s, src);
            }
        }
    }

    /// <summary>
    /// A Brood Urchin egg on the floor. It waits for the tide: when the next tide comes in, it bursts in a ring of
    /// <see cref="Spines"/> spines, twice if it lies in one of the new pools; with no tide in <see cref="Fuse"/> s it bursts
    /// anyway. One hit pops it harmlessly. Tell: it pulses faster as the tide nears (PulseSlow, PulseFast).
    /// </summary>
    public class BroodEggFx : MonoBehaviour
    {
        public const float Fuse = 10f, Again = 0.35f, Land = 0.4f;
        public const int Spines = 6;
        /// <summary>The egg's pulses (set by the kit).</summary>
        public static exSpriteAnimClip SlowClip, FastClip;

        float m_age, m_again;
        bool m_done;
        int m_pulse;
        exSpriteAnimation m_anim;

        public void Arm()
        {
            m_age = 0f; m_again = -1f; m_done = false; m_pulse = 0;
            m_anim = GetComponent<exSpriteAnimation>();
        }

        void OnEnable() { Arm(); BelTide.TideIn += OnTide; }
        void OnDisable() { BelTide.TideIn -= OnTide; }

        void OnTide(List<BelTidePool> made)
        {
            if (m_done || m_age < Land) return;
            Vector2 me = transform.position;
            bool wet = false;
            foreach (var p in made) if (p != null && p.Inside(me)) wet = true;
            Burst();
            if (wet) m_again = Again; else Finish(null);
        }

        void Update()
        {
            m_age += Time.deltaTime;
            if (m_again > 0f)
            {
                m_again -= Time.deltaTime;
                if (m_again <= 0f) { Burst(); Finish(null); }
                return;
            }
            if (m_done || m_age < Land) return;
            if (HeroStrikes.Near(transform.position, 7f)) { Finish(BelMoraFx.EggPop); return; }
            float left = Mathf.Min(BelTide.SecondsToNext, Fuse - m_age);
            Pulse(left < 2.5f ? 2 : left < 6f ? 1 : 0);
            if (m_age >= Fuse) { Burst(); Finish(null); }
        }

        void Pulse(int n)
        {
            if (n == m_pulse || m_anim == null) return;
            m_pulse = n;
            var clip = n == 2 ? FastClip : SlowClip;
            if (clip == null) return;
            if (m_anim.GetAnimation(clip.name) == null) m_anim.AddAnimation(clip);
            m_anim.Play(clip.name);
        }

        void Burst()
        {
            m_done = true;
            if (BelMoraFx.EggSpine == null) return;
            var src = FxFactory.SourceOf(gameObject);
            Vector2 at = (Vector2)transform.position + new Vector2(0f, 3f);
            float a0 = Random.Range(0f, 60f);
            for (int i = 0; i < Spines; i++) FxFactory.SpawnOwned(BelMoraFx.EggSpine, at, src, a0 + i * 360f / Spines);
            if (BelMoraFx.EggPop != null) SystemPool.Spawn(BelMoraFx.EggPop, transform.position);
        }

        void Finish(GameObject fx)
        {
            m_done = true;
            m_again = -1f;
            if (fx != null) SystemPool.Spawn(fx, transform.position);
            if (gameObject.activeInHierarchy) SystemPool.Despawn(gameObject);
        }
    }
}
