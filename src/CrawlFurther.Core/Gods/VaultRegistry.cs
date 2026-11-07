using System.Collections.Generic;

namespace CrawlFurther.Gods
{
    /// <summary>
    /// Extra entries for the main-menu vault (creatures that are not on any god's tree, ghost forms...). Add them at
    /// load time, from a content pack; the vault reads the list when it builds its pages.
    /// </summary>
    public static class VaultRegistry
    {
        public class Entry
        {
            /// <summary>Vault page: "Monsters", "Ghosts", "Heroes"...</summary>
            public string category;
            /// <summary>Prefab name for a monster (e.g. "ModGhostMote"), any unique id otherwise.</summary>
            public string id;
            /// <summary>Display name.</summary>
            public string name;
            /// <summary>One line of description.</summary>
            public string text;
            /// <summary>Sprite sheet whose "Portrait" anim (or "Idle" frame 0) is the picture.</summary>
            public string iconSheet;
        }

        public static readonly List<Entry> Entries = new List<Entry>();

        /// <summary>Add an entry; a second entry with the same category and id is ignored.</summary>
        public static void Add(string category, string id, string name, string text, string iconSheet)
        {
            foreach (var e in Entries) if (e.category == category && e.id == id) return;
            Entries.Add(new Entry { category = category, id = id, name = name, text = text, iconSheet = iconSheet });
        }
    }
}
