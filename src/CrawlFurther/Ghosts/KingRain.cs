using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Ghosts
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// The King Blob's Rain: on the spew frame it throws five globs high. Each one's shadow grows on the floor for 0.8 s
    /// before it lands there, so the hero always sees where. The middle glob lands where the King aims, as far out as the
    /// hero is (within <see cref="Reach"/>), and leaves a slowing puddle; the other four land around it.
    /// </summary>
    public class KingRain : MonsterBehaviour
    {
        /// <summary>The clip event on the Rain anim's spew frame.</summary>
        public const string Event = "ModBlobKingRain";
        /// <summary>How far ahead the middle glob can land (px); the AI starts Rain only with the hero this close.</summary>
        public const float Reach = 100f;
        /// <summary>Each glob's hit (a Titan's slam is 1.6).</summary>
        public const float DropDamage = 0.6f;
        const float Nearest = 30f, Spread = 22f, Stagger = 0.08f;

        PlayerMovement m_move;
        Player m_body;

        protected override void Awake()
        {
            base.Awake();
            m_move = GetComponent<PlayerMovement>();
            m_body = GetComponent<Player>();
        }

        void OnDisable() { StopAllCoroutines(); }

        /// <summary>Clip event: the globs go up.</summary>
        public void ModBlobKingRain()
        {
            if (Monster == null || !Monster.Alive) return;
            StartCoroutine(Rain(Target(), Monster.OwnSource()));
        }

        /// <summary>A player's King: straight along the aim, at the hero's distance. Left to its AI: at the hero.</summary>
        Vector2 Target()
        {
            Vector2 me = transform.position;
            var to = Monster.HeroPos - me;
            float d = Mathf.Clamp(to.magnitude, Nearest, Reach);
            var dir = m_move != null ? m_move.GetFaceDirection() : Vector2.right;
            if (m_body != null && m_body.GetIsAI() && to.sqrMagnitude > 1f) dir = to;
            if (dir.sqrMagnitude < 0.01f) dir = Vector2.right;
            return me + dir.normalized * d;
        }

        IEnumerator Rain(Vector2 at, DamageSource src)
        {
            Drop(GhostPack.KingDropPool ?? GhostPack.KingDrop, at, src);
            float a0 = Random.Range(0f, 90f);
            for (int i = 0; i < 4; i++)
            {
                yield return new WaitForSeconds(Stagger);
                if (Monster == null || !Monster.Alive) yield break;
                float a = (a0 + i * 90f) * Mathf.Deg2Rad;
                Drop(GhostPack.KingDrop, at + new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.6f) * Spread, src);
            }
        }

        static void Drop(GameObject template, Vector2 at, DamageSource src)
        {
            if (template != null && SystemLevel.GetInCurrentRoom(at)) FxFactory.SpawnOwned(template, at, src);
        }
    }
}
