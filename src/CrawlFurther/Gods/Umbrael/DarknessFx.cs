using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;

    /// <summary>
    /// A pool of darkness. Umbrael monsters inside it are nearly invisible. A Gloamcoil lying in it makes it spread
    /// (<see cref="Grow"/>): its creeping edge is drawn by an overlay that keeps up with the radius.
    /// </summary>
    public class DarknessFx : Registered<DarknessFx>
    {
        public float radius = 22f;
        float m_base;
        GameObject m_edge;
        int m_edgeStep = -1;

        /// <summary>Start a fresh pool of <paramref name="r"/> px (pooled instances come back through here).</summary>
        public void Reset(float r)
        {
            radius = m_base = r;
            DropEdge();
        }

        /// <summary>True if <paramref name="p"/> lies inside any darkness pool.</summary>
        public static bool Covers(Vector2 p)
        {
            for (int i = 0; i < All.Count; i++)
                if (All[i] != null && (All[i].Pos - p).sqrMagnitude < All[i].radius * All[i].radius) return true;
            return false;
        }

        /// <summary>The pool covering <paramref name="p"/>, or null.</summary>
        public static DarknessFx At(Vector2 p)
        {
            for (int i = 0; i < All.Count; i++)
                if (All[i] != null && (All[i].Pos - p).sqrMagnitude < All[i].radius * All[i].radius) return All[i];
            return null;
        }

        /// <summary>Spread by <paramref name="px"/>, up to <paramref name="max"/> px of radius.</summary>
        public void Grow(float px, float max)
        {
            if (radius >= max) return;
            radius = Mathf.Min(max, radius + px);
            var clips = UmbraelFx.DuskEdges;
            if (UmbraelFx.DuskEdge == null || clips == null) return;
            int step = -1;
            for (int i = 0; i < UmbraelFx.DuskRadii.Length; i++) if (radius >= UmbraelFx.DuskRadii[i] - 2) step = i;
            if (step < 0 || step == m_edgeStep) return;
            if (m_edge == null || !m_edge.activeInHierarchy) m_edge = SystemPool.Spawn(UmbraelFx.DuskEdge, Pos);
            if (m_edge == null) return;
            m_edgeStep = step;
            var an = m_edge.GetComponent<exSpriteAnimation>();
            var clip = clips[step];
            if (an == null || clip == null) return;
            if (an.GetAnimation(clip.name) == null) an.AddAnimation(clip);
            an.Play(clip.name);
        }

        void LateUpdate()
        {
            if (m_edge == null) return;
            if (!m_edge.activeInHierarchy) { m_edge = null; m_edgeStep = -1; return; }
            var p = transform.position;
            m_edge.transform.position = new Vector3(p.x, p.y, m_edge.transform.position.z);
        }

        protected override void OnDisable()
        {
            base.OnDisable();
            DropEdge();
        }

        void DropEdge()
        {
            if (m_edge != null && m_edge.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(m_edge);
            m_edge = null;
            m_edgeStep = -1;
            if (m_base > 0f) radius = m_base;
        }
    }
}
