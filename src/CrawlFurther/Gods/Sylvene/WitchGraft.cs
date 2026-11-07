using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    /// <summary>Bloom Witch, Graft: a ripe pod grows onto the head of each Sylvene monster within <see cref="Range"/> px
    /// (up to <see cref="MaxKin"/>) and onto her own (<see cref="Grafted"/>).</summary>
    public class WitchGraft : SylveneBehaviour
    {
        public const float Range = 60f;
        public const int MaxKin = 3;

        /// <summary>Clip event: the pods swell over her palms.</summary>
        public void ModSylGraft()
        {
            if (!Alive) return;
            var kin = new List<Player>();
            foreach (var p in FindObjectsOfType<Player>())
                if (p != null && p.gameObject != gameObject && SylveneMonster.IsKin(p.gameObject) && Near(p.transform.position, Me, Range)) kin.Add(p);
            kin.Sort((a, b) => ((Vector2)a.transform.position - Me).sqrMagnitude.CompareTo(((Vector2)b.transform.position - Me).sqrMagnitude));
            for (int i = 0; i < kin.Count && i < MaxKin; i++) Grafted.Graft(kin[i].gameObject, Own);
            Grafted.Graft(gameObject, Own);
        }
    }
}
