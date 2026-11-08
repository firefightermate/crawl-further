using System;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Ghosts;
    using CrawlFurther.Util;

    /// <summary>
    /// A ghost blob's special is on the ghost button (keys C / B / M / full stop, middle click, pad X, or what the player
    /// set; an Online Crawl player's own ghost button), not on Back. In the game Back does two things in a blob body:
    /// pressed, Player.HandleAlternateInput starts the special; released, PropFodder.Update lets the player out
    /// (PlayerData.GetInputUpBack). A blob with a special (the Brute, Titan and King) so threw its player out every time
    /// it was used. In a mod blob Back now only lets the player out, and the ghost button starts the special the way the
    /// game would (ready, not mid-attack, nothing stopping attacks). A blob left to its AI uses its special through
    /// AiSpecial, as before. On every mod blob prefab.
    /// </summary>
    public class BlobSpecialInput : MonoBehaviour
    {
        Player m_player;
        Health m_health;

        static readonly System.Reflection.MethodInfo s_queue = AccessTools.Method(typeof(Player), "QueueState");

        void Awake()
        {
            m_player = GetComponent<Player>();
            m_health = GetComponent<Health>();
        }

        /// <summary>A player (not the AI) is in this blob.</summary>
        public bool PlayerInside
        {
            get
            {
                if (m_player == null || m_player.GetIsAI() || ModUtil.IsGhost(m_player)) return false;
                var pd = m_player.GetPlayerData();
                return pd != null && pd.IsHuman && !pd.IsHero;
            }
        }

        /// <summary>The blob has a special of its own (the Mote, Spitter and Gel have none).</summary>
        public bool HasSpecial { get { return m_player != null && m_player.HasSpecialAttack(); } }

        void Update()
        {
            if (!PlayerInside || !HasSpecial || m_health == null || !m_health.IsAlive() || SystemTime.Paused) return;
            if (!GhostControls.Down(m_player.GetPlayerData())) return;
            try { Fire(m_player); }
            catch (Exception e) { Plugin.Log.LogError("Blob special failed: " + e); }
        }

        /// <summary>Start the special as Player.HandleAlternateInput does for Back: only when ready and free to attack.</summary>
        public static bool Fire(Player p)
        {
            if (p == null || s_queue == null || !p.HasSpecialAttack() || !p.GetSpecialReady()) return false;
            var atk = p.GetAttackComponent();
            if (atk == null || !atk.CanAttack(true)) return false;
            var sm = p.GetStatusManager();
            if (sm != null && sm.GetPreventAttack()) return false;
            var dont = R.Get<TimedList<string>>(p, "m_dontAttackList");
            if (dont != null && !dont.Empty()) return false;
            var state = R.Get<Player.ePlayerState>(p, "m_state");
            if (state != Player.ePlayerState.Idle && state != Player.ePlayerState.Run && state != Player.ePlayerState.Attack) return false;
            R.Set(p, "m_specialCharge", 0f);
            var pd = p.GetPlayerData();
            if (pd != null && pd.GameData != null) pd.GameData.MessagePowerups("OnSpecial");
            s_queue.Invoke(p, new object[] { Player.ePlayerState.AttackSpecial });
            return true;
        }

        /// <summary>The player is in a mod blob whose special the ghost button starts (so it is not the gold ghost's
        /// jump-out or a pause click there).</summary>
        public static bool SpecialOnGhostButton(Player body)
        {
            var b = body != null ? body.GetComponent<BlobSpecialInput>() : null;
            return b != null && b.PlayerInside && b.HasSpecial;
        }
    }

    /// <summary>Back in a mod blob only lets the player out: it never starts the special (BlobSpecialInput).</summary>
    [HarmonyPatch(typeof(Player), "HandleAlternateInput")]
    static class Patch_BlobBackNoSpecial
    {
        static bool Prefix(Player __instance, ref bool __result)
        {
            try
            {
                var b = __instance.GetComponent<BlobSpecialInput>();
                if (b == null || !b.PlayerInside) return true;
                __result = false;
                return false;
            }
            catch { return true; }
        }
    }
}
