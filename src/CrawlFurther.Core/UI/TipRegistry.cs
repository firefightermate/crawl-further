using System.Collections.Generic;

namespace CrawlFurther.UI
{
    /// <summary>
    /// The text of the HUD monster tips, the Pause > Tips pages and the monsters' vault lines.
    ///
    /// Monster tips are keyed by prefab name ("ModWickling"; a boss part is "BossPrefab/PartName"). A player who takes a
    /// monster body sees its tip above their HUD panel, and the first pause page repeats it. Add them with
    /// <see cref="Add"/> when your mod starts. Crawl: Further keeps its text in data/tips/tips_&lt;group&gt;.json:
    /// <code>
    /// { "ModWickling": { "name": "Wickling", "attack": "Lunging bite", "special": "Dash off in a streak of fire",
    ///                    "passive": ["first line", "second line"], "vault": "A wick-tailed rat that bites..." } }
    /// </code>
    /// tools/merge_tips.py checks lengths and characters and turns the files into C# tables that the mod adds here; the
    /// file name is the group. Pause pages are <see cref="PauseTopic"/>s (data/tips/tips_pages.json): the topics of the
    /// gods in the current game come first, then the game's own pages, then <see cref="TopicOrder"/>, then the rest.
    /// </summary>
    public static class TipRegistry
    {
        public static readonly Dictionary<string, MonsterTip> Tips = new Dictionary<string, MonsterTip>();
        /// <summary>Prefabs that share another prefab's tip.</summary>
        public static readonly Dictionary<string, string> Alias = new Dictionary<string, string>();
        /// <summary>The group of each key ("ysveld", "ghosts"): it links a monster to the pause topic with that id, and
        /// keeps a god's monsters together in the vault.</summary>
        public static readonly Dictionary<string, string> Group = new Dictionary<string, string>();
        /// <summary>Vault lines: prefab name -> (display name, line).</summary>
        public static readonly Dictionary<string, KeyValuePair<string, string>> Vault = new Dictionary<string, KeyValuePair<string, string>>();
        /// <summary>The <see cref="Vault"/> keys in the order they were added.</summary>
        public static readonly List<string> VaultOrder = new List<string>();
        /// <summary>The Pause > Tips topics in the order they were added.</summary>
        public static readonly List<PauseTopic> Topics = new List<PauseTopic>();
        /// <summary>Topic ids shown right after the game's own pause pages, in this order (shared mechanics); the topics of
        /// gods not in the game follow.</summary>
        public static readonly List<string> TopicOrder = new List<string>();
        /// <summary>The topic whose paragraphs describe the ghost forms: the paragraph holding "&gt;FormId:&lt;" and the
        /// bullets after it make a ghost's "you" page.</summary>
        public static string GhostFormTopic;

        /// <summary>Add (or replace) the tip for a prefab name. <paramref name="group"/> is optional.</summary>
        public static void Add(string key, MonsterTip tip, string group = null)
        {
            if (string.IsNullOrEmpty(key)) return;
            Tips[key] = tip;
            if (group != null) Group[key] = group;
        }

        /// <summary>Show <paramref name="sameAs"/>'s tip for <paramref name="key"/> too.</summary>
        public static void AddAlias(string key, string sameAs) { if (!string.IsNullOrEmpty(key)) Alias[key] = sameAs; }

        /// <summary>A monster's vault name and line (one line in the vanilla prop tone, up to 90 characters). Used for a mod
        /// monster with no <see cref="UI.Vault.AddMonsterLine"/> line.</summary>
        public static void AddVaultLine(string key, string name, string line)
        {
            if (string.IsNullOrEmpty(key)) return;
            if (!Vault.ContainsKey(key)) VaultOrder.Add(key);
            Vault[key] = new KeyValuePair<string, string>(name, line);
        }

        /// <summary>Add a Pause > Tips topic (replacing one with the same id).</summary>
        public static void AddTopic(PauseTopic topic)
        {
            if (topic == null) return;
            int i = Topics.FindIndex(t => t.id == topic.id);
            if (i >= 0) Topics[i] = topic; else Topics.Add(topic);
        }

        /// <summary>The tip for a prefab name, following aliases. False if there is none.</summary>
        public static bool TryGet(string key, out MonsterTip tip)
        {
            string a;
            if (key != null && Alias.TryGetValue(key, out a)) key = a;
            if (key != null && Tips.TryGetValue(key, out tip)) return true;
            tip = default(MonsterTip);
            return false;
        }
    }
}
