using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ossivar
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Helpers for the things Ossivar leaves on the floor: solid footprints that block the way (spears, headstones, ribs),
    /// objects the hero can hit (the Rattlebones' skull, the ribs) and lines drawn from segments (ropes, marrow threads).
    /// </summary>
    public static class OssFloor
    {
        /// <summary>The layer of a statue's solid footprint: blocks players, not shots.</summary>
        const int WallBase = 24;

        /// <summary>A solid footprint child (off until <see cref="SetSolid"/>): w x h px, its centre dy above the origin,
        /// turned <paramref name="angle"/> degrees.</summary>
        public static GameObject Body(GameObject owner, float w, float h, float dy = 1f, float angle = 0f)
        {
            var t = owner.transform.Find("OssBody");
            GameObject b = t != null ? t.gameObject : new GameObject("OssBody");
            b.layer = WallBase;
            b.transform.SetParent(owner.transform, false);
            b.transform.localPosition = new Vector3(0f, dy, 5f);
            b.transform.localRotation = Quaternion.Euler(0f, 0f, angle);
            b.transform.localScale = Vector3.one;
            var bc = b.GetComponent<BoxCollider>() ?? b.AddComponent<BoxCollider>();
            bc.size = new Vector3(w, h, 150f);
            b.SetActive(false);
            return b;
        }

        /// <summary>Is a living player within (rx, ry) of <paramref name="p"/>? Footprints only turn solid when nobody stands
        /// in them, so nobody is ever shut inside one.</summary>
        public static bool Occupied(Vector2 p, float rx = 7f, float ry = 5f)
        {
            var players = SystemPlayers.GetActivePlayers();
            if (players == null) return false;
            foreach (var pd in players)
            {
                var go = pd != null ? pd.GameObject : null;
                if (go == null || !go.activeInHierarchy) continue;
                var h = go.GetComponent<Health>();
                if (h != null && !h.IsAlive()) continue;
                var d = (Vector2)go.transform.position - p;
                if (Mathf.Abs(d.x) < rx && Mathf.Abs(d.y) < ry) return true;
            }
            return false;
        }

        /// <summary>
        /// Let the hero's attacks hit <paramref name="go"/> like a barrel: a Health (it never dies; the object reads the hits
        /// in its own OnDamaged) and a "Damagable" child on the DamagableProp layer, w x h px with its centre cy up.
        /// </summary>
        public static Health Hittable(GameObject go, float w, float h, float cy)
        {
            var hp = go.GetComponent<Health>() ?? go.AddComponent<Health>();
            R.Set(hp, "m_healthMax", 999f);
            R.Set(hp, "m_healthCurrent", 999f);
            R.Set(hp, "m_flashOnHit", true);
            R.Set(hp, "m_allowedDamageSource", eAllowedDamageSource.Hero);
            R.Set(hp, "m_spawnInvulnerableTime", 0f);
            var t = go.transform.Find("Damagable");
            GameObject d = t != null ? t.gameObject : new GameObject("Damagable");
            int layer = LayerMask.NameToLayer("DamagableProp");
            d.layer = layer >= 0 ? layer : 25;
            d.transform.SetParent(go.transform, false);
            d.transform.localPosition = Vector3.zero;
            var rb = d.GetComponent<Rigidbody>() ?? d.AddComponent<Rigidbody>();
            rb.isKinematic = true; rb.useGravity = false;
            var bc = d.GetComponent<BoxCollider>() ?? d.AddComponent<BoxCollider>();
            bc.size = new Vector3(w, h, 200f);
            bc.center = new Vector3(0f, cy, 0f);
            bc.isTrigger = false;
            return hp;
        }

        /// <summary>Lay a line of segment effects (each drawn 12 px long) from a to b, reusing those in <paramref name="segs"/>.</summary>
        public static void Line(List<GameObject> segs, GameObject tmpl, Vector2 a, Vector2 b, int maxSegs = 10)
        {
            var d = b - a;
            float len = d.magnitude;
            int n = len < 1f || tmpl == null ? 0 : Mathf.Clamp(Mathf.CeilToInt(len / 12f), 1, maxSegs);
            float ang = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
            for (int k = 0; k < n; k++)
            {
                while (segs.Count <= k) segs.Add(null);
                var s = segs[k];
                if (s == null || !s.activeInHierarchy) { s = SystemPool.Spawn(tmpl, (Vector3)a); segs[k] = s; }
                if (s == null) continue;
                var p = a + d * ((k + 0.5f) / n);
                s.transform.position = new Vector3(p.x, p.y, s.transform.position.z);
                s.transform.rotation = Quaternion.Euler(0f, 0f, ang);
                s.transform.localScale = new Vector3(len / n / 12f, 1f, 1f);
            }
            Clear(segs, n);
        }

        /// <summary>Despawn the segments from index <paramref name="from"/> on.</summary>
        public static void Clear(List<GameObject> segs, int from = 0)
        {
            for (int i = segs.Count - 1; i >= from; i--)
            {
                if (segs[i] != null && segs[i].activeInHierarchy) SystemPool.Despawn(segs[i]);
                segs.RemoveAt(i);
            }
        }

        /// <summary>A bone pile at <paramref name="p"/> (kept clear of walls from <paramref name="from"/>).</summary>
        public static BonePileFx DropPile(Vector2 from, Vector2 p, DamageSource src)
        {
            if (OssivarFx.BonePile == null) return null;
            var go = FxFactory.SpawnOwned(OssivarFx.BonePile, ModUtil.SafePoint(from, p, 4f), src);
            return go != null ? go.GetComponent<BonePileFx>() : null;
        }
    }
}
