using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;

    /// <summary>
    /// The drawn status overlays and indicators on one character: pooled instances that follow the feet or head every
    /// frame, sized to the victim (a "Big" art variant for large bodies), sorted just in front of it, and despawned the
    /// moment the status ends or the character dies, despawns or is destroyed. No per-frame allocation.
    /// </summary>
    public class StatusOverlays : MonoBehaviour
    {
        const int Max = 8;
        static readonly AccessTools.FieldRef<PlayerStatusManager, List<ActiveStatus>> s_list =
            AccessTools.FieldRefAccess<PlayerStatusManager, List<ActiveStatus>>("m_statuses");
        static readonly AccessTools.FieldRef<PlayerStatusManager, GameObject> s_owner =
            AccessTools.FieldRefAccess<PlayerStatusManager, GameObject>("m_gameObject");

        internal static bool Has(PlayerStatusManager m, Status s)
        {
            var list = m != null ? s_list(m) : null;
            if (list == null || s == null) return false;
            for (int i = 0; i < list.Count; i++) if (list[i] != null && list[i].m_data == s) return true;
            return false;
        }

        /// <summary>The character a status manager belongs to.</summary>
        public static GameObject Owner(PlayerStatusManager m) { return m != null ? s_owner(m) : null; }

        readonly StatusOverlayDef[] m_def = new StatusOverlayDef[Max];
        readonly GameObject[] m_inst = new GameObject[Max];
        readonly OverlayTag[] m_tag = new OverlayTag[Max];
        readonly float[] m_y = new float[Max];      // the anchor height above the feet, worked out when shown
        readonly float[] m_until = new float[Max];  // timed indicators: drop at this Time.time (0 = until hidden)
        int m_count;
        Health m_health;
        Transform m_tr;
        BoxCollider m_box;
        bool m_boxLooked;
        exSprite m_spr;
        Renderer m_rend;

        void Awake()
        {
            m_tr = transform;
            m_spr = GetComponent<exSprite>();
            m_rend = GetComponent<Renderer>();
            m_health = GetComponent<Health>();
        }

        /// <summary>Head top (px above the feet) and width of the body: the hurtbox, checked against the art.</summary>
        void Measure(out float top, out float width)
        {
            top = 18f; width = 12f;
            if (!m_boxLooked)
            {
                m_boxLooked = true;
                int layer = LayerMask.NameToLayer("DamagablePlayer");
                foreach (var b in GetComponentsInChildren<BoxCollider>(true))
                    if (b.transform != m_tr && b.gameObject.layer == layer) { m_box = b; break; }
            }
            float feetY = m_tr.position.y;
            if (m_box != null)
            {
                var bt = m_box.transform;
                var ls = bt.lossyScale;
                var c = bt.TransformPoint(m_box.center);
                top = c.y + Mathf.Abs(m_box.size.y * ls.y) * 0.5f - feetY;
                width = Mathf.Abs(m_box.size.x * ls.x);
            }
            float sTop = -1f, sW = 0f;
            if (m_spr != null && m_spr.enabled && m_spr.atlas != null)
            {
                var sh = SpriteSheets.ByAtlas(m_spr.atlas);
                int bx, by, bw, bh;
                if (sh != null)
                {
                    // mod sheets are untrimmed cells: use the frame's opaque bounds
                    if (MonsterFactory.Bounds(sh, m_spr.index, out bx, out by, out bw, out bh))
                    {
                        float k = Mathf.Abs(m_tr.lossyScale.y);
                        sTop = (m_spr.offset.y + by + bh) * k; sW = bw * Mathf.Abs(m_tr.lossyScale.x);
                    }
                }
                else if (m_rend != null)
                {
                    var b = m_rend.bounds;                 // vanilla sprites are trimmed quads
                    sTop = b.max.y - feetY; sW = b.size.x;
                }
            }
            if (sTop > 0f) top = Mathf.Max(top, Mathf.Min(sTop, top + 14f));
            width = Mathf.Max(width, sW);
        }

        internal void Show(StatusOverlayDef d) { Show(d, 0f); }

        /// <summary>Show for <paramref name="seconds"/> (0 = until hidden). Showing again extends the time and keeps the
        /// running loop; a one-shot restarts.</summary>
        internal void Show(StatusOverlayDef d, float seconds)
        {
            if (d == null || d.small == null) return;
            float until = seconds > 0f ? Time.time + seconds : 0f;
            for (int i = 0; i < Max; i++)
                if (m_def[i] == d && Live(i))
                {
                    if (d.once) { Drop(i); break; }
                    if (m_until[i] > 0f) m_until[i] = until == 0f ? 0f : Mathf.Max(m_until[i], until);
                    return;                                     // already showing (a refresh keeps the running loop)
                }
            int slot = -1;
            for (int i = 0; i < Max; i++) if (m_def[i] == null || !Live(i)) { slot = i; break; }
            if (slot < 0) return;
            float top, width;
            Measure(out top, out width);
            // never pixel-doubled: the drawn "Big" variant is the largest an overlay gets
            bool big = width >= 22f || top >= 34f;
            var tmpl = big && d.big != null ? d.big : d.small;
            float y;
            if (d.at == OverlayAt.Head) y = top + d.offsetY;
            else if (d.liftOverHead) y = Mathf.Max(d.offsetY, top + 1f);
            else y = d.offsetY;
            var go = SystemPool.Spawn(tmpl, Pos(y, 0f));
            if (go == null) return;
            go.transform.localScale = Vector3.one;
            var tag = go.GetComponent<OverlayTag>() ?? go.AddComponent<OverlayTag>();
            tag.owner = this;
            m_def[slot] = d; m_inst[slot] = go; m_tag[slot] = tag; m_y[slot] = y; m_until[slot] = until;
            Recount();
            Place();
        }

        /// <summary>True while <paramref name="d"/> is shown on this character.</summary>
        public bool Showing(StatusOverlayDef d)
        {
            for (int i = 0; i < Max; i++) if (m_def[i] == d && Live(i)) return true;
            return false;
        }

        internal void Hide(StatusOverlayDef d)
        {
            for (int i = 0; i < Max; i++)
                if (m_def[i] == d) Drop(i);
            Recount();
        }

        bool Live(int i)
        {
            var go = m_inst[i];
            return go != null && go.activeSelf && m_tag[i] != null && m_tag[i].owner == this;
        }

        void Drop(int i)
        {
            if (Live(i))
            {
                m_tag[i].owner = null;
                if (!SystemMain.GetDeloadInProgress()) SystemPool.Despawn(m_inst[i]);
            }
            m_def[i] = null; m_inst[i] = null; m_tag[i] = null; m_until[i] = 0f;
        }

        void Recount()
        {
            m_count = 0;
            for (int i = 0; i < Max; i++) if (m_def[i] != null) m_count++;
        }

        Vector3 Pos(float y, float dz)
        {
            var p = m_tr.position;
            return new Vector3(p.x, p.y + y, p.z - 0.04f - dz);
        }

        void Place()
        {
            float stack = 0f;
            for (int i = 0; i < Max; i++)
            {
                if (m_def[i] == null) continue;
                if (!Live(i)) { m_def[i] = null; m_inst[i] = null; m_tag[i] = null; continue; }
                var d = m_def[i];
                bool overHead = d.at == OverlayAt.Head || d.liftOverHead;
                float y = m_y[i] + (overHead ? stack : 0f);
                // feet overlays draw in front of the victim; head ones a touch further forward
                m_inst[i].transform.position = Pos(y, overHead ? 0.02f : 0f);
                if (overHead) stack += d.height * m_inst[i].transform.localScale.y + 1f;
            }
        }

        void LateUpdate()
        {
            if (m_count == 0) return;
            // indicators (not statuses) end with the character's life, and timed ones on their clock
            bool dead = m_health != null && !m_health.IsAlive();
            float now = Time.time;
            for (int i = 0; i < Max; i++)
            {
                var d = m_def[i];
                if (d == null || !d.indicator) continue;
                if (dead || (m_until[i] > 0f && now >= m_until[i])) Drop(i);
            }
            Place();
            Recount();
        }

        void OnDisable()
        {
            for (int i = 0; i < Max; i++) if (m_def[i] != null) Drop(i);
            m_count = 0;
        }
    }

    /// <summary>Marks which character an overlay instance belongs to (pooled instances get reused).</summary>
    internal class OverlayTag : MonoBehaviour
    {
        public StatusOverlays owner;
    }
}
