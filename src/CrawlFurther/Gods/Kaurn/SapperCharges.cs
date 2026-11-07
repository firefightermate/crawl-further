using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Fuse Sapper's Lay Charges: three charges lobbed down round the hero (see <see cref="KrnChargeFx"/>).</summary>
    public class SapperCharges : KaurnBehaviour
    {
        public const int Count = 3;
        public const float Near = 16f, Far = 28f;

        /// <summary>Clip event: the charges leave its hand.</summary>
        public void KrnLayCharges()
        {
            if (KaurnFx.ChargeLob == null) return;
            Vector2 hp = HeroPos;
            float a0 = Random.Range(0f, 360f);
            for (int i = 0; i < Count; i++)
            {
                float a = (a0 + i * 360f / Count + Random.Range(-20f, 20f)) * Mathf.Deg2Rad;
                float r = Random.Range(Near, Far);
                var to = ModUtil.SafePoint(hp, hp + new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.6f) * r);
                var go = FxFactory.SpawnOwned(KaurnFx.ChargeLob, Me + new Vector2(12f * Side, 16f), Own);
                var lob = go != null ? go.GetComponent<KrnLobFx>() : null;
                if (lob != null) { lob.target = to; lob.time = 0.4f + i * 0.08f; }
            }
        }
    }
}
