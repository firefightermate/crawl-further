using System;
using HarmonyLib;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// No achievement is granted while a mod monster's vault challenge is played. The game's challenge achievements
    /// already ignore mod monsters: AchievementChallengeMonster names a vanilla prefab, and the challenge counts and
    /// ratios leave mod entries out (see LibraryEntries). This keeps every other achievement out of a mod monster's
    /// challenge too. Skipping AchievementBase.Unlock leaves the achievement as it was and unsaved, as if its check
    /// had not passed.
    /// </summary>
    [HarmonyPatch(typeof(AchievementBase), "Unlock")]
    static class Patch_ChallengeNoAchievements
    {
        static bool Prefix()
        {
            try { return !Challenges.ModChallengeRunning; }
            catch (Exception) { return true; }
        }
    }
}
