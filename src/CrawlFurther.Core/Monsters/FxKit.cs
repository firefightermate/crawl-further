using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// Ready-made effect templates for kits: projectiles, melee hitboxes, body hits, visuals, ground effects, minion
    /// spawners. Most clone a vanilla effect (keeping its layer, rigidbody, collider and DamageEffect wiring) and dresses
    /// it in mod art; names should start with "Mod". Damage is in the game's health units, knockback a multiplier, speeds
    /// in pixels per second, times in seconds. A status may be null; statusChance is 0..1.
    /// </summary>
    public static class FxKit
    {
        /// <summary>Switch off the vanilla ColorTinter, which would recolour mod art.</summary>
        public static void NoTint(GameObject go) { var t = go.GetComponent<ColorTinter>(); if (t != null) t.enabled = false; }

        /// <summary>
        /// A flying projectile reskinned from vanilla <paramref name="vanilla"/> (e.g. "DFX_skelMageNewProjectile"), playing
        /// <paramref name="anim"/> of sheet <paramref name="art"/> in a loop. It keeps the vanilla collider and layer; its
        /// wall and body contacts spawn the impact puff themed for its sheet (see <see cref="ImpactFx"/>).
        /// </summary>
        public static GameObject Projectile(string name, string vanilla, string art, string anim, float speed, float life,
                                            float damage, float knock, Status status = null, float statusChance = 1f,
                                            float accel = 0f, float speedMax = 0f, bool rotate = true, bool destroyOnHit = true)
        {
            var sh = SpriteSheets.Get(art);
            var go = FxFactory.Clone(vanilla, name);
            if (go == null) return null;
            var clip = new ClipBuilder(sh, anim, name + "Fly").Loop().Build();
            FxFactory.Reskin(go, clip, sh);
            FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: life, freeRotate: rotate);
            foreach (var m in go.GetComponents<ParticleMotion>()) R.Set(m, "m_trailObject", null);
            FxFactory.SetMotion(go, speed, accel: accel, speedMax: speedMax);
            FxFactory.SetDamage(go, damage, knockback: knock, status: status, statusChance: statusChance, collisionAtStart: true);
            FxFactory.SetContacts(go, destroyOnHit: destroyOnHit);
            // webBall's player contact spawns WebEffectZone (vanilla StatusStuckToFloor: no attacking, outside the
            // CC guard). Never inherit a status-zone spawn; callers that want an on-hit spawn set their own after.
            var de = go.GetComponent<DamageEffect>();
            if (de != null && de.m_contactData != null)
                foreach (var c in de.m_contactData)
                    if (c != null && c.m_spawnOnHit != null && c.m_spawnOnHit.GetComponent<StatusZone>() != null) c.m_spawnOnHit = null;
            // wall and body contacts: the impact puff themed for the art sheet, never the vanilla spark
            ImpactFx.ThemeProjectile(go, art);
            NoTint(go);
            return go;
        }

        /// <summary>A melee hitbox reusing a vanilla swipe (its own art and damage timing) with new numbers.
        /// <paramref name="stun"/>: seconds, below 0 keeps the vanilla value.</summary>
        public static GameObject Swipe(string name, string vanilla, float damage, float knock, Status status = null, float statusChance = 1f, float stun = -1f)
        {
            var go = FxFactory.Clone(vanilla, name);
            if (go == null) return null;
            FxFactory.SetDamage(go, damage, knockback: knock, status: status, statusChance: statusChance, stun: stun);
            return go;
        }

        /// <summary>An invisible hitbox that stays live for <paramref name="life"/> seconds (attach it for dashes and rolls);
        /// <paramref name="rate"/>: seconds between hits on the same target. Size it with <see cref="Strike.HitBox"/>.</summary>
        public static GameObject BodyHit(string name, float damage, float rate, float knock, float life, Status status = null, float statusChance = 1f)
        {
            var go = FxFactory.Clone("DamageGiantRatAttack", name);
            if (go == null) return null;
            FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: life);
            FxFactory.SetDamage(go, damage, rate: rate, knockback: knock, status: status, statusChance: statusChance);
            return go;
        }

        /// <summary>A pure visual from a mod sheet (no damage): flashes, auras, markers. <paramref name="lifetime"/> &gt; 0
        /// despawns it after that many seconds; <paramref name="durations"/> overrides the frame times.</summary>
        public static GameObject Visual(string name, string art, string anim, bool loop = false, float lifetime = 0f, params float[] durations)
        {
            var sh = SpriteSheets.Get(art);
            if (sh == null || !sh.Has(anim)) { FurtherCore.Log.LogWarning("Visual " + name + ": missing " + art + "/" + anim); return null; }
            var cb = new ClipBuilder(sh, anim, name + "Clip");
            if (loop) cb.Loop(); else cb.Once();
            if (durations != null && durations.Length > 0) cb.Durations(durations);
            return FxFactory.Visual(name, sh, cb.Build(), loop, lifetime);
        }

        /// <summary>
        /// A hitbox wearing mod art: clones a vanilla damage effect (for its layer, rigidbody and collider), reskins it and
        /// switches damage on at <paramref name="onFrame"/> and off at <paramref name="offFrame"/> of the anim. Plays once.
        /// </summary>
        public static GameObject TimedHit(string name, string vanilla, string art, string anim, int onFrame, int offFrame,
                                          float damage, float knock, Status status = null, float statusChance = 1f, float rate = 0f,
                                          float colliderScale = 1f, float[] durations = null, bool canFlip = true)
        {
            var sh = SpriteSheets.Get(art);
            var go = FxFactory.Clone(vanilla, name);
            if (go == null || sh == null) return go;
            FxFactory.StripChildren(go);
            var cb = new ClipBuilder(sh, anim, name + "Clip").Once().Ev(onFrame, "AnimDamageOn").Ev(offFrame, "AnimDamageOff");
            if (durations != null) cb.Durations(durations);
            FxFactory.Reskin(go, cb.Build(), sh);
            var spr = go.GetComponent<exSprite>();
            if (spr != null) { spr.anchor = exPlane.Anchor.BotCenter; spr.offset = Vector2.zero; }
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, canFlip: canFlip, freeRotate: false);
            foreach (var m in go.GetComponents<ParticleMotion>()) { R.Set(m, "m_trailObject", null); m.enabled = false; }
            FxFactory.SetDamage(go, damage, rate: rate, knockback: knock, status: status, statusChance: statusChance, collisionAtStart: false);
            ImpactFx.Theme(go, art);
            if (Math.Abs(colliderScale - 1f) > 0.01f)
            {
                foreach (var c in go.GetComponents<CapsuleCollider>()) { c.radius *= colliderScale; c.height *= colliderScale; c.center *= colliderScale; }
                foreach (var c in go.GetComponents<BoxCollider>()) { c.size = Vector3.Scale(c.size, new Vector3(colliderScale, colliderScale, 1f)); c.center = Vector3.Scale(c.center, new Vector3(colliderScale, colliderScale, 1f)); }
            }
            NoTint(go);
            return go;
        }

        /// <summary>A ground effect that plays mod art and then releases a minion (cloned from the vanilla rat-ball spawner).
        /// Without art it waits <paramref name="delay"/> seconds instead.</summary>
        public static GameObject MinionSpawner(string name, GameObject minionPrefab, string art, string anim, float delay = 0.5f)
        {
            var go = FxFactory.Clone("FX_RatBallSpawner", name);
            if (go == null) return null;
            FxFactory.StripChildren(go);
            var sh = art != null ? SpriteSheets.Get(art) : null;
            if (sh != null && sh.Has(anim))
            {
                FxFactory.Reskin(go, new ClipBuilder(sh, anim, name + "Clip").Once().Build(), sh);
                FxFactory.SetEffect(go, destroyOnAnimEnd: true, spawnOnDestroy: minionPrefab, freeRotate: false);
            }
            else
            {
                var spr = go.GetComponent<exSprite>(); if (spr != null) spr.enabled = false;
                FxFactory.SetEffect(go, destroyOnAnimEnd: false, destroyAfter: delay, spawnOnDestroy: minionPrefab, freeRotate: false);
            }
            FxFactory.SetMotion(go, 0f, enabled: false);
            FxFactory.SetDamage(go, 0f, enabled: false);
            return go;
        }

        /// <summary>A hero-side copy of a monster effect with scaled damage (spells reuse monster moves, softer).</summary>
        public static GameObject Weakened(GameObject template, string name, float damageMult)
        {
            if (template == null) return null;
            var go = MonsterFactory.ClonePrefab(template, name);
            foreach (var d in go.GetComponentsInChildren<DamageEffect>(true))
                R.Set(d, "m_damage", R.Get<float>(d, "m_damage") * damageMult);
            FxFactory.Templates[name] = go;
            Action<GameObject> hook;
            if (FxFactory.OnSpawn.TryGetValue(template, out hook)) FxFactory.OnSpawn[go] = hook;
            return go;
        }

        /// <summary>
        /// A shadow-tinted copy of an attack template at reduced strength, linked as its echo: a monster whose traits have
        /// <see cref="MonsterTraits.echo"/> repeats the attack with it. Returns the echo template.
        /// </summary>
        public static GameObject EchoOf(GameObject template, float damageMult = 0.5f)
        {
            if (template == null) return null;
            var go = MonsterFactory.ClonePrefab(template, template.name + "Echo");
            var d = go.GetComponent<DamageEffect>();
            if (d != null) R.Set(d, "m_damage", R.Get<float>(d, "m_damage") * damageMult);
            foreach (var spr in go.GetComponentsInChildren<exSprite>(true)) spr.color = new Color(0.45f, 0.25f, 0.7f, 0.75f);
            FxFactory.Templates[go.name] = go;
            Action<GameObject> hook;
            if (FxFactory.OnSpawn.TryGetValue(template, out hook)) FxFactory.OnSpawn[go] = hook;
            Patch_SpawnEffectEcho.EchoOf[template] = go;
            return go;
        }

        /// <summary>The echo linked to <paramref name="template"/> by <see cref="EchoOf"/>, or null.</summary>
        public static GameObject FindEcho(GameObject template)
        {
            GameObject echo;
            return template != null && Patch_SpawnEffectEcho.EchoOf.TryGetValue(template, out echo) ? echo : null;
        }

        /// <summary>
        /// A non-damaging object that still remembers who spawned it (seeds, egg sacs): a clone of the rat-ball spawner with
        /// its damage switched off, wearing mod art. Its DamageEffect relays ownership to whatever it spawns.
        /// <paramref name="thenAnim"/> (optional) plays after <paramref name="anim"/>, <paramref name="thenRepeat"/> times.
        /// </summary>
        public static GameObject Inert(string name, string art, string anim, bool destroyOnAnimEnd = true, float life = 0f,
                                       GameObject spawnOnDestroy = null, string thenAnim = null, int thenRepeat = 1)
        {
            var go = FxFactory.Clone("FX_RatBallSpawner", name);
            if (go == null) return null;
            FxFactory.StripChildren(go);
            var sh = art != null ? SpriteSheets.Get(art) : null;
            if (sh == null) { var spr0 = go.GetComponent<exSprite>(); if (spr0 != null) spr0.enabled = false; }
            if (sh != null && sh.Has(anim))
            {
                var cb = new ClipBuilder(sh, anim, name + "Clip").Once();
                if (thenAnim != null) cb.Then(thenAnim, thenRepeat);
                FxFactory.Reskin(go, cb.Build(), sh);
                var spr = go.GetComponent<exSprite>(); if (spr != null) { spr.anchor = exPlane.Anchor.BotCenter; spr.offset = Vector2.zero; }
            }
            FxFactory.SetEffect(go, destroyOnAnimEnd: destroyOnAnimEnd, destroyAfter: life, spawnOnDestroy: spawnOnDestroy, freeRotate: false);
            FxFactory.SetMotion(go, 0f, enabled: false);
            FxFactory.SetDamage(go, 0f, enabled: false);
            return go;
        }

        /// <summary>A slow drifting cloud that hurts every <paramref name="rate"/> seconds while it lingers (ash, spores).</summary>
        public static GameObject Cloud(string name, string art, string anim, float speed, float damage, float rate,
                                       Status status, float statusChance, params float[] durations)
        {
            var sh = SpriteSheets.Get(art);
            var go = FxFactory.Clone("DFX_skelMageNewProjectile", name);
            if (go == null || sh == null) return go;
            var cb = new ClipBuilder(sh, anim, name + "Clip").Once();
            if (durations != null && durations.Length > 0) cb.Durations(durations);
            FxFactory.Reskin(go, cb.Build(), sh);
            FxFactory.SetEffect(go, destroyOnAnimEnd: true, freeRotate: false);
            foreach (var m in go.GetComponents<ParticleMotion>()) R.Set(m, "m_trailObject", null);
            FxFactory.SetMotion(go, speed, accel: speed * 1.4f, speedMax: speed * 0.12f);
            FxFactory.SetDamage(go, damage, rate: rate, knockback: 0.1f, status: status, statusChance: statusChance, collisionAtStart: true);
            FxFactory.SetContacts(go, destroyOnHit: false, clearSpawnOnHit: true);
            var a = go.GetComponent<AudioCueSource>(); if (a != null) R.Set(a, "m_playOnSpawn", null);
            NoTint(go);
            return go;
        }

        /// <summary>An effect that, once it knows its owner, bursts a ring of <paramref name="count"/> copies of a projectile.</summary>
        public static GameObject Emitter(string name, GameObject projectile, int count)
        {
            if (projectile == null) return null;
            var go = Inert(name, null, null, destroyOnAnimEnd: false, life: 0.3f);
            if (go == null) return null;
            FxFactory.OnSpawn[go] = i => { var e = i.GetComponent<EmitterFx>() ?? i.AddComponent<EmitterFx>(); e.projectile = projectile; e.count = count; };
            return go;
        }
    }
}
