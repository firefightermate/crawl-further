using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;

    /// <summary>
    /// Everything that makes a god: what the god select shows, the starters, the monster tree, the perk and the tips.
    /// Pass it to <see cref="DeityFactory.Register"/> from a content pack.
    /// </summary>
    public class GodDef
    {
        /// <summary>The god's name, shown on the god select and used as its id (must be unique).</summary>
        public string name;
        /// <summary>The perk line under the portrait ("Dead burn as pyres, then wax").</summary>
        public string text;
        /// <summary>Flavour text, two short lines ("\n" between them).</summary>
        public string flavour;
        /// <summary>The line shown when the god's player wins; null takes the template god's.</summary>
        public string winText;
        /// <summary>Sprite sheet of the portrait: its "Portrait" anim, or "Idle" when it has none (29 x 24 pixels).</summary>
        public string portraitArt;
        /// <summary>Vanilla god whose select sound and win animation this god uses.</summary>
        public string copySoundsFrom = "Gholoth";
        /// <summary>The starters: MonsterDef ids or vanilla prefab names. The vanilla menus show three.</summary>
        public string[] startingMonsters;
        /// <summary>Gold at the start of a run.</summary>
        public int gold;
        /// <summary>Vanilla god whose perk (PlayerModifiers) this god uses; ignored when <see cref="modifiers"/> is set.</summary>
        public string copyModifiersFrom;
        /// <summary>The god's own PlayerModifiers (a stat perk); null for none.</summary>
        public PlayerModifier[] modifiers;

        /// <summary>The god's monsters (starters and every evolution). Register builds them and links their trees;
        /// leave null when you build them yourself before registering.</summary>
        public MonsterDef[] monsters;
        /// <summary>A perk that lives on the monsters: run on every monster in <see cref="monsters"/> after its own
        /// customize (e.g. add a death spawn). Arguments: the prefab's GameObject and its Player.</summary>
        public Action<GameObject, Player> perk;
        /// <summary>HUD and pause tips per monster prefab name ("Mod" + MonsterDef.id).</summary>
        public Dictionary<string, MonsterTip> tips;
        /// <summary>The god's page in Pause > Tips, shown while a player follows the god (its god field is the god's name).</summary>
        public PauseTopic pausePage;
    }
}
