using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Content.Gods;
    using CrawlFurther.Util;

    /// <summary>Kit and death ice: lays its slabs on the first frame it knows where it is.</summary>
    public class YsvIceSpawn : MonoBehaviour
    {
        int m_count; float m_life; bool m_done;
        public void Arm(int count, float life) { m_count = count; m_life = life; m_done = false; }
        void OnEnable() { m_done = false; }
        void Update()
        {
            if (m_done || m_count <= 0) return;
            m_done = true;
            YsvFloor.Patch(transform.position, m_count, m_life);
        }
    }
}
