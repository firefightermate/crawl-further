using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Sand Wraith, Held Time: Time Out hangs an hourglass over the hero for 3 s. Its top bulb drains with the real timer
    /// (twelve frames, picked from the clock, never from the animation's own pace) and is empty the moment the sand column
    /// falls on him. The Wraith's hits and echoes on him in those 3 s do nothing yet: they pile up in the glass (its eye
    /// lights up) and fall with the column, which carries all of them, +0.2 per hit held, on top of its own 0.5. The
    /// column's shadow marks his spot for the last 0.5 s, and he can step out of it.
    /// </summary>
    public class WraithHeldTime : UmbraelBehaviour
    {
        public const float Held = 3f, Shadow = 0.5f, PerHit = 0.2f, Base = 0.5f, GlassY = 26f;
        float m_start = -99f, m_until = -99f, m_held;
        int m_count, m_frame = -1;
        bool m_lit;
        GameObject m_glass, m_on;

        protected override void OnEnable() { base.OnEnable(); m_until = -99f; }
        protected override void OnDisable() { base.OnDisable(); DropGlass(); m_until = -99f; }

        void DropGlass()
        {
            if (m_glass != null && m_on != null) ModAttach.Drop(m_glass, m_on);
            m_glass = null;
            m_frame = -1;
        }

        /// <summary>Clip event: the hourglass is cast over him.</summary>
        public void ModUmbTimeOut()
        {
            var h = ModUtil.Hero();
            if (h == null) return;
            StopCoroutine("Release");
            DropGlass();
            m_on = h; m_held = 0f; m_count = 0; m_lit = false;
            m_start = Time.time;
            m_until = m_start + Held;
            if (UmbraelFx.SandGlass != null) m_glass = ModAttach.Spawn(UmbraelFx.SandGlass, h, new Vector2(0f, GlassY), 0.05f);
            ShowFrame();
            StartCoroutine("Release");
        }

        void Update() { if (m_glass != null) ShowFrame(); }

        /// <summary>The glass shows how much of the 3 s is left: frame i of 12 for the i-th twelfth.</summary>
        void ShowFrame()
        {
            var set = m_lit ? UmbraelFx.SandDrainHeld : UmbraelFx.SandDrain;
            if (set == null) return;
            int f = Mathf.Clamp((int)((Time.time - m_start) / Held * UmbraelFx.SandFrames), 0, UmbraelFx.SandFrames - 1);
            int key = f + (m_lit ? 100 : 0);
            if (key == m_frame) return;
            m_frame = key;
            UmbraelFx.Play(m_glass, set[f]);
        }

        public override bool HoldHitOnHero(DamageInfo d)
        {
            if (Time.time > m_until) return false;
            m_held += d.m_amount;
            m_count++;
            m_lit = true;
            return true;
        }

        IEnumerator Release()
        {
            yield return new WaitForSeconds(Held - Shadow);
            if (m_on == null || !Alive) { m_until = -99f; DropGlass(); yield break; }
            Vector2 at = m_on.transform.position;
            if (UmbraelFx.SandShadow != null) SystemPool.Spawn(UmbraelFx.SandShadow, at);
            yield return new WaitForSeconds(Shadow);
            m_until = -99f;
            DropGlass();
            if (UmbraelFx.SandColumn == null) yield break;
            var col = FxFactory.SpawnOwned(UmbraelFx.SandColumn, at, Own);
            var de = col != null ? col.GetComponent<DamageEffect>() : null;
            if (de != null) R.Set(de, "m_damage", Base + m_held + PerHit * m_count);
        }
    }
}
