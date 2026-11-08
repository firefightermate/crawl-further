using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Game
{
    using CrawlFurther.Ghosts;
    using CrawlFurther.Util;

    /// <summary>
    /// Chaos: the hero holds two spells. Special casts the first (the game's own spell slot), the ghost button the second.
    /// <para>The game keeps one spell per player (PlayerGameData.m_powerupSwappable and its prefab; a spell is a powerup of
    /// stack type Swap). The second is kept here, with its own live instance on the hero and its own charge. To cast it,
    /// the two are exchanged in the game's slot (pointers, special attack, charge), the game's buffered special press is
    /// set, and once the cast has played out they are exchanged back. Both instances stay alive the whole time, so a
    /// spell that is still working (a shield, a beam) is never cut short.</para>
    /// <para>Buying a spell with one held puts it in the second slot. With two held, the buyer picks which one to drop
    /// (a bot drops the cheaper). Bots use whichever spell is ready.</para>
    /// </summary>
    public static class ChaosSpells
    {
        /// <summary>Set false to keep one spell in chaos games too.</summary>
        public static bool Enabled = true;

        internal const string PickTitle = "_Drop a spell_";
        internal const string PickText = "You can hold two spells. Pick the one to drop for {0}.";
        const int ModCooldownSpecial = 28;           // the game's modifier for special charge times
        const float CastWait = 0.6f;                // a cast that has not started by then is given up
        const float CastLimit = 6f;                 // and one that has not ended by then is ended

        class Slot
        {
            public Powerup prefab, inst;            // the second spell (the first while exchanged for a cast)
            public float charge = 999f;             // its charge, as Player.m_specialCharge
            public bool swapped;                    // exchanged with the game's slot for a cast
            public float since;                     // when the exchange was made
            public float chargeAtSwap;
            public bool cast;
            public float castAt;
            public int idleFrames;
        }

        static readonly Dictionary<int, Slot> s_slots = new Dictionary<int, Slot>();
        internal static bool s_bypass;

        public static bool Active { get { return Enabled && ChaosMode.Active; } }

        internal static void Reset() { s_slots.Clear(); }

        static Slot Get(PlayerData pd, bool make)
        {
            Slot s;
            if (!s_slots.TryGetValue(pd.Id, out s) && make) s_slots[pd.Id] = s = new Slot();
            return s;
        }

        internal static bool IsSpell(Powerup p)
        {
            try { return p != null && (int)p.GetStackType() == 2; } catch { return false; }
        }

        // ------------------------------------------------------------------ what a player holds
        /// <summary>The spell Special casts (the game's slot, unless exchanged for a cast of the second).</summary>
        public static Powerup First(PlayerData pd)
        {
            if (pd == null) return null;
            var s = Get(pd, false);
            return s != null && s.swapped ? s.prefab : pd.GameData.GetPowerupSwappablePrefab();
        }

        /// <summary>The spell the ghost button casts, or null.</summary>
        public static Powerup Second(PlayerData pd)
        {
            if (pd == null) return null;
            var s = Get(pd, false);
            if (s == null) return null;
            return s.swapped ? pd.GameData.GetPowerupSwappablePrefab() : s.prefab;
        }

        /// <summary>Charge of the first and second spell, 0 to 1.</summary>
        public static float Ratio(PlayerData pd, bool second)
        {
            var s = pd != null ? Get(pd, false) : null;
            var p = Body(pd);
            if (p == null) return 0f;
            bool inGame = second == (s != null && s.swapped);       // the spell asked about is in the game's slot
            float charge = inGame ? R.Get<float>(p, "m_specialCharge") : (s != null ? s.charge : 0f);
            var spell = second ? Second(pd) : First(pd);
            float t = ChargeTime(pd, spell);
            return t <= 0.001f ? 1f : Mathf.Clamp01(charge / t);
        }

        static Player Body(PlayerData pd)
        {
            try { return pd != null && pd.GameObject != null ? pd.GameObject.GetComponent<Player>() : null; } catch { return null; }
        }

        static MethodInfo s_modify, s_applyMods, s_libraryFound;

        static float ChargeTime(PlayerData pd, Powerup spell)
        {
            if (spell == null) return 0f;
            float t = spell.GetSpecialChargeTime();
            try
            {
                if (s_modify == null) s_modify = AccessTools.Method(typeof(PlayerGameData), "Modify");
                var pt = s_modify.GetParameters()[0].ParameterType;
                return (float)s_modify.Invoke(pd.GameData, new object[] { Enum.ToObject(pt, ModCooldownSpecial), t });
            }
            catch { return t; }
        }

        // ------------------------------------------------------------------ the slot's instance
        static void Spawn(PlayerData pd, Slot s)
        {
            if (s.prefab == null || s.inst != null) return;
            var body = pd.GameObject;
            if (body == null || !pd.IsHero || !pd.IsAlive) return;
            var go = ExtentionsMethodsPool.Spawn(s.prefab.gameObject, body.transform.position, Quaternion.identity);
            var inst = go != null ? go.GetComponent<Powerup>() : null;
            if (inst == null) return;
            inst.Initialise(body, s.prefab);
            s.inst = inst;
        }

        static void Despawn(Slot s)
        {
            if (s.inst != null)
            {
                try { ExtentionsMethodsPool.Despawn(s.inst.gameObject); } catch { }
            }
            s.inst = null;
        }

        static void ApplyModifiers(Powerup prefab, PlayerData pd)
        {
            if (s_applyMods == null) s_applyMods = AccessTools.Method(typeof(Powerup), "ApplyPowerupModifiers");
            try { s_applyMods.Invoke(null, new object[] { prefab, pd }); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Chaos spells: modifiers of " + prefab.name + ": " + e.Message); }
        }

        static void Found(PlayerData pd, Powerup prefab)
        {
            try
            {
                if (s_libraryFound == null)
                    foreach (var m in typeof(SystemLibrary).GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static))
                        if (m.Name == "OnEntryFound" && m.GetParameters().Length == 3 && m.GetParameters()[0].ParameterType == typeof(PlayerData)) { s_libraryFound = m; break; }
                if (s_libraryFound != null) s_libraryFound.Invoke(null, new object[] { pd, prefab.gameObject, null });
            }
            catch { }
        }

        /// <summary>The second slot takes <paramref name="prefab"/>.</summary>
        static void Put(PlayerData pd, Slot s, Powerup prefab)
        {
            Despawn(s);
            if (s.prefab != null) pd.GameData.RemoveModifiers(s.prefab.name);
            s.prefab = prefab;
            s.charge = 999f;
            ApplyModifiers(prefab, pd);
            Spawn(pd, s);
            FurtherCore.Log.LogInfo("Chaos: P" + (pd.Id + 1) + " holds " + Name(First(pd)) + " and " + Name(prefab));
        }

        internal static string Name(Powerup p)
        {
            if (p == null) return "nothing";
            try { var n = p.GetDisplayName(); return string.IsNullOrEmpty(n) ? p.name : n; } catch { return p.name; }
        }

        /// <summary>The second spell and the game's slot change places: prefab, instance, special attack and charge.</summary>
        static void Exchange(PlayerData pd, Slot s)
        {
            var gd = pd.GameData;
            var p1 = R.Get<Powerup>(gd, "m_powerupSwappablePrefab");
            var i1 = R.Get<Powerup>(gd, "m_powerupSwappable");
            R.Set(gd, "m_powerupSwappablePrefab", s.prefab);
            R.Set(gd, "m_powerupSwappable", s.inst);
            s.prefab = p1;
            s.inst = i1;
            var body = Body(pd);
            if (body == null) return;
            float c = R.Get<float>(body, "m_specialCharge");
            R.Set(body, "m_specialCharge", s.charge);
            s.charge = c;
            var now = R.Get<Powerup>(gd, "m_powerupSwappablePrefab");
            var atk = body.GetAttackComponent();
            if (atk == null || !pd.IsHero || now == null) return;
            var data = R.Get<AttackData>(now, "m_specialAttack");
            if (data != null && data.m_animationFront != null)
                atk.SetSpecialAttack(data, R.Get<List<DamageEffectData>>(now, "m_specialAttackDamageEffects"));
            else atk.RemoveSpecialAttack();
        }

        static void EndCast(PlayerData pd, Slot s)
        {
            if (!s.swapped) return;
            s.swapped = false;
            Exchange(pd, s);
        }

        // ------------------------------------------------------------------ every frame
        internal static void Tick()
        {
            if (s_slots.Count == 0) return;
            bool active = Active;
            float dt = Time.deltaTime;
            foreach (var kv in s_slots)
            {
                PlayerData pd = null;
                try { pd = SystemPlayers.GetPlayer(kv.Key); } catch { }
                var s = kv.Value;
                if (pd == null) continue;
                try { Step(pd, s, active, dt); }
                catch (Exception e) { FurtherCore.Log.LogWarning("Chaos spells: " + e.Message); s.swapped = false; }
            }
        }

        static void Step(PlayerData pd, Slot s, bool active, float dt)
        {
            var body = Body(pd);
            if (body != null) s.charge += dt;
            if (s.swapped)
            {
                if (body == null || !pd.IsHero || !pd.IsAlive) { EndCast(pd, s); return; }
                float now = R.Get<float>(body, "m_specialCharge");
                if (!s.cast)
                {
                    if (now < s.chargeAtSwap - 0.0001f)
                    {
                        s.cast = true; s.castAt = Time.time; s.idleFrames = 0;
                        // spent: the buffered press must not cast the first spell too once they swap back
                        R.Set(body, "m_timePressedSpecial", -1000f);
                    }
                    else if (Time.time - s.since > CastWait) { R.Set(body, "m_timePressedSpecial", -1000f); EndCast(pd, s); }
                    return;
                }
                var atk = body.GetAttackComponent();
                bool busy = atk != null && atk.GetAttacking();
                s.idleFrames = busy ? 0 : s.idleFrames + 1;
                if ((s.idleFrames >= 2 && Time.time - s.castAt > 0.1f) || Time.time - s.castAt > CastLimit) EndCast(pd, s);
                return;
            }
            if (!active || s.prefab == null || body == null || !pd.IsHero || !pd.IsAlive) return;
            if (pd.IsBot)
            {
                // a bot uses whichever is ready: the ready one goes into the game's slot for good
                var a = body.GetAttackComponent();
                if (a != null && !a.GetAttacking() && !body.GetSpecialReady() && s.charge > ChargeTime(pd, s.prefab)) Exchange(pd, s);
                return;
            }
            if (!GhostControls.Down(pd)) return;
            if (s.charge <= ChargeTime(pd, s.prefab)) return;
            var attacks = body.GetAttackComponent();
            if (attacks == null || attacks.GetAttacking()) return;
            s.swapped = true;
            s.cast = false;
            s.since = Time.time;
            Exchange(pd, s);
            s.chargeAtSwap = R.Get<float>(body, "m_specialCharge");
            // the game's own buffered press: it casts as soon as the hero can, through the usual checks
            R.Set(body, "m_timePressedSpecial", Time.timeSinceLevelLoad);
        }

        // ------------------------------------------------------------------ buying
        /// <summary>Powerup.Collect for a spell in a chaos game. False: handled here (the game's code is skipped).</summary>
        internal static bool OnCollect(Powerup prefab, PlayerData pd, bool fromDeity, ref Powerup result)
        {
            if (s_bypass || !Active || pd == null || !IsSpell(prefab) || pd.GameData == null) return true;
            var s = Get(pd, true);
            EndCast(pd, s);
            var cur = pd.GameData.GetPowerupSwappablePrefab();
            if (cur == null || !IsSpell(cur) || cur == prefab) return true;
            if (s.prefab == prefab) { result = s.inst; return false; }
            if (!fromDeity) Found(pd, prefab);
            if (s.prefab == null) { Put(pd, s, prefab); result = s.inst; return false; }
            // two held already
            if (pd.IsBot)
            {
                float c1 = cur.m_cost, c2 = s.prefab.m_cost;
                if (c1 <= c2) { Replace(pd, prefab); return false; }
                Put(pd, s, prefab);
                result = s.inst;
                return false;
            }
            Ask(pd, prefab);
            result = null;
            return false;
        }

        /// <summary>The first spell is dropped for <paramref name="prefab"/>: the game's own collect, which swaps its slot.</summary>
        static void Replace(PlayerData pd, Powerup prefab)
        {
            s_bypass = true;
            try { Powerup.Collect(prefab, pd, true, false); }
            finally { s_bypass = false; }
            FurtherCore.Log.LogInfo("Chaos: P" + (pd.Id + 1) + " holds " + Name(First(pd)) + " and " + Name(Second(pd)));
        }

        static void Ask(PlayerData pd, Powerup prefab)
        {
            var first = First(pd); var second = Second(pd);
            Action dropFirst = () => Safe(() => Replace(pd, prefab));
            Action dropSecond = () => Safe(() => { var s = Get(pd, true); EndCast(pd, s); Put(pd, s, prefab); });
            Singleton<SystemMenu>.Get.ShowPrompt(PickTitle, string.Format(PickText, Name(prefab)),
                                                  Name(first), dropFirst, Name(second), dropSecond, pd.Id, null);
        }

        static void Safe(Action a)
        {
            try { a(); }
            catch (Exception e) { FurtherCore.Log.LogError("Chaos spells: " + e); }
        }

        // ------------------------------------------------------------------ the game's own lifecycle
        internal static void BeforeInstantiate(PlayerGameData gd)
        {
            var pd = Owner(gd);
            Slot s;
            if (pd == null || !s_slots.TryGetValue(pd.Id, out s)) return;
            if (s.swapped)
            {
                // back to the plain order before the game rebuilds its instances (the body may be gone: data only)
                s.swapped = false;
                var p1 = R.Get<Powerup>(gd, "m_powerupSwappablePrefab");
                var i1 = R.Get<Powerup>(gd, "m_powerupSwappable");
                R.Set(gd, "m_powerupSwappablePrefab", s.prefab);
                R.Set(gd, "m_powerupSwappable", s.inst);
                s.prefab = p1; s.inst = i1;
            }
            Despawn(s);
        }

        internal static void AfterInstantiate(PlayerGameData gd, GameObject body, bool isHero, bool isAlive, bool inhabiting)
        {
            var pd = Owner(gd);
            Slot s;
            if (pd == null || !s_slots.TryGetValue(pd.Id, out s) || s.prefab == null) return;
            if (body != null && isHero && isAlive && !inhabiting) Spawn(pd, s);
        }

        internal static void Cleared(PlayerGameData gd)
        {
            var pd = Owner(gd);
            Slot s;
            if (pd == null || !s_slots.TryGetValue(pd.Id, out s)) return;
            Despawn(s);
            if (s.prefab != null) gd.RemoveModifiers(s.prefab.name);
            s_slots.Remove(pd.Id);
        }

        internal static void SelfCheck(Action<string> bad, Action<string> note)
        {
            foreach (var f in new[] { "m_powerupSwappablePrefab", "m_powerupSwappable", "m_ownerPlayerId" })
                if (AccessTools.Field(typeof(PlayerGameData), f) == null) bad("PlayerGameData." + f + " not found");
            foreach (var f in new[] { "m_specialCharge", "m_timePressedSpecial" })
                if (AccessTools.Field(typeof(Player), f) == null) bad("Player." + f + " not found");
            foreach (var f in new[] { "m_specialAttack", "m_specialAttackDamageEffects" })
                if (AccessTools.Field(typeof(Powerup), f) == null) bad("Powerup." + f + " not found");
            if (AccessTools.Method(typeof(Powerup), "ApplyPowerupModifiers") == null) bad("Powerup.ApplyPowerupModifiers not found");
            if (AccessTools.Method(typeof(PlayerGameData), "Modify") == null) bad("PlayerGameData.Modify not found");
            if (AccessTools.Field(typeof(GUIPlayer), "m_barSpecial") == null) bad("GUIPlayer.m_barSpecial not found");
            if (AccessTools.Field(typeof(GUIHeroStats), "m_spell") == null) bad("GUIHeroStats.m_spell not found");
            if (AccessTools.Field(typeof(MenuMain), "m_menuMain") == null) bad("MenuMain.m_menuMain not found");
            note(!Enabled || !ChaosMode.Enabled ? "off" : ChaosMode.Active ? "a chaos game is on" : "on (no chaos game right now)");
        }

        static PlayerData Owner(PlayerGameData gd)
        {
            try { return gd != null ? SystemPlayers.GetPlayer(R.Get<int>(gd, "m_ownerPlayerId")) : null; } catch { return null; }
        }
    }

    [HarmonyPatch(typeof(Powerup), "Collect")]
    static class Patch_ChaosSpellCollect
    {
        static bool Prefix(Powerup powerupPrefab, PlayerData player, bool fromDeity, ref Powerup __result)
        {
            try { return ChaosSpells.OnCollect(powerupPrefab, player, fromDeity, ref __result); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Chaos spells (collect): " + e.Message); return true; }
        }
    }

    [HarmonyPatch(typeof(PlayerGameData), "InstantiatePowerups")]
    static class Patch_ChaosSpellInstances
    {
        static void Prefix(PlayerGameData __instance)
        {
            try { ChaosSpells.BeforeInstantiate(__instance); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Chaos spells (rebuild): " + e.Message); }
        }

        static void Postfix(PlayerGameData __instance, GameObject playerObject, bool isHero, bool isAlive, bool inhabiting)
        {
            try { ChaosSpells.AfterInstantiate(__instance, playerObject, isHero, isAlive, inhabiting); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Chaos spells (rebuild): " + e.Message); }
        }
    }

    [HarmonyPatch(typeof(PlayerGameData), "ClearPowerups")]
    static class Patch_ChaosSpellClear
    {
        static void Postfix(PlayerGameData __instance)
        {
            try { ChaosSpells.Cleared(__instance); }
            catch (Exception e) { FurtherCore.Log.LogWarning("Chaos spells (clear): " + e.Message); }
        }
    }
}
