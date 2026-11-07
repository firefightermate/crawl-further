using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Fortune Teller, Clouded Glass and Sealed Fate: the coming card is drawn as soon as Foretell is ready, and her
    /// crystal ball takes its colour (red Tower, gold Fool, blue Star). The fate mark then follows the hero for
    /// <see cref="FateMarkFx.TrackTime"/> s, its eye open, and seals where it is.
    /// </summary>
    public class TellerFate : JinxBehaviour
    {
        /// <summary>Per fate (Tower, Fool, Star): the idle, run and Foretell clips with the ball in its colour (set by the kit).</summary>
        public static exSpriteAnimClip[] FateIdle, FateRun, FateCast;

        int m_fate = -1;
        bool m_shown;

        protected override void OnEnable() { base.OnEnable(); m_fate = -1; m_shown = false; }

        void Update()
        {
            if (!Alive) return;
            bool ready = Body.HasSpecialAttack() && Body.GetSpecialReady();
            if (ready && m_fate < 0) m_fate = Random.Range(0, 3);
            bool show = m_fate >= 0 && (ready || InAttack);
            if (show == m_shown) return;
            m_shown = show;
            if (show && FateIdle != null)
            {
                SetStance(FateIdle[m_fate], FateRun[m_fate]);
                SetSpecialClip(FateCast[m_fate]);
            }
            else SetStance(null, null);
        }

        /// <summary>The fate the mark she just cast will turn (it is then spent).</summary>
        public int TakeFate()
        {
            int f = m_fate >= 0 ? m_fate : Random.Range(0, 3);
            m_fate = -1;
            return f;
        }

        /// <summary>Clip event: the mark lands under the hero.</summary>
        public void ModJinxForetell()
        {
            if (!Alive || JinxFx.FateMark == null) return;
            var go = FxFactory.SpawnOwned(JinxFx.FateMark, HeroPos, Own);
            var f = go != null ? go.GetComponent<FateMarkFx>() : null;
            if (f != null) f.Seal(TakeFate());
        }
    }
}
