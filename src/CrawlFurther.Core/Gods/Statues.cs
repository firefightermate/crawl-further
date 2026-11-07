using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Monster statues: rooms between fights sometimes hold stone statues a ghost can step into to become that monster.
    /// They come from the vanilla "EnemyGroupStatue" spawn group (big late-tree monsters). Every mod final (a monster at
    /// the last tier's damage) with a carved statue joins it: the statue is anim "Statue_&lt;art sheet&gt;" on one of the
    /// sheets in <see cref="Sheets"/>.
    ///
    /// Statue art: the MonsterStatue prop's sprite is anchored BotCenter with useTextureOffset, so the bottom-centre of
    /// the frame's untrimmed canvas sits on the prop's floor point. Draw untrimmed cells with the plinth's bottom row on
    /// the cell's last row and the plinth centred, as vanilla statue canvases are; the prop's collider (15 x 6 at y 2.6)
    /// and selection marker (+10) then line up without any offset.
    /// </summary>
    public static class Statues
    {
        /// <summary>Weight of each mod final in the statue group (vanilla entries are 20-100, most 100).</summary>
        public static float Chance = 30f;

        /// <summary>True for a final (by prefab name) that statue rooms never offer; it still gets its statue art.</summary>
        public static Func<string, bool> Exclude;

        /// <summary>Sheets holding carved statues; add yours before the game's systems are up (from your mod's start callback).</summary>
        public static readonly List<string> Sheets = new List<string>();

        /// <summary>Put every mod final with a statue into the statue group. Runs once after all content packs.</summary>
        public static void Register()
        {
            SpawnGroup group = null;
            foreach (var g in Resources.FindObjectsOfTypeAll<SpawnGroup>())
                if (g.gameObject.name == "EnemyGroupStatue" && !g.gameObject.scene.IsValid()) { group = g; break; }
            if (group == null) { FurtherCore.Log.LogWarning("Statues: EnemyGroupStatue not found"); return; }
            var items = R.Get<List<SpawnItem>>(group, "m_items");
            if (items == null || items.Count == 0) { FurtherCore.Log.LogWarning("Statues: statue group is empty"); return; }
            var sheets = new List<SpriteSheet>();
            foreach (var id in Sheets)
            {
                var sh = SpriteSheets.Get(id);
                if (sh != null) sheets.Add(sh);
                else FurtherCore.Log.LogWarning("Statues: statue sheet " + id + " missing");
            }
            items.RemoveAll(i => i != null && i.m_object != null && Excluded(i.m_object.name));
            var like = items[0];
            int added = 0;
            var skipped = new List<string>();
            foreach (var kv in MonsterFactory.Tier)
            {
                if (kv.Value < 3) continue;          // finals only
                Player p = null;
                foreach (var b in MonsterFactory.Built.Values) if (b != null && b.gameObject.name == kv.Key) { p = b; break; }
                if (p == null) continue;
                // an excluded final still gets its statue art, it just never stands in a statue room
                if (Excluded(kv.Key)) { GiveStatueClip(p, sheets); continue; }
                if (!GiveStatueClip(p, sheets)) { skipped.Add(kv.Key); continue; }
                if (items.Exists(i => i != null && i.m_object == p.gameObject)) continue;
                var it = R.Clone(like);
                it.m_object = p.gameObject;
                it.m_chance = Chance;
                items.Add(it);
                added++;
            }
            FurtherCore.Log.LogInfo("Statues: " + added + " mod finals can appear as monster statues");
            if (skipped.Count > 0)
                FurtherCore.Log.LogWarning("Statues: no statue frame for " + string.Join(", ", skipped.ToArray()) + "; left out of the statue group");
        }

        /// <summary>True for a final that statue rooms never offer (<see cref="Exclude"/>). Register takes such finals
        /// out of the group again if something put them in.</summary>
        public static bool Excluded(string prefabName)
        {
            return Exclude != null && Exclude(prefabName);
        }

        /// <summary>The art sheet a mod monster was built from (via its idle clip's atlas).</summary>
        static string ArtSheetOf(Player p)
        {
            foreach (var f in new[] { "m_animationIdle", "m_portraitAnim", "m_animationRun" })
            {
                var c = R.Get<exSpriteAnimClip>(p, f);
                if (c == null || c.frameInfos == null || c.frameInfos.Count == 0) continue;
                var s = SpriteSheets.ByAtlas(c.frameInfos[0].atlas);
                if (s != null) return s.id;
            }
            return null;
        }

        /// <summary>
        /// Point the prefab's m_animationStatue at its carved statue. Statue props are pooled and their exSpriteAnimation
        /// looks clips up by name, so every monster gets its own clip name ("ModStatue_&lt;sheet&gt;").
        /// </summary>
        static bool GiveStatueClip(Player p, List<SpriteSheet> sheets)
        {
            string art = ArtSheetOf(p);
            if (art == null) return false;
            var statues = sheets.Find(s => s.Has("Statue_" + art));
            if (statues == null) return false;
            string clipName = "ModStatue_" + art;
            var cur = p.GetAnimationStatue();
            if (cur != null && cur.name == clipName) return true;              // Register already ran
            var clip = SpriteSheets.MakeClip(statues, "Statue_" + art, cur, clipName);
            if (clip == null) return false;
            clip.wrapMode = WrapMode.Loop;                                      // one still frame, held
            clip.eventInfos = new List<exSpriteAnimClip.EventInfo>();
            R.Set(p, "m_animationStatue", clip);
            return true;
        }
    }
}
