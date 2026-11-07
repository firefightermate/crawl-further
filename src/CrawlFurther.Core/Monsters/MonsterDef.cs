using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;

    /// <summary>
    /// A new monster: a vanilla base prefab cloned, reskinned with your sheet and re-tuned. Pass it to
    /// <see cref="MonsterFactory.Build"/> once the game's prefabs are loaded, then link the tree with
    /// <see cref="MonsterFactory.LinkEvolutions"/>.
    /// </summary>
    public class MonsterDef
    {
        /// <summary>Unique id; the prefab is named "Mod" + id.</summary>
        public string id;
        /// <summary>The vanilla monster prefab whose body, physics and AI you start from (e.g. "EnemyGnome").</summary>
        public string basePrefab;
        /// <summary>The art sheet id (defaults to <see cref="id"/>). Needs Idle, Run and Death (or Dead) anims.</summary>
        public string art;
        /// <summary>Max health; 0 or below keeps the base's.</summary>
        public float health = -1f;
        /// <summary>Multiplies the base's move speed.</summary>
        public float speedMult = 1f;
        /// <summary>Evolution cost. Below 0 keeps the base's. Core reads it as the tier (<see cref="TierRules"/>): Crawl:
        /// Further's trees cost 0, 2.5 and 4.5 (the game's own tiers cost 0, 1, 2.5 and 4).</summary>
        public float evolveCost = -1f;
        /// <summary>Seconds to charge the special, set after the <see cref="kit"/> and the tier rule. 0 or below keeps
        /// theirs.</summary>
        public float specialChargeTime = -1f;
        /// <summary>Multiplies the cooldown of every basic attack, the <see cref="kit"/>'s included.</summary>
        public float attackCooldownMult = 1f;
        /// <summary>Multiplies every hit this monster lands on the hero (its moves and what its behaviours spawn), on top
        /// of the tier rule. Statuses keep their own damage.</summary>
        public float damageMult = 1f;
        /// <summary>What it evolves into: ids of mod monsters or vanilla prefab names.</summary>
        public string[] evolveTo = new string[0];
        /// <summary>Keep the base prefab's own evolutions instead of <see cref="evolveTo"/>.</summary>
        public bool keepEvolutions;
        /// <summary>
        /// The authored moveset, run after the reskin: replace the base's attacks with your own (see <see cref="Kit"/>,
        /// <see cref="FxKit"/>, <see cref="Strike"/>). Arguments: the new prefab's Player and its sheet.
        /// </summary>
        public Action<Player, SpriteSheet> kit;
        /// <summary>Without a <see cref="kit"/>: maps the base's attack slots ("Attack0", "Attack1", "Special") to anims of
        /// your sheet with other names. Unmapped slots use the anim of the slot's own name.</summary>
        public Dictionary<string, string> aliases = new Dictionary<string, string>();
        /// <summary>Last step of the build, for anything else: (prefab GameObject, its Player).</summary>
        public Action<GameObject, Player> customize;
        /// <summary>Plates, regeneration, stealth, lifetime and extra behaviours (optional; see <see cref="MonsterTraits"/>).</summary>
        public MonsterTraits traits;

        /// <summary>"Mod" + id: the prefab's name, and the key for tips, statues and traits.</summary>
        public string PrefabName { get { return "Mod" + id; } }
    }
}
