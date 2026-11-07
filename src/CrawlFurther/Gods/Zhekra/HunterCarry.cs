using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Hunting Wasp, Hunter's Mark and Carry Off: she rises, circles and Marks the hero from range, then flies
    /// <see cref="HuntSpeed"/>x for <see cref="HuntTime"/> s. A lance sting that lands on a Marked hero seizes him: she
    /// carries him <see cref="CarryDist"/> px toward the biggest group of Zhekra (<see cref="CarryTime"/> s, he can't act)
    /// and drops him there. Tell: her wings beat white (Carry), the hero's shadow stays on the floor as he lifts.
    /// </summary>
    public class HunterCarry : ZhkBehaviour
    {
        public const float HuntSpeed = 1.3f, HuntTime = 4f, MarkRange = 170f, CarryDist = 50f, CarryTime = 0.6f, GroupRadius = 64f;
        /// <summary>The carrying loop (set by the kit).</summary>
        public static exSpriteAnimClip CarryClip;

        float m_huntUntil;
        bool m_carrying;

        protected override void OnEnable() { base.OnEnable(); m_huntUntil = 0f; m_carrying = false; }

        void Update()
        {
            if (m_huntUntil > 0f && Time.time >= m_huntUntil) { m_huntUntil = 0f; SpeedScale(1f); }
        }

        /// <summary>Clip event (Rise): the Mark from range.</summary>
        public void ModZhkHunterMark()
        {
            var hero = ModUtil.Hero();
            if (!Alive || hero == null || ZhekraFx.Mark == null) return;
            if (((Vector2)hero.transform.position - Me).sqrMagnitude > MarkRange * MarkRange) return;
            var p = hero.GetComponent<Player>();
            if (p != null) p.AddStatus(ZhekraFx.Mark, Own, "zhkhunt");
            m_huntUntil = Time.time + HuntTime;
            SpeedScale(HuntSpeed);
        }

        protected override void OnHeroContact(DamageInfo d, string effect)
        {
            if (effect != "ModZhkLance" || m_carrying || !HeroMarked()) return;
            var hero = ModUtil.Hero();
            if (hero == null || !ModStatus.AllowCrowdControl(hero)) return;
            var group = Biggest(hero.transform.position);
            if (!group.HasValue) return;
            StartCoroutine(Carry(hero, group.Value));
        }

        /// <summary>The Zhekra monster with the most kin round it (the hero's nearest on a tie), or none.</summary>
        Vector2? Biggest(Vector2 hp)
        {
            var all = ZhkBrain.Snapshot();
            ZhkBrain best = null; int bestN = -1; float bestD = 0f;
            foreach (var b in all)
            {
                if (b == null || !b.Alive || b.gameObject == gameObject) continue;
                int n = 0;
                foreach (var o in all) if (o != null && o != b && o.Alive && (o.Pos - b.Pos).sqrMagnitude <= GroupRadius * GroupRadius) n++;
                float dd = (b.Pos - hp).sqrMagnitude;
                if (n > bestN || (n == bestN && dd < bestD)) { best = b; bestN = n; bestD = dd; }
            }
            return best != null ? (Vector2?)best.Pos : null;
        }

        IEnumerator Carry(GameObject hero, Vector2 toward)
        {
            m_carrying = true;
            Vector2 from = hero.transform.position, dir = toward - from;
            float dist = Mathf.Min(CarryDist, dir.magnitude);
            dir = dir.sqrMagnitude > 1f ? dir.normalized : Face;
            var to = ModUtil.SafePoint(from, from + dir * dist);
            ZhkHero.On(hero).Lift(CarryTime, 7f);
            Hold(CarryClip, CarryTime);
            for (float t = 0f; t < CarryTime; t += Time.deltaTime)
            {
                if (!Alive || hero == null || !hero.activeInHierarchy) break;
                var p = Vector2.Lerp(from, to, t / CarryTime);
                ModUtil.Teleport(hero, p);
                ModUtil.Teleport(gameObject, ModUtil.SafePoint(p, p - dir * 6f));
                yield return null;
            }
            if (hero != null && Alive) ModUtil.Teleport(hero, to);
            m_carrying = false;
        }
    }
}
