# Contributing

Bug reports, fixes and new content are welcome. For anything large, open an issue first so we can agree on where it
goes.

## Reporting a bug

Include `BepInEx/LogOutput.log`, `BepInEx/plugins/CrawlFurther/CrawlMod_selftest.txt`, the list of other mods you
have installed, and what you did just before the problem.

## Core or content?

The repo holds two assemblies, and the rule for which one a change belongs in is simple: if another modder adding a
god of their own would need it, it goes in Core (`src/CrawlFurther.Core`). If it names one of Crawl: Further's
gods, monsters, items, objects, ghost forms or origins, or holds text a player reads, it goes in the content mod
(`src/CrawlFurther`). Core must compile without the content mod. A file that would mix both is split.

## Code style

- C# 7.3 for the game's Mono (.NET 3.5 profile). No APIs newer than that.
- PascalCase for types, methods and properties. Private fields keep the game's own `m_` and `s_` prefixes.
- Every public member of Core has a one- or two-sentence XML doc comment.
- Comments say why, briefly: an engine quirk, a pooling rule, a number's source. No change history and no
  commented-out code.
- One main type per file, named after it. Folders follow namespaces (`CrawlFurther.Monsters` lives in
  `src/CrawlFurther.Core/Monsters`).
- Never touch a game type from a plugin's `Awake` ([getting-started.md](docs/getting-started.md#how-a-mod-starts)).
- Reach private game fields through `R.Get` and `R.Set`, and reflection on other mods through the `Compat` classes.
- Name every runtime-made prefab, template and clip with a `Mod` prefix and a unique name.

## Text a player sees

Plain words and real numbers ("0.6 damage", "for 3 s"). Monster tip lines stay within 60 characters with their
label, vault lines within 90 and three rows of the vault page, and the god select's texts (a god's text and flavour, an
origin's or ghost form's summary and flavour) within the four lines the game's own take there (`tools/validate.py`
measures them). No `[word]` (the game's text drops it), and none of `% { | } ~` in the text of secrets,
challenges or room objects. `tools/validate.py` and `tools/merge_tips.py` check most of this.

## Before a pull request

```sh
./build.sh                       # 0 warnings
python3 tools/validate.py        # OK
python3 tools/check_trees.py     # OK
python3 tools/merge_tips.py      # after changing data/tips
```

Then start the game with your build and check that the banner says "self-test OK". [docs/testing.md](docs/testing.md)
describes the test panel for trying content without playing a whole run.

- Never commit DLLs, `lib/`, `build/` or `*_preview.png` files (`.gitignore` covers them).
- Art changes go through the rig scripts in `tools/sprites`, not by hand-editing the PNGs, so they can be rebuilt.
- Keep commit messages plain: what changed and, when it is not obvious, why.

By contributing you agree that your work is released under the repo's [license](LICENSE).
