using System;
using System.Collections.Generic;

namespace CrawlFurther.UI
{
    /// <summary>
    /// A category of its own in the vault (the main menu library), listed before BACK and shown as a picture grid.
    /// Register it with <see cref="Vault.AddCategory"/> when your mod starts. A category with no pages is not listed.
    /// </summary>
    public class VaultCategory
    {
        /// <summary>The category's menu text, in capitals ("FURTHER").</summary>
        public string label;
        /// <summary>A sheet whose frame 0 is the stamp shown while the category is highlighted (59 x 48, like the vanilla
        /// stamps). Null: no stamp.</summary>
        public string stamp;
        /// <summary>The text under the category list while it is highlighted: (found, total) -> text.</summary>
        public Func<int, int, string> summary;
        /// <summary>Builds the pages. Called once, when the vault entries are made (after every content pack has run).</summary>
        public Func<IEnumerable<VaultPage>> pages;
        /// <summary>True: the pages are the registered <see cref="Secrets"/> (riddle and silhouette until found);
        /// <see cref="pages"/> is not used.</summary>
        public bool secrets;
        /// <summary>Extra self-test checks for this category's pages (run in the "branding" self-test section).</summary>
        public Action<Action<string>> selfCheck;
    }
}
