# Item FX timing (tools/sprites/item_fx.py)

Every sheet's json has `origin: [x, y]`: the cell pixel placed on the effect's spawn point (ItemArt.Place ->
Strike.ArtAt). Pixel coordinates below are relative to that origin, x right, y up NEGATIVE.
Durations copied from a monster sheet keep the replaced effect's clip length and damage events (listed as 'timing of').

## FxItemEmberVolley  (cell 22x18, origin 12,9)
Ember Volley flame bolt (DFX_skelMageNewProjectile box 11x10) + its wall/monster pop
- Fly: 4 frames, 0.24 s: 0.06, 0.06, 0.06, 0.06
- Pop: 5 frames, 0.33 s: 0.04, 0.05, 0.06, 0.08, 0.1

## FxItemWickBolt  (cell 22x18, origin 12,9)
Saint's Wick holy candle-flame bolt with a gold halo + pop
- Fly: 4 frames, 0.24 s: 0.06, 0.06, 0.06, 0.06
- Pop: 5 frames, 0.33 s: 0.04, 0.05, 0.06, 0.08, 0.1

## FxItemWickFire  (cell 26x18, origin 13,13)
Wickwalk burning wax drips (ground 20x7 at the origin)
- Life: 30 frames, 2.70 s: 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09
- Loop: 6 frames, 0.54 s: 0.09, 0.09, 0.09, 0.09, 0.09, 0.09

## FxItemVotive  (cell 28x18, origin 13,13)
Votive Candle spilled burning tallow + votive candles (ground 20x7)
- Life: 30 frames, 2.70 s: 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09
- Loop: 6 frames, 0.54 s: 0.09, 0.09, 0.09, 0.09, 0.09, 0.09

## FxItemWaxFire  (cell 28x18, origin 13,13)
Wax Slick set alight (hero wax ignition; ground 20x7)
- Life: 30 frames, 2.70 s: 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09
- Loop: 6 frames, 0.54 s: 0.09, 0.09, 0.09, 0.09, 0.09, 0.09

## FxItemWickRunner  (cell 16x16, origin 8,13)
Wickwalk runner
- Run: 4 frames, 0.24 s: 0.06, 0.06, 0.06, 0.06

## FxItemWaxRunner  (cell 16x16, origin 8,13)
Wax Slick runner
- Run: 4 frames, 0.24 s: 0.06, 0.06, 0.06, 0.06

## FxItemThornRunner  (cell 16x16, origin 8,13)
Thornwall sower
- Run: 4 frames, 0.24 s: 0.06, 0.06, 0.06, 0.06

## FxItemRootRunner  (cell 18x16, origin 9,13)
Root Snare burrower
- Run: 4 frames, 0.24 s: 0.06, 0.06, 0.06, 0.06

## FxItemWaxSlick  (cell 26x10, origin 13,5)
Wax Slick puddle (status zone 22x8)
- Life: 25 frames, 5.96 s: 0.05, 0.05, 0.05, 0.05, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.12, 0.12, 0.12
- Idle: 2 frames, 0.60 s: 0.3, 0.3

## FxItemUndertowBrine  (cell 28x10, origin 14,5)
Undertow brine left by the wave (zone 23x8)
- Life: 26 frames, 8.36 s: 0.12, 0.12, 0.12, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.2, 0.2, 0.2

## FxItemRiptidePool  (cell 28x10, origin 14,5)
Riptide Dash whirlpool left where you started (zone 23x8)
- Life: 26 frames, 8.36 s: 0.12, 0.12, 0.12, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.37, 0.2, 0.2, 0.2

## FxItemAcidPool  (cell 26x12, origin 13,7)
Acid Spit pool (ground 22x10)
- Life: 18 frames, 3.09 s: 0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.13, 0.13, 0.13

## FxItemThornwall  (cell 26x14, origin 12,10)
Thornwall bramble patch (ground 18x7)
- Life: 24 frames, 7.95 s: 0.1, 0.1, 0.1, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.15, 0.15, 0.15

## FxItemThornMail  (cell 26x14, origin 12,10)
Thorn Mail iron thorns bursting from the floor (ground 18x7)
- Life: 24 frames, 7.95 s: 0.1, 0.1, 0.1, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.15, 0.15, 0.15

## FxItemGraveSpear  (cell 36x16, origin 21,8)
Grave Call bone spear (box 11x10, pierces) + bone-chip impact
- Fly: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05
- Pop: 4 frames, 0.25 s: 0.04, 0.05, 0.07, 0.09

## FxItemBoneBoomerang  (cell 18x18, origin 9,9)
Bone Boomerang spinning skull, 8 frames like the vanilla boomerang (capsule 13x8)
- Fly: 8 frames, 0.32 s: 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04
- Pop: 4 frames, 0.25 s: 0.04, 0.05, 0.07, 0.09

## FxItemMarrowSpikes  (cell 58x36, origin 29,23)
Marrow Spikes ring (ground 52x21 at the origin)
- Play: 4 frames, 0.28 s: 0.05, 0.06, 0.07, 0.1

## FxItemMarrowPlate  (cell 28x22, origin 14,20)
Marrow Flask bone plates (hero version)
- Orbit1: 6 frames, 0.60 s: 0.1, 0.1, 0.1, 0.1, 0.1, 0.1
- Orbit2: 6 frames, 0.60 s: 0.1, 0.1, 0.1, 0.1, 0.1, 0.1
- Break: 4 frames, 0.29 s: 0.05, 0.06, 0.08, 0.1

## FxItemJokerShield  (cell 30x24, origin 14,20)
Joker's Wild 'Diamonds' card shield (hero version)
- Orbit1: 6 frames, 0.60 s: 0.1, 0.1, 0.1, 0.1, 0.1, 0.1
- Orbit2: 6 frames, 0.60 s: 0.1, 0.1, 0.1, 0.1, 0.1, 0.1
- Break: 4 frames, 0.29 s: 0.05, 0.06, 0.08, 0.1

## FxItemSporePod  (cell 18x21, origin 10,17)
Spore Bomb pod: rides 10 px above the webBall's floor point
- Fly: 4 frames, 0.32 s: 0.08, 0.08, 0.08, 0.08

## FxItemSporeBurst  (cell 34x22, origin 17,15)
Spore Bomb poison burst (ground 26x12 at the origin)
- Burst: 5 frames, 0.43 s: 0.06, 0.06, 0.07, 0.1, 0.14

## FxItemRootSnare  (cell 24x16, origin 11,12)
Root Snare root grab, laid along the burrower's path (ground 20x8)
- Play: 7 frames, 0.58 s: 0.06, 0.05, 0.05, 0.12, 0.12, 0.08, 0.1

## FxItemMaggots  (cell 20x20, origin 10,9)
Rotting Apple seeking maggot swarm (capsule 9x13) + bite pop
- Fly: 4 frames, 0.32 s: 0.08, 0.08, 0.08, 0.08
- Pop: 4 frames, 0.29 s: 0.05, 0.06, 0.08, 0.1

## FxItemNovaShard  (cell 22x16, origin 12,8)
Shard Nova star-glass shard (box 11x10) + shatter pop
- Fly: 4 frames, 0.24 s: 0.06, 0.06, 0.06, 0.06
- Pop: 4 frames, 0.25 s: 0.04, 0.05, 0.07, 0.09

## FxItemMirrorShatter  (cell 32x26, origin 16,20)
Mirror Step pane shatter (ground 22x12 at the feet)
- Shatter: 5 frames, 0.35 s: 0.04, 0.06, 0.07, 0.08, 0.1

## FxItemMirrorBlur  (cell 32x10, origin 16,5)
Mirror Step dash streak (replaces the vanilla DashBlur)
- Play: 4 frames, 0.37 s: 0.067, 0.1, 0.1, 0.1

## FxItemMirrorGlint  (cell 8x8, origin 4,4)
Mirror Step glints dropped along the dash
- Play: 5 frames, 0.60 s: 0.1, 0.1, 0.2, 0.1, 0.1

## FxItemShadowSwap  (cell 30x30, origin 15,25)
Shadow Swap vortex at both ends of the swap + cast sigil
- Flash: 5 frames, 0.33 s: 0.04, 0.05, 0.06, 0.08, 0.1
- Cast: 3 frames, 0.19 s: 0.05, 0.06, 0.08

## FxItemShadowEcho  (cell 22x22, origin 11,20)
Hollow Crown shadow echo (replaces the violet-tinted hero afterimage)
- Echo: 4 frames, 0.44 s: 0.08, 0.1, 0.12, 0.14

## FxItemSoulLantern  (cell 16x16, origin 8,8)
Soul Lantern swinging soul-flame lantern (capsule 15x10)
- Fly: 4 frames, 0.32 s: 0.08, 0.08, 0.08, 0.08

## FxItemSoulBurst  (cell 48x36, origin 24,12)
Soul Lantern burst (skydropExplode capsule 41x22, centred 6 px under the origin), 11 frames like the vanilla burst
- Burst: 11 frames, 1.20 s: 0.067, 0.067, 0.1, 0.1, 0.133, 0.133, 0.133, 0.167, 0.1, 0.1, 0.1

## FxItemBellToll  (cell 58x28, origin 29,15)
Bell Toll bronze sound ring (ground 50x20)
- Ring: 5 frames, 0.36 s: 0.05, 0.06, 0.07, 0.08, 0.1

## FxItemTideBurst  (cell 62x34, origin 31,18)
Tidecaller Conch wave burst (ground 56x24)
- Ring: 6 frames, 0.48 s: 0.05, 0.06, 0.07, 0.08, 0.1, 0.12

## FxItemUndertowWave  (cell 32x22, origin 17,11)
Undertow wave (box 18x22, pierces) + splash
- Fly: 4 frames, 0.32 s: 0.08, 0.08, 0.08, 0.08
- Pop: 4 frames, 0.25 s: 0.04, 0.05, 0.07, 0.09

## FxItemRiptideBlur  (cell 32x10, origin 16,5)
Riptide Dash water streak (replaces the vanilla DashBlur)
- Play: 4 frames, 0.37 s: 0.067, 0.1, 0.1, 0.1

## FxItemRiptideDrop  (cell 8x8, origin 4,4)
Riptide Dash droplets dropped along the dash
- Play: 5 frames, 0.60 s: 0.1, 0.1, 0.2, 0.1, 0.1

## FxItemWildCard  (cell 18x14, origin 9,7)
Wild Card spinning card; FlyFire/Poison/Frost/Daze wear the drawn curse
- Fly: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05
- FlyFire: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05
- FlyPoison: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05
- FlyFrost: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05
- FlyDaze: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05

## FxItemWildCurse  (cell 20x24, origin 10,22)
Wild Card curse landing on the monster (one per curse)
- CurseFire: 5 frames, 0.41 s: 0.05, 0.06, 0.08, 0.1, 0.12
- CursePoison: 5 frames, 0.41 s: 0.05, 0.06, 0.08, 0.1, 0.12
- CurseFrost: 5 frames, 0.41 s: 0.05, 0.06, 0.08, 0.1, 0.12
- CurseDaze: 5 frames, 0.41 s: 0.05, 0.06, 0.08, 0.1, 0.12

## FxItemLoadedDie  (cell 22x18, origin 11,9)
Loaded Dice tumbling die (box 15x13)
- Fly: 4 frames, 0.24 s: 0.06, 0.06, 0.06, 0.06

## FxItemDieRoll  (cell 18x24, origin 8,23)
Loaded Dice: the rolled face (1-6 pips) pops over the monster it hit
- Roll1: 4 frames, 0.47 s: 0.05, 0.12, 0.2, 0.1
- Roll2: 4 frames, 0.47 s: 0.05, 0.12, 0.2, 0.1
- Roll3: 4 frames, 0.47 s: 0.05, 0.12, 0.2, 0.1
- Roll4: 4 frames, 0.47 s: 0.05, 0.12, 0.2, 0.1
- Roll5: 4 frames, 0.47 s: 0.05, 0.12, 0.2, 0.1
- Roll6: 4 frames, 0.47 s: 0.05, 0.12, 0.2, 0.1

## FxItemPuppetString  (cell 28x10, origin 14,5)
Puppet Strings piercing thread (box 11x10) + snap
- Fly: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05
- Pop: 4 frames, 0.25 s: 0.04, 0.05, 0.07, 0.09

## FxItemLuckyDie  (cell 22x36, origin 11,35)
Lucky Die: a green-pipped six flips over the hero as the hit misses
- Dodge: 5 frames, 0.51 s: 0.05, 0.06, 0.18, 0.12, 0.1

## FxItemJesterCrit  (cell 24x27, origin 12,25)
Jester's Bell: the bell rings on every 6th (double damage) hit
- Crit: 5 frames, 0.42 s: 0.05, 0.07, 0.08, 0.1, 0.12

## FxItemJokerFlip  (cell 14x27, origin 7,26)
Joker's Wild flip card and its four suit reveals
- Flip: 8 frames, 0.74 s: 0.06, 0.05, 0.05, 0.06, 0.12, 0.14, 0.14, 0.12
- Hearts: 1 frames, 0.90 s: 0.9
- Diamonds: 1 frames, 0.90 s: 0.9
- Spades: 1 frames, 0.90 s: 0.9
- Clubs: 1 frames, 0.90 s: 0.9

## FxItemMarionetteTug  (cell 16x30, origin 8,29)
Marionette Cross: strings jerk the monster that hit you (shown with its daze)
- Tug: 4 frames, 0.40 s: 0.06, 0.1, 0.12, 0.12

## FxItemAcidSpit  (cell 24x22, origin 12,17)
Acid Spit glob (webBall: floor point, drawn 10 px up); it lands as FxItemAcidPool
- Fly: 4 frames, 0.32 s: 0.08, 0.08, 0.08, 0.08

## FxItemHiveAmber  (cell 38x23, origin 19,15)
Hive Amber resin ring (ground 32x14) + honeycomb pop at the hero
- Burst: 5 frames, 0.39 s: 0.05, 0.06, 0.07, 0.09, 0.12
- Pop: 5 frames, 0.39 s: 0.05, 0.06, 0.07, 0.09, 0.12

## FxItemChainSpark  (cell 22x18, origin 11,9)
Chain Spark spark (box 11x10) + jump / hit flash
- Fly: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05
- Hit: 4 frames, 0.23 s: 0.04, 0.05, 0.06, 0.08

## FxItemRodBall  (cell 24x24, origin 12,12)
Lightning Rod ball lightning (box 11x10) + burst
- Fly: 4 frames, 0.28 s: 0.07, 0.07, 0.07, 0.07
- Pop: 5 frames, 0.33 s: 0.04, 0.05, 0.06, 0.08, 0.1

## FxItemIcicle  (cell 24x64, origin 12,59)
Icicle Requiem: crowned icicle falls on its telegraph (0.7 s), shatters (ground 18x10)
- Fall: 8 frames, 0.70 s: 0.12, 0.1, 0.1, 0.1, 0.08, 0.08, 0.06, 0.06
- Shatter: 5 frames, 0.36 s: 0.05, 0.06, 0.07, 0.08, 0.1

## FxItemShawl  (cell 54x26, origin 27,15)
Widow's Shawl frost-silk web (ground 48x20) + silk puff at the hero
- Nova: 6 frames, 0.40 s: 0.04, 0.05, 0.06, 0.07, 0.08, 0.1
- Puff: 4 frames, 0.23 s: 0.04, 0.05, 0.06, 0.08

## FxItemEmberHeart  (cell 16x16, origin 8,9)
Ember Heart ignite flare
- Proc: 4 frames, 0.28 s: 0.04, 0.06, 0.08, 0.1

## FxItemVenomGland  (cell 16x16, origin 8,8)
Venom Gland poison splash
- Proc: 4 frames, 0.28 s: 0.04, 0.06, 0.08, 0.1

## FxItemRimeRing  (cell 16x16, origin 8,8)
Rime Ring freeze snap
- Proc: 4 frames, 0.28 s: 0.04, 0.06, 0.08, 0.1

## FxItemLeechSeed  (cell 16x27, origin 8,25)
Leech Seed: the kill's life drawn into you
- Heal: 5 frames, 0.45 s: 0.05, 0.07, 0.09, 0.11, 0.13

## FxItemBrineFlask  (cell 16x28, origin 8,27)
Brine Flask regen bubbles
- Regen: 5 frames, 0.50 s: 0.06, 0.08, 0.1, 0.12, 0.14

## FxItemBarnacle  (cell 22x15, origin 11,13)
Barnacle Shell crust while you stand still (35% less damage)
- On: 3 frames, 0.20 s: 0.06, 0.06, 0.08
- Loop: 4 frames, 0.80 s: 0.2, 0.2, 0.2, 0.2

## FxItemHourglass  (cell 16x34, origin 8,33)
Hourglass of Ash: the glass turns as you cast (spells recharge faster)
- Proc: 5 frames, 0.38 s: 0.06, 0.06, 0.06, 0.08, 0.12

## FxItemGlassMask  (cell 18x32, origin 8,31)
Glass Mask: the mask cracks when a hit gets through (you take 35% more)
- Crack: 4 frames, 0.33 s: 0.05, 0.08, 0.1, 0.1

## FxItemTokenApple  (cell 16x18, origin 8,17)
Rotting Apple follower
- Idle: 12 frames, 1.40 s: 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117
- Ready: 2 frames, 0.20 s: 0.1, 0.1
- Activate: 10 frames, 0.96 s: 0.1, 0.067, 0.067, 0.067, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12
- Wait: 6 frames, 1.00 s: 0.167, 0.167, 0.167, 0.167, 0.167, 0.167
- WakeUp: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05

## FxItemTokenWick  (cell 16x19, origin 8,18)
Saint's Wick follower
- Idle: 12 frames, 1.40 s: 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117
- Ready: 2 frames, 0.20 s: 0.1, 0.1
- Activate: 10 frames, 0.96 s: 0.1, 0.067, 0.067, 0.067, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12
- Wait: 6 frames, 1.00 s: 0.167, 0.167, 0.167, 0.167, 0.167, 0.167
- WakeUp: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05

## FxItemTokenRod  (cell 16x18, origin 8,17)
Lightning Rod follower
- Idle: 12 frames, 1.40 s: 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117
- Ready: 2 frames, 0.20 s: 0.1, 0.1
- Activate: 10 frames, 0.96 s: 0.1, 0.067, 0.067, 0.067, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12
- Wait: 6 frames, 1.00 s: 0.167, 0.167, 0.167, 0.167, 0.167, 0.167
- WakeUp: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05

## Sync points used by the code

- FxItemWickFire / FxItemVotive / FxItemWaxFire Life: damage on frame 0, off 3 frames from the end (the 6-frame loop x5 of the
  burning pool, 2.7 s).
- FxItemWaxSlick Life: slow zone live from frame 2 to 3 frames from the end (FxWaxPuddle timing, 5.96 s).
- FxItemThornwall / FxItemThornMail Life: damage frames 3..21 (FxThornPatch timing, 7.95 s).
- FxItemUndertowBrine / FxItemRiptidePool Life: zone live from frame 1 to 3 from the end (FxBrine timing, 8.36 s).
- FxItemAcidPool Life: damage frames 2..15 (FxZhkAcidPool timing).
- FxItemMarrowSpikes Play: damage frames 0..3; FxItemBellToll Ring 0..3; FxItemTideBurst Ring 0..3; FxItemHiveAmber Burst 1..3;
  FxItemShawl Nova 0..4; FxItemMirrorShatter 1..3; FxItemSporeBurst 1..4; FxItemRootSnare 3..5; FxItemIcicle Shatter 0..2.
- FxItemSoulBurst Burst: the vanilla skydropExplode events (damage on 0.12 s, off 0.37 s): same 11 frame times.
- FxItemIcicle Fall: 0.7 s telegraph, then Shatter spawns on the same spot.
- Tokens: Activate fires the shot (AnimAttack 0 + AnimFlash) at the start of frame 3 (the brightest frame).
- Runner sheets ride the HeroSlimeDropper / WebDropper runner (anchor: feet at the origin).
