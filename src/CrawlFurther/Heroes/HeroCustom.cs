using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using BepInEx;
using BepInEx.Configuration;
using UnityEngine;

namespace CrawlFurther.Content.Heroes
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Heroes;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Items;
    using CrawlFurther.Content.Weapons;

    /// <summary>
    /// The custom silver / gold hero: data, rules and art for the hero editor (its UI is built on this).
    ///
    /// SILVER = appearance + any one weapon. GOLD = appearance + a weapon and/or a spell. Every weapon and spell carries
    /// a debuff set (stronger picks cost more; tools/sprites/hero_custom.py --doc writes the full table). Each player slot (player
    /// id 0-3) keeps its own silver and gold choice, saved in BepInEx/config/CrawlFurther.HeroCustom.cfg.
    ///
    /// Editor flow: c = HeroCustom.Get(pid, tier).Clone(); change c.look[part] / c.weapon / c.spell; show
    /// PortraitClip(c, pid, tier) and Summary(c, tier) live; on confirm HeroCustom.Set(pid, tier, c).
    ///
    /// Art (tools/sprites/hero_custom.py): the portrait is composed at run time from drawn layers (HcPortrait) whose
    /// marker colours are swapped for the choice; in game the body is recoloured through the player's hero ramp
    /// (HeroLooks calls BodySwaps) and the head / face pieces are recoloured gear sheets (HeroGear calls GearSheets).
    /// The player-slot colour always stays on the belt, boots and far side in game and on the portrait collar and
    /// background, so two players with the same look are still told apart.
    /// </summary>
    public static partial class HeroCustom
    {
        // ============================================================================================ appearance
        public const string PartOutfit = "Outfit", PartColour = "Colour", PartTrim = "Trim", PartSkin = "Skin",
                            PartHair = "Hair", PartHead = "Head", PartFace = "Face";

        /// <summary>One choice of an appearance part.</summary>
        public class Option
        {
            public string id;        // stable id (saved in config)
            public string name;      // display name, upper case
            public string text;      // one short line for the editor
            internal string icon;    // HcIcons anim ("Colour_Player" is per slot: "_P1".."_P4" added)
            internal bool perSlot;

            /// <summary>20x20 picture of this choice (the Player colour shows the player's own slot colour).</summary>
            public exSpriteAnimClip Icon(int playerId)
            {
                string a = perSlot ? icon + "_P" + (HeroLooks.SlotOfId(playerId) + 1) : icon;
                return IconClip(a);
            }
        }

        /// <summary>One appearance part (a row in the editor): the options cycle with left / right.</summary>
        public class Part
        {
            public string id, name;
            public readonly List<Option> options = new List<Option>();
            public int Count { get { return options.Count; } }
            public int IndexOf(string optionId)
            {
                for (int i = 0; i < options.Count; i++) if (options[i].id == optionId) return i;
                return -1;
            }
        }

        static List<Part> s_parts;
        /// <summary>Appearance parts in editor order: OUTFIT, MAIN COLOUR, TRIM COLOUR, SKIN, HAIR, HEAD, FACE.</summary>
        public static List<Part> Parts { get { if (s_parts == null) s_parts = BuildParts(); return s_parts; } }

        public static int PartIndex(string partId)
        {
            var ps = Parts;
            for (int i = 0; i < ps.Count; i++) if (ps[i].id == partId) return i;
            return -1;
        }

        static List<Part> BuildParts()
        {
            var l = new List<Part>();
            var p = new Part { id = PartOutfit, name = "OUTFIT" };
            for (int i = 0; i < s_outfitIds.Length; i++)
                p.options.Add(new Option { id = s_outfitIds[i], name = s_outfitNames[i], text = s_outfitText[i], icon = "Outfit_" + s_outfitIds[i] });
            l.Add(p);
            foreach (var pid in new[] { PartColour, PartTrim })
            {
                p = new Part { id = pid, name = pid == PartColour ? "MAIN COLOUR" : "TRIM COLOUR" };
                for (int i = 0; i < s_colourIds.Length; i++)
                    p.options.Add(new Option
                    {
                        id = s_colourIds[i], name = s_colourNames[i], icon = "Colour_" + s_colourIds[i], perSlot = s_colourIds[i] == "Player",
                        text = s_colourIds[i] == "Player" ? "Your player colour" : (pid == PartColour ? "Main clothes" : "Vest, trim and hat dye"),
                    });
                l.Add(p);
            }
            p = new Part { id = PartSkin, name = "SKIN" };
            for (int i = 0; i < s_skinIds.Length; i++) p.options.Add(new Option { id = s_skinIds[i], name = s_skinNames[i], text = "Skin tone", icon = "Skin_" + s_skinIds[i] });
            l.Add(p);
            p = new Part { id = PartHair, name = "HAIR" };
            for (int i = 0; i < s_hairIds.Length; i++) p.options.Add(new Option { id = s_hairIds[i], name = s_hairNames[i], text = "Hair and beard colour", icon = "Hair_" + s_hairIds[i] });
            l.Add(p);
            p = new Part { id = PartHead, name = "HEAD" };
            for (int i = 0; i < s_headIds.Length; i++) p.options.Add(new Option { id = s_headIds[i], name = s_headNames[i], text = "Hair or headwear", icon = "Head_" + s_headIds[i] });
            l.Add(p);
            p = new Part { id = PartFace, name = "FACE" };
            for (int i = 0; i < s_faceIds.Length; i++) p.options.Add(new Option { id = s_faceIds[i], name = s_faceNames[i], text = "Face", icon = "Face_" + s_faceIds[i] });
            l.Add(p);
            return l;
        }

        // ============================================================================================ debuffs
        /// <summary>Stat penalties a weapon or spell costs (negative numbers), applied on top of the god's stats.</summary>
        public class Debuff
        {
            public int vit, str, dex;
            public const int Floor = -4;     // one stat never drops by more than this; the excess moves to another stat

            public Debuff() { }
            public Debuff(int v, int s, int d) { vit = v; str = s; dex = d; }
            public int Points { get { return -(vit + str + dex); } }
            public bool IsEmpty { get { return vit == 0 && str == 0 && dex == 0; } }

            public static Debuff Sum(Debuff a, Debuff b)
            {
                var r = new Debuff((a != null ? a.vit : 0) + (b != null ? b.vit : 0), (a != null ? a.str : 0) + (b != null ? b.str : 0),
                                   (a != null ? a.dex : 0) + (b != null ? b.dex : 0));
                // keep every stat at Floor or above without lowering the total cost: move the excess to the lightest stat
                for (int guard = 0; guard < 12; guard++)
                {
                    int[] v = { r.vit, r.str, r.dex };
                    int lo = 0;
                    for (int i = 1; i < 3; i++) if (v[i] < v[lo]) lo = i;
                    if (v[lo] >= Floor) break;
                    int hi = 0;
                    for (int i = 1; i < 3; i++) if (v[i] > v[hi]) hi = i;
                    if (v[hi] <= Floor) break;
                    v[lo]++; v[hi]--;
                    r.vit = v[0]; r.str = v[1]; r.dex = v[2];
                }
                return r;
            }

            /// <summary>"-2 VIT, -1 STR" ("no cost" when empty).</summary>
            public string Text
            {
                get
                {
                    if (IsEmpty) return "no cost";
                    var sb = new StringBuilder();
                    Add(sb, vit, "VIT"); Add(sb, str, "STR"); Add(sb, dex, "DEX");
                    return sb.ToString();
                }
            }

            static void Add(StringBuilder sb, int v, string n)
            {
                if (v == 0) return;
                if (sb.Length > 0) sb.Append(", ");
                sb.Append(v > 0 ? "+" : "").Append(v).Append(' ').Append(n);
            }
        }

        // ============================================================================================ weapons and spells
        /// <summary>A weapon or spell the custom hero can start with.</summary>
        public class Pick
        {
            public string id;        // prefab name ("WeaponBow", "ModWeaponReaper", "SpellHyperdash", "ModSpellWaxSlick"); "" = none
            public string name;      // display name, upper case
            public string text;      // one line: what it does (plain words, no special characters)
            public string family;    // weapons: portrait weapon family ("Sword" ... "Knives"); null for spells / none
            public bool magic;       // magic vanilla variant or mod weapon (sparkles on the portrait)
            public bool mod;         // mod content (shows the MOD gem in lists)
            public Debuff debuff = new Debuff();
            public string DebuffText { get { return debuff.Text; } }
            internal bool spell;

            /// <summary>Is the prefab loaded (mod content builds at load; a failed build hides the pick)?</summary>
            public bool Available { get { return id == "" || (spell ? (UnityEngine.Object)FindSpell(id) : FindWeapon(id)) != null; } }

            /// <summary>The game's own shop bubble of this weapon / spell (null for "none").</summary>
            public exSpriteAnimClip Icon
            {
                get
                {
                    if (string.IsNullOrEmpty(id)) return null;
                    try
                    {
                        if (spell) { var p = FindSpell(id); return p != null ? R.Get<exSpriteAnimClip>(p, "m_animPurchasableBubble") : null; }
                        var w = FindWeapon(id);
                        return w != null ? R.Get<exSpriteAnimClip>(w, "m_animationPurchasableBubble") : null;
                    }
                    catch { return null; }
                }
            }
        }

        static List<Pick> s_weapons, s_spells;
        static int s_weaponsBuiltAt = -1, s_spellsBuiltAt = -1;

        /// <summary>Every weapon: [0] = keep the god's weapon (free), then vanilla, then mod (WeaponPack) weapons.</summary>
        public static List<Pick> Weapons
        {
            get
            {
                int n = WeaponPack.Built.Count;
                if (s_weapons == null || s_weaponsBuiltAt != n) { s_weapons = BuildWeapons(); s_weaponsBuiltAt = n; }
                return s_weapons;
            }
        }

        /// <summary>Every spell: [0] = no spell (free), then vanilla spells and spellbooks, then mod spells.</summary>
        public static List<Pick> Spells
        {
            get
            {
                int n = ItemPack.Built.Count;
                if (s_spells == null || s_spellsBuiltAt != n) { s_spells = BuildSpells(); s_spellsBuiltAt = n; }
                return s_spells;
            }
        }

        public static int WeaponIndex(string id)
        {
            var l = Weapons;
            for (int i = 0; i < l.Count; i++) if (l[i].id == (id ?? "")) return i;
            return 0;
        }

        public static int SpellIndex(string id)
        {
            var l = Spells;
            for (int i = 0; i < l.Count; i++) if (l[i].id == (id ?? "")) return i;
            return 0;
        }

        // vanilla weapons: prefab, name, family, magic, vit, str, dex, text
        static readonly object[][] s_vanillaWeapons =
        {
            new object[] { "WeaponStartingThievingKnife", "PRACTICE KNIFE", "Dagger", false, -1, 0, 0, "A dull training knife" },
            new object[] { "WeaponSlingStarting", "SLING", "Sling", false, -1, -1, 0, "A makeshift ranged weapon" },
            new object[] { "WeaponSling", "SHEPHERD SLING", "Sling", false, -2, -1, 0, "A better sling, a little further" },
            new object[] { "WeaponClubStarting", "OLD CLUB", "Club", false, -2, 0, -1, "Slow, heavy knocks" },
            new object[] { "WeaponBowStarting", "CRACKED BOW", "Bow", false, -2, -2, 0, "A low powered bow" },
            new object[] { "Weapon1HandedSword", "SWORD", "Sword", false, -1, -1, -1, "A sound blade, quick combos" },
            new object[] { "WeaponDagger", "DAGGER", "Dagger", false, -2, -1, 0, "Fast stabs, short reach" },
            new object[] { "WeaponSpear", "SPEAR", "Spear", false, -2, 0, -1, "Long reach thrusts" },
            new object[] { "WeaponClub", "CLUB", "Club", false, -2, 0, -1, "Heavy hits that stagger" },
            new object[] { "WeaponThrowingKnives", "THROWING KNIVES", "Knives", false, -2, -1, -1, "Quick thrown blades" },
            new object[] { "Weapon2HandedSword", "GREATSWORD", "Greatsword", false, -2, 0, -2, "Wide, slow, strong swings" },
            new object[] { "WeaponBattleAxe", "BATTLE AXE", "Axe", false, -2, 0, -3, "The hardest hits, the slowest swings" },
            new object[] { "WeaponBow", "BOW", "Bow", false, -2, -2, -1, "Arrows at a safe distance" },
            new object[] { "WeaponCrossbow", "CROSSBOW", "Crossbow", false, -3, -2, 0, "Heavy bolts, slow to reload" },
            new object[] { "WeaponMagicStaff", "MAGIC STAFF", "Staff", true, -3, -2, 0, "Casts magic bolts" },
            new object[] { "WeaponSlingProjectile", "MAGIC SLING", "Sling", true, -2, -2, 0, "Stones that carry a spell" },
            new object[] { "WeaponBowMagic", "MAGIC BOW", "Bow", true, -3, -2, -1, "Arrows of eternal fire" },
            new object[] { "Weapon1HandedSwordBeam", "SUN RAY SWORD", "Sword", true, -1, -2, -1, "A sword that casts the sun ray" },
            new object[] { "Weapon1HandedSwordProjectile", "HEXED SWORD", "Sword", true, -1, -2, -1, "A sword that throws a spell" },
            new object[] { "Weapon1HandedSwordSummon", "BLOODSTRIKE SWORD", "Sword", true, -1, -2, -1, "A sword that calls bloodstrike" },
            new object[] { "Weapon2HandedSwordBeam", "SUN RAY GREATSWORD", "Greatsword", true, -2, -1, -2, "A greatsword that casts the sun ray" },
            new object[] { "Weapon2HandedSwordProjectile", "HEXED GREATSWORD", "Greatsword", true, -2, -1, -2, "A greatsword that throws cyclones" },
            new object[] { "Weapon2HandedSwordSummon", "BLOODSTRIKE GREATSWORD", "Greatsword", true, -2, -1, -2, "A greatsword that calls bloodstrike" },
            new object[] { "WeaponClubBeam", "SUN RAY CLUB", "Club", true, -2, -1, -1, "A club that casts fire or the sun ray" },
            new object[] { "WeaponClubProjectile", "HEXED CLUB", "Club", true, -2, -1, -1, "A club that throws a spell" },
            new object[] { "WeaponClubSummon", "SPEARTRAP CLUB", "Club", true, -2, -1, -1, "A club that springs the speartrap" },
            new object[] { "WeaponDaggerBeam", "SUN RAY DAGGER", "Dagger", true, -2, -2, 0, "A dagger that casts the sun ray" },
            new object[] { "WeaponDaggerProjectile", "HEXED DAGGER", "Dagger", true, -2, -2, 0, "A dagger that throws a spell" },
            new object[] { "WeaponDaggerSummon", "BLOODSTRIKE DAGGER", "Dagger", true, -2, -2, 0, "A dagger that calls bloodstrike" },
            new object[] { "WeaponSpearBeam", "SUN RAY SPEAR", "Spear", true, -2, -1, -1, "A spear that casts the sun ray" },
            new object[] { "WeaponSpearProjectile", "HEXED SPEAR", "Spear", true, -2, -1, -1, "A spear that throws a spell" },
            new object[] { "WeaponSpearSummon", "SPEARTRAP SPEAR", "Spear", true, -2, -1, -1, "A spear that springs the speartrap" },
            new object[] { "WeaponThrowingKnivesBeam", "SUN RAY KNIVES", "Knives", true, -2, -2, -1, "Knives that cast the sun ray" },
            new object[] { "WeaponThrowingKnivesProjectile", "HEXED KNIVES", "Knives", true, -2, -2, -1, "Knives that throw a spell" },
            new object[] { "WeaponThrowingKnivesSummon", "BLOODSTRIKE KNIVES", "Knives", true, -2, -2, -1, "Knives that call bloodstrike" },
        };

        // mod weapons (WeaponPack ids): vit, str, dex. Any weapon added later falls back to CostDebuff.
        static readonly Dictionary<string, int[]> s_modWeapons = new Dictionary<string, int[]>
        {
            { "Gravehook", new[] { -2, 0, -2 } }, { "Moonglaive", new[] { -2, -1, -1 } }, { "Riftblade", new[] { -2, -1, 0 } },
            { "SnakeEyes", new[] { -2, 0, -1 } }, { "Tidebreaker", new[] { -3, 0, -2 } }, { "Leechfang", new[] { -3, -1, 0 } },
            { "Briarbow", new[] { -2, -2, -1 } }, { "DirgeMaul", new[] { -2, -1, -3 } }, { "Wickstaff", new[] { -3, -2, 0 } },
            { "Arcbolt", new[] { -3, -2, -1 } }, { "Frostbrand", new[] { -2, -1, -1 } }, { "Mercyblade", new[] { -2, -1, 0 } },
            { "Reaper", new[] { -3, 0, -2 } }, { "Starfall", new[] { -2, -1, -3 } }, { "HydraBow", new[] { -2, -2, -1 } },
            { "Bulwark", new[] { -2, 0, -1 } }, { "Heartseeker", new[] { -3, -2, 0 } }, { "Kris", new[] { -2, -1, 0 } },
            { "Blightstaff", new[] { -3, -2, 0 } }, { "Orrery", new[] { -3, -2, 0 } }, { "Grudgestone", new[] { -2, -1, 0 } },
            { "Midas", new[] { -2, -1, 0 } }, { "Lance", new[] { -2, 0, -2 } }, { "Lash", new[] { -2, -1, -1 } },
            { "Kunai", new[] { -2, -1, -1 } },
        };

        // vanilla spells: prefab, name, vit, str, dex, text
        static readonly object[][] s_vanillaSpells =
        {
            new object[] { "SpellTribalShield", "TRIBAL SHIELD", -1, 0, 0, "Summon a shield in front of you" },
            new object[] { "SpellBerserker", "BERSERKER", 0, 0, -1, "A frenzy: more damage, faster, but fragile" },
            new object[] { "SpellFetidDischarge", "FETID DISCHARGE", -1, 0, 0, "Emit a dangerous putrid sludge" },
            new object[] { "SpellCycloneSummon", "CYCLONE SUMMON", -1, -1, 0, "Throw cyclones at your foes" },
            new object[] { "SpellDodgeRollAdvanced", "ADVANCED ROLL", -1, -1, 0, "Roll further and more often" },
            new object[] { "SpellBullCharge", "RAGING BULL", -1, -1, 0, "Charge your foes as a spirit bull" },
            new object[] { "SpellFloatingBeam", "FLOATING BEAM", -1, -1, 0, "A floating rune casts an energy beam" },
            new object[] { "SpellSpiritBow", "SPIRIT BOW", -1, -1, 0, "Conjure a bow of pure energy" },
            new object[] { "SpellHyperdash", "HYPERDASH", -2, -1, 0, "Dash forwards at super speed" },
            new object[] { "ArtifactSpellbookFireball", "BOOK OF FLAME", -2, -1, 0, "A tome follows you and casts fireballs" },
            new object[] { "ArtifactSpellbookTears", "BOOK OF TEARS", -2, -1, 0, "A tome follows you and weeps on foes" },
            new object[] { "ArtifactSpellbookBeam", "BOOK OF THE SUN", -2, -2, 0, "A holy tome follows you and casts beams" },
        };

        // mod spells (ItemPack ids): vit, str, dex. Any spell added later falls back to CostDebuff.
        static readonly Dictionary<string, int[]> s_modSpells = new Dictionary<string, int[]>
        {
            { "SpellEmberVolley", new[] { -1, -1, 0 } }, { "SpellWaxSlick", new[] { -1, 0, 0 } }, { "SpellMarrowSpikes", new[] { -1, -1, 0 } },
            { "SpellBoneBoomerang", new[] { -1, -1, 0 } }, { "SpellSporeBomb", new[] { -1, 0, 0 } }, { "SpellRootSnare", new[] { -1, -1, 0 } },
            { "SpellShardNova", new[] { -2, -1, 0 } }, { "SpellShadowSwap", new[] { -1, 0, -1 } }, { "SpellSoulLantern", new[] { -1, -1, 0 } },
            { "SpellBellToll", new[] { -2, -1, 0 } }, { "SpellUndertow", new[] { -1, -1, 0 } }, { "SpellRiptide", new[] { -1, 0, -1 } },
            { "SpellWildCard", new[] { -1, 0, 0 } }, { "SpellLoadedDice", new[] { -1, 0, 0 } }, { "SpellPuppetStrings", new[] { -1, 0, 0 } },
            { "SpellWickwalk", new[] { -1, 0, 0 } }, { "SpellGraveCall", new[] { -1, -1, 0 } }, { "SpellThornwall", new[] { -1, 0, 0 } },
            { "SpellMirrorStep", new[] { -1, -1, -1 } }, { "SpellYsvRequiem", new[] { -1, -1, 0 } }, { "SpellZhkAcidSpit", new[] { -1, -1, 0 } },
            { "SpellKrnChainSpark", new[] { -1, -1, 0 } },
        };

        /// <summary>Fallback for content added after this table: about one point per 20 gold of shop price.</summary>
        public static Debuff CostDebuff(float cost, bool spell)
        {
            int pts = Mathf.Clamp(Mathf.RoundToInt(cost / 20f), 1, spell ? 3 : 5);
            var d = new Debuff();
            int[] order = spell ? new[] { 0, 1, 0 } : new[] { 0, 1, 2, 0, 1 };
            for (int i = 0; i < pts; i++)
            {
                int s = order[i % order.Length];
                if (s == 0) d.vit--; else if (s == 1) d.str--; else d.dex--;
            }
            return d;
        }

        static string Plain(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            s = s.Replace("%", " percent").Replace("{", "").Replace("}", "").Replace("|", "").Replace("~", "").Replace("[", "").Replace("]", "")
                 .Replace("\n", " ");
            return s.Trim();
        }

        static List<Pick> BuildWeapons()
        {
            var l = new List<Pick> { new Pick { id = "", name = "GOD'S WEAPON", text = "Keep the weapon your god gives" } };
            foreach (var r in s_vanillaWeapons)
                l.Add(new Pick { id = (string)r[0], name = (string)r[1], family = (string)r[2], magic = (bool)r[3],
                                 debuff = new Debuff((int)r[4], (int)r[5], (int)r[6]), text = (string)r[7] });
            foreach (var def in WeaponPack.Defs)
            {
                int[] d;
                var p = new Pick { id = "ModWeapon" + def.id, name = (def.name ?? def.id).ToUpperInvariant(), family = FamilyOf(def.baseWeapon),
                                   magic = true, mod = true, text = Plain(def.description) };
                p.debuff = s_modWeapons.TryGetValue(def.id, out d) ? new Debuff(d[0], d[1], d[2]) : CostDebuff(def.cost, false);
                l.Add(p);
            }
            return l;
        }

        static List<Pick> BuildSpells()
        {
            var l = new List<Pick> { new Pick { id = "", name = "NO SPELL", text = "Keep your god's spell", spell = true } };
            foreach (var r in s_vanillaSpells)
                l.Add(new Pick { id = (string)r[0], name = (string)r[1], debuff = new Debuff((int)r[2], (int)r[3], (int)r[4]), text = (string)r[5], spell = true });
            var keys = new List<string>(ItemPack.Built.Keys);
            keys.Sort(StringComparer.Ordinal);
            // the table order first (by god), then anything else that is a spell
            var ordered = new List<string>();
            foreach (var k in s_modSpells.Keys) if (ItemPack.Built.ContainsKey(k)) ordered.Add(k);
            foreach (var k in keys) if (k.StartsWith("Spell", StringComparison.Ordinal) && !ordered.Contains(k)) ordered.Add(k);
            foreach (var k in ordered)
            {
                var pu = ItemPack.Built[k];
                if (pu == null) continue;
                int[] d;
                string nm = (pu.m_displayName ?? k).Replace(" (MOD)", "").ToUpperInvariant();
                l.Add(new Pick { id = "Mod" + k, name = nm, mod = true, spell = true, text = Plain(pu.m_description),
                                 debuff = s_modSpells.TryGetValue(k, out d) ? new Debuff(d[0], d[1], d[2]) : CostDebuff(pu.m_cost, true) });
            }
            return l;
        }

        /// <summary>Portrait weapon family of a vanilla weapon prefab name.</summary>
        public static string FamilyOf(string prefab)
        {
            if (string.IsNullOrEmpty(prefab)) return null;
            if (prefab.StartsWith("Weapon2Handed", StringComparison.Ordinal)) return "Greatsword";
            if (prefab.StartsWith("Weapon1Handed", StringComparison.Ordinal) || prefab == "WeaponStarting") return "Sword";
            if (prefab.StartsWith("WeaponBattleAxe", StringComparison.Ordinal)) return "Axe";
            if (prefab.StartsWith("WeaponCrossbow", StringComparison.Ordinal)) return "Crossbow";
            if (prefab.StartsWith("WeaponBow", StringComparison.Ordinal)) return "Bow";
            if (prefab.StartsWith("WeaponClub", StringComparison.Ordinal)) return "Club";
            if (prefab.StartsWith("WeaponDagger", StringComparison.Ordinal) || prefab == "WeaponStartingThievingKnife") return "Dagger";
            if (prefab.StartsWith("WeaponSpear", StringComparison.Ordinal)) return "Spear";
            if (prefab.StartsWith("WeaponMagicStaff", StringComparison.Ordinal)) return "Staff";
            if (prefab.StartsWith("WeaponSling", StringComparison.Ordinal)) return "Sling";
            if (prefab.StartsWith("WeaponThrowingKnives", StringComparison.Ordinal)) return "Knives";
            return "Sword";
        }

        /// <summary>Weapon prefab by name: mod weapons from WeaponPack.Built, vanilla through HeroClasses.FindPrefab.</summary>
        public static Weapon FindWeapon(string id) { return HeroClasses.FindWeapon(id); }

        /// <summary>Spell powerup by name: mod spells from ItemPack.Built ("Mod" + id), vanilla through HeroClasses.FindPrefab.</summary>
        public static Powerup FindSpell(string id) { return HeroClasses.FindSpell(id); }

        // ============================================================================================ the choice
        /// <summary>One custom hero: an option index per appearance part (Parts order), a weapon and a spell (prefab names).</summary>
        public class Choice
        {
            public int[] look;
            public string weapon = "", spell = "";

            public Choice Clone()
            {
                return new Choice { look = (int[])look.Clone(), weapon = weapon ?? "", spell = spell ?? "" };
            }

            public Option Get(string partId)
            {
                int p = PartIndex(partId);
                if (p < 0) return null;
                var part = Parts[p];
                int i = p < look.Length ? look[p] : 0;
                return part.options[Mathf.Clamp(i, 0, part.Count - 1)];
            }

            public string Id(string partId) { var o = Get(partId); return o != null ? o.id : ""; }

            /// <summary>Step a part's choice by delta (wraps), for the editor's left / right.</summary>
            public void Step(string partId, int delta)
            {
                int p = PartIndex(partId);
                if (p < 0) return;
                int n = Parts[p].Count;
                look[p] = ((look[p] + delta) % n + n) % n;
            }

            /// <summary>Step the weapon (or spell) through the available picks (wraps).</summary>
            public void StepWeapon(int delta) { weapon = StepPick(Weapons, weapon, delta); }
            public void StepSpell(int delta) { spell = StepPick(Spells, spell, delta); }

            static string StepPick(List<Pick> l, string cur, int delta)
            {
                int i = 0;
                for (int k = 0; k < l.Count; k++) if (l[k].id == (cur ?? "")) i = k;
                for (int t = 0; t < l.Count; t++)
                {
                    i = ((i + delta) % l.Count + l.Count) % l.Count;
                    if (l[i].Available) return l[i].id;
                }
                return "";
            }

            /// <summary>Stable text form (saved in config): "Outfit=Tunic;Colour=Player;...;Weapon=WeaponBow;Spell=".</summary>
            public string Key
            {
                get
                {
                    var sb = new StringBuilder();
                    var ps = Parts;
                    for (int i = 0; i < ps.Count; i++) sb.Append(ps[i].id).Append('=').Append(Get(ps[i].id).id).Append(';');
                    sb.Append("Weapon=").Append(weapon ?? "").Append(";Spell=").Append(spell ?? "");
                    return sb.ToString();
                }
            }

            public static Choice Parse(string s)
            {
                var c = Default();
                if (string.IsNullOrEmpty(s)) return c;
                foreach (var kv in s.Split(';'))
                {
                    int eq = kv.IndexOf('=');
                    if (eq <= 0) continue;
                    string k = kv.Substring(0, eq), v = kv.Substring(eq + 1);
                    if (k == "Weapon") { c.weapon = v; continue; }
                    if (k == "Spell") { c.spell = v; continue; }
                    int p = PartIndex(k);
                    if (p < 0) continue;
                    int o = Parts[p].IndexOf(v);
                    if (o >= 0) c.look[p] = o;
                }
                return c;
            }
        }

        /// <summary>The vanilla hero look in the player's colour: tunic, umber vest, tan skin, brown short hair.</summary>
        public static Choice Default()
        {
            var c = new Choice { look = new int[Parts.Count] };
            c.look[PartIndex(PartTrim)] = Math.Max(0, Parts[PartIndex(PartTrim)].IndexOf("Umber"));
            return c;
        }

        public static bool AllowsWeapon(SlotTier tier) { return tier != SlotTier.Normal; }
        public static bool AllowsSpell(SlotTier tier) { return tier == SlotTier.Gold; }

        /// <summary>The weapon / spell picks that apply in this tier (silver ignores a stored spell).</summary>
        public static Pick WeaponOf(Choice c) { var l = Weapons; return l[WeaponIndex(c != null ? c.weapon : "")]; }
        public static Pick SpellOf(Choice c, SlotTier tier)
        {
            if (!AllowsSpell(tier) || c == null) return Spells[0];
            return Spells[SpellIndex(c.spell)];
        }

        /// <summary>Total stat cost of the choice in this tier (weapon + spell, each stat at Debuff.Floor or above).</summary>
        public static Debuff TotalDebuff(Choice c, SlotTier tier)
        {
            var w = WeaponOf(c); var s = SpellOf(c, tier);
            return Debuff.Sum(w.Available ? w.debuff : null, s.Available ? s.debuff : null);
        }

        public static OriginKind KindOf(Choice c, SlotTier tier)
        {
            bool w = c != null && WeaponOf(c).id != "";
            bool s = c != null && SpellOf(c, tier).id != "";
            return w ? (s ? OriginKind.WeaponAndSpell : OriginKind.Weapon) : (s ? OriginKind.Spell : OriginKind.Plain);
        }

        /// <summary>One line for the panel text: "Crossbow, Hyperdash, -4 VIT, -3 STR" (the look is in the portrait).</summary>
        public static string Summary(Choice c, SlotTier tier)
        {
            if (c == null) return "";
            var parts = new List<string>();
            var w = WeaponOf(c); var s = SpellOf(c, tier);
            parts.Add(w.id == "" ? "God's weapon" : Title(w.name));
            if (AllowsSpell(tier) && s.id != "") parts.Add(Title(s.name));
            var d = TotalDebuff(c, tier);
            if (!d.IsEmpty) parts.Add(d.Text);
            return string.Join(", ", parts.ToArray());
        }

        public static string Summary(int playerId, SlotTier tier) { return Summary(Get(playerId, tier), tier); }

        static string Title(string upper)
        {
            if (string.IsNullOrEmpty(upper)) return "";
            var sb = new StringBuilder(upper.Length);
            bool start = true;
            foreach (char ch in upper)
            {
                sb.Append(start ? char.ToUpperInvariant(ch) : char.ToLowerInvariant(ch));
                start = ch == ' ' || ch == '-';
            }
            return sb.ToString();
        }

        // ============================================================================================ storage
        static readonly Dictionary<int, Choice>[] s_store = { new Dictionary<int, Choice>(), new Dictionary<int, Choice>() };
        static ConfigFile s_cfg;
        static readonly Dictionary<string, ConfigEntry<string>> s_entries = new Dictionary<string, ConfigEntry<string>>();

        static ConfigEntry<string> Entry(int playerId, SlotTier tier)
        {
            string k = "P" + (playerId + 1) + "." + tier;
            ConfigEntry<string> e;
            if (s_entries.TryGetValue(k, out e)) return e;
            try
            {
                if (s_cfg == null) s_cfg = new ConfigFile(Path.Combine(Paths.ConfigPath, "CrawlFurther.HeroCustom.cfg"), true);
                e = s_cfg.Bind("Player" + (playerId + 1), tier.ToString(), "",
                    "Player " + (playerId + 1) + "'s last " + tier.ToString().ToLowerInvariant() + " custom hero (set in the game's hero editor).");
            }
            catch (Exception ex) { Plugin.Log.LogWarning("HeroCustom: config unavailable: " + ex.Message); e = null; }
            s_entries[k] = e;
            return e;
        }

        /// <summary>The stored choice of a player slot (loaded from config the first time; never null). Do not edit it in
        /// place from the editor: Clone(), edit, then Set().</summary>
        public static Choice Get(int playerId, SlotTier tier)
        {
            if (tier == SlotTier.Normal) tier = SlotTier.Silver;
            var d = s_store[tier == SlotTier.Gold ? 1 : 0];
            Choice c;
            if (d.TryGetValue(playerId, out c)) return c;
            var e = playerId >= 0 && playerId < 4 ? Entry(playerId, tier) : null;
            c = Choice.Parse(e != null ? e.Value : "");
            d[playerId] = c;
            return c;
        }

        /// <summary>Store a player's choice, save it, and re-apply it to that player's hero (stats, gear, colours).</summary>
        public static void Set(int playerId, SlotTier tier, Choice c)
        {
            if (c == null || tier == SlotTier.Normal) return;
            c = c.Clone();
            if (!AllowsSpell(tier)) c.spell = "";
            s_store[tier == SlotTier.Gold ? 1 : 0][playerId] = c;
            HeroGear.Version++;                                  // worn gear re-resolves on its next frame
            var e = playerId >= 0 && playerId < 4 ? Entry(playerId, tier) : null;
            if (e != null) { try { e.Value = c.Key; } catch (Exception ex) { Plugin.Log.LogWarning("HeroCustom: save failed: " + ex.Message); } }
            var pd = SystemPlayers.GetPlayer(playerId);
            var def = pd != null ? HeroClasses.For(pd) : null;
            if (def != null && def.tier == tier && pd.GetDeity() != null) pd.SetDeity(pd.GetDeity());
        }

        /// <summary>The origin to apply for a player's custom slot (used by HeroClasses.Apply).</summary>
        public static OriginDef Resolve(int playerId, SlotTier tier)
        {
            var c = Get(playerId, tier);
            var w = WeaponOf(c); var s = SpellOf(c, tier);
            var d = TotalDebuff(c, tier);
            // built field by field (not an object initializer) so tools/validate.py doesn't read it as an origin
            var r = new OriginDef();
            r.id = "Custom" + tier; r.tier = tier; r.name = tier == SlotTier.Gold ? "GOLD HERO" : "SILVER HERO";
            r.weapon = w.id != "" && w.Available ? w.id : null;
            r.powerups = s.id != "" && s.Available ? new[] { s.id } : new string[0];
            r.vitality = d.vit; r.strength = d.str; r.dexterity = d.dex;
            r.summary = Summary(c, tier);
            return r;
        }

        // ============================================================================================ colours
        static Color32 C(int v) { return new Color32((byte)(v >> 16), (byte)(v >> 8), (byte)v, 255); }

        /// <summary>Marker group colours for a choice: [group 1..7][shade]. Groups: main, trim, skin, hair, slot, bg, tier.</summary>
        static Color32[][] MarkerPalette(Choice c, int slot, SlotTier tier)
        {
            var g = new Color32[8][];
            g[1] = ColourShades(c.Id(PartColour), slot);
            g[2] = ColourShades(c.Id(PartTrim), slot);
            g[3] = Block(s_skinShades, Array.IndexOf(s_skinIds, c.Id(PartSkin)), 6);
            g[4] = Block(s_hairShades, Array.IndexOf(s_hairIds, c.Id(PartHair)), 3);
            g[5] = Block(s_slotShades, slot, 4);
            g[6] = Block(s_slotBg, slot, 4);
            g[7] = Block(s_tierShades, tier == SlotTier.Gold ? 1 : 0, 4);
            return g;
        }

        static Color32[] Block(int[] a, int i, int n)
        {
            if (i < 0) i = 0;
            var r = new Color32[n];
            for (int k = 0; k < n; k++) r[k] = C(a[Mathf.Min(a.Length - 1, i * n + k)]);
            return r;
        }

        /// <summary>L M S D of a colour option in a slot ("Player" follows the slot).</summary>
        static Color32[] ColourShades(string id, int slot)
        {
            int ci = Array.IndexOf(s_colourIds, id);
            if (ci < 0) ci = 0;
            // the shade table holds Player first (4 slots x 4), then one block of 4 per colour
            int at = ci == 0 ? slot * 4 : 16 + (ci - 1) * 4;
            var r = new Color32[4];
            for (int k = 0; k < 4; k++) r[k] = C(s_colourShades[at + k]);
            return r;
        }

        static Color32 Recolour(Color32 p, Color32[][] pal)
        {
            if (p.r != 254 || p.g < 1 || p.g > 7) return p;
            var g = pal[p.g];
            if (g == null || p.b < 1 || p.b > g.Length) return p;
            var c = g[p.b - 1];
            c.a = p.a;
            return c;
        }

        // ============================================================================================ in-game body
        static readonly Dictionary<string, ColorSwap[]> s_swapCache = new Dictionary<string, ColorSwap[]>();

        /// <summary>Ramp swaps for a player's custom hero body (outfit roles, slot belt / boots / far side, skin, hair).</summary>
        public static ColorSwap[] BodySwaps(PlayerData pd, SlotTier tier, out string key)
        {
            key = null;
            if (pd == null) return null;
            var c = Get(pd.Id, tier);
            int slot = HeroLooks.SlotOf(pd);
            key = "custom|" + slot + "|" + c.Key;
            ColorSwap[] sw;
            if (s_swapCache.TryGetValue(key, out sw)) return sw;
            var main = ColourShades(c.Id(PartColour), slot);
            var trim = ColourShades(c.Id(PartTrim), slot);
            var slotc = Block(s_slotShades, slot, 4);
            var look = new Dictionary<string, Color32>();
            int oi = Mathf.Max(0, Array.IndexOf(s_outfitIds, c.Id(PartOutfit)));
            foreach (var tok in s_outfitRoles[oi].Split(' '))
            {
                var f = tok.Split(':');
                if (f.Length != 3) continue;
                int k = int.Parse(f[2]);
                Color32 col;
                switch (f[1])
                {
                    case "m": col = main[k]; break;
                    case "t": col = trim[k]; break;
                    case "l": col = C(s_leather[k]); break;
                    case "s": col = C(s_steel[k]); break;
                    default: col = C(s_dark[k]); break;
                }
                look[f[0]] = col;
            }
            look["trim"] = slotc[2];
            look["shadow"] = slotc[3];
            look["hair"] = Block(s_hairShades, Array.IndexOf(s_hairIds, c.Id(PartHair)), 3)[0];
            var list = new List<ColorSwap>();
            foreach (var kv in look)
            {
                int[] src;
                if (!s_roleSrc.TryGetValue(kv.Key, out src)) continue;
                for (int i = 0; i + 1 < src.Length; i += 2)
                {
                    float k = src[i + 1] / 1000f;
                    var t = kv.Value;
                    var to = new Color32((byte)Mathf.Clamp(Mathf.RoundToInt(t.r * k), 0, 255), (byte)Mathf.Clamp(Mathf.RoundToInt(t.g * k), 0, 255),
                                         (byte)Mathf.Clamp(Mathf.RoundToInt(t.b * k), 0, 255), 255);
                    list.Add(new ColorSwap { m_from = C(src[i]), m_to = to });
                }
            }
            var skin = Block(s_skinShades, Array.IndexOf(s_skinIds, c.Id(PartSkin)), 6);
            for (int i = 0; i < s_gameSkinFrom.Length; i++)
                list.Add(new ColorSwap { m_from = C(s_gameSkinFrom[i]), m_to = skin[s_gameSkinShade[i]] });
            sw = list.ToArray();
            s_swapCache[key] = sw;
            return sw;
        }

        // ============================================================================================ in-game gear
        static readonly Dictionary<string, SpriteSheet> s_gearCache = new Dictionary<string, SpriteSheet>();

        /// <summary>The recoloured head and face gear sheets of a player's custom hero (null where the choice has none).</summary>
        public static void GearSheets(PlayerData pd, SlotTier tier, out SpriteSheet head, out SpriteSheet face)
        {
            head = face = null;
            if (pd == null) return;
            var c = Get(pd.Id, tier);
            int slot = HeroLooks.SlotOf(pd);
            string h = c.Id(PartHead), f = c.Id(PartFace);
            var pal = MarkerPalette(c, slot, tier);
            // everything the palette depends on (tier too): the texture name is then a full key for its pixels, so the
            // cache never hands out another tier's colours and an online client never matches a different picture by name
            string ckey = "|" + slot + "|" + (int)tier + "|" + c.Id(PartColour) + "," + c.Id(PartTrim) + "," + c.Id(PartSkin) + "," + c.Id(PartHair);
            if (Array.IndexOf(s_headGear, h) >= 0) head = Recoloured("HcHead_" + h, ckey, pal);
            if (Array.IndexOf(s_faceGear, f) >= 0) face = Recoloured("HcFace_" + f, ckey, pal);
        }

        static SpriteSheet Recoloured(string sid, string ckey, Color32[][] pal)
        {
            string key = sid + ckey;
            SpriteSheet s;
            if (s_gearCache.TryGetValue(key, out s)) return s;
            s = null;
            try
            {
                var src = SpriteSheets.Get(sid);
                if (src != null && src.atlas != null)
                {
                    var t = src.atlas.texture as Texture2D;
                    var px = t.GetPixels32();
                    for (int i = 0; i < px.Length; i++) if (px[i].a > 0) px[i] = Recolour(px[i], pal);
                    s = MakeSheet("Mod_" + key, px, t.width, t.height, src.manifest);
                }
            }
            catch (Exception e) { Plugin.Log.LogWarning("HeroCustom: gear " + sid + " recolour failed: " + e.Message); }
            if (s_gearCache.Count > 256) s_gearCache.Clear();
            s_gearCache[key] = s;
            return s;
        }

        /// <summary>A runtime sheet from pixels (bottom-up rows, like Texture2D.GetPixels32), laid out like SpriteSheets's.</summary>
        static SpriteSheet MakeSheet(string id, Color32[] px, int w, int h, SheetManifest m)
        {
            var tex = new Texture2D(w, h, TextureFormat.ARGB32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, name = id };
            tex.SetPixels32(px);
            tex.Apply();
            SpriteSheets.Keep(tex);
            int count = (w / m.cellW) * (h / m.cellH);
            var elems = new exAtlas.Element[count];
            for (int i = 0; i < count; i++)
            {
                int col = i % m.cols, row = i / m.cols;
                int x = col * m.cellW, yTop = row * m.cellH;
                elems[i] = new exAtlas.Element
                {
                    name = id + "_" + i, originalWidth = m.cellW, originalHeight = m.cellH,
                    trimRect = new Rect(0, 0, m.cellW, m.cellH),
                    coords = new Rect((float)x / w, (float)(h - yTop - m.cellH) / h, (float)m.cellW / w, (float)m.cellH / h),
                    rotated = false
                };
            }
            var atlas = ScriptableObject.CreateInstance<exAtlas>();
            atlas.name = "ModAtlas_" + id;
            atlas.texture = tex;
            atlas.elements = elems;
            var mat = new Material(SpriteSheets.TemplateMaterial) { name = "ModMat_" + id, mainTexture = tex };
            atlas.material = mat;
            SpriteSheets.Keep(atlas);
            SpriteSheets.Keep(mat);
            return new SpriteSheet(id, atlas, m);
        }

        // ============================================================================================ portraits
        const int PW = 29, PH = 24;
        static readonly float[] s_durs = { 0.2f, 0.18f, 0.2f, 0.16f };
        static readonly Dictionary<string, PortraitEntry> s_portraits = new Dictionary<string, PortraitEntry>();
        static Color32[] s_layerPx;
        static int s_layerW, s_layerH;
        static readonly Dictionary<string, exSpriteAnimClip> s_icons = new Dictionary<string, exSpriteAnimClip>();

        static exSpriteAnimClip IconClip(string anim)
        {
            exSpriteAnimClip c;
            if (s_icons.TryGetValue(anim, out c)) return c;
            c = null;
            var sh = SpriteSheets.Get("HcIcons");
            if (sh != null && sh.Has(anim)) c = new ClipBuilder(sh, anim, "ModHcIcon_" + anim).Loop().Build();
            s_icons[anim] = c;
            return c;
        }

        /// <summary>The player's custom hero portrait (4 frame looping Idle, 29x24, in the player's slot colours).</summary>
        public static exSpriteAnimClip PortraitClip(int playerId, SlotTier tier) { return PortraitClip(Get(playerId, tier), playerId, tier); }

        /// <summary>One composed portrait: its runtime sheet (texture + material) and clip, and when it was last asked for.</summary>
        sealed class PortraitEntry
        {
            public SpriteSheet sheet;
            public exSpriteAnimClip clip;
            public long used;
        }

        const int PortraitCacheMax = 48, PortraitCacheKeep = 40, RecentPerSlot = 4;
        static long s_portraitTick;
        static int s_portraitSerial;
        /// <summary>Per slot (0-3): the last few portrait keys asked for, newest last (what a picker or editor shows now).</summary>
        static readonly List<string>[] s_recent = { new List<string>(), new List<string>(), new List<string>(), new List<string>() };

        static string PortraitKey(Choice c, int slot, SlotTier tier)
        {
            var w = WeaponOf(c); var s = SpellOf(c, tier);
            return slot + "|" + tier + "|" + c.Key + "|" + (w.family ?? "") + (w.magic ? "*" : "") + (s.id != "" ? "+" : "");
        }

        /// <summary>Live preview of any choice (the editor's working copy) for a player. Cached per look (LRU; a look a
        /// panel may be showing is never destroyed: every stored silver / gold look and each slot's last few requests).</summary>
        public static exSpriteAnimClip PortraitClip(Choice c, int playerId, SlotTier tier)
        {
            if (c == null) return null;
            if (tier == SlotTier.Normal) tier = SlotTier.Silver;
            int slot = HeroLooks.SlotOfId(playerId);
            string key = PortraitKey(c, slot, tier);
            var recent = s_recent[Mathf.Clamp(slot, 0, 3)];
            recent.Remove(key); recent.Add(key);
            if (recent.Count > RecentPerSlot) recent.RemoveAt(0);
            PortraitEntry e;
            if (s_portraits.TryGetValue(key, out e) && e.clip != null) { e.used = ++s_portraitTick; return e.clip; }
            try
            {
                var w = WeaponOf(c); var s = SpellOf(c, tier);
                var sheet = ComposePortrait(c, slot, tier, w.family, w.id != "" && w.magic, s.id != "");
                if (sheet == null) return null;
                var clip = new ClipBuilder(sheet, "Idle", "ModHcPortrait_" + (s_portraitSerial++)).Loop().Build();
                s_portraits[key] = new PortraitEntry { sheet = sheet, clip = clip, used = ++s_portraitTick };
                if (s_portraits.Count > PortraitCacheMax) EvictPortraits();   // only frees looks nothing shows
                return clip;
            }
            catch (Exception ex)
            {
                Plugin.Log.LogWarning("HeroCustom: portrait failed: " + ex);
                return null;
            }
        }

        static int s_sweepAt = PortraitCacheMax;
        static readonly HarmonyLib.AccessTools.FieldRef<exSpriteAnimation, Dictionary<string, exSpriteAnimState>> s_states =
            HarmonyLib.AccessTools.FieldRefAccess<exSpriteAnimation, Dictionary<string, exSpriteAnimState>>("nameToState");

        /// <summary>
        /// Free the least recently used portraits down to PortraitCacheKeep. Never touched: pinned looks (every stored
        /// silver / gold look, each slot's last few requests) and any entry a live object still uses. Before destroying,
        /// one scan of every exSprite (its atlas) and exSpriteAnimation (default clip, clip list, current and registered
        /// states) finds the users; an entry in use stays cached and is freed by a later sweep once nothing shows it.
        /// The scan only runs when the cache is over its cap, and the next sweep waits for 8 more looks if this one could
        /// not get under it.
        /// </summary>
        static void EvictPortraits()
        {
            if (s_portraits.Count <= s_sweepAt) return;
            var pinned = new HashSet<string>();
            foreach (var r in s_recent) foreach (var k in r) pinned.Add(k);
            for (int pid = 0; pid < 4; pid++)
                foreach (var t in new[] { SlotTier.Silver, SlotTier.Gold })
                {
                    Choice c;
                    if (!s_store[t == SlotTier.Gold ? 1 : 0].TryGetValue(pid, out c)) continue;
                    pinned.Add(PortraitKey(c, HeroLooks.SlotOfId(pid), t));
                }
            var cand = new List<KeyValuePair<string, PortraitEntry>>();
            foreach (var kv in s_portraits) if (!pinned.Contains(kv.Key)) cand.Add(kv);
            cand.Sort((x, y) => x.Value.used.CompareTo(y.Value.used));
            // who still uses our atlases / clips
            var usedAtlas = new HashSet<exAtlas>();
            var usedClip = new HashSet<exSpriteAnimClip>();
            try
            {
                foreach (var sp in Resources.FindObjectsOfTypeAll<exSprite>())
                    if (sp != null && sp.atlas != null) usedAtlas.Add(sp.atlas);
                foreach (var an in Resources.FindObjectsOfTypeAll<exSpriteAnimation>())
                {
                    if (an == null) continue;
                    if (an.defaultAnimation != null) usedClip.Add(an.defaultAnimation);
                    if (an.animations != null) foreach (var cl in an.animations) if (cl != null) usedClip.Add(cl);
                    var cur = an.GetCurrentAnimation();
                    if (cur != null && cur.clip != null) usedClip.Add(cur.clip);
                    Dictionary<string, exSpriteAnimState> st = null;
                    try { st = s_states(an); } catch { }
                    if (st != null) foreach (var v in st.Values) if (v != null && v.clip != null) usedClip.Add(v.clip);
                }
            }
            catch (Exception e)
            {
                Plugin.Log.LogWarning("HeroCustom: portrait sweep could not scan users, nothing freed: " + e.Message);
                s_sweepAt = s_portraits.Count + 8;
                return;
            }
            int drop = s_portraits.Count - PortraitCacheKeep;
            foreach (var kv in cand)
            {
                if (drop <= 0) break;
                var en = kv.Value;
                var atlas = en.sheet != null ? en.sheet.atlas : null;
                if ((atlas != null && usedAtlas.Contains(atlas)) || (en.clip != null && usedClip.Contains(en.clip))) continue;   // still shown
                s_portraits.Remove(kv.Key);
                drop--;
                if (atlas != null)
                {
                    UnityEngine.Object.Destroy(atlas.texture);
                    UnityEngine.Object.Destroy(atlas.material);
                    UnityEngine.Object.Destroy(atlas);
                }
                if (en.clip != null) UnityEngine.Object.Destroy(en.clip);
            }
            s_sweepAt = Math.Max(PortraitCacheMax, s_portraits.Count + (s_portraits.Count > PortraitCacheMax ? 8 : 0));
        }

        /// <summary>Is a composed clip still drawable (clip, its frames' atlas, texture and material alive)?</summary>
        static bool ClipAlive(exSpriteAnimClip c)
        {
            if (c == null || c.frameInfos == null || c.frameInfos.Count == 0) return false;
            var a = c.frameInfos[0].atlas;
            return a != null && a.texture != null && a.material != null;
        }

        static SpriteSheet ComposePortrait(Choice c, int slot, SlotTier tier, string family, bool magic, bool spell)
        {
            var src = SpriteSheets.Get("HcPortrait");
            if (src == null || src.atlas == null) return null;
            if (s_layerPx == null)
            {
                var t = (Texture2D)src.atlas.texture;
                s_layerPx = t.GetPixels32(); s_layerW = t.width; s_layerH = t.height;
            }
            var pal = MarkerPalette(c, slot, tier);
            bool female = c.Id(PartFace) == "Soft";
            var names = new List<string>();
            foreach (var part in s_layerOrder)
            {
                switch (part)
                {
                    case "Weapon": if (!string.IsNullOrEmpty(family)) names.Add("Weapon_" + family); break;
                    case "Outfit": names.Add((female ? "OutfitF_" : "Outfit_") + c.Id(PartOutfit)); break;
                    case "Face": names.Add("Face_" + c.Id(PartFace)); break;
                    case "FacePiece": names.Add("FacePiece_" + c.Id(PartFace)); break;
                    case "Head": names.Add("Head_" + c.Id(PartHead)); break;
                    case "Glint": if (magic && !string.IsNullOrEmpty(family)) names.Add("Glint"); break;
                    case "Spell": if (spell) names.Add("Spell"); break;
                    case "TierCrest": if (tier == SlotTier.Gold) names.Add("TierCrest"); break;
                    default: names.Add(part); break;
                }
            }
            const int OW = 128, OH = 32;
            var outPx = new Color32[OW * OH];
            int cols = src.manifest.cols;
            foreach (var n in names)
            {
                var a = src.Anim(n);
                if (a == null || a.frames == null) continue;
                for (int k = 0; k < 4 && k < a.frames.Length; k++)
                {
                    int fi = a.frames[k];
                    int cx = (fi % cols) * PW, cyTop = (fi / cols) * PH;
                    for (int y = 0; y < PH; y++)
                    {
                        int sy = s_layerH - 1 - (cyTop + y), dy = OH - 1 - y;
                        if (sy < 0) continue;
                        for (int x = 0; x < PW; x++)
                        {
                            var p = s_layerPx[sy * s_layerW + cx + x];
                            if (p.a == 0) continue;
                            p = Recolour(p, pal);
                            p.a = 255;
                            outPx[dy * OW + k * PW + x] = p;
                        }
                    }
                }
            }
            var m = new SheetManifest { cellW = PW, cellH = PH, cols = 4, anims = new[] { new SheetAnim { name = "Idle", frames = new[] { 0, 1, 2, 3 }, durations = s_durs } } };
            return MakeSheet("HcPortrait_" + slot + "_" + tier + "_" + s_portraitSerial, outPx, OW, OH, m);
        }

        // ============================================================================================ self-test
        /// <summary>Static checks (run by the self-test): art for every option, picks resolve, texts clean.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            var all = HeroClasses.All;
            if (all.Count < 3 || all[all.Count - 2].tier != SlotTier.Silver || all[all.Count - 1].tier != SlotTier.Gold)
                bad("hero origins: silver and gold custom heroes are not the last two entries");
            // four player-slot colour sets for every origin: menu portrait and in-game gear
            foreach (var d in all)
            {
                if (d.tier != SlotTier.Normal) continue;
                for (int k = 1; k <= 4; k++)
                {
                    var sh = SpriteSheets.Get(d.portraitArt + "_P" + k);
                    if (sh == null || !sh.Has("Idle")) bad("origin " + d.id + ": slot portrait " + d.portraitArt + "_P" + k + " missing");
                    if (!string.IsNullOrEmpty(d.gearArt) && SpriteSheets.Get(d.gearArt + "_P" + k) == null)
                        bad("origin " + d.id + ": slot gear " + d.gearArt + "_P" + k + " missing");
                }
                int n = 0;
                for (int k = 0; k < 4; k++) if (d.id != "Wanderer" && !HeroLooks.HasSlotTable(d.id, k)) n++;
                if (n > 0) bad("origin " + d.id + ": " + n + " player slot colour table(s) missing (run tools/sprites/hero_looks.py)");
            }
            var ps = SpriteSheets.Get("HcPortrait");
            if (ps == null) bad("custom hero: HcPortrait layers missing");
            var ic = SpriteSheets.Get("HcIcons");
            if (ic == null) bad("custom hero: HcIcons missing");
            foreach (var l in s_layerOrder)
                if (ps != null && l != "Weapon" && l != "Outfit" && l != "Face" && l != "FacePiece" && l != "Head" && !ps.Has(l))
                    bad("custom hero: portrait layer " + l + " missing");
            foreach (var p in Parts)
                foreach (var o in p.options)
                {
                    if (ic != null && !(o.perSlot ? ic.Has(o.icon + "_P1") && ic.Has(o.icon + "_P4") : ic.Has(o.icon)))
                        bad("custom hero: no icon for " + p.id + " " + o.id);
                    if (ps == null) continue;
                    if (p.id == PartOutfit && (!ps.Has("Outfit_" + o.id) || !ps.Has("OutfitF_" + o.id))) bad("custom hero: no outfit layer " + o.id);
                    if (p.id == PartHead && !ps.Has("Head_" + o.id)) bad("custom hero: no head layer " + o.id);
                    if (p.id == PartFace && (!ps.Has("Face_" + o.id) || !ps.Has("FacePiece_" + o.id))) bad("custom hero: no face layer " + o.id);
                }
            foreach (var g in s_headGear) if (SpriteSheets.Get("HcHead_" + g) == null) bad("custom hero: head gear sheet HcHead_" + g + " missing");
            foreach (var g in s_faceGear) if (SpriteSheets.Get("HcFace_" + g) == null) bad("custom hero: face gear sheet HcFace_" + g + " missing");
            foreach (var f in s_families) if (ps != null && !ps.Has("Weapon_" + f)) bad("custom hero: no portrait weapon " + f);
            foreach (var t in new[] { "HeroCustomSilver", "HeroCustomGold" })
                if (SpriteSheets.Get(t) == null || !SpriteSheets.Get(t).Has("Idle")) bad("custom hero: slot portrait " + t + " missing");
            int missing = 0;
            foreach (var l in new[] { Weapons, Spells })
                foreach (var p in l)
                {
                    if (!p.Available) { missing++; Plugin.Log.LogWarning("HeroCustom: pick not loaded: " + p.id); }
                    if (p.debuff.vit > 0 || p.debuff.str > 0 || p.debuff.dex > 0) bad("custom hero: " + p.id + " has a positive debuff");
                    if (p.id != "" && p.debuff.IsEmpty) bad("custom hero: " + p.id + " costs nothing");
                    foreach (var s in new[] { p.name, p.text, p.DebuffText })
                        if (s != null && s.IndexOfAny(new[] { '%', '{', '}', '|', '~', '[' }) >= 0) bad("custom hero: text of " + p.id + " has a special character: " + s);
                }
            if (missing > 0) bad("custom hero: " + missing + " weapon/spell pick(s) not loaded (see log)");
            // every mod weapon / spell has a hand-tuned entry
            foreach (var d in WeaponPack.Defs) if (!s_modWeapons.ContainsKey(d.id)) bad("custom hero: mod weapon " + d.id + " has no debuff entry (uses the cost rule)");
            foreach (var k in ItemPack.Built.Keys) if (k.StartsWith("Spell", StringComparison.Ordinal) && !s_modSpells.ContainsKey(k)) bad("custom hero: mod spell " + k + " has no debuff entry (uses the cost rule)");
            // the cache never frees a look that is stored or shown: compose 60 looks, the stored looks must stay drawable
            try
            {
                var stored = new List<exSpriteAnimClip>();
                for (int pid = 0; pid < 4; pid++)
                    foreach (var t in new[] { SlotTier.Silver, SlotTier.Gold }) stored.Add(PortraitClip(pid, t));
                var probe = Default();
                for (int i = 0; i < 60; i++)
                {
                    probe.Step(PartColour, 1);
                    if (i % 17 == 16) probe.Step(PartHead, 1);
                    PortraitClip(probe, i % 4, (i & 1) == 0 ? SlotTier.Silver : SlotTier.Gold);
                }
                int dead = 0;
                foreach (var cl in stored) if (!ClipAlive(cl)) dead++;
                if (dead > 0) bad("custom hero: " + dead + " stored portrait clip(s) destroyed by the portrait cache");
                if (s_portraits.Count > PortraitCacheMax + 16) bad("custom hero: portrait cache grew to " + s_portraits.Count + " looks");
            }
            catch (Exception ex) { bad("custom hero: portrait cache check crashed: " + ex.Message); }
            // round trip of the saved form
            var c = Default(); c.Step(PartHead, 3); c.weapon = "WeaponBow"; c.spell = "SpellHyperdash";
            if (Choice.Parse(c.Key).Key != c.Key) bad("custom hero: choice does not survive a save / load round trip");
        }
    }
}
