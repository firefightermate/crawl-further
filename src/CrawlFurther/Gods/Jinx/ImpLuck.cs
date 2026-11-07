using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;

    /// <summary>
    /// Dice Imp, Lucky Six: a tossed die that rolls a 6 banks the luck: its next toss is two dice in a V. Tell: its big die
    /// burns gold (the Lucky idle and run) and a gold 6 hangs over it. Basic 0 is Toss, basic 1 the twin toss.
    /// </summary>
    public class ImpLuck : JinxBehaviour
    {
        /// <summary>The idle and run while a six is banked (set by the kit).</summary>
        public static exSpriteAnimClip LuckyIdle, LuckyRun;

        bool m_lucky;

        protected override void OnEnable() { base.OnEnable(); SetLucky(false); }

        void SetLucky(bool on)
        {
            m_lucky = on;
            NextBasic(on ? 1 : 0);
            SetStance(on ? LuckyIdle : null, on ? LuckyRun : null);
            if (JinxFx.Lucky != null) ModInd.Set(gameObject, JinxFx.Lucky, on && Alive);
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (m_lucky || template != JinxFx.Die) return;
            var roll = fx.GetComponent<ChanceFx>();
            if (roll != null && roll.lastRoll == 6) SetLucky(true);
        }

        /// <summary>Clip event: the twin toss is spent.</summary>
        public void ModJinxTwinThrown() { SetLucky(false); }
    }
}
