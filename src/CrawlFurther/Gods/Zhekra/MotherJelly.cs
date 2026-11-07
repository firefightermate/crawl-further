using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Brood Mother, Royal Jelly: larvae within <see cref="Radius"/> px of her don't wither (<see cref="ZhkLarvaLife"/>).
    /// She feeds one at a time: that larva glows gold for <see cref="FeedTime"/> s, then becomes an Acid Grub. Tell: the
    /// gold glow on the larva and a thread of jelly from her mouthparts to it.
    /// </summary>
    public class MotherJelly : ZhkBehaviour
    {
        public const float Radius = 100f, FeedTime = 3f, Rest = 2.5f;
        static readonly List<MotherJelly> s_all = new List<MotherJelly>();

        float m_next;
        bool m_feeding;

        protected override void OnEnable() { base.OnEnable(); m_next = Time.time + Rest; m_feeding = false; if (!s_all.Contains(this)) s_all.Add(this); }
        protected override void OnDisable() { base.OnDisable(); s_all.Remove(this); m_feeding = false; }

        /// <summary>True if a living Brood Mother is within <paramref name="r"/> px of <paramref name="at"/>.</summary>
        public static bool Near(Vector2 at, float r)
        {
            for (int i = 0; i < s_all.Count; i++)
            {
                var m = s_all[i];
                if (m != null && m.Alive && ((Vector2)m.transform.position - at).sqrMagnitude <= r * r) return true;
            }
            return false;
        }

        Vector2 Mouth { get { return Me + new Vector2(14f * Side, 26f); } }

        void Update()
        {
            if (!Alive || m_feeding || Time.time < m_next) return;
            ZhkBrain pick = null; float best = Radius * Radius;
            foreach (var b in ZhkBrain.Snapshot())
            {
                if (b == null || !b.Alive || !b.IsLarva) continue;
                float d = (b.Pos - Me).sqrMagnitude;
                if (d < best) { best = d; pick = b; }
            }
            if (pick == null) { m_next = Time.time + 0.5f; return; }
            StartCoroutine(Feed(pick));
        }

        IEnumerator Feed(ZhkBrain larva)
        {
            m_feeding = true;
            ModInd.Set(larva.gameObject, ZhekraFx.JellyGlow, true, FeedTime);
            float beads = 0f;
            for (float t = 0f; t < FeedTime; t += Time.deltaTime)
            {
                if (!Alive || larva == null || !larva.Alive || (larva.Pos - Me).sqrMagnitude > Radius * Radius * 1.5f) { Done(larva); yield break; }
                beads -= Time.deltaTime;
                if (beads <= 0f && ZhekraFx.JellyBead != null)
                {
                    beads = 0.07f;
                    float f = (t * 3f) % 1f;
                    SystemPool.Spawn(ZhekraFx.JellyBead, Vector2.Lerp(Mouth, larva.Pos + new Vector2(0f, 3f), f));
                }
                yield return null;
            }
            Vector2 at = larva.Pos;
            Done(larva);
            larva.SendMessage("MsgDespawn", SendMessageOptions.DontRequireReceiver);
            if (ZhekraFx.GrublingSpawner != null) FxFactory.SpawnOwned(ZhekraFx.GrublingSpawner, at, Own);
            if (ZhekraFx.ResinPop != null) SystemPool.Spawn(ZhekraFx.ResinPop, at);
        }

        void Done(ZhkBrain larva)
        {
            m_feeding = false;
            m_next = Time.time + Rest;
            if (larva != null) ModInd.Set(larva.gameObject, ZhekraFx.JellyGlow, false);
        }
    }
}
