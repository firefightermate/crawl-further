using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// Keeps a visual drawn just in front of a character, and optionally makes it follow the character's feet.
    /// DepthHandler sorts an effect by its own height, so anything placed up the body (a mark at the chest, an orbiting
    /// plate) would otherwise sort behind the body and be hidden by it. A following visual despawns itself when the
    /// character is gone or (dieWithTarget) dead. Pool-safe: the binding is cleared on recycle and disable.
    /// </summary>
    public class ModAttach : MonoBehaviour
    {
        Transform m_to;
        Health m_hp;
        Vector2 m_off;
        bool m_follow, m_dieWith;
        float m_dz;

        /// <summary>Sort <paramref name="fx"/> in front of <paramref name="to"/> without moving it (e.g. a parented visual).</summary>
        public static void Front(GameObject fx, GameObject to, float dz = 0.03f) { Bind(fx, to, false, Vector2.zero, dz, false); }

        /// <summary>Spawn <paramref name="tmpl"/> so it follows <paramref name="to"/>'s feet (plus <paramref name="offset"/>
        /// pixels) in front of it. Returns the instance, or null.</summary>
        public static GameObject Spawn(GameObject tmpl, GameObject to, Vector2 offset, float dz = 0.03f, bool dieWithTarget = true)
        {
            if (tmpl == null || to == null) return null;
            var go = SystemPool.Spawn(tmpl, (Vector2)to.transform.position + offset);
            Bind(go, to, true, offset, dz, dieWithTarget);
            return go;
        }

        static void Bind(GameObject fx, GameObject to, bool follow, Vector2 off, float dz, bool dieWith)
        {
            if (fx == null || to == null) return;
            var a = fx.GetComponent<ModAttach>() ?? fx.AddComponent<ModAttach>();
            a.m_to = to.transform; a.m_hp = to.GetComponent<Health>(); a.m_off = off; a.m_follow = follow; a.m_dz = dz; a.m_dieWith = dieWith;
            a.enabled = true;
            a.LateUpdate();
        }

        /// <summary>True while <paramref name="fx"/> is a live visual bound to <paramref name="to"/> (not a pooled copy reused elsewhere).</summary>
        public static bool Owns(GameObject fx, GameObject to)
        {
            var a = fx != null && fx.activeInHierarchy ? fx.GetComponent<ModAttach>() : null;
            return a != null && to != null && a.m_to == to.transform;
        }

        /// <summary>Despawn <paramref name="fx"/> if it is still bound to <paramref name="to"/>.</summary>
        public static void Drop(GameObject fx, GameObject to)
        {
            if (!Owns(fx, to)) return;
            fx.GetComponent<ModAttach>().m_to = null;
            if (!SystemMain.GetDeloadInProgress()) SystemPool.Despawn(fx);
        }

        void LateUpdate()
        {
            if (m_to == null) return;
            bool gone = !m_to.gameObject.activeInHierarchy || (m_dieWith && m_hp != null && !m_hp.IsAlive());
            if (gone)
            {
                m_to = null;
                if (m_follow) SystemPool.Despawn(gameObject);
                return;
            }
            var p = m_follow ? (Vector2)m_to.position + m_off : (Vector2)transform.position;
            transform.position = new Vector3(p.x, p.y, m_to.position.z - m_dz);
        }

        // SystemPool sends Recycle when it reuses the instance
        void Recycle(GameObject prefab) { m_to = null; }
        void OnDisable() { m_to = null; }
    }
}
