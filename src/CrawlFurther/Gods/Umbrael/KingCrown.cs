using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The Hollow King, Court of One: Hollow Crown throws his crown to the floor by the hero. For 5 s a shadow king stands
    /// where it lies, and every echo of his cleaves strikes there instead, swung the same way: he fights in two places.
    /// Tell: the crown on the floor and the shadow king rising from it (he fights bare-headed meanwhile). Basic 0 is the
    /// crowned cleave, basic 1 the bare one.
    /// </summary>
    public class KingCrown : UmbraelBehaviour
    {
        public const float Court = 5f, Flight = 0.25f;
        /// <summary>The bare-headed idle and run (set by the kit).</summary>
        public static exSpriteAnimClip BareIdle, BareRun;

        GameObject m_shade;
        bool m_court;

        protected override void OnEnable() { base.OnEnable(); m_court = false; m_shade = null; }

        protected override void OnDisable()
        {
            base.OnDisable();
            if (m_shade != null && m_shade.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(m_shade);
            m_shade = null;
        }

        /// <summary>Clip event: the throw.</summary>
        public void ModUmbThrowCrown()
        {
            if (m_court) return;
            var to = Me - HeroPos;
            var land = ModUtil.SafePoint(HeroPos, HeroPos + (to.sqrMagnitude > 1f ? to.normalized : Vector2.left) * 10f, 4f);
            StartCoroutine(Throw(Me + new Vector2(Face.x >= 0f ? 10f : -10f, 18f), land));
        }

        IEnumerator Throw(Vector2 from, Vector2 land)
        {
            m_court = true;
            SetStance(BareIdle, BareRun);
            NextBasic(1);
            var crown = UmbraelFx.Crown != null ? SystemPool.Spawn(UmbraelFx.Crown, from) : null;
            for (float t = 0f; t < Flight; t += Time.deltaTime)
            {
                if (crown != null)
                {
                    var p = Vector2.Lerp(from, land, t / Flight) + new Vector2(0f, Mathf.Sin(t / Flight * Mathf.PI) * 10f);
                    crown.transform.position = new Vector3(p.x, p.y, crown.transform.position.z);
                }
                yield return null;
            }
            if (crown != null && crown.activeInHierarchy) SystemPool.Despawn(crown);
            if (UmbraelFx.CrownShade != null)
            {
                m_shade = SystemPool.Spawn(UmbraelFx.CrownShade, land);
                UmbraelFx.Play(m_shade, UmbraelFx.ShadeRise);
                yield return new WaitForSeconds(0.34f);
                UmbraelFx.Play(m_shade, UmbraelFx.ShadeIdle);
            }
            yield return new WaitForSeconds(Court - 0.34f);
            if (m_shade != null)
            {
                UmbraelFx.Play(m_shade, UmbraelFx.ShadeFade);
                yield return new WaitForSeconds(0.3f);
                if (m_shade.activeInHierarchy) SystemPool.Despawn(m_shade);
                m_shade = null;
            }
            m_court = false;
            SetStance(null, null);
            NextBasic(0);
        }

        public override void PlanEcho(EchoPlan plan)
        {
            if (m_shade == null || !m_shade.activeInHierarchy) return;
            var off = (Vector2)m_shade.transform.position - Me;
            for (int i = 0; i < plan.sites.Count; i++) plan.sites[i] += off;
        }

        public override void EchoFired(GameObject echo, Vector2 site, EchoPlan plan)
        {
            if (m_shade == null || !m_shade.activeInHierarchy) return;
            var s = m_shade.transform.localScale;
            m_shade.transform.localScale = new Vector3(Mathf.Abs(s.x) * (Face.x >= 0f ? 1f : -1f), s.y, s.z);
            StopCoroutine("Swing");
            StartCoroutine("Swing");
        }

        IEnumerator Swing()
        {
            UmbraelFx.Play(m_shade, UmbraelFx.ShadeSwing);
            yield return new WaitForSeconds(0.41f);
            if (m_shade != null && m_court) UmbraelFx.Play(m_shade, UmbraelFx.ShadeIdle);
        }
    }
}
