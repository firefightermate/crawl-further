using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Util;

    /// <summary>
    /// The vault challenge's extra strength for mod monsters (<see cref="TierRules.Challenge"/>, per monster in
    /// <see cref="MonsterFactory.ChallengeStrength"/>). Inside a challenge only, the monster's max health and its hits on
    /// the hero each get the square root of its boost. Outside a challenge nothing changes.
    /// </summary>
    public static class ChallengeBoost
    {
        /// <summary>A vault challenge is being played.</summary>
        public static bool Active
        {
            get { try { return SystemMenu.GetChallengeMode(); } catch { return false; } }
        }

        static readonly Dictionary<int, float> s_boostedMax = new Dictionary<int, float>();

        internal static void OnSpawned(GameObject monster)
        {
            if (monster == null || !Active) return;
            float boost;
            if (!MonsterFactory.ChallengeStrength.TryGetValue(ModUtil.PrefabName(monster), out boost)) return;
            var h = monster.GetComponent<Health>();
            if (h == null) return;
            float max = R.Get<float>(h, "m_healthMaxFinal");
            float done;
            if (max <= 0f || (s_boostedMax.TryGetValue(monster.GetInstanceID(), out done) && Mathf.Approximately(done, max))) return;
            float boosted = Mathf.Round(max * Mathf.Sqrt(boost) * 2f) / 2f;
            float ratio = R.Get<float>(h, "m_healthCurrent") / max;
            R.Set(h, "m_healthMaxFinal", boosted);
            R.Set(h, "m_healthCurrent", Mathf.Max(0.5f, boosted * ratio));
            s_boostedMax[monster.GetInstanceID()] = boosted;
            FurtherCore.Log.LogInfo("Challenge: " + monster.name + " health " + max + " -> " + boosted + ", hits x" + Mathf.Sqrt(boost).ToString("0.00"));
        }
    }

    [HarmonyPatch(typeof(SystemLevel), "OnMonsterSpawned")]
    static class Patch_ChallengeBoostSpawn
    {
        static void Postfix(GameObject monster) { ChallengeBoost.OnSpawned(monster); }
    }
}
