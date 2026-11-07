using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>One echo about to be queued: its owner's quirk may change the delay, add sites, or move them.</summary>
    public class EchoPlan
    {
        /// <summary>Seconds until it strikes (the perk's 0.6 s unless a quirk changes it).</summary>
        public float delay = 0.6f;
        /// <summary>Where it strikes; a quirk may add sites (each strikes) or move them.</summary>
        public readonly List<Vector2> sites = new List<Vector2>();
        /// <summary>The attack's own turn, kept for every site.</summary>
        public Quaternion rot;
        /// <summary>The attack template it echoes.</summary>
        public GameObject attack;
    }

    /// <summary>
    /// The one echo spawner for Umbrael's monsters (the god perk: every basic attack repeats 0.6 s later in the same spot
    /// for half damage). The rules that bend it all run here, in order: the owner's quirk plans the delay and the sites
    /// (Shade Imp, Twinned, Hollow King); when an echo strikes, a Glass Seraph nearby bends it toward the hero, and inside
    /// a Glassmoth's glitter it hits at full damage. An Hourglass that rewinds takes its pending echoes back with it.
    /// </summary>
    public class UmbraelEcho : MonoBehaviour
    {
        class Pending
        {
            public ModMonster owner;
            public GameObject half, whole;
            public Vector2 pos;
            public float z;
            public Quaternion rot;
            public Vector3 scale;
            public DamageSource src;
            public float at;
            public EchoPlan plan;
        }

        /// <summary>How far a Glass Seraph's light reaches, and how far it bends an echo.</summary>
        public const float BendRange = 60f, BendMax = 20f;

        static UmbraelEcho s_inst;
        static readonly Dictionary<GameObject, GameObject> s_attackOf = new Dictionary<GameObject, GameObject>();
        readonly List<Pending> m_pending = new List<Pending>();

        static UmbraelEcho I
        {
            get
            {
                if (s_inst == null)
                {
                    var go = new GameObject("CrawlFurther.UmbraelEcho");
                    DontDestroyOnLoad(go);
                    s_inst = go.AddComponent<UmbraelEcho>();
                }
                return s_inst;
            }
        }

        /// <summary>Link each half echo back to its attack (called once the templates are built).</summary>
        public static void Index()
        {
            s_attackOf.Clear();
            foreach (var kv in UmbraelFx.FullEcho)
            {
                var half = FxKit.FindEcho(kv.Key);
                if (half != null) s_attackOf[half] = kv.Key;
            }
        }

        /// <summary>Queue the echo of an attack an Umbrael monster just made (from <see cref="Patch_UmbraelEcho"/>).</summary>
        internal static void Queue(ModMonster mm, GameObject half, Vector3 pos, Quaternion rot, Vector3 scale, DamageSource src)
        {
            GameObject attack, whole = null;
            s_attackOf.TryGetValue(half, out attack);
            if (attack != null) UmbraelFx.FullEcho.TryGetValue(attack, out whole);
            var plan = new EchoPlan { rot = rot, attack = attack };
            plan.sites.Add(pos);
            var quirk = mm.GetComponent<UmbraelBehaviour>();
            if (quirk != null) quirk.PlanEcho(plan);
            var spr = mm.GetComponent<exSprite>();
            AfterimageFx.Spawn(spr, mm.transform.position, plan.delay + 0.15f);
            if (mm.Traits.echoFx != null) SystemPool.Spawn(mm.Traits.echoFx, mm.transform.position);
            foreach (var site in plan.sites)
                I.m_pending.Add(new Pending { owner = mm, half = half, whole = whole, pos = site, z = pos.z, rot = rot, scale = scale, src = src,
                                              at = Time.time + plan.delay, plan = plan });
        }

        /// <summary>The Hourglass snapped back: its pending echoes strike now, moved by <paramref name="offset"/>.</summary>
        public static void Rewind(ModMonster owner, Vector2 offset)
        {
            if (s_inst == null) return;
            foreach (var p in s_inst.m_pending)
                if (p.owner == owner) { p.pos += offset; p.at = Time.time; }
        }

        void Update()
        {
            for (int i = 0; i < m_pending.Count; i++)
            {
                var p = m_pending[i];
                if (Time.time < p.at) continue;
                m_pending.RemoveAt(i--);
                if (p.owner == null || !p.owner.gameObject.activeInHierarchy || p.half == null) continue;
                Fire(p);
            }
        }

        static void Fire(Pending p)
        {
            var site = p.pos;
            // a Glass Seraph's guiding light bends an echo near it toward the hero
            var hero = ModUtil.Hero();
            var seraph = SeraphLight.Nearest(site, BendRange, s => s.Alive);
            if (seraph != null && hero != null)
            {
                var to = (Vector2)hero.transform.position - site;
                site += Vector2.ClampMagnitude(to, BendMax);
                seraph.Thread(site);
            }
            // inside glitter an echo hits whole
            var tmpl = p.half;
            if (p.whole != null && GlitterFx.Covers(site))
            {
                tmpl = p.whole;
                if (UmbraelFx.EchoSparkle != null) SystemPool.Spawn(UmbraelFx.EchoSparkle, site);
            }
            var go = SystemPool.SpawnBegin(tmpl, new Vector3(site.x, site.y, p.z), p.rot);
            if (go == null) return;
            go.transform.localScale = p.scale;
            if (p.src != null)
                go.SendMessage(Constants.MSG_SETSPAWNER, new DamageSource(go, p.src.m_sourceOwner, p.src.m_sourcePlayer, -1, -1, p.src.m_damageMod, false),
                               SendMessageOptions.DontRequireReceiver);
            SystemPool.SpawnFinalize(go);
            var quirk = p.owner.GetComponent<UmbraelBehaviour>();
            if (quirk != null) quirk.EchoFired(go, site, p.plan);
        }
    }

    /// <summary>Umbrael's monsters queue their echoes through <see cref="UmbraelEcho"/> instead of Core's fixed one.</summary>
    [HarmonyLib.HarmonyPatch(typeof(ModMonster), "QueueEcho")]
    static class Patch_UmbraelEcho
    {
        // after Patch_CustomPerkNoEcho, which turns echoes off for starters lent to another god's perk
        [HarmonyLib.HarmonyPriority(HarmonyLib.Priority.Low)]
        static bool Prefix(ModMonster __instance, GameObject echoTemplate, Vector3 pos, Quaternion rot, Vector3 scale, DamageSource src,
                           bool __runOriginal)
        {
            if (!__runOriginal) return false;
            if (!(__instance.Traits is UmbraelTraits)) return true;
            UmbraelEcho.Queue(__instance, echoTemplate, pos, rot, scale, src);
            return false;
        }
    }
}
