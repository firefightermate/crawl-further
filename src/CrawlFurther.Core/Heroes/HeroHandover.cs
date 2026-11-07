using System;
using HarmonyLib;

namespace CrawlFurther.Heroes
{
    using CrawlFurther.Util;

    /// <summary>
    /// The crown always passes on. When the hero dies in an ordinary room, SystemLevel.OnPlayerKilled hands the crown to
    /// the player the killing hit credits (DamageSource.m_sourcePlayer); with none, the game gives up: the hero stays
    /// dead, nobody becomes the hero and the dead hero's player never gets a ghost, so the run cannot go on. Our own
    /// sources credit a player (<see cref="ModUtil.MonsterSource"/>); for any hit that still credits nobody (another mod's,
    /// or a case we missed), this credits the player behind the body or effect that made it, as the game credits that
    /// body's own attacks, and logs it once per source so it can be fixed where it starts.
    /// </summary>
    public static class HeroHandover
    {
        static string s_lastLogged;

        /// <summary>The hit to hand to OnPlayerKilled: <paramref name="damage"/> itself, or a copy crediting a player.</summary>
        internal static DamageInfo Credited(Player killed, DamageInfo damage)
        {
            if (killed == null || damage == null || damage.m_source == null || damage.m_source.m_sourcePlayer != null) return damage;
            var pd = killed.GetPlayerData();
            if (pd == null || !pd.IsHero || !GoesToKiller()) return damage;
            var from = damage.m_source;
            var credit = ModUtil.CreditFor(from);
            string what = Name(from.m_source) + " / " + Name(from.m_sourceOwner);
            if (credit == null || credit == pd)
            {
                Log("the hero was killed by " + what + ", which credits no player: the game may not pass the crown on");
                return damage;
            }
            Log("the hero was killed by " + what + " with no player credited: the crown goes to P" + (credit.Id + 1));
            var src = new DamageSource(from.m_source, from.m_sourceOwner, credit, from.m_sourceAttack, from.m_sourceAttackUId,
                                       from.m_damageMod, from.m_attached);
            src.m_sourceOwnerPlayer = from.m_sourceOwnerPlayer;
            return new DamageInfo(damage.m_amount, damage.m_knockbackMultiplier, damage.m_stunTime, damage.m_direction, src)
            {
                m_status = damage.m_status,
                m_victim = damage.m_victim,
                m_animOnContact = damage.m_animOnContact,
                m_animOnContactVictim = damage.m_animOnContactVictim,
                m_isDamageFromStatus = damage.m_isDamageFromStatus,
            };
        }

        /// <summary>The hero's death goes the ordinary way (SystemLevel.OnPlayerKilled: not a challenge, hero battle,
        /// tutorial or boss fight), where the killer takes the crown.</summary>
        static bool GoesToKiller()
        {
            return !SystemMenu.GetChallengeMode() && !SystemLevel.GetHeroBattleActive() && SystemTutorial.GetHumanityRegainedEnabled()
                   && !SystemLevel.GetBossEncounterActive();
        }

        static string Name(UnityEngine.GameObject go) { return go != null ? ModUtil.PrefabName(go) : "nothing"; }

        static void Log(string line)
        {
            if (line == s_lastLogged) return;
            s_lastLogged = line;
            FurtherCore.Log.LogWarning("Hero handover: " + line);
        }
    }

    /// <summary>A hero killed by a hit that credits no player still passes the crown on (see <see cref="HeroHandover"/>).</summary>
    [HarmonyPatch(typeof(SystemLevel), "OnPlayerKilled")]
    static class Patch_HeroHandover
    {
        static void Prefix(Player killed, ref DamageInfo damage)
        {
            try { damage = HeroHandover.Credited(killed, damage); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Hero handover: " + e.Message); }
        }
    }
}
