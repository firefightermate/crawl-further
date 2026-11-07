using System;
using System.IO;
using UnityEngine;

namespace CrawlFurther.Compat
{
    /// <summary>
    /// Naming rules that keep mod art working with Online Crawl. Its clients rebuild the host's picture from names:
    /// a texture is matched by name against what the client has loaded, a material is rebuilt from a loaded material of
    /// the same name (or its shader) plus a few captured properties, and only ex2D meshes and textures it swaps itself
    /// are watched for changes. So:
    /// <list type="bullet">
    /// <item>A texture loaded from a sheet file is named <see cref="SheetTexture"/> ("Mod_&lt;sheet&gt;"): a client that
    /// has not loaded it yet reads art/&lt;sheet&gt;.png from its own install instead of asking the host for it.</item>
    /// <item>A texture composed at run time is named <see cref="ComposedTexture"/>: a key that names its exact pixels, so
    /// a client never reuses a different picture of the same name. Such names never match a file.</item>
    /// <item>A texture repainted while it is shown keeps an empty name (no client can hold a stale copy) and is passed to
    /// <see cref="CompatOnline.TextureChanged"/> after every Apply.</item>
    /// <item>A Mesh edited by hand (not an ex2D sprite) is passed to <see cref="CompatOnline.MeshChanged"/> after every edit.</item>
    /// <item>Atlases and materials of a sheet are "ModAtlas_&lt;sheet&gt;" and "ModMat_&lt;sheet&gt;".</item>
    /// </list>
    /// Host and clients must run the same mod versions: a file of the same name but other pixels would be used as is.
    /// </summary>
    public static class OnlineNames
    {
        public const string TexturePrefix = "Mod_";
        public const string AtlasPrefix = "ModAtlas_";
        public const string MaterialPrefix = "ModMat_";
        /// <summary>Separates the parts of a composed texture's key; it cannot appear in a file name.</summary>
        public const char KeySeparator = '|';

        static readonly char[] s_badName = Path.GetInvalidFileNameChars();

        /// <summary>The texture name for sheet <paramref name="sheetId"/> (art/&lt;sheetId&gt;.png).</summary>
        public static string SheetTexture(string sheetId) { return TexturePrefix + sheetId; }

        /// <summary>The texture name for pixels composed at run time from <paramref name="parts"/> (each part a
        /// sheet id, colour key or choice): equal parts must mean equal pixels.</summary>
        public static string ComposedTexture(params string[] parts) { return TexturePrefix + string.Join(KeySeparator.ToString(), parts); }

        /// <summary>The atlas name for a sheet.</summary>
        public static string Atlas(string sheetId) { return AtlasPrefix + sheetId; }

        /// <summary>The material name for a sheet.</summary>
        public static string Material(string sheetId) { return MaterialPrefix + sheetId; }

        /// <summary>True for a texture made from mod art (named by these rules).</summary>
        public static bool IsModTexture(Texture t) { return t != null && t.name != null && t.name.StartsWith(TexturePrefix, StringComparison.Ordinal); }

        /// <summary>The sheet a texture name loads from, or null for a composed or foreign name.</summary>
        public static string SheetOf(string textureName)
        {
            if (string.IsNullOrEmpty(textureName) || textureName.Length <= TexturePrefix.Length
                || !textureName.StartsWith(TexturePrefix, StringComparison.Ordinal)) return null;
            string id = textureName.Substring(TexturePrefix.Length);
            return id.IndexOfAny(s_badName) >= 0 ? null : id;
        }
    }
}
