using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Pyre Warden, Keeper of Pyres: death pyres within <see cref="KeepRange"/> px of a living Warden never cool to wax
    /// (<see cref="VhPyreFx"/>; a gold sigil flame over each kept pyre). Stoke swings the censer into the fire nearest the
    /// hero within <see cref="StokeRange"/> px of the Warden (or lights a new pyre at its feet), and that fire spreads one
    /// ring outward every <see cref="RingEvery"/> s, three times.
    /// </summary>
    public class WardenKeeper : VhorrulBehaviour
    {
        public const float KeepRange = 60f, StokeRange = 60f, RingEvery = 0.5f;
        static readonly List<WardenKeeper> s_live = new List<WardenKeeper>();

        protected override void OnEnable() { base.OnEnable(); if (!s_live.Contains(this)) s_live.Add(this); }
        protected override void OnDisable() { s_live.Remove(this); base.OnDisable(); }

        /// <summary>True if a living Warden stands within keeping range of <paramref name="p"/>.</summary>
        public static bool Keeps(Vector2 p)
        {
            foreach (var w in s_live)
                if (w != null && w.Alive && ((Vector2)w.transform.position - p).sqrMagnitude <= KeepRange * KeepRange) return true;
            return false;
        }

        static bool IsFloorFire(IgniterFx f)
        {
            var n = f.gameObject.name;
            return n.StartsWith("ModBurningPool") || n.StartsWith("ModVhPyre") || n.StartsWith("ModVhLineFlare") || n.StartsWith("ModVhCoilFlame");
        }

        /// <summary>Clip event (the censer strikes): stoke the fire nearest the hero, or light a pyre here.</summary>
        public void VhStoke()
        {
            if (!Alive) return;
            Vector2 hero = HeroPos, me = Me;
            IgniterFx best = null;
            float bd = float.MaxValue;
            foreach (var f in IgniterFx.All)
            {
                if (f == null || !f.isActiveAndEnabled || !IsFloorFire(f) || (f.Pos - me).sqrMagnitude > StokeRange * StokeRange) continue;
                float d = (f.Pos - hero).sqrMagnitude;
                if (d < bd) { bd = d; best = f; }
            }
            Vector2 at = best != null ? best.Pos : me + Face * 10f;
            if (best == null && VhorrulFx.Pyre != null) FxFactory.SpawnOwned(VhorrulFx.Pyre, at, Own);
            StartCoroutine(Rings(at));
        }

        IEnumerator Rings(Vector2 at)
        {
            var src = Own;
            foreach (var ring in VhorrulFx.StokeRing)
            {
                if (ring != null) FxFactory.SpawnOwned(ring, at, src);
                yield return new WaitForSeconds(RingEvery);
            }
        }
    }
}
