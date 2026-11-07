using System;

namespace CrawlFurther.UI
{
    /// <summary>
    /// One page in a mod vault category (see <see cref="VaultCategory.pages"/>). Pages start found and show their
    /// picture; a page with <see cref="unlock"/> or <see cref="locked"/> shows a padlock and the challenge's progress
    /// until it opens.
    /// </summary>
    public class VaultPage
    {
        /// <summary>A short word for what the page is ("God", "Hero"); with <see cref="id"/> it makes the page's save key
        /// "ModVault" + kind + id (letters and digits only), so keep both stable once released.</summary>
        public string kind, id;
        /// <summary>The page's title and text (one or two lines; GUIText drops any "[word]").</summary>
        public string name, text;
        /// <summary>The sheet of the picture: its "Portrait" anim, else "Vault", else "Idle". Null: no picture.</summary>
        public string art;
        /// <summary>An <see cref="Unlocks"/> challenge id: the page is locked until it is done.</summary>
        public string unlock;
        /// <summary>Optional lock test that overrides <see cref="unlock"/> (true: locked).</summary>
        public Func<bool> locked;
    }
}
