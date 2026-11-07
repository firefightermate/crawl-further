namespace CrawlFurther.UI
{
    /// <summary>
    /// A secret: something rare a player can find. Its vault page shows the riddle and rarity until it is found, then
    /// its name, picture and text. Register it with <see cref="Secrets.Add"/> and mark it found with
    /// <see cref="Secrets.Found"/> from your own game code. All text is plain words: no "[word]" and none of % { | } ~.
    /// </summary>
    public class SecretDef
    {
        /// <summary>Unique id, e.g. "SecretStatueGargoyle", or a monster's prefab name.</summary>
        public string id;
        /// <summary>The real name, shown once found.</summary>
        public string name;
        /// <summary>Shown until it is found: a riddle or a plain hint (up to 75 characters).</summary>
        public string riddle;
        /// <summary>How rare it is, e.g. "Rare" or "Legendary: about 1 in 200" (up to 30 characters).</summary>
        public string rarity;
        /// <summary>Shown once found: what it is and does, one or two lines (up to 120 characters).</summary>
        public string text;
        /// <summary>The sheet of its picture ("Portrait", else "Vault", else "Idle" frame 0).</summary>
        public string iconSheet;
        /// <summary>Its group (see <see cref="Secrets.AddGroup"/>): the vault lists secrets group by group.</summary>
        public string group;
        /// <summary>True for a monster secret: found when a human player becomes the monster whose prefab name is
        /// <see cref="id"/> (spawns as, evolves into or inhabits it).</summary>
        public bool monster;
    }
}
