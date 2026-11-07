using UnityEngine;

namespace CrawlFurther.Gods
{
    /// <summary>
    /// One row of a <see cref="SlotEditorUI"/>. Set the fields, then add it with SlotEditorUI.Add, which calls Build. The
    /// editor calls Refresh after every change and routes input to the focused row: Up / Down return true when the row
    /// used the press (a grid moving between its own rows), false to move focus to the next row.
    /// </summary>
    public abstract class EdRow
    {
        public SlotEditorUI ui;
        public GameObject root;
        /// <summary>Panel-local y of the row's centre (world units).</summary>
        public float y;
        public virtual bool Focusable { get { return true; } }
        public abstract void Build();
        public abstract void Refresh(bool focused);
        public virtual bool Up() { return false; }
        public virtual bool Down() { return false; }
        public virtual void Step(int dir) { }
        public virtual void Press() { }
        public virtual void Enter(int fromDir) { }
        public virtual bool Hover(Vector2 world) { return false; }
        public virtual void Click(Vector2 world) { Press(); }
        public virtual void Wheel(int dir) { Step(dir); }
        public virtual void Destroy() { if (root != null) UnityEngine.Object.Destroy(root); root = null; }

        protected static Rect Around(Transform t, float w, float h)
        {
            var p = t.position;
            return new Rect(p.x - w / 2f, p.y - h / 2f, w, h);
        }
    }
}
