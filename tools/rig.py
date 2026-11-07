"""Tiny 2D pixel rig: body parts are hand-drawn char-grid sprites, limbs are pixel polylines driven
by joint angles. Every animation frame is a distinct pose rendered fresh (no shifting of a single
image), which gives real limb motion at Crawl's 15-35 px scale.

Angles are in degrees, 0 = pointing right (facing direction), 90 = pointing down.
"""
import math
from anim import Spr


def line_px(x0, y0, x1, y1):
    """Bresenham line, inclusive."""
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return pts


class Part:
    def __init__(self, grid, pivot):
        """grid: char-grid text; pivot: (col,row) inside grid that sits on the joint."""
        rows = [r for r in grid.strip("\n").split("\n")]
        self.px = {}
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c not in ". ":
                    self.px[(x - pivot[0], y - pivot[1])] = c

    def flipped_v(self):
        p = Part.__new__(Part); p.px = {(x, -y): c for (x, y), c in self.px.items()}; return p


class Canvas:
    def __init__(self):
        self.px = {}

    def put(self, x, y, c, over=True):
        if over or (x, y) not in self.px:
            self.px[(x, y)] = c

    def part(self, part, x, y, dx=0, dy=0):
        for (px, py), c in part.px.items():
            self.put(x + px + dx, y + py + dy, c)

    def limb(self, x, y, segs, colors, width=1, end=None):
        """segs: [(length, angle_deg)], colors: per segment char (or (main, shade)).
        Returns end point. width 2 draws a second shaded line one pixel up/left."""
        cx, cy = float(x), float(y)
        for i, (ln, ang) in enumerate(segs):
            a = math.radians(ang)
            nx, ny = cx + ln * math.cos(a), cy + ln * math.sin(a)
            col = colors[min(i, len(colors) - 1)]
            main, shade = (col, col) if len(col) == 1 else (col[0], col[1])
            for (px, py) in line_px(int(round(cx)), int(round(cy)), int(round(nx)), int(round(ny))):
                if width >= 2:
                    self.put(px, py - 1, shade, over=False)
                self.put(px, py, main)
            cx, cy = nx, ny
        ex, ey = int(round(cx)), int(round(cy))
        if end is not None:
            self.part(end, ex, ey)
        return ex, ey

    def spr(self):
        return Spr(dict(self.px))
