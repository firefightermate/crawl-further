# Working with other mods

Core talks to the mods below through reflection only. It has no compile-time reference to any of them, nothing
runs when they are not installed, and a lookup that fails turns off only its own feature. The self-test has a
section for each that says what was found. The code is in `CrawlFurther.Compat`.

## Online Crawl

Online Crawl (BepInEx GUID `crawl.online`, written against 0.4.1) runs the game on the host. Every client mirrors
the host's renderers, materials, textures, cameras and sounds, and sends only its controllers' seven game inputs
plus Escape. Clients rebuild the host's picture from names, so a mod's art works online as long as its names
follow these rules. Art loaded through Core follows them already:

- A sheet's texture is named `Mod_<sheet>`, its atlas `ModAtlas_<sheet>` and its material `ModMat_<sheet>`
  (`OnlineNames`). A client that has not loaded the texture yet reads `art/<sheet>.png` from its own install
  instead of asking the host for it.
- A texture you compose at run time should be named `OnlineNames.ComposedTexture(parts...)`, a key that names its
  exact pixels, so a client never reuses a different picture with the same name.
- A texture you repaint while it is shown keeps an empty name and goes to `CompatOnline.TextureChanged(texture)`
  after every `Apply`. A mesh you edit by hand (not an ex2D sprite) goes to `CompatOnline.MeshChanged(mesh)` after
  every edit. Online Crawl only watches ex2D meshes and the textures its own colour swapper writes.

Host and clients must run the same versions of every mod: a file with the same name but other pixels is used as it
is.

Core also handles the input side. A client's ghost button reaches the host as a Left and a Right press on the same
frame, which a stick cannot do; the host takes the pair out before the game sees it. A remote mouse player's
middle click is the ghost button. The slot editors accept a remote mouse pointer.

`CompatOnline.Present`, `IsHost` and `IsClient` tell your code where it is running. Test mode switches itself off
for the length of an online session ([testing.md](testing.md)).

## CrawlAPI

CrawlAPI (Anumania's, GUID `org.anumania.plugins.crawlapi`) adds a "Custom" entry to the end of the god list and
its own menu for the gods in `DeityAPI.customDeities`. Its hooks expect Trials to be the second-to-last entry,
which is no longer true once Core's god grid or Crawl: Further's idol entries follow Trials. With CrawlAPI loaded,
Core:

- lays the god grid out again when the entry count changes, so the Custom entry joins the grid,
- answers the entries the vanilla select code would misread (Trials by its real index, the entry CrawlAPI's patch
  takes for Trials, Custom and any other mod entry after Trials), so selecting Custom opens CrawlAPI's menu,
- leaves CrawlAPI's gods in CrawlAPI's own menu. They are not folded into the grid.

`CompatCrawlApi.CustomDeities` lists CrawlAPI's gods.

## Boss mods

Rules for any mod that adds final bosses by cloning a vanilla boss room. CrawlCustomBosses (CrawlBossKit and its
boss plugins, GUIDs `com.zac.*`) is the case they are tested against:

- `BossFactory`, which picks mod bosses, runs last and replaces only a vanilla pick (`CompatBosses.IsVanillaBoss`), so a boss
  another mod chose for the run is never swapped out.
- Room objects never spawn in a boss arena (`CompatBosses.IsBossArena`).
- In a fight against another mod's boss (`CompatBosses.ForeignFight`), monster tips show only text written for what
  the player controls.

Crawl: Further's own two bosses are switched off in this version (`[Bosses] Enabled` in
`BepInEx/config/com.firefightermate.crawlfurther.cfg`).

## Two mods built on Core

Mods built on Core share the god list, the vault and the art folders. To stay out of each other's way:

- Prefix every id: sheets, `MonsterDef` ids, item and object ids, clip names. A sheet id is global, and the first
  folder that has it wins.
- Name templates and prefabs `Mod...` (Core's own factories do this), so Core and Online Crawl treat them as mod
  objects.
- Keep your self-test sections to your own content. `DeityFactory.BuiltNames` and `MonsterFactory.Built` list
  every mod's gods and monsters, not just yours.
