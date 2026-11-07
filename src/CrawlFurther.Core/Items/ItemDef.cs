using System;
using UnityEngine;

namespace CrawlFurther.Items
{
    /// <summary>
    /// A shop item (spell, potion or artifact): a copy of a vanilla Powerup prefab with a new name, text, price and
    /// icons, sold from a vanilla shop group. Pass it to <see cref="ItemRegistry.Register(ItemDef)"/>.
    /// </summary>
    public class ItemDef
    {
        /// <summary>Unique id. The prefab is named "Mod" + id; its shop pedestal frame is named id.</summary>
        public string id;
        /// <summary>The vanilla Powerup prefab to copy (its effects, sounds and behaviour), e.g. "SpellCycloneSummon".</summary>
        public string cloneFrom;
        /// <summary>Shop name and description. Plain words: the game's GUIText drops any "[word]".</summary>
        public string name, description;
        public float cost;
        /// <summary>Sheets for the shop bubble (anim "Bubble") and the HUD icon (anim "Hud"); null keeps the vanilla one.</summary>
        public string bubbleArt, hudArt;
        /// <summary>The vanilla SpawnGroup that sells it, e.g. "GroupSpellsPurchasable" or "GroupArtifactsPurchasable".</summary>
        public string group;
        /// <summary>Runs on the new prefab before it is registered: re-wire effects, modifiers and so on here.</summary>
        public Action<GameObject, Powerup> customize;
    }
}
