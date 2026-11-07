namespace CrawlFurther.Testing
{
    /// <summary>One entry of a test panel list: the text shown, the object it stands for, and the heading it sits under.</summary>
    public sealed class TestItem
    {
        /// <summary>The text on the entry's button.</summary>
        public string Label { get; private set; }

        /// <summary>What the entry stands for (a prefab, a deity, an id...). The list's pick callback gets it back.</summary>
        public object Value { get; private set; }

        /// <summary>The heading the entry is listed under ("Tier 2", "Vanilla"), or null for none.</summary>
        public string Group { get; private set; }

        /// <summary>Create an entry. Entries with the same <paramref name="group"/> should be next to each other.</summary>
        public TestItem(string label, object value, string group = null)
        {
            Label = label ?? "";
            Value = value;
            Group = group;
        }
    }
}
