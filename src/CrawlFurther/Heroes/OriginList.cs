namespace CrawlFurther.Content.Heroes
{
    using CrawlFurther.Gods;
    using CrawlFurther.Heroes;

    /// <summary>
    /// Crawl: Further's hero origins. Most cost a little (an extra stat point, or a weaker perk), so a custom hero
    /// picking the same weapon pays about the same.
    /// </summary>
    public static class OriginList
    {
        static PlayerModifier Mod(PlayerModifier.eType t, float v)
        {
            return new PlayerModifier { m_modify = t, m_type = ValueModifier.eModifierType.Multiply, m_value = v, m_priority = 0f };
        }

        public static readonly OriginDef[] All =
        {
            new OriginDef { id = "Wanderer", name = "WANDERER", portraitArt = "HeroWanderer", isVanilla = true,
                summary = "The standard hero, no changes",
                flavour = "An ordinary hero\non the long way down." },
            new OriginDef { id = "Sellsword", name = "SELLSWORD", portraitArt = "HeroSellsword", gearArt = "GearSellsword",
                vitality = 1, strength = -1, dexterity = -1, powerups = new[] { "SpellTribalShield" },
                summary = "Shield spell, more VIT, less STR and DEX",
                flavour = "Paid in advance.\nRefunds are not offered." },
            new OriginDef { id = "Huntress", name = "HUNTRESS", portraitArt = "HeroHuntress", gearArt = "GearHuntress",
                weapon = "WeaponBowStarting", vitality = -2, strength = -2,
                summary = "Bow, less VIT and STR",
                flavour = "She stays out of reach\nand shoots from there." },
            new OriginDef { id = "Hexblade", name = "HEXBLADE", portraitArt = "HeroHexblade", gearArt = "GearHexblade",
                weapon = "WeaponMagicStaff", strength = -2, vitality = -3,
                modifiers = new[] { Mod(PlayerModifier.eType.HeroSpecialChargeTime, 0.9f) },
                summary = "Staff, faster spells, less VIT and STR",
                flavour = "Her spells come fast.\nHer body pays for them." },
            new OriginDef { id = "Flagellant", name = "FLAGELLANT", portraitArt = "HeroFlagellant", gearArt = "GearFlagellant",
                weapon = "WeaponClubStarting", vitality = -3, powerups = new[] { "ArtifactBleedWhenHit", "PowerupLowHealth2xDamage" },
                summary = "Club, less VIT, bleeds, hits harder when low",
                flavour = "He bleeds on purpose\nand hits harder for it." },
            new OriginDef { id = "Pilgrim", name = "PILGRIM", portraitArt = "HeroPilgrim", gearArt = "GearPilgrim",
                vitality = 1, strength = -1, dexterity = -1, powerups = new[] { "PowerupPentagramHealing" },
                summary = "More VIT, less STR and DEX, pentagrams heal",
                flavour = "A long road, a short prayer,\nand a hat for the rain." },
            new OriginDef { id = "Gambler", name = "GAMBLER", portraitArt = "HeroGambler", gearArt = "GearGambler",
                weapon = "WeaponSlingStarting", vitality = -2, strength = -1, gold = 15, powerups = new[] { "ArtifactLuckyClaw" },
                summary = "Sling, less VIT and STR, extra gold, cheap shops",
                flavour = "Starts with more gold\nand haggles at every shop." },
            new OriginDef { id = "Reaver", name = "REAVER", portraitArt = "HeroReaver", gearArt = "GearReaver",
                weapon = "WeaponBattleAxe", vitality = -2, dexterity = -3,
                summary = "Battle axe, less VIT and DEX",
                flavour = "A heavy axe and no patience\nfor footwork." },
            new OriginDef { id = "Cutpurse", name = "CUTPURSE", portraitArt = "HeroCutpurse", gearArt = "GearCutpurse",
                weapon = "WeaponStartingThievingKnife", dexterity = 1, vitality = -2, strength = -1,
                summary = "Knife, more DEX, less VIT and STR",
                flavour = "Light fingers, quick feet,\nand a very dull knife." },
            new OriginDef { id = "Arbalist", name = "ARBALIST", portraitArt = "HeroArbalist", gearArt = "GearArbalist",
                weapon = "WeaponCrossbow", vitality = -3, strength = -2,
                summary = "Crossbow, less VIT and STR",
                flavour = "One bolt, one bounty.\nReloading is the hard part." },
            new OriginDef { id = "Scholar", name = "SCHOLAR", portraitArt = "HeroScholar", gearArt = "GearScholar",
                vitality = -2, strength = -1, powerups = new[] { "ArtifactSpellbookFireball" },
                summary = "Book of Flame, less VIT and STR",
                flavour = "Her book floats beside her\nand does the fighting." },
            // the silver and gold custom heroes (always the last two entries)
            new OriginDef { tier = SlotTier.Silver, id = "CustomSilver", name = "SILVER HERO", portraitArt = "HeroCustomSilver",
                summary = "Your own hero: any look, any one weapon",
                flavour = "Made to order,\nfrom hat to boots." },
            new OriginDef { tier = SlotTier.Gold, id = "CustomGold", name = "GOLD HERO", portraitArt = "HeroCustomGold",
                summary = "Your own hero: any look, a weapon and a spell",
                flavour = "Made to order,\nwith a spell up the sleeve." },
        };

        /// <summary>Add every origin to Core's origin list, in order.</summary>
        public static void Register()
        {
            foreach (var o in All) HeroClasses.Register(o);
        }
    }
}
