using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Sylvene
{
    /// <summary>
    /// Cordyceps Saint, Infect: drives spines into up to <see cref="MaxKin"/> Sylvene monsters within <see cref="Range"/>
    /// px (into itself if none is near). They sprout stalks for <see cref="Infected.Duration"/> s; one that dies meanwhile
    /// fights on as a shambler (<see cref="Infected"/>).
    /// </summary>
    public class CordycepsInfect : SylveneBehaviour
    {
        public const float Range = 60f;
        public const int MaxKin = 2;

        /// <summary>Clip event: the spines fly from its stalks.</summary>
        public void ModSylInfect()
        {
            if (!Alive) return;
            var kin = new List<Player>();
            foreach (var p in FindObjectsOfType<Player>())
                if (p != null && p.gameObject != gameObject && SylveneMonster.IsKin(p.gameObject) && Near(p.transform.position, Me, Range)) kin.Add(p);
            kin.Sort((a, b) => ((Vector2)a.transform.position - Me).sqrMagnitude.CompareTo(((Vector2)b.transform.position - Me).sqrMagnitude));
            if (kin.Count == 0) { Infected.Infect(gameObject, Own); return; }
            for (int i = 0; i < kin.Count && i < MaxKin; i++) Infected.Infect(kin[i].gameObject, Own);
        }
    }
}
