using System.Collections.Generic;

namespace CrawlFurther.Content.Tips
{
    using CrawlFurther.UI;

    /// <summary>
    /// The text every monster tip shows, keyed by prefab name (instances drop their "(Clone)" suffix first).
    /// Lines are written for the player who IS the monster ("Pull the hero to you"). The renderer adds "Attack: ",
    /// "Special: " and "Passive: " in front, and (until 0.9.1) a " (MOD)" tag after mod names (round
    /// brackets: the game's GUIText deletes any square-bracketed word). Every line + its label stays within 60 characters (a passive may take a second line of up to 60),
    /// and only characters every HUD font has are used (CrawlSmall lacks the percent sign, braces, bar and tilde).
    /// This file holds the vanilla monsters and vanilla boss parts, worked out from the prefab dump (attack clips,
    /// their effect objects, damage, statuses, projectile motion). Every mod monster, minion, ghost blob and mod boss
    /// part lives in data/tips/tips_*.json, merged by tools/merge_tips.py into MonsterTipsGenerated.cs (which also checks
    /// lengths, characters and that every MonsterDef has a tip). Boss parts are keyed "BossPrefab/PartName".
    /// </summary>
    public static partial class MonsterTipsData
    {
        public static readonly Dictionary<string, MonsterTip> Tips = new Dictionary<string, MonsterTip>();
        /// <summary>Prefabs that share another prefab's moveset (challenge / tutorial copies, slime colours).</summary>
        public static readonly Dictionary<string, string> Alias = new Dictionary<string, string>();

        const string None = "none";

        static void T(string key, string name, string attack, string special, string passive = null) { Tips[key] = new MonsterTip(name, attack, special, passive); }
        static void A(string key, string sameAs) { Alias[key] = sameAs; }

        static MonsterTipsData()
        {
            // ================================================================ vanilla: starters and their trees
            T("EnemyGnome", "Gnome", "Lunge in and stab up close", "Drop a bear trap that snaps shut on the hero");
            T("EnemyGoblin", "Goblin", "Throw a fast dagger", "Toss a bomb that explodes and stuns");
            T("EnemyForestShaman_Shield", "Shield Shaman", "Blow a fast dart", "Drop a spiked shield that knocks the hero back");
            T("EnemyForestShaman_Turret", "Totem Shaman", "Blow a fast dart", "Plant a totem turret that lasts a while");
            T("EnemyOrc", "Orc", "Two-hit sword combo", "Dodge roll, invulnerable while rolling");
            T("EnemyTroll", "Troll", "Heave a boulder that shakes the ground", "Ground pound that leaves the hero dizzy");
            T("EnemySmallDragon", "Dragon", "Spit a fireball", "Breathe a long stream of fire");
            T("EnemyCapraDemon", "Capra Demon", "Fast claw combo, the last hit slams down", "Long charge along the dotted line, stuns");
            T("EnemyGiantRat_Fireball", "Giant Rat", "Leaping bite", "Spit a fireball that rolls along the floor");
            T("EnemyRatman", "Ratman", "Claw swipe", "Slash, then throw a fast blade");
            T("EnemySatyrWarrior", "Satyr Archer", "Hold to aim, release a very fast arrow", "Invulnerable dash");
            T("EnemyWildShaman", "Wild Shaman", "Throw a small rolling fireball", "Throw a rat ball that hatches a tiny rat");
            T("EnemyMinotaur", "Minotaur", "Heavy axe swing", "Charge along the dotted line, stuns on hit");
            T("EnemyGiantSpider_Standard", "Giant Spider", "Quick bite", "Run and lay a web trail that roots the hero");
            T("EnemyGiantSpider_SpitWebs", "Web Spitter", "Quick bite", "Spit five web balls that root the hero");
            T("EnemyScorpion", "Scorpion", "Fast lunging pincer", "Spit goo that sticks the hero to the floor");
            T("EnemyDemonSnake", "Demon Snake", "Spit two bouncing fireballs", "One big bouncing fireball that stuns");
            T("EnemyDemonMouth", "Demon Mouth", "Slide forward biting, leaves poison goo", "Spit an egg that hatches a little mouth");
            T("EnemyDemonLord", "Demon Lord", "Fly up and crash down in a stunning shockwave", "Charge and grab the hero for big damage");
            T("EnemyDemonQueen", "Demon Queen", "Rapid fireballs", "Throw three bombs that land in a line");
            T("EnemyStingerTadpole_Standard", "Stinger Tadpole", "Fire a slow spear", "Dive under and dash, invulnerable");
            T("EnemyStingerTadpole_GroundSpears", "Spear Tadpole", "Fire a slow spear", "Dive dash that leaves spike holes behind");
            T("EnemyStingerTadpole_Giant", "Giant Tadpole", "Lash out with its tongue", "Dive dash that leaves a line of spikes");
            T("EnemyMindflayer_Teleport", "Mindflayer", "Tentacle lash", "Teleport, hurting what is at both ends");
            T("EnemyOctopusHead", "Octopus Head", "Heavy tentacle lash", "Send a tentacle line along the floor, stuns");
            T("EnemyBirdAbomination", "Bird Abomination", "Slam down, shockwaves stun and spread", "Charge and grab the hero");
            T("EnemyBlobfish", "Blobfish", "Chomp that stuns", "Slide forward leaving a trail of harmful slime");
            T("EnemyFishWizard", "Fish Wizard", "Cast a fireball", "Place a turret that shoots bubbles for a while");
            T("EnemyGiantBlobfish", "Giant Blobfish", "Huge chomp that stuns", "Invulnerable dodge roll");
            T("EnemyTentacleGlutton", "Tentacle Glutton", "Dash through the hero biting, leaves ink", "Big bite that stuns");
            T("EnemyTinyFish", "Tiny Fish", "Blow a bouncing bubble", "Invulnerable slide that leaves poison goo");
            T("EnemyFlyingEye_Dodge", "Flying Eye", "Cry a tear shot", "Invulnerable dash");
            T("EnemyEyeBaby", "Eye Baby", "Cry a tear shot", "Dash, leaving a rune that heals monsters");
            T("EnemyFlyingEye_Rapidfire", "Rapid-fire Eye", "Fire a long stream of small tears", "Invulnerable dash");
            T("EnemyFlyingEye_Red", "Red Eye", "Fire a laser beam, turn slowly to sweep it", "Invulnerable dash");
            T("EnemyFlyingEyeBomber", "Bomber Eye", "Shoot an eyeball that explodes", "Invulnerable dash");
            T("EnemyBeholder", "Beholder", "Hold a long eye beam that pushes the hero back", "Dash bite that stuns");
            T("EnemyEyelessBeast", "Eyeless Beast", "Your floating eye fires a burst of bolts", "Long invulnerable dodge");
            T("EnemyGargoyle", "Gargoyle", "Throw a stone bolt", "Turn to stone: invulnerable, blocks hits");
            T("EnemyForestSprite", "Forest Sprite", "Hop back, leaving a puddle that slows", "Suck the hero in toward you");
            T("EnemyGhostGirl", "Ghost Girl", "Fling your floating flame, steer with move", "Place a rune that heals monsters in it");
            T("EnemyGhostGirl_Dark", "Dark Ghost Girl", "Fling your dark flame, steer with move", "Fire a zap that chains forward three times");
            T("EnemyWitch", "Witch", "Bouncing magic zap", "Zap that turns the hero into a frog");
            T("EnemyFacelessShaman", "Faceless Shaman", "Bouncing orb that bursts on the floor", "Teleport, invulnerable");
            T("EnemyPrincess", "Princess", "Hold to aim, release a fast zap", "Place a rune that doubles monster damage");
            T("EnemyPriestess", "Priestess", "Cast a big bouncing rune that stuns", "Teleport, invulnerable");
            T("EnemyGhoul", "Ghoul", "Spit goo that leaves slowing puddles", "Raise a zombie from the ground");
            T("EnemyMushroom", "Mushroom", "Burrow (unhittable), leaving poison goo", "Launch a spore that grows a little mushroom");
            T("EnemySlimeMonk_Mushroom", "Mushroom Monk", "Spread a pool of poison slime", "Throw a heavy rune");
            T("EnemySlimeMonk_Ice", "Ice Monk", "Speed burst, leaving a trail of ice spikes", "Throw an ice rune");
            T("EnemySkeleton", "Skeleton", "Sword swipe", "Throw a bouncing bone");
            T("EnemySkeletonArcher_Shockwave", "Skeleton Archer", "Hold to aim, release a fast arrow", "Stomp a big shockwave that knocks back");
            T("EnemySkeletonArcher_Flame", "Flame Archer", "Hold to aim, release a fast arrow", "Fire two flaming arrows that stun");
            T("EnemySkeletonPirate", "Skeleton Pirate", "Lunging cutlass slash", "Raise a guard that blocks hits for a moment");
            T("EnemySkeletonMage", "Skeleton Mage", "Rapid magic bolts", "Spread a ring of harmful slime");
            T("EnemySkeletonPope", "Skeleton Pope", "Fire a homing orb", "Homing orb plus a burst of poison smoke");
            T("EnemySkeletonGiantShield", "Giant Shield Skeleton", "Heavy sword strike that stuns", "Block with the shield, then throw the sword");
            T("EnemyDarkServant", "Dark Servant", "Claw swipe", "Hop back and throw a dark bolt");
            T("EnemyDarkHaunt", "Dark Haunt", "Strafe and fire three bolts", "Fast invulnerable dash");
            T("EnemyDarkExecutioner_Boomerang", "Dark Executioner", "Huge axe strike that stuns", "Throw the axe, it comes back like a boomerang");
            T("EnemyDarkGuardian", "Dark Guardian", "Three-hit combo ending in a shockwave", "Giant hands burst up from the floor");

            // ================================================================ vanilla: statues, fodder, oddities
            T("EnemyIRSman", "Taxman", "Throw paperwork that stuns the hero", "Fire a long red-tape beam");
            T("EnemyGaben", "Gaben", "Rising uppercut that launches the hero", "Transform: stunning blast, then knife combo");
            T("EnemyMimic", "Mimic", "Scatter gold coins as bait", "Huge bite that stuns");
            T("EnemyStrongGnome", "Strong Gnome", "Throw a fast dagger", "Toss a bomb that explodes and stuns");
            T("EnemyMiniWilderbeast", "Mini Wildebeest", "Claw swipe", "Hop back and throw a bolt");
            T("EnemyFodderMushroom", "Little Mushroom", "Burrow (unhittable), leaving poison goo", None);
            T("EnemyTinyRatFodder", "Tiny Rat", "Leaping bite", None);
            T("EnemyFodderDemonMouth", "Little Mouth", "Slide forward biting, leaves poison goo", None);
            T("EnemyFodderZombie", "Zombie", "Slow claw swipe", None);
            T("EnemyFodderEyeBaby", "Little Eye", "Tear shot, or a dash that leaves a healing rune", None);
            T("EnemySlimeMedium", "Slime", "Spit three small slime blobs", None);
            T("EnemySlimeLarge", "Big Slime", "Spit three small slime blobs", None);
            T("EnemyTutorialSkeletonPope", "Skeleton Pope", "Fire a homing orb", None);
            T("EnemyHydraHeadA", "Fire Head", "Aim and breathe a stream of fire", None);
            T("EnemyHydraHeadB", "Frost Head", "Spit frost globs that linger on the floor", None);
            T("EnemyHydraHeadC", "Goo Head", "Spit goo that leaves burning puddles", None);
            T("EnemyCageDemon", "Cage Demon", "A short swing (unused monster, no damage)", None);
            T("EnemyHunchback", "Hunchback", "A short swing (unused monster, no damage)", None);
            T("EnemyTentacleBoss_Bomber", "Kourok Bomber", "Swell up and burst in a stunning blast", None);

            A("EnemyBlobfishChallenge", "EnemyBlobfish");
            A("EnemyGiantSpider_StandardChallenge", "EnemyGiantSpider_Standard");
            A("EnemyGiantSpider_SpitWebsChallenge", "EnemyGiantSpider_SpitWebs");
            A("EnemyTutorialBirdAbomination", "EnemyBirdAbomination");
            A("EnemyTutorialDarkHaunt", "EnemyDarkHaunt");
            A("EnemyTutorialGreenSlime", "EnemySlimeMedium");
            A("EnemyTutorialGreenSlimeFinal", "EnemySlimeMedium");
            A("EnemyTutorialGreenSlimeRound2", "EnemySlimeMedium");
            foreach (var c in new[] { "1Blue", "2Red", "3Green", "4Yellow" })
            {
                A("EnemySlime" + c + "Medium", "EnemySlimeMedium");
                A("EnemySlime" + c + "Large", "EnemySlimeLarge");
            }

            // ================================================================ vanilla boss parts (possessed as a ghost)
            const string aim = "none, aim with movement";
            T("BossHydra/TrapA", "Ghidraak - Fire Head", "Aim and breathe a long stream of fire", aim);
            T("BossHydra/TrapB", "Ghidraak - Frost Head", "Spit frost globs that linger on the floor", aim);
            T("BossHydra/TrapC", "Ghidraak - Goo Head", "Spit goo that leaves burning puddles", aim);
            T("BossTentacleBlob/TentacleL", "Kourok - Left Tentacle", "Lob a bubble that traps the hero", aim);
            T("BossTentacleBlob/TentacleR", "Kourok - Right Tentacle", "Throw slime bombs that leave harmful goo", aim);
            T("BossTentacleBlob/Eye", "Kourok - Eye", "Fire a sweeping eye beam", aim);
            T("BossBurriedStatue_P1", "Tezekcal - Head", "Steer the crosshair, drop a heavy bomb", "none, wait for the head to recharge");
            T("BossBurriedStatue_P2", "Tezekcal - Left Arm", "Stab the floor, stuns on hit", aim);
            T("BossBurriedStatue_P4", "Tezekcal - Right Arm", "Slap the floor, stuns on hit", aim);
            T("BossBurriedStatue_P5", "Tezekcal - Left Leg", "Stomp the floor, stuns on hit", aim);
            T("BossBurriedStatue_P8", "Tezekcal - Right Leg", "Stomp the floor, stuns on hit", aim);
            T("BossBurriedStatue_P3", "Tezekcal - High Hand", "Fire a beam of magic from the hand", aim);
            T("BossBurriedStatue_P7", "Tezekcal - Low Hand", "Fire a beam of magic from the hand", aim);
            T("BossBurriedStatue_P6", "Tezekcal - Orb Spout", "Roll an orb that leaves a barrier behind", aim);
            T("BossBurriedStatue_P9", "Tezekcal - Spitter", "Shoot short-range bolts", aim);
            for (int i = 1; i <= 5; i++)
                T("BossBurriedStatue_SummonedArm" + i, "Tezekcal - Summoned Arm", "Fire one bolt, then you are let go", None);

            // the gods' tip files (tools/merge_tips.py) override the rows above
            AddGenerated();
        }

        /// <summary>The tip for a prefab name, following aliases. False if the table has none.</summary>
        public static bool TryGet(string key, out MonsterTip tip)
        {
            string a;
            if (key != null && Alias.TryGetValue(key, out a)) key = a;
            if (key != null && Tips.TryGetValue(key, out tip)) return true;
            tip = default(MonsterTip);
            return false;
        }
    }
}
