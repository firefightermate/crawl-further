using UnityEngine;

namespace CrawlFurther.Art
{
    /// <summary>Texture and atlas copies for recolouring vanilla art.</summary>
    static class SpriteUtil
    {
        /// <summary>
        /// A readable copy of <paramref name="src"/>. The game's atlas textures are not readable from script, so the copy
        /// goes through the GPU (Blit, then ReadPixels).
        /// </summary>
        public static Texture2D CopyTexture(Texture src)
        {
            var rt = RenderTexture.GetTemporary(src.width, src.height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Linear);
            var prev = RenderTexture.active;
            Graphics.Blit(src, rt);
            RenderTexture.active = rt;
            var t = new Texture2D(src.width, src.height, TextureFormat.ARGB32, false);
            t.ReadPixels(new Rect(0, 0, src.width, src.height), 0, 0);
            t.Apply(false);
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
            t.filterMode = FilterMode.Point;
            t.wrapMode = TextureWrapMode.Clamp;
            return t;
        }

        /// <summary>An atlas over <paramref name="tex"/> with the given elements and a copy of <paramref name="templateMat"/>, kept for the session.</summary>
        public static exAtlas MakeAtlas(string name, Texture2D tex, exAtlas.Element[] elements, Material templateMat)
        {
            var a = ScriptableObject.CreateInstance<exAtlas>();
            a.name = name;
            a.texture = tex;
            a.elements = elements;
            var m = new Material(templateMat);
            m.name = name + "_Mat";
            m.mainTexture = tex;
            a.material = m;
            SpriteSheets.Keep(a);
            SpriteSheets.Keep(m);
            SpriteSheets.Keep(tex);
            return a;
        }
    }
}
