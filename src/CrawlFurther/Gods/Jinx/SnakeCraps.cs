using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Snake-Eyes, luck both ways. Craps flicks two dice at the hero that hit for 0.2 per pip. Any other doubles flip
    /// another Wild Card and roll again (twice at most); but a craps roll (2, 3 or 12) and she has Crapped Out: she is
    /// dazed for <see cref="CrapTime"/> s, eyes crossed (the Dazed loop).
    /// </summary>
    public class SnakeCraps : JinxBehaviour
    {
        public const float CrapTime = 1.2f, PerPip = 0.2f;
        /// <summary>The crossed-eyes daze (set by the kit).</summary>
        public static exSpriteAnimClip DazedClip;

        /// <summary>Clip event: roll the dice.</summary>
        public void ModJinxCraps() { StopAllCoroutines(); StartCoroutine(Craps()); }

        IEnumerator Craps()
        {
            for (int roll = 0; roll < 3; roll++)
            {
                if (!Alive || JinxFx.SnakeDie == null) yield break;
                Vector2 from = ModUtil.SafePoint(Me, Me + new Vector2(12f * Side, 1f), 2f);
                float a = AngleTo(from, HeroPos);
                int r1 = Random.Range(1, 7), r2 = Random.Range(1, 7);
                Throw(from, a - 7f, r1);
                Throw(from, a + 7f, r2);
                int sum = r1 + r2;
                if (sum == 2 || sum == 3 || sum == 12)
                {
                    yield return new WaitForSeconds(0.25f);
                    Hold(DazedClip, CrapTime);
                    yield break;
                }
                if (r1 != r2 || roll == 2) yield break;
                yield return new WaitForSeconds(0.45f);
                SendMessage("ModWildCard", SendMessageOptions.DontRequireReceiver);
            }
        }

        void Throw(Vector2 from, float angle, int pips)
        {
            var go = FxFactory.SpawnOwned(JinxFx.SnakeDie, from, Own, angle);
            if (go == null) return;
            var d = go.GetComponent<DamageEffect>();
            if (d != null) R.Set(d, "m_damage", PerPip * pips);
            var spr = go.GetComponent<exSprite>();
            if (spr != null) spr.color = Color.Lerp(Color.white, new Color(1f, 0.55f, 0.4f), (pips - 1) / 5f);
            var rr = go.GetComponent<RollReadout>() ?? go.AddComponent<RollReadout>();
            rr.roll = pips; rr.max = 6; rr.fromSource = false;
        }
    }
}
