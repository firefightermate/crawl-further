using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Ringmaster, Encore: a flaming hoop that comes back without hitting anything is thrown again at once, up to twice,
    /// faster each time. Tell: the encore hoop flares white-gold and he doffs his hat (when he is free to).
    /// </summary>
    public class RingmasterEncore : JinxBehaviour
    {
        public const int MaxEncores = 2;
        /// <summary>The hat-doffing flourish (set by the kit).</summary>
        public static exSpriteAnimClip EncoreClip;

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template == JinxFx.Hoop) Track(fx, 0);
        }

        void Track(GameObject hoop, int encore)
        {
            if (hoop == null) return;
            var h = hoop.GetComponent<HoopEncoreFx>() ?? hoop.AddComponent<HoopEncoreFx>();
            h.Bind(this, encore);
        }

        /// <summary>A hoop of generation <paramref name="encore"/> came back without hitting anything.</summary>
        public void HoopMissed(int encore)
        {
            if (!Alive || encore >= MaxEncores || JinxFx.HoopEncore == null || !gameObject.activeInHierarchy) return;
            StartCoroutine(Encore(encore));
        }

        IEnumerator Encore(int encore)
        {
            yield return null;
            var tmpl = JinxFx.HoopEncore[encore];
            if (!Alive || tmpl == null) yield break;
            Flourish(EncoreClip);
            Vector2 from = Me + new Vector2(11f * Side, 15f);
            var go = FxFactory.SpawnOwned(tmpl, from, Own, AngleTo(from, HeroPos + new Vector2(0f, 6f)));
            Track(go, encore + 1);
        }
    }
}
