using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Loom Widow, Full Spool: each frost pip her line eats (<see cref="YsvSpoolLine"/>) winds onto her loom, up to three.
    /// With three, her next Silk Whip (basic 1) pins the hero at once and empties the loom. Tell: the spool on her loom
    /// grows (FxYsvSpool S1..S3 over the loom).
    /// </summary>
    public class LoomSpool : YsveldBehaviour
    {
        public const int Full = 3;
        public static GameObject PinLash;
        static readonly Vector2 Spool = new Vector2(14f, 21f);
        int m_wound;
        GameObject m_show;

        protected override void OnEnable() { base.OnEnable(); m_wound = 0; }

        protected override void OnDisable() { base.OnDisable(); Hide(); }

        /// <summary>Where the spool sits, in world space (the line ends there).</summary>
        public Vector2 SpoolPoint { get { return Me + new Vector2(Spool.x * Side, Spool.y); } }

        /// <summary>A pip arrived up the line.</summary>
        public void Wind()
        {
            if (m_wound >= Full) return;
            m_wound++;
            Hide();
            var t = YsveldFx.SpoolShow[m_wound - 1];
            if (t != null) m_show = SystemPool.Spawn(t, SpoolPoint);
            if (m_wound >= Full) NextBasic(1);
        }

        void Hide() { if (m_show != null) { SystemPool.Despawn(m_show); m_show = null; } }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template != PinLash) return;
            m_wound = 0;
            Hide();
            NextBasic(0);
        }

        void LateUpdate()
        {
            if (m_show == null) return;
            if (!Alive || !m_show.activeInHierarchy) { Hide(); return; }
            var p = SpoolPoint;
            m_show.transform.position = new Vector3(p.x, p.y, transform.position.z - 0.05f);
        }
    }

    /// <summary>On the Loom Widow's pinning whip: a hero it hits is pinned at once.</summary>
    public class YsvPinFx : MonoBehaviour
    {
        void MsgOnAttackContact(DamageInfo d)
        {
            var hero = CrawlFurther.Util.ModUtil.Hero();
            if (d == null || hero == null || d.m_victim != hero) return;
            YsvRime.Of(hero).Pin(d.m_source);
        }
    }
}
