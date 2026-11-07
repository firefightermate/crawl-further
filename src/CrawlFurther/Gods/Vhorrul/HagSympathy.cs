using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Wick Hag, Sympathy: Poppet sets a lit wax poppet of the hero down within 20 px of her, on a fire if one is that
    /// close (<see cref="VhPoppetFx"/> links its burns to him). While it stands and he keeps his distance, her hex flames
    /// fly at the poppet instead of at him.
    /// </summary>
    public class HagSympathy : VhorrulBehaviour
    {
        public const float Reach = 20f, FarHero = 40f;

        /// <summary>Clip event (the poppet goes down).</summary>
        public void VhPoppet()
        {
            if (!Alive || VhorrulFx.Poppet == null) return;
            var old = VhPoppetFx.Of(gameObject);
            if (old != null) return;
            var fire = IgniterFx.Nearest(Me, Reach, f => !f.gameObject.name.StartsWith("ModVhHexFlame"));
            Vector2 at = fire != null ? fire.Pos : Me + Face * 10f;
            FxFactory.SpawnOwned(VhorrulFx.Poppet, at, Own);
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template != VhorrulFx.HexFlame || HeroDist < FarHero) return;
            var p = VhPoppetFx.Of(gameObject);
            var pm = fx.GetComponent<ParticleMotion>();
            if (p == null || pm == null) return;
            var d = p.Pos + new Vector2(0f, 3f) - (Vector2)fx.transform.position;
            if (d.sqrMagnitude < 1f) return;
            pm.SetDirection(d.normalized);
            fx.transform.rotation = Quaternion.Euler(0f, 0f, AngleOf(d));
        }
    }
}
