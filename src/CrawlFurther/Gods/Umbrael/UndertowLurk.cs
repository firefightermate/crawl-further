using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Undertow, Under a Friend: Lurk Beneath slips it into the ink under the nearest ally within 60 px. It rides there
    /// up to 4 s, moving with them and unhittable, biting out at a hero who comes close; two bites end it. The ink spreads
    /// as darkness under the ally, so the ally is hidden too. With no ally it sinks where it is for 3 s. Tell: an ink pool
    /// with two eyes under the ally's feet.
    /// </summary>
    public class UndertowLurk : UmbraelBehaviour
    {
        public const float Reach = 60f, Ride = 4f, Alone = 3f, BiteRange = 24f, BiteGap = 0.7f;
        /// <summary>The body's lurk, bite-out and surface clips (set by the kit).</summary>
        public static exSpriteAnimClip LurkClip, BiteClip, SurfaceClip;

        GameObject m_ink;
        Transform m_under;
        bool m_riding;

        protected override void OnEnable() { base.OnEnable(); m_riding = false; m_under = null; }
        protected override void OnDisable() { base.OnDisable(); DropInk(); m_riding = false; }

        void DropInk()
        {
            if (m_ink != null)
            {
                if (m_under != null) ModAttach.Drop(m_ink, m_under.gameObject);
                else if (m_ink.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(m_ink);
            }
            m_ink = null;
        }

        public override bool BlockHeroHit(DamageInfo d) { return m_riding; }

        /// <summary>Clip event: under the ink.</summary>
        public void ModUmbLurk()
        {
            if (m_riding) return;
            ModMonster ally = null; float best = Reach * Reach;
            foreach (var mm in FindObjectsOfType<ModMonster>())
            {
                if (mm == null || mm == Monster || !mm.Alive) continue;
                float d = ((Vector2)mm.transform.position - Me).sqrMagnitude;
                if (d < best) { best = d; ally = mm; }
            }
            StartCoroutine(Lurk(ally));
        }

        IEnumerator Lurk(ModMonster ally)
        {
            m_riding = true;
            BodyEvent("AnimStartInvincibility");
            BodyEvent("AnimCollideOff");
            m_under = ally != null ? ally.transform : null;
            if (UmbraelFx.InkUnder != null)
                m_ink = ally != null ? ModAttach.Spawn(UmbraelFx.InkUnder, ally.gameObject, Vector2.zero, -0.02f) : SystemPool.Spawn(UmbraelFx.InkUnder, Me);
            float end = Time.time + (ally != null ? Ride : Alone), next = 0f;
            int bites = 0;
            bool looped = false;
            Hold(LurkClip, end - Time.time);
            while (Time.time < end && bites < 2 && Alive)
            {
                if (!looped && m_ink != null && Time.time > end - (ally != null ? Ride : Alone) + 0.2f) { UmbraelFx.Play(m_ink, UmbraelFx.InkLoop); looped = true; }
                if (ally != null)
                {
                    if (!ally.Alive || !ally.gameObject.activeInHierarchy) break;
                    ModUtil.Teleport(gameObject, (Vector2)ally.transform.position + new Vector2(0f, -1f));
                    var to = HeroPos - Me;
                    if (Time.time >= next && to.sqrMagnitude < BiteRange * BiteRange)
                    {
                        next = Time.time + BiteGap;
                        bites++;
                        Monster.FaceHero();
                        Hold(BiteClip, 0.45f);
                        if (UmbraelFx.VenomBite != null) FxFactory.SpawnOwned(UmbraelFx.VenomBite, Me + to.normalized * 8f + new Vector2(0f, 8f), Own, AngleTo(Me, HeroPos));
                        yield return new WaitForSeconds(0.45f);
                        if (Time.time < end) Hold(LurkClip, end - Time.time);
                        continue;
                    }
                }
                yield return null;
            }
            if (m_ink != null) UmbraelFx.Play(m_ink, UmbraelFx.InkFade);
            yield return new WaitForSeconds(0.25f);
            DropInk();
            m_under = null;
            m_riding = false;
            BodyEvent("AnimStopInvincibility");
            BodyEvent("AnimCollideOn");
            if (Alive) Hold(SurfaceClip, 0.45f);
        }
    }
}
