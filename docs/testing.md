# Test mode

Test mode lets you try a god, a monster, an item or a boss without playing a whole run to reach it. It adds a
panel (F2) and switches on Crawl's own hidden debug menu. It is part of Crawl Further Core, so any mod built on
Core can add its own buttons to the panel.

It is off by default. With it off, nothing in the game changes.

## Turning it on

Open `BepInEx/config/CrawlMod.Debug.cfg` (it appears after the first launch with the mod) and set:

```
[Testing]
TestMode = true
PanelKey = F2
```

Start the game. The load banner at the top left gets a second line:
`Test mode on: F2 opens the test panel, Tab + ` the game's debug menu`.

Test mode never runs in a Crawl Online match. While you host or join one, the panel stays shut, every switch
below goes off, the game's debug keys stop, and the banner says `Test mode is off online`. It comes back when
the session ends.

Set `TestMode = false` again for real runs. While test mode is on, nothing you do counts:

- monsters you become or spawn are not marked found in the vault,
- challenge counters (hero kills, finals reached, ectoplasm banked and the rest) do not move,
- secrets you become, spawn or take are not recorded.

Crawl's own lifetime stats (games played, gold earned) still count, as they do with its debug menu.

## The panel

Press F2 (or your `PanelKey`) to open or close it. Use the mouse. The window is sized for 1080p and scales with
the screen height, so it reads the same at 1440p. Drag it by its title bar.

Along the top are the pages. Under them:

- **Acting for**: the player that Become, origin, god and gold actions apply to. `Auto` picks the first human
  monster player, then the first monster player. Click a player to choose one yourself. The hero is listed too,
  for the god and gold actions.
- **Pause while open**: pauses the game with its own pause while the panel is up. Clicking an action resumes
  the game for a moment so the action can play out, then pauses again. Turn it on before typing in a search box;
  the game still reads the keyboard.
- A line that says what the last action did, or why it could not.

Each page has buttons and switches on the left and lists on the right. Lists longer than 12 entries have a
search box. Entries are grouped under small headings (tiers, Crawl or Mods).

### Become

| Control | What it does | How the game does it |
| --- | --- | --- |
| Become a ghost | A monster body dies, a ghost turns into a fresh ghost | The body's own death (`Health.Suicide`), so the ghost form, death effects and ectoplasm all happen |
| Become the hero (kills the hero) | Your monster kills the hero and takes the crown | The hero dies to your monster (`Health.InstaKill` with your player as the killer), so the full hero change plays |
| God, then Monster (by tier) | Pick any god, vanilla or mod, then any monster of its tree | The game's debug body swap (its Tab + M key): spawn the new body where you stand, drop the old one, `InitAsPlayer` |
| Hero origin | Sets the acting player's origin | `HeroClasses.Apply`. Stats and the starting weapon apply while the player is not the hero |
| Ghost form (Crawl: Further) | Choose a ghost form and become that ghost | Sets the form as the picker does, then Become a ghost. The silver and gold forms need Open everything |
| Ghost blob (Crawl: Further) | Choose the blob your ghost spawns with Back, and become a ghost | Sets the pick as the blob row of the ghost page does, then Become a ghost. A blob that does not fit the form is refused; the Mote, Spitter and Gel need their challenge or Open everything, the King a silver or gold form |
| Silver ascended final (Crawl: Further) | Become any final in its silver ascended form | The body swap, then the silver ghost's own ascension |

### Spawn

| Control | What it does | How the game does it |
| --- | --- | --- |
| Hostile monster | A monster appears beside the hero and fights | Monsters with their own AI (fodder, blobs) run it (`InitAsAI`). Any other monster is given to a bot in a free player slot (`SystemPlayers.AssignBot`), so it fights with its real moves |
| Remove the test bots | Takes out the bots added above, body and all | Despawns the body and unassigns the slot. A bot that became the hero stays |
| Room object | Places any registered room object beside the hero | `ObjectKit.SpawnAt`. Never in a boss room |

A run has four player slots. Hostile monsters that need a bot stop when all four are in use.

### Items

| Control | What it does | How the game does it |
| --- | --- | --- |
| Item or spell (to the hero) | The hero gets it at once | `Powerup.Collect`, as a god's starting gift (not a vault find) |
| Weapon (to the hero) | Puts the weapon, or one of its named variants, in the hero's hands | `Player.ChangeWeapon`, as the game's Tab + W key |

Items go straight to the hero. Crawl sells items on shop pedestals and has no free floor pickup for them, so
there is nothing to drop at his feet.

### Run

| Control | What it does | How the game does it |
| --- | --- | --- |
| Go to floor | The next floor is the number you set (1 to 99) | Sets the floor counter, then ends the floor as the stairs do. The evolve screen comes first. The floor's look changes once, not once per area skipped |
| Next floor | Ends this floor | The game's own level end (its Tab + Shift + R) |
| Go to the boss now | Opens the boss portal | `BossEncounter.Start` with the boss picked below |
| Open the doors | Opens the room and clears its monsters | The game's Open Doors |
| Next room | Moves the hero through a door, to an unseen room when there is one | The game's teleport (`OnTeleportToRoom`), as its Go To Store does |
| Go to the shop, Go to the portal room | Moves the hero there | The game's Go To Store and Go To Portal |
| Reload this floor | Loads the floor again | The game's Reload Level |
| God of the player acting | Swaps the god mid-run, so its tree and perks apply | `PlayerData.SetDeity`, as the god select does. Gold resets to the god's starting gold |
| Boss | Picks the boss for Go to the boss now: vanilla bosses, mod bosses when they are switched on, or the game's pick | With mod bosses built, the run's own next boss fight takes the pick too |

### Player

| Control | What it does | How the game does it |
| --- | --- | --- |
| Everyone: +1 level and evolve | Every player gains a level and evolves | The game's Increment Lvl + Evolve |
| Everyone: skip to level 10 | Every player jumps to level 10 or more and evolves as far as it can | The game's Skip to Lvl 10 |
| Hero level | Raises the hero to that level (2 to 30) | Normal level-ups, one by one. Levels only go up |
| Gold for the player acting | Adds gold (1 to 99999) | `PlayerData.OnGoldCollected` |
| Full heal: everyone | Heals every living body to full | `Health.Heal` |
| Invulnerable hero | Nothing hurts the hero | The game's invincibility list, kept on whatever body the hero has |
| Invulnerable monster players | Nothing hurts the players' monsters | The same, on every monster player's body |
| Endless ectoplasm for ghosts | Ghosts stay at full ectoplasm | A top-up twice a second, as a pickup does, capped at the ghost's maximum |

### View

| Control | What it does |
| --- | --- |
| Game speed | x0.25, x0.5, x1 or x2, through the game's own debug time multiplier |
| Hitboxes (red) and hurtboxes (green) | Outlines every live attack's colliders in red and every body's hurtbox in green |
| Freeze monster AI and bots | Room monsters and bots stand still and stop attacking. Bosses keep going |
| Hide the HUD | Hides the game's HUD, as its own GUI hide does |

### Progress

| Control | What it does |
| --- | --- |
| Open everything for this session (nothing is saved) | Everything Crawl keeps locked, every Crawl: Further challenge and every secret reads as open until you switch it off or close the game. Nothing is written to the save or the config files |
| The game's open-everything item (writes your save) | Crawl's own version. This one is permanent |

### Secrets (Crawl: Further)

| Control | What it does |
| --- | --- |
| Every boss fight is a mod boss | Only when the mod bosses are switched on (`[Bosses] Enabled`) |
| Secret monster (become) | Become a secret statue monster, a silver unique or one of the gold secret line |
| Secret statue (place) | Puts a secret statue beside the hero, ready to take |

## The game's own debug menu

With test mode on, Crawl's debug mode is on from the start, so its menu is complete: hold Tab and press the key
under Escape (`). The game pauses and shows a text menu. Its items that change your save now
say so in their names, for example `Library 4. Clear Found Entries (erases your library)`. The floor items (Open Doors, Go To Boss, Skip to Lvl 10 and others) appear once a floor has started.

The game's debug keys also work. All are Tab plus a key:

| Keys | What they do |
| --- | --- |
| Tab + R / Tab + Shift + R | Reload the floor / end the floor |
| Tab + D | Open the doors |
| Tab + Shift + B | Go to the run's boss |
| Tab + H | Hide the game's GUI |
| Tab + L | Everyone +1 level and evolve |
| Tab + S | Go to the shop |
| Tab + X / Tab + G / Tab + F | Hero XP / gold / favour |
| Tab + T | The game's debug overlay |
| Tab + 1 to 4, Tab + 7 to 0 | Put the keyboard on player 1 to 4 / give player 1 to 4 to a bot |
| Tab + U | opens everything for good (writes your save) |
| Tab + V | Mark the whole vault found (writes your save) |
| Page Up / Page Down / End (with Tab) | Speed up / slow down / normal speed |

Two keys are blocked while test mode is on, because they wipe your progress: Tab + Delete (deletes every save)
and Tab + Shift + U (locks everything again).

## Adding your own actions

Any mod built on Core can add pages, or add to Core's pages, from its start callback. The example mod adds a
Glimmer page (`examples/ExampleGod/GlimmerTests.cs`):

```csharp
public static void Register()
{
    if (!TestMode.On) return;
    TestMode.AddList("Glimmer", "Become a Glimmer monster", Bodies,
        item => TestGame.Become(TestMode.Player, (GameObject)item.Value));
    TestMode.AddList("Glimmer", "Spawn a hostile Glimmer monster", Bodies,
        item => TestGame.SpawnHostile((GameObject)item.Value));
    TestMode.AddAction("Glimmer", "Give the hero Glimmer Volley", () =>
    {
        Powerup volley;
        if (!ItemRegistry.Items.TryGetValue(GlimmerItems.VolleyId, out volley)) throw new TestModeException("Glimmer Volley was not built");
        TestGame.GiveItem(volley);
        TestMode.Say("The hero has Glimmer Volley");
    });
}

static IEnumerable<TestItem> Bodies()
{
    foreach (var m in GlimmerPack.Monsters)
    {
        Player p;
        if (MonsterFactory.Built.TryGetValue(m.id, out p) && p != null) yield return new TestItem(m.id, p.gameObject);
    }
}
```

Check `TestMode.On` first so nothing is built when test mode is off. The calls are in `CrawlFurther.Testing`.

- `AddAction`, `AddToggle`, `AddNumber`, `AddChoice` and `AddList` take the page name first. A new name makes a
  new page, after Core's. Core's pages are Become, Spawn, Items, Run, Player, View and Progress.
- `AddAction(page, name, run)` is a button. `AddToggle(page, name, get, set)` is a switch that shows `get()`.
  `AddNumber(page, name, min, max, start, run)` is a number with - and + and a Go button. `AddChoice(page, name,
  options, get, set)` is a row of buttons with one lit. `AddList(page, name, items, pick)` is a picker whose entries
  are `TestItem(label, value, group)`, asked for again every two seconds while shown.
- `AddList` returns the list. Its `Selected` and `SelectedValue` are the last pick, so one list can show what
  another picked (Core's Monster list shows the tree of the god picked beside it).
- Throw `TestModeException` with a short reason when an action cannot run. The panel shows the reason. Any other
  exception shows as a failure and goes to the log with its stack trace.
- `TestMode.Say` puts a line at the top of the panel.
- `TestMode.Player` is the player the panel acts for.
- `TestMode.SwitchedOff` runs when an online match starts. Turn off anything lasting your actions switched on.
- `TestGame` has the calls Core's own actions use: `Become`, `BecomeGhost`, `BecomeHero`, `SetOrigin`,
  `SpawnHostile`, `RemoveTestBots`, `PlaceObject`, `GiveItem`, `GiveWeapon`, `SetGod`, `GoToFloor`, `NextFloor`,
  `GoToBoss`, `OpenDoors`, `ReloadLevel`, `NextRoom`, `GoToStore`, `GoToPortal`, `LevelUpAll`, `SkipToLevel10`,
  `SetHeroLevel`, `AddGold`, `FullHeal`, `BesideHero`, `Tree` and `AllMonsters`.
- `TestMode.Banner` is the line Crawl: Further puts in its load banner. Show it in yours if you have one.

While test mode is on, the self-test report (`CrawlMod_selftest.txt`) has a "test mode" section. It checks that
every game method the panel calls was found and patched.
