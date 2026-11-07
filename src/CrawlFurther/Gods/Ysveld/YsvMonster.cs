using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>On every Ysveld monster: 25% faster while standing on ice, the roll call the blizzard reads, and the
    /// death notice a Winter Bride listens for.</summary>
    public class YsvMonster : MonoBehaviour
    {
        public const float IceSpeed = 1.25f;
        public static readonly List<YsvMonster> Living = new List<YsvMonster>();

        /// <summary>Raised once when a Ysveld monster dies: the body and where it fell.</summary>
        public static event Action<GameObject, Vector2> Died;

        PlayerMovement m_move;
        Health m_health;
        bool m_on, m_dead;
        float m_speed = 1f;

        public bool Alive { get { return isActiveAndEnabled && (m_health == null || m_health.IsAlive()); } }

        /// <summary>True while it stands on Ysveld ice.</summary>
        public bool OnIce { get { return m_on; } }

        void Awake() { m_move = GetComponent<PlayerMovement>(); m_health = GetComponent<Health>(); }
        void OnEnable() { m_on = false; m_dead = false; m_speed = 1f; if (!Living.Contains(this)) Living.Add(this); YsvFloor.Ensure(); }
        void OnDestroy() { Living.Remove(this); }

        /// <summary>A speed factor of the monster's own (a Geode half), kept under the ice bonus.</summary>
        public void SetBaseSpeed(float k) { m_speed = k; Apply(); }

        void Apply()
        {
            if (m_move == null) return;
            float k = m_speed * (m_on ? IceSpeed : 1f);
            if (Mathf.Abs(k - 1f) < 0.001f) m_move.ResetSpeedMultiplier(); else m_move.SetSpeedMultiplier(k);
        }

        void NoteDeath()
        {
            if (m_dead || m_health == null || m_health.IsAlive()) return;
            m_dead = true;
            if (Died == null) return;
            try { Died(gameObject, transform.position); }
            catch (Exception e) { Plugin.Log.LogError("Ysveld death handler failed: " + e); }
        }

        void Update()
        {
            if (m_move == null) return;
            bool alive = m_health == null || m_health.IsAlive();
            if (!alive) NoteDeath();
            bool on = alive && YsvFloor.Count > 0 && YsvFloor.Covers(transform.position);
            if (on == m_on) return;
            m_on = on;
            Apply();
            ModInd.Set(gameObject, YsveldFx.IndIce, on);      // skating: the same ice skid the sliding hero shows
        }

        void OnDisable()
        {
            NoteDeath();
            Living.Remove(this);
            if (m_move != null && (m_on || m_speed != 1f)) m_move.ResetSpeedMultiplier();
            if (m_on) ModInd.Set(gameObject, YsveldFx.IndIce, false);
            m_on = false; m_speed = 1f;
        }

        static readonly List<GameObject> s_bodies = new List<GameObject>();
        static float s_bodiesAt = -1f;

        /// <summary>Every living monster body in play (any god), refreshed at most every 0.1 s.</summary>
        public static List<GameObject> AllBodies()
        {
            if (Time.time - s_bodiesAt < 0.1f) return s_bodies;
            s_bodiesAt = Time.time;
            s_bodies.Clear();
            var hero = ModUtil.Hero();
            foreach (var p in FindObjectsOfType<Player>())
            {
                if (p == null || p.gameObject == hero || ModUtil.IsGhost(p)) continue;
                var h = p.GetComponent<Health>();
                if (h != null && h.IsAlive()) s_bodies.Add(p.gameObject);
            }
            return s_bodies;
        }
    }
}
