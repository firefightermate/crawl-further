using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Forgemaster's Collector: he comes in carrying <see cref="StartRods"/> rods, picks up every rod he walks over, up to
    /// <see cref="MaxRods"/>, and carries them in his
    /// quiver (they show there). His sledge hits <see cref="Bonus"/> harder per rod. Rod Volley throws them all to land in a
    /// ring round the hero (0.9 each), where they stand as rods for 9 s; with none he plants one at his feet.
    /// </summary>
    public class ForgemasterCollector : KaurnBehaviour
    {
        public const int MaxRods = 3, StartRods = 2;
        public const float Reach = 11f, Bonus = 0.15f, Swing = 1.3f, Ring = 22f;
        public static readonly exSpriteAnimClip[] RodIdle = new exSpriteAnimClip[MaxRods + 1], RodRun = new exSpriteAnimClip[MaxRods + 1];
        int m_rods;
        float m_scan;

        protected override void OnEnable() { base.OnEnable(); m_rods = StartRods; m_scan = 0f; }

        void Show() { SetStance(RodIdle[m_rods], RodRun[m_rods]); }

        void Update()
        {
            m_scan -= Time.deltaTime;
            if (m_scan > 0f || m_rods >= MaxRods || !Alive) return;
            m_scan = 0.1f;
            var rod = KrnNode.Nearest(Me, Reach, n => n.IsRod && Time.time - n.born > 0.5f);
            if (rod == null) return;
            rod.Remove();
            m_rods++;
            Unit.Pop();
            Show();
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template == KaurnFx.MasterSmash) FxFactory.SetDamage(fx, Swing + Bonus * m_rods);
        }

        /// <summary>Clip event: throw every rod carried round the hero (or plant one at his feet).</summary>
        public void KrnVolley()
        {
            if (m_rods == 0)
            {
                if (KaurnFx.RodVolley != null) FxFactory.SpawnOwned(KaurnFx.RodVolley, Me + Face * 9f, Own);
                return;
            }
            Vector2 hp = HeroPos;
            float a0 = Random.Range(0f, 360f);
            for (int i = 0; i < m_rods; i++)
            {
                float a = (a0 + i * 360f / m_rods) * Mathf.Deg2Rad;
                var to = ModUtil.SafePoint(hp, hp + new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.6f) * Ring);
                var go = KaurnFx.ThrownRod != null ? FxFactory.SpawnOwned(KaurnFx.ThrownRod, Me + new Vector2(-3f * Side, 30f), Own) : null;
                var lob = go != null ? go.GetComponent<KrnLobFx>() : null;
                if (lob == null) continue;
                lob.target = to; lob.land = KaurnFx.RodLand; lob.land2 = KaurnFx.RodVolley; lob.time = 0.5f + i * 0.06f;
            }
            m_rods = 0;
            Show();
        }
    }
}
