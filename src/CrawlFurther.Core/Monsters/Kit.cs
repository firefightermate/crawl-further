using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Monsters
{
    using CrawlFurther.Art;
    using CrawlFurther.Util;

    /// <summary>
    /// Replacing a cloned monster's moveset inside a <see cref="MonsterDef.kit"/>. A move is a clip (built with
    /// <see cref="Melee"/>, <see cref="Shot"/> or a ClipBuilder) whose "AnimAttack" events spawn effect slots added with
    /// <see cref="AddEffect"/>, wrapped in an AttackData by <see cref="Attack"/>. Typical kit: take the base's first attack
    /// and special as templates, add effect slots, build clips, clear <see cref="Attacks"/> and add the new attacks, then
    /// <see cref="SetSpecial"/>.
    /// </summary>
    public static class Kit
    {
        /// <summary>The monster's basic attacks (edit in place; the AI picks among them).</summary>
        public static List<AttackData> Attacks(Player p) { return R.Get<List<AttackData>>(p, "m_attacks"); }
        /// <summary>The monster's effect slots: what "AnimAttack" clip events spawn, by index.</summary>
        public static List<DamageEffectData> Effects(Player p) { return R.Get<List<DamageEffectData>>(p, "m_attackDamageEffects"); }

        /// <summary>
        /// Append an effect slot that spawns <paramref name="prefab"/>; returns its index for AnimAttack(i). Offsets in
        /// pixels from the attack node (see <see cref="Strike.Feet"/>), angle in degrees. <paramref name="attach"/>: the
        /// effect follows the monster. <paramref name="like"/>: copy another slot's settings first.
        /// </summary>
        public static int AddEffect(Player p, GameObject prefab, bool attach = false, bool destroyOnAnimEnd = false,
                                    float offsetX = 0f, float offsetY = 0f, float angle = 0f, float angleMax = float.NaN,
                                    DamageEffectData.eSpawnPoint spawnPoint = DamageEffectData.eSpawnPoint.Node, DamageEffectData like = null)
        {
            var list = Effects(p);
            var d = like != null ? R.Clone(like) : new DamageEffectData();
            d.m_object = prefab;
            d.m_attach = attach;
            d.m_destroyOnAnimEnd = destroyOnAnimEnd;
            if (like == null || offsetX != 0f) d.m_offsetX = new MinMaxRange(offsetX);
            if (like == null || offsetY != 0f) d.m_offsetY = new MinMaxRange(offsetY);
            d.m_angle = float.IsNaN(angleMax) ? new MinMaxRange(angle) : new MinMaxRange(angle, angleMax);
            d.m_scaleX = new MinMaxRange(1f); d.m_scaleY = new MinMaxRange(1f);
            d.m_spawnDelay = new MinMaxRange(0f);
            d.m_spawnPoint = spawnPoint;
            list.Add(d);
            return list.Count - 1;
        }

        /// <summary>Push a ground quake further out when the attack aims straight up or down (vanilla m_offsetAimUp/Down,
        /// blended by aim angle): the quake's offsetX turns with the aim, but a flat ellipse reaches less far vertically.</summary>
        public static void AimReach(Player p, int effect, float up, float down)
        {
            var list = Effects(p);
            if (list == null || effect < 0 || effect >= list.Count) return;
            list[effect].m_offsetAimUp = new Vector2(0f, up);
            list[effect].m_offsetAimDown = new Vector2(0f, -down);
        }

        /// <summary>
        /// A new attack from <paramref name="template"/>'s settings (AI data, feel) playing <paramref name="clip"/>, with
        /// its own cooldown (seconds) and, optionally, the AI's ranges (pixels): attack within inner..outer, back off
        /// inside retreat.
        /// </summary>
        public static AttackData Attack(AttackData template, exSpriteAnimClip clip, float cooldown,
                                        float rangeInner = -1f, float rangeOuter = -1f, float rangeRetreat = -1f, bool? retreatWhileAttacking = null)
        {
            var a = R.Clone(template);
            a.m_animationFront = clip;
            a.m_animAngles = new List<AttackDataAnimAngle>();
            a.m_cooldown = cooldown;
            var bot = R.Clone(template.m_botData);
            if (rangeInner >= 0f) bot.m_rangeInner = rangeInner;
            if (rangeOuter >= 0f) bot.m_rangeOuter = rangeOuter;
            if (rangeRetreat >= 0f) bot.m_rangeRetreat = rangeRetreat;
            if (retreatWhileAttacking.HasValue) bot.m_retreatWhileAttacking = retreatWhileAttacking.Value;
            a.m_botData = bot;
            return a;
        }

        /// <summary>First AnimSound object param found in a vanilla clip (to reuse the monster's own voice).</summary>
        public static Object FindSound(exSpriteAnimClip clip, int nth = 0)
        {
            if (clip == null) return null;
            foreach (var e in clip.eventInfos)
                if (e.methodName == "AnimSound" && e.objectParam != null && nth-- == 0) return e.objectParam;
            return null;
        }

        /// <summary>The monster's special attack (null for a base without one).</summary>
        public static AttackData Special(Player p) { return R.Get<AttackData>(p, "m_specialAttack"); }
        /// <summary>Replace the special attack and its charge time (seconds).</summary>
        public static void SetSpecial(Player p, AttackData a, float charge)
        {
            R.Set(p, "m_specialAttack", a);
            R.Set(p, "m_specialAttackChargeTime", charge);
        }
        /// <summary>Give a special to a monster whose base had none (blobs).</summary>
        public static void EnableSpecial(Player p, AttackData a, float charge)
        {
            R.Set(p, "m_hasSpecialAttack", true);
            SetSpecial(p, a, charge);
        }

        /// <summary>How the AI picks among the basic attacks (random, in order...), and the combo reset time (seconds).</summary>
        public static void Order(Player p, Attacks.eAttackOrderType t, float comboReset = -1f)
        {
            R.Set(p, "m_attackOrderType", t);
            if (comboReset >= 0f) R.Set(p, "m_comboResetTime", comboReset);
        }
        /// <summary>
        /// Scale the effect a slot spawns. Crawl 1.x ignores DamageEffectData.m_scaleX/Y, so this scales the
        /// (mod-owned, single-use) template itself; Effect keeps the magnitude when it orients the instance.
        /// </summary>
        public static void Scale(Player p, int effect, float s)
        {
            var d = Kit.Effects(p)[effect];
            if (d.m_object != null && d.m_object.name.StartsWith("Mod")) d.m_object.transform.localScale = new Vector3(s, s, 1f);
        }

        /// <summary>A vanilla sound cue object by name (for AnimSound events).</summary>
        public static GameObject SoundGO(string name)
        {
            foreach (var c in Resources.FindObjectsOfTypeAll<AudioCue>())
                if (c.gameObject.name == name) return c.gameObject;
            return null;
        }

        /// <summary>
        /// Standard ranged or cast clip: aim freely during the wind-up, lock on frame <paramref name="release"/>, fire every
        /// effect slot there (each <paramref name="stagger"/> seconds after the last), then hand control back on the last
        /// frame. Returns the builder: add events, then Build().
        /// </summary>
        public static ClipBuilder Shot(SpriteSheet sh, string anim, string clipName, int release, UnityEngine.Object sound, float stagger, params int[] effects)
        {
            var c = new ClipBuilder(sh, anim, clipName).Once()
                .EvF(0, "AnimInputMultiplyFreeFace", 0f)
                .Ev(release, "AnimInputMultiplyStop").Ev(release, "AnimInputOff");
            for (int i = 0; i < effects.Length; i++) c.Ev(release, "AnimAttack", effects[i], i * stagger);
            if (sound != null) c.EvO(release, "AnimSound", sound);
            c.Ev(-1, "AnimRun");
            return c;
        }

        /// <summary>
        /// Standard melee clip: aim during the wind-up, then for each (frame, effect slot, lunge) triple in
        /// <paramref name="hits"/> step forward (lunge speed, 0 for none) and strike. Returns the builder: add events, then Build().
        /// </summary>
        public static ClipBuilder Melee(SpriteSheet sh, string anim, string clipName, UnityEngine.Object sound, params float[] hits)
        {
            var c = new ClipBuilder(sh, anim, clipName).Once().EvF(0, "AnimInputMultiplyFreeFace", 0f);
            int first = hits.Length >= 3 ? (int)hits[0] : 1;
            c.Ev(Mathf.Max(0, first - 1), "AnimInputMultiplyStop").Ev(Mathf.Max(0, first - 1), "AnimInputOff");
            for (int i = 0; i + 2 < hits.Length; i += 3)
            {
                int f = (int)hits[i];
                if (hits[i + 2] > 0f) c.EvF(f, "AnimMoveStick", hits[i + 2]);
                c.Ev(f, "AnimAttack", (int)hits[i + 1]);
                if (i == 0 && sound != null) c.EvO(f, "AnimSound", sound);
                c.Ev(f + 1, "AnimMoveStop");
            }
            c.Ev(-1, "AnimRun");
            return c;
        }

        /// <summary>The base monster's attack sound, to reuse in new clips.</summary>
        public static UnityEngine.Object Voice(Player p)
        {
            var atk = Attacks(p);
            UnityEngine.Object v = null;
            if (atk.Count > 0) v = FindSound(atk[0].m_animationFront);
            if (v == null) { var sp = Special(p); if (sp != null) v = FindSound(sp.m_animationFront); }
            if (v == null && atk.Count > 0 && atk[0].m_sound != null) v = atk[0].m_sound.gameObject;
            return v;
        }

        /// <summary>Add an object the monster leaves behind when it dies (a pool, a pile of bones).</summary>
        public static void AddDeathSpawn(Player p, GameObject prefab, float offsetY = 0f)
        {
            if (prefab == null) return;
            var old = R.Get<DamageEffectData[]>(p, "m_spawnOnDeath") ?? new DamageEffectData[0];
            var d = new DamageEffectData
            {
                m_object = prefab, m_attach = false, m_destroyOnAnimEnd = false,
                m_offsetX = new MinMaxRange(0f), m_offsetY = new MinMaxRange(offsetY), m_angle = new MinMaxRange(0f),
                m_scaleX = new MinMaxRange(1f), m_scaleY = new MinMaxRange(1f), m_spawnDelay = new MinMaxRange(0f)
            };
            var list = new List<DamageEffectData>(old) { d };
            R.Set(p, "m_spawnOnDeath", list.ToArray());
        }
    }
}
