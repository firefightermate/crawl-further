using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>The Wild Card over the head of the Jinx monster that drew it (found where JinxMonster.ModWildCard spawned it:
    /// its feet + 18 px), following it for the 1.2 s the card shows, sorted in front of it.</summary>
    public class JinxCardOverHead : MonoBehaviour
    {
        public const float Lift = 3f;
        GameObject m_owner;

        public void Bind()
        {
            m_owner = null;
            Vector2 feet = (Vector2)transform.position - new Vector2(0f, 18f);
            float best = 2.5f * 2.5f;
            foreach (var mm in FindObjectsOfType<ModMonster>())
            {
                if (mm == null || !(mm.Traits is JinxTraits)) continue;
                float d = ((Vector2)mm.transform.position - feet).sqrMagnitude;
                if (d < best) { best = d; m_owner = mm.gameObject; }
            }
            LateUpdate();
        }

        void OnDisable() { m_owner = null; }

        void LateUpdate()
        {
            if (m_owner == null) return;
            if (!m_owner.activeInHierarchy) { m_owner = null; return; }
            var p = FloatNumber.OverHead(m_owner, Lift);
            transform.position = new Vector3(Mathf.Round(p.x), Mathf.Round(p.y), m_owner.transform.position.z - 0.06f);
        }
    }
}
