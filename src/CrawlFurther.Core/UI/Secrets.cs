using System;
using System.Collections.Generic;
using System.IO;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Art;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;

    /// <summary>
    /// The secrets framework: registration, the found state (kept in BepInEx/config/CrawlFurther.Secrets.cfg, one found id
    /// per line) and the groups the vault lists them by. A newly found secret is announced with the unlock banner on the
    /// next menu and gets the vault's red "new" dot. The debug setting UnlockAll (CrawlMod.Debug.cfg) shows every secret
    /// as found and leaves the file alone. The vault shows the pages in a category registered with
    /// <see cref="VaultCategory.secrets"/> set.
    /// </summary>
    public static class Secrets
    {
        public static readonly List<SecretDef> All = new List<SecretDef>();

        /// <summary>Add a secret, or replace the one with the same id.</summary>
        public static void Add(SecretDef e)
        {
            if (e == null || string.IsNullOrEmpty(e.id)) return;
            for (int i = 0; i < All.Count; i++) if (All[i].id == e.id) { All[i] = e; return; }
            All.Add(e);
        }

        /// <summary>Mark a secret as found (saved at once). Call it from your own game hooks.</summary>
        public static Action<string> Found = MarkFound;
        /// <summary>Has this secret been found (or shown by the debug UnlockAll)?</summary>
        public static Func<string, bool> IsFound = CheckFound;

        public const string FILE = "CrawlFurther.Secrets.cfg";

        class Group { public string name, hiddenTitle; public SlotTier banner; }
        static readonly List<Group> s_groups = new List<Group>();

        /// <summary>
        /// Add a group: the vault lists groups in the order they were added (unknown groups follow, in the order their
        /// first secret was added). <paramref name="hiddenTitle"/> is the page title until a secret is found ("A gold
        /// secret"); <paramref name="banner"/> colours the banner that announces a find.
        /// </summary>
        public static void AddGroup(string name, string hiddenTitle, SlotTier banner = SlotTier.Gold)
        {
            if (string.IsNullOrEmpty(name)) return;
            s_groups.RemoveAll(g => g.name == name);
            s_groups.Add(new Group { name = name, hiddenTitle = hiddenTitle, banner = banner });
        }

        static Group GroupOf(string name)
        {
            foreach (var g in s_groups) if (g.name == name) return g;
            return null;
        }

        /// <summary>The page title of a secret of this group that is still hidden (the vault shows it in capitals).</summary>
        public static string HiddenTitle(string group)
        {
            var g = GroupOf(group);
            return g != null && !string.IsNullOrEmpty(g.hiddenTitle) ? g.hiddenTitle : "A secret";
        }

        static readonly HashSet<string> s_found = new HashSet<string>();
        static bool s_loaded;
        /// <summary>Called by the vault when a secret is found during play (marks its page new).</summary>
        internal static Action<string> OnFound;

        static string PathOf { get { return System.IO.Path.Combine(BepInEx.Paths.ConfigPath, FILE); } }

        static void Load()
        {
            if (s_loaded) return;
            s_loaded = true;
            try
            {
                if (!File.Exists(PathOf)) return;
                foreach (var raw in File.ReadAllLines(PathOf))
                {
                    var l = raw.Trim();
                    if (l.Length == 0 || l.StartsWith("#")) continue;
                    s_found.Add(l);
                }
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Secrets: could not read " + FILE + ": " + e.Message); }
        }

        static void Save()
        {
            try
            {
                var lines = new List<string> { "# Secrets you have found (one id per line). Delete a line to hide that secret again." };
                var ids = new List<string>(s_found); ids.Sort(StringComparer.Ordinal);
                lines.AddRange(ids);
                File.WriteAllLines(PathOf, lines.ToArray());
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Secrets: could not write " + FILE + ": " + e.Message); }
        }

        static void MarkFound(string id)
        {
            // test mode can become or spawn any secret: finding one there is not finding it
            if (string.IsNullOrEmpty(id) || Testing.TestMode.Active) return;
            Load();
            if (!s_found.Add(id)) return;
            Save();
            var e = Find(id);
            FurtherCore.Log.LogInfo("Secret found: " + id + (e != null ? " (" + e.name + ")" : " (not registered)"));
            if (e != null)
            {
                try
                {
                    var g = GroupOf(e.group);
                    Unlocks.Announce.Enqueue(new UnlockDef
                    {
                        id = "Secret" + id, title = "SECRET", slot = "VAULT SECRET", tier = g != null ? g.banner : SlotTier.Gold,
                        text = e.name,
                    });
                }
                catch { }
            }
            if (OnFound != null) { try { OnFound(id); } catch (Exception ex) { FurtherCore.Log.LogWarning("Secrets: " + ex.Message); } }
        }

        static bool CheckFound(string id)
        {
            if (string.IsNullOrEmpty(id)) return false;
            if (Unlocks.UnlockAll || Unlocks.OpenForTest) return true;
            Load();
            return s_found.Contains(id);
        }

        /// <summary>Found for real (the debug reveal not counted).</summary>
        public static bool FoundForReal(string id) { Load(); return !string.IsNullOrEmpty(id) && s_found.Contains(id); }

        public static SecretDef Find(string id)
        {
            foreach (var e in All) if (e.id == id) return e;
            return null;
        }

        /// <summary>All secrets in vault order: group by group (see <see cref="AddGroup"/>), registration order inside a group.</summary>
        public static List<SecretDef> Ordered()
        {
            var groups = new List<string>();
            foreach (var g in s_groups) groups.Add(g.name);
            foreach (var e in All) if (!groups.Contains(e.group ?? "")) groups.Add(e.group ?? "");
            var list = new List<SecretDef>();
            foreach (var g in groups) foreach (var e in All) if ((e.group ?? "") == g) list.Add(e);
            return list;
        }

        /// <summary>A monster secret for a built mod monster (prefab name "ModX" or MonsterDef id "X"): its vault name,
        /// line and picture, found when a human player becomes it.</summary>
        public static void AddMonster(string prefabId, string group, string riddle, string rarity)
        {
            string key = prefabId.StartsWith("Mod", StringComparison.Ordinal) ? prefabId.Substring(3) : prefabId;
            Player p;
            if (!MonsterFactory.Built.TryGetValue(key, out p) || p == null) { FurtherCore.Log.LogWarning("Secrets: " + prefabId + " is not built"); return; }
            string name, text;
            LibraryEntries.MonsterInfo(key, out name, out text);
            string sheet = null;
            var spr = p.GetComponent<exSprite>();
            var sh = spr != null ? SpriteSheets.ByAtlas(spr.atlas) : null;
            if (sh != null) sheet = sh.id;
            Add(new SecretDef { id = prefabId, name = name, riddle = riddle, rarity = rarity, text = text, iconSheet = sheet, group = group, monster = true });
        }

        /// <summary>Longest texts that still fit the vault page (about 5 lines of 25 characters under the name).</summary>
        public const int MaxRiddle = 75, MaxRarity = 30, MaxText = 120;

        /// <summary>Self-test: every secret is complete and plain, ids are unique, pictures exist.</summary>
        public static void SelfCheck(Action<string> bad)
        {
            var ids = new HashSet<string>();
            foreach (var e in All)
            {
                string l = "secret " + e.id;
                if (!ids.Add(e.id)) bad(l + ": id used twice");
                if (string.IsNullOrEmpty(e.name)) bad(l + ": no name");
                if (string.IsNullOrEmpty(e.riddle)) bad(l + ": no riddle");
                if (string.IsNullOrEmpty(e.rarity)) bad(l + ": no rarity");
                if (string.IsNullOrEmpty(e.text)) bad(l + ": no text");
                if (string.IsNullOrEmpty(e.group)) bad(l + ": no group");
                foreach (var t in new[] { e.name, e.riddle, e.rarity, e.text })
                    if (t != null && (t.IndexOfAny(new[] { '%', '{', '}', '|', '~', '[', ']' }) >= 0 || t.Contains("(MOD)"))) bad(l + ": text has a character GUIText eats: " + t);
                if (string.IsNullOrEmpty(e.iconSheet) || SpriteSheets.Get(e.iconSheet) == null) bad(l + ": picture " + (e.iconSheet ?? "null") + " missing");
                else if (LibraryEntries.PictureAnim(SpriteSheets.Get(e.iconSheet)) == null) bad(l + ": picture " + e.iconSheet + " has no Portrait, Vault or Idle anim");
                if (e.riddle != null && e.riddle.Length > MaxRiddle) bad(l + ": riddle is " + e.riddle.Length + " characters (keep it to " + MaxRiddle + " so the page fits)");
                if (e.rarity != null && e.rarity.Length > MaxRarity) bad(l + ": rarity is " + e.rarity.Length + " characters (keep it to " + MaxRarity + ")");
                if (e.text != null && e.text.Length > MaxText) bad(l + ": text is " + e.text.Length + " characters (keep it to " + MaxText + ")");
            }
        }
    }

    /// <summary>A human player becomes (or evolves into, or starts as) a monster: the vanilla library's "found" call finds
    /// monster secrets. Bots and inactive players are skipped.</summary>
    [HarmonyPatch(typeof(SystemLibrary), "OnEntryFound", new[] { typeof(PlayerData), typeof(GameObject), typeof(string) })]
    static class Patch_SecretMonsterFound
    {
        static void Postfix(PlayerData player, GameObject obj)
        {
            if (obj == null || player == null || !player.IsActive || player.IsBot) return;
            try
            {
                string n = obj.name;
                if (n.EndsWith("(Clone)")) n = n.Substring(0, n.Length - 7);
                var se = Secrets.Find(n);
                if (se != null && se.monster) Secrets.Found(n);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Secret found hook: " + e.Message); }
        }
    }
}
