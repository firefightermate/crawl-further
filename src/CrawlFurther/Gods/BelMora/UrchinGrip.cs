namespace CrawlFurther.Content.Gods.BelMora
{
    /// <summary>
    /// Bell Urchin, Tube Feet: standing in brine its tube feet grip the floor and nothing knocks it back
    /// (<see cref="Patch_BelMoraGrip"/>). Tell: the feet splay out pale round its base in a ring of foam (the Grip idle).
    /// </summary>
    public class UrchinGrip : BelBehaviour
    {
        /// <summary>The idle shown while it grips (set by the kit).</summary>
        public static exSpriteAnimClip GripIdle;

        float m_scan;

        /// <summary>True while it stands in brine.</summary>
        public bool Gripping { get; private set; }

        protected override void OnEnable() { base.OnEnable(); Gripping = false; m_scan = 0f; }

        void Update()
        {
            if (!Alive) return;
            m_scan -= UnityEngine.Time.deltaTime;
            if (m_scan > 0f) return;
            m_scan = 0.15f;
            bool g = BelWater.InBrine(Feet);
            if (g == Gripping) return;
            Gripping = g;
            SetStance(g ? GripIdle : null, null);
        }
    }

    /// <summary>A gripping Bell Urchin takes no knockback (the push is zeroed before the game applies it).</summary>
    [HarmonyLib.HarmonyPatch(typeof(Player), "Knockback")]
    static class Patch_BelMoraGrip
    {
        static void Prefix(Player __instance, ref float knockbackMultiplier)
        {
            var g = __instance != null ? __instance.GetComponent<UrchinGrip>() : null;
            if (g != null && g.Alive && g.Gripping) knockbackMultiplier = 0f;
        }
    }
}
