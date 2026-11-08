using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Library
{
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Content.Ghosts;

    /// <summary>
    /// Crawl: Further's vault challenges. Core gives them (see <see cref="Challenges"/>): every monster of the nine
    /// gods' trees and every secret monster (statues, silver uniques, the gold line) has the game's hero challenge,
    /// with the goal for its tier from <see cref="Challenges.GoalByCost"/> (4, 7 and 10). Minions and the ghost blobs
    /// have none, as the game's own fodder and blobs have none. This is the self-test of that.
    /// </summary>
    public static class MonsterChallenges
    {
        /// <summary>Monsters per god tree (3 / 6 / 12).</summary>
        const int PerGod = 21;
        /// <summary>Secret monsters: 3 silver uniques, the 7 of the gold line and the 5 secret statues.</summary>
        const int SecretMonsters = 15;

        public static void SelfCheck(Action<string> bad, Action<string> note)
        {
            if (!Singleton<SystemLibrary>.HasInstance() || !LibraryEntries.HasModEntries)
            {
                note("the vault is not built yet: challenges are given when it is");
                return;
            }
            int gods = 0, inTrees = 0;
            foreach (var god in ContentChecks.GodNames)
            {
                var d = SystemDeity.GetDeity(god);
                if (d == null) continue;   // the trees section reports a missing god
                gods++;
                int n = 0;
                var seen = new HashSet<Player>();
                var todo = new Queue<KeyValuePair<Player, int>>();
                foreach (var go in d.GetStartingMonsters() ?? new GameObject[0])
                {
                    var p = go != null ? go.GetComponent<Player>() : null;
                    if (p != null) todo.Enqueue(new KeyValuePair<Player, int>(p, 1));
                }
                while (todo.Count > 0)
                {
                    var kv = todo.Dequeue();
                    if (!seen.Add(kv.Key)) continue;
                    n++;
                    Check(kv.Key, god + " T" + kv.Value, Challenges.GoalFor(kv.Key), bad);
                    foreach (var x in kv.Key.GetEvolveTo() ?? new Player[0]) if (x != null) todo.Enqueue(new KeyValuePair<Player, int>(x, kv.Value + 1));
                }
                if (n != PerGod) bad(god + ": " + n + " monsters in the tree, " + PerGod + " expected");
                inTrees += n;
            }
            int secrets = 0;
            foreach (var se in Secrets.All)
            {
                var p = LibraryEntries.SecretMonster(se);
                if (p == null) { if (se != null && se.monster) bad("secret monster " + se.id + " is not built"); continue; }
                Check(p, "secret", Challenges.GoalFor(p), bad);
                secrets++;
            }
            if (secrets != SecretMonsters) bad(secrets + " secret monsters have a challenge, " + SecretMonsters + " expected (3 silver, 7 gold, 5 statues)");
            foreach (var b in new[] { GhostPack.Mote, GhostPack.Spitter, GhostPack.Gel, GhostPack.Brute, GhostPack.Titan, GhostPack.King })
            {
                if (b == null) continue;   // the ghost forms section reports a missing blob
                var e = SystemLibrary.GetMonsterEntry(b.gameObject);
                if (e != null && LibraryEntries.HasChallenge(e)) bad(b.gameObject.name + ": a ghost blob has a challenge (the game's blobs have none)");
            }
            note(inTrees + " god monsters (" + gods + " gods) and " + secrets + " secret monsters have the game's challenge; the ghost blobs have none");
        }

        static void Check(Player p, string where, int goal, Action<string> bad)
        {
            var e = SystemLibrary.GetMonsterEntry(p.gameObject);
            string label = where + " " + p.gameObject.name;
            if (e == null) { bad(label + ": no vault entry"); return; }
            if (!LibraryEntries.HasChallenge(e)) { bad(label + ": no challenge"); return; }
            if (Challenges.Of(p.gameObject.name) == null && e.m_targetScore != goal) bad(label + ": goal " + e.m_targetScore + ", the tier table gives " + goal);
        }
    }
}
