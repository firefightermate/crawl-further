using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Sun Scarab's rolling fossil ball. When it stops (a hit, a wall, the end of its roll) it cracks: the larvae
    /// caught in it jump out (they won't wither for <see cref="LarvaGrace"/> more seconds); an empty ball just splashes
    /// rooting resin.
    /// </summary>
    public class ZhkFossilFx : MonoBehaviour
    {
        public const float LarvaGrace = 4f;
        int m_brood;
        bool m_armed;
        DamageSource m_src;

        public void Arm(int brood) { m_brood = brood; m_armed = true; m_src = null; }

        void Start() { m_src = FxFactory.SourceOf(gameObject); }

        void OnDisable()
        {
            if (!m_armed || SystemMain.GetDeloadInProgress()) return;
            m_armed = false;
            Vector2 at = transform.position;
            var src = m_src ?? FxFactory.SourceOf(gameObject);
            if (m_brood <= 0)
            {
                if (ZhekraFx.CrackEmpty != null) FxFactory.SpawnOwned(ZhekraFx.CrackEmpty, at, src);
                return;
            }
            if (ZhekraFx.CrackBrood != null) SystemPool.Spawn(ZhekraFx.CrackBrood, at);
            for (int i = 0; i < m_brood && ZhekraFx.LarvaFree != null; i++)
            {
                var off = (Vector2)(Quaternion.Euler(0, 0, i * 120f + 30f) * Vector2.right) * 6f;
                FxFactory.SpawnOwned(ZhekraFx.LarvaFree, ModUtil.SafePoint(at, at + off), src);
            }
            ZhkGrace.After(at, 0.5f);
        }
    }
}
