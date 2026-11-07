using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Testing
{
    /// <summary>
    /// A picker on the test panel: a column of entries with a search box when it is long. Made by
    /// <see cref="TestMode.AddList"/>. <see cref="Selected"/> is the last entry picked, so one list can depend on another
    /// (the Become page's monster list shows the tree of the god picked in the list beside it).
    /// </summary>
    public sealed class TestList
    {
        /// <summary>Lists longer than this get a search box.</summary>
        internal const int SearchFrom = 12;
        const float RefreshSeconds = 2f;

        readonly Func<IEnumerable<TestItem>> m_source;
        readonly Action<TestItem> m_pick;
        List<TestItem> m_items = new List<TestItem>();
        float m_builtAt = -100f;

        internal string Filter = "";
        internal Vector2 Scroll;

        /// <summary>The list's heading.</summary>
        public string Name { get; private set; }

        /// <summary>The entry picked last, or null.</summary>
        public TestItem Selected { get; private set; }

        /// <summary>The value of the entry picked last, or null.</summary>
        public object SelectedValue { get { return Selected != null ? Selected.Value : null; } }

        internal TestList(string name, Func<IEnumerable<TestItem>> source, Action<TestItem> pick)
        {
            Name = name;
            m_source = source;
            m_pick = pick;
        }

        /// <summary>Rebuild the entries the next time the panel draws them (lists also rebuild every two seconds).</summary>
        public void Refresh() { m_builtAt = -100f; }

        /// <summary>The entries, rebuilt from the source now and then; a source that throws gives an empty list.
        /// Rebuilt only on IMGUI's layout event, so layout and repaint of one frame see the same entries.</summary>
        internal List<TestItem> Items
        {
            get
            {
                if (Time.unscaledTime - m_builtAt < RefreshSeconds) return m_items;
                if (Event.current != null && Event.current.type != EventType.Layout) return m_items;
                m_builtAt = Time.unscaledTime;
                var list = new List<TestItem>();
                try
                {
                    var src = m_source != null ? m_source() : null;
                    if (src != null) foreach (var it in src) if (it != null) list.Add(it);
                }
                catch (Exception e) { FurtherCore.Log.LogWarning("Test list " + Name + ": " + e.Message); }
                m_items = list;
                if (Selected != null && !m_items.Exists(i => Same(i, Selected))) Selected = null;
                return m_items;
            }
        }

        /// <summary>A row of a drawn list: a group heading (Item null) or an entry.</summary>
        internal struct Row
        {
            public string Label;
            public TestItem Item;
        }

        List<Row> m_rows;
        List<TestItem> m_rowsFrom;
        string m_rowsFilter;

        /// <summary>The entries that match <paramref name="filter"/>, with a heading row before each group. Cached until
        /// the entries or the filter change.</summary>
        internal List<Row> Rows(string filter)
        {
            var items = Items;
            if (m_rows != null && ReferenceEquals(m_rowsFrom, items) && m_rowsFilter == filter) return m_rows;
            var rows = new List<Row>();
            string group = null;
            foreach (var it in items)
            {
                if (filter.Length > 0 && it.Label.IndexOf(filter, StringComparison.OrdinalIgnoreCase) < 0) continue;
                if (it.Group != group)
                {
                    group = it.Group;
                    if (group != null) rows.Add(new Row { Label = group });
                }
                rows.Add(new Row { Label = it.Label, Item = it });
            }
            m_rows = rows;
            m_rowsFrom = items;
            m_rowsFilter = filter;
            return rows;
        }

        internal bool IsSelected(TestItem item) { return Selected != null && Same(item, Selected); }

        internal void Pick(TestItem item)
        {
            Selected = item;
            if (m_pick != null) TestMode.Run(item.Label, () => m_pick(item));
            TestMode.RefreshLists();
        }

        static bool Same(TestItem a, TestItem b)
        {
            return a.Label == b.Label && a.Group == b.Group && Equals(a.Value, b.Value);
        }
    }
}
