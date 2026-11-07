using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.BelMora
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Tide Matriarch, Riptide Lanes: she plants her trident and for <see cref="Length"/> s a current runs from each of the
    /// <see cref="Lanes"/> nearest brine pools to her feet, as foam lanes <see cref="Width"/> px wide. A hero in a lane is
    /// carried along it toward her at <see cref="Carry"/> px/s; stepping sideways gets him off. Moon's Pull: with fewer
    /// than two pools in reach she calls the tide in early (two pools well up <see cref="CallDist"/> px from her), and her
    /// thrust hits +<see cref="Bonus"/> on a hero the current brought in. Tell: foam arrows along the lanes; her crown
    /// glows while they run (PlantLoop).
    /// </summary>
    public class MatriarchLanes : BelBehaviour
    {
        public const float Length = 3f, Width = 14f, Carry = 60f, Reach = 150f, CallDist = 70f, Bonus = 0.3f, Brought = 1.5f;
        public const int Lanes = 3;
        /// <summary>The planted, glowing loop (set by the kit).</summary>
        public static exSpriteAnimClip PlantLoop;

        readonly List<BelLine> m_lines = new List<BelLine>();
        float m_carried = -9f;

        protected override void OnDisable() { base.OnDisable(); ClearLines(); }

        /// <summary>Clip event (Plant, the trident bites the floor): the lanes start.</summary>
        public void BelLanes()
        {
            if (!Alive || !gameObject.activeInHierarchy) return;
            var pools = BelWater.Near(Me, Reach);
            if (pools.Count < 2)
            {
                BelTide.CallEarly(Me, 2, CallDist, Own);
                pools = BelWater.Near(Me, Reach);
            }
            var from = new List<Vector2>();
            for (int i = 0; i < pools.Count && from.Count < Lanes; i++)
                if (ModUtil.Clear(pools[i].Pos, Me)) from.Add(pools[i].Pos);
            if (from.Count == 0) return;
            Hold(PlantLoop, Length);
            StopAllCoroutines();
            StartCoroutine(Run(from));
        }

        IEnumerator Run(List<Vector2> from)
        {
            while (m_lines.Count < from.Count) m_lines.Add(new BelLine());
            for (int i = 0; i < from.Count; i++) m_lines[i].Lay(BelMoraFx.Lane, from[i], Feet, 12f, rotate: true);
            float t = 0f;
            while (t < Length && Alive)
            {
                t += Time.deltaTime;
                var hero = ModUtil.Hero();
                if (hero != null)
                {
                    Vector2 hp = hero.transform.position, me = Feet;
                    foreach (var a in from)
                    {
                        var ab = me - a;
                        float len = ab.magnitude;
                        if (len < 1f) continue;
                        var dir = ab / len;
                        float along = Vector2.Dot(hp - a, dir);
                        float across = Mathf.Abs(Vector2.Dot(hp - a, new Vector2(-dir.y, dir.x)));
                        if (along < -4f || along > len - 8f || across > Width * 0.5f) continue;
                        var to = ModUtil.SafePoint(hp, hp + dir * Carry * Time.deltaTime, 2f);
                        ModUtil.Teleport(hero, to);
                        m_carried = Time.time;
                        break;
                    }
                }
                yield return null;
            }
            ClearLines();
        }

        public override float HitOnHeroScale(DamageInfo d)
        {
            if (!HitFrom(d, BelMoraFx.TridentThrust) || Time.time - m_carried > Brought || d.m_amount <= 0f) return 1f;
            return (d.m_amount + Bonus) / d.m_amount;
        }

        void ClearLines() { foreach (var l in m_lines) l.Clear(); }
    }
}
