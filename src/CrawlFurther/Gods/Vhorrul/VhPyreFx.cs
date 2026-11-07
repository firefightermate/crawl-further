using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// A death pyre. While a living Pyre Warden stands within <see cref="WardenKeeper.KeepRange"/> px the pyre never cools:
    /// it is held in its Burn loop and wears a gold sigil flame over it (the tell).
    /// </summary>
    public class VhPyreFx : MonoBehaviour
    {
        // frame layout of the pyre clip: Ignite 2, Burn 3 x 9, Gutter 3
        const int BurnFirst = 2, GutterFirst = 2 + 27;

        exSpriteAnimation m_anim;
        GameObject m_sigil;
        float m_check;
        bool m_kept;

        public void Restart() { m_kept = false; m_check = 0f; DropSigil(); }
        void OnDisable() { DropSigil(); }

        void Update()
        {
            m_check -= Time.deltaTime;
            if (m_check > 0f) return;
            m_check = 0.1f;
            m_kept = WardenKeeper.Keeps(transform.position);
            if (m_kept && m_sigil == null && VhorrulFx.SigilFlame != null)
                m_sigil = ModAttach.Spawn(VhorrulFx.SigilFlame, gameObject, new Vector2(0f, 10f), 0.05f);
            else if (!m_kept) DropSigil();
            if (!m_kept) return;
            if (m_anim == null) m_anim = GetComponent<exSpriteAnimation>();
            var st = m_anim != null ? m_anim.GetCurrentAnimation() : null;
            if (st == null) return;
            // about to gutter: back to the start of the Burn loop
            if (m_anim.GetCurFrameIndex() >= GutterFirst - 2) m_anim.Play(st.clip, BurnFirst + 3);
        }

        void DropSigil()
        {
            if (m_sigil != null && m_sigil.activeInHierarchy) SystemPool.Despawn(m_sigil);
            m_sigil = null;
        }
    }
}
