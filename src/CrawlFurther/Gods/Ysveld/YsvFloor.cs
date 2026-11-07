using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Content.Gods;
    using CrawlFurther.Util;

    /// <summary>
    /// Ysveld's perk: floor ice. Every slab of Ysveld ice is one entry here (an ellipse 11 x 6 px round its centre, drawn
    /// as a FxYsvFloe slab at floor depth: under every character and shadow, over the floor).
    ///
    /// BLIZZARD: while a living Ysveld monster is in the hero's room, a blizzard sweeps the room 1.5 s after the fight
    /// starts and then every 12 s (8 s while a Pale Empress lives: Storm Queen). Three snow gusts blow across and lay ice
    /// paths along the wind: 3 paths the first time, 2 after. With an Empress in the room the paths run toward the hero.
    /// Blizzard ice lasts the fight: 3 s after the last Ysveld monster in the room is gone (or at once when the hero
    /// leaves the room) every slab thaws. Other ice (death patches, the Silkmoth's wake, the Knight's cleave, the
    /// Colossus' road) is timed.
    /// </summary>
    public class YsvFloor : MonoBehaviour
    {
        public const int Variants = 4, MaxBlizzardSlabs = 48, MaxOtherSlabs = 36;
        public const float RX = 11f, RY = 6f, Step = 12f, FloorZ = 90f, FirstDelay = 1.5f, Interval = 12f, QueenInterval = 8f,
                           ThawDelay = 3f, GaleTime = 0.9f, KitIceLife = 6.5f, DeathIceLife = 8f, SlabGap = 0.04f;

        class Slab { public GameObject go; public Vector2 pos; public int v; public float flip; public float expire; public int path; }

        static YsvFloor s_inst;
        static readonly List<Slab> s_slabs = new List<Slab>();
        Room m_room;
        bool m_fight;
        float m_lastFight, m_scan;
        int m_blizzards, m_pathId = 1;

        /// <summary>Time.time of the next blizzard while a fight is on, or -1.</summary>
        public static float NextBlizzard { get; private set; }

        public static int Count { get { return s_slabs.Count; } }

        public static void Ensure()
        {
            if (s_inst != null) return;
            var go = new GameObject("CrawlMod_YsveldFloor");
            DontDestroyOnLoad(go);
            s_inst = go.AddComponent<YsvFloor>();
            NextBlizzard = -1f;
        }

        /// <summary>Is this point on Ysveld ice?</summary>
        public static bool Covers(Vector2 p)
        {
            for (int i = s_slabs.Count - 1; i >= 0; i--)
            {
                var d = p - s_slabs[i].pos;
                if ((d.x * d.x) / (RX * RX) + (d.y * d.y) / (RY * RY) <= 1f) return true;
            }
            return false;
        }

        /// <summary>Centres of the slabs within <paramref name="radius"/> px of <paramref name="c"/>, nearest first.</summary>
        public static List<Vector2> Near(Vector2 c, float radius)
        {
            var list = new List<Vector2>();
            foreach (var s in s_slabs) if ((s.pos - c).sqrMagnitude <= radius * radius) list.Add(s.pos);
            list.Sort((a, b) => (a - c).sqrMagnitude.CompareTo((b - c).sqrMagnitude));
            return list;
        }

        /// <summary>Lay one slab (variant v &lt; 0: random). life &lt;= 0: blizzard ice (lasts the fight, path = its path id).</summary>
        public static void Lay(Vector2 p, int v, float life, int path)
        {
            Ensure();
            if (v < 0) v = Random.Range(0, Variants);
            var tmpl = YsveldFx.FloeLay[v % Variants];
            float flip = Random.value < 0.5f ? -1f : 1f;
            GameObject go = null;
            if (tmpl != null)
            {
                go = SystemPool.Spawn(tmpl, new Vector3(p.x, p.y, Z(p)));
                if (go != null) { go.transform.position = new Vector3(p.x, p.y, Z(p)); go.transform.localScale = new Vector3(flip, 1f, 1f); }
            }
            if (go == null) return;            // no art, no ice: never an invisible slab
            s_slabs.Add(new Slab { go = go, pos = p, v = v % Variants, flip = flip, expire = life > 0f ? Time.time + life : -1f, path = path });
            var hero = ModUtil.Hero();
            if (hero != null && hero.GetComponent<YsvSlide>() == null) hero.AddComponent<YsvSlide>();
            // keep the floor readable: the oldest slabs of the same kind thaw first
            int blizzard = 0, other = 0;
            foreach (var s in s_slabs) if (s.expire < 0f) blizzard++; else other++;
            for (int i = 0; i < s_slabs.Count && (blizzard > MaxBlizzardSlabs || other > MaxOtherSlabs); i++)
            {
                var s = s_slabs[i];
                if (s.expire < 0f && blizzard > MaxBlizzardSlabs) { blizzard--; Thaw(i--, true); }
                else if (s.expire >= 0f && other > MaxOtherSlabs) { other--; Thaw(i--, true); }
            }
        }

        /// <summary>Lay <paramref name="count"/> timed slabs in a short row across <paramref name="c"/> (kit and death ice).</summary>
        public static void Patch(Vector2 c, int count, float life)
        {
            for (int i = 0; i < count; i++)
            {
                float dx = (i - (count - 1) * 0.5f) * Step;
                Lay(ModUtil.SafePoint(c, c + new Vector2(dx, (i % 2) * 1.5f), 4f), -1, life, 0);
            }
        }

        static Room CurrentRoom()
        {
            try { return Singleton<SystemLevel>.Get != null ? SystemLevel.GetCurrentRoom() : null; } catch { return null; }
        }

        // upper slabs draw over lower ones (so each slab's lit top rim lies on its own ice), all at floor depth
        static float Z(Vector2 p) { return FloorZ - Mathf.Repeat(p.y, 1000f) * 0.001f; }

        /// <summary>Floor depth for a floor-level visual at <paramref name="p"/> (just over the ice).</summary>
        public static float FloorDepth(Vector2 p) { return Z(p) - 0.5f; }

        static void Thaw(int i, bool melt)
        {
            var s = s_slabs[i];
            s_slabs.RemoveAt(i);
            if (s.go != null && s.go.activeInHierarchy) SystemPool.Despawn(s.go);
            if (!melt) return;
            var m = YsveldFx.FloeMelt[s.v];
            if (m == null) return;
            var go = SystemPool.Spawn(m, new Vector3(s.pos.x, s.pos.y, Z(s.pos)));
            if (go != null) { go.transform.position = new Vector3(s.pos.x, s.pos.y, Z(s.pos)); go.transform.localScale = new Vector3(s.flip, 1f, 1f); }
        }

        static void ThawAll(bool melt) { for (int i = s_slabs.Count - 1; i >= 0; i--) Thaw(i, melt); }

        static bool AnyYsveldIn(Room room)
        {
            foreach (var m in YsvMonster.Living)
            {
                if (m == null || !m.Alive || !room.IsPointInRoom(m.transform.position)) continue;
                // a custom god built from Ysveld starters with another god's perk: no blizzard from them
                bool swapped = false;
                try { swapped = CustomGod.PerkSwappedAway(m.GetComponent<Player>(), "Ysveld"); } catch { }
                if (!swapped) return true;
            }
            return false;
        }

        void Update()
        {
            for (int i = s_slabs.Count - 1; i >= 0; i--)
            {
                var s = s_slabs[i];
                if (s.go == null || !s.go.activeInHierarchy) { s_slabs.RemoveAt(i); continue; }   // a level change took it
                if (s.expire >= 0f && Time.time >= s.expire) Thaw(i, true);
            }
            m_scan -= Time.deltaTime;
            if (m_scan > 0f) return;
            m_scan = 0.25f;
            var hero = ModUtil.Hero();
            var hh = hero != null ? hero.GetComponent<Health>() : null;
            var room = hero != null ? CurrentRoom() : null;
            if (room != m_room)
            {
                ThawAll(false);                // a new room (or level): the old room's ice is out of sight
                m_room = room; m_fight = false; NextBlizzard = -1f; StopAllCoroutines();
            }
            bool fight = room != null && hero != null && hh != null && hh.IsAlive() && AnyYsveldIn(room);
            if (fight)
            {
                bool queen = EmpressStormQueen.AnyIn(room);
                if (!m_fight) { m_fight = true; m_blizzards = 0; NextBlizzard = Time.time + FirstDelay; }
                // Storm Queen: an Empress arriving mid-fight pulls the next blizzard in
                else if (queen && NextBlizzard - Time.time > QueenInterval) NextBlizzard = Time.time + QueenInterval;
                m_lastFight = Time.time;
                if (Time.time >= NextBlizzard)
                {
                    NextBlizzard = Time.time + (queen ? QueenInterval : Interval);
                    StartCoroutine(Blizzard(room, hero, queen));
                }
            }
            else if (m_fight && Time.time - m_lastFight >= ThawDelay)
            {
                m_fight = false;
                NextBlizzard = -1f;
                StopAllCoroutines();
                StartCoroutine(ThawBlizzard());
            }
        }

        IEnumerator ThawBlizzard()
        {
            // staggered, so the floor clears like melting rather than blinking out
            for (int i = s_slabs.Count - 1; i >= 0; i--)
            {
                if (i >= s_slabs.Count) continue;
                if (s_slabs[i].expire >= 0f) continue;
                Thaw(i, true);
                yield return new WaitForSeconds(0.03f);
            }
        }

        IEnumerator Blizzard(Room room, GameObject hero, bool queen)
        {
            int n = m_blizzards++ == 0 ? 3 : 2;
            float wind = Random.value < 0.5f ? -1f : 1f;
            Vector2 hp = hero.transform.position;
            // the gusts: three bands of driven snow crossing the hero's view, upwind to downwind
            if (YsveldFx.Gale != null)
                for (int g = 0; g < 3; g++)
                {
                    var at = new Vector2(hp.x - wind * (150f + g * 30f), hp.y - 55f + g * 52f + Random.Range(-8f, 8f));
                    var go = SystemPool.Spawn(YsveldFx.Gale, new Vector3(at.x, at.y, -15f));
                    if (go == null) continue;
                    go.transform.position = new Vector3(at.x, at.y, -15f);
                    go.transform.localScale = new Vector3(wind, 1f, 1f);
                    var gf = go.GetComponent<YsvGaleFx>();
                    if (gf != null) gf.wind = wind;
                }
            yield return new WaitForSeconds(0.25f);
            for (int k = 0; k < n; k++)
            {
                var pts = queen && hero != null ? PathToward(room, hero.transform.position) : Path(room, wind);
                if (pts == null) continue;
                int id = m_pathId++;
                if (!queen && wind < 0f) pts.Reverse();      // laid from the upwind end
                foreach (var p in pts)
                {
                    if (CurrentRoom() != room) yield break;
                    Lay(p, -1, 0f, id);
                    yield return new WaitForSeconds(SlabGap);
                }
            }
        }

        /// <summary>A gently bending line of slab centres running with the wind (east or west +-35 deg), 7-11 slabs,
        /// stopped by walls and the room's edge; null if no spot gave at least 5.</summary>
        static List<Vector2> Path(Room room, float wind)
        {
            for (int tries = 0; tries < 5; tries++)
            {
                Vector2 p = room.CalcRandomPointInRoom(20f);
                if (Covers(p)) continue;
                var pts = Walk(room, p, Random.Range(-35f, 35f), Random.Range(7, 12));
                if (pts.Count >= 5) return pts;
            }
            return null;
        }

        /// <summary>Storm Queen: a path that starts somewhere 50-110 px from the hero and runs at him.</summary>
        static List<Vector2> PathToward(Room room, Vector2 hero)
        {
            for (int tries = 0; tries < 6; tries++)
            {
                var off = (Vector2)(Quaternion.Euler(0f, 0f, Random.Range(0f, 360f)) * Vector2.right) * Random.Range(50f, 110f);
                Vector2 p = hero + off;
                if (!room.IsPointInRoom(p) || !ModUtil.Clear(hero, p)) continue;
                var d = hero - p;
                var pts = Walk(room, p, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg, Random.Range(7, 11), 10f);
                if (pts.Count >= 5) return pts;
            }
            return null;
        }

        static List<Vector2> Walk(Room room, Vector2 p, float ang, int want, float wobble = 12f)
        {
            float a0 = ang;
            var pts = new List<Vector2> { p };
            for (int i = 1; i < want; i++)
            {
                ang = Mathf.Clamp(ang + Random.Range(-wobble, wobble), a0 - 50f, a0 + 50f);
                float a = ang * Mathf.Deg2Rad;
                float step = Step - 4f * Mathf.Abs(Mathf.Sin(a));      // steeper runs pack closer (slabs are wider than tall)
                var q = pts[pts.Count - 1] + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * step;
                if (!room.IsPointInRoom(q) || !ModUtil.Clear(pts[pts.Count - 1], q) || ModUtil.SafePoint(pts[pts.Count - 1], q, 8f) != q) break;
                pts.Add(q);
            }
            return pts;
        }

        void OnDestroy() { if (s_inst == this) s_inst = null; }
    }
}
