CRAWL: FURTHER 1.3.1
====================

Crawl: Further (formerly "Crawl Mod") is a big content mod for Crawl. Nine new gods with 189 monsters between
them (21 each, plus minions and blob monsters), 15 secret monsters, 2 bosses (switched off for now), 25 new
weapons, 67 shop items (22 spells, 38 artifacts and 7 potions) plus 2 secret items, 32 room objects, hero
origins and ghost forms. Everything from the mod is marked in purple: a violet pip in the menus, or a small
violet gem on its picture (portraits, shop pictures, vault cells and the evolution menu). Names carry no tag.
Every mod monster, item, weapon, object, god, origin and ghost form has a vault entry, and everything has its
own drawn art.

Launch Crawl normally. The top-left banner shows "Crawl: Further 1.3.1" and "self-test OK" when everything
loaded. If anything failed, BepInEx\plugins\CrawlFurther\CrawlMod_selftest.txt lists what and why.
The mod is two DLLs in BepInEx\plugins\CrawlFurther: CrawlFurther.Core.dll (the library) and CrawlFurther.dll.
Delete an old BepInEx\plugins\CrawlMod folder when you update. The config files keep their old names, so
updating from any earlier version keeps your settings and saves. New settings files start with CrawlFurther.
The mod's two bosses are switched off in this version (see BOSSES).

NEW IN 1.3.1
------------
  - Mod monsters are exactly the same in vault challenges as in normal games, so a challenge shows how a
    monster really plays.
  - The Poltergeist's hex bolt can't hit the hero from on top of him, and does nothing in the shop.

NEW IN 1.3.0
------------
  - Crawl Chaos: a new Chaos entry on the main menu, under Play. Continuing a won game also turns it on. In
    chaos the hero holds two spells: Special casts the first, the ghost button the second (see CHAOS).
  - The join screen's controls pictures show the ghost button: the pad's X, the keyboard's C and the mouse's
    middle button in blue, with a Ghost row under Special.
  - Continue works in Online Crawl games: every player sees the prompt and anyone can answer it.

NEW IN 1.2.1
------------
  - Keep playing after a win: Continue gives two more tries at the boss, and anyone can win again. Turn it off
    with ContinueAfterWin in com.firefightermate.crawlfurther.cfg.
  - New art for every hero: close-up origin portraits in the style of the game's god portraits, matching
    silver and gold hero portraits and icons, and headwear redrawn to fit the hero's head in game.
  - Mod monsters are rebalanced against the game's own, in normal games and in vault challenges. Starters
    were well behind and are stronger now.
  - Tallow Grub is stronger: normal speed, a further and harder Wax Spit, a faster Melt that rises as soon
    as the puddle is under the hero, and a harder burst.
  - The secret monsters' finals have as much health as the gods' finals.
  - The Royal Grub has its own art.
  - Fixed: the Moth Matron's ember moths always flew right when not hunting a burning hero.
  - Fixed: the Fuse Scorpion's death animation, a Wire Wyvern that could freeze, the self-test's false reports
    and the Well Spirit's rarity line.

NEW IN 1.2.0
------------
  - Every god monster and secret monster has a challenge in the vault, like the game's own monsters: select
    it in MONSTERS and press Challenge. Play it against a bot hero who comes back stronger each time you kill
    him. Starters ask for hero level 4, tier 2 for level 7, finals for level 10. A passed challenge gets the
    game's tick on its vault cell, and the mod's violet gem moves to that cell's bottom-left corner.
  - Minions and blobs have no challenge, as the game's own have none.
  - A monster's vault page shows its challenge under its line. A few long lines are a little shorter so it fits.
  - Mod challenges never count toward Steam achievements, and playing one earns none.
  - Test mode: Run > Monster challenge starts any monster's challenge from the menus. Scores are not saved.
  - Pick your blob on its own page after confirming your ghost form. Forms with no choice skip it.
  - Long tips, names and banner lines no longer get cut off or drawn over other text.

NEW IN 1.1.0
------------
  - The Gleaner, Poltergeist and Binder earn their own blobs (Mote, Spitter, Gel) through a challenge each,
    played as that form. Until then they spawn the regular blob. After it, a row under the forms lets them pick.
  - Silver and gold ghosts pick from every earned blob and the new King Blob: a goo slam and a rain of globs
    that land where their shadows grow.

NEW IN 1.0.2
------------
  - Tier 2 and tier 3 monsters are stronger, in line with the game's own: more health on the finals, harder hits
    and specials that charge sooner.
  - Fixed runs getting stuck when a minion, a thrall or a spawned effect killed the hero: nobody took the crown
    and the dead hero's player never became a ghost.

NEW IN 1.0.1
------------
  - Fixes for the evolve screen with a translation mod: no white box, one violet gem per panel, and mod
    monsters stay inside their panel.
  - Mod content shows one violet gem everywhere. ModGem = false in CrawlFurther.UI.cfg hides them.
  - Tips, pause pages and the vault keep working when a translation mod swaps fonts or labels.
  - The Carrion Roc can no longer leave the ally it carried unkillable.
  - Online Crawl: a player who drops and joins again right away gets a working screen.

NEW IN 1.0.0
------------
  - All nine gods rebuilt (see GODS). Each of the 189 monsters has new art and a move or quirk of its own
    with a tell you can see, and its tips, vault line and its god's pause page are rewritten to match.
    Three monsters are replaced: the Ouroboros (was the Dice Rattler), The Sower (was the Amber Hornet) and
    the Gulper Eel (was the Storm Eel). Each god has its own gold idol portrait.
  - Everything else is redrawn too, from the origin portraits and the 25 weapons down to the 32 room
    objects, the blobs and the menus. It all sits in Crawl's own muted palette, with no hard black outline.
  - Test mode: an F2 panel for trying things without a full run (see TEST MODE).
  - The mod is now two DLLs: CrawlFurther.Core.dll, a modding library other mods can build on, and
    CrawlFurther.dll, the content.
  - Works alongside CrawlAPI and boss mods such as CrawlCustomBosses (see OTHER MODS).
  - The Leviathan and Pandemonium are switched off for now (see BOSSES).
  - Binder: only Gels fuse (2 make a Brute, 3 a Titan). The King Blob is gone, and Back no longer fuses.
    Every ghost form has its own tip.
  - Silver and gold idols: each slot pick starts on the top-left monster, and the ready screen shows the
    idol's perk god.
  - The Golden Duck has its own 1 in 500 roll per room (before, it turned up far more often than it should).
  - The hero still slides on Ysveld ice but no longer runs faster on it.
  - Potion effects with a timer count down only during fights, with a countdown by that player's HUD panel.
  - Fixes: monsters built on the gnome no longer make the hero drop gold; a hero who picks up a vanilla
    weapon after a mod weapon no longer turns invisible; vault text is never cut off; at most two Loose
    Jacks at once; a grown grub keeps its health when its body is used again; the Widow Matron's wrap
    wears off on its own.

NEW IN 0.10.0
-------------
  - THE VAULT: SECRETS. A page for every secret in Crawl: Further, 25 in all: the 3 silver uniques, the 7
    gold secret monsters, the 5 secret statues, 8 object secrets and 2 secret items. A secret you have not
    found shows as a silhouette with a short riddle and how rare it is. Once found it shows its picture, name
    and story. A new find is announced on the next menu. Found secrets are kept in
    BepInEx\config\CrawlFurther.Secrets.cfg.
  - 32 room objects (see OBJECTS): 7 ghost traps, a snare, warp stones, shrines and a strongbox for the hero,
    then the fun ones (Jukebox, Disco Ball, Slot Machine, Wishing Well, Pinata, Confetti Cannon and more)
    and a few that hide secrets.
  - 25 new items (see POTIONS AND TRINKETS): 7 stat potions, 16 trinkets and 2 secret items you can't buy.
  - 5 secret statue monsters (see SECRET STATUES), including the legendary Lachrymosa and her Lights Out.
  - God perks reworked so they show up in every fight: Vhorrul's dead burn as pyres that cool into tallow
    slicks, Ossivar's bone piles crawl to the nearest Ossivar monster, Sylvene's pods ripen in 2.5 s and burst
    wider, Bel'Mora's Rising Tide leaves brine pools every 14 s, Umbrael's bite echoes snap shadow jaws you can
    see, Jinx's Wild Card shows over the monster's head, Ysveld's blizzard lays ice paths every 12 s, and
    Kaurn's iron rods stand 9 s.
  - Every mod monster's melee now turns toward where it aims, so it can hit up and down too. The
    Jack-in-the-Box has its own up and down punches.
  - Size fixes: floating numbers, the Wishing Well and boss status icons are drawn at vanilla scale.
  - Every tier-3 monster, mod and vanilla, has a moonlit silver version of its art. The silver ghost's
    Ascension uses it, and an ascended body no longer grows bigger.
  - The silver upgrade follows vanilla trees all 4 levels deep.
  - Monster tips show for every player in multiplayer, each above that player's own HUD panel, and are
    smaller with 3 or 4 players. Options has "Tips: ALL / P1 ONLY / OFF".
  - Works alongside the Online Crawl mod (see ONLINE CRAWL).
  - Marrow Hound: a bone pile heals half its health, only while it is below 3/4 health.
  - Fixes: item buffs no longer stay on after the hero dies; the Phoenix Feather and Patchwork Bandage are not
    used up by hits your weapon guard blocks; objects no longer take the attack button from the hero in a
    fight; the Caryatid's columns can't trap the hero.

NEW IN 0.9.1
------------
  - Names no longer carry a mod tag. Mod things are marked only in purple: violet pips in the menus and a
    small violet gem on their pictures (portraits, shop pictures, vault cells, the vault's big picture).
  - MUSIC: Crawl: Further has its own instrumental tracks (BepInEx\plugins\CrawlFurther\music). When a new piece
    of gameplay music starts, there is about a 1 in 3 chance it is one of them, never the same one twice in a
    row. They follow the game's music volume and fade in and out like the game's own. Boss, level 10, win and
    lose music are never replaced. Settings in CrawlFurther.UI.cfg: CustomMusic (on/off), CustomMusicChance
    (0 to 1), CustomMusicOnTitle (also on the title screen), CustomMusicVolume.
    Soundtrack: "Further Down", "Tallow Hymn", "Gilded Rot" and "Lingbourn".
  - The silver ghost became Ascension (silver orbs upgrade your next body) and the gold ghost became Thralls
    (jump out of your monster and it fights on in gold). Silver orbs drop more often than before: 1 to 4 a
    death, about 2.3 on average.
  - 3 silver unique tier-3 monsters (Moonwarden, Comet Stag and the legendary Astrarch) that only a silver
    ghost's tier-3 upgrade can give you.
  - A secret gold monster line, 7 monsters in all. Where it hides is a riddle in the Secrets vault.
  - The gold idol's evolve screen shows all 4 monsters.

NEW IN 0.9.0
------------
  - The mod is now called Crawl: Further.
  - A "Further" wordmark sits at the bottom right of the CRAWL logo on the title screen and in the credits.
    It burns in when the logo settles, glints and throws the odd ember, and tears along with the logo when
    the logo glitches.
  - Main menu: small flames mark the selected item, embers and dust drift up behind the logo, and the
    version is shown bottom right.
  - The vault: WEAPONS, ITEMS and OBJECTS are picture grids like MONSTERS. Every entry has a picture
    (weapons show the hero holding that weapon in its own stance, items their shop picture, objects their
    vault picture). Undiscovered entries show a sealed "?". Select one to see its name, the big picture and
    its description below, as before. The mouse wheel and Page Up / Page Down scroll any vault grid.
  - The vault has a new FURTHER category: a page for every mod god, hero origin and ghost form (locked
    silver and gold slots show a padlock and what opens them).
  - Silver and gold slots for gods, heroes and ghosts: build your own (see SILVER AND GOLD SLOTS).
  - Six new ghost forms (ten in all), a ghost button you can rebind (the Binder fuses with it, mouse uses
    middle click), every hero origin has four colour sets (one per player slot), and most origins cost a
    little more.
  - Turn the menu touches off in BepInEx\config\CrawlFurther.UI.cfg (FurtherWordmark, MenuDressing, VaultGrid).

GOD SELECT
----------
The god list is always three rows of pips, no scrolling. Mod gods have violet pips.
The last two pips of the god list, the origin list and the ghost list are always the silver and gold
slots (see SILVER AND GOLD SLOTS below). New content is added before them.
Confirming a god opens two more pip lists in the same panel (arrows to browse, confirm, back).
Origin pips: violet = a weapon (or no item), blue = a spell, rose with a cyan glint = a weapon and a spell.
Violet pips are mod choices:
1. Hero origin (applies whenever you are the hero, and recolours the hero in game)
  Wanderer    the vanilla hero, no changes
  Sellsword   +1 VIT, -1 STR, -1 DEX, Tribal Shield
  Huntress    bow, -2 VIT, -2 STR
  Hexblade    magic staff, -3 VIT, -2 STR, spells recharge in 10% less time
  Flagellant  club, -3 VIT, bleeds when hit, double damage near death
  Pilgrim     +1 VIT, -1 STR, -1 DEX, heals on pentagrams
  Gambler     sling, -2 VIT, -1 STR, +15 gold, 20% off in shops
  Reaver      battle axe, -2 VIT, -3 DEX
  Cutpurse    practice knife, +1 DEX, -2 VIT, -1 STR
  Arbalist    crossbow, -3 VIT, -2 STR
  Scholar     Book of Flame, -2 VIT, -1 STR
  Silver/Gold your own hero: any look + any weapon (gold: and/or a spell), each pick has a stat cost
  Each origin also wears its own colours in each player slot (P1 blue, P2 red, P3 green, P4 amber).
2. Ghost form (applies whenever you are a ghost between bodies). Ten regular forms, then silver and gold:
  Wisp         vanilla
  Gleaner      blobs drift to you from far away and extra small wisps keep appearing, but each blob is worth less.
               your fodder is a pair of fast Motes
  Binder       your fodder is a Gel. Press the ghost button (see GHOST BUTTON below) with your Gels
               within about 90 px of you to fuse them: 2 Gels make a Brute, 3 make a Titan. Only Gels
               fuse, so a Brute or a Titan stays as it is. A dying Titan leaves a Gel behind
  Poltergeist  attack to throw a weak hex bolt at the hero (not from on top of him, not in the shop).
               Your fodder is a Spitter
  Banshee      attack wails for 3 ectoplasm, slowing a hero within 40 px. Your Keener fodder can slow
  Sexton       back digs up to 3 graves; a Revenant claws out when the hero comes within 52 px, or after 10 s
  Kindler      your fodder is Fusebelly bombs; attack lights the nearest one within 140 px
  Mason        your fodder is Gargling stone turrets; attack makes them all spit
  Hexer        attack throws a pin: the hero is hexed for 4 s and takes a quarter more damage.
               pickups are worth 0.85x
  Miser        back spends every stored body on one Mimic with that many times the health
  Silver / Gold  your own look (shape, colour, eyes, trail).
               Silver, Ascension: when your monster dies it drops 1 to 4 silver orbs (about 2.3 on average).
               Only your own ghost picks them up, by touching them. An orb lasts 20 s (it blinks for the
               last 3) and vanishes if the room is left. You bank up to 8 and they circle your ghost.
               With 8, your next body (circle, statue or blob) is upgraded one level deeper in its own
               tree (vanilla trees have 4 levels, mod trees 3). A final instead ascends: same size, its own
               moonlit silver art, +30 percent max health (healed to full) and silver sparks. Now and then
               it becomes a silver-only monster instead: Moonwarden or Comet Stag (1 in 5 each) or the
               Astrarch (1 in 25). A secret statue monster always ascends.
               No orbs drop in boss fights.
               Gold, Thralls: as a monster, press the ghost button to jump out. The body fights on in gold
               with its own moves (half max health, healed to 75 percent, 60 percent damage). One at a
               time, and not in boss fights (a gold padlock flickers on your monster instead). You get 2
               ectoplasm when the hero kills your thrall.
  GHOST BUTTON   defaults: keyboard 1 C, keyboard 2 B, keyboard 3 M, keyboard 4 full stop, mouse middle
               click, controller X. Change it in the game's controls settings (GHOST BUTTON row). The join
               screen's controls picture shows it in blue (a changed one is named under the picture
               instead). As the hero in a chaos game it casts your second spell (see CHAOS). In a Brute,
               Titan or King Blob it uses the blob's special; Back only leaves the blob.
3. Blob (a third page, after you confirm a ghost form that has a choice). The blob your ghost spawns with
  Back, shown in boxes where the god page shows its starters. Left and right (or the mouse) to pick, confirm
  to finish, back to return to the forms. It starts on the blob you had last. Forms with no choice skip it.
  Locked blobs show as a dark outline with their challenge and progress, and can't be confirmed.
  Gleaner      the regular blob, or its Motes (quick, fragile, in pairs). Earn them: gather 250 ectoplasm as
               the Gleaner
  Poltergeist  the regular blob, or its Spitters (slowing goo). Earn them: hit the hero with 40 hex bolts
  Binder       the regular blob, or its Gels (fuse into a Brute or a Titan with the ghost button). Earn them:
               spawn 40 blobs as the Binder
               Until a form earns its blob it spawns the regular one. After that its own is the default.
  Silver/Gold  the regular blob, any blob already earned, and the King Blob. The King is
               theirs alone: it slams out a ring of goo, and the ghost button rains globs that land where
               their shadows grow (0.8 s). 6.5 health (a Titan has 6), no Gel when it dies, costs 3 bodies of ectoplasm
  The other forms spawn what they always did. Bots always use their form's default.

SILVER AND GOLD SLOTS
---------------------
Build your own god, hero or ghost. Each slot opens with a challenge (bots, the tutorial and trials don't
count). A locked slot shows chains, a padlock and your progress, e.g. "12 / 60".
  Silver Idol    pick any god's perk, then any 3 starters from any god (vanilla or mod). Only the chosen
                 perk applies: the starters keep their own moves but not their own god's perk.
                 Opens when you evolve 60 monsters.
  Gold Idol      the same with 4 starters (the god page and the evolve screen get a fourth box).
                 Opens when you reach 20 different final forms.
  Silver Hero    any look (outfit, colours, skin, hair, head, face) and any weapon. Every pick costs VIT,
                 STR or DEX, stronger picks cost more. Opens when you kill 400 monsters as the hero.
  Gold Hero      the same, plus a spell. Opens when you win 5 games.
  Silver Shade   your own ghost look (shape, colour, eyes, trail) and Ascension. Opens when you gather 1000
                 ectoplasm.
  Gold Spectre   your own ghost look and Thralls. Opens when you kill the hero 40 times as a monster.
Each player slot remembers its own picks (BepInEx\config\CrawlFurther.*.cfg). To try everything at once,
set UnlockAll=true in BepInEx\config\CrawlMod.Debug.cfg (it also shows every secret in the vault).
Progress is kept in the CrawlFurther config files, and a banner announces each newly opened slot on the
next menu.

GODS
----
Each god has 3 starters, 6 tier-2 and 12 tier-3 monsters. Every starter and tier-2 monster offers two
evolutions of its own, nothing shared, so each god's tree has 12 paths, one to each final.

  Vhorrul, the Tallow Saint    wax and fire: the dead burn as pyres (28 px wide, about 5.5 s, 0.5 every 0.6 s)
                               that cool into tallow slicks for 8 s. Wax slows, and fire lights it.
                               Its monsters play with the floor: they swim in wax, soak it up, pour it
                               as fuses, and put fires out.
                               Finals include: Tallow Colossus, Wick Hag, Fuse Scorpion, Lantern Wraith
  Ossivar, the Marrow King     bones: the dead leave bone piles that crawl to the nearest Ossivar monster
                               within 90 px, which eats the pile as a bone plate that blocks a hit.
                               Its monsters build with bone, hunt by blood and carry the dead about.
                               Finals include: Charnel Rider, Church Grim, The Ossuary, Carrion Roc
  Sylvene, the Rot Orchard     the dead drop seeds that ripen in 2.5 s into spore pods. A pod bursts when the
                               hero comes within 20 px: 0.75 damage and poison in a cloud 34 px wide. Each
                               monster works the orchard: tending, shaking, slinging, hiding or sowing pods.
                               Finals include: The Rot Mother, The Sower, Briar Behemoth, Carrion Queen
  Umbrael, the Hollow Mirror   every basic attack repeats 0.6 s later as a shadow echo for half damage,
                               and each monster bends that echo or the dark its own way.
                               Finals include: The Hollow King, The Sundered, Sand Wraith, The Unblinking
  Bel'Mora, the Drowned Bell   hooks, currents and songs drag the hero in. Rising Tide: 1.5 s into a fight and
                               every 14 s after, the tide leaves 2 wide brine pools (3 when 3 or more
                               Bel'Mora monsters are up, 4 at most), and the dead leave brine. Brine slows the hero and
                               heals Bel'Mora monsters 0.35 a second.
                               Finals include: The Drowned Bell, Tide Matriarch, Gulper Eel, Abyss Kraken
  Jinx, the Grinning Jester    every special flips a Wild Card over the monster's head (heal / damage surge /
                               plate / speed). Cards pick a random curse, and dice deal damage per pip (a
                               Dice Imp's die 0.25 a pip, Snake-Eyes' 0.2), and the roll pops up as a number.
                               Finals include: The Grand Jester, Big-Top Chimera, Puppeteer, One-Armed Bandit
  Zhekra, the Brood Queen      insects and acid: the dead hatch a biting larva, acid makes you take 20% more
                               damage for 3 s, and resin roots. A Zhekra monster with any other monster within
                               64 px swarms (faster, harder hits). Most do something to or for their kin: the
                               Mother raises larvae into grubs, the Mortar aims through them, the Hunting Wasp
                               carries a Marked hero into the swarm, and a Botfly egg hatches a larva per hit.
                               Finals include: Brood Mother, Chitin Colossus, Amber Hive, Acid Mantis
  Kaurn, the Storm Forge       lightning and iron: a Kaurn monster or iron rod is linked by an arc to any
                               monster or rod within 70 px, and crossing an arc costs you 0.3. The dead leave
                               an iron rod for 9 s. Each attack stores a spark that the special fires. Every
                               monster works the circuit its own way: red-hot rods, a wired hero, beads that
                               run along the arcs, a wyvern that rides them, charges that blow when an arc
                               reaches them, and rods that take the bolt meant for you.
                               Finals include: Forgemaster, Wire Wyvern, Voltaic Pile, Tesla Spire
  Ysveld, the Frost Widow      ice and silk: while Ysveld monsters fight, a blizzard sweeps the room 1.5 s in
                               and every 12 s after, laying ice paths you slide on (they run 1.25x faster on
                               ice). The dead leave ice too. Three frost pips pin you for 0.8 s, and every
                               monster has a frost trick: a widow wraps you, a bride turns black, a geode splits.
                               Finals include: Widow Matron, Pale Empress, Winter Bride, Rime Colossus

MONSTER STATUES
  Mod finals can turn up as stone statues between fights, carved from their own art. As a ghost,
  step into one to become that monster, the same as the vanilla statues.

SECRET STATUES
  Now and then a statue in a statue room has a plinth mended with a glinting gold seam. Only a ghost can
  take it (never a bot), and nothing else in the game offers these five monsters. About 1 statue room in 12
  holds one of the first four (1 in 48 each). The legendary is about 1 in 200.
  Grotesque      a gargoyle that turns to stone for 2 s (no harm) and throws the hits it took back as shards.
                 Its first killing blow only crumbles it, and it reforms with 3.5 health.
  Sixfold Idol   each swing is a random weapon of four. Its rite is Ring, Fan, Spiral or Cross, and the sigil
                 over its head shows which comes next. All four come once before any repeats.
  Gambit         a chess knight: three L-shaped leaps, the landing marked first. A landing on the hero puts
                 him in check for 4 s, and its next slam on him is checkmate (0.8 more and a daze).
  Caryatid       raises marble columns under the hero that stand 6 s as solid stone (two at most), and takes
                 0.7x damage beside them.
  Lachrymosa     legendary. While the hero looks at her she is slow stone that takes 0.6x damage. Unseen,
                 she moves 1.4x faster and hits 1.3x harder. Lights Out: she pinches out her halo and the room
                 goes dark for 2.5 s. In the dark nobody can watch her, and she moves and takes damage as
                 normal.
  A ghost can also buy a secret statue at the Sculptor's Altar (see OBJECTS).

MONSTER TIPS
  When you become a monster (any monster, vanilla or mod, at any tier), a short note just above your
  own HUD panel explains its moves and its passive. Every player gets their own, in their colour,
  so in multiplayer each tip sits over the player it is for. It stays for 7 seconds (one more for
  each passive line), then fades. With 3 or 4 players tips are smaller, two lines and 5 seconds, and
  each player has one at a time. A tip fades while the hero walks behind it. The same text is the
  first page of Pause > Tips.
  Options has "Tips: ALL / P1 ONLY / OFF". The setting is saved in BepInEx\config\CrawlMod.Tips.cfg.

PAUSE > TIPS
  The game's own Gameplay Tips gain pages. In order: YOU (the monster you are right now), each mod god
  in this game, the game's own five pages, STATUS, ICONS, GHOSTS, SLOTS (silver and gold), the page on
  how each slot opens, the other mod gods (VHORRUL, OSSIVAR, SYLVENE, UMBRAEL, BEL'MORA, JINX,
  ZHEKRA, KAURN, YSVELD), then TRINKETS, OBJECTS, FUN (party, games and secrets) and STATUES.
  Next / back work as before. On the mod pages Left and Right jump to the previous or next topic.

INDICATORS
  Small markers show what is going on. Over the head: shields (plates left, each blocks one hit), lightning
  bolts (stored Kaurn sparks, max 3), ice crystals over the hero (frost pips, 3 pin him), a red double
  chevron (more damage for a while). At the feet: green sparkles (healing), white streaks (faster), a blue
  skid (on Ysveld ice), plus the overlays for slow, root and stun. A Lucky Die dodge shows DODGE.

BOSSES
  The Leviathan and Pandemonium are switched off in this version. They never spawn, and their tips and
  pause page are hidden. The setting is Enabled under [Bosses] in BepInEx\config\com.firefightermate.crawlfurther.cfg.

SHOP: 22 spells, 38 artifacts and 7 potions (67 items). Their shop pictures carry the violet gem, and the
descriptions give the numbers. Shop pedestals show a small vanilla-style sprite for every mod item and weapon.
The big picture is the pop-up.

POTIONS AND TRINKETS (new in 0.10.0)
  Potions change your stats for good. Some have a short catch, shown on the hero.
  Troll Marrow       25 gold  +2 VIT, but 20 percent slower for 15 s
  Wyrm Blood         25 gold  +2 STR, but 0.15 damage a second for 3 s (never below 0.5 health)
  Hare's Dew         25 gold  +2 DEX, but 20 percent less damage for 15 s
  Berserker's Grog   20 gold  +3 STR, -2 VIT
  Stoneskin Draught  20 gold  +3 VIT, -2 DEX
  Quicksilver        20 gold  +3 DEX, -2 STR
  Chaos Brew         10 gold  +2 to one random stat, -1 to another (arrows show which)
  Fun trinkets: Party Hat (confetti on kills, every 8th kill drops 5 gold), Bard's Lute (a seeking note
  every 7 s), Pet Ferret (fetches gold within 70 px), Bubble Pipe (slowing bubbles while you walk), Rubber
  Duck (squeaks monsters away when you are hit), Firefly Jar (3 zapping fireflies), Dancing Shoes (25
  percent faster for 2 s after your spell).
  Little trinkets that change a run: Whetstone (first hit on each monster deals 1.5x), Phoenix Feather
  (survive one killing hit on 0.5 health), Siphon Gem (each kill charges your spell by 1 s), Glutton's Fork
  (health pickups heal 1.5x), Tally Stick (+4 percent damage every 8 kills, up to 20 percent), Gambler's
  Coin (heads: 20 percent more damage, tails: 20 percent faster, each fight), Patchwork Bandage (the first
  monster hit each fight does half damage), Wanted Poster (the toughest monster takes 1.4x damage from you),
  Iron Boots (no knockback, 8 percent slower).
  Two items are never sold. Look for them behind the dungeon's walls.

OBJECTS (new in 0.10.0)
  About 38 percent of rooms get a Crawl: Further object, and 12 percent of those a second one (never the
  start room, shops or boss rooms). Each object has a vault page.
  Turn them off or change the odds in BepInEx\config\CrawlFurther.Objects.cfg.
  Ghost traps (step a ghost in, aim with movement, attack to fire; the number is the reload):
    Chain Winch     a hook, 0.4 damage, drags the hero to the winch. 2.5 s
    Steam Vent      a 36 px jet, 0.6 damage and a hard shove, 8 directions. 2 s
    Tar Spout       a glob, 0.4 damage, leaves a slowing tar pool for 3 s. 3 s
    Pendulum Blade  1 damage under its frame, swinging each way in turn. 1.2 s
    Rune Plate      a fire ring bursts 0.7 s later, 1.2 damage. 3 s
    Toll Bell       0.3 damage and a 0.6 s daze within 30 px. 4.5 s
    Scatter Idol    three bone darts in a fan, 0.6 damage each. 1.6 s
  On the floor: the Iron Snare holds whoever steps in for 0.8 s (0.5 damage, resets in 6 s). Warp Stones
  come in pairs: step on one to stand on the other.
  For the hero, outside fights, once each: the Mending Spring heals 3 over 6 s, the Weapon Rack swaps your
  weapon for one of like worth, the Ward Shrine (30 gold) halves damage taken until 15 s into your next
  fight, the Cursed Altar gives 1.3x damage dealt and taken for the rest of the floor, and a Strongbox holds
  30 to 55 gold (but 1 in 4 is a mimic that bites for 1). A ghost smashes a Spirit Urn to fill its
  ectoplasm, unless the hero takes it first for 20 gold.
  Fun ones: the Jukebox changes the music for the rest of the floor (anyone can play it). The Disco Ball
  lights the floor for 20 s; stand on a lit tile for 4 beats in a row for Disco Fever (20 percent faster for
  8 s). The Confetti Cannon knocks back and dazes everything in front, then the whole room is 15 percent
  faster for 10 s. Hit the Pinata 3 times for 10 to 18 gold. The Bounce Shroom flings you about 60 px. A
  Firework Crate fires 6 rockets 2 s after it is lit.
  Games of chance: the Slot Machine (5 gold a pull, 8 pulls), the Fortune Teller (3 gold a reading, some
  are hints) and the Wishing Well (1 gold a coin, 1 in 10 coins grants a wish).
  Secrets: the Lever Trio, the Cracked Wall, the Mysterious Keyhole, the Sculptor's Altar (a ghost pays 3
  ectoplasm for a secret statue, 1 in 20 is the legendary), the Watching Portrait and the very rare Golden
  Duck all hide something. The vault's SECRETS page has a riddle for each.

CHAOS
  A game mode that grows with each update. Start it from Chaos on the main menu (under Play), or continue a
  won game: a continued game is a chaos game until it ends. Not in the tutorial or vault challenges.
  Two spells: the hero holds two. Special casts the first, the ghost button the second, and each charges on
  its own. The second spell's charge shows in a blue bar under the special bar, and the hero stats panel
  names both. Buying a spell with one held makes it the second. Buying one with two held asks which to drop
  (the shop's text says so before you buy). Bots use whichever spell is ready and drop the cheaper one.
  Turn chaos off with Chaos under [Game] in com.firefightermate.crawlfurther.cfg.

TEST MODE
  For checking things without playing a whole run. Off by default: set TestMode = true under [Testing]
  in BepInEx\config\CrawlMod.Debug.cfg. F2 opens the panel (mouse-driven): become any monster, ghost form
  or the hero, spawn hostile monsters and room objects, give the hero items and weapons, pick the run's
  gods, skip floors, go to the boss, slow the game down and show hitboxes. It also turns on Crawl's own
  hidden debug menu (Tab + `), and start any monster's vault challenge from the menus. While it is on,
  nothing counts toward the vault, challenges or secrets.
  It turns itself off in an Online Crawl match. Set it back to false for real runs.

OTHER MODS
  CrawlAPI: its Custom entry joins the god grid and opens CrawlAPI's own menu.
  Boss mods such as CrawlCustomBosses: a boss another mod picked is never replaced, room objects never
  spawn in a boss arena, and the silver upgrade waits until the boss fight is over.

ONLINE CRAWL
  Crawl: Further works alongside the Online Crawl mod. The host runs the game, and everyone must have the
  same Crawl: Further version installed. Each remote player's ghost button comes from their own PC's
  settings. A remote mouse player pauses with Escape (middle click is their ghost button). A remote
  keyboard player who presses Left and Right together also presses the ghost button. Slot progress and
  secrets found by remote players are saved on the host's PC. "Tips: P1 ONLY" means the host. Vault
  scrolling with the wheel or Page Up / Page Down works on the host only; remote players scroll the vault
  with the stick.
  A player who loses the connection can join the host again. During a run their character plays as a
  bot meanwhile: back in, press Start and pick Drop In (not offered during a boss fight).

WEAPONS (in the weapon shop slots)
The hero swings each one with the closest vanilla weapon's animation, and the weapon in your hands is
drawn from its own art.
  Gravehook       spear       the thrown hook drags the monster to your feet
  Moonglaive      knives      the glaive flies out, hangs, and comes back, hitting both ways
  Riftblade       sword       marked monsters take 35% of the stored damage again 0.8 s later
  Snake-Eyes      club        every swing rolls a die: 1 = weak, 6 = double damage and a gold burst
  Tidebreaker     greatsword  the third swing sends a wave that carries monsters, and walls hurt and stun
  Leechfang       dagger      hits send blood beads back to you, and every 5th heals
  Briarbow        bow         arrows plant briar patches that prick and may root
  Dirge Maul      axe         slams ring a stunning bell, and every 3rd tolls a second, wider ring
  Wickstaff       staff       bolts leave soul fire, and monsters that die in it release a seeking wisp
  Arcbolt         crossbow    bolts chain to up to 3 more monsters for 60% each jump
  Frostbrand      sword       cuts chill (35% slow), and the 3rd chill shatters for damage around the monster
  Mercyblade      sword       below 35% health, every cut on a monster strikes twice
  Reaper          greatsword  each kill adds +10% damage (max +50%), lost when you get hit
  Starfall Maul   axe         slams open a star well that pulls monsters in, then implodes
  Hydra Bow       bow         an arrow that flies far enough splits into three shards
  Bulwark Mace    club        every 3rd hit raises a ward that blocks the next hit and bashes the attacker
  Heartseeker     crossbow    bolts pierce, hitting 40% harder for each monster already pierced
  Shadow Kris     dagger      a stab in a monster's back hits again for 1.5x the damage
  Blightstaff     staff       plague damages over 2 s, then jumps to another monster (up to 3 jumps)
  Orrery Staff    staff       each cast adds a star that circles you for 5 s (max 3)
  Grudgestone     sling       stones home in on the last monster that hurt you and hit it twice
  Midas Sling     sling       coins hit harder the more gold you carry, and a coin kill pays 2 gold
  Charger Lance   spear       after 0.5 s of running, the next thrust charges for x1.8 and heavy knockback
  Viper Lash      knives      a whip: the tip cracks for big damage and may stun, the rest only grazes
  Hunter's Kunai  knives      a thrown kunai marks a monster for 3 s, and your next slash on it deals +0.7

SLOWS, ROOTS AND STUNS (mod sources)
  Slow 1 s (45% slower), root 0.8 s (85% slower), stun 0.6 s. After any chain of these lasts 1.2 s, the
  target is immune to all three for 3 s. None of them stop you attacking except the short stun.

BALANCE
  Evolving costs the vanilla amounts again (2.5 wrath for tier 2, 4.5 for tier 3). Evolved mod monsters
  have vanilla-level health, hit the hero 15% (tier 2) or 20% (tier 3) softer than their raw moves, and
  their specials recharge 25% slower. Shop items were toned down (the descriptions in game have the numbers).
  Mod monsters are drawn to vanilla sizes (starters no bigger than a goblin), their hurtboxes match their
  art, and every attack's hitbox was checked against where the art strikes.
  Fixed the monster pictures in the evolve menu.

Source, developer docs and an example mod: https://github.com/firefightermate/crawl-further (MIT license).
