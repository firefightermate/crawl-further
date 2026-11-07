using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Fires an AI monster's special at the hero, as a player would. The vanilla AI never uses specials (a special
    /// needs a player behind it), so gold thralls and fused blobs call <see cref="Drive"/> every frame.
    /// </summary>
    public static class AiSpecial
    {
        /// <summary>AI monsters charge their special this many times slower than a player would.</summary>
        public const float Slow = 1.5f;

        /// <summary>Prefab names whose special failed to start when fired by the AI; they are never tried again.
        /// Every special audited runs on anim events that are safe without a player, so this starts empty.</summary>
        public static readonly HashSet<string> Skip = new HashSet<string>();

        /// <summary>PlayerAI's private nested attack entry (one per attack the AI may pick).</summary>
        internal static readonly Type AttackType = typeof(PlayerAI).GetNestedType("Attack", System.Reflection.BindingFlags.NonPublic);
        static readonly System.Reflection.MethodInfo s_setState = AccessTools.Method(typeof(Player), "SetState");

        /// <summary>
        /// Count <paramref name="timer"/> up and, once the special has charged (<see cref="Slow"/> times its player
        /// charge time) and the hero is in its reach, start it. Does nothing while a player controls the body (its AI is
        /// switched off then).
        /// </summary>
        public static void Drive(Player p, ref float timer)
        {
            if (p == null || s_setState == null || AttackType == null) return;
            var atks = p.GetAttackComponent();
            int sid = atks != null ? atks.GetSpecialAttackId() : -1;
            if (sid < 0) return;
            var ai = R.Get<PlayerAI>(p, "m_playerAI");
            if (ai == null || !ai.enabled) return;
            var state = R.Get<Player.ePlayerState>(p, "m_state");
            if (state == Player.ePlayerState.AttackSpecial)
            {
                // the AI may not cut its own special short with a normal attack (it picks one only after a cooldown)
                if (R.Get<float>(ai, "m_timeSinceAttack") > 0f) R.Set(ai, "m_timeSinceAttack", 0f);
                return;
            }
            timer += Time.deltaTime;
            float wait = Mathf.Max(1f, p.GetSpecialChargeTime()) * Slow;
            if (timer < wait) return;
            string key = ModUtil.PrefabName(p.gameObject);
            if (Skip.Contains(key)) return;
            if (state != Player.ePlayerState.Idle && state != Player.ePlayerState.Run) return;
            if (R.Get<Player.ePlayerState>(p, "m_stateNext") != Player.ePlayerState.None) return;
            var sm = p.GetStatusManager();
            if (sm != null && sm.GetPreventAttack()) return;
            var hero = ModUtil.Hero();
            if (hero == null) return;
            var hh = hero.GetComponent<Health>();
            if (hh != null && !hh.IsAlive()) return;
            var list = Kit.Attacks(p);
            var sp = list != null && sid < list.Count ? list[sid] : Kit.Special(p);
            float reach = sp != null && sp.m_botData != null && sp.m_botData.m_rangeOuter > 0f ? sp.m_botData.m_rangeOuter : 60f;
            Vector2 to = (Vector2)hero.transform.position - (Vector2)p.transform.position;
            if (to.magnitude > reach) return;
            try
            {
                // the special entry state starts whatever attack id the AI holds (an AI body has no player data): hand it
                // the special, facing the hero
                var a = Activator.CreateInstance(AttackType);
                R.Set(a, "m_attackId", sid);
                R.Set(a, "m_attackPriority", 99);
                R.Set(a, "m_attackRadius", reach);
                R.Set(a, "m_attackCooldown", new MinMaxRange(1.6f, 2.6f));
                R.Set(a, "m_facePlayer", true);
                if (to.sqrMagnitude > 0.01f) R.Set(ai, "m_faceDirection", to.normalized);
                R.Set(ai, "m_currentAttack", a);
                s_setState.Invoke(p, new object[] { Player.ePlayerState.AttackSpecial });
                timer = 0f;
                if (atks.GetCurrAttackId() != sid) throw new Exception("special did not start");
            }
            catch (Exception e)
            {
                Skip.Add(key);
                timer = 0f;
                Plugin.Log.LogWarning("AI special skipped for " + key + ": " + (e.InnerException ?? e).Message);
                try { R.Set(ai, "m_currentAttack", null); } catch { }
            }
        }
    }
}
