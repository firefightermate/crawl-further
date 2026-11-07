using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// A pile of bones on the floor: fuel for Ossivar monsters (plates, heals, raised rats, crows). A pile can be filled with
    /// marrow by a Marrow Wyrm (it then gives two plates and shows red veins) and locked while something carries it.
    /// </summary>
    public class BonePileFx : Registered<BonePileFx>
    {
        GameObject m_veins;

        /// <summary>Held by something (a harpoon, a talon): nobody eats it and it does not crawl.</summary>
        public bool Locked { get; set; }

        /// <summary>Filled with marrow: eaten, it gives two plates.</summary>
        public bool Marrow { get; private set; }

        protected override void OnEnable() { base.OnEnable(); Locked = false; Marrow = false; DropVeins(); }
        protected override void OnDisable() { base.OnDisable(); StopAllCoroutines(); DropVeins(); }

        /// <summary>Fill it with marrow (the red veins show for as long as it lies there).</summary>
        public void FillMarrow()
        {
            if (Marrow) return;
            Marrow = true;
            if (OssivarFx.MarrowVeins == null) return;
            m_veins = SystemPool.Spawn(OssivarFx.MarrowVeins, transform.position);
            if (m_veins != null) ModAttach.Front(m_veins, gameObject);
        }

        void DropVeins()
        {
            if (m_veins == null) return;
            ModAttach.Drop(m_veins, gameObject);
            if (m_veins.activeInHierarchy) SystemPool.Despawn(m_veins);
            m_veins = null;
        }

        /// <summary>Eaten, raised or reeled in: remove the pile.</summary>
        public void Consume() { DropVeins(); All.Remove(this); SystemPool.Despawn(gameObject); }

        /// <summary>Hop <paramref name="dist"/> px toward <paramref name="to"/> in a short arc (the Cairn Crow's caw).</summary>
        public void Hop(Vector2 to, float dist)
        {
            if (!isActiveAndEnabled || Locked) return;
            Vector2 me = transform.position, d = to - me;
            if (d.sqrMagnitude < 4f) return;
            StopAllCoroutines();
            StartCoroutine(HopTo(ModUtil.SafePoint(me, me + d.normalized * Mathf.Min(dist, d.magnitude - 2f), 3f)));
        }

        IEnumerator HopTo(Vector2 end)
        {
            Vector2 start = transform.position;
            float z = transform.position.z;
            for (float t = 0f; t < 1f; t += Time.deltaTime / 0.25f)
            {
                var p = Vector2.Lerp(start, end, t) + new Vector2(0f, Mathf.Sin(t * Mathf.PI) * 6f);
                transform.position = new Vector3(p.x, p.y, z);
                yield return null;
            }
            transform.position = new Vector3(end.x, end.y, z);
        }
    }
}
