using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// Base for a component that gives mod monsters behaviour of your own: methods named by clip events (an event calls
    /// the method of that name on every component of the body, with its int, float, string or object parameter) and
    /// per-frame rules in Update. List it with <see cref="MonsterTraits.Add{T}"/>; <see cref="ModMonster"/> adds it to
    /// every instance. Instances are pooled: reset per-life state in OnEnable.
    /// </summary>
    public abstract class MonsterBehaviour : MonoBehaviour
    {
        /// <summary>The body's <see cref="ModMonster"/>: plates, healing, facing and ownership helpers.</summary>
        protected ModMonster Monster { get; private set; }

        protected virtual void Awake() { Monster = GetComponent<ModMonster>(); }
    }
}
