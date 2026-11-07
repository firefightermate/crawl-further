using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// The Sundered, Torn: its pale half drifts to where the dark half was 1 s ago and can't be hit; a crack of light joins
    /// them. It fights too: when the dark half scissors, the pale half steps up beside it and cuts a beat later (its own
    /// Cut anim and <see cref="UmbraelFx.PaleCut"/> hitbox). Rejoin: the pale half swings out past the hero, then rushes back
    /// to the dark half in a straight line, cutting everything between.
    /// </summary>
    public class SunderedTorn : UmbraelBehaviour
    {
        public const float Lag = 1f, Rush = 0.25f, TorsoY = 18f, Gap = 12f;
        /// <summary>How fast the pale half eases back onto its trail (px/s) after a cut or a rush.</summary>
        public const float Follow = 150f;
        /// <summary>The pale cut: a step up beside the dark half (Flank px to its side), the wind-up frame, then the cut.</summary>
        public const float Step = 0.1f, Windup = 0.08f, CutRest = 0.43f, Flank = 10f, ChestY = 12f;
        /// <summary>Rejoin's set-up: the pale half swings out to Beyond px past the hero, then waits for the rush.</summary>
        public const float Beyond = 18f, Swing = 0.18f, SwingWait = 0.4f;
        /// <summary>The dark half alone, idle and running (set by the kit as the body's own idle and run).</summary>
        public static exSpriteAnimClip SoloIdle, SoloRun;
        readonly Queue<KeyValuePair<float, Vector2>> m_trail = new Queue<KeyValuePair<float, Vector2>>();
        GameObject m_pale, m_crack;
        exSpriteAnimClip m_playing;
        Coroutine m_swing, m_strike;
        Vector2 m_paleAt;
        float m_faceX = 1f;
        bool m_busy, m_rushing;

        protected override void OnEnable()
        {
            base.OnEnable();
            m_trail.Clear(); m_busy = m_rushing = false; m_swing = m_strike = null; m_paleAt = Me - Face * Gap;
        }

        protected override void OnDisable() { base.OnDisable(); Drop(); }

        void Drop()
        {
            bool live = !SystemMain.GetDeloadInProgress();
            if (m_pale != null && m_pale.activeInHierarchy && live) SystemPool.Despawn(m_pale);
            if (m_crack != null && m_crack.activeInHierarchy && live) SystemPool.Despawn(m_crack);
            m_pale = m_crack = null;
            m_playing = null;
        }

        void Update()
        {
            if (!Alive) { Drop(); return; }
            // a pooled half that something put away (a room change) is spawned again, never left missing
            if (m_pale != null && !m_pale.activeInHierarchy) { m_pale = null; m_playing = null; }
            if (m_crack != null && !m_crack.activeInHierarchy) m_crack = null;
            if (m_pale == null && UmbraelFx.PaleHalf != null) { m_pale = SystemPool.Spawn(UmbraelFx.PaleHalf, m_paleAt); m_trail.Clear(); }
            if (m_crack == null && UmbraelFx.Crack != null) m_crack = SystemPool.Spawn(UmbraelFx.Crack, Me);
            m_trail.Enqueue(new KeyValuePair<float, Vector2>(Time.time, Me));
            while (m_trail.Count > 1 && Time.time - m_trail.Peek().Key > Lag) m_trail.Dequeue();
            if (!m_busy)
            {
                var target = m_paleAt;
                if (m_trail.Count > 0 && Time.time - m_trail.Peek().Key >= Lag * 0.95f) target = m_trail.Peek().Value;
                // at rest it stands a pace behind, never inside the dark half
                if ((target - Me).sqrMagnitude < Gap * Gap) target = Me - Face * Gap;
                var was = m_paleAt;
                m_paleAt = Vector2.MoveTowards(m_paleAt, target, Follow * Time.deltaTime);
                float speed = (m_paleAt - was).magnitude / Mathf.Max(Time.deltaTime, 0.0001f);
                m_faceX = Face.x >= 0f ? 1f : -1f;
                Show(speed > 12f ? UmbraelFx.PaleDrift : UmbraelFx.PaleIdle);
            }
            Place();
        }

        void Show(exSpriteAnimClip clip, bool restart = false)
        {
            if (m_pale == null || clip == null || (clip == m_playing && !restart)) return;
            UmbraelFx.Play(m_pale, clip);
            m_playing = clip;
        }

        void FaceTo(Vector2 at) { if (Mathf.Abs(at.x - m_paleAt.x) > 0.5f) m_faceX = at.x >= m_paleAt.x ? 1f : -1f; }

        void Place()
        {
            if (m_pale != null)
            {
                m_pale.transform.position = new Vector3(m_paleAt.x, m_paleAt.y, m_pale.transform.position.z);
                var s = m_pale.transform.localScale;
                m_pale.transform.localScale = new Vector3(Mathf.Abs(s.x) * m_faceX, s.y, s.z);
            }
            if (m_crack != null) UmbraelFx.Span(m_crack, m_paleAt + new Vector2(0f, TorsoY), Me + new Vector2(0f, TorsoY));
        }

        // ------------------------------------------------------------------------------------- the pale half's own cut

        /// <summary>Clip event (Cross, as the sabres scissor): the pale half steps up beside the dark half and cuts.</summary>
        public void ModUmbPaleCut()
        {
            if (m_busy || m_pale == null || !Alive) return;
            m_strike = StartCoroutine(PaleStrike());
        }

        IEnumerator PaleStrike()
        {
            m_busy = true;
            var hero = HeroPos;
            var dir = hero - Me;
            dir = dir.sqrMagnitude > 1f ? dir.normalized : Face;
            // flank the dark half on the side the pale half already stands on, a step toward the hero
            // (straight behind: the far side, so the dark half and its hurtbox stay in front)
            var side = new Vector2(-dir.y, dir.x);
            float on = Vector2.Dot(m_paleAt - Me, side);
            if (Mathf.Abs(on) < 1f ? side.y < 0f : on < 0f) side = -side;
            Vector2 from = m_paleAt, to = Me + side * Flank;
            Show(UmbraelFx.PaleRush, true);
            for (float t = 0f; t < Step; t += Time.deltaTime)
            {
                m_paleAt = Vector2.Lerp(from, to, t / Step);
                FaceTo(hero);
                yield return null;
            }
            m_paleAt = to;
            hero = HeroPos;
            FaceTo(hero);
            Show(UmbraelFx.PaleCutClip, true);
            yield return new WaitForSeconds(Windup);
            if (Alive && UmbraelFx.PaleCut != null)
            {
                var aim = hero - m_paleAt;
                aim = aim.sqrMagnitude > 1f ? aim.normalized : dir;
                FxFactory.SpawnOwned(UmbraelFx.PaleCut, m_paleAt + new Vector2(0f, ChestY) + aim * 4f, Own, AngleTo(m_paleAt, hero));
            }
            yield return new WaitForSeconds(CutRest);
            m_strike = null;
            m_busy = false;
        }

        // ------------------------------------------------------------------------------------- Rejoin

        /// <summary>Clip event (Rejoin's brace): the pale half swings out past the hero, so the rush home runs through him.</summary>
        public void ModUmbRejoinSet()
        {
            if (m_rushing || m_pale == null || !Alive) return;
            if (m_strike != null) { StopCoroutine(m_strike); m_strike = null; }
            if (m_swing != null) StopCoroutine(m_swing);
            m_swing = StartCoroutine(SwingOut());
        }

        IEnumerator SwingOut()
        {
            m_busy = true;
            var hero = HeroPos;
            var d = hero - Me;
            d = d.sqrMagnitude > 1f ? d.normalized : Face;
            Vector2 from = m_paleAt, to = hero + d * Beyond;
            Show(UmbraelFx.PaleDrift, true);
            for (float t = 0f; t < Swing; t += Time.deltaTime)
            {
                // a shallow arc round the hero, not straight through him (that is the rush's job)
                float u = t / Swing;
                m_paleAt = Vector2.Lerp(from, to, u) + new Vector2(-d.y, d.x) * (Mathf.Sin(u * Mathf.PI) * 10f);
                FaceTo(Me);
                yield return null;
            }
            m_paleAt = to;
            FaceTo(Me);
            Show(UmbraelFx.PaleIdle);
            yield return new WaitForSeconds(SwingWait);
            // the special was cut short before the rush: go back to trailing
            m_swing = null;
            m_busy = false;
        }

        /// <summary>Clip event: the pale half rushes home.</summary>
        public void ModUmbRejoin()
        {
            if (m_rushing || m_pale == null) return;
            if (m_swing != null) { StopCoroutine(m_swing); m_swing = null; }
            StartCoroutine(RushHome());
        }

        IEnumerator RushHome()
        {
            m_rushing = m_busy = true;
            Show(UmbraelFx.PaleRush, true);
            Vector2 from = m_paleAt;
            FaceTo(Me);
            var hit = UmbraelFx.RejoinHit != null ? FxFactory.SpawnOwned(UmbraelFx.RejoinHit, from, Own) : null;
            int cuts = 0;
            for (float t = 0f; t < Rush; t += Time.deltaTime)
            {
                m_paleAt = Vector2.Lerp(from, Me, t / Rush);
                if (hit != null && hit.activeInHierarchy) hit.transform.position = new Vector3(m_paleAt.x, m_paleAt.y, hit.transform.position.z);
                if (UmbraelFx.RejoinCut != null && t / Rush >= cuts / 3f) { SystemPool.Spawn(UmbraelFx.RejoinCut, m_paleAt); cuts++; }
                yield return null;
            }
            m_paleAt = Me;
            m_trail.Clear();
            Show(UmbraelFx.PaleIdle);
            m_rushing = m_busy = false;
        }
    }
}
