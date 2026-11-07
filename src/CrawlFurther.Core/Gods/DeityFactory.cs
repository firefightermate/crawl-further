using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Gods
{
    using CrawlFurther.Art;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Util;

    /// <summary>
    /// Adds gods to the game. Mod gods go into SystemDeity's list just before the trial gods, so vanilla gods keep their
    /// indices and the god select lists them after the vanilla ones (in registration order).
    /// </summary>
    public static class DeityFactory
    {
        /// <summary>Names of the gods registered here, in order.</summary>
        public static readonly List<string> BuiltNames = new List<string>();
        /// <summary>God name to its portrait sheet.</summary>
        public static readonly Dictionary<string, string> ArtByName = new Dictionary<string, string>();

        static readonly Dictionary<string, Deity> s_built = new Dictionary<string, Deity>();

        /// <summary>
        /// Build a god and add it to the game: its monsters (when <see cref="GodDef.monsters"/> is set), tips and pause
        /// page, then the Deity itself. Call it from a content pack (ContentManager.AddPack), which runs once the game's
        /// systems are up. Registering the same name twice returns the first god.
        /// </summary>
        public static Deity Register(GodDef def)
        {
            Deity done;
            if (s_built.TryGetValue(def.name, out done))
            {
                FurtherCore.Log.LogWarning("God " + def.name + " is already registered");
                return done;
            }
            if (def.monsters != null) BuildMonsters(def);
            AddTips(def);
            var d = Build(def);
            s_built[def.name] = d;
            return d;
        }

        static void BuildMonsters(GodDef def)
        {
            foreach (var m in def.monsters)
            {
                if (def.perk != null)
                {
                    var own = m.customize;
                    var perk = def.perk;
                    m.customize = (go, p) => { if (own != null) own(go, p); perk(go, p); };
                }
                MonsterFactory.Build(m);
            }
            MonsterFactory.LinkEvolutions(def.monsters);
        }

        static void AddTips(GodDef def)
        {
            if (def.tips != null)
                foreach (var kv in def.tips) TipRegistry.Add(kv.Key, kv.Value, def.pausePage != null ? def.pausePage.id : null);
            if (def.pausePage != null) TipRegistry.AddTopic(def.pausePage);
        }

        static Deity Build(GodDef def)
        {
            var deities = SystemDeity.GetDeities();
            var template = SystemDeity.GetDeity(def.copySoundsFrom) ?? deities[0];
            var d = new Deity();
            R.Set(d, "m_name", def.name);
            R.Set(d, "m_text", def.text);
            R.Set(d, "m_textFlavour", def.flavour);
            R.Set(d, "m_winText", def.winText ?? R.Get<string>(template, "m_winText"));
            R.Set(d, "m_soundSelected", R.Get<AudioCue>(template, "m_soundSelected"));
            R.Set(d, "m_winHeroAnimation", R.Get<exSpriteAnimClip>(template, "m_winHeroAnimation"));
            R.Set(d, "m_gold", def.gold);
            R.Set(d, "m_heroStatModifiers", new List<HeroStatModifier>());
            R.Set(d, "m_startingPowerups", new Powerup[0]);
            R.Set(d, "m_startingWeapon", null);

            var src = def.copyModifiersFrom != null ? SystemDeity.GetDeity(def.copyModifiersFrom) : null;
            R.Set(d, "m_modifiers", def.modifiers ?? (src != null ? R.Get<PlayerModifier[]>(src, "m_modifiers") : new PlayerModifier[0]));

            var mons = new List<GameObject>();
            foreach (var id in def.startingMonsters ?? new string[0])
            {
                Player p;
                if (!MonsterFactory.Built.TryGetValue(id, out p)) p = MonsterFactory.FindVanilla(id);
                if (p != null) mons.Add(p.gameObject); else FurtherCore.Log.LogWarning("God starter missing: " + id);
            }
            R.Set(d, "m_startingMonsters", mons.ToArray());

            // the god select looks portraits up by clip name, so every god gets its own
            var sheet = SpriteSheets.Get(def.portraitArt);
            var tmplClip = R.Get<exSpriteAnimClip>(template, "m_portrait");
            exSpriteAnimClip clip = null;
            if (sheet != null)
                clip = SpriteSheets.MakeClip(sheet, sheet.Has("Portrait") ? "Portrait" : "Idle", null, "ModDeity_" + def.name);
            if (clip == null) clip = tmplClip;
            else clip.wrapMode = clip.frameInfos.Count > 1 ? WrapMode.Loop : (tmplClip != null ? tmplClip.wrapMode : WrapMode.Once);
            R.Set(d, "m_portrait", clip);

            int idx = Insert(d);
            BuiltNames.Add(def.name);
            ArtByName[def.name] = def.portraitArt;
            FurtherCore.Log.LogInfo("Registered deity " + def.name + " at index " + idx + " with " + mons.Count + " starters");
            return d;
        }

        /// <summary>Put a deity into SystemDeity's list just before the trial gods; returns its index.</summary>
        public static int Insert(Deity d)
        {
            var deities = SystemDeity.GetDeities();
            int idx = deities.FindIndex(x => x.GetIsTrial());
            if (idx < 0) idx = deities.Count;
            deities.Insert(idx, d);
            return idx;
        }
    }
}
