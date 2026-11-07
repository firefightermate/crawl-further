using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Spinehook, Reel It In: a harpoon that bites a bone pile (<see cref="OssHarpoonFx"/>) hauls it back along the rope in a
    /// straight line, hitting the hero if he is in the way, and the Spinehook eats it for a plate on arrival. Tell: the taut
    /// rope and the pile skidding along it.
    /// </summary>
    public class SpinehookReel : OssBehaviour
    {
        public const float ReelSpeed = 200f, HitDamage = 1.2f, HitRange = 8f;
        readonly List<GameObject> m_rope = new List<GameObject>();
        BonePileFx m_pile;

        protected override void OnDisable() { base.OnDisable(); Release(); }

        void Release()
        {
            OssFloor.Clear(m_rope);
            if (m_pile != null) m_pile.Locked = false;
            m_pile = null;
        }

        Vector2 Hand { get { return Me + new Vector2(Side * 16f, 16f); } }

        /// <summary>The harpoon bit <paramref name="pile"/>.</summary>
        public void Reel(BonePileFx pile)
        {
            if (!Alive || pile == null || m_pile != null) return;
            m_pile = pile;
            pile.Locked = true;
            StartCoroutine(Haul());
        }

        IEnumerator Haul()
        {
            bool hit = false;
            float t = 0f;
            while (m_pile != null && m_pile.isActiveAndEnabled && Alive && t < 2f)
            {
                t += Time.deltaTime;
                Vector2 p = m_pile.Pos, to = Me - p;
                float d = to.magnitude;
                if (d < 10f)
                {
                    var pile = m_pile; m_pile = null;
                    OssFloor.Clear(m_rope);
                    pile.Consume();
                    Monster.AddPlate(Mathf.Max(1, Monster.Traits.maxPlates));
                    yield break;
                }
                Vector2 next = p + to / d * Mathf.Min(d, ReelSpeed * Time.deltaTime);
                m_pile.transform.position = new Vector3(next.x, next.y, m_pile.transform.position.z);
                OssFloor.Line(m_rope, OssivarFx.RopeSeg, Hand, next + new Vector2(0f, 2f));
                if (!hit && Hero != null && ((Vector2)Hero.transform.position - next).sqrMagnitude < HitRange * HitRange)
                {
                    hit = true;
                    HurtHero(HitDamage, 0.8f);
                }
                yield return null;
            }
            Release();
        }
    }
}
