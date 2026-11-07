using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Sand Wraith, Held Time: Time Out hangs an hourglass over the hero for 3 s. The Wraith's hits and echoes on him in
    /// those 3 s do nothing yet: they pile up in the glass, then fall as one sand column on his spot (all of it, +0.2 per
    /// hit held) after a 0.5 s shadow. He can step out of it. Tell: sand filling the glass.
    /// </summary>
    public class WraithHeldTime : UmbraelBehaviour
    {
        public const float Held = 3f, Shadow = 0.5f, PerHit = 0.2f, GlassY = 26f;
        float m_until = -99f, m_held;
        int m_count;
        GameObject m_glass, m_on;

        protected override void OnEnable() { base.OnEnable(); m_until = -99f; }
        protected override void OnDisable() { base.OnDisable(); DropGlass(); m_until = -99f; }

        void DropGlass()
        {
            if (m_glass != null && m_on != null) ModAttach.Drop(m_glass, m_on);
            m_glass = null;
        }

        /// <summary>Clip event: the hourglass is cast over him.</summary>
        public void ModUmbTimeOut()
        {
            var h = ModUtil.Hero();
            if (h == null) return;
            StopCoroutine("Release");
            DropGlass();
            m_on = h; m_held = 0f; m_count = 0;
            m_until = Time.time + Held;
            if (UmbraelFx.SandGlass != null) m_glass = ModAttach.Spawn(UmbraelFx.SandGlass, h, new Vector2(0f, GlassY), 0.05f);
            StartCoroutine("Release");
        }

        public override bool HoldHitOnHero(DamageInfo d)
        {
            if (Time.time > m_until) return false;
            m_held += d.m_amount;
            m_count++;
            if (m_glass != null && UmbraelFx.SandFill != null) UmbraelFx.Play(m_glass, UmbraelFx.SandFill[Mathf.Min(4, m_count)]);
            return true;
        }

        IEnumerator Release()
        {
            yield return new WaitForSeconds(Held);
            m_until = -99f;
            DropGlass();
            if (m_count == 0 || m_on == null || !Alive) yield break;
            Vector2 at = m_on.transform.position;
            if (UmbraelFx.SandShadow != null) SystemPool.Spawn(UmbraelFx.SandShadow, at);
            yield return new WaitForSeconds(Shadow);
            if (UmbraelFx.SandColumn == null) yield break;
            var col = FxFactory.SpawnOwned(UmbraelFx.SandColumn, at, Own);
            var de = col != null ? col.GetComponent<DamageEffect>() : null;
            if (de != null) R.Set(de, "m_damage", m_held + PerHit * m_count);
        }
    }
}
