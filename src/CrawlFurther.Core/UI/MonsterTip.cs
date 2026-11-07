namespace CrawlFurther.UI
{
    /// <summary>One monster's tip: its display name, one short line each for the basic attack and the special, and an
    /// optional passive of one or two lines ("\n" between them; null or empty: not shown). Lines are written for the
    /// player who is the monster ("Pull the hero to you"); with its label ("Attack: ") each stays within 60 characters.</summary>
    public struct MonsterTip
    {
        public string name, attack, special, passive;
        public MonsterTip(string name, string attack, string special, string passive = null)
        { this.name = name; this.attack = attack; this.special = special; this.passive = passive; }
    }
}
