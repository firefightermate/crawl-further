using System;
using System.Collections;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Game
{
    using CrawlFurther.Compat;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>
    /// Keep playing at the end of a game, won or lost. When the hero kills the boss, or the last try at the boss fails,
    /// the game's own prompt (the one Pause > Quit uses) offers three choices:
    ///  - Continue: <see cref="ExtraBossAttempts"/> more tries at the boss, and the run goes on as it was. After a win the
    ///    winner goes back through the portal to the dungeon, the way a failed try does.
    ///  - Continue in chaos: the same, and the rest of the game is a chaos game (<see cref="ChaosMode"/>). Only offered when
    ///    chaos is on and the game is not a chaos game already.
    ///  - End run: the game ends the game's own way. A game that someone won and then continued ends as a win for the
    ///    last player who beat the boss, not as the boss's escape.
    ///
    /// How the game ends a run (decompiled): BossEncounter.OnBossKilled plays the win (other players' bodies hidden, the
    /// hero in a cutscene, the win music) and then calls BossEncounter.SaveAndQuit(true), which records the game and loads
    /// the win scene. A hero killed on the last allowed try ends with SaveAndQuit(false) and the boss's escape scene.
    /// SystemMenu.GetBossAttemptsAllowed (3 in the game) against SystemPlayers.GetTotalBossAttempts decides the last try.
    ///
    /// Nothing changes in the tutorial, a vault challenge, attract mode or a game with no human player. In an Online Crawl
    /// game the host's prompt is mirrored to every client like the rest of its screen, and any player can answer it. Mods can react with <see cref="GameEvents.GameContinued"/>.
    /// </summary>
    public static class ContinueGame
    {
        /// <summary>Offer to keep playing at the end of a game. Set false to end every game the game's own way.</summary>
        public static bool Enabled = true;
        /// <summary>How many tries at the boss each continue adds.</summary>
        public static int ExtraBossAttempts = 2;

        /// <summary>How many times the game being played has been continued (0 before the first win).</summary>
        public static int Continues { get; private set; }
        /// <summary>The last player who beat the boss in this game, or null.</summary>
        public static PlayerData LastWinner { get; private set; }

        internal const string Title = "_Keep playing?_";
        internal const string WonText = "{0} beat the boss. Play on with two more tries at the boss, or end the run here.";
        internal const string OutText = "No one has beaten the boss again. Play on with two more tries at the boss, or end the run here. {0} keeps the win.";
        internal const string LostText = "The boss got away. Play on with two more tries at the boss, or end the run here.";
        internal const string ChaosText = " Chaos turns the rest of the game into a chaos game.";
        internal const string ContinueLabel = "Continue";
        internal const string ChaosLabel = "Continue in chaos";
        internal const string EndLabel = "End run";

        static readonly HashSet<int> s_winsCounted = new HashSet<int>();
        internal static bool PassThrough;
        static Player s_lastDeadHero;
        static DamageInfo s_lastDeadHeroHit;

        internal static void Reset()
        {
            Continues = 0;
            LastWinner = null;
            s_winsCounted.Clear();
            s_lastDeadHero = null;
            s_lastDeadHeroHit = null;
        }

        /// <summary>The player's win in this game has been counted for <see cref="Unlocks.StatWins"/>. Each player counts
        /// once per game, however many times the game is continued and won.</summary>
        internal static bool WinCounted(PlayerData pd) { return pd != null && !s_winsCounted.Add(pd.Id); }

        /// <summary>The game's end can be offered here.</summary>
        static bool Offered()
        {
            if (!Enabled) return false;
            try
            {
                // Online Crawl: only the host runs the game and every client sees its screen, so the prompt shows for
                // all players and any of them can answer it (a remote player's pad is a pad on the host)
                if (CompatOnline.IsClient) return false;
                if (SystemGame.GetIsTutorialMatch() || SystemTutorial.GetActive()) return false;
                if (SystemMenu.GetChallengeMode() || SystemMenu.GetAttractMode()) return false;
                for (int i = 0; i < SystemPlayers.GetMaxPlayers(); i++)
                {
                    var pd = SystemPlayers.GetPlayer(i);
                    if (pd != null && pd.IsActive && pd.IsHuman) return true;
                }
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("ContinueGame: " + e.Message); }
            return false;
        }

        /// <summary>SaveAndQuit was called. True: the prompt is up and the game must not end yet.</summary>
        internal static bool Intercept(BossEncounter enc, bool won)
        {
            if (!Offered()) return false;
            if (won)
            {
                var winner = SystemLevel.GetHeroPlayerData();
                if (winner == null) return false;
                LastWinner = winner;
                Ask(string.Format(WonText, Name(winner)), c => ContinueAfterWin(enc, winner, c), () => End(enc, true));
                return true;
            }
            // out of tries, won before or not: the hero who died on the last try comes back if the game goes on
            if (s_lastDeadHero == null) return false;
            if (LastWinner != null && LastWinner.IsActive)
                Ask(string.Format(OutText, Name(LastWinner)), c => ContinueAfterLoss(enc, c), () => EndAsLastWin(enc));
            else
                Ask(LostText, c => ContinueAfterLoss(enc, c), () => End(enc, false));
            return true;
        }

        /// <summary>The hero died on the last try (BossEncounter.CoroutineHeroKilledFinalSequence): kept so a continue can
        /// bring him back through the portal as a failed try would.</summary>
        internal static void OnFinalHeroDeath(Player hero, DamageInfo hit) { s_lastDeadHero = hero; s_lastDeadHeroHit = hit; }

        static string Name(PlayerData pd)
        {
            try { return string.IsNullOrEmpty(pd.Name) ? "The hero" : pd.Name; } catch { return "The hero"; }
        }

        /// <summary>The prompt: Continue, Continue in chaos (when chaos is on and this is not a chaos game yet), End run.
        /// The game's prompt holds two choices; the third is added to its menu (<see cref="PromptExtraChoice"/>). If that
        /// fails, the prompt is shown with the two plain choices instead.</summary>
        static void Ask(string text, Action<bool> onContinue, Action onEnd)
        {
            var menu = Singleton<SystemMenu>.Get;
            if (ChaosOffered())
            {
                GameObject go = null;
                try
                {
                    go = menu.ShowPrompt(Title, text + ChaosText, ContinueLabel, () => Safe(() => onContinue(false)),
                                         ChaosLabel, () => Safe(() => onContinue(true)), -1, null);
                    if (PromptExtraChoice.Add(go, EndLabel, () => Safe(onEnd))) return;
                }
                catch (Exception e) { FurtherCore.Log.LogWarning("ContinueGame: no chaos choice: " + e.Message); }
                if (go != null) menu.HideModalPopup(go);
            }
            menu.ShowPrompt(Title, text, ContinueLabel, () => Safe(() => onContinue(false)), EndLabel, () => Safe(onEnd), -1, null);
        }

        static bool ChaosOffered()
        {
            try { return ChaosMode.Enabled && !ChaosMode.Active; } catch { return false; }
        }

        static void Safe(Action a)
        {
            try { a(); }
            catch (Exception e) { FurtherCore.Log.LogError("ContinueGame: " + e); }
        }

        static void AddTries(bool chaos)
        {
            Continues++;
            if (chaos) ChaosMode.OnContinue();
            SystemMenu.SetBossAttemptsAllowed(SystemMenu.GetBossAttemptsAllowed() + ExtraBossAttempts);
            FurtherCore.Log.LogInfo("Game continued (" + Continues + "): " + SystemPlayers.GetTotalBossAttempts() + " of "
                                    + SystemMenu.GetBossAttemptsAllowed() + " boss tries used");
        }

        static void End(BossEncounter enc, bool won)
        {
            PassThrough = true;
            try { AccessTools.Method(typeof(BossEncounter), "SaveAndQuit").Invoke(enc, new object[] { won }); }
            finally { PassThrough = false; }
        }

        /// <summary>The game members the continue relies on are where it expects them.</summary>
        internal static void SelfCheck(Action<string> bad, Action<string> note)
        {
            foreach (var f in new[] { "m_heroKilled", "m_encounterActive", "m_portal", "m_teleportPosition", "m_teleportRoom",
                                      "m_playerExitPortalOffset", "m_playerEnterPortalAnim", "m_playerExitPortalAnim",
                                      "m_destroyOnEncounterEnd", "m_playerDeathAnims" })
                if (AccessTools.Field(typeof(BossEncounter), f) == null) bad("BossEncounter." + f + " not found");
            foreach (var m in new[] { "SaveAndQuit", "CoroutineHeroKilledSequence", "CoroutineHeroKilledFinalSequence" })
                if (AccessTools.Method(typeof(BossEncounter), m) == null) bad("BossEncounter." + m + " not found");
            if (AccessTools.Field(typeof(SystemLevel), "m_heroPlayerData") == null) bad("SystemLevel.m_heroPlayerData not found");
            if (AccessTools.Field(typeof(PlayerData), "m_isHero") == null) bad("PlayerData.m_isHero not found");
            if (AccessTools.Field(typeof(MenuPrompt), "m_menu") == null) bad("MenuPrompt.m_menu not found");
            if (AccessTools.Field(typeof(MenuPrompt), "m_background") == null) bad("MenuPrompt.m_background not found");
            if (AccessTools.Field(typeof(MenuTextMenu), "m_itemSpacing") == null) bad("MenuTextMenu.m_itemSpacing not found");
            if (AccessTools.Field(typeof(MenuTextMenu), "m_owner") == null) bad("MenuTextMenu.m_owner not found");
            note(Enabled ? "on: a won or lost game offers to continue with " + ExtraBossAttempts + " more boss tries"
                           + (ChaosMode.Enabled ? ", as it was or in chaos" : "") : "off");
        }

        // ---- continue after a win ----

        static void ContinueAfterWin(BossEncounter enc, PlayerData winner, bool chaos)
        {
            if (winner.IsHuman && !UnlockHooks.Excluded() && !WinCounted(winner)) { Unlocks.Count(Unlocks.StatWins); Unlocks.Save(); }
            AddTries(chaos);
            R.Set(enc, "m_heroKilled", true);      // this floor's try is spent, as after a failed one
            Singleton<SystemLevel>.Get.StartCoroutine(BackThroughPortal(enc, winner));
        }

        /// <summary>The failed try's way home (BossEncounter.CoroutineHeroKilledSequence) for a hero who is still alive:
        /// he steps into the portal, comes out beside the portal on the floor, and the floor's music comes back.</summary>
        static IEnumerator BackThroughPortal(BossEncounter enc, PlayerData heroPd)
        {
            yield return null;
            var heroGo = heroPd.GameObject;
            Singleton<SystemPlayers>.Get.OnEncounterEnded();
            var gui = SystemLevel.GetGUI();
            gui.Hide("Boss", false);
            // the win hid the other players' bodies; the failed try's way: remove them and let the game bring the ghosts back
            for (int i = 0; i < SystemPlayers.GetMaxPlayers(); i++)
            {
                var pd = SystemPlayers.GetPlayer(i);
                if (pd == null || pd == heroPd || pd.IsAlive || pd.GameObject == null) continue;
                pd.GameObject.Despawn();
            }
            Singleton<SystemPlayers>.Get.UnassignBossOnlyBots();
            if (heroGo == null) { Finish(enc); yield break; }

            var health = heroGo.GetComponent<Health>();
            if (health != null) health.StopInvincibility("bossdead");
            var anim = heroGo.GetComponent<exSpriteAnimation>();
            var enter = R.Get<exSpriteAnimClip>(enc, "m_playerEnterPortalAnim");
            var exit = R.Get<exSpriteAnimClip>(enc, "m_playerExitPortalAnim");
            heroGo.SendMessage("MsgEnterPortal", SendMessageOptions.DontRequireReceiver);
            SystemAudio.StopMusic(3f);
            yield return PlayAndWait(anim, enter);

            var portal = R.Get<GameObject>(enc, "m_portal");
            Vector3 pos = (Vector2)R.Get<Vector2>(enc, "m_teleportPosition");
            if (portal != null)
            {
                Vector3 off = (Vector2)R.Get<Vector2>(enc, "m_playerExitPortalOffset");
                if (heroGo.transform.localScale.x < 0f) off.x = -off.x;
                pos = portal.transform.position + off;
            }
            var rend = heroGo.GetComponent<Renderer>();
            if (rend != null) rend.enabled = false;
            heroGo.transform.position = pos;
            gui.Show("BossPermanant");
            Singleton<SystemLevel>.Get.OnTeleportToRoom(R.Get<Room>(enc, "m_teleportRoom"));
            if (portal != null) portal.SendMessage(AnimStateMachine.STR_MSGSETSTATE, "TeleportBack", SendMessageOptions.DontRequireReceiver);
            var toDestroy = R.Get<List<GameObject>>(enc, "m_destroyOnEncounterEnd");
            if (toDestroy != null)
                foreach (var go in toDestroy.ToArray())
                    if (go != null) go.Despawn();
            yield return null;
            yield return new WaitForSeconds(0.25f);

            if (rend != null) rend.enabled = true;
            yield return PlayAndWait(anim, exit);
            heroGo.SendMessage("MsgExitPortal", SendMessageOptions.DontRequireReceiver);
            heroGo.SendMessage("MsgShowHealth", true, SendMessageOptions.DontRequireReceiver);
            gui.Show("Boss");
            gui.HideHeroStats();
            if (portal != null) portal.SendMessage("MsgSetState", "Disabled", SendMessageOptions.DontRequireReceiver);
            Finish(enc);
        }

        static IEnumerator PlayAndWait(exSpriteAnimation anim, exSpriteAnimClip clip)
        {
            if (anim == null || clip == null) yield break;
            anim.AddAnimation(clip);
            anim.Play(clip.name);
            yield return null;
            float t = 0f;
            while (anim != null && anim.IsPlaying(clip.name) && t < 3f) { t += Time.deltaTime; yield return null; }
        }

        static void Finish(BossEncounter enc)
        {
            SystemMain.PlayMusic(Singleton<Constants>.Get.m_musicLevel10, 0.2f);
            R.Set(enc, "m_encounterActive", false);
            GameEvents.RaiseGameContinued(Continues);
        }

        // ---- out of tries after a continue ----

        /// <summary>The game's failed-try sequence brings the hero back; its death pose already played in the last try's
        /// own sequence, so it is skipped this time.</summary>
        static void ContinueAfterLoss(BossEncounter enc, bool chaos)
        {
            AddTries(chaos);
            Singleton<SystemLevel>.Get.StartCoroutine(FailedTryWayHome(enc, s_lastDeadHero, s_lastDeadHeroHit));
            s_lastDeadHero = null;
            s_lastDeadHeroHit = null;
        }

        static IEnumerator FailedTryWayHome(BossEncounter enc, Player hero, DamageInfo hit)
        {
            var deathAnims = R.Get<exSpriteAnimClip[]>(enc, "m_playerDeathAnims");
            R.Set(enc, "m_playerDeathAnims", new exSpriteAnimClip[0]);
            var seq = (IEnumerator)AccessTools.Method(typeof(BossEncounter), "CoroutineHeroKilledSequence").Invoke(enc, new object[] { hero, hit });
            Singleton<SystemLevel>.Get.StartCoroutine(seq);
            yield return null;
            yield return null;
            R.Set(enc, "m_playerDeathAnims", deathAnims);
            while (SystemLevel.GetBossEncounterActive()) yield return null;
            GameEvents.RaiseGameContinued(Continues);
        }

        /// <summary>End a continued game that ran out of tries as the last winner's win: he is made the hero again so the
        /// game records and shows his win.</summary>
        static void EndAsLastWin(BossEncounter enc)
        {
            var winner = LastWinner;
            try
            {
                var lvl = Singleton<SystemLevel>.Get;
                for (int i = 0; i < SystemPlayers.GetMaxPlayers(); i++)
                {
                    var pd = SystemPlayers.GetPlayer(i);
                    if (pd != null) R.Set(pd, "m_isHero", pd == winner);
                }
                R.Set(lvl, "m_heroPlayerData", winner);
            }
            catch (Exception e)
            {
                FurtherCore.Log.LogError("ContinueGame: could not hand the win back, the game ends the game's own way: " + e.Message);
                End(enc, false);
                return;
            }
            End(enc, true);
        }
    }

    /// <summary>
    /// A third choice on one of the game's prompts (MenuPrompt holds two). Its menu sends each item's message to the
    /// menu's owner, so this sits on that object and answers the extra item's message, then closes the prompt the way
    /// the prompt's own choices do.
    /// </summary>
    public class PromptExtraChoice : MonoBehaviour
    {
        const string Message = "MsgCrawlModPromptExtra";
        Action m_action;
        GameObject m_popup;

        /// <summary>Add a choice at the bottom of the prompt <paramref name="popup"/>. False if it could not be added.</summary>
        public static bool Add(GameObject popup, string label, Action action)
        {
            if (popup == null) return false;
            var prompt = popup.GetComponent<MenuPrompt>();
            var menu = prompt != null ? R.Get<MenuTextMenu>(prompt, "m_menu") : null;
            var owner = menu != null ? R.Get<GameObject>(menu, "m_owner") : null;
            if (owner == null) return false;
            var c = owner.AddComponent<PromptExtraChoice>();
            c.m_action = action;
            c.m_popup = popup;
            var item = menu.AddItem(new MenuTextMenuItemData { m_text = label, m_message = Message, m_enabled = true });
            if (item == null) { Destroy(c); return false; }
            // the prompt sized its backing to its text and two choices: grow it by half a row, as it does per row
            var bg = R.Get<GameObject>(prompt, "m_background");
            if (bg != null)
            {
                var sc = bg.transform.localScale;
                bg.transform.localScale = new Vector3(sc.x, sc.y + 0.5f * R.Get<float>(menu, "m_itemSpacing"), sc.z);
            }
            return true;
        }

        void MsgCrawlModPromptExtra()
        {
            var a = m_action;
            m_action = null;
            try { if (a != null) a(); }
            finally { Singleton<SystemMenu>.Get.HideModalPopup(m_popup != null ? m_popup : gameObject); }
        }
    }

    [HarmonyPatch(typeof(BossEncounter), "SaveAndQuit")]
    static class Patch_ContinueGameEnd
    {
        static bool Prefix(BossEncounter __instance, bool won, ref Coroutine __result, bool __runOriginal)
        {
            if (!__runOriginal || ContinueGame.PassThrough) return __runOriginal;
            try
            {
                if (!ContinueGame.Intercept(__instance, won)) return true;
                __result = null;
                return false;
            }
            catch (Exception e)
            {
                FurtherCore.Log.LogError("ContinueGame: " + e);
                return true;
            }
        }
    }

    [HarmonyPatch(typeof(BossEncounter), "CoroutineHeroKilledFinalSequence")]
    static class Patch_ContinueGameFinalTry
    {
        static void Prefix(Player hero, DamageInfo damage) { ContinueGame.OnFinalHeroDeath(hero, damage); }
    }
}
