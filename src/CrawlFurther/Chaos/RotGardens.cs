using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Chaos
{
    using CrawlFurther.Art;
    using CrawlFurther.Game;
    using CrawlFurther.Gods;
    using CrawlFurther.Monsters;
    using CrawlFurther.Objects;
    using CrawlFurther.Util;

    /// <summary>
    /// Rot Gardens, the first chaos biome: the Caves gone over to fungus. The rooms are the Caves' (and their big
    /// copies) in plum and mould green, with moss creeping over the floors; the props are glowing caps, puffballs,
    /// rotten logs and mycelium. Hazard: puffballs and bell caps burst at a hit (anyone's) into a spore cloud that dazes
    /// the hero, and while a fight is on, spore drifts float across the room.
    /// </summary>
    public static class RotGardens
    {
        public const string Id = "Rot";
        public const float CloudLife = 3.2f, CloudRx = 20f, CloudRy = 11f;
        public const float DriftEvery = 7f, DriftJitter = 4f, DriftSpeed = 16f, DriftLife = 9f, DriftRx = 24f, DriftRy = 11f;
        /// <summary>After a daze from spores, the hero is safe from spores this long.</summary>
        public const float DazeGap = 2.2f;

        public static BiomeDef Def;
        internal static GameObject Burst, Cloud, Drift;

        static readonly Color32 Moss = new Color32(62, 94, 74, 255), MossLight = new Color32(88, 128, 92, 255), Glow = new Color32(110, 255, 220, 255);

        public static void Register()
        {
            Cloud = FxKit.Visual("BiomeRotCloudFx", "BiomeRotCloud", "Loop", loop: true, lifetime: CloudLife);
            Burst = FxKit.Visual("BiomeRotBurstFx", "BiomeRotBurst", "Burst");
            Drift = FxKit.Visual("BiomeRotDriftFx", "BiomeRotDrift", "Loop", loop: true, lifetime: DriftLife);
            if (Burst != null && Cloud != null) FxFactory.SetEffect(Burst, destroyOnAnimEnd: true, spawnOnDestroy: Cloud, canFlip: false, freeRotate: false);
            // the game spawns what a prop leaves turned to the hit's direction: spores stay upright
            if (Burst != null) FxFactory.OnSpawn[Burst] = go => go.transform.rotation = Quaternion.identity;
            if (Cloud != null) FxFactory.OnSpawn[Cloud] = go =>
            {
                go.transform.rotation = Quaternion.identity;
                (go.GetComponent<SporeCloud>() ?? go.AddComponent<SporeCloud>()).Begin(Vector2.zero, CloudRx, CloudRy);
            };
            if (Drift != null) FxFactory.OnSpawn[Drift] = go => (go.GetComponent<SporeCloud>() ?? go.AddComponent<SporeCloud>()).Begin(Vector2.zero, DriftRx, DriftRy);

            var d = new BiomeDef
            {
                id = Id, name = "Rot Gardens", baseEnvironment = "Caves", chance = 0.35f,
                floor = Recolour.Hsv(0.86f, 0.42f, 0.84f, 0.55f),
                wall = Recolour.Hsv(0.82f, 0.45f, 0.7f, 0.6f),
                floorDetail = MossOver,
                floorNames = new[] { "The Rot Gardens", "Mouldering Halls", "The Spore Beds", "Capwood", "The Soft Rot", "Glowcap Hollow",
                                     "The Mycelium Deep", "Puffball Fields", "The Damp Below", "Gills and Stalks" },
                gameProp = n => n.IndexOf("Stalag", StringComparison.OrdinalIgnoreCase) >= 0 ? Recolour.Hsv(0.8f, 0.3f, 1.05f, 0.6f)
                              : n.IndexOf("Plant", StringComparison.OrdinalIgnoreCase) >= 0 || n.IndexOf("Grass", StringComparison.OrdinalIgnoreCase) >= 0
                                ? Recolour.Hsv(0.47f, 1.2f, 1.15f, 1f) : Recolour.Hsv(0.82f, 0.45f, 0.8f, 0.6f),
                gamePropShare = 0.3f,
                roomSpawned = go => { var r = go.GetComponent<RotRoom>() ?? go.AddComponent<RotRoom>(); r.Reset(); },
            };
            Add(d.decals, PropKit.Decal("BiomeRotMoss1", "BiomeRotMoss1"), 3f);
            Add(d.decals, PropKit.Decal("BiomeRotMoss2", "BiomeRotMoss2"), 3f);
            Add(d.decals, PropKit.Decal("BiomeRotMycelium1", "BiomeRotMycelium1"), 2f);
            Add(d.decals, PropKit.Decal("BiomeRotMycelium2", "BiomeRotMycelium2"), 2f);
            for (int i = 1; i <= 3; i++) Add(d.decals, PropKit.Decal("BiomeRotPins" + i, "BiomeRotPins" + i), 1.5f);
            Add(d.small, PropKit.Still("BiomeRotInkCaps1", "BiomeRotInkCaps1", 8f, 4f), 2f);
            Add(d.small, PropKit.Still("BiomeRotInkCaps2", "BiomeRotInkCaps2", 6f, 4f), 2f);
            Add(d.small, PropKit.Breakable("BiomeRotPuffball1", "BiomeRotPuffball1", 12f, 6f, 1f, Burst), 3f);
            Add(d.small, PropKit.Breakable("BiomeRotPuffball2", "BiomeRotPuffball2", 8f, 4f, 1f, Burst), 2f);
            Add(d.small, PropKit.Decal("BiomeRotEggSacs1", "BiomeRotEggSacs1"), 1.5f);
            Add(d.small, PropKit.Decal("BiomeRotEggSacs2", "BiomeRotEggSacs2"), 1.5f);
            Add(d.large, PropKit.Still("BiomeRotCapParasol", "BiomeRotCapParasol", 10f, 6f), 2f);
            Add(d.large, PropKit.Still("BiomeRotCapParasolSmall", "BiomeRotCapParasolSmall", 8f, 5f), 2.5f);
            Add(d.large, PropKit.Breakable("BiomeRotCapBell", "BiomeRotCapBell", 14f, 7f, 1f, Burst), 2.5f);
            Add(d.large, PropKit.Still("BiomeRotCapShelf", "BiomeRotCapShelf", 18f, 6f), 1.5f);
            Add(d.large, PropKit.Still("BiomeRotLog1", "BiomeRotLog1", 42f, 8f), 1.5f);
            Add(d.large, PropKit.Still("BiomeRotLog2", "BiomeRotLog2", 30f, 8f), 1.5f);
            Add(d.large, PropKit.Still("BiomeRotRoots1", "BiomeRotRoots1", 12f, 6f), 1f);
            Add(d.large, PropKit.Still("BiomeRotRoots2", "BiomeRotRoots2", 12f, 6f), 1f);
            Add(d.feature, PropKit.Still("BiomeRotCapParasolBig", "BiomeRotCapParasol", 10f, 6f), 3f);
            Add(d.feature, PropKit.Breakable("BiomeRotCapBellBig", "BiomeRotCapBell", 14f, 7f, 1f, Burst), 2f);
            Def = d;
            Biomes.Register(d);
            VaultRegistry.Add("Places", "BiomeRot", "Rot Gardens",
                "Chaos floors. Caves gone to fungus. Puffballs and bell caps burst into spores that daze the hero. Spores drift through fights",
                "BiomeRotCapParasol");
        }

        static void Add(List<KeyValuePair<GameObject, float>> into, GameObject p, float w)
        {
            if (p != null) into.Add(new KeyValuePair<GameObject, float>(p, w));
        }

        /// <summary>Moss creeping over the floor picture: soft-edged patches in two greens, with a few glowing specks.</summary>
        static void MossOver(Color32[] px, int w, int h, System.Random rng)
        {
            int patches = Mathf.Clamp(w * h / 2400, 3, 40);
            for (int p = 0; p < patches; p++)
            {
                int cx = rng.Next(w), cy = rng.Next(h);
                float rx = 6 + rng.Next(18), ry = rx * (0.45f + (float)rng.NextDouble() * 0.3f);
                var col = rng.Next(3) == 0 ? MossLight : Moss;
                for (int y = Mathf.Max(0, (int)(cy - ry - 2)); y < Mathf.Min(h, (int)(cy + ry + 3)); y++)
                    for (int x = Mathf.Max(0, (int)(cx - rx - 2)); x < Mathf.Min(w, (int)(cx + rx + 3)); x++)
                    {
                        int i = y * w + x;
                        if (px[i].a < 200) continue;
                        float dx = (x - cx) / rx, dy = (y - cy) / ry, e = dx * dx + dy * dy;
                        // ragged edge: a hash of the pixel decides the rim
                        float n = ((x * 73856093 ^ y * 19349663 ^ p * 83492791) & 1023) / 1023f;
                        if (e > 0.75f + n * 0.5f) continue;
                        float k = e < 0.5f ? 0.8f : 0.55f;
                        px[i] = Mix(px[i], col, k);
                    }
                if (rng.Next(3) == 0)
                {
                    int gx = Mathf.Clamp(cx + rng.Next(-4, 5), 0, w - 1), gy = Mathf.Clamp(cy + rng.Next(-2, 3), 0, h - 1);
                    int gi = gy * w + gx;
                    if (px[gi].a >= 200) px[gi] = Mix(px[gi], Glow, 0.7f);
                }
            }
        }

        static Color32 Mix(Color32 a, Color32 b, float k)
        {
            return new Color32((byte)(a.r + (b.r - a.r) * k), (byte)(a.g + (b.g - a.g) * k), (byte)(a.b + (b.b - a.b) * k), a.a);
        }

        /// <summary>Spores: is the hero inside this ellipse (centred a little above the effect's feet)?</summary>
        internal static bool HeroIn(Vector2 c, float rx, float ry, out Player hero)
        {
            hero = null;
            var h = ModUtil.Hero();
            if (h == null) return false;
            hero = h.GetComponent<Player>();
            if (hero == null) return false;
            var d = (Vector2)h.transform.position - c;
            return (d.x * d.x) / (rx * rx) + (d.y * d.y) / (ry * ry) <= 1f;
        }

        static float s_lastDaze = -99f;

        internal static void Daze(GameObject from, Player hero)
        {
            if (hero == null || ModStatus.Daze == null || Time.time - s_lastDaze < DazeGap) return;
            var hp = hero.GetComponent<Health>();
            if (hp != null && !hp.IsAlive()) return;
            s_lastDaze = Time.time;
            try { hero.AddStatus(ModStatus.Daze, new DamageSource(from, from, null), "rotspore"); }
            catch (Exception e) { Plugin.Log.LogWarning("Rot spores: " + e.Message); }
        }
    }

    /// <summary>A spore cloud or drift: dazes the hero it touches (once per <see cref="RotGardens.DazeGap"/>);
    /// a drift also floats along its <see cref="vel"/>.</summary>
    public class SporeCloud : MonoBehaviour
    {
        public Vector2 vel;
        float rx = 20f, ry = 10f, born;

        public void Begin(Vector2 velocity, float radiusX, float radiusY)
        {
            vel = velocity; rx = radiusX; ry = radiusY; born = Time.time;
        }

        void Update()
        {
            if (vel != Vector2.zero) transform.position += (Vector3)(vel * Time.deltaTime);
            if (Time.time - born < 0.25f) return;   // the burst gets a beat before it bites
            Player hero;
            if (RotGardens.HeroIn((Vector2)transform.position + new Vector2(0f, 6f), rx, ry, out hero)) RotGardens.Daze(gameObject, hero);
        }
    }

    /// <summary>On every Rot Gardens room: while a fight is on in it, spore drifts float across it now and then.</summary>
    public class RotRoom : MonoBehaviour
    {
        float next;

        public void Reset() { next = 0f; }

        void Update()
        {
            if (RotGardens.Drift == null || !ModUtil.DoorsLocked()) { next = 0f; return; }
            Room room = null;
            try { room = SystemLevel.GetCurrentRoom(); } catch { }
            if (room == null || room.gameObject != gameObject) return;
            if (next <= 0f) { next = Time.time + RotGardens.DriftEvery * 0.5f; return; }
            if (Time.time < next) return;
            next = Time.time + RotGardens.DriftEvery + UnityEngine.Random.value * RotGardens.DriftJitter;
            SendDrift(room);
        }

        static void SendDrift(Room room)
        {
            List<Vector2> pts = null;
            try { pts = room.GetRoomBounds(); } catch { }
            if (pts == null || pts.Count < 3) return;
            float x0 = float.MaxValue, x1 = float.MinValue, y0 = float.MaxValue, y1 = float.MinValue;
            foreach (var p in pts) { x0 = Mathf.Min(x0, p.x); x1 = Mathf.Max(x1, p.x); y0 = Mathf.Min(y0, p.y); y1 = Mathf.Max(y1, p.y); }
            bool fromLeft = UnityEngine.Random.value < 0.5f;
            for (int i = 0; i < 10; i++)
            {
                var at = new Vector2(fromLeft ? x0 + 14f : x1 - 14f, Mathf.Lerp(y0 + 12f, y1 - 12f, UnityEngine.Random.value));
                bool inside = true;
                try { inside = room.IsPointInRoom(at); } catch { }
                if (!inside) continue;
                var g = SystemPool.Spawn(RotGardens.Drift, at);
                if (g == null) return;
                var c = g.GetComponent<SporeCloud>() ?? g.AddComponent<SporeCloud>();
                c.Begin(new Vector2((fromLeft ? 1f : -1f) * RotGardens.DriftSpeed, (UnityEngine.Random.value - 0.5f) * 4f), RotGardens.DriftRx, RotGardens.DriftRy);
                return;
            }
        }
    }
}
