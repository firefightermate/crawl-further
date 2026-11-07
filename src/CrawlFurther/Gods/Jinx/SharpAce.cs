namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Card Sharp, Ace up the Sleeve: every third Deal is one gold Ace instead of three cards: fast, it cuts through
    /// everything in its path and dazes. Tell: the gold Ace hangs over its head while the next deal is the Ace.
    /// Basic 0 is Deal, basic 1 the Ace.
    /// </summary>
    public class SharpAce : JinxBehaviour
    {
        int m_deals;

        protected override void OnEnable() { base.OnEnable(); m_deals = 0; Show(false); }

        void Show(bool ace)
        {
            NextBasic(ace ? 1 : 0);
            if (JinxFx.AceReady != null) ModInd.Set(gameObject, JinxFx.AceReady, ace && Alive);
        }

        /// <summary>Clip event: a Deal let its three cards go.</summary>
        public void ModJinxDealt()
        {
            m_deals++;
            Show(m_deals >= 2);
        }

        /// <summary>Clip event: the Ace was thrown.</summary>
        public void ModJinxAceThrown()
        {
            m_deals = 0;
            Show(false);
        }
    }
}
