using BepInEx;
using CrawlFurther;

namespace ExampleGod
{
    /// <summary>
    /// The BepInEx plugin. Awake only registers the mod with Core; everything that touches the game runs later, in
    /// <see cref="OnBooted"/>. This class must not name a game type anywhere (fields included): on Unity 5.4, loading
    /// Assembly-CSharp before the engine has registered its scripts breaks every script in the game.
    /// </summary>
    [BepInPlugin(GUID, NAME, VERSION)]
    [BepInDependency(FurtherCore.GUID)]
    public class ExampleGodPlugin : BaseUnityPlugin
    {
        public const string GUID = "com.example.crawl.examplegod";
        public const string NAME = "Example God";
        public const string VERSION = "1.0.0";

        static FurtherMod s_mod;

        void Awake()
        {
            s_mod = Further.AddMod(this, OnBooted);
        }

        /// <summary>Runs once the game has booted, before any content pack.</summary>
        static void OnBooted()
        {
            s_mod.PatchAll();
            GlimmerPack.Setup();
            Further.AddPack("Glimmer", GlimmerPack.Register);
            GlimmerEvents.Subscribe(s_mod.Log);
            GlimmerTests.Register();
        }
    }
}
