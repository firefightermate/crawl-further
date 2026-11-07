using System;

namespace CrawlFurther.Testing
{
    /// <summary>
    /// Thrown by a test action that cannot run right now ("Start a run first"). The panel shows the message as it is and
    /// logs nothing; any other exception is shown as a failure and logged with its stack trace.
    /// </summary>
    public sealed class TestModeException : Exception
    {
        /// <summary>Create one with the line the panel shows.</summary>
        public TestModeException(string message) : base(message) { }
    }
}
