using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Cairn Crow. Pick the Bones: a peck on a bleeding hero pulls a splinter out of him; it falls as a bone pile beside him
    /// (tell: a white splinter flying off). Caw: every bone pile within <see cref="CawRange"/> px hops
    /// <see cref="CawHop"/> px toward the nearest Ossivar monster.
    /// </summary>
    public class CrowPicker : OssBehaviour
    {
        public const float CawRange = 60f, CawHop = 20f;
        float m_lastSplinter;

        public override void OnHitHero(DamageInfo d)
        {
            if (!From(d, OssivarFx.CrowPeck) || !HeroBleeding || Time.time - m_lastSplinter < 0.4f) return;
            m_lastSplinter = Time.time;
            Vector2 hero = HeroPos;
            if (OssivarFx.Splinter != null) SystemPool.Spawn(OssivarFx.Splinter, hero);
            Vector2 away = Me - hero;
            away = away.sqrMagnitude > 0.01f ? away.normalized : -Face;
            OssFloor.DropPile(hero, hero + away * 10f + Random.insideUnitCircle * 3f, Own);
        }

        /// <summary>Clip event (Caw frame 3).</summary>
        public void OssCaw()
        {
            if (!Alive) return;
            if (OssivarFx.Caw != null) SystemPool.Spawn(OssivarFx.Caw, Me);
            foreach (var p in BonePileFx.Snapshot())
            {
                if (p == null || p.Locked || (p.Pos - Me).sqrMagnitude > CawRange * CawRange) continue;
                var kin = NearestKin(p.Pos);
                if (kin != null) p.Hop(kin.transform.position, CawHop);
            }
        }

        static OssivarMonster NearestKin(Vector2 at)
        {
            OssivarMonster best = null; float bd = float.MaxValue;
            foreach (var m in Object.FindObjectsOfType<OssivarMonster>())
            {
                if (m == null || !m.isActiveAndEnabled) continue;
                var h = m.GetComponent<Health>();
                if (h == null || !h.IsAlive()) continue;
                float d = ((Vector2)m.transform.position - at).sqrMagnitude;
                if (d < bd) { bd = d; best = m; }
            }
            return best;
        }
    }
}
