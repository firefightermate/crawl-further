# Crawl: Further

A large content mod for Crawl (formerly "Crawl Mod"). It adds nine new gods with 189 monsters between them, 15 secret monsters, 25 weapons, 67 shop items (22 spells, 38 artifacts and 7 potions) plus 2 secret items, 32 room objects, hero origins and ghost forms. All of it has its own drawn art in Crawl's palette, down to the weapons in the hero's hands. Vanilla content is untouched. Everything new is marked in purple: a violet pip in the menus or a small violet gem on its picture.

## New in 1.0.0

- All nine gods are rebuilt. Every one of the 189 monsters has new art and a move or quirk of its own, with a tell you can see.
- New art for the hero origins, weapons, items, room objects, blobs, ghosts, secret monsters and menus.
- A test panel (F2) for trying any monster, item or object without playing a whole run.
- Crawl Further Core, the modding library under the mod, is open for other mods to build on.
- Works alongside Online Crawl, CrawlAPI and boss mods such as CrawlCustomBosses.

The full list is in the changelog.

## The nine gods

Each god has 21 monsters: three starters, six at tier 2 and twelve finals. Every starter and tier-2 monster offers two evolutions of its own, nothing shared, so each tree has 12 paths. Each god has a perk that shows up in every fight:

- **Vhorrul**, the Tallow Saint: wax and fire. The dead burn as pyres that cool into tallow slicks, and his monsters swim in the wax, soak it up and pour it as fuses.
- **Ossivar**, the Marrow King: bones. The dead leave bone piles that crawl to the nearest Ossivar monster and become plates that block a hit.
- **Sylvene**, the Rot Orchard: rot and spores. The dead drop seeds that ripen in 2.5 s into poison pods, and each of her monsters works the pods in its own way.
- **Umbrael**, the Hollow Mirror: shadows. Every basic attack repeats 0.6 s later as a shadow echo for half damage, and each monster bends that echo its own way.
- **Bel'Mora**, the Drowned Bell: the sea. Hooks, currents and songs drag you in, and every 14 s the tide leaves brine pools that slow you and heal her monsters.
- **Jinx**, the Grinning Jester: luck. Each special flips a Wild Card over the monster's head, and dice hit for their roll.
- **Zhekra**, the Brood Queen: insects. Larvae and acid, resin that roots, and monsters that swarm when packed together.
- **Kaurn**, the Storm Forge: lightning and iron. Arcs link Kaurn monsters and iron rods to anything near them, and crossing one hurts.
- **Ysveld**, the Frost Widow: ice and silk. Every 12 s a blizzard lays ice paths her monsters skate on, and three frost hits pin you.

Every mod monster's melee turns toward where it aims, so it hits up and down as well as sideways. Mod finals can also turn up as stone statues between fights, and a ghost can step into one.

## What else is in it

**Secrets.** 15 secret monsters: three silver-only finals from the silver ghost's upgrade, a seven-monster gold line hidden somewhere gilded, and five statues on gold-seamed plinths (the legendary Lachrymosa is about 1 in 200). The vault's SECRETS page has all 25 secrets. One you haven't found shows a silhouette, a riddle and how rare it is.

**Room objects.** 32 of them: ghost traps (Chain Winch, Steam Vent, Pendulum Blade and more), a snare and warp stones, shrines and a strongbox for the hero, a Jukebox that changes the music, a Disco Ball, a Slot Machine, a Wishing Well, a Pinata, and a few that hide secrets.

**Weapons.** Each of the 25 has a mechanic no vanilla weapon has. Gravehook drags monsters to you, Moonglaive comes back like a boomerang, Snake-Eyes rolls a die for its damage, and Arcbolt chains lightning. Reaper gets stronger with every kill until you're hit, and Midas Sling hits harder the more gold you carry.

**Shop items.** 22 spells, 38 artifacts and 7 stat potions, some with a short catch. The trinkets run from a Party Hat and a Pet Ferret to a Phoenix Feather that saves you from one killing hit. Two more items are never sold.

**Hero origins.** After picking a god, pick one of 10 origins (or the vanilla hero). Each changes stats or gear and recolours the hero, with its own colour set for each player slot.

**Ghost forms.** Ten ways to play between bodies: Wisp, Gleaner, Binder, Poltergeist, Banshee, Sexton, Kindler, Mason, Hexer and Miser, each with its own creatures.

**Silver and gold slots.** The last two entries of the god, origin and ghost lists let you build your own: an idol with any god's perk and starters from any god, a hero with any look and weapon, a ghost with your own look. The silver ghost's orbs push your next body one level deeper in its tree. The gold ghost leaves its body fighting on for you. Each slot opens with a challenge that takes a few games, and a locked slot shows your progress.

**Monster tips.** When you become a monster, vanilla or mod, a note above your own HUD panel explains its moves. Pause > Tips gets pages for every mod god, status effects, ghost forms, objects and more.

**Menus and music.** A "Further" wordmark under the CRAWL logo, flame markers and embers on the main menu, picture grids in the vault, and four instrumental tracks that rotate in with the game's own music.

**Keep playing and Chaos.** After a win, Continue gives the game two more tries at the boss. A continued game, or one started from Chaos on the main menu, is a chaos game: the hero holds two spells, one on Special and one on the ghost button.

**Bosses.** The mod's two bosses are switched off in this version. They never spawn.

## Works with other mods

- **Online Crawl.** The host runs the game, and every player needs the same Crawl: Further version. Remote players use the ghost button from their own settings.
- **CrawlAPI.** Its Custom entry joins the god grid and opens CrawlAPI's own menu.
- **CrawlCustomBosses and other boss mods.** A boss another mod picked is never replaced, room objects never spawn in a boss arena, and the silver upgrade waits until the boss fight is over.
- **Mods built on Crawl Further Core** share the god list (a grid that pages once it is full), the vault and the test panel.

## Test panel

Curious how a final plays without reaching it? Open `BepInEx/config/CrawlMod.Debug.cfg` (it appears after the first launch) and set `TestMode = true` under `[Testing]`. In a game, **F2** opens a panel where you can become any monster, ghost form or the hero, spawn monsters and room objects, give yourself items and weapons, skip floors, go straight to the boss, slow the game down and show hitboxes.

While test mode is on, nothing counts toward your vault, challenges or secrets, and it switches itself off in an Online Crawl match. Set it back to `false` for real runs.

## For modders

The mod is two DLLs. `CrawlFurther.Core.dll` is a modding library with no content of its own, and `CrawlFurther.dll` is Crawl: Further built on it. A mod built on Core can add its own gods and monsters with their own moves. It can add shop items and weapons, room objects, vault pages and secrets, and buttons on the test panel. It works with Online Crawl the same way this mod does. Core can also export the game's own sprite atlases to PNG.

The source, the developer docs and an example mod (one god, three monsters, one spell) are on GitHub: [firefightermate/crawl-further](https://github.com/firefightermate/crawl-further), under the MIT license. Start with `docs/getting-started.md`. Core ships inside this package for now, so a mod built on it should list Crawl: Further as its dependency.

## Install

With a mod manager (r2modman or the Thunderstore app), install this mod and launch the game through the manager. BepInExPack Crawl comes with it as a dependency.

To install by hand, install BepInExPack Crawl first, then copy the `plugins` folder from this zip into `BepInEx` in your Crawl folder. On Steam Deck or Linux (Proton), set the game's launch options to `WINEDLLOVERRIDES="winhttp=n,b" %command%`.

When the mod loads, a small banner in the top-left corner reads "Crawl: Further 1.0.0" and "self-test OK". Back up `Crawl.sav` (in the Crawl folder) before your first run.

Updating from 0.9.x or older: the plugin folder is now `CrawlFurther`, so delete an old `BepInEx/plugins/CrawlMod` folder. Config file names are unchanged, so your settings and saves carry over.

## Controls and settings

- Ghost button (Binder fuse, gold ghost jump-out, the hero's second spell in chaos): **C** on the keyboard, **middle click** with the mouse or **X** on a controller. Rebind it in the controls settings.
- Pause > Tips: **Left** / **Right** jumps between topics on the mod pages.
- Vault grids: **mouse wheel** or **Page Up** / **Page Down** scrolls.

`BepInEx/config/CrawlFurther.UI.cfg` turns the menu touches and the music on or off, and `CrawlFurther.Objects.cfg` sets how often room objects appear.

## Reporting bugs

Open an issue on [GitHub](https://github.com/firefightermate/crawl-further/issues). Say what you were doing, and attach `BepInEx/LogOutput.log` and `CrawlMod_selftest.txt` (next to `CrawlFurther.dll`). If you play with other mods, list them and their versions.

## Credits

Made by firefightermate, aided by AI. Crawl is made by Powerhoof; this is a fan-made mod.
