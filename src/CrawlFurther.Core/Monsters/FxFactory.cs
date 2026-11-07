using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// Low-level effect template building: clone a vanilla effect prefab (to keep its physics layer, rigidbody, collider
    /// and DamageEffect wiring), then reskin and retune it. <see cref="FxKit"/> wraps the common cases.
    /// Custom components go on each spawned instance through <see cref="OnSpawn"/>, never on the template: Unity 5.4
    /// can't serialize plugin-assembly components on Instantiate.
    /// </summary>
    public static class FxFactory
    {
        static readonly Dictionary<string, GameObject> s_vanilla = new Dictionary<string, GameObject>();
        /// <summary>Every mod effect template by name.</summary>
        public static readonly Dictionary<string, GameObject> Templates = new Dictionary<string, GameObject>();
        /// <summary>Per-template hooks run on every spawned instance (add components here). Chain onto an existing hook
        /// rather than replacing it.</summary>
        public static readonly Dictionary<GameObject, Action<GameObject>> OnSpawn = new Dictionary<GameObject, Action<GameObject>>();
        static readonly Dictionary<string, Status> s_status = new Dictionary<string, Status>();

        /// <summary>The vanilla prefab named <paramref name="name"/> (an asset, not a scene object), or null (logged).</summary>
        public static GameObject Vanilla(string name)
        {
            GameObject g;
            if (s_vanilla.TryGetValue(name, out g) && g != null) return g;
            foreach (var go in Resources.FindObjectsOfTypeAll<GameObject>())
            {
                if (go.name != name || go.transform.parent != null) continue;
                if (go.scene.IsValid()) continue;          // prefab assets have no scene
                s_vanilla[name] = go;
                return go;
            }
            FurtherCore.Log.LogError("Vanilla prefab not found: " + name);
            return null;
        }

        /// <summary>A status by name, e.g. "StatusOnFire". The vanilla slows and daze come back as the timed
        /// <see cref="ModStatus"/> versions.</summary>
        public static Status GetStatus(string name)
        {
            Status s = ModStatus.Redirect(name);
            if (s != null) return s;
            if (s_status.TryGetValue(name, out s) && s != null) return s;
            foreach (var st in Resources.FindObjectsOfTypeAll<Status>())
                if (st.gameObject.name == name) { s_status[name] = st; return st; }
            FurtherCore.Log.LogWarning("Status not found: " + name);
            return null;
        }

        /// <summary>A new template cloned from vanilla <paramref name="vanillaName"/>, with its vanilla impact visuals
        /// replaced by the neutral mod puff (<see cref="ImpactFx"/>).</summary>
        public static GameObject Clone(string vanillaName, string newName)
        {
            var src = Vanilla(vanillaName);
            if (src == null) return null;
            var go = MonsterFactory.ClonePrefab(src, newName);
            Templates[newName] = go;
            ImpactFx.Sanitize(go);      // no vanilla impact visual (or the hero's damaging special burst) rides along on a mod clone
            return go;
        }

        /// <summary>
        /// A purely visual effect built from scratch (sprite + animation + Effect + depth sorting), for things
        /// like orbiting plates, flashes and bursts that never deal damage.
        /// </summary>
        public static GameObject Visual(string name, SpriteSheet sheet, exSpriteAnimClip clip, bool loop, float lifetime = 0f)
        {
            var go = new GameObject(name);
            go.transform.SetParent(MonsterFactory.Holder.transform, false);
            go.layer = 0;
            go.AddComponent<MeshFilter>();
            go.AddComponent<MeshRenderer>();
            var spr = go.AddComponent<exSprite>();
            spr.anchor = exPlane.Anchor.BotCenter;
            var anim = go.AddComponent<exSpriteAnimation>();
            if (clip != null) clip.wrapMode = loop ? WrapMode.Loop : WrapMode.Once;
            go.AddComponent<DepthHandler>();
            var eff = go.AddComponent<Effect>();
            Reskin(go, clip, sheet);
            SetEffect(go, destroyOnAnimEnd: !loop && lifetime <= 0f, destroyAfter: lifetime, canFlip: true, freeRotate: false);
            Templates[name] = go;
            return go;
        }

        /// <summary>Point the effect's sprite and animation at a mod clip.</summary>
        public static void Reskin(GameObject fx, exSpriteAnimClip clip, SpriteSheet sheet)
        {
            var anim = fx.GetComponent<exSpriteAnimation>();
            var spr = fx.GetComponent<exSprite>();
            if (spr != null && sheet != null && clip != null && clip.frameInfos.Count > 0)
            {
                spr.enabled = true;
                spr.SetSprite(sheet.atlas, clip.frameInfos[0].index);
                var rr = spr.GetComponent<Renderer>();
                if (rr != null && sheet.atlas.material != null) rr.sharedMaterial = sheet.atlas.material;
            }
            if (anim != null && clip != null)
            {
                anim.enabled = true;
                anim.animations = new List<exSpriteAnimClip> { clip };
                anim.defaultAnimation = clip;
                anim.playAutomatically = true;
            }
            var eff = fx.GetComponent<Effect>();
            if (eff != null)
            {
                R.Set(eff, "m_animationDefault", clip);
                R.Set(eff, "m_randomAnimation", false);
                R.Set(eff, "m_startFrame", new MinMaxRange(0f));
                var angles = R.F(typeof(Effect), "m_angleAnimations");
                var list = angles.GetValue(eff) as System.Collections.IList;
                if (list != null) list.Clear();
            }
        }

        /// <summary>Set the Effect's life and placement: despawn at the anim's end or after <paramref name="destroyAfter"/>
        /// seconds, offset in pixels, what it spawns when it ends, flip and rotation rules.</summary>
        public static void SetEffect(GameObject fx, bool destroyOnAnimEnd, float destroyAfter = 0f, float offsetX = 0f, float offsetY = 0f,
                                     GameObject spawnOnDestroy = null, GameObject alsoSpawn = null, bool? canFlip = null, float? snap = null, bool? freeRotate = null)
        {
            var e = fx.GetComponent<Effect>();
            if (e == null) return;
            R.Set(e, "m_destroyOnAnimEnd", destroyOnAnimEnd);
            R.Set(e, "m_destroyAfterTime", destroyAfter);
            R.Set(e, "m_offsetX", new MinMaxRange(offsetX));
            R.Set(e, "m_offsetY", new MinMaxRange(offsetY));
            R.Set(e, "m_spawnOnDestroy", spawnOnDestroy);
            R.Set(e, "m_alsoSpawn", alsoSpawn);
            if (canFlip.HasValue) R.Set(e, "m_canFlip", canFlip.Value);
            if (snap.HasValue) R.Set(e, "m_snap", snap.Value);
            if (freeRotate.HasValue) R.Set(e, "m_freeRotate", freeRotate.Value);
        }

        /// <summary>Set the DamageEffect's numbers: damage, seconds between ticks, knockback multiplier, status (always
        /// replaced) and its chance, stun seconds. Negative values keep what the clone had.</summary>
        public static void SetDamage(GameObject fx, float damage, float rate = -1f, float knockback = -1f, Status status = null,
                                     float statusChance = -1f, float stun = -1f, bool? collisionAtStart = null, bool? nullifyable = null,
                                     bool enabled = true)
        {
            var d = fx.GetComponent<DamageEffect>();
            if (d == null) return;
            d.enabled = enabled;
            R.Set(d, "m_damage", damage);
            if (rate >= 0f) R.Set(d, "m_damageRate", rate);
            if (knockback >= 0f) R.Set(d, "m_knockbackMultiplier", knockback);
            R.Set(d, "m_status", status);
            if (statusChance >= 0f) R.Set(d, "m_statusChance", statusChance);
            if (stun >= 0f) R.Set(d, "m_stunTime", stun);
            if (collisionAtStart.HasValue) R.Set(d, "m_collisionOnAtStart", collisionAtStart.Value);
            if (nullifyable.HasValue) R.Set(d, "m_nullifyable", nullifyable.Value);
        }

        /// <summary>Set the contact behaviour on every ContactData entry of the DamageEffect.</summary>
        public static void SetContacts(GameObject fx, bool? destroyOnHit = null, GameObject spawnOnHit = null, bool clearSpawnOnHit = false)
        {
            var d = fx.GetComponent<DamageEffect>();
            if (d == null) return;
            var arr = R.F(typeof(DamageEffect), "m_contactData").GetValue(d) as System.Collections.IEnumerable;   // List<ContactData>
            if (arr != null)
            foreach (var c in arr)
            {
                if (destroyOnHit.HasValue) R.Set(c, "m_destroyOnHit", destroyOnHit.Value);
                if (spawnOnHit != null || clearSpawnOnHit) R.Set(c, "m_spawnOnHit", spawnOnHit);
            }
            // legacy top-level fields too
            if (spawnOnHit != null || clearSpawnOnHit) R.Set(d, "m_spawnOnHit", spawnOnHit);
        }

        /// <summary>Set the ParticleMotion: speed and acceleration (pixels per second), trail objects, wall collision and bounce.</summary>
        public static void SetMotion(GameObject fx, float speed, float accel = 0f, float speedMax = 0f, GameObject trail = null,
                                     float trailDist = 50f, float trailTime = 0f, bool? collide = null, float bounce = -1f, bool enabled = true,
                                     float snapToZero = -1f)
        {
            var m = fx.GetComponent<ParticleMotion>();
            if (m == null) return;
            m.enabled = enabled;
            R.Set(m, "m_speed", new MinMaxRange(speed));
            R.Set(m, "m_accelleration", accel);
            R.Set(m, "m_speedMax", new MinMaxRange(speedMax));
            R.Set(m, "m_trailObject", trail);
            R.Set(m, "m_trailDropDistance", new MinMaxRange(trailDist));
            R.Set(m, "m_trailDropTime", new MinMaxRange(trailTime));
            if (collide.HasValue) R.Set(m, "m_collide", collide.Value);
            if (bounce >= 0f) R.Set(m, "m_bounce", bounce);
            if (snapToZero >= 0f) R.Set(m, "m_speedSnapToZero", snapToZero);
        }

        /// <summary>Set the StatusZone (a floor area that applies a status while stood in) and whom it affects.</summary>
        public static void SetStatusZone(GameObject fx, Status status, bool? hitsHero = null, bool? hitsMonster = null)
        {
            var z = fx.GetComponent<StatusZone>();
            if (z == null) return;
            if (status != null) R.Set(z, "m_status", status);
            if (hitsHero.HasValue) R.Set(z, "m_hitsHero", hitsHero.Value);
            if (hitsMonster.HasValue) R.Set(z, "m_hitsMonster", hitsMonster.Value);
        }

        /// <summary>Remove all child objects (old visuals like shadows/backs) from a template.</summary>
        public static void StripChildren(GameObject fx, params string[] keep)
        {
            var kill = new List<GameObject>();
            foreach (Transform t in fx.transform)
                if (Array.IndexOf(keep, t.name) < 0) kill.Add(t.gameObject);
            foreach (var k in kill) UnityEngine.Object.DestroyImmediate(k);
        }

        /// <summary>Spawn an effect at a point (pixels), turned <paramref name="angle"/> degrees, and hand it a copy of
        /// <paramref name="from"/> so its hits count as that monster's (or player's).</summary>
        public static GameObject SpawnOwned(GameObject template, Vector2 pos, DamageSource from, float angle = 0f)
        {
            var z = template.GetComponent<DepthHandler>() != null ? 0f : -10f;
            var go = SystemPool.SpawnBegin(template, new Vector3(pos.x, pos.y, z), Quaternion.Euler(0, 0, angle));
            if (go == null) return null;
            if (from != null)
            {
                go.SendMessage(Constants.MSG_SETSPAWNER, ModUtil.HandOn(from, go, keepAttack: true), SendMessageOptions.DontRequireReceiver);
            }
            SystemPool.SpawnFinalize(go);
            return go;
        }

        /// <summary>The damage source a spawned effect was handed, or null.</summary>
        public static DamageSource SourceOf(GameObject fx)
        {
            var d = fx.GetComponent<DamageEffect>();
            return d == null ? null : R.Get<DamageSource>(d, "m_source");
        }
    }
}
