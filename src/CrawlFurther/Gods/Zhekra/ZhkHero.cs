using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// What Zhekra leaves on the hero, kept on the hero (not on the monster, so it carries on if that monster dies):
    /// the Botfly's Hatchery (while the egg is in him every hit he takes pops a larva, up to three), the Hornet's scent
    /// trail (a Marked hero leaves amber prints), and being lifted off the floor (Carry Off, Uproot).
    /// </summary>
    public class ZhkHero : MonoBehaviour
    {
        public const int MaxHatch = 3;
        public const float PrintStep = 9f;
        Health m_health;
        PlayerStatusManager m_sm;
        Player m_player;
        exSprite m_sprite;
        // Hatchery
        int m_eggs;
        DamageSource m_eggSrc;
        // scent
        Vector2 m_lastPrint;
        // lift
        float m_liftT, m_liftTime, m_liftH, m_lifted;
        GameObject m_shadow;

        public static ZhkHero On(GameObject hero)
        {
            if (hero == null) return null;
            return hero.GetComponent<ZhkHero>() ?? hero.AddComponent<ZhkHero>();
        }

        void Awake()
        {
            m_health = GetComponent<Health>();
            m_player = GetComponent<Player>();
            m_sm = m_player != null ? m_player.GetStatusManager() : null;
            m_sprite = GetComponent<exSprite>();
        }

        void OnDisable()
        {
            m_eggs = 0; m_eggSrc = null;
            EndLift();
        }

        bool Has(string cls) { return m_sm != null && m_sm.GetHasStatusWithClass(cls); }

        // ------------------------------------------------------------------ Hatchery
        /// <summary>The Botfly's egg went in: three larvae wait for the hits he takes.</summary>
        public void Implanted(DamageSource src)
        {
            m_eggs = MaxHatch;
            m_eggSrc = src;
            ModInd.Count(gameObject, ZhekraFx.Eggs, m_eggs);
        }

        /// <summary>He took a hit: while implanted it hatches a larva out of him.</summary>
        public void Struck(DamageInfo d)
        {
            if (m_eggs <= 0 || d == null || d.m_amount < 0.1f || !Has("ModZhkImplant")) return;
            m_eggs--;
            Vector2 at = transform.position;
            if (ZhekraFx.ImplantBurst != null) SystemPool.Spawn(ZhekraFx.ImplantBurst, at);
            if (ZhekraFx.LarvaFree != null)
            {
                var off = (Vector2)(Quaternion.Euler(0, 0, Random.Range(0f, 360f)) * Vector2.right) * 8f;
                FxFactory.SpawnOwned(ZhekraFx.LarvaFree, ModUtil.SafePoint(at, at + off), m_eggSrc);
            }
            ModInd.Count(gameObject, ZhekraFx.Eggs, m_eggs);
        }

        // ------------------------------------------------------------------ lift
        /// <summary>Lift him off the floor for <paramref name="seconds"/> (an arc <paramref name="height"/> px high): he can't
        /// act, his shadow stays on the floor.</summary>
        public void Lift(float seconds, float height)
        {
            m_liftT = 0f; m_liftTime = seconds; m_liftH = height;
            var mv = GetComponent<PlayerMovement>();
            if (mv != null) mv.InputOff("zhklift", seconds);
            if (m_player != null) m_player.Stun(seconds, false);
            if (m_shadow == null && ZhekraFx.CarryShadow != null) m_shadow = ModAttach.Spawn(ZhekraFx.CarryShadow, gameObject, Vector2.zero, -0.02f);
        }

        void EndLift()
        {
            if (m_sprite != null && m_lifted != 0f) m_sprite.offset = new Vector2(m_sprite.offset.x, m_sprite.offset.y - m_lifted);
            m_lifted = 0f; m_liftTime = 0f;
            ModAttach.Drop(m_shadow, gameObject);
            m_shadow = null;
        }

        void Update()
        {
            if (m_eggs > 0 && !Has("ModZhkImplant")) { m_eggs = 0; ModInd.Count(gameObject, ZhekraFx.Eggs, 0); }
            if (m_health == null || !m_health.IsAlive()) { if (m_liftTime > 0f) EndLift(); return; }
            // a Marked hero leaves a print every few steps
            if (Has("ModZhkMark") && ZhekraFx.Prints != null)
            {
                Vector2 p = transform.position;
                if ((p - m_lastPrint).sqrMagnitude >= PrintStep * PrintStep) { m_lastPrint = p; SystemPool.Spawn(ZhekraFx.Prints, p); }
            }
            else m_lastPrint = new Vector2(-9999f, -9999f);
            if (m_liftTime > 0f)
            {
                m_liftT += Time.deltaTime;
                float want = m_liftT >= m_liftTime ? 0f : Mathf.Sin(Mathf.Clamp01(m_liftT / m_liftTime) * Mathf.PI) * m_liftH;
                if (m_sprite != null) m_sprite.offset = new Vector2(m_sprite.offset.x, m_sprite.offset.y + want - m_lifted);
                m_lifted = want;
                if (m_liftT >= m_liftTime) EndLift();
            }
        }
    }

    /// <summary>Statuses Zhekra puts on the hero that need a component on him (the Botfly's implant, the Mark's scent).</summary>
    [HarmonyLib.HarmonyPatch(typeof(PlayerStatusManager), "AddStatus", new[] { typeof(Status), typeof(DamageSource), typeof(string) })]
    static class Patch_ZhkHeroStatus
    {
        static void Postfix(PlayerStatusManager __instance, Status status, DamageSource damageSource)
        {
            try
            {
                if (status == null || (status != ZhekraFx.Implant && status != ZhekraFx.Mark)) return;
                var who = StatusOverlays.Owner(__instance);
                if (who == null || who != ModUtil.Hero()) return;
                var h = ZhkHero.On(who);
                if (status == ZhekraFx.Implant && __instance.GetHasStatusWithClass("ModZhkImplant")) h.Implanted(damageSource);
            }
            catch (System.Exception e) { Plugin.Log.LogError("Zhekra hero status: " + e); }
        }
    }

    /// <summary>Hits the hero takes, for the Hatchery.</summary>
    [HarmonyLib.HarmonyPatch(typeof(Health), "Damage", new[] { typeof(DamageInfo), typeof(bool) })]
    static class Patch_ZhkHeroStruck
    {
        static void Postfix(Health __instance, DamageInfo damage, bool __result)
        {
            try
            {
                if (!__result || damage == null || damage.m_isDamageFromStatus) return;
                var h = __instance.GetComponent<ZhkHero>();
                if (h != null && __instance.gameObject == ModUtil.Hero()) h.Struck(damage);
            }
            catch (System.Exception e) { Plugin.Log.LogError("Zhekra hatchery: " + e); }
        }
    }
}
