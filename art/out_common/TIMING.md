# out_common: CORE-FX shared effects (tools/sprites/common_fx.py)

Coordinates are pixels relative to the anchor, x right, y up NEGATIVE.

## Status overlays (src/Core/ModStatus.cs)

The anchor is each cell's bottom-centre. StatusOverlays (a component on the afflicted) moves the overlay with the victim
every LateUpdate, from the moment the status lands until it is removed. That covers the timer running out, the CC window
closing, death, despawn and destruction. The overlay sorts just in front of the victim (z - 0.04 for feet, z - 0.06 for
head). The "Big" anims are used when the victim is at least 22 px wide or 34 px tall, measured from its hurtbox and its
art. Bosses at least 56 px wide or 64 px tall get x2.

| sheet | cell | anchor | anims | durations (s) | notes |
|---|---|---|---|---|---|
| FxCommonStatusSlow | 32 x 16 | (16, 15) | Loop 6, LoopBig 6 | 0.1 each (0.6 s loop) | The feet line is row 13, two rows above the bottom, so the code offset is -2. An ochre-olive tar pool, about 17 x 5 (Big 27 x 7), sits in front of the feet. Tar strands cling to the shins, drips fall from about 7 px (Big 10 px) above the feet into the pool, and bubbles swell and pop. |
| FxCommonStatusRoot | 32 x 20 | (16, 19) | Grip 3 then Loop 4; GripBig 3 then LoopBig 4 | Grip 0.05 0.06 0.07; Loop 0.12 each | Feet line on row 17 (offset -2). Grip: bark tendrils tear up through a cracked floor ring and coil round the ankles, with earth chips thrown up. Loop: the coil squirms, a quarter turn each frame, and a leaf bud opens and closes. The clip is Grip + Loop with an AnimLoopStart event on the first Loop frame, so the Effect replays only the loop. About 18 x 9 (Big 26 x 12). |
| FxCommonStatusDaze | 24 x 10 | (12, 10) | Loop 4, LoopBig 4 | 0.11 each | Bottom row = the art's bottom. The code places it 1 px above the victim's head top. Two violet birds and two gold stars ride a tilted orbit, rx 5 / ry 1.8 (Big 8 / 2.8). Each frame turns the orbit 45 degrees and the back half is drawn dimmer. About 13 x 6 (Big 21 x 9); vanilla FXDizzyStars is 7 x 4. |

Registered by ModStatus itself:
- ModStatusSlow: Feet, -2.
- ModStatusRoot: Feet, -2, intro Grip.
- ModStatusDaze: Head, +1.

Other packs register their own overlays with `ModStatus.RegisterOverlay(statusName, sheet, anim, offsetY)` (offsetY in px
above the feet; 12 or more is lifted to clear the head) or with the overload that takes `OverlayAt.Head/Feet` and an
optional intro anim.

## Impact puffs (src/Core/ImpactFx.cs)

Each puff has a 24 x 24 cell with the impact point at the cell centre (12, 12); the code anchors it MidCenter.

The game plays each puff as a clone of the vanilla contact it replaces, which keeps that contact's sound and depth.
- Wall: sits 3 px off the wall, toward the shooter, and has a depth offset of -4.
- Hit: has a depth offset of -22, so it sorts in front of the victim.
- Neither rotates. Both flip with the contact direction.

| anim | frames | durations (s) | timeline |
|---|---|---|---|
| Wall | 5 | 0.05 0.05 0.083 0.083 0.083 (vanilla ContactGenericSmall) | f0 streak flash (about 13 px) in the god's colours; f1 small flash plus the first burst; f2-f4 the god's debris thins and dims, reaching about 16-20 px. |
| Hit | 5 | 0.05 0.06 0.07 0.08 0.09 (0.35 s; vanilla ArcadeyHitEffect2halfsize is 4 x 0.1) | f0 big flash (arms 8, about 17 px), f1 afterglow plus burst, f2-f4 debris out to about 20-23 px. |

| sheet | god | motif |
|---|---|---|
| FxCommonImpactVh | Vhorrul | A candle-flame flash, then a cream wax splat with drips running down, flying wax droplets carrying flame licks, and soot specks. |
| FxCommonImpactBel | Bel'Mora | A teal flash, then a brine crown splash that collapses into a ripple ring; foam droplets fall under gravity. |
| FxCommonImpactOss | Ossivar | An ivory flash, then tumbling bone chips with dark undersides, a fleck of marrow red and grey dust. Hit adds crack fissures. |
| FxCommonImpactSyl | Sylvene | A green flash, then a spore puff with thinning, dithered edges; pollen, pink and violet spores drift upward. |
| FxCommonImpactUmb | Umbrael | A violet flash, then a dark rift opens and snaps shut while lilac-rimmed shadow shards fly outward. |
| FxCommonImpactJinx | Jinx | A gold flash, then confetti in red, gold, cyan, magenta, green and cream. The pieces flip as they fall. |
| FxCommonImpactZhk | Zhekra | An acid flash, then a green splat whose bubbles swell and pop into rising fizz. |
| FxCommonImpactKrn | Kaurn | A blue-white flash, then jagged electric arcs, with forge-orange embers trailing under gravity. |
| FxCommonImpactYsv | Ysveld | A white-cyan flash, then pale ice chips (diamond shapes) and a dotted frost ring. |
| FxCommonImpactMod | neutral | A white flash, then a pale dust ring with the mod's violet glint. This is the fallback for any sheet that maps to no god. |
| FxCommonImpactWpn | hero weapons | A steel-white flash, then metallic sparks (white, yellow, orange streaks) and steel flecks. |

## Floating roll numbers (src/Core/FloatNumber.cs, tools/sprites/float_digits.py)

| sheet | cell | anims |
|---|---|---|
| FxCommonDigits | 12 x 16 | one single-frame anim per tone and glyph: `<Tone><Glyph>`, tones Normal / Max / Min / Flash, glyphs 0-9 D O G E (56 cells) |

The glyphs are Crawl's own CrawlBitmapLarge font (8 x 10 digits, 3 px strokes) with a 1 px dark outline and a 1 px drop
shadow. Inside a cell the body sits on rows 2-11, the outline on rows 1-12 and the shadow on row 13. The code anchors the
cells BotLeft at local y -2, so the number's visible bottom is its origin. Neighbouring glyphs overlap by 1 px, so the
outlines merge. Glyph widths are measured from the texture at run time. Tones: Normal is cream, Max is gold with a brown
outline (the top face of the die), Min is a dull grey-red (a 1), and Flash is white-hot.

Timeline (0.8 s, pooled, z -30, whole pixels):
- 0.00-0.08 s: Flash tone. A gold max roll of one or two glyphs is also drawn at x2 for 0.00-0.04 s.
- 0.00-0.14 s: rises 9 px, easing out.
- 0.14-0.24 s: drops back to 6 px.
- 0.24-0.80 s: drifts up to 24 px.
- 0.55-0.80 s: alpha fades from 1 to 0.

If a number spawns within 16 x 12 px of one that is younger than 0.55 s, it is moved sideways by +15, -15, +30 and so on,
and 4 px up.

Where each roll shows:
- Loaded Dice: the pips, 12 px right of and 11 px above the hit point, beside the die face (FxItemDieRoll) that pops there.
- Snake-Eyes weapon: each blow's d6, 2 px above every monster it lands on.
- Dice Imp toss and Snake-Eyes Craps dice: the pips, 2 px above the hero's head when they hit.
- Lucky Die: a gold DODGE 35 px above the hero's feet, just over the flipped die.

## Effect indicators (src/Core/ModStatus.cs `ModInd`, tools/sprites/common_fx.py `build_indicators`)

Indicators are for effects that are not statuses: stacks, charges, timed buffs, regeneration and heals. They use the
same `StatusOverlays` machinery as the status overlays. That machinery follows the character, picks the Big anim for
large bodies (x2 for bosses), stacks head icons upward with the status overlays, and cleans up on hide, timer, death,
despawn and pooling. Every cell's anchor is its bottom-centre.

| sheet | cell | anims | durations (s) | placement | used for |
|---|---|---|---|---|---|
| FxCommonIndRime | 24 x 9 | One 4, Two 4 | 0.12 each | Head +1 | Ysveld Rime on the hero: a 3-slot ice meter. Filled crystals glint. On Two, the third (bind) slot pulses. |
| FxCommonIndCharge | 24 x 9 | One 4, Two 4, Three 4 | 0.08 each | Head +1 | Kaurn static pips: a 3-slot bolt meter. Bolts flicker, with arcs between them. |
| FxCommonIndPlates | 24 x 9 | One 4, Two 4, Three 4 | 0.14 each | Head +1 | Plate count (one steel shield per plate, a glint sweeping across). Shown when the holder can carry more than one plate. |
| FxCommonIndMight | 16 x 11 | Loop 4 | 0.1 each | Head +1 | Damage up: a red-orange double chevron that pulses upward, with embers (Joker's Wild Spades, 4 s). |
| FxCommonIndRegen | 36 x 38 | Loop 6, LoopBig 6 | 0.1 each | Feet -2 | Regenerating: a green ring breathes at the feet and crosses climb the flanks (brine / wax / resin regen, only while hurt). |
| FxCommonIndHeal | 36 x 38 | Play 6, PlayBig 6 (one-shot) | 0.05 0.06 0.07 0.08 0.09 0.1 | Feet -2 | Any instant heal: a white-green ring flash, then crosses burst up and out. |
| FxCommonIndHaste | 32 x 18 | Loop 4, LoopBig 4 | 0.07 each | Feet -2 | Move speed up: a wind ring with a bright arc chasing round the ankles, speed lines peeling off both sides, and dust at the heels. |
| FxCommonIndIce | 32 x 14 | Loop 4, LoopBig 4 | 0.11 each | Feet -2 | On Ysveld ice (the hero slides; Ysveld monsters skate faster): a glassy skid under the feet, glints and frost chips. |

Feet line: row cellH-3 for the feet overlays (code offset -2). Head counters put the art's bottom on the cell's bottom
row. Statuses that got overlays in this pass are ModStatusZhkSwarm (FxZhkSwarm, Head +1) and ModStatusZhkMark
(FxZhkMark, Head +1). Before this pass they were hand-parented children at fixed heights.

`ModAttach` (Behaviours.cs) keeps a visual sorted just in front of a character. DepthHandler sorts an effect by its own
height, so a mark at chest height used to land behind the body and be hidden by it. The visuals that now use it:
- plate orbits
- weapon follow-marks (rift, chill, kunai, plague, guard ring, lance ready)
- Kaurn crackles
- the Jinx surge aura, which also follows the feet
