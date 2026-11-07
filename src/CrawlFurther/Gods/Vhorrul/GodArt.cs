using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Vhorrul
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Mod art on vanilla melee swipes and hit splats, shared by every god pack.</summary>
    public static class GodArt
    {
        /// <summary>
        /// Reskin a vanilla melee swipe: the clone keeps its collider, layer, flip/rotate and DamageEffect; only the picture
        /// and its clip change (damage live on frame 0 like vanilla). (gx, gy) is the sheet's origin pixel, put on the
        /// effect's spawn point by Strike.ArtAt.
        /// </summary>
        public static void Swipe(GameObject go, string sheet, string anim, int gx, int gy)
        {
            if (go == null) return;
            var art = SpriteSheets.Get(sheet);
            if (art == null || !art.Has(anim)) { Plugin.Log.LogWarning("GodArt.Swipe " + go.name + ": missing " + sheet + "/" + anim); return; }
            FxFactory.StripChildren(go);
            var clip = new ClipBuilder(art, anim, go.name + "Clip").Once().Ev(0, "AnimDamageOn").Ev(1, "AnimDamageOff").Build();
            FxFactory.Reskin(go, clip, art);
            go.transform.localScale = Vector3.one;
            foreach (var s in go.GetComponentsInChildren<exSprite>(true)) s.color = Color.white;
            FxKit.NoTint(go);
            Strike.ArtAt(go, sheet, gx, gy);
        }

        /// <summary>
        /// A god's own hit splat: a clone of the vanilla BloodSplashGenericRandom (keeps its hit sound and layer) playing one
        /// of the sheet's two variants ("Play" / "Play2") at random, without the red tint or the vanilla ContactGenericSmall spark.
        /// </summary>
        public static GameObject HitSplat(string name, string sheet, int gx, int gy)
        {
            var art = SpriteSheets.Get(sheet);
            var go = FxFactory.Clone("BloodSplashGenericRandom", name);
            if (go == null || art == null || !art.Has("Play")) return null;
            FxFactory.StripChildren(go);
            var a = new ClipBuilder(art, "Play", name + "A").Once().Build();
            var b = art.Has("Play2") ? new ClipBuilder(art, "Play2", name + "B").Once().Build() : null;
            FxFactory.Reskin(go, a, art);
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, freeRotate: false);   // alsoSpawn (the vanilla spark) cleared
            var anim = go.GetComponent<exSpriteAnimation>();
            var eff = go.GetComponent<Effect>();
            if (anim != null && b != null && eff != null)
            {
                anim.animations = new List<exSpriteAnimClip> { a, b };
                R.Set(eff, "m_randomAnimation", true);
                R.Set(eff, "m_animationDefault", null);
            }
            FxKit.NoTint(go);
            foreach (var s in go.GetComponentsInChildren<exSprite>(true)) s.color = Color.white;
            Strike.ArtAt(go, sheet, gx, gy);
            return go;
        }

        /// <summary>Swap the vanilla red blood in a monster's m_spawnOnHit for the god's splat.</summary>
        public static void UseHitSplat(Player p, GameObject splat)
        {
            if (p == null || splat == null) return;
            var arr = R.Get<DamageEffectData[]>(p, "m_spawnOnHit");
            if (arr == null) return;
            foreach (var d in arr)
                if (d != null && d.m_object != null && d.m_object.name.StartsWith("BloodSplash")) d.m_object = splat;
        }
    }
}
