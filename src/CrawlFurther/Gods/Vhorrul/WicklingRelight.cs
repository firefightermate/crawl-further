using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Wickling, Relight: Gutter Dash puts its tail flame out (a smoke curl; its bites stop burning). Touching any fire
    /// relights it white-hot with a flare, and the next bite hits <see cref="HotBonus"/> harder and always burns.
    /// A bot whose tail is out runs back to the nearest fire when the hero isn't in reach.
    /// </summary>
    public class WicklingRelight : VhorrulBehaviour
    {
        public const float HotBonus = 0.3f, TouchRange = 9f, SeekRange = 70f;
        public static exSpriteAnimClip IdleOut, RunOut, IdleHot, RunHot;
        enum Tail { Lit, Out, Hot }
        Tail m_tail;

        protected override void OnEnable() { base.OnEnable(); m_tail = Tail.Lit; }

        /// <summary>Clip event (Gutter Dash's last frame): the tail has guttered out.</summary>
        public void VhGutter() { Set(Tail.Out); }

        void Set(Tail t)
        {
            m_tail = t;
            SetStance(t == Tail.Out ? IdleOut : t == Tail.Hot ? IdleHot : null, t == Tail.Out ? RunOut : t == Tail.Hot ? RunHot : null);
        }

        void Update()
        {
            if (!Alive || m_tail != Tail.Out) { Steer(null); return; }
            if (FireNear(TouchRange) != null)
            {
                Set(Tail.Hot);
                Steer(null);
                if (VhorrulFx.Flare != null) ModAttach.Spawn(VhorrulFx.Flare, gameObject, new Vector2(Face.x >= 0f ? -8f : 8f, 10f));
                return;
            }
            var fire = IsBot && !InAttack && HeroDist > 34f ? FireNear(SeekRange) : null;
            Steer(fire != null ? (Vector2?)fire.Pos : null);
        }

        public override void OnHitHero(DamageInfo d)
        {
            if (!From(d, VhorrulFx.WickBite)) return;
            if (m_tail == Tail.Out) d.m_status = null;
            else if (m_tail == Tail.Hot)
            {
                d.m_amount += HotBonus;
                d.m_status = VhorrulFx.OnFire;
                Set(Tail.Lit);
            }
        }
    }
}
