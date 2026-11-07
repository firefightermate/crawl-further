using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Util;

    /// <summary>
    /// On a god-select panel: while the portrait shows the player's slot god, the god whose perk it uses is shown small
    /// at the portrait's bottom-right corner, so the panel says more than "Gold Idol" once the player is ready.
    /// Needs <see cref="SlotGods.PerkGodOf"/>.
    /// </summary>
    public class SlotGodBadge : MonoBehaviour
    {
        /// <summary>Size of the perk god's picture relative to the portrait.</summary>
        public const float Scale = 0.45f;

        MenuDeitySelectPlayer m_panel;
        exSpriteAnimation m_portrait;
        Renderer m_portraitR;
        exSprite m_badge;
        Renderer m_badgeR;
        int m_playerId = -1;

        internal static void Attach(MenuDeitySelectPlayer panel)
        {
            if (panel.GetComponent<SlotGodBadge>() != null) return;
            var b = panel.gameObject.AddComponent<SlotGodBadge>();
            b.m_panel = panel;
            b.m_playerId = R.Get<int>(panel, "m_playerId");
            b.m_portrait = R.Get<exSpriteAnimation>(panel, "m_portrait");
            b.m_portraitR = b.m_portrait != null ? b.m_portrait.GetComponent<Renderer>() : null;
        }

        void LateUpdate()
        {
            Deity perk = SlotGods.PerkGodOf != null ? PerkShown() : null;
            var clip = perk != null ? perk.GetPortraitAnim() : null;
            if (clip == null)
            {
                if (m_badgeR != null && m_badgeR.enabled) m_badgeR.enabled = false;
                return;
            }
            if (m_badge == null) Build();
            if (m_badge == null) return;
            SlotArt.Play(m_badge, clip);
            var b = m_portraitR.bounds;
            var t = m_badge.transform;
            var p = new Vector3(b.max.x, b.min.y + b.size.y * Scale * 0.5f, t.position.z);
            if ((t.position - p).sqrMagnitude > 0.0001f) t.position = p;
            if (!m_badgeR.enabled) m_badgeR.enabled = true;
        }

        /// <summary>The perk god of the slot god the portrait is showing right now, or null.</summary>
        Deity PerkShown()
        {
            if (m_portrait == null || m_portraitR == null || !m_portrait.gameObject.activeInHierarchy || !m_portraitR.enabled) return null;
            var pd = SystemPlayers.GetPlayer(m_playerId);
            var d = pd != null ? pd.GetDeity() : null;
            if (d == null) return null;
            var cur = m_portrait.GetCurrentAnimation();
            if (cur == null || cur.clip == null || cur.clip != d.GetPortraitAnim()) return null;
            return SlotGods.PerkGodOf(d);
        }

        void Build()
        {
            var spr = SlotArt.Sprite("ModSlotGodPerk", m_portrait.transform, new Vector3(0f, 0f, -1.2f), null);
            var ps = m_portrait.GetComponent<exSprite>();
            spr.scale = (ps != null ? ps.scale : Vector2.one) * Scale;
            m_badge = spr;
            m_badgeR = spr.GetComponent<Renderer>();
        }
    }
}
