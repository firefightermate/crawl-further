# Art

Crawl draws everything with ex2D, a Unity 2D plugin: an `exAtlas` (a texture cut into elements) and
`exSpriteAnimClip`s (lists of atlas elements with frame times and events). Core builds both at run time from plain
PNG and JSON files, so a mod never touches the game's asset files. The code is in `CrawlFurther.Art`.

## The sheet format

A sheet is `Name.png` plus `Name.json` in a mod's `art/` folder. The PNG is a grid of equal cells, and the JSON
describes the grid and names the animations:

```json
{
  "cellW": 32, "cellH": 32,
  "cols": 8,
  "anims": [
    { "name": "Idle",   "frames": [0, 1, 2, 1], "durations": [0.15, 0.1, 0.15, 0.1] },
    { "name": "Attack", "frames": [8, 9, 10, 11] }
  ]
}
```

- `cellW` and `cellH` are one cell's size in pixels. Every frame is one whole cell.
- `cols` is the number of cells per row. Cells are numbered from 0 at the top left, left to right, then down.
- `frames` lists cell numbers in play order. `durations` is seconds per frame. Leave it out for 0.1 s a frame.
- Animation names are matched without regard to case. Keys Core does not know are ignored, so tools can add their
  own.

Cells are not trimmed: the sprite is the whole cell, so draw every frame in the same place within its cell.
Textures load with point filtering.

### Where the feet go

For monsters and room objects the floor point is the pixel at (`cellW / 2`, `cellH - 2`) counted from the cell's
top left: the centre column, two rows up from the bottom. `MonsterFactory` puts that pixel on the monster's
transform, so draw the feet there and the shadow lines up. Effects choose their own origin (see `Strike.ArtAt`
and `Strike.Ground` in [monsters.md](monsters.md#placing-effects)).

### What each kind of sheet needs

| Sheet | Animations | Size |
| --- | --- | --- |
| Monster (`MonsterDef.art`) | `Idle`, `Run`, `Death` (or a one-frame `Dead`) and a one-frame stone `Statue`. `Knockback`, `Portrait` and `Spawn` are optional and fall back to `Idle`. Plus one per move your kit builds | Any cell size. Crawl: Further keeps the visible Idle frame within 20 x 16 (tier 1), 28 x 26 (tier 2) and 42 x 40 (tier 3) |
| God portrait (`GodDef.portraitArt`) | `Portrait`, or `Idle` when there is no `Portrait` | 29 x 24 |
| Shop bubble (`ItemDef.bubbleArt`) | `Bubble` (or `Idle`) | Crawl: Further uses 34 x 41 |
| HUD icon of an artifact (`ItemDef.hudArt`) | `Hud` (or `Idle`) | Crawl: Further uses 11 x 7 |
| Shop pedestal pictures (`ShopPedestal.AddSheet`) | One per purchasable, named after it; frame 0 is used | 35 x 33, the item standing bottom-centre |
| Room object (`ObjectDef.art`) | See [objects.md](objects.md) | Any |
| Vault category stamp (`VaultCategory.stamp`) | Frame 0 | 59 x 48 |

`Death` should end on the corpse: Core plays it once and holds the last frame. `Statue` has no fallback: without it
the monster keeps its base's statue art, and the self-test reports it.

## Loading sheets

Core adds `<plugin folder>/art` for every mod registered with `Further.AddMod`, so most mods never load a sheet by
hand: `MonsterDef`, `GodDef`, `ItemDef` and `ObjectDef` take sheet ids. To get one yourself:

| Call | Returns |
| --- | --- |
| `SpriteSheets.Get(id)` | The sheet from the first art folder that has `<id>.png` and `<id>.json` |
| `SpriteSheets.Load(modDir, id)` | The sheet from `<modDir>/art` only |
| `SpriteSheets.ByAtlas(atlas)` | The sheet an atlas came from, or null for vanilla atlases |

Folders are searched in the order they were added (Core's first, then each mod's in load order). A sheet is
loaded once and cached by id. A missing sheet returns null and logs `Art missing for <id>`. Because the id is the
cache key, two mods that both ship a sheet called `Shared` get whichever was loaded first. Prefix your ids.

`SpriteSheet` gives you `id`, `atlas` (the `exAtlas`, element `i` is cell `i`), `manifest`, `Anim(name)` and
`Has(name)`. `SpriteSheets.FromTexture(id, texture, manifest)` wraps a texture you made in code. It is not
cached, so `Get` will not find it.

Runtime-made textures, atlases, materials and clips need `SpriteSheets.Keep(obj)` or Unity unloads them on the
next scene change. Core does this for everything it builds.

## Clips: ClipBuilder

`ClipBuilder` turns an animation into an `exSpriteAnimClip` and pins events to frames:

```csharp
var dashClip = new ClipBuilder(sh, "Dash", "ModGlimmerRatDash").Once()
    .EvF(0, "AnimInputMultiplyFreeFace", 0f)
    .Ev(2, "AnimInputMultiplyStop").Ev(2, "AnimInputOff").EvF(2, "AnimMove", 330f).Ev(2, "AnimCollideOff")
    .Ev(2, "AnimAttack", dash).EvO(2, "AnimSound", voice)
    .Ev(6, "AnimMoveStop").Ev(6, "AnimCollideOn")
    .Ev(-1, "AnimRun")
    .Build();
```

(from `examples/ExampleGod/GlimmerPack.cs`)

- The clip name (`ModGlimmerRatDash`) must be unique in the game: ex2D finds clips by name, so two clips with one
  name play whichever was registered first.
- `Ev(frame, method)` sends `method` when that frame starts. `Ev`, `EvF`, `EvS`, `EvO` and `EvB` add an int,
  float, string, object or bool parameter, and an optional offset in seconds. A negative frame counts from the
  end: `-1` is the last frame. Events stay on their frames if you retime the art.
- `Loop()` or `Once()` (the default), `Speed(k)`, `Durations(...)` to override the frame times, `Repeat(n)` to play
  the frames n times, and `Then(anim, repeat)` to append another animation of the same sheet.
- Events reach every component on the object through `SendMessage`. The game's `Player` handles the `Anim...`
  events. `Kit.Melee` and `Kit.Shot` build the common attack clips for you ([monsters.md](monsters.md#kits)).

`SpriteSheets.MakeClip(sheet, anim, template, name)` copies a vanilla clip instead: same events, new frames. With
the same frame count and no `durations`, the template's timing is kept. Otherwise its events are stretched to
the new length.

## Sheets drawn at another size: ArtScale

`ArtScale.BySheet["MySheet"] = 0.75f` tells `MonsterFactory` that a sheet was redrawn at three quarters of the size
its kit was written for. The kit's effect offsets are scaled to match. Fill it before your packs run.

## Exporting the game's art: Ex2DExport

`Ex2DExport` writes any atlas or clip, vanilla or modded, to files you can read and edit:

| Call | Writes |
| --- | --- |
| `Ex2DExport.Atlas(atlas, dir)` | `<dir>/<atlas name>.png` and `.json`, in the sheet format above |
| `Ex2DExport.Clip(clip, dir)` | `<dir>/<clip name>.json`: frames, timings and events |
| `Ex2DExport.All(dir)` | Every loaded atlas to `<dir>/atlases`, every loaded clip to `<dir>/clips`, and a list of the atlases in `<dir>/index.txt` |

Without code: set `DebugKeys = true` under `[General]` in `BepInEx/config/CrawlMod.Debug.cfg` and press F8 in the
game. Everything loaded at that moment goes to `ex2d_export` in Core's plugin folder (it takes a few seconds).
F9 swaps the hero and monster atlases red and blue, to check that a recolour reaches every clip. Leave
`DebugKeys` off when you play.

The game's atlases are packed (frames trimmed, some rotated). The export unpacks them onto a grid where every
cell is as big as the largest frame and each frame sits bottom-centred at its original size. The JSON adds
`source` (the atlas name) and `elements` (each cell's original name and size), and its `anims` list every loaded
clip drawn only from that atlas. An exported atlas is a normal sheet: copy it into your art folder, edit it and
load it with `SpriteSheets.Get`. An atlas too big for one grid texture is written packed, with `"packed": true`
and each element's rectangle.

## The rig scripts

Crawl: Further's own art is drawn by Python scripts in `tools/sprites/` (they need Pillow). Each writes sheets
into an `art/out*` folder, with a `_preview.png` beside each sheet. They are written for this mod, but
`tools/anim.py` (packing frames into a sheet) and `tools/sprites/jinx_v2_rigs.py` (shading by material) can be
reused. `tools/validate.py` checks every sheet the
code names ([building.md](building.md#checks)).
