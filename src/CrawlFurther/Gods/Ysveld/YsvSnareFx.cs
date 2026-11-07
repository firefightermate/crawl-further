using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A Rime Lurker snare on the floor. Off ice it lasts about 5 s (its clip). Set in Ice: a snare that lands on ice
    /// freezes into it (a faint blue glint, the Iced loop) and stays until that ice thaws, and adds two pips instead of
    /// one. A step into it (9 x 4.5 px) snaps it shut: the mod root and the pips.
    /// </summary>
    public class YsvSnareFx : MonoBehaviour
    {
        public const float RX = 9f, RY = 4.5f, ArmDelay = 0.3f, IcedMax = 40f;
        float m_age;
        bool m_done, m_checked, m_iced;

        public void Arm() { m_age = 0f; m_done = false; m_checked = false; m_iced = false; }
        void OnEnable() { Arm(); }

        void Update()
        {
            if (m_done) return;
            m_age += Time.deltaTime;
            Vector2 me = transform.position;
            if (!m_checked)
            {
                m_checked = true;
                m_iced = YsvFloor.Covers(me);
                if (m_iced) YsvUtil.Play(gameObject, YsveldFx.SnareIcedClip);
            }
            // frozen in: it lasts as long as the ice under it (checked every frame: cheap, a handful of slabs)
            if (m_iced && (m_age > IcedMax || !YsvFloor.Covers(me))) { SystemPool.Despawn(gameObject); return; }
            if (m_age < ArmDelay) return;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            var d = (Vector2)hero.transform.position - me;
            if ((d.x * d.x) / (RX * RX) + (d.y * d.y) / (RY * RY) > 1f) return;
            var hh = hero.GetComponent<Health>();
            if (hh == null || !hh.IsAlive()) return;
            m_done = true;
            var src = FxFactory.SourceOf(gameObject);
            var pl = hero.GetComponent<Player>();
            var root = FxFactory.GetStatus("StatusStuckToFloor");
            if (pl != null && root != null) pl.AddStatus(root, src, "modysvsnare");
            YsvUtil.Rime(hero, src, m_iced ? 2 : 1, m_iced);
            if (YsveldFx.SnareSnap != null) SystemPool.Spawn(YsveldFx.SnareSnap, hero.transform.position);
            SystemPool.Despawn(gameObject);
        }
    }
}
