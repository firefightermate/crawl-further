using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// Rules <see cref="ModMonster"/> applies to every instance of one mod monster: hit-blocking plates, regeneration,
    /// stealth, echoing attacks, a limited lifetime, and extra <see cref="MonsterBehaviour"/> components. Give a
    /// <see cref="MonsterDef.traits"/> or call <see cref="Register"/> before the monster first spawns. Derive from this
    /// class to carry settings of your own and read them back from your behaviour through <see cref="ModMonster.Traits"/>.
    /// </summary>
    public class MonsterTraits
    {
        static readonly Dictionary<string, MonsterTraits> s_byPrefab = new Dictionary<string, MonsterTraits>();

        /// <summary>Set the traits of the monster prefab <paramref name="prefabName"/> (e.g. "ModWickling"), replacing any.</summary>
        public static void Register(string prefabName, MonsterTraits traits)
        {
            if (string.IsNullOrEmpty(prefabName) || traits == null) return;
            s_byPrefab[prefabName] = traits;
        }

        /// <summary>The traits registered for a prefab name, or null.</summary>
        public static MonsterTraits Of(string prefabName)
        {
            MonsterTraits t;
            return prefabName != null && s_byPrefab.TryGetValue(prefabName, out t) ? t : null;
        }

        /// <summary>Plate art for monsters whose traits name none: the orbiting visual and the break effect.</summary>
        public static GameObject DefaultPlateFx, DefaultPlateBreakFx;

        /// <summary>Plates the monster can hold from its own sources (each blocks one hit from the hero).</summary>
        public int maxPlates;
        /// <summary>Looping visual parented to the body while it has plates (null: <see cref="DefaultPlateFx"/>).</summary>
        public GameObject plateFx;
        /// <summary>Spawned when a plate absorbs a hit (null: <see cref="DefaultPlateBreakFx"/>).</summary>
        public GameObject plateBreakFx;
        /// <summary>Show the plate counter over the head even for one plate (for monsters that can stack past maxPlates).</summary>
        public bool showPlateCount;

        /// <summary>Where the monster regenerates: called each frame with its position; null means never.</summary>
        public Func<Vector2, bool> regenAt;
        /// <summary>Health regained per second while <see cref="regenAt"/> holds.</summary>
        public float regenPerSecond = 0.35f;

        /// <summary>Keep the gold-stealing hit (the vanilla Thieving status) that a monster cloned from a thief such as
        /// the gnome inherits. Off by default: the hero only loses gold to monsters meant to take it.</summary>
        public bool stealsGold;

        /// <summary>Turns nearly invisible after standing still for 0.9 s.</summary>
        public bool stealth;
        /// <summary>Where the monster is nearly invisible (e.g. inside a darkness cloud); null means nowhere.</summary>
        public Func<Vector2, bool> hiddenAt;

        /// <summary>Attacks whose effect has an echo template (<see cref="FxKit.EchoOf"/>) repeat after <see cref="echoDelay"/>.</summary>
        public bool echo;
        /// <summary>Seconds between an attack and its echo.</summary>
        public float echoDelay = 0.6f;
        /// <summary>Spawned at the feet with each echo, beside the afterimage (optional).</summary>
        public GameObject echoFx;

        /// <summary>Above 0: the monster despawns after this many seconds (decoys, summons).</summary>
        public float lifetime;
        /// <summary>Spawned, owned by the monster, when its lifetime runs out (optional).</summary>
        public GameObject expireFx;

        /// <summary>Components added to every instance; see <see cref="Add{T}"/>.</summary>
        public readonly List<Type> behaviours = new List<Type>();

        /// <summary>Add a <see cref="MonsterBehaviour"/> to every instance of this monster. Returns this, for chaining.</summary>
        public MonsterTraits Add<T>() where T : MonsterBehaviour
        {
            if (!behaviours.Contains(typeof(T))) behaviours.Add(typeof(T));
            return this;
        }
    }
}
