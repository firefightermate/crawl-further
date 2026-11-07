using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Forge Colossus's Overheat: every slam and every Rod Fence adds heat (the furnace goes orange, then yellow). At
    /// <see cref="VentAt"/> it goes white, the chimney shrieks and it vents a blast of steam round itself (0.8, knockback),
    /// then stands cooled for <see cref="CoolTime"/> s: half speed, taking <see cref="CoolDamage"/>x damage.
    /// </summary>
    public class ColossusOverheat : KaurnBehaviour
    {
        public const int VentAt = 3;
        public const float CoolTime = 2f, CoolSpeed = 0.5f, CoolDamage = 1.3f, VentHold = 0.84f, VentBlast = 0.34f;
        public static exSpriteAnimClip HotIdle, HotRun, HotterIdle, HotterRun, ColdIdle, ColdRun, VentClip;
        int m_heat;
        bool m_venting, m_cold;
        float m_baseMult = 1f;

        protected override void Awake() { base.Awake(); if (Hp != null) m_baseMult = R.Get<float>(Hp, "m_vulnerableDamageMult"); }

        protected override void OnEnable() { base.OnEnable(); m_heat = 0; m_venting = m_cold = false; Vulnerable(false); }

        protected override void OnDisable() { base.OnDisable(); Vulnerable(false); }

        void Show()
        {
            if (m_cold) SetStance(ColdIdle, ColdRun);
            else if (m_heat >= 2) SetStance(HotterIdle, HotterRun);
            else if (m_heat == 1) SetStance(HotIdle, HotRun);
            else SetStance(null, null);
        }

        void Vulnerable(bool on)
        {
            if (Hp == null) return;
            R.Set(Hp, "m_vulnerableDamageMult", on ? CoolDamage : m_baseMult);
            if (on) Hp.AnimVulnerableOn(); else Hp.AnimVulnerableOff();
        }

        /// <summary>Clip event on a slam or a Rod Fence: one more step of heat.</summary>
        public void KrnHeat()
        {
            if (m_venting || m_cold) return;
            m_heat++;
            if (m_heat >= VentAt) StartCoroutine(Vent());
            else Show();
        }

        IEnumerator Vent()
        {
            m_venting = true;
            while (InAttack && Alive) yield return null;
            Hold(VentClip, VentHold);
            yield return new WaitForSeconds(VentBlast);
            if (KaurnFx.Steam != null) FxFactory.SpawnOwned(KaurnFx.Steam, Me, Own);
            yield return new WaitForSeconds(VentHold - VentBlast);
            m_heat = 0; m_venting = false; m_cold = true;
            Show(); SpeedScale(CoolSpeed); Vulnerable(true);
            yield return new WaitForSeconds(CoolTime);
            m_cold = false;
            Show(); SpeedScale(1f); Vulnerable(false);
        }
    }
}
