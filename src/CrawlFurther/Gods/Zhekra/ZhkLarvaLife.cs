using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A Hive Larva's clock: it withers 8 s after it hatches (MonsterTraits.lifetime), but not while a Brood Mother is
    /// within <see cref="MotherRadius"/> px (Royal Jelly) or for a while after a Sun Scarab's ball lets it out.
    /// </summary>
    public class ZhkLarvaLife : MonsterBehaviour
    {
        public const float MotherRadius = 100f;
        float m_protectUntil;

        void OnEnable() { m_protectUntil = 0f; }

        /// <summary>Hold off withering for <paramref name="seconds"/> more.</summary>
        public void Protect(float seconds) { m_protectUntil = Mathf.Max(m_protectUntil, Time.time + seconds); }

        void Update()
        {
            if (Monster == null || !Monster.Alive) return;
            bool safe = Time.time < m_protectUntil || MotherJelly.Near(transform.position, MotherRadius);
            if (!safe) return;
            // the age clock ticks in ModMonster.Update: take back what it added this frame
            float age = R.Get<float>(Monster, "m_age");
            if (age > 0f) R.Set(Monster, "m_age", Mathf.Max(0f, age - Time.deltaTime));
        }

        /// <summary>Larvae within <paramref name="radius"/> px of <paramref name="at"/>: hold off their withering.</summary>
        public static void ProtectAround(Vector2 at, float radius, float seconds)
        {
            foreach (var b in ZhkBrain.Snapshot())
            {
                if (b == null || !b.Alive || !b.IsLarva || (b.Pos - at).sqrMagnitude > radius * radius) continue;
                var l = b.GetComponent<ZhkLarvaLife>();
                if (l != null) l.Protect(seconds);
            }
        }
    }
}
