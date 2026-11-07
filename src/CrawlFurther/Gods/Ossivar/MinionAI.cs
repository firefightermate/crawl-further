using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Util;

    /// <summary>
    /// Minions released by spawner effects (bone rats, sprouts, larvae, jacks, broodlings) run as AI on the fodder base's
    /// PlayerAI, not on the bot ranges the kits set. The fodder mushroom never chases (chase radius 0) and swings at
    /// anything within 200 px; the tiny rat bites from 50 px. Tune each minion's PlayerAI to its real reach.
    /// </summary>
    public static class MinionAI
    {
        public static void Tune(Player p, float chaseFrom, float holdAt, float attackRadius, float cdMin, float cdMax, float chaseSpeed = 1f)
        {
            try
            {
                var ai = p != null ? p.GetComponent<PlayerAI>() : null;
                if (ai == null) return;
                // chase starts inside chaseFrom and stops (stands to attack) inside holdAt
                R.Set(ai, "m_chaseStartRadius", new MinMaxRange(chaseFrom, chaseFrom + 30f));
                R.Set(ai, "m_chaseStopRadius", new MinMaxRange(Mathf.Max(2f, holdAt * 0.4f), holdAt));
                R.Set(ai, "m_chaseMoveMultiplier", chaseSpeed);
                var list = R.Get<System.Collections.IList>(ai, "m_attacks");
                if (list == null) return;
                foreach (var a in list)
                {
                    if (a == null) continue;
                    R.Set(a, "m_attackRadius", attackRadius);
                    R.Set(a, "m_attackCooldown", new MinMaxRange(cdMin, cdMax));
                }
            }
            catch (System.Exception e) { Plugin.Log.LogWarning("MinionAI " + (p != null ? p.name : "?") + ": " + e.Message); }
        }
    }
}
