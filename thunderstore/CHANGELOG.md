# Changelog

## Unreleased

- Pick your ghost's blob. The ghost page has a second row under the forms: the blob your ghost spawns with Back.
  Every form starts on its own blob, so nothing changes until you pick. Move down from the forms to reach the row.
- The Mote, Spitter and Gel open for every form through a challenge each: spawn 100 Motes as the Gleaner, hit the
  hero with Spitter goo 60 times, fuse 3 Titans as the Binder. Locked blobs show as a dark outline with their
  challenge and progress, and the vault has a page for each.
- Any ghost that spawns Gels fuses them with the ghost button, and any ghost that spawns Motes gets them in pairs.
- New blob, the King Blob, for the silver and gold ghosts only. It slams out a ring of goo and rains globs that land
  where their shadows grow. It has a little more health than a Titan, leaves no Gel behind, and costs three bodies
  of ectoplasm.
- The Sexton's graves and the Miser's hoard raise the picked blob too.
- Test mode: Become > Ghost blob sets the blob.

## 1.0.2

- Tier 2 and tier 3 monsters of all nine gods are stronger, in line with the game's own tier 3 monsters and
  finals: the finals have more health, hits land harder and specials charge sooner. The Glue Mortar also lobs faster.
- Hits that monsters deal through their quirks now count god perks and damage runes, like their normal attacks.
- When a minion, a gold thrall or another monster with no player inside killed the hero, nobody took the crown and
  the dead hero's player never became a ghost, so the run could not go on. The player who made that monster now
  becomes the hero, as with the game's own monsters.

## 1.0.1

- Online Crawl: a player who lost the connection and joins again right away gets a working screen. Back in the
  game, their character plays as a bot until they press Start and pick Drop In.
- Fixed a white box on the evolve screen with a translation mod installed. The cost number now uses its label's font.
- The evolve screen shows one violet gem per panel, not one on every monster.
- Mod monsters on the evolve screen stay inside their panel.
- Mod content shows one violet gem, never two: the vault, the god and origin pickers and the shop each mark an entry once. The gems can be turned off with ModGem in CrawlFurther.UI.cfg.
- Tips, pause pages and vault pages keep working when a translation mod swaps the game's fonts or labels.
- The Carrion Roc can no longer leave the ally it carried unkillable.
- A monster that lurks or coils no longer comes back later without collision.
- The list of monsters you've seen tips for is kept if it fails to load once.
- The slot machine's health and ectoplasm results no longer show numbers.

## 1.0.0

### Gods
- All nine gods are rebuilt. Each of the 189 monsters has new art and a move or quirk of its own with a tell you can see, and its tips, vault line and its god's pause page are rewritten to match.
- Three monsters are replaced: the Ouroboros takes the Dice Rattler's place (Jinx), The Sower the Amber Hornet's (Sylvene) and the Gulper Eel the Storm Eel's (Bel'Mora).
- Vhorrul: monsters swim in wax, soak it up and pour it as fuses. The Wick Hag has a poppet and the Tallow Colossus sheds wax layers.
- Ossivar: the Church Grim falls into bones and rises again unless the hero stands on the pile. The Carrion Roc carries an ally across the room and drops it.
- Sylvene: each monster tends, shakes, slings, hides or sows the orchard's pods.
- Umbrael: each monster bends the shadow echo its own way. The Hollow King throws his crown, and a shadow king stands there for 5 s.
- Bel'Mora: the Drowned Bell throws his bell, the Gulper Eel swallows, and the Siren's song drags the brine pools.
- Jinx: the Grand Jester swaps a fast Comedy mask for a tough Tragedy mask, and the Oracle's ghost acts out her next move a second early.
- Zhekra: the Brood Mother raises a larva into a grub, the Hunting Wasp carries a Marked hero into the swarm, and a Botfly egg hatches a larva for every hit the hero takes.
- Kaurn: red-hot rods, a wired hero, a wyvern that rides the arcs, and rods that take the bolt meant for you.
- Ysveld: a widow wraps you, a bride turns black, a geode splits.
- Each of the nine gods has its own gold idol portrait.

### Art
- New art for the 11 origin portraits and the gear the origins wear, all 25 weapons (in the hero's hands, in the shop bubble, and their swings and shots), the item and spell icons, all 32 room objects and their effects, the six blobs, the six ghost fodder creatures and the ghost form portraits, the secret statues and the gold secret monsters (now with real death animations), the silver and gold idols, the slot padlock, the banner for a newly opened slot and the evolve menu's header.
- Everything is drawn in Crawl's own muted palette: three tones per material, light from the top left, and no hard black outline. Item colours were measured against the game's own art.
- Artifacts stand 22 px tall in the shop bubble (was 16), and the small HUD icons are drawn by hand.
- Silver ascended finals and the statue carvings are redrawn from the new art.

### Test mode
- A test panel on F2 for trying things without a full run. Become any monster, ghost form or the hero, spawn hostile monsters and room objects, give the hero items and weapons, pick the run's gods, skip floors, go to the boss, slow the game down and show hitboxes. It also turns on Crawl's own hidden debug menu (Tab + `).
- Off by default. Set TestMode = true under [Testing] in BepInEx/config/CrawlMod.Debug.cfg. While it is on, nothing counts toward the vault, challenges or secrets, and it turns itself off in an Online Crawl match.

### Framework
- The mod is now two DLLs: CrawlFurther.Core.dll, a modding library with no content of its own, and CrawlFurther.dll, the content built on it. Settings and saves carry over.
- Other mods can use Core to add their own gods and monsters, shop items and weapons, room objects, vault pages and secrets, and pages on the test panel. The source, developer docs and an example mod (one god, three monsters, one spell) are on GitHub under the MIT license.
- The god select shows the gods as a grid that pages once it is full, so more gods fit.

### Compatibility
- Works alongside CrawlAPI: its Custom entry joins the god grid and opens CrawlAPI's own menu.
- Works alongside boss mods such as CrawlCustomBosses: a boss another mod picked is never replaced, room objects never spawn in a boss arena, and the silver upgrade waits until the boss fight is over.
- Online Crawl still works as in 0.10.0. Every player needs the same Crawl: Further version.

### Fixes and playtest changes
- The Leviathan and Pandemonium are switched off for now: they never spawn, and their tips and pause page are hidden. The setting is Enabled under [Bosses] in com.firefightermate.crawlfurther.cfg.
- Binder: only Gels fuse. 2 Gels make a Brute, 3 make a Titan, and a Brute or Titan never fuses again. The King Blob is gone. Back no longer fuses.
- Every ghost form has its own tip, and a Fusebelly that Attack will light shows a spark on its fuse.
- Silver and gold idols: each time you pick a monster for a slot, the cursor starts on the top-left monster. The ready screen shows the idol's perk god.
- The Golden Duck has its own 1 in 500 roll per room. Before, it turned up far more often than the 1 in 150 it promised.
- The hero still slides on Ysveld ice but no longer runs faster on it.
- Potion effects with a timer count down only during fights, with a countdown next to that player's HUD panel.
- The first gold secret monster steals 1 to 4 gold with its basic attack and aims it in any direction. Playing dead, it takes a quarter damage but drops gold when hit.
- Monsters built on the gnome (Rime Shardling, Barnacle Crab, Thornbiter, Rivet Imp) no longer make the hero drop gold.
- A hero who picks up a vanilla weapon after a mod weapon no longer turns invisible.
- Vault text is measured against the game's font, so none of it is cut off or runs under BACK.
- At most two Loose Jacks are out at once.
- A grub that grew in a past life keeps its full health when its body is used again.
- The Widow Matron's wrap wears off on its own.

## 0.10.0
- The vault has a SECRETS category with a page for each of the 25 secrets: 3 silver uniques, 7 gold secret monsters, 5 secret statues, 8 object secrets and 2 secret items. Until you find one it shows a silhouette, a little riddle and how rare it is. Once found, its picture, name and story. New finds are announced on the next menu and get the vault's red dot.
- 32 room objects. Ghost traps: Chain Winch, Steam Vent, Tar Spout, Pendulum Blade, Rune Plate, Toll Bell and Scatter Idol. On the floor: Iron Snare and Warp Stones. For the hero: Mending Spring, Weapon Rack, Cursed Altar, Ward Shrine (30 gold, half damage until 15 s into your next fight) and Strongbox, plus the Spirit Urn for ghosts. Fun: Jukebox, Disco Ball, Pinata, Confetti Cannon, Slot Machine, Fortune Teller, Bounce Shroom, Firework Crate and Wishing Well. Secrets: Lever Trio, Hidden Hatch, Cracked Wall, Mysterious Keyhole, Golden Reliquary, Sculptor's Altar, Watching Portrait and Golden Duck. CrawlFurther.Objects.cfg sets how often they appear.
- 25 new items: 7 stat potions (Troll Marrow, Wyrm Blood, Hare's Dew, Berserker's Grog, Stoneskin Draught, Quicksilver, Chaos Brew), 16 trinkets (Party Hat, Bard's Lute, Pet Ferret, Bubble Pipe, Rubber Duck, Firefly Jar, Dancing Shoes, Whetstone, Phoenix Feather, Siphon Gem, Glutton's Fork, Tally Stick, Gambler's Coin, Patchwork Bandage, Wanted Poster, Iron Boots) and 2 secret items that are never sold (Skeleton Key, Gilded Heart). The shops now carry 67 mod items.
- 5 secret statue monsters on gold-seamed plinths: Grotesque, Sixfold Idol, Gambit and Caryatid (about 1 statue room in 12 between them) and the legendary Lachrymosa (about 1 in 200), whose Lights Out darkens the room for 2.5 s.
- God perks reworked so they matter in every fight. Vhorrul: the dead burn as pyres, then cool into tallow slicks. Ossivar: bone piles crawl to the nearest Ossivar monster. Sylvene: pods ripen in 2.5 s and burst in a wider cloud. Bel'Mora: Rising Tide leaves brine pools every 14 s. Umbrael: a bite's echo shows shadow jaws. Jinx: the Wild Card shows over the monster's head. Ysveld: a blizzard lays ice paths every 12 s. Kaurn: iron rods stand 9 s.
- Marrow Hound: a bone pile heals half its health, but only while it is below 3/4 health.
- Every mod monster's melee turns toward where it aims, so it can hit up and down. The Jack-in-the-Box has its own up and down punches.
- Size fixes: floating numbers, the Wishing Well and boss status icons.
- Every tier-3 monster, mod and vanilla, has a moonlit silver version of its art, used by the silver ghost's Ascension. Ascended bodies no longer grow bigger.
- The silver upgrade follows vanilla trees all 4 levels deep.
- Monster tips show for every player in multiplayer, each above that player's own HUD panel, smaller with 3 or 4 players. Options: Tips ALL / P1 ONLY / OFF.
- Monster tips show every time you take a monster, including one you took earlier in the same room. Options: Tooltips ALWAYS / FIRST TIME (once per save) / OFF.
- Works alongside the Online Crawl mod.
- Fixes: item buffs no longer stay on after the hero dies; the Phoenix Feather and Patchwork Bandage are not used up by hits your weapon guard blocks; objects no longer take the attack button from the hero in a fight; the Caryatid's columns can't trap the hero. A Ward Shrine blessing ends if the one who prayed stops being the hero. Item text says "percent", which the game's font can show.

## 0.9.1
- Names no longer carry a mod tag. Mod content is marked only with the violet pip or gem, now also on vault cells and the vault's big picture.
- New Crawl: Further soundtrack: "Further Down", "Tallow Hymn", "Gilded Rot" and "Lingbourn", instrumental tracks made for the mod, rotate in with the game's music (about 1 in 3 new gameplay tracks), following the game's music volume and fades. CrawlFurther.UI.cfg: CustomMusic, CustomMusicChance, CustomMusicOnTitle, CustomMusicVolume.
- Silver ghost reworked into Ascension: your fallen monsters drop silver orbs, and 8 of them upgrade your next body. Orbs drop more often than before (1 to 4 a death, about 2.3 on average).
- Gold ghost reworked into Thralls: press the ghost button as a monster to jump out, and the body fights on in gold for you.
- 3 silver unique tier-3 monsters that only the silver ghost's tier-3 upgrade gives: Moonwarden and Comet Stag (1 in 5 upgrades each) and the legendary Astrarch (1 in 25).
- A secret gold monster line, 7 monsters in all. Where it hides is a riddle in the Secrets vault.
- The gold idol's evolve screen shows all 4 monsters.

## 0.9.0 (Crawl: Further)
- The mod is now called Crawl: Further. The plugin folder, DLL and config names are unchanged, so updates keep settings and saves.
- A drawn "Further" wordmark at the bottom right of the CRAWL logo on the title screen and in the credits. It burns in, glints, sheds embers and glitches along with the logo.
- Main menu: flame markers beside the selected item, drifting embers and dust behind the logo, and the version bottom right.
- Vault: weapons, items and objects are picture grids like the monsters, with a picture for every entry. Weapons show the hero in that weapon's stance, undiscovered entries a sealed "?". The name shows above the description. Mouse wheel and Page Up / Page Down scroll the grids.
- Vault: new FURTHER category with a page for every mod god, hero origin and ghost form.
- Hero origins: each has its own colour set per player slot (P1 blue, P2 red, P3 green, P4 amber), and most origins cost a little more.
- Silver and gold slots at the end of the origin list: build your own hero (any look, any weapon, and on gold a spell too), each pick with a stat cost.
- Six new ghost forms (ten in all): Banshee, Sexton, Kindler, Mason, Hexer and Miser, each with its own creatures and effects.
- Silver and gold ghosts with your own look (shape, colour, eyes, trail).
- A ghost button (Binder fuse) that you can rebind in the controls settings; mouse uses middle click.
- Silver and gold idols at the end of the god list: pick any god's perk, then 3 (silver) or 4 (gold) starters from any god. Only the chosen perk applies.
- Silver and gold slots open through challenges that take some play time (evolve 60 monsters, reach 20 different finals, kill 400 monsters as the hero, win 5 games, gather 1000 ectoplasm, kill the hero 40 times as a monster). A locked slot shows your progress.
- Origin pips show what an origin gives: violet for a weapon, blue for a spell, rose for both.
- CrawlFurther.UI.cfg turns the wordmark, menu touches or vault grids off.

## 0.8.0
- Evolutions are never shared: every god's tree is 3 starters, 6 tier-2 and 12 finals (21 monsters per god, 189 in all), and each monster has exactly one parent.
- Art pass: every mod monster, effect, item, weapon, boss and ghost form has its own drawn art. Evolutions are redrawn to show both parents, each god has its own hit splats, weapons are drawn in the hero's hands, and hero origins carry their own gear.
- Pause > Tips has new pages: the monster you are now, each mod god, status effects, icons, ghost forms and bosses. Left and Right skip topics.
- Dice show their roll as a number, and a Lucky Die dodge shows DODGE.
- New icons over the head and at the feet for plates, sparks, frost pips, healing, speed, damage and ice.
- Fixed the monster pictures in the evolve menu.
- Monster tips now explain each passive in plain words, on up to two lines.
- Zhekra monsters swarm next to any other monster, and Kaurn arcs reach any monster near a Kaurn monster or rod.

## 0.7.2
- Every god's tree is now 3 starters, 4 tier-2 and 4 finals, and each monster offers two different evolutions. 38 new monsters.
- Mod finals appear as monster statues, with their own carved statue art.
- Monster tips: when you become any monster, a 7-second note explains its attack and special. Toggle in Options.
- 15 new weapons (25 in all), and every mod weapon is recoloured in the hero's hands.
- Every mod monster, item and weapon has an entry in the library.
- Binder ghost form: fuse blobs with X (controller) or C (keyboard), and the fuse range is now about 90 px.
- Changed the mod tag after names, because the game hid the old one.

## 0.7.1
- Shop pedestals show small vanilla-style sprites for every mod item and weapon.
- Fixed the Rotting Apple, Saint's Wick, Lightning Rod, Votive Candle, Marrow Flask, Hollow Crown, Soul Lantern, Glass Mask and Chain Spark.

## 0.7.0
- Three new gods (Zhekra, Kaurn, Ysveld), ten weapons, four hero origins, in-game hero colours per origin.
- Monsters resized to vanilla scale, with hurtboxes and attack hitboxes checked against the art.
