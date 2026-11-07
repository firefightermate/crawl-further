using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Eclipse Wyrm, Corona: Eclipse has the void head swallow the glass head; for 3 s it is a black disc with a burning
    /// white corona that burns a hero within 26 px (0.4 every 0.5 s) and moves 30 % faster. Then the glass head bursts out
    /// (1.2 round it). Tell: the corona. Basic 1 is the disc's harmless roll.
    /// </summary>
    public class WyrmEclipse : UmbraelBehaviour
    {
        public const float Length = 3f, Pulse = 0.5f, Haste = 1.3f;
        /// <summary>The disc and the burst (set by the kit).</summary>
        public static exSpriteAnimClip DiscClip, BurstClip;
        GameObject m_corona;

        protected override void OnDisable() { base.OnDisable(); DropCorona(); }

        void DropCorona()
        {
            if (m_corona != null) ModAttach.Drop(m_corona, gameObject);
            m_corona = null;
        }

        /// <summary>Clip event: the glass head is swallowed.</summary>
        public void ModUmbEclipse() { StopCoroutine("Eclipse"); StartCoroutine("Eclipse"); }

        IEnumerator Eclipse()
        {
            SetStance(DiscClip, DiscClip);
            SpeedScale(Haste);
            NextBasic(1);
            if (UmbraelFx.Corona != null) m_corona = ModAttach.Spawn(UmbraelFx.Corona, gameObject, Vector2.zero, 0.05f);
            for (float t = 0f; t < Length; t += Pulse)
            {
                if (UmbraelFx.CoronaHit != null && Alive) FxFactory.SpawnOwned(UmbraelFx.CoronaHit, Me, Own);
                yield return new WaitForSeconds(Pulse);
                if (!Alive) { DropCorona(); yield break; }
            }
            DropCorona();
            SetStance(null, null);
            SpeedScale(1f);
            NextBasic(0);
            Hold(BurstClip, 0.5f);
            if (UmbraelFx.EclipseBurst != null) FxFactory.SpawnOwned(UmbraelFx.EclipseBurst, Me, Own);
        }
    }
}
