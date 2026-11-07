using System;
using System.Collections.Generic;

namespace CrawlFurther.Art
{
    /// <summary>
    /// A sprite sheet (PNG grid plus <see cref="SheetManifest"/>) as a runtime exAtlas. Get one with
    /// <see cref="SpriteSheets.Get"/>; turn its animations into clips with <see cref="ClipBuilder"/> or <see cref="SpriteSheets.MakeClip"/>.
    /// </summary>
    public class SpriteSheet
    {
        /// <summary>The sheet's id: its file name without extension.</summary>
        public readonly string id;

        /// <summary>The atlas the game draws from. Element i is cell i of the grid.</summary>
        public readonly exAtlas atlas;

        /// <summary>The grid and animations read from the sheet's JSON.</summary>
        public readonly SheetManifest manifest;

        readonly Dictionary<string, SheetAnim> m_anims = new Dictionary<string, SheetAnim>(StringComparer.OrdinalIgnoreCase);

        /// <summary>Wrap an atlas you built yourself; <see cref="SpriteSheets.FromTexture"/> does this for a grid texture.</summary>
        public SpriteSheet(string id, exAtlas atlas, SheetManifest manifest)
        {
            this.id = id;
            this.atlas = atlas;
            this.manifest = manifest;
            if (manifest.anims != null) foreach (var a in manifest.anims) m_anims[a.name] = a;
        }

        /// <summary>The animation called <paramref name="name"/> (any case), or null.</summary>
        public SheetAnim Anim(string name)
        {
            SheetAnim a;
            return m_anims.TryGetValue(name, out a) ? a : null;
        }

        /// <summary>True if the sheet has an animation called <paramref name="name"/> (any case).</summary>
        public bool Has(string name) { return m_anims.ContainsKey(name); }
    }
}
