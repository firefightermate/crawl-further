using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Gloom Lurker, Ambush: hidden after 1 s standing still or in darkness, and its bite from hiding hits twice as hard
    /// and may daze (ModMonster.ModAmbush). Tell: while hidden, only a faint outline of its eyes shows.
    /// </summary>
    public class LurkerEyes : UmbraelBehaviour
    {
        GameObject m_eyes;

        protected override void OnDisable() { base.OnDisable(); Drop(); }

        void Drop()
        {
            if (m_eyes != null) ModAttach.Drop(m_eyes, gameObject);
            m_eyes = null;
        }

        void Update()
        {
            bool show = Alive && Monster.Unseen;
            if (show && (m_eyes == null || !ModAttach.Owns(m_eyes, gameObject)))
                m_eyes = UmbraelFx.LurkEyes != null ? ModAttach.Spawn(UmbraelFx.LurkEyes, gameObject, Vector2.zero, 0.05f) : null;
            else if (!show && m_eyes != null) Drop();
        }
    }
}
