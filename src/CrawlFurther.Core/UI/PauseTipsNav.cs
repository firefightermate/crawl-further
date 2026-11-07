using UnityEngine;

namespace CrawlFurther.UI
{
    /// <summary>On MenuTips: Left / Right on a mod page jumps to the first page of the previous / next topic.</summary>
    public class PauseTipsNav : MonoBehaviour
    {
        MenuStateMachine m_sm;
        int m_player = -1;
        int[] m_topic;

        public void Setup(MenuStateMachine sm, int player, int[] topicOfState) { m_sm = sm; m_player = player; m_topic = topicOfState; }

        bool Down(eInput i)
        {
            try { return m_player >= 0 ? SystemInput.InputDown(i, m_player) : SystemInput.InputDown(i); }
            catch { return false; }
        }

        int FirstOf(int state)
        {
            while (state > 0 && m_topic[state - 1] == m_topic[state]) state--;
            return state;
        }

        void Update()
        {
            if (m_sm == null || m_topic == null) return;
            int s = m_sm.GetState();
            if (s < 0 || s >= m_topic.Length || m_topic[s] < 0) return;   // vanilla pages keep vanilla input only
            if (Down(eInput.Right))
            {
                int t = s;
                while (t < m_topic.Length && m_topic[t] == m_topic[s]) t++;
                if (t < m_sm.m_states.Count) m_sm.SetState(t);   // past the last topic: "Back", out to the pause menu
            }
            else if (Down(eInput.Left))
            {
                int first = FirstOf(s);
                if (first > 0) m_sm.SetState(FirstOf(first - 1));
            }
        }
    }
}
