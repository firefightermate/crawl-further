# Items wave 3 world art (tools/sprites/items3_fx.py)

Origin = the cell pixel ItemArt.Place puts on the spawn point. Feet pops spawn at the hero's feet; hit sparks at the body's aim point.

## FxItem3Quaff  (cell 32x40, origin 16,38)
A potion is drunk: its brew bubbles up round the hero (spawned at the feet).
- Marrow: 8 frames, 0.61 s: 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.09, 0.1
- Wyrm: 8 frames, 0.61 s: 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.09, 0.1
- Hare: 8 frames, 0.61 s: 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.09, 0.1
- Grog: 8 frames, 0.61 s: 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.09, 0.1
- Stone: 8 frames, 0.61 s: 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.09, 0.1
- Quick: 8 frames, 0.61 s: 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.09, 0.1
- Chaos: 8 frames, 0.61 s: 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.09, 0.1
- Heart: 8 frames, 0.61 s: 0.06, 0.06, 0.07, 0.07, 0.08, 0.08, 0.09, 0.1

## FxItem3ChaosRoll  (cell 36x48, origin 18,46)
Chaos Brew: which stat went up 2 (green arrow) and which down 1 (red), over the head (art 14-26 px above the feet).
- VS: 7 frames, 1.22 s: 0.06, 0.06, 0.1, 0.3, 0.4, 0.15, 0.15
- VD: 7 frames, 1.22 s: 0.06, 0.06, 0.1, 0.3, 0.4, 0.15, 0.15
- SV: 7 frames, 1.22 s: 0.06, 0.06, 0.1, 0.3, 0.4, 0.15, 0.15
- SD: 7 frames, 1.22 s: 0.06, 0.06, 0.1, 0.3, 0.4, 0.15, 0.15
- DV: 7 frames, 1.22 s: 0.06, 0.06, 0.1, 0.3, 0.4, 0.15, 0.15
- DS: 7 frames, 1.22 s: 0.06, 0.06, 0.1, 0.3, 0.4, 0.15, 0.15

## FxItem3Tally  (cell 20x44, origin 10,42)
Tally Stick: a new notch is carved (over the head).
- One: 7 frames, 1.01 s: 0.06, 0.06, 0.1, 0.25, 0.3, 0.12, 0.12
- Two: 7 frames, 1.01 s: 0.06, 0.06, 0.1, 0.25, 0.3, 0.12, 0.12
- Three: 7 frames, 1.01 s: 0.06, 0.06, 0.1, 0.25, 0.3, 0.12, 0.12
- Four: 7 frames, 1.01 s: 0.06, 0.06, 0.1, 0.25, 0.3, 0.12, 0.12
- Five: 7 frames, 1.01 s: 0.06, 0.06, 0.1, 0.25, 0.3, 0.12, 0.12

## FxItem3Confetti  (cell 40x40, origin 20,24)
Party Hat: confetti from the killed monster's body.
- Burst: 10 frames, 0.79 s: 0.04, 0.05, 0.06, 0.07, 0.08, 0.08, 0.09, 0.1, 0.1, 0.12

## FxItem3PartyHat  (cell 12x12)
Party Hat worn: head overlay (offset -3: the brim sits 3 px into the head).
- Hat: 4 frames, 0.90 s: 0.3, 0.15, 0.3, 0.15

## FxItem3TokenLute  (cell 14x16, origin 7,14)
Bard's Lute follower (Book of Tears states). The note leaves on Activate frame 3 (the strum flash).
- Idle: 12 frames, 1.40 s: 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117, 0.117
- Ready: 2 frames, 0.20 s: 0.1, 0.1
- Activate: 10 frames, 0.96 s: 0.1, 0.067, 0.067, 0.067, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12
- Wait: 6 frames, 1.00 s: 0.167, 0.167, 0.167, 0.167, 0.167, 0.167
- WakeUp: 4 frames, 0.20 s: 0.05, 0.05, 0.05, 0.05

## FxItem3Note  (cell 14x16, origin 7,9)
Bard's Lute note: skeleton-mage bolt collider at the origin.
- Fly: 4 frames, 0.32 s: 0.08, 0.08, 0.08, 0.08
- Pop: 5 frames, 0.30 s: 0.04, 0.05, 0.06, 0.07, 0.08

## FxItem3Ferret  (cell 24x14, origin 12,12)
Pet Ferret, faces right; code flips it (feet at the origin).
- Idle: 4 frames, 0.97 s: 0.3, 0.25, 0.3, 0.12
- Run: 6 frames, 0.42 s: 0.07, 0.07, 0.07, 0.07, 0.07, 0.07

## FxItem3Bubble  (cell 14x14, origin 7,7)
Bubble Pipe bubble: drifts 45 px/s for 2.6 s, pops on a monster (0.3 + slow) or at the end.
- Fly: 4 frames, 0.48 s: 0.12, 0.12, 0.12, 0.12
- Pop: 5 frames, 0.25 s: 0.03, 0.04, 0.05, 0.06, 0.07

## FxItem3Duck  (cell 88x40, origin 44,22)
Rubber Duck squeak ring: damage frames 0..3, hitbox 80 x 34 on the feet (the TrollGroundPound ring, Strike.Collider).
- Squeak: 6 frames, 0.48 s: 0.05, 0.06, 0.07, 0.08, 0.1, 0.12

## FxItem3Firefly  (cell 12x12, origin 6,6)
Firefly Jar: each firefly orbits 17 x 7 px round the hero's chest (code); Zap pops on the monster it touched.
- Glow: 4 frames, 0.42 s: 0.1, 0.1, 0.12, 0.1
- Dim: 2 frames, 0.80 s: 0.4, 0.4
- Zap: 5 frames, 0.25 s: 0.03, 0.04, 0.05, 0.06, 0.07

## FxItem3Dance  (cell 16x12, origin 8,10)
Dancing Shoes: a sparkly footprint every 0.16 s while dancing.
- Step: 6 frames, 0.56 s: 0.06, 0.06, 0.08, 0.1, 0.12, 0.14

## FxItem3Whet  (cell 20x20, origin 10,10)
Whetstone: first hit on a monster (at its aim point).
- Spark: 5 frames, 0.26 s: 0.03, 0.04, 0.05, 0.06, 0.08

## FxItem3Phoenix  (cell 48x56, origin 24,52)
Phoenix Feather burns instead of the hero (at the feet).
- Burst: 10 frames, 0.86 s: 0.05, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.1, 0.12, 0.14

## FxItem3Siphon  (cell 24x36, origin 12,34)
Siphon Gem: a kill's wisp spirals into the hero (at the feet).
- Wisp: 8 frames, 0.40 s: 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05

## FxItem3Fork  (cell 24x32, origin 12,30)
Glutton's Fork: the extra half of a health pickup.
- Heal: 7 frames, 0.63 s: 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12

## FxItem3Coin  (cell 20x48, origin 10,46)
Gambler's Coin: flips over the head as a fight starts; Heads = damage (gold crown), Tails = speed (silver wing).
- Heads: 12 frames, 1.40 s: 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.2, 0.3, 0.3, 0.2
- Tails: 12 frames, 1.40 s: 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.2, 0.3, 0.3, 0.2

## FxItem3Bandage  (cell 32x36, origin 16,34)
Patchwork Bandage halves the first monster hit of a fight.
- Absorb: 7 frames, 0.49 s: 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1

## FxItem3Boots  (cell 28x12, origin 14,10)
Iron Boots: hit but not knocked back.
- Clank: 5 frames, 0.30 s: 0.04, 0.05, 0.06, 0.07, 0.08

## FxItem3Key  (cell 28x28, origin 14,22)
Skeleton Key pickup on the floor (origin on the pickup point) and the sparkle when it is picked up.
- Lie: 8 frames, 1.45 s: 0.12, 0.08, 0.2, 0.2, 0.15, 0.2, 0.2, 0.3
- Collect: 6 frames, 0.40 s: 0.04, 0.05, 0.06, 0.07, 0.08, 0.1

## FxItem3Heart  (cell 32x40, origin 16,36)
Gilded Heart pickup (beats), collect sparkle, and the golden beat that heals 0.5 as a fight starts.
- Lie: 6 frames, 1.24 s: 0.25, 0.2, 0.12, 0.12, 0.25, 0.3
- Collect: 6 frames, 0.40 s: 0.04, 0.05, 0.06, 0.07, 0.08, 0.1
- Beat: 7 frames, 0.57 s: 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.12

## FxItem3IndSluggish  (cell 24x12)
Troll Marrow slow: feet overlay.
- Loop: 4 frames, 0.60 s: 0.15, 0.15, 0.15, 0.15

## FxItem3IndBurn  (cell 24x20)
Wyrm Blood burn: feet overlay.
- Loop: 4 frames, 0.32 s: 0.08, 0.08, 0.08, 0.08

## FxItem3IndShaky  (cell 18x10)
Hare's Dew shaky hands: head overlay.
- Loop: 4 frames, 0.36 s: 0.09, 0.09, 0.09, 0.09

## FxItem3IndKey  (cell 24x16)
Skeleton Key carried: feet overlay (the key hangs at the hip).
- Loop: 8 frames, 1.40 s: 0.2, 0.15, 0.15, 0.2, 0.2, 0.15, 0.15, 0.2

## FxItem3IndBandage  (cell 12x10)
Bandage armed: head overlay.
- Loop: 4 frames, 1.00 s: 0.25, 0.25, 0.25, 0.25

## FxItem3Wanted  (cell 15x15)
Wanted mark: head overlay on the monster.
- Mark: 4 frames, 0.60 s: 0.15, 0.15, 0.15, 0.15

## FxItem3IndHeart  (cell 24x14)
Gilded Heart carried: feet overlay.
- Loop: 5 frames, 0.60 s: 0.12, 0.12, 0.12, 0.12, 0.12
