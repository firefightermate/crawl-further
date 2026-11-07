namespace CrawlFurther.Content.Library
{
    using CrawlFurther.UI;

    /// <summary>
    /// Hand-written vault lines for the monsters, in vault order: name and one line in the vanilla prop tone. A monster
    /// with no line here takes the "vault" field of its tip (data/tips/tips_&lt;god&gt;.json) and is listed after its god's
    /// block. tools/merge_tips.py reads the M("Id", ...) rows to check every monster has a line.
    /// </summary>
    public static class VaultLines
    {
        public static void Register()
        {
            // Vhorrul, the Tallow Saint
            M("Wickling", "Wickling", "A wick-tailed rat. Its dash snuffs its tail, and fire lights it white-hot");
            M("TallowGrub", "Tallow Grub", "Melts into a puddle of its own wax and wells up under its prey");
            M("AshMoth", "Ash Moth", "Puffs dazing ash. Near a flame it flies faster and its ash smoulders");
            M("WaxenKnight", "Waxen Knight", "Walks through fire to wear it, then cracks its burning wax off in a ring");
            M("Chandler", "Chandler", "Pours a line of wax and waits. One spark sends fire racing down it");
            M("MothMatron", "Moth Matron", "Her ember moths drift and smoulder, until their prey catches fire");
            M("Candelabra", "Candelabra", "Fans out candle flames that split in two wherever they cross wax");
            M("TallowColossus", "Tallow Colossus", "Soaks up wax to grow, then topples flat onto its prey");
            M("LanternWraith", "Lantern Wraith", "Takes a soul's flame into its lantern. Fire gives it back");
            M("VhChandelier", "Grand Chandelier", "Bobs on its chain out of reach, and drips a ring of wax before lighting it");
            M("VhAshSeraph", "Ashen Seraph", "Beats every fire out with six wings, and the ash comes looking for you");
            // Ossivar, the Marrow King
            M("Rattlebones", "Rattlebones", "Throws its own skull, and while it lies there only the skull can be hurt");
            M("MarrowHound", "Marrow Hound", "Smells blood and runs faster at a bleeding hero. A pile of bones heals it");
            M("CairnCrow", "Cairn Crow", "Pecks splinters out of open wounds, and caws loose bones toward its kin");
            M("OssGravetusk", "Gravetusk", "Its charge bends after the scent of blood and bursts the bones it tramples");
            M("BoneLancer", "Bone Lancer", "Throws spears that stand in the floor and snag whoever runs into them");
            M("OssuaryPriest", "Ossuary Priest", "Bones crawl to its feet from across the room, and stand up again as rats");
            M("OssCarrionVulture", "Carrion Vulture", "Circles a wounded hero, and plummets from high above onto his spot");
            M("OssMarrowWyrm", "Marrow Wyrm", "Fills nearby bones with marrow: whatever eats them grows two plates");
            M("OssCharnelRider", "Charnel Rider", "Jousts until it hits a wall. Unhorsed, it fights on with a thrown lance");
            M("Ossuary", "The Ossuary", "Cages its prey in giant ribs and stands guard behind three bone plates");
            M("OssCarrionSaint", "Carrion Saint", "Crows perch on its arms. It sends them one by one, or all at once as a wall");
            M("BoneRat", "Bone Rat", "Raised from a pile of bones. It bites, and little else");
            // Sylvene, the Rot Orchard
            M("Sporeling", "Sporeling", "Puffs spores, and tends the seeds round it so they ripen faster");
            M("Thornbiter", "Thornbiter", "Lashes with a vine. Its racing roots leave a seed wherever they stop");
            M("Rotfly", "Rotfly", "Dive-bombs in a puff of poison. Its spit sprouts a seed where it misses");
            M("BrambleKnight", "Bramble Knight", "Its thorn sword leaves a knot of thorns at the end of every sweep");
            M("SylSporeHusk", "Spore Husk", "One blow of its fungal club shakes every ripe pod nearby loose at once");
            M("BloomWitch", "Bloom Witch", "Fires piercing pollen, and grafts ripe pods onto the heads of her kin");
            M("SylGallWasp", "Gall Wasp", "Its needles plant striped seeds that ripen faster than any other");
            M("RotMother", "The Rot Mother", "Roots erupt beneath the hero. Every pod that bursts on him feeds her");
            M("SylBriarBehemoth", "Briar Behemoth", "Charges with a thorn bush in tow. The bush swings in when it turns");
            M("SylPollenMonarch", "Pollen Monarch", "Its pollen dusts the hero, and dusted, he sets off pods from afar");
            M("SylCarrionLily", "Carrion Lily", "Roots itself to heal and strike from far off. It walks slowly uprooted");
            M("Sprout", "Sprout", "Bursts up through the floor at the Rot Mother's call and puffs spores");
            // Umbrael, the Hollow Mirror
            M("ShadeImp", "Shade Imp", "Rakes twice and steps through smoke. In the dark its echoes come faster");
            M("Glimmer", "Glimmer", "Its shards ricochet, and strike harder once they have. It splits into decoys");
            M("GlimmerDecoy", "Glimmer Decoy", "A perfect copy of a Glimmer. It flicks weak shards and shatters when struck");
            M("GloomLurker", "Gloom Lurker", "Bites harder unseen, and breathes a darkness that hides its kin");
            M("Twinned", "The Twinned", "Two bodies, two cuts. After it swaps with the hero, its cut echoes in both places");
            M("Nailshade", "Nailshade", "Flings glass nails, tighter each time they hit. When its pin holds, it is already there");
            M("MirrorWitch", "Mirror Witch", "Her bolts bank off the walls. Her standing mirror turns them on you and your shots back");
            M("Gloamcoil", "Gloamcoil", "A rearing bite. It leaves pools of darkness, and the dark it lies in spreads");
            M("EclipseWyrm", "Eclipse Wyrm", "Two heads, two bites. One swallows the other and it burns as a black eclipse");
            M("HollowKing", "The Hollow King", "He throws his crown down, and a shadow king takes every echo of his cleaves");
            M("GlassSeraph", "Glass Seraph", "Its feathers ricochet and split. Echoes near it bend toward the hero");
            M("Unblinking", "The Unblinking", "Its gaze burns. When it shuts its eye the dark falls, and when it opens, stand still");
            // Bel'Mora, the Drowned Bell
            M("BellUrchin", "Bell Urchin", "Rolls into the hero as a spiked ball. In brine its tube feet grip and nothing moves it");
            M("Lurefish", "Lurefish", "Its lure brightens while it waits, and a bright lure tugs the hero in from far off");
            M("BarnacleCrab", "Barnacle Crab", "Pinches hard and grows a barnacle plate. It scuttles sideways faster than you walk");
            M("BellDiver", "Bell Diver", "Its hook reels you in. When it misses, the Diver hauls itself along the chain");
            M("SaltSiren", "Salt Siren", "Her song pulls the hero close, and drags the brine pools to his feet");
            M("BellHermit", "Bell Hermit", "It carries the sea in its bell, and pours it out when the bell comes down");
            M("BrineLamprey", "Brine Lamprey", "It lunges along the floor and latches on. Dodge or strike to shake it off");
            M("DrownedBell", "The Drowned Bell", "He throws his bell at you. Until he lifts it back on, his back is bare");
            M("TideMatriarch", "Tide Matriarch", "She plants her trident and the currents run from the brine to her feet");
            M("DrownedCaptain", "Drowned Captain", "He swings across the room on his grapple. Kicked into brine, you are held under");
            M("AbyssKraken", "Abyss Kraken", "Its arms rise from the brine and stay to swat. With three up, its head is open");
            // Jinx, the Grinning Jester
            M("JackInTheBox", "Jack-in-the-Box", "Winds itself up while it stands still, then punches harder. It pops out by the hero");
            M("CardSharp", "Card Sharp", "Throws cursed cards, and every third deal a gold Ace. It swaps places with its allies");
            M("DiceImp", "Dice Imp", "Rolls dice that hit for what they show. A six makes its next toss two dice");
            M("Ringmaster", "Ringmaster", "A long whip, and a flaming hoop. A hoop that misses comes back for an encore");
            M("Marionette", "Marionette", "Its strings pull the hero in. Then it mirrors the hero's every step");
            M("JinxFortuneTeller", "Fortune Teller", "Her crystal ball shows the hero's fate before the mark seals: knives, bombs or a blessing");
            M("JinxSnakeEyes", "Snake-Eyes", "A venomous bite and a pair of dice. Doubles roll again, and a craps roll dazes her");
            M("GrandJester", "The Grand Jester", "Two masks. Smiling, he juggles from afar. Weeping, he smashes up close");
            M("JinxChimera", "Big-Top Chimera", "Mauls and leaps through a ring of fire. Badly hurt, its mane burns and its paws scorch");
            M("JinxPuppeteer", "Puppeteer", "Hauls its allies onto the stage round the hero and guards them on its strings");
            M("JinxBandit", "One-Armed Bandit", "Spins its reels for knives, bombs, coins or health. Hit it mid-spin and it jams");
            M("JackMinion", "Loose Jack", "A Jack-in-the-Box let out by the wheel. It punches whatever is near");
            // Zhekra, the Brood Queen
            M("ZhkGrub", "Acid Grub", "A fat grub that spits acid, and grows fatter on every bite of a hero coated in it");
            M("ZhkDrone", "Brood Drone", "Fires stinger darts and dives through the hero. Dying, it spends its life on one sting");
            M("ZhkBeetle", "Resin Beetle", "Spits sticky resin, then shoves the hero into it with its shovel jaws");
            M("ZhkSpitter", "Acid Spitter", "Its sac of acid fills as it waits. Full, it floods the floor, or bursts if struck");
            M("ZhkSoldier", "Hive Soldier", "Stands guard with its scythes raised and cuts down whatever steps too close");
            M("ZhkHornet", "Hive Hornet", "Marks the hero with its scent. The whole hive follows the trail he leaves");
            M("ZhkNasute", "Nasute", "A termite with a glue nozzle for a head. Strike its kin and it squirts you");
            M("ZhkMother", "Brood Mother", "The queen. Her larvae never wither while she lives, and she raises them into grubs");
            M("ZhkColossus", "Chitin Colossus", "All armour in front, soft behind. It bulldozes the hero ahead of its plate");
            M("ZhkHive", "Amber Hive", "A walking hive. Every crack in its comb spills amber it mends itself in");
            M("ZhkMantis", "Acid Mantis", "Its acid blades strike anything in reach, even a shot in the air");
            M("ZhkLarva", "Hive Larva", "Hatched from the dead. It withers in seconds, unless the queen is near");
            // Kaurn, the Storm Forge
            M("KrnRivetImp", "Rivet Imp", "Bonks with a hammer and bats hot rivets that stick in the floor");
            M("KrnSparkBeetle", "Spark Beetle", "Zaps with its antennae, then rolls through the hero as ball lightning");
            M("KrnCoilWisp", "Coil Wisp", "Spits motes of ball lightning and discharges a static ring");
            M("KrnAnvilSmith", "Anvil Smith", "Its hammer splits the floor. It takes the lightning into its iron");
            M("KrnStormcaller", "Stormcaller", "Hurls ball lightning, and calls a bolt down on you unless a rod takes it");
            M("KrnLodeHound", "Lodestone Hound", "A leaping bite, and a howl that pulls or pushes, red collar or blue");
            M("KrnLeydenGolem", "Leyden Golem", "A jar brimming with lightning. It throws jolts and charges up its kin");
            M("KrnForgeColossus", "Forge Colossus", "Quakes the floor with both fists until its furnace boils over in steam");
            M("KrnStormHerald", "Storm Herald", "A lance of lightning, and a storm all round it. The calm is at its side");
            M("KrnThunderBull", "Thunder Bull", "The further it charges the harder it hits. Walls stop it");
            M("KrnStormOrrery", "Storm Orrery", "Flings ringed orbs. Its planets line up on you, then fire");
            // Ysveld, the Frost Widow
            M("YsvRimeling", "Rimeling", "A frost-fanged bite and a slowing glob of silk-frost");
            M("YsvHoarmoth", "Hoarmoth", "Flings a fan of rime, and beats its wings to knock the hero back");
            M("YsvShardling", "Rime Shardling", "Head-butts with its crystal crown and calls an icicle down on the hero");
            M("YsvWeaver", "Silk Weaver", "Fires a silk line that leashes the hero to it");
            M("YsvSilkmoth", "Silkmoth", "Flings silk-wrapped ice needles, and dives through the hero leaving ice");
            M("YsvVeilWitch", "Veil Witch", "Grows a shattering crystal by you for every frost pip you carry");
            M("YsvRimeKnight", "Rime Knight", "A two-handed crystal cleave. It freezes plates of ice armour");
            M("YsvMatron", "Widow Matron", "Lays egg sacs of Broodlings. Pinned near her, you are wrapped in silk");
            M("YsvBride", "The Winter Bride", "Breathes frost and sweeps her train. A fallen ally turns her veil black");
            M("YsvEmpress", "The Pale Empress", "A fan of aurora motes, and a blizzard that hunts the hero");
            M("YsvColossus", "Rime Colossus", "Paves a road of ice to you, then throws itself down it on its belly");
            M("YsvBroodling", "Broodling", "Hatched by the Widow Matron or shaken off a Tarantula. A small frost bite, soon gone");
            // Ghost forms: the blobs a ghost raises
            M("BlobMote", "Mote Blob", "A Gleaner's little blob. Quick, fragile, and it nips");
            M("BlobSpitter", "Spitter Blob", "A Poltergeist's blob. It spits goo that slides along the floor");
            M("BlobGel", "Gel Blob", "A Binder's blob. Two fuse into a Brute, three into a Titan");
            M("BlobBrute", "Brute Blob", "Two Gels fused into one. It hops in and lands with a slam");
            M("BlobTitan", "Titan Blob", "Three Gels fused into one. It slams, engulfs, and leaves a Gel when it dies");
        }

        static void M(string id, string name, string line) { Vault.AddMonsterLine(id, name, line); }
    }
}
