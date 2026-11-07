namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>Eats the bone pile at its feet (see <see cref="OssivarTraits"/>), and the clip events every Ossivar monster shares.</summary>
    public class OssivarMonster : MonsterBehaviour
    {
        public const float EatRange = 10f;
        Health m_health;

        protected override void Awake()
        {
            base.Awake();
            m_health = GetComponent<Health>();
        }

        OssivarTraits Traits { get { return Monster != null ? Monster.Traits as OssivarTraits : null; } }

        /// <summary>Would this monster use <paramref name="pile"/> now (heal, plate, crow)?</summary>
        public bool Wants(BonePileFx pile)
        {
            var t = Traits;
            if (t == null || pile == null || pile.Locked || !Monster.Alive || m_health == null) return false;
            if (t.shepherd) return false;
            if (t.healOnBones && m_health.GetHealthCurrent() < m_health.GetHealthMax() * 0.75f) return true;
            if (t.pilesToCrows) { var f = GetComponent<SaintFlock>(); return f != null && f.Crows < SaintFlock.MaxCrows; }
            return Monster.Plates < PlateCap(pile);
        }

        int PlateCap(BonePileFx pile)
        {
            int cap = Traits.maxPlates;
            return pile.Marrow ? System.Math.Max(cap, 2) : cap;
        }

        void Update()
        {
            if (Traits == null || !Monster.Alive) return;
            var pile = BonePileFx.Nearest(transform.position, EatRange, p => !p.Locked);
            if (pile == null || !Wants(pile)) return;
            Eat(pile);
        }

        /// <summary>Use the pile now (whatever this monster turns bones into) and remove it.</summary>
        public void Eat(BonePileFx pile)
        {
            var t = Traits;
            if (t.healOnBones && m_health.GetHealthCurrent() < m_health.GetHealthMax() * 0.75f) Monster.Heal(m_health.GetHealthMax() * 0.5f);
            else if (t.pilesToCrows) { var f = GetComponent<SaintFlock>(); if (f != null) f.AddCrow(); }
            else
            {
                Monster.AddPlate(PlateCap(pile));
                if (pile.Marrow) Monster.AddPlate(PlateCap(pile));
            }
            pile.Consume();
        }

        /// <summary>Clip event (Rattlebones' Collapse): heal 1.</summary>
        public void ModCollapseHeal() { Monster.Heal(1f); }

        /// <summary>Clip event: leave a bone pile at the feet.</summary>
        public void ModDropBones() { if (OssivarFx.BonePile != null) FxFactory.SpawnOwned(OssivarFx.BonePile, transform.position, Monster.OwnSource()); }
    }
}
