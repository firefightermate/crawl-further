using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.UI
{
    /// <summary>
    /// Vault (main menu library) pages for mod content. Mod monsters, shop items and weapons get their pages without
    /// any call (from MonsterFactory and <see cref="Items.ItemRegistry"/>); this is for the text and the rest.
    /// </summary>
    public static class Vault
    {
        internal class MonsterLine { public string id, name, line; }

        internal static readonly List<MonsterLine> MonsterLines = new List<MonsterLine>();
        internal static readonly List<VaultCategory> Categories = new List<VaultCategory>();

        /// <summary>
        /// The name and line (one line in the vanilla prop tone, up to 90 characters) of a mod monster's vault page, by
        /// MonsterDef id. The MONSTERS grid lists monsters with a line from here in the order they were added; a monster
        /// without one takes the "vault" line of its tip (see <see cref="TipRegistry.AddVaultLine"/>) and is listed after
        /// the block of its tip group.
        /// </summary>
        public static void AddMonsterLine(string monsterId, string name, string line)
        {
            if (string.IsNullOrEmpty(monsterId)) return;
            MonsterLines.RemoveAll(m => m.id == monsterId);
            MonsterLines.Add(new MonsterLine { id = monsterId, name = name, line = line });
        }

        /// <summary>Add a category of your own (see <see cref="VaultCategory"/>). Call it when your mod starts.</summary>
        public static void AddCategory(VaultCategory category)
        {
            if (category != null && !string.IsNullOrEmpty(category.label) && !Categories.Contains(category)) Categories.Add(category);
        }

        /// <summary>
        /// A page in the OBJECTS grid for a room object (trap, interactable, prop). <see cref="Objects.ObjectKit"/> calls
        /// this itself. Works before or after the vault is built. The page is found when a human player meets the object:
        /// call SystemLibrary.OnEntryFound(playerData, instance) from your interaction code. The picture is
        /// <paramref name="portrait"/>, else the prefab's own (its "Active" state, its default animation or its sprite).
        /// </summary>
        public static void AddObject(GameObject prefab, string name, string description, exSpriteAnimClip portrait = null, Vector2 portraitOffset = default(Vector2))
        {
            LibraryEntries.AddExtra(prefab, name, description, portrait, portraitOffset, true);
        }

        /// <summary>A page in the ITEMS grid for a Powerup that was not built through <see cref="Items.ItemRegistry"/>.</summary>
        public static void AddItem(Powerup item)
        {
            if (item == null || Items.ItemRegistry.Items.ContainsValue(item)) return;
            LibraryEntries.AddExtra(item.gameObject, item.GetDisplayName(), item.GetDescription(), null, default(Vector2), false);
        }
    }
}
