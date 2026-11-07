namespace CrawlFurther.Content.Gods.Kaurn
{
    /// <summary>Coil Wisp's Relay: its arcs reach <see cref="Reach"/> px, not 70, and its coil glows while one is joined to it.</summary>
    public class WispRelay : KaurnBehaviour
    {
        public const float Reach = 110f;
        public static exSpriteAnimClip LinkedIdle, LinkedRun;
        bool m_lit;
        float m_check;

        protected override void OnEnable() { base.OnEnable(); Unit.linkRange = Reach; m_lit = false; m_check = 0f; }

        void Update()
        {
            m_check -= UnityEngine.Time.deltaTime;
            if (m_check > 0f) return;
            m_check = 0.15f;
            bool lit = KaurnConduction.Linked(Unit);
            if (lit == m_lit) return;
            m_lit = lit;
            SetStance(lit ? LinkedIdle : null, lit ? LinkedRun : null);
        }
    }
}
