"""Builds every rigged sheet (monsters + effects) into art/out. The god portrait is drawn by vhorrul_v2_fx.py."""
import os, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out")
sys.argv = [sys.argv[0], OUT]
import wickling_rig, grub_rig, moth_rig, knight_rig, chandler_rig, candelabra_rig, big_rigs, fx
import scalekit as SK
# v0.7 size pass: linear design scale per sheet (1.0 = authored size); see src/CrawlFurther/SheetScales.cs.
# AshMoth also flies 5 design px lower when small (its hover height counts toward the T1 limit).
SCALE = {"TallowGrub": 0.82, "Candelabra": 0.86}
# v0.10: Wickling, AshMoth and MothMatron are redrawn at final size by godsa_final.py (no SCALE / ArtScale entry)
for m in (wickling_rig, candelabra_rig, big_rigs):
    m.Canvas = SK.SCanvas
for m, name in ((grub_rig, "TallowGrub"), (knight_rig, "WaxenKnight"),
                (chandler_rig, "Chandler"), (candelabra_rig, "Candelabra")):
    with SK.scaled(SCALE.get(name, 1.0)):
        m.build(OUT)
big_rigs.OUT = OUT
big_rigs.build_colossus()   # the Lantern Wraith moved to vhorrul_t3.py (v0.8 redraw)
fx.OUT = OUT; fx.build()
import godsa_final
godsa_final.ROOT = os.path.dirname(OUT)
for _n in ("Wickling", "AshMoth", "MothMatron"):
    godsa_final.BUILDERS[_n](godsa_final.ROOT)
print("all rig sheets built")
