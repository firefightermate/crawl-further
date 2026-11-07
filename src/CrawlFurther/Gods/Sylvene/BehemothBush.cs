using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Briar Behemoth, Dragged Bush: a thorn bush trails <see cref="Trail"/> px behind it on a vine and swings out round
    /// it when it turns sharply or stops (1.0, may bleed; the end of a Charge swings it harder, 1.2). Tell: the vine pulls
    /// taut for <see cref="TautTime"/> s before the swing.
    /// </summary>
    public class BehemothBush : SylveneBehaviour
    {
        public const float Trail = 20f, TautTime = 0.15f, Cooldown = 1.4f, TurnDeg = 80f;

        GameObject m_bush;
        exSpriteAnimation m_bushAnim;
        exSprite m_bushSprite;
        Vector2 m_bushPos, m_lastDir;
        float m_lastSpeed, m_ready, m_turnClock;
        bool m_swinging;

        protected override void OnEnable()
        {
            base.OnEnable();
            m_bush = null; m_swinging = false; m_ready = 0f; m_lastSpeed = 0f; m_lastDir = Vector2.zero;
        }

        protected override void OnDisable()
        {
            base.OnDisable();
            DropBush();
        }

        void Update()
        {
            if (!Alive) { DropBush(); return; }
            if (m_bush == null) SpawnBush();
            if (m_bush == null) return;
            var v = Move != null ? Move.GetVelocity() : Vector2.zero;
            float speed = v.magnitude;
            Vector2 dir = speed > 1f ? v / speed : (m_lastDir.sqrMagnitude > 0f ? m_lastDir : -Face);
            if (!m_swinging)
            {
                // the bush drags along behind on its vine
                Vector2 want = Me - dir * Trail;
                m_bushPos = Vector2.Lerp(m_bushPos, want, 1f - Mathf.Exp(-6f * Time.deltaTime));
                if ((m_bushPos - Me).magnitude > Trail + 6f) m_bushPos = Me + (m_bushPos - Me).normalized * (Trail + 6f);
                Place();
                if (Time.time >= m_ready && !InAttack)
                {
                    bool stopped = m_lastSpeed > 35f && speed < 8f;
                    bool turned = speed > 30f && m_lastDir.sqrMagnitude > 0f && Vector2.Angle(m_lastDir, dir) > TurnDeg;
                    if (stopped || turned) StartCoroutine(Swing(SylveneFx.BushSwing));
                }
            }
            if (speed > 1f)
            {
                // compare against the heading of a moment ago, so a sharp turn reads even when it takes a few frames
                m_turnClock += Time.deltaTime;
                if (m_turnClock > 0.12f) { m_lastDir = dir; m_turnClock = 0f; }
            }
            m_lastSpeed = Mathf.Lerp(m_lastSpeed, speed, 0.5f);
        }

        /// <summary>Clip event: the Charge skids to a stop and the bush swings in after it, harder.</summary>
        public void ModSylBushSlam()
        {
            if (!Alive || m_bush == null || m_swinging) return;
            StopAllCoroutines();
            StartCoroutine(Swing(SylveneFx.BushSwingBig));
        }

        IEnumerator Swing(GameObject hit)
        {
            m_swinging = true;
            m_ready = Time.time + Cooldown;
            if (m_bushAnim != null && SylveneFx.BushTaut != null) m_bushAnim.Play(SylveneFx.BushTaut);
            yield return new WaitForSeconds(TautTime);
            if (!Alive) { m_swinging = false; yield break; }
            if (hit != null) FxFactory.SpawnOwned(hit, Me, Own, Side < 0f ? 180f : 0f);
            if (m_bushSprite != null) m_bushSprite.enabled = false;
            yield return new WaitForSeconds(0.25f);
            m_bushPos = Me - Face * Trail;
            if (m_bushSprite != null) m_bushSprite.enabled = true;
            if (m_bushAnim != null && SylveneFx.BushDrag != null) m_bushAnim.Play(SylveneFx.BushDrag);
            Place();
            m_swinging = false;
        }

        void SpawnBush()
        {
            if (SylveneFx.Bush == null) return;
            m_bushPos = Me - Face * Trail;
            m_bush = SystemPool.Spawn(SylveneFx.Bush, m_bushPos);
            if (m_bush == null) return;
            m_bushAnim = m_bush.GetComponent<exSpriteAnimation>();
            m_bushSprite = m_bush.GetComponent<exSprite>();
            if (m_bushSprite != null) m_bushSprite.enabled = true;
            if (m_bushAnim != null)
            {
                if (SylveneFx.BushTaut != null && m_bushAnim.GetAnimation(SylveneFx.BushTaut.name) == null) m_bushAnim.AddAnimation(SylveneFx.BushTaut);
                if (SylveneFx.BushDrag != null) m_bushAnim.Play(SylveneFx.BushDrag);
            }
            Place();
        }

        void Place()
        {
            if (m_bush == null) return;
            var p = m_bush.transform.position;
            m_bush.transform.position = new Vector3(m_bushPos.x, m_bushPos.y, p.z);
            // the vine is drawn along +x: point it at the Behemoth
            var s = m_bush.transform.localScale;
            float sx = Me.x >= m_bushPos.x ? 1f : -1f;
            m_bush.transform.localScale = new Vector3(Mathf.Abs(s.x) * sx, s.y, s.z);
        }

        void DropBush()
        {
            if (m_bush == null) return;
            var b = m_bush;
            m_bush = null;
            if (b.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(b);
        }
    }
}
