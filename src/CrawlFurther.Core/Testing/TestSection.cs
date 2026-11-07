using System.Collections.Generic;

namespace CrawlFurther.Testing
{
    /// <summary>A page of the test panel: its controls in the left column, its lists side by side on the right.</summary>
    sealed class TestSection
    {
        public readonly string Name;
        public readonly List<TestControl> Controls = new List<TestControl>();
        public readonly List<TestList> Lists = new List<TestList>();

        public TestSection(string name) { Name = name; }
    }
}
