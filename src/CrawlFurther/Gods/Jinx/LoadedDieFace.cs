using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Loaded Die, Loaded: Tumble lands it on a face that it keeps, and its next slam stamps that face into the floor for
    /// <see cref="PerPip"/> a pip more. It is loaded: a 1 never stays up, it tips itself over onto the 6. Tell: the stored
    /// face floats over its head.
    /// </summary>
    public class LoadedDieFace : JinxBehaviour
    {
        public const float PerPip = 0.15f;

        int m_face;

        protected override void OnEnable() { base.OnEnable(); m_face = 0; }

        void Show()
        {
            if (JinxFx.Loaded != null) ModInd.Count(gameObject, JinxFx.Loaded, Alive ? m_face : 0);
        }

        /// <summary>Clip event: the tumble lands on a face.</summary>
        public void ModJinxLoad()
        {
            if (!Alive) return;
            m_face = Random.Range(1, 7);
            if (m_face == 1)
            {
                FloatNumber.RollOver(gameObject, 1, 6);
                m_face = 6;
                FloatNumber.RollOver(gameObject, 6, 6, 9f);
            }
            else FloatNumber.RollOver(gameObject, m_face, 6);
            Show();
        }

        /// <summary>Clip event: a slam with a loaded face stamps it into the floor in front.</summary>
        public void ModJinxLoadedSlam()
        {
            if (m_face <= 0 || JinxFx.Imprint == null || !Alive) return;
            var go = FxFactory.SpawnOwned(JinxFx.Imprint, ModUtil.SafePoint(Me, Me + Face * 12f, 2f), Own);
            var d = go != null ? go.GetComponent<DamageEffect>() : null;
            if (d != null) R.Set(d, "m_damage", PerPip * m_face);
            m_face = 0;
            Show();
        }
    }
}
