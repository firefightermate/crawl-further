using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;

    /// <summary>
    /// A monster melee arc wearing its own sheet. It clones the vanilla swipe it replaces
    /// (OrcSwipe / OrcSwipe2: collider, layer, attach and rotation behaviour kept), keeps that swipe's whoosh sound, and
    /// draws the sheet with its origin pixel (ox, oy) on the effect's origin, where the vanilla arc used to sit.
    /// Damage is live from <paramref name="damageFrame"/> for one frame, like the vanilla clip (on 0, off 0.117 s).
    /// Used by Sylvene, Umbrael and Jinx; Umbrael's Twice Struck echoes tint these arcs like any other template.
    /// </summary>
    internal static class GodsBArc
    {
        public static GameObject Swipe(string name, string vanilla, string art, string anim, int ox, int oy, float damage, float knock,
                                       Status status = null, float statusChance = 1f, float stun = -1f, int damageFrame = 0)
        {
            var go = FxFactory.Clone(vanilla, name);
            if (go == null) return null;
            var sh = SpriteSheets.Get(art);
            if (sh == null || !sh.Has(anim))
            {
                Plugin.Log.LogWarning("GodsBArc " + name + ": missing " + art + "/" + anim + ", keeping the vanilla arc");
                FxFactory.SetDamage(go, damage, knockback: knock, status: status, statusChance: statusChance, stun: stun);
                Strike.ArmSwipe2(go);
                return go;
            }
            Object whoosh = null;
            var an = go.GetComponent<exSpriteAnimation>();
            var old = an != null ? an.defaultAnimation : null;
            if (old != null && old.eventInfos != null)
                foreach (var e in old.eventInfos)
                    if (e != null && e.methodName == "AnimSound" && e.objectParam != null) { whoosh = e.objectParam; break; }
            FxFactory.StripChildren(go);
            var cb = new ClipBuilder(sh, anim, name + "Clip").Once().Ev(damageFrame, "AnimDamageOn").Ev(damageFrame + 1, "AnimDamageOff");
            if (whoosh != null) cb.EvO(0, "AnimSound", whoosh);
            FxFactory.Reskin(go, cb.Build(), sh);
            Strike.ArtAt(go, art, ox, oy);
            var spr = go.GetComponent<exSprite>();
            if (spr != null) spr.color = Color.white;
            FxFactory.SetEffect(go, destroyOnAnimEnd: true);
            FxFactory.SetDamage(go, damage, knockback: knock, status: status, statusChance: statusChance, stun: stun, collisionAtStart: false);
            FxKit.NoTint(go);
            return go;
        }
    }
}
