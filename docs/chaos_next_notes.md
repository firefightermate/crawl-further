# Next chaos update: player text kept for its release

These lines were in the 1.4.5 test build's notes. 1.4.6 shipped without the chaos work (compiled out with
CHAOS_NEXT, see build.sh), so they go back into the notes when the chaos update ships.

## Changelog lines

- Chaos floors are built mostly from big rooms: wider, deeper copies of the game's own rooms, grown out of their own
  floor and walls, with more enemies and props to fill them. Every room still fits on one screen.
- Rot Gardens, the first chaos floor of its own: caves overgrown with fungus, plum stone and glowing caps. Puffballs
  and bell caps burst at a hit into spores that daze the hero, and spore drifts cross the room during fights.
- A chaos game starts every monster player on tier 2 monsters. The hero levels faster, monster players earn wrath
  faster, and gold comes in a little quicker.
- Test mode (F2) has a Chaos page: turn chaos on, pick how many big rooms a floor gets, reload the floor built
  around any big room to look at it, and go straight to Rot Gardens.

## README.txt, CHAOS section

  Big rooms: most rooms on a chaos floor are wider, deeper copies of the game's own rooms, grown out of
  their own floor and walls, with more enemies and props. Each still fits on one screen; a room that can't
  grow cleanly keeps its own size. ChaosBigRooms under [Game] turns them off.
  Rot Gardens: now and then a stretch of chaos floors is overgrown caves instead of one of the game's
  floors. Puffballs and bell caps burst at a hit from anyone (hero or monster) into a spore cloud that dazes
  the hero, and while a fight is on, spore drifts float across the room. ChaosBiomes under [Game] turns
  them off.
  Pace: monster players start on tier 2 monsters, the hero levels faster, wrath comes faster and gold a
  little quicker. A continued game picks up the faster pace from the continue on.

## thunderstore/README.md, Keep playing and Chaos

...is a chaos game: the hero holds two spells, floors are mostly big rooms, and some stretches are Rot Gardens,
overgrown caves full of bursting spores.
