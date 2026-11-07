namespace CrawlFurther.Heroes
{
    using CrawlFurther.Gods;

    /// <summary>
    /// A hero origin: what the player starts with whenever they take the hero's body, on top of their god's kit. Add it
    /// with <see cref="HeroClasses.Register"/>. Stats are offsets from the god's starting values.
    /// </summary>
    public class OriginDef
    {
        /// <summary>Unique id; also the key of the origin's colours (<see cref="HeroLooks.SetColours"/>).</summary>
        public string id;
        /// <summary>Name on the origin page.</summary>
        public string name;
        /// <summary>One line of mechanics, shown under the name.</summary>
        public string summary;
        /// <summary>Two short lines of flavour ("\n" between them).</summary>
        public string flavour;
        /// <summary>Portrait sheet (anim "Idle", 29 x 24). Sheets named portraitArt + "_P1".."_P4" are used in each player's colours.</summary>
        public string portraitArt;
        /// <summary>Headwear the in-game hero wears: a sheet of 15 x 15 pose cells (see HeroGear), with "_P1".."_P4"
        /// variants per player colour. Null for none.</summary>
        public string gearArt;
        /// <summary>Weapon prefab: a vanilla Weapon name or "ModWeapon" + a registered weapon id; null keeps the god's.</summary>
        public string weapon;
        public int vitality, strength, dexterity;
        /// <summary>Powerups granted (vanilla prefab names, or "Mod" + a registered item id).</summary>
        public string[] powerups = new string[0];
        /// <summary>Gold at the start of a run.</summary>
        public int gold;
        public PlayerModifier[] modifiers = new PlayerModifier[0];
        /// <summary>The game's own hero (no changes): shown with the vanilla pip.</summary>
        public bool isVanilla;
        /// <summary>Normal, or a silver / gold "make your own" slot (see <see cref="ICustomHeroes"/>).</summary>
        public SlotTier tier = SlotTier.Normal;

        /// <summary>Weapon / spell / both, from <see cref="weapon"/> and the spell powerups. For a silver or gold slot this
        /// is what the slot can grant at most (silver a weapon, gold both); <see cref="HeroClasses.KindFor"/> gives one
        /// player's actual pick.</summary>
        public OriginKind Kind
        {
            get
            {
                if (tier == SlotTier.Silver) return OriginKind.Weapon;
                if (tier == SlotTier.Gold) return OriginKind.WeaponAndSpell;
                bool w = !string.IsNullOrEmpty(weapon), sp = false;
                foreach (var p in powerups) if (HeroClasses.IsSpellPowerup(p)) sp = true;
                return w ? (sp ? OriginKind.WeaponAndSpell : OriginKind.Weapon) : (sp ? OriginKind.Spell : OriginKind.Plain);
            }
        }
    }
}
