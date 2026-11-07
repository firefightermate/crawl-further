using System;

namespace CrawlFurther.Testing
{
    /// <summary>A button, switch, number or choice on a test panel page. The panel draws each kind; see TestPanel.</summary>
    abstract class TestControl
    {
        public string Name;
    }

    sealed class TestAction : TestControl
    {
        public Action Run;
    }

    sealed class TestToggle : TestControl
    {
        public Func<bool> Get;
        public Action<bool> Set;
    }

    sealed class TestNumber : TestControl
    {
        public int Min, Max, Value;
        public Action<int> Run;
    }

    sealed class TestChoice : TestControl
    {
        public string[] Options;
        public Func<int> Get;
        public Action<int> Set;
    }
}
