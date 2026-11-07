using UnityEngine;

namespace CrawlFurther.Content.Gods.Kaurn
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A piece of Kaurn iron on the floor or in the air: a rod, a stud, a hanging wisp, a drifting ball, a Fuse Sapper
    /// charge. Rods, studs, wisps and balls are arc ends (<see cref="KaurnConduction"/>); charges are not, an arc that
    /// reaches one sets it off (<see cref="KrnChargeFx"/>).
    /// </summary>
    public class KrnNode : Registered<KrnNode>
    {
        public enum Kind { Rod, Stud, Wisp, Orb, Charge }

        /// <summary>The most posts kept at once: the oldest goes when there are more, so the floor stays readable.</summary>
        public const int Cap = 14;
        /// <summary>Seconds a freshly planted Anvil Smith rod stays red hot.</summary>
        public const float HotTime = 3f;

        public Kind kind = Kind.Rod;
        /// <summary>Height of the arc's end above the node's position.</summary>
        public float height = 13f;
        public float born;
        float m_hotUntil;

        /// <summary>True while its arcs hurt double (a fresh Anvil Smith rod).</summary>
        public bool Hot { get { return Time.time < m_hotUntil; } }

        /// <summary>A post the Forgemaster can pick up, the Static Moth can drink and the Tesla Spire fires from.</summary>
        public bool IsRod { get { return kind == Kind.Rod; } }

        /// <summary>Joins arcs (a charge only sets off).</summary>
        public bool Conducts { get { return kind != Kind.Charge; } }

        public Vector2 Top { get { return (Vector2)transform.position + new Vector2(0f, height); } }

        public void Init(Kind k, float h, float hot)
        {
            kind = k;
            height = h;
            m_hotUntil = hot > 0f ? Time.time + hot : 0f;
        }

        protected override void OnEnable()
        {
            base.OnEnable();
            born = Time.time;
            m_hotUntil = 0f;
            KaurnConduction.Ensure();
            if (All.Count > Cap)
            {
                KrnNode oldest = null;
                foreach (var n in All) if (n != null && n != this && (oldest == null || n.born < oldest.born)) oldest = n;
                if (oldest != null) SystemPool.Despawn(oldest.gameObject);
            }
        }

        /// <summary>A damage source owned by whoever made the node (its monster), else the node itself.</summary>
        public DamageSource Source()
        {
            var s = FxFactory.SourceOf(gameObject);
            if (s != null && s.m_sourceOwner != null) return ModUtil.HandOn(s, gameObject);
            return new DamageSource(gameObject, gameObject, null);
        }

        /// <summary>Take the node off the floor (picked up, drunk dry, blown).</summary>
        public void Remove() { if (gameObject.activeInHierarchy) SystemPool.Despawn(gameObject); }
    }
}
