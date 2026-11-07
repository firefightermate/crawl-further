using UnityEngine;

namespace CrawlFurther.Objects
{
    using CrawlFurther.Monsters;

    /// <summary>One use of an object: who used it, and helpers for the effect.</summary>
    public class ObjUse
    {
        public ModObject obj;
        public Player player;
        public PlayerData pd;
        public bool IsHero { get { return pd != null && pd.IsHero; } }
        public bool IsMonster { get { return pd != null && pd.IsMonster; } }
        public bool IsGhost { get { return pd != null && !pd.IsAlive; } }
        public GameObject Body { get { return player != null ? player.gameObject : null; } }
        public Vector2 At { get { return obj != null ? (Vector2)obj.transform.position : Vector2.zero; } }

        public void Heal(float amount)
        {
            var h = Body != null ? Body.GetComponent<Health>() : null;
            if (h == null || !h.IsAlive()) return;
            h.Heal(amount);
            ModInd.Heal(Body);
        }
        public void Gold(int amount) { if (pd != null && amount > 0) pd.OnGoldCollected(amount); }
        public void Ecto(float amount) { if (pd != null && amount > 0) pd.OnEctoplasmCollected(amount); }
        public void Status(Status s, string tag)
        {
            if (player == null || s == null) return;
            player.AddStatus(s, tag);   // no attacker (the vanilla overload the game uses for environment statuses)
        }
        /// <summary>Damage the user with no attacker. Resistance (wards, curses, items) applies unless <paramref name="exact"/>
        /// (costs are exact, like the vanilla health shrines).</summary>
        public void Hurt(float amount, bool exact = false)
        {
            var h = Body != null ? Body.GetComponent<Health>() : null;
            if (h == null || !h.IsAlive()) return;
            float k = exact ? h.GetDamageResistance() : 1f;
            h.DamageNoSource(amount * k);
        }
        /// <summary>Show a short word or number over the user (FloatNumber glyphs: 0-9 D O G E).</summary>
        public void Say(string text, NumberTone tone = NumberTone.Normal) { if (Body != null) FloatNumber.Show(text, tone, FloatNumber.OverHead(Body, 4f), Body); }
    }
}
