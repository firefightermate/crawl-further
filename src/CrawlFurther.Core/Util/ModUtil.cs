using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Util
{
    using CrawlFurther.Monsters;

    /// <summary>Small game queries and moves that monster and item code needs often. Distances are in world pixels.</summary>
    public static class ModUtil
    {
        /// <summary>Traits by monster prefab name, filled as monsters are built and read when their instances wake.</summary>
        public static readonly Dictionary<string, MonsterTraits> Traits = new Dictionary<string, MonsterTraits>();

        /// <summary>The hero's GameObject, or null between heroes.</summary>
        public static GameObject Hero()
        {
            var h = SystemPlayers.GetHeroPlayerData();
            return h != null ? h.GameObject : null;
        }

        /// <summary>A damage source owned by the hero, for damage the hero should be credited with; null without a hero.</summary>
        public static DamageSource HeroSource()
        {
            var h = SystemPlayers.GetHeroPlayerData();
            return h != null && h.GameObject != null ? new DamageSource(h.GameObject, h.GameObject, h) : null;
        }

        /// <summary>
        /// A damage source owned by <paramref name="body"/>, for hits it makes outside its Attacks (effects it spawns,
        /// statuses, direct damage). The player credited is the one the game credits for that body's own attacks
        /// (Player.GetAttackSpawnerPlayer): the player in it, or for an AI body (fodder, a minion, a thrall) the player
        /// who made it. A hit that kills the hero must credit a player: the game hands the crown to that player and gives
        /// up when there is none (no new hero, and the old one never becomes a ghost). The body stays the hitting body
        /// (m_sourceOwnerPlayer), so rules that ask which monster hit still see it.
        /// </summary>
        public static DamageSource BodySource(GameObject body)
        {
            if (body == null) return null;
            var p = body.GetComponent<Player>();
            var src = new DamageSource(body, body, p != null ? p.GetAttackSpawnerPlayer() : null);
            src.m_sourceOwnerPlayer = body;
            return src;
        }

        /// <summary>
        /// <paramref name="from"/> handed on to a new effect <paramref name="effect"/>: the same owner, credited player and
        /// damage modifier (<paramref name="keepAttack"/> also keeps the attack ids). The hitting body is worked out as the
        /// game does (the credited player's body), except for a <see cref="BodySource"/> of an AI body, which stays that body.
        /// </summary>
        public static DamageSource HandOn(DamageSource from, GameObject effect, bool keepAttack = false)
        {
            if (from == null) return null;
            var src = new DamageSource(effect, from.m_sourceOwner, from.m_sourcePlayer,
                                       keepAttack ? from.m_sourceAttack : -1, keepAttack ? from.m_sourceAttackUId : -1, from.m_damageMod, false);
            var body = from.m_sourceOwner;
            var p = body != null && from.m_sourceOwnerPlayer == body ? body.GetComponent<Player>() : null;
            if (p != null && p.GetIsAI()) src.m_sourceOwnerPlayer = body;
            return src;
        }

        /// <summary>
        /// The player to credit for <paramref name="source"/> when it names none: the game's own credit for the body or
        /// effect behind it (its player, or the player who made an AI body). Null when nothing behind it has one.
        /// </summary>
        public static PlayerData CreditFor(DamageSource source)
        {
            if (source == null) return null;
            if (source.m_sourcePlayer != null) return source.m_sourcePlayer;
            foreach (var go in new[] { source.m_sourceOwnerPlayer, source.m_sourceOwner, source.m_source })
            {
                var p = go != null ? go.GetComponent<Player>() : null;
                var pd = p != null ? p.GetAttackSpawnerPlayer() : null;
                if (pd != null) return pd;
            }
            return null;
        }

        static readonly HarmonyLib.AccessTools.FieldRef<Player, bool> s_isGhost = HarmonyLib.AccessTools.FieldRefAccess<Player, bool>("m_isGhost");

        /// <summary>True if <paramref name="p"/> is a ghost. Player.m_isGhost has no getter; this field ref is cheap enough
        /// to call every frame.</summary>
        public static bool IsGhost(Player p) { return p != null && s_isGhost(p); }

        /// <summary>
        /// A player's hurtbox collider (the child on the DamagablePlayer layer), or null. It searches the children, so
        /// code that tracks one target every frame should cache the result.
        /// </summary>
        public static Collider Hurtbox(GameObject who)
        {
            if (who == null) return null;
            int layer = LayerMask.NameToLayer("DamagablePlayer");
            foreach (var c in who.GetComponentsInChildren<Collider>())
                if (c.transform != who.transform && c.gameObject.layer == layer && c.enabled) return c;
            return null;
        }

        /// <summary>An instance's prefab name: its name without the "(Clone)" Unity adds.</summary>
        public static string PrefabName(GameObject go)
        {
            var n = go.name;
            int i = n.IndexOf("(Clone)");
            return i >= 0 ? n.Substring(0, i).Trim() : n;
        }

        /// <summary>True if no wall lies on the straight line from <paramref name="a"/> to <paramref name="b"/>.</summary>
        public static bool Clear(Vector2 a, Vector2 b)
        {
            var d = b - a;
            if (d.sqrMagnitude < 0.01f) return true;
            return !Physics.Raycast(new Vector3(a.x, a.y, 0f), new Vector3(d.x, d.y, 0f).normalized, d.magnitude, Constants.COL_MASK_WALLS);
        }

        /// <summary>The furthest point from <paramref name="from"/> towards <paramref name="to"/> that stays
        /// <paramref name="margin"/> pixels short of any wall in between.</summary>
        public static Vector2 SafePoint(Vector2 from, Vector2 to, float margin = 6f)
        {
            var d = to - from;
            float len = d.magnitude;
            if (len < 0.01f) return from;
            RaycastHit hit;
            if (Physics.Raycast(new Vector3(from.x, from.y, 0f), new Vector3(d.x, d.y, 0f) / len, out hit, len, Constants.COL_MASK_WALLS))
                return from + d / len * Mathf.Max(0f, hit.distance - margin);
            return to;
        }

        /// <summary>Move <paramref name="go"/> to <paramref name="p"/> at once (keeping its depth), stopping its rigidbody.</summary>
        public static void Teleport(GameObject go, Vector2 p)
        {
            var z = go.transform.position.z;
            go.transform.position = new Vector3(p.x, p.y, z);
            var rb = go.GetComponent<Rigidbody>();
            if (rb != null) { rb.position = go.transform.position; rb.velocity = Vector3.zero; }
        }

        /// <summary>Pull a player towards a point with an impulse (hooks, lures). Players already within 6 pixels are left alone.</summary>
        public static void Pull(GameObject who, Vector2 toward, float strength)
        {
            if (who == null) return;
            var mv = who.GetComponent<PlayerMovement>();
            if (mv == null) return;
            var d = toward - (Vector2)who.transform.position;
            if (d.sqrMagnitude < 36f) return;
            mv.AddImpulse(d.normalized * Mathf.Min(strength, d.magnitude * 6f));
        }

        /// <summary>True while the current room's doors are locked (a fight is on).</summary>
        public static bool DoorsLocked()
        {
            var lvl = Singleton<SystemLevel>.Get;
            var room = lvl != null ? R.Get<Room>(lvl, "m_currentRoom") : null;
            return room != null && room.GetDoorsLocked();
        }
    }
}
