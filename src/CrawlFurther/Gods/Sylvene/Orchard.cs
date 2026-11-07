using System;
using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// The state the whole orchard shares: planting seeds, the hero's pollen dust (pods burst for him from
    /// <see cref="DustedRadius"/> px), the Sower's furrows, and the pods that burst on the hero (each one feeds every
    /// Rot Mother in the room).
    /// </summary>
    public static class Orchard
    {
        /// <summary>A pod bursting this close to the hero burst on him.</summary>
        public const float OnHero = 26f;
        /// <summary>How far a pod reaches for a hero dusted with pollen.</summary>
        public const float DustedRadius = 40f;

        static float s_dustUntil;
        static int s_furrow;

        /// <summary>True while the hero carries pollen dust (Pollen Monarch).</summary>
        public static bool HeroDusted { get { return Time.time < s_dustUntil && ModUtil.Hero() != null; } }

        /// <summary>Dust the hero for <paramref name="seconds"/> (the overlay shows for as long).</summary>
        public static void Dust(float seconds)
        {
            s_dustUntil = Mathf.Max(s_dustUntil, Time.time + seconds);
            var hero = ModUtil.Hero();
            if (hero != null && SylveneFx.DustInd != null) ModInd.Set(hero, SylveneFx.DustInd, true, s_dustUntil - Time.time);
        }

        /// <summary>Plant a seed from <paramref name="template"/> at <paramref name="at"/> (pulled back out of walls towards
        /// <paramref name="from"/>), owned by <paramref name="src"/>. Returns it, or null.</summary>
        public static SeedFx Plant(GameObject template, Vector2 from, Vector2 at, DamageSource src)
        {
            if (template == null) return null;
            var go = FxFactory.SpawnOwned(template, ModUtil.SafePoint(from, at, 3f), src);
            return go != null ? go.GetComponent<SeedFx>() : null;
        }

        /// <summary>A new furrow id for the seeds of one Sower pass.</summary>
        public static int NewFurrow() { return ++s_furrow; }

        /// <summary>Every seed of a furrow starts ripening again at once, so they ripen together.</summary>
        public static void RipenTogether(int furrow)
        {
            if (furrow == 0) return;
            foreach (var s in SeedFx.Snapshot()) if (s != null && s.furrow == furrow) s.Replant();
        }

        /// <summary>Burst every seed left in a furrow.</summary>
        public static void BurstFurrow(int furrow)
        {
            foreach (var s in SeedFx.Snapshot()) if (s != null && s.isActiveAndEnabled && s.furrow == furrow) s.Burst();
            Furrow.Wither(furrow);
        }

        /// <summary>A pod burst at <paramref name="at"/>: if it caught the hero, the orchard feeds the Rot Mothers.</summary>
        public static void PodBurst(Vector2 at)
        {
            var hero = ModUtil.Hero();
            if (hero == null || ((Vector2)hero.transform.position - at).sqrMagnitude > OnHero * OnHero) return;
            MotherFeed.Fed(at);
        }

        /// <summary>Run <paramref name="act"/> next frame. Effects that end inside a pool despawn must not spawn on the spot.</summary>
        public static void Later(Action act)
        {
            if (act == null || Plugin.I == null) return;
            Plugin.I.StartCoroutine(NextFrame(act));
        }

        static IEnumerator NextFrame(Action act)
        {
            yield return null;
            if (SystemMain.GetDeloadInProgress()) yield break;
            try { act(); }
            catch (Exception e) { Plugin.Log.LogError("Sylvene: " + e); }
        }
    }
}
