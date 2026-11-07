using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// On the hero: while he stands on Ysveld ice his deceleration and friction drop to 12% (he keeps sliding and drifts
    /// through turns); both are restored the moment he leaves the ice, dies, or this component goes away. Low friction
    /// lets old velocity pile onto new input, so walking speed on ice is capped at his normal top speed.
    /// Moves that throw him across the ice drive him through here too: <see cref="Glide"/> (a Sleet Gust) adds a second
    /// shove that the ice carries on, and <see cref="Curl"/> (a Hoarclaw's hurl) keeps him sliding until he leaves the ice
    /// or hits something.
    /// </summary>
    public class YsvSlide : MonoBehaviour
    {
        public const float Slip = 0.12f;
        /// <summary>The longest a curl may last (the mod's crowd-control cap).</summary>
        public const float CurlMax = 1.2f;
        static readonly HarmonyLib.AccessTools.FieldRef<PlayerMovement, float> s_speedMax =
            HarmonyLib.AccessTools.FieldRefAccess<PlayerMovement, float>("m_speedMaxFinal");
        static readonly HarmonyLib.AccessTools.FieldRef<PlayerMovement, float> s_animTag =
            HarmonyLib.AccessTools.FieldRefAccess<PlayerMovement, float>("m_animTagVelocity");
        static readonly HarmonyLib.AccessTools.FieldRef<PlayerMovement, float> s_pushTimer =
            HarmonyLib.AccessTools.FieldRefAccess<PlayerMovement, float>("m_pushTimer");
        static readonly HarmonyLib.AccessTools.FieldRef<PlayerMovement, Vector2> s_velocity =
            HarmonyLib.AccessTools.FieldRefAccess<PlayerMovement, Vector2>("m_velocity");

        /// <summary>How many heroes are on ice or being driven right now; lets the movement patch skip everyone else.</summary>
        internal static int Busy;

        PlayerMovement m_move;
        Health m_health;
        Rigidbody m_body;
        bool m_on, m_busy;
        float m_decel, m_friction;
        // a curl: a set velocity held while on ice
        Vector2 m_curl; float m_curlLeft, m_trail; GameObject m_curlBy, m_spin; System.Action<YsvSlide, bool> m_curlEnd;

        void Awake() { m_move = GetComponent<PlayerMovement>(); m_health = GetComponent<Health>(); m_body = GetComponent<Rigidbody>(); }

        /// <summary>The hero's slide component (added if missing).</summary>
        public static YsvSlide Of(GameObject hero) { return hero == null ? null : hero.GetComponent<YsvSlide>() ?? hero.AddComponent<YsvSlide>(); }

        /// <summary>True while the hero stands on ice.</summary>
        public bool OnIce { get { return m_on; } }

        /// <summary>True while a curl is driving him.</summary>
        public bool Curling { get { return m_curlLeft > 0f; } }

        /// <summary>Shove him along <paramref name="dir"/> at <paramref name="speed"/> px/s; on ice the slide carries it far.</summary>
        public void Glide(Vector2 dir, float speed)
        {
            if (m_move == null || dir.sqrMagnitude < 0.01f) return;
            m_move.AddImpulse(dir.normalized * speed);
        }

        /// <summary>Slide at <paramref name="speed"/> px/s along <paramref name="dir"/> while on ice (at most
        /// <see cref="CurlMax"/> s). <paramref name="end"/> is called once when it stops: true if he hit a wall.</summary>
        public void Curl(Vector2 dir, float speed, GameObject by, System.Action<YsvSlide, bool> end)
        {
            if (dir.sqrMagnitude < 0.01f) return;
            m_curl = dir.normalized * speed; m_curlLeft = CurlMax; m_curlBy = by; m_curlEnd = end; m_trail = 0f;
            if (YsveldFx.CurlSpin != null && m_spin == null) m_spin = ModAttach.Spawn(YsveldFx.CurlSpin, gameObject, Vector2.zero);
            SetBusy();
        }

        void SetBusy() { if (!m_busy) { m_busy = true; Busy++; } }
        void ClearBusy() { if (m_busy && !m_on && m_curlLeft <= 0f) { m_busy = false; Busy--; } }

        void Update()
        {
            if (m_move == null) return;
            bool alive = m_health == null || m_health.IsAlive();
            bool on = alive && YsvFloor.Count > 0 && YsvFloor.Covers(transform.position);
            if (on != m_on)
            {
                ModInd.Set(gameObject, YsveldFx.IndIce, on);
                if (on)
                {
                    m_decel = R.Get<float>(m_move, "m_deceleration");
                    m_friction = R.Get<float>(m_move, "m_friction");
                    R.Set(m_move, "m_deceleration", m_decel * Slip);
                    R.Set(m_move, "m_friction", m_friction * Slip);
                    m_on = true;
                    SetBusy();
                }
                else Restore();
            }
            if (m_curlLeft > 0f)
            {
                m_curlLeft -= Time.deltaTime;
                Vector2 me = transform.position;
                if (!alive || m_curlLeft <= 0f || !m_on) { EndCurl(false); return; }
                if (!ModUtil.Clear(me, me + m_curl.normalized * 8f)) { EndCurl(true); return; }
                if (MonsterAhead(me)) { EndCurl(false); return; }
                m_trail -= Time.deltaTime;
                if (m_trail <= 0f && YsveldFx.CurlTrail != null) { m_trail = 0.06f; SystemPool.Spawn(YsveldFx.CurlTrail, me); }
            }
        }

        bool MonsterAhead(Vector2 me)
        {
            foreach (var m in YsvMonster.AllBodies())
            {
                if (m == null || m == gameObject || m == m_curlBy) continue;
                var d = (Vector2)m.transform.position - me;
                if (d.sqrMagnitude < 100f && Vector2.Dot(d, m_curl) > 0f) return true;
            }
            return false;
        }

        void EndCurl(bool wall)
        {
            if (m_curlLeft <= 0f && m_curlEnd == null) return;
            m_curlLeft = 0f;
            if (m_spin != null) { ModAttach.Drop(m_spin, gameObject); m_spin = null; }
            var cb = m_curlEnd; m_curlEnd = null; m_curlBy = null;
            if (m_body != null) m_body.velocity = Vector3.zero;
            if (m_move != null) s_velocity(m_move) = Vector2.zero;
            ClearBusy();
            if (cb != null) cb(this, wall);
        }

        /// <summary>Called after PlayerMovement.FixedUpdate: a curl drives him; plain walking on ice is held to
        /// his top speed (lunges and knockback are left alone so they still carry across the ice).</summary>
        internal void AfterMove()
        {
            if (m_move == null || m_body == null) return;
            if (m_curlLeft > 0f)
            {
                s_velocity(m_move) = m_curl;
                m_body.velocity = new Vector3(m_curl.x, m_curl.y, 0f);
                return;
            }
            if (!m_on || s_animTag(m_move) > 0f || s_pushTimer(m_move) > 0f) return;
            float max = s_speedMax(m_move);
            Vector2 v = s_velocity(m_move);
            if (max <= 0f || v.sqrMagnitude <= max * max) return;
            v = v.normalized * max;
            s_velocity(m_move) = v;
            m_body.velocity = new Vector3(v.x, v.y, 0f);
        }

        void Restore()
        {
            if (!m_on || m_move == null) return;
            R.Set(m_move, "m_deceleration", m_decel);
            R.Set(m_move, "m_friction", m_friction);
            m_on = false;
            ClearBusy();
        }

        void OnDisable()
        {
            if (m_curlLeft > 0f) { m_curlLeft = 0f; m_curlEnd = null; }
            if (m_spin != null) { ModAttach.Drop(m_spin, gameObject); m_spin = null; }
            Restore();
            if (m_busy) { m_busy = false; Busy--; }
            ModInd.Set(gameObject, YsveldFx.IndIce, false);
        }

        void OnDestroy() { Restore(); }
    }

    [HarmonyLib.HarmonyPatch(typeof(PlayerMovement), "FixedUpdate")]
    static class Patch_YsvSlideCap
    {
        static void Postfix(PlayerMovement __instance)
        {
            if (YsvSlide.Busy <= 0) return;
            var slide = __instance.GetComponent<YsvSlide>();
            if (slide != null) slide.AfterMove();
        }
    }
}
