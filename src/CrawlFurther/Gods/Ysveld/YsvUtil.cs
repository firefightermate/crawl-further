using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Small helpers the Ysveld effects share.</summary>
    static class YsvUtil
    {
        /// <summary>The monster that spawned an effect (its DamageSource owner).</summary>
        public static GameObject Owner(GameObject fx)
        {
            var src = FxFactory.SourceOf(fx);
            return src != null ? src.m_sourceOwner : null;
        }

        public static bool Alive(GameObject go)
        {
            if (go == null || !go.activeInHierarchy) return false;
            var h = go.GetComponent<Health>();
            return h == null || h.IsAlive();
        }

        /// <summary>Add frost pips to the hero from a source.</summary>
        public static void Rime(GameObject hero, DamageSource src, int pips = 1, bool ignoreGap = false)
        {
            var r = YsvRime.Of(hero);
            if (r != null) r.Add(src, pips, ignoreGap);
        }

        /// <summary>A damage source owned by <paramref name="monster"/> (for hits that are not effects).</summary>
        public static DamageSource Source(GameObject monster)
        {
            return ModUtil.BodySource(monster);
        }

        /// <summary>Hurt <paramref name="victim"/> directly; <paramref name="push"/> &gt; 0 also shoves it along dir.</summary>
        public static void Hurt(GameObject victim, float amount, Vector2 dir, DamageSource src, float push = 0f)
        {
            var h = victim != null ? victim.GetComponent<Health>() : null;
            if (h == null || !h.IsAlive() || src == null) return;
            var d = dir.sqrMagnitude > 0.01f ? dir.normalized : Vector2.right;
            h.Damage(new DamageInfo(amount, 0f, 0f, d, src), false);
            if (push <= 0f) return;
            var mv = victim.GetComponent<PlayerMovement>();
            if (mv != null) mv.AddImpulse(d * push);
        }

        /// <summary>The hero, if he is alive.</summary>
        public static GameObject LiveHero()
        {
            var hero = ModUtil.Hero();
            var h = hero != null ? hero.GetComponent<Health>() : null;
            return h != null && h.IsAlive() ? hero : null;
        }

        /// <summary>Play the anim named <paramref name="clip"/> on an effect instance (added to it first if needed).</summary>
        public static void Play(GameObject fx, exSpriteAnimClip clip)
        {
            var a = fx != null ? fx.GetComponent<exSpriteAnimation>() : null;
            if (a == null || clip == null) return;
            if (a.GetAnimation(clip.name) == null) a.AddAnimation(clip);
            a.Play(clip.name);
        }

        /// <summary>Put a floor-level visual at floor depth (under characters, just over the ice).</summary>
        public static GameObject Floor(GameObject tmpl, Vector2 at)
        {
            if (tmpl == null) return null;
            var go = SystemPool.Spawn(tmpl, at);
            if (go != null) go.transform.position = new Vector3(at.x, at.y, YsvFloor.FloorDepth(at));
            return go;
        }
    }
}
