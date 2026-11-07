using System;
using System.Collections.Generic;

namespace CrawlFurther
{
    using CrawlFurther.Diagnostics;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;

    /// <summary>Waits for Crawl's singletons and monster prefabs, then registers every queued pack exactly once.</summary>
    static class ContentManager
    {
        internal static bool Registered { get; private set; }
        internal static string Status = "waiting for game systems";
        static int s_tries;
        static readonly List<KeyValuePair<string, Action>> s_packs = new List<KeyValuePair<string, Action>>();

        /// <summary>Packs whose register call threw.</summary>
        internal static readonly List<string> FailedPacks = new List<string>();

        internal static void AddPack(string name, Action register)
        {
            s_packs.Add(new KeyValuePair<string, Action>(name, register));
        }

        internal static void Tick()
        {
            if (Registered) return;
            if (!Singleton<SystemDeity>.HasInstance() || !Singleton<Constants>.HasInstance() || !Singleton<SystemUnlocks>.HasInstance())
                return;
            if (SystemDeity.GetDeities() == null) return;
            // scanning loaded objects is expensive: only look twice a second
            if (++s_tries % 30 != 0) return;
            if (!MonsterFactory.TryIndexVanilla())
            {
                if (s_tries % 300 == 0) FurtherCore.Log.LogInfo("Monster prefabs not loaded yet...");
                return;
            }
            Registered = true;
            var packs = s_packs.ToArray();
            int ok = 0;
            var failed = FailedPacks;
            failed.Clear();
            foreach (var kv in packs)
            {
                try { kv.Value(); ok++; FurtherCore.Log.LogInfo("Pack registered: " + kv.Key); }
                catch (Exception e) { failed.Add(kv.Key); FurtherCore.Log.LogError("Pack " + kv.Key + " failed: " + e); }
            }
            try { Strike.KeepAllScales(); } catch (Exception e) { FurtherCore.Log.LogError("KeepAllScales: " + e); }
            try { LibraryEntries.Register(); } catch (Exception e) { FurtherCore.Log.LogError("Library entries: " + e); }
            try { Statues.Register(); } catch (Exception e) { FurtherCore.Log.LogError("Statues: " + e); }
            try { ModInd.Build(); } catch (Exception e) { FurtherCore.Log.LogError("Indicators: " + e); }   // now, not mid-fight
            Status = ok + "/" + packs.Length + " packs, " + MonsterFactory.Built.Count + " monsters" +
                     (failed.Count > 0 ? "  FAILED: " + string.Join(", ", failed.ToArray()) : "");
            FurtherCore.Log.LogInfo(Status);
            GameEvents.RaiseGameReady();
            try { SelfTest.Run(); } catch (Exception e) { FurtherCore.Log.LogError("Self-test crashed: " + e); }
        }
    }
}
