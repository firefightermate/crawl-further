using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>The Pale Empress' blizzard: drifts after the hero (slower than he walks) for as long as it lives.</summary>
    public class YsvHomingFx : MonoBehaviour
    {
        public const float Speed = 34f, Turn = 2.5f;
        Vector2 m_vel;
        public void Reset() { m_vel = Vector2.zero; }
        void OnEnable() { m_vel = Vector2.zero; }
        void Update()
        {
            var hero = ModUtil.Hero();
            if (hero == null) return;
            Vector2 me = transform.position, to = (Vector2)hero.transform.position + new Vector2(0f, 8f);
            var d = to - me;
            if (d.sqrMagnitude < 1f) return;
            m_vel = Vector2.Lerp(m_vel, d.normalized * Speed, Mathf.Clamp01(Time.deltaTime * Turn));
            var n = me + m_vel * Time.deltaTime;
            if (!ModUtil.Clear(me, n)) { m_vel = Vector2.zero; return; }
            transform.position = new Vector3(n.x, n.y, transform.position.z);
        }
    }
}
