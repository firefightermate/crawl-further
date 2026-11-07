using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>A short-lived shadow copy of a sprite's current frame that fades out (the afterimage of an echoing attack).</summary>
    public class AfterimageFx : MonoBehaviour
    {
        float m_life = 0.6f;
        float m_t;
        exSprite m_spr;
        Color m_col;

        /// <summary>Leave an afterimage of <paramref name="src"/> at <paramref name="pos"/> that fades over
        /// <paramref name="life"/> seconds.</summary>
        public static void Spawn(exSprite src, Vector3 pos, float life)
        {
            if (src == null || src.atlas == null) return;
            var go = new GameObject("ModAfterimage");
            go.layer = src.gameObject.layer;
            go.transform.position = pos + new Vector3(0, 0, 0.5f);
            go.transform.localScale = src.transform.lossyScale;
            go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();
            var s = go.AddComponent<exSprite>();
            s.anchor = src.anchor;
            s.SetSprite(src.atlas, src.index);
            var a = go.AddComponent<AfterimageFx>();
            a.m_life = life;
            a.m_spr = s;
            a.m_col = new Color(0.45f, 0.25f, 0.75f, 0.75f);
            s.color = a.m_col;
        }

        void Update()
        {
            m_t += Time.deltaTime;
            if (m_spr != null) m_spr.color = new Color(m_col.r, m_col.g, m_col.b, m_col.a * Mathf.Clamp01(1f - m_t / m_life));
            if (m_t >= m_life) Destroy(gameObject);
        }
    }
}
