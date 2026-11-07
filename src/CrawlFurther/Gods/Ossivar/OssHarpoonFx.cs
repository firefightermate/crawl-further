using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;

    /// <summary>The Spinehook's harpoon in flight: the first bone pile it passes over is bitten and reeled in by its thrower.</summary>
    public class OssHarpoonFx : MonoBehaviour
    {
        /// <summary>It flies at chest height (Height px over the floor its piles lie on).</summary>
        public const float Bite = 8f, Height = 16f;
        bool m_done;
        void OnEnable() { m_done = false; }

        void Update()
        {
            if (m_done) return;
            var pile = BonePileFx.Nearest((Vector2)transform.position - new Vector2(0f, Height), Bite, p => !p.Locked);
            if (pile == null) return;
            m_done = true;
            var src = FxFactory.SourceOf(gameObject);
            var owner = src != null ? src.m_sourceOwner : null;
            var reel = owner != null ? owner.GetComponent<SpinehookReel>() : null;
            if (reel != null) reel.Reel(pile);
            SystemPool.Despawn(gameObject);
        }
    }
}
