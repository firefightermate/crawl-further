# Ghost form art: cells, origins, event frames (tools/sprites/ghost_v11.py, ghost_forms_v11.py, ghost_custom.py)

## Fodder (final size, no ArtScale; kit offsets in GhostV11.cs are px above the feet). Spawn 5 = vanilla slime timing, AnimAttack 3 = own ring
| Sheet | Form | Attack | Special |
|---|---|---|---|
| FodKeener | Banshee | Shriek 6, release 3 (FxShriek from the mouth (5, 8)) | - |
| FodRevenant | Sexton | Claw 6, hit 3 | - |
| FodFusebelly | Kindler | Lick 5, hit 2 | Blow 7: FxFuseBlast + AnimModBlowUp on 5 (it dies) |
| FodGargling | Mason | Spit 6, release 3 (stone from the maw (7, 11)) | Fan 7, release 4 (3 stones, 18 deg apart) |
| FodPoppet | Hexer | Jab 6, hit 3 (Hexed 35 percent) | - |
| FodMimic | Miser | Chomp 6, hit 3 | Spit 6, release 3 (3 coins, 14 deg apart) |

## Ghost bodies (54 x 50, the vanilla ghost cell; Spawn 10 x 0.1 s, Idle 6 x 0.2 s, Run 6 x 0.1 s)
FormBanshee Wail 6 (AnimModGhostAbility on 3), FormKindler Ignite 6 (ability on 3), FormMason Rouse 6 (ability on 3),
FormHexer Throw 6 (pin released on 3 at offset (12, -1), the Poltergeist's hand), FormSexton and FormMiser: no attack.

## FX origins (cell pixel placed on the spawn point, Strike.ArtAt / RingPair)
FxWailRing (40, 22) | FxShriek, FxStoneShard, FxHexPin, FxCoinShot: centred | FxFuseBlast Play/Pop: floor centre (36, 46)
FxGrave (11, 18) Rise 4, Idle 6, Glow 6, Sink 4 | rings FxKeenerRise FxGraveRaise FxWaxRing FxRubbleRing FxStuffingRing FxCoinRing (20, 15)
FxHoardBurst (38, 36) | FxHauntLatch (20, 14) | FxSoulLeap Fly (16, 6) | FxSoulLand (22, 16) | FxTithe (15, 26)
Overlays: FxHexMark Loop (Hexed, head), FxHaunted Loop (Haunted, head), FxHoardAura (Miser ghost 2+ bodies; Mimic feet).
Auras on the ghost: FxSilverAura, FxGoldAura, FxHoardAura.

## Custom ghosts
CustomGhostBody: <Shape>Spawn/Idle/Run (Hag, Hood, Sheet, Horned) in key colours, markers (14,0,0) eyes, (15,0,0) tail.
CustomGhostEyes 11 x 7 origin (5, 3); CustomGhostTrails 30 x 28 origin (18, 12); CustomGhostFrames Silver 4 / Gold 4 (29 x 24).
Portrait window = body cell x 13..41, y 17..40. GhostSilver / GhostGold = default-look portraits.

## Silver / gold (GhostSlots.cs)
Removed: Haunt, Soul Leap, Tithe, Phase Step, Soulstorm and the thrall gold bolt (code and art).
SILVER Ascension: FxSilverOrb Idle 6 / Collect 5 (24 x 22, origin (12, 18) = the orb's spot on the floor) |
FxSoulWisp Orbit 4 / Bright 4 (the orb tally circling the ghost; Bright = 8 banked) | FxAscendFlash Play 10
(70 x 76, origin (35, 64) at the body's feet) | FxAscendAura Loop (feet overlay) | FxAscendSpark Play 5 (14, 12).
GOLD Thralls: FxThrallJump Play 7 (17, 30) | FxThrallLocked Play 6 (12, 20) | FxThrallBurst Play 7 (20, 24) |
overlays FxThrallMark Loop (head), FxThrallSigil Loop (feet), FxThrallCount One (the gold player's head).
Tints (exSprite vertex colour, so hit flashes still show): thrall gold (1, 0.86, 0.5), ascended silver (0.72, 0.82, 1).
