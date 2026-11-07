using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// On a projectile or a runner: where it ends (it hits something, hits a wall or runs out), it leaves
    /// <see cref="spawn"/> behind (a seed, a pod burst), owned by whoever fired it. <see cref="skipOnHero"/>: nothing is
    /// left if it hit the hero (the Rotfly's spit only seeds the floor when it misses). <see cref="furrow"/> is handed
    /// to the seed (set per instance by the Sower).
    /// </summary>
    public class PlantOnEnd : MonoBehaviour
    {
        public GameObject spawn;
        public bool skipOnHero;
        public int furrow;

        bool m_live, m_hitHero;
        Vector2 m_from;

        void OnEnable() { m_live = false; m_hitHero = false; furrow = 0; m_from = transform.position; }

        // pools wake and sleep their copies once at load: only an effect that has run a frame is live
        void Update() { m_live = true; }

        void MsgOnAttackContact(DamageInfo d)
        {
            if (d != null && d.m_victim != null && d.m_victim == ModUtil.Hero()) m_hitHero = true;
        }

        void OnDisable()
        {
            if (!m_live || spawn == null || (skipOnHero && m_hitHero) || SystemMain.GetDeloadInProgress()) return;
            m_live = false;
            var hero = ModUtil.Hero();
            Vector2 at = transform.position, from = m_from;
            if (hero == null || ((Vector2)hero.transform.position - at).sqrMagnitude > 300f * 300f) return;
            var src = FxFactory.SourceOf(gameObject);
            var what = spawn;
            int f = furrow;
            Orchard.Later(() =>
            {
                if (!SylveneFx.IsSeed(what))
                {
                    var p = ModUtil.SafePoint(from, at, 3f);
                    FxFactory.SpawnOwned(what, p, src);
                    if (what == SylveneFx.PodBurstBig) Orchard.PodBurst(p);
                    return;
                }
                var s = Orchard.Plant(what, from, at, src);
                if (s != null && f != 0) Furrow.Add(f, s);
            });
        }
    }
}
