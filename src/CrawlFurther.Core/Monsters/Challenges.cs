using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Util;

    /// <summary>
    /// Vault challenges for mod monsters. They are the game's own hero challenges: the vault's Challenge button, its
    /// level (one cave room, a bot hero that gains a level, a weapon and now and then a spell or artifact each time it
    /// dies), its HUD, scoring and save. Core only gives each mod monster's vault entry its goal, the hero level to
    /// reach, which is the one setting the game keeps per monster. The room, weapons, powerups and gold are shared by
    /// every challenge, the game's own included.
    ///
    /// Who gets one, as in the game, whose vault lists only monsters a player can become: every mod monster reached
    /// from a god's starting monsters through evolutions, and every secret that is a mod monster (see
    /// <see cref="UI.LibraryEntries.SecretMonster"/>) and its evolutions. Minions and ghost blobs get none. A <see cref="ChallengeDef"/> overrides both ways.
    ///
    /// Scores are saved by the game with the rest of the vault, under the prefab name ("Mod" + id). They never count
    /// towards the game's challenge achievements, and no achievement is granted while a mod monster's challenge runs.
    /// </summary>
    public static class Challenges
    {
        /// <summary>The goal of a vault entry with no challenge (no hero level reaches it).</summary>
        public const int NoGoal = 9999;
        /// <summary>The highest goal a <see cref="ChallengeDef"/> may set.</summary>
        public const int MaxGoal = 30;

        /// <summary>
        /// The goal by evolution cost: a monster takes the goal of the highest cost it reaches. The game's own goals (4,
        /// 5, 7 and 10 on average at its costs 0, 1, 2.5 and 4) are passed by few players. These are about 70% of them:
        /// the hero level a player of moderate skill reaches in half of all runs of five tries, from a model of the
        /// challenge (tools/challenge_sim.py). Crawl: Further's tiers cost 0, 2.5 and 4.5, so they get 3, 5 and 7.
        /// Change it before the vault opens.
        /// </summary>
        public static readonly List<KeyValuePair<float, int>> GoalByCost = new List<KeyValuePair<float, int>>
        {
            new KeyValuePair<float, int>(0f, 3),
            new KeyValuePair<float, int>(1f, 4),
            new KeyValuePair<float, int>(2.5f, 5),
            new KeyValuePair<float, int>(4f, 7),
        };

        static readonly Dictionary<string, ChallengeDef> s_defs = new Dictionary<string, ChallengeDef>();

        /// <summary>Set the challenge of the monster prefab <paramref name="prefabName"/> (e.g. "ModWickling"), replacing
        /// any. <see cref="MonsterFactory.Build"/> does this for <see cref="MonsterDef.challenge"/>.</summary>
        public static void Register(string prefabName, ChallengeDef def)
        {
            if (string.IsNullOrEmpty(prefabName) || def == null) return;
            s_defs[prefabName] = def;
        }

        /// <summary>The <see cref="ChallengeDef"/> registered for a prefab name, or null.</summary>
        public static ChallengeDef Of(string prefabName)
        {
            ChallengeDef d;
            return prefabName != null && s_defs.TryGetValue(prefabName, out d) ? d : null;
        }

        /// <summary>The goal <see cref="GoalByCost"/> gives an evolution cost.</summary>
        public static int GoalFor(float evolveCost)
        {
            int goal = 0;
            float best = float.MinValue;
            foreach (var kv in GoalByCost)
                if (evolveCost >= kv.Key - 0.001f && kv.Key > best) { best = kv.Key; goal = kv.Value; }
            if (goal <= 0 && GoalByCost.Count > 0) goal = GoalByCost[0].Value;
            return Mathf.Clamp(goal, 1, MaxGoal);
        }

        /// <summary>The goal <see cref="GoalByCost"/> gives this monster prefab's evolution cost.</summary>
        public static int GoalFor(Player prefab)
        {
            float cost = 0f;
            try { if (prefab != null) cost = R.Get<float>(prefab, "m_evolveCost"); } catch { }
            return GoalFor(cost);
        }

        /// <summary>The goal of this mod monster's challenge, or 0 for none. <paramref name="playable"/>: a player can
        /// become it (Core works that out for the vault).</summary>
        public static int GoalOf(Player prefab, bool playable)
        {
            if (prefab == null) return 0;
            var d = Of(prefab.gameObject.name);
            if (d != null)
            {
                if (d.none) return 0;
                return d.goal > 0 ? Mathf.Clamp(d.goal, 1, MaxGoal) : GoalFor(prefab);
            }
            return playable ? GoalFor(prefab) : 0;
        }

        /// <summary>The monster of the challenge being played when it is a mod monster, else null.</summary>
        public static Player RunningModMonster
        {
            get
            {
                try
                {
                    if (!Singleton<SystemMenu>.HasInstance() || !SystemMenu.GetChallengeMode()) return null;
                    var p = SystemMenu.GetChallengeModeMonster();
                    return p != null && MonsterFactory.Built.ContainsValue(p) ? p : null;
                }
                catch (Exception) { return null; }
            }
        }

        /// <summary>A challenge is being played and its monster is a mod monster.</summary>
        public static bool ModChallengeRunning { get { return RunningModMonster != null; } }
    }
}
