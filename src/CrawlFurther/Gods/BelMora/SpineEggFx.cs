using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Spinewalker egg: arms after <see cref="ArmDelay"/> s, then bursts in a spine ring when the hero comes within
    /// <see cref="Range"/> px (or at <see cref="Fuse"/> s). Adrift: an egg in brine floats free and drifts after the hero at
    /// <see cref="Drift"/> px/s until it bursts or leaves the pool. Tell: the drifting egg bobs in a ring of foam.
    /// </summary>
    public class SpineEggFx : MonoBehaviour
    {
        public const float ArmDelay = 0.6f, Range = 18f, Fuse = 7f, Drift = 15f;
        /// <summary>The drifting loop and the resting idle (set by the kit).</summary>
        public static exSpriteAnimClip DriftClip, IdleClip;

        float m_age;
        bool m_done, m_drifting;
        exSpriteAnimation m_anim;

        public void Arm() { m_age = 0f; m_done = false; m_drifting = false; m_anim = GetComponent<exSpriteAnimation>(); }
        void OnEnable() { Arm(); }

        void Update()
        {
            if (m_done) return;
            m_age += Time.deltaTime;
            if (m_age < ArmDelay) return;
            var hero = ModUtil.Hero();
            Vector2 me = transform.position;
            bool wet = BelWater.InBrine(me);
            if (wet != m_drifting) Show(wet);
            if (wet && hero != null)
            {
                var d = (Vector2)hero.transform.position - me;
                var n = me + d.normalized * Mathf.Min(Drift * Time.deltaTime, d.magnitude);
                if (ModUtil.Clear(me, n)) transform.position = new Vector3(n.x, n.y, transform.position.z);
            }
            bool near = false;
            if (hero != null)
            {
                var hh = hero.GetComponent<Health>();
                near = hh != null && hh.IsAlive() && ((Vector2)hero.transform.position - me).sqrMagnitude < Range * Range;
            }
            if (!near && m_age < Fuse) return;
            m_done = true;
            if (BelMoraFx.EggBurst != null) FxFactory.SpawnOwned(BelMoraFx.EggBurst, transform.position, FxFactory.SourceOf(gameObject));
            SystemPool.Despawn(gameObject);
        }

        void Show(bool drift)
        {
            m_drifting = drift;
            var clip = drift ? DriftClip : IdleClip;
            if (m_anim == null || clip == null) return;
            if (m_anim.GetAnimation(clip.name) == null) m_anim.AddAnimation(clip);
            m_anim.Play(clip.name);
        }
    }
}
