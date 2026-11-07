using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>On every Sylvene monster: marks it as one of the orchard's (grafts and infections look for it) and answers
    /// the clip events the god's kits share.</summary>
    public class SylveneMonster : MonsterBehaviour
    {
        PlayerMovement m_move;

        protected override void Awake() { base.Awake(); m_move = GetComponent<PlayerMovement>(); }

        /// <summary>Sow two seeds round the monster (the Sporeling's Scatter).</summary>
        public void ModSowSeeds()
        {
            Vector2 me = transform.position;
            for (int i = 0; i < 2; i++)
            {
                var off = new Vector2(i == 0 ? -7f : 7f, Random.Range(-3f, 3f));
                Orchard.Plant(SylveneFx.Seed, me, me + off, Monster.OwnSource());
            }
        }

        /// <summary>Spring back away from where it faces at <paramref name="speed"/> px/s (the Rotfly climbing off its dive).</summary>
        public void ModSylRecoil(float speed)
        {
            if (m_move == null || Monster == null || !Monster.Alive) return;
            var f = m_move.GetFaceDirection();
            if (f.sqrMagnitude < 0.01f) return;
            m_move.Push(-f.normalized * speed, 0.25f);
        }

        /// <summary>True if <paramref name="go"/> is a living Sylvene monster (no boss, no ghost).</summary>
        public static bool IsKin(GameObject go)
        {
            if (go == null || go.GetComponent<SylveneMonster>() == null) return false;
            var h = go.GetComponent<Health>();
            var p = go.GetComponent<Player>();
            return h != null && h.IsAlive() && p != null && !ModUtil.IsGhost(p) && go.GetComponentInParent<Boss>() == null;
        }
    }
}
