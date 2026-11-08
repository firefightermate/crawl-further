namespace CrawlFurther.Monsters
{
    /// <summary>
    /// The vault challenge of one mod monster: the game's own hero challenge (pick the monster in the vault, keep a bot
    /// hero from levelling up). Give it as <see cref="MonsterDef.challenge"/>, or with <see cref="Challenges.Register"/>
    /// for a monster built some other way. Without one, a monster a player can become gets a challenge with the goal
    /// <see cref="Challenges.GoalFor"/> picks from its evolution cost, and any other monster (minions, blobs) gets none.
    /// </summary>
    public class ChallengeDef
    {
        /// <summary>The hero level to reach to pass (the game's m_targetScore). 0 or below: the goal for the monster's
        /// evolution cost from <see cref="Challenges.GoalByCost"/>.</summary>
        public int goal;
        /// <summary>No challenge at all: the vault shows no Challenge button for this monster.</summary>
        public bool none;
    }
}
