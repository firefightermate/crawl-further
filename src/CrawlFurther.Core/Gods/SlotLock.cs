using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Util;

    /// <summary>
    /// The lock shown over a locked silver / gold slot's portrait (chains and a padlock), and the shake when a locked
    /// slot is confirmed. One per panel, a child of the panel's portrait.
    /// </summary>
    public class SlotLock : MonoBehaviour
    {
        exSprite m_spr;
        float m_shake;

        /// <summary>The panel's lock overlay (made on first use, hidden).</summary>
        public static SlotLock For(MenuDeitySelectPlayer panel)
        {
            var portrait = R.Get<exSpriteAnimation>(panel, "m_portrait");
            if (portrait == null) return null;
            var l = portrait.GetComponentInChildren<SlotLock>(true);
            if (l != null) return l;
            var spr = SlotArt.Sprite("ModSlotLock", portrait.transform, new Vector3(0f, 0f, -1.5f), SlotArt.Clip("SlotLockOverlay", "Idle"));
            spr.scale = portrait.GetComponent<exSprite>().scale;   // the portrait draws its 29 x 24 art at 0.8
            l = spr.gameObject.AddComponent<SlotLock>();
            l.m_spr = spr;
            spr.gameObject.SetActive(false);
            return l;
        }

        /// <summary>Show or hide the panel's lock overlay.</summary>
        public static void Show(MenuDeitySelectPlayer panel, bool on)
        {
            var l = For(panel);
            if (l != null && l.gameObject.activeSelf != on) l.gameObject.SetActive(on);
        }

        /// <summary>Confirming a locked slot: the padlock rattles and the portrait flashes red.</summary>
        public static void Deny(MenuDeitySelectPlayer panel)
        {
            var l = For(panel);
            if (l == null) return;
            l.gameObject.SetActive(true);
            l.m_shake = 0.3f;
            SlotArt.Play(l.m_spr, SlotArt.Clip("SlotLockOverlay", "Shake"));
            var portrait = R.Get<exSpriteAnimation>(panel, "m_portrait");
            var tint = portrait != null ? portrait.GetComponent<ColorTinterBase>() : null;
            if (tint != null) tint.StartFlash(new ColorTinterBase.FlashTintData { m_colour = SlotArt.Bad, m_duration = 0.24f, m_rate = 0.08f });
        }

        void Update()
        {
            if (m_shake <= 0f) return;
            m_shake -= Time.unscaledDeltaTime;
            if (m_shake <= 0f) SlotArt.Play(m_spr, SlotArt.Clip("SlotLockOverlay", "Idle"));
        }
    }
}
