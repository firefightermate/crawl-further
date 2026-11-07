using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Tesla Spire's Any Rod Will Do: its bolt (1.1) comes from the Kaurn rod nearest the hero (within <see cref="Reach"/> px
    /// of him, clear line), never from where it stands unless there is none. The rod about to fire glows blue for
    /// <see cref="Warn"/> s. Every Rod Answers: it roots itself for 3 s and each rod within reach of the hero fires at him once
    /// a second (0.8).
    /// </summary>
    public class SpireRemote : KaurnBehaviour
    {
        public const float Reach = 100f, Warn = 0.3f, AnswerTime = 3f, Crown = 34f;
        public const int MaxAnswer = 4, Answers = 3;
        public static exSpriteAnimClip RootedClip;
        KrnNode m_from;

        Vector2 CrownPos { get { return Me + new Vector2(0f, Crown); } }

        static bool Post(KrnNode n) { return n.kind == KrnNode.Kind.Rod || n.kind == KrnNode.Kind.Stud || n.kind == KrnNode.Kind.Wisp; }

        List<KrnNode> RodsNearHero(int max)
        {
            Vector2 hc = HeroPos + new Vector2(0f, 8f);
            var o = new List<KrnNode>();
            foreach (var n in KrnNode.Snapshot())
                if (n != null && n.gameObject.activeInHierarchy && Post(n) && (n.Top - hc).sqrMagnitude <= Reach * Reach && ModUtil.Clear(n.Top, hc)) o.Add(n);
            o.Sort((x, y) => (x.Top - hc).sqrMagnitude.CompareTo((y.Top - hc).sqrMagnitude));
            if (o.Count > max) o.RemoveRange(max, o.Count - max);
            return o;
        }

        void Glow(KrnNode n)
        {
            if (KaurnFx.RodGlow == null) return;
            if (n != null) SystemPool.Spawn(KaurnFx.RodGlow, n.transform.position);
            else if (KaurnFx.RelayFlash != null) SystemPool.Spawn(KaurnFx.RelayFlash, CrownPos);
        }

        void Fire(KrnNode n, GameObject bolt)
        {
            if (bolt == null) return;
            var from = n != null && n.gameObject.activeInHierarchy ? n.Top : CrownPos;
            if (KaurnFx.RelayFlash != null) SystemPool.Spawn(KaurnFx.RelayFlash, from);
            FxFactory.SpawnOwned(bolt, from, Own, KaurnFx.Angle(from, HeroPos + new Vector2(0f, 8f)));
        }

        /// <summary>Clip event: pick the rod (its tip glows).</summary>
        public void KrnRemoteAim()
        {
            var rods = RodsNearHero(1);
            m_from = rods.Count > 0 ? rods[0] : null;
            Glow(m_from);
        }

        /// <summary>Clip event: the picked rod fires.</summary>
        public void KrnRemoteFire() { Fire(m_from, KaurnFx.Relay); m_from = null; }

        /// <summary>Clip event: it plants its legs and every rod answers.</summary>
        public void KrnAnswer() { StopAllCoroutines(); StartCoroutine(Answer()); }

        IEnumerator Answer()
        {
            Hold(RootedClip, AnswerTime);
            for (int k = 0; k < Answers && Alive; k++)
            {
                var rods = RodsNearHero(MaxAnswer);
                if (rods.Count == 0) Glow(null); else foreach (var n in rods) Glow(n);
                yield return new WaitForSeconds(Warn);
                if (!Alive) yield break;
                if (rods.Count == 0) Fire(null, KaurnFx.RelayAnswer);
                else foreach (var n in rods) Fire(n, KaurnFx.RelayAnswer);
                yield return new WaitForSeconds(AnswerTime / Answers - Warn);
            }
        }
    }
}
