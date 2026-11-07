using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>A splinter skidding over the ice: it melts away as soon as it leaves the ice.</summary>
    public class YsvSkidFx : MonoBehaviour
    {
        float m_age;
        void OnEnable() { m_age = 0f; }
        void Update()
        {
            m_age += Time.deltaTime;
            if (m_age > 0.08f && !YsvFloor.Covers((Vector2)transform.position - new Vector2(0f, 2f))) SystemPool.Despawn(gameObject);
        }
    }
}
