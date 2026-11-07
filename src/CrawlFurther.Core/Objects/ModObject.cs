using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Objects
{
    using CrawlFurther.Util;

    /// <summary>The Prop of a Use / Touch object instance (added on spawn, never on the template).</summary>
    public class ModObject : Prop
    {
        public ObjectDef def;
        /// <summary>The linked copy when <see cref="ObjSpawn.pair"/> is set.</summary>
        public ModObject partner;
        /// <summary>Per-instance values for the def's own code; cleared on every spawn.</summary>
        public readonly Dictionary<string, object> data = new Dictionary<string, object>();
        AnimStateMachine m_states;
        GameObject m_indicator;
        int m_uses;
        float m_cool, m_possibleAt = -10f, m_flashAt = -10f;
        int m_flashId = -1;
        readonly float[] m_touchCool = new float[8];
        bool m_spent, m_off;

        public int Uses { get { return m_uses; } }
        public bool IsSpent { get { return m_spent; } }
        public bool IsOff { get { return m_off; } }
        public Room Room { get { return GetRoom(); } }
        public string State { get { return m_states != null ? m_states.GetStateName() : null; } }

        int m_gen;

        public void Init(ObjectDef d)
        {
            m_gen++;
            StopAllCoroutines();
            def = d;
            partner = null;
            data.Clear();
            m_uses = 0; m_cool = 0f; m_spent = false; m_off = false; m_possibleAt = -10f;
            for (int i = 0; i < m_touchCool.Length; i++) m_touchCool[i] = 0f;
            if (m_states == null) m_states = GetComponent<AnimStateMachine>();
            NextOf("Use", "Idle");
            var ind = transform.Find("Select_Reticule");
            m_indicator = ind != null ? ind.gameObject : null;
            if (m_indicator != null) m_indicator.SetActive(false);
        }

        public void Play(string state)
        {
            if (m_states == null) m_states = GetComponent<AnimStateMachine>();
            if (m_states != null && m_states.GetStateId(state) >= 0) m_states.SetState(state);
        }

        public bool Has(string state) { return m_states != null && m_states.GetStateId(state) >= 0; }

        /// <summary>Point a once-state at the state that follows it (per instance; the machine resolved ids at Start).</summary>
        void NextOf(string state, string next)
        {
            if (m_states == null) return;
            int a = m_states.GetStateId(state), b = m_states.GetStateId(next);
            if (a < 0 || b < 0) return;
            m_states.m_states[a].m_nextState = next;
            m_states.m_states[a].m_nextStateId = b;
        }

        /// <summary>Use it up now (shows "Spent").</summary>
        public void Spent()
        {
            m_spent = true;
            if (Has("Spent")) Play("Spent");
            if (m_indicator != null) m_indicator.SetActive(false);
        }

        /// <summary>Usable again (after a Spent()), playing <paramref name="state"/> (e.g. a reset anim whose then-state is Idle).</summary>
        public void Rearm(string state = "Idle") { m_spent = false; m_uses = 0; Play(Has(state) ? state : "Idle"); }

        /// <summary>Touch: this player cannot trigger it for <paramref name="seconds"/> (e.g. arriving on a warp pad).</summary>
        public void HoldOff(int playerId, float seconds)
        {
            if (playerId >= 0 && playerId < m_touchCool.Length) m_touchCool[playerId] = Mathf.Max(m_touchCool[playerId], seconds);
        }

        /// <summary>Run <paramref name="act"/> after <paramref name="seconds"/> while this object is alive and spawned.</summary>
        public void After(float seconds, Action act)
        {
            if (act == null) return;
            int gen = m_gen;
            StartCoroutine(AfterCo(seconds, act, gen));
        }

        System.Collections.IEnumerator AfterCo(float s, Action act, int gen)
        {
            yield return new WaitForSeconds(s);
            if (gen != m_gen || def == null) yield break;
            try { act(); } catch (Exception e) { FurtherCore.Log.LogError("Object " + def.id + " timer: " + e); }
        }

        public override Vector2 GetActionCenterPoint() { return transform.position; }
        public override bool GetPlayScaleBounceOnAction() { return def != null && def.bounce; }
        public override string GetActionText() { return def != null ? def.actionText : string.Empty; }

        bool TypeOk(PlayerData pd)
        {
            if (pd == null) return false;
            var u = def.users;
            if ((u & ObjUser.Hero) != 0 && pd.IsHero) return true;
            if ((u & ObjUser.Monster) != 0 && pd.IsMonster) return true;
            if ((u & ObjUser.Ghost) != 0 && !pd.IsAlive) return true;
            return false;
        }

        bool Afford(PlayerData pd)
        {
            if (def.costGold > 0 && Mathf.FloorToInt(pd.Gold) < def.costGold) return false;
            if (def.costEcto > 0 && Mathf.FloorToInt(pd.Ectoplasm) < def.costEcto) return false;
            if (def.costHealth > 0f)
            {
                var h = pd.GameObject != null ? pd.GameObject.GetComponent<Health>() : null;
                if (h == null || h.GetHealthCurrent() - 0.5f <= def.costHealth) return false;
            }
            return true;
        }

        bool HeroFight()
        {
            var r = GetRoom();
            return r != null && (r.GetDoorsLocked() || r.GetNumUnspawnedEnemies() > 0);
        }

        bool Ready()
        {
            if (def == null || m_spent || m_off || m_cool > 0f) return false;
            if (!gameObject.activeInHierarchy || !IsCurrentRoom()) return false;
            return true;
        }

        public override bool GetCanAction(PlayerData actioner, bool altButton)
        {
            if (altButton || def == null || def.kind != ObjKind.Use) return false;
            if (!Ready() || !TypeOk(actioner) || !Afford(actioner)) return false;
            // vanilla Player runs a usable prop's action INSTEAD of the attack: in a fight the hero never uses an object
            // (ghosts and monster players are unaffected) unless the def opts in
            if (actioner.IsHero && !def.heroInFight && HeroFight()) return false;
            if (def.canUse != null)
            {
                try { if (!def.canUse(new ObjUse { obj = this, pd = actioner, player = actioner.GameObject != null ? actioner.GameObject.GetComponent<Player>() : null })) return false; }
                catch (Exception e) { FurtherCore.Log.LogWarning("Object " + def.id + " canUse: " + e.Message); return false; }
            }
            return true;
        }

        public override bool OnPlayerCanAction(PlayerData actioner, bool altButton)
        {
            if (def == null || def.kind != ObjKind.Use || altButton) return false;
            bool heroBlocked = actioner != null && actioner.IsHero && !def.heroInFight && HeroFight();
            if (Ready() && TypeOk(actioner) && !heroBlocked) ObjectKit.TipOnce(actioner, def, this);
            if (Ready() && TypeOk(actioner) && !heroBlocked && def.costGold > 0 && actioner.IsHero) { m_flashAt = Time.time; StartFlash(actioner); }
            if (!GetCanAction(actioner, altButton)) return false;
            m_possibleAt = Time.time;
            return true;
        }

        public override bool OnAction(Player actioner, bool altButton)
        {
            if (actioner == null) return false;
            var pd = actioner.GetPlayerData();
            if (!OnPlayerCanAction(pd, altButton)) return false;
            if (def.costGold > 0) pd.SpendGold(def.costGold);
            if (def.costEcto > 0) pd.SpendEctoplasm(def.costEcto);
            if (def.costHealth > 0f) new ObjUse { obj = this, player = actioner, pd = pd }.Hurt(def.costHealth, true);
            Fire(actioner, pd);
            return true;
        }

        void Fire(Player actioner, PlayerData pd)
        {
            m_uses++;
            m_cool = def.cooldown;
            // the last use flows straight from Use into Spent (no frame of Idle between them)
            if (def.uses > 0 && m_uses >= def.uses) NextOf("Use", "Spent");
            if (Has("Use")) Play("Use");
            if (def.kind == ObjKind.Use && def.bounce)
            {
                var an = GetComponent<Animation>();
                if (an != null && an.GetClip("AnimActionBounce") != null) { an.Stop(); an.Play("AnimActionBounce"); }   // the vanilla prop hop
            }
            ObjectKit.PlaySound(def.useSound, transform);
            ObjectKit.Discovered(pd, this.gameObject, def);
            if (def.onUse != null)
            {
                try { def.onUse(new ObjUse { obj = this, player = actioner, pd = pd }); }
                catch (Exception e) { FurtherCore.Log.LogError("Object " + def.id + " onUse failed: " + e); }
            }
            if (def.uses > 0 && m_uses >= def.uses) m_spent = true;
            if (m_indicator != null) m_indicator.SetActive(false);
        }

        void StartFlash(PlayerData pd)
        {
            if (m_flashId == pd.Id) return;
            StopFlash();
            try { SystemLevel.GetGUI().FlashGoldStart(pd.Id); m_flashId = pd.Id; } catch { }
        }

        void StopFlash()
        {
            if (m_flashId < 0) return;
            try { SystemLevel.GetGUI().FlashGoldStop(m_flashId); } catch { }
            m_flashId = -1;
        }

        void Update()
        {
            if (def == null) return;
            if (m_cool > 0f) m_cool -= Time.deltaTime;
            for (int i = 0; i < m_touchCool.Length; i++) if (m_touchCool[i] > 0f) m_touchCool[i] -= Time.deltaTime;

            bool off = def.offDuringFight && GetRoom() != null && (GetRoom().GetDoorsLocked() || GetRoom().GetNumUnspawnedEnemies() > 0);
            if (off != m_off)
            {
                m_off = off;
                if (off && Has("Off")) Play("Off");
                else if (!off) Play(m_spent && Has("Spent") ? "Spent" : "Idle");
            }
            // after a once-state ends the machine goes to its next state; a spent object settles on Spent
            if (m_spent && !m_off && State == "Idle" && Has("Spent")) Play("Spent");

            if (m_indicator != null)
            {
                bool show = Time.time - m_possibleAt < 0.12f && !m_spent;
                if (show != m_indicator.activeSelf) m_indicator.SetActive(show);
            }
            if (m_flashId >= 0 && Time.time - m_flashAt > 0.15f) StopFlash();

            if (def.kind == ObjKind.Touch && Ready()) PollTouch();
        }

        void PollTouch()
        {
            Vector2 at = transform.position;
            float r2 = def.touchRadius * def.touchRadius;
            int n = 0;
            try { n = SystemPlayers.GetMaxPlayers(); } catch { n = 4; }
            for (int i = 0; i < n && i < m_touchCool.Length; i++)
            {
                PlayerData pd;
                try { pd = SystemPlayers.GetPlayer(i); } catch { continue; }
                if (pd == null || !pd.IsActive || pd.GameObject == null || m_touchCool[i] > 0f) continue;
                if (!TypeOk(pd)) continue;
                var go = pd.GameObject;
                if (((Vector2)go.transform.position - at).sqrMagnitude > r2) continue;
                var p = go.GetComponent<Player>();
                if (p == null) continue;
                if ((pd.IsAlive && ModUtil.IsGhost(p))) continue;
                if (def.canUse != null)
                {
                    bool ok;
                    try { ok = def.canUse(new ObjUse { obj = this, player = p, pd = pd }); } catch { ok = false; }
                    if (!ok) continue;
                }
                m_touchCool[i] = def.rearm;
                ObjectKit.TipOnce(pd, def, this);
                Fire(p, pd);
                if (!Ready()) break;
            }
        }

        void OnDisable() { StopFlash(); }
    }
}
