using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Testing
{
    /// <summary>
    /// The test panel's lasting switches (invulnerability, endless ectoplasm, frozen AI, hidden HUD, game speed, the
    /// session unlock) and the per-frame work that keeps them true as bodies come and go. All are off at start and
    /// switched off together when an online match begins.
    /// </summary>
    static class TestCheats
    {
        /// <summary>The source name test mode gives the game's invincibility list and HUD hide list.</summary>
        internal const string Source = "TestMode";

        internal static bool InvulnerableHero, InvulnerableMonsters, EndlessEcto, FreezeAI, Hitboxes, UnlockAll;

        static bool s_hideHud;
        static GUIGame s_hiddenOn;
        static float s_speed = 1f;
        static float s_ectoAt;

        static readonly HashSet<Health> s_shielded = new HashSet<Health>();
        static readonly List<Health> s_want = new List<Health>();
        static readonly List<Health> s_drop = new List<Health>();

        /// <summary>The game speeds the View page offers.</summary>
        internal static readonly float[] Speeds = { 0.25f, 0.5f, 1f, 2f };

        internal static bool HideHud
        {
            get { return s_hideHud; }
            set { s_hideHud = value; ApplyHud(); }
        }

        /// <summary>Game speed through the game's own debug time multiplier (SystemTime keeps it on top of slow-mo).</summary>
        internal static float Speed
        {
            get { return s_speed; }
            set
            {
                s_speed = value;
                if (Singleton<SystemTime>.HasInstance()) SystemTime.SetDebugTimeMultiplier(value);
            }
        }

        /// <summary>Every frame while test mode is active.</summary>
        internal static void Tick()
        {
            Shields();
            if (EndlessEcto && Time.unscaledTime - s_ectoAt > 0.5f)
            {
                s_ectoAt = Time.unscaledTime;
                FillEcto();
            }
            if (s_hideHud) ApplyHud();
        }

        /// <summary>Everything off (an online match started).</summary>
        internal static void Reset()
        {
            InvulnerableHero = InvulnerableMonsters = EndlessEcto = FreezeAI = Hitboxes = UnlockAll = false;
            Shields();
            HideHud = false;
            if (s_speed != 1f) Speed = 1f;
        }

        /// <summary>Keep the game's invincibility on exactly the bodies the switches cover, including new bodies.</summary>
        static void Shields()
        {
            s_want.Clear();
            if ((InvulnerableHero || InvulnerableMonsters) && Singleton<SystemPlayers>.HasInstance())
            {
                foreach (var p in SystemPlayers.GetPlayers())
                {
                    if (p == null || !p.IsActive || p.GameObject == null || !p.IsAlive) continue;
                    if (p.IsHero ? !InvulnerableHero : !InvulnerableMonsters) continue;
                    var h = p.GameObject.GetComponent<Health>();
                    if (h != null) s_want.Add(h);
                }
            }
            foreach (var h in s_want) { h.StartInvincibility(Source); s_shielded.Add(h); }
            if (s_shielded.Count == s_want.Count) return;
            s_drop.Clear();
            foreach (var h in s_shielded) if (!s_want.Contains(h)) s_drop.Add(h);
            foreach (var h in s_drop)
            {
                s_shielded.Remove(h);
                if (h != null) h.StopInvincibility(Source);
            }
        }

        /// <summary>Top up every ghost's ectoplasm the way a pickup does (the game caps it at the ghost's maximum).</summary>
        static void FillEcto()
        {
            if (!Singleton<SystemPlayers>.HasInstance() || !Singleton<SystemLevel>.HasInstance()) return;
            foreach (var p in SystemPlayers.GetPlayers())
                if (p != null && p.IsActive && !p.IsHero && !p.IsAlive && p.GameObject != null) p.OnEctoplasmCollected(100f);
        }

        static void ApplyHud()
        {
            var gui = Singleton<SystemLevel>.HasInstance() ? SystemLevel.GetGUI() : null;
            if (s_hideHud)
            {
                if (gui == null || gui == s_hiddenOn) return;
                gui.Hide(Source);
                s_hiddenOn = gui;
            }
            else
            {
                if (s_hiddenOn != null) s_hiddenOn.Show(Source);
                s_hiddenOn = null;
            }
        }
    }
}
