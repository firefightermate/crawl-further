using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Fuse Sapper's Live Charges: a charge blows (1.3, 20 px) <see cref="Fuse"/> s after an arc reaches it, and an arc
    /// reaches it from any living Kaurn monster or post within 70 px (clear line), the Sapper included. It blinks faster as
    /// one comes within 110 px. Unreached, it fizzles after <see cref="Life"/> s.
    /// </summary>
    public class KrnChargeFx : MonoBehaviour
    {
        public const float Life = 8f, Fuse = 0.4f, Arm = 0.6f, Warn = 110f;
        static exSpriteAnimClip s_idle, s_blink, s_live, s_fizzle;
        readonly List<GameObject> m_segs = new List<GameObject>();
        exSpriteAnimation m_anim;
        float m_t, m_scan, m_fuse;
        Component m_by;
        float m_byHeight;
        int m_state;

        public void Reset()
        {
            m_t = 0f; m_scan = 0f; m_fuse = -1f; m_by = null; m_state = -1;
            m_anim = GetComponent<exSpriteAnimation>();
            if (s_idle == null)
            {
                s_idle = KaurnFx.Clip("FxKrnCharge", "Idle", true);
                s_blink = KaurnFx.Clip("FxKrnCharge", "Blink", true);
                s_live = KaurnFx.Clip("FxKrnCharge", "Live", true);
                s_fizzle = KaurnFx.Clip("FxKrnCharge", "Fizzle", false);
            }
        }

        void OnDisable() { KaurnFx.Clear(m_segs); }

        void Show(int state, exSpriteAnimClip clip)
        {
            if (state == m_state || m_anim == null || clip == null) return;
            m_state = state;
            if (m_anim.GetAnimation(clip.name) == null) m_anim.AddAnimation(clip);
            m_anim.Play(clip.name);
        }

        void Update()
        {
            m_t += Time.deltaTime;
            Vector2 me = transform.position;
            if (m_fuse >= 0f)
            {
                // the arc holds on until it blows
                if (m_by != null && m_by.gameObject.activeInHierarchy)
                    KaurnFx.Chain(m_segs, KaurnFx.ArcSeg, (Vector2)m_by.transform.position + new Vector2(0f, m_byHeight), me + new Vector2(0f, 5f), 8);
                m_fuse -= Time.deltaTime;
                if (m_fuse > 0f) return;
                if (KaurnFx.ChargeBlast != null) FxFactory.SpawnOwned(KaurnFx.ChargeBlast, me, FxFactory.SourceOf(gameObject));
                SystemPool.Despawn(gameObject);
                return;
            }
            if (m_t >= Life) { Show(3, s_fizzle); if (m_t >= Life + 0.45f) SystemPool.Despawn(gameObject); return; }
            m_scan -= Time.deltaTime;
            if (m_scan > 0f) return;
            m_scan = 0.1f;
            float best = Warn * Warn;
            Component by = null; float h = 0f;
            foreach (var u in KaurnUnit.All)
            {
                if (u == null || !u.Alive) continue;
                float d = (u.FeetPos - me).sqrMagnitude;
                if (d < best && ModUtil.Clear(u.FeetPos, me)) { best = d; by = u; h = u.height + (u.FeetPos.y - u.transform.position.y); }
            }
            foreach (var n in KrnNode.All)
            {
                if (n == null || !n.gameObject.activeInHierarchy || !n.Conducts) continue;
                float d = ((Vector2)n.transform.position - me).sqrMagnitude;
                if (d < best && ModUtil.Clear(n.transform.position, me)) { best = d; by = n; h = n.height; }
            }
            if (by != null && m_t >= Arm && best <= KaurnConduction.Range * KaurnConduction.Range)
            {
                m_by = by; m_byHeight = h; m_fuse = Fuse;
                Show(2, s_live);
                if (KaurnFx.HitFx != null) SystemPool.Spawn(KaurnFx.HitFx, me + new Vector2(0f, 5f));
                return;
            }
            if (by != null) Show(1, s_blink); else Show(0, s_idle);
        }
    }
}
