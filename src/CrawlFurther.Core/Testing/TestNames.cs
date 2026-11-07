using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Testing
{
    /// <summary>
    /// Names for the panel's lists: the vault's name for a prefab when it has one (vanilla and mod entries alike), else
    /// the prefab name without its "Mod" prefix.
    /// </summary>
    static class TestNames
    {
        static Dictionary<GameObject, string> s_names;
        static int s_count = -1;

        internal static string Of(GameObject prefab)
        {
            if (prefab == null) return "(none)";
            Build();
            string n;
            if (s_names.TryGetValue(prefab, out n) && !string.IsNullOrEmpty(n)) return n;
            return Plain(prefab.name);
        }

        internal static string Plain(string prefabName)
        {
            if (string.IsNullOrEmpty(prefabName)) return "(none)";
            int c = prefabName.IndexOf("(Clone)");
            if (c >= 0) prefabName = prefabName.Substring(0, c).Trim();
            if (prefabName.StartsWith("Mod") && prefabName.Length > 3 && char.IsUpper(prefabName[3])) prefabName = prefabName.Substring(3);
            return prefabName;
        }

        /// <summary>Rebuilt whenever the vault's lists change size (mods add their entries once packs register).</summary>
        static void Build()
        {
            if (!Singleton<SystemLibrary>.HasInstance()) { if (s_names == null) s_names = new Dictionary<GameObject, string>(); return; }
            int count = SystemLibrary.GetMonsters().Count + SystemLibrary.GetItems().Count + SystemLibrary.GetWeapons().Count;
            if (s_names != null && count == s_count) return;
            s_count = count;
            s_names = new Dictionary<GameObject, string>();
            foreach (var e in SystemLibrary.GetMonsters()) Add(e);
            foreach (var e in SystemLibrary.GetItems()) Add(e);
            foreach (var e in SystemLibrary.GetWeapons()) if (string.IsNullOrEmpty(e.m_type)) Add(e);
        }

        static void Add(SystemLibrary.LibraryEntry e)
        {
            if (e == null || e.m_prefab == null || string.IsNullOrEmpty(e.m_name) || s_names.ContainsKey(e.m_prefab)) return;
            s_names[e.m_prefab] = e.m_name;
        }
    }
}
