"""Draws the Supernote Manta template for sketching the sea map (1920x2560, grayscale PNG).

The 9x9 squares are the game's room map: columns A-I from the west, rows 1-9 from the north,
home in E5. Each square is 560 px of the world (WORLD_SIZE 5040 / 9). Run:
    python tools/map-template/make_template.py              (with the legend of marks at the bottom)
    python tools/map-template/make_template.py --no-marks   (the same page without it: ..._no_marks.png)
The grid sits in the same place on both, so import_map.py reads either.
"""
import pathlib, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 2560                     # Supernote Manta, portrait, 300 ppi
N = 9
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
FONT_R = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
NO_MARKS = '--no-marks' in sys.argv
OUT = pathlib.Path(__file__).with_name('supernote_sea_map_9x9' + ('_no_marks' if NO_MARKS else '') + '.png')

img = Image.new('L', (W, H), 255)
d = ImageDraw.Draw(img)
big, mid, small = ImageFont.truetype(FONT, 64), ImageFont.truetype(FONT, 46), ImageFont.truetype(FONT_R, 34)

# the grid: a square as wide as the page allows, room for the names round it
L, T, CELL = 150, 330, 189            # left, top, square size -> grid 1701 px
R, B = L + N*CELL, T + N*CELL

d.text((L, 70), 'Vento e Vele - sea map', font=big, fill=0)
d.text((L, 160), 'Squares A-I (west to east), 1-9 (north to south). Home is E5. One square = 560 px of the world.',
       font=small, fill=90)

# a faint dot every quarter square, to place things more exactly
for j in range(N*4 + 1):
    for i in range(N*4 + 1):
        if i % 4 == 0 and j % 4 == 0:
            continue
        x, y = L + i*CELL/4, T + j*CELL/4
        d.ellipse([x-2, y-2, x+2, y+2], fill=200)

# the seams between squares (grey) and the frame (black)
for k in range(1, N):
    x, y = L + k*CELL, T + k*CELL
    d.line([(x, T), (x, B)], fill=150, width=3)
    d.line([(L, y), (R, y)], fill=150, width=3)
d.rectangle([L, T, R, B], outline=0, width=6)

# names: letters along the top (and bottom), numbers down both sides
for k in range(N):
    cx, cy = L + (k + 0.5)*CELL, T + (k + 0.5)*CELL
    letter, num = chr(65 + k), str(k + 1)
    for (x, y, t) in [(cx, T - 45, letter), (cx, B + 45, letter), (L - 50, cy, num), (R + 45, cy, num)]:
        d.text((x, y), t, font=mid, fill=0, anchor='mm')

# home: a small house outline in the middle of E5, and the compass's north at the top right
hx, hy = L + 4.5*CELL, T + 4.5*CELL
d.polygon([(hx - 22, hy - 2), (hx, hy - 24), (hx + 22, hy - 2)], outline=110, width=4)
d.rectangle([hx - 16, hy - 2, hx + 16, hy + 22], outline=110, width=4)
d.polygon([(R + 30, 70), (R + 10, 130), (R + 50, 130)], fill=0)
d.text((R + 30, 160), 'N', font=mid, fill=0, anchor='mm')

if not NO_MARKS:
    # a legend: the marks to draw with, so the map can be read back
    ly = B + 100
    d.text((L, ly), 'Marks', font=mid, fill=0)
    items = [('island: draw its coast, shade it', 'island'), ('village (name it)', 'village'), ('temple', 'temple'),
             ('rocks', 'rocks'), ('whirlpool', 'whirl'), ('storm clouds', 'storm'), ('boiling sea: hatch it', 'boil'),
             ('wreck', 'wreck'), ('fish bank', 'fish'), ('anything else: write a word', 'note')]
    col_w, row_h = 850, 64
    for n, (label, kind) in enumerate(items):
        x = L + (n % 2)*col_w
        y = ly + 50 + (n // 2)*row_h
        cx, cy = x + 30, y + 22
        if kind == 'island':
            d.ellipse([cx - 28, cy - 18, cx + 28, cy + 18], outline=0, width=4)
            for k in range(-20, 24, 8):
                d.line([(cx + k, cy - 12), (cx + k + 10, cy + 12)], fill=0, width=2)
        elif kind == 'village':
            d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=0)
        elif kind == 'temple':
            d.polygon([(cx, cy - 18), (cx - 18, cy + 14), (cx + 18, cy + 14)], outline=0, width=4)
        elif kind == 'rocks':
            for ox in (-14, 6):
                d.polygon([(cx + ox - 8, cy + 12), (cx + ox, cy - 10), (cx + ox + 8, cy + 12)], fill=0)
        elif kind == 'whirl':
            d.arc([cx - 20, cy - 20, cx + 20, cy + 20], 0, 300, fill=0, width=4)
            d.arc([cx - 10, cy - 10, cx + 10, cy + 10], 120, 420, fill=0, width=4)
        elif kind == 'storm':
            d.line([(cx + 6, cy - 20), (cx - 8, cy + 2), (cx + 6, cy + 2), (cx - 6, cy + 22)], fill=0, width=5)
        elif kind == 'boil':
            d.rectangle([cx - 24, cy - 18, cx + 24, cy + 18], outline=0, width=3)
            for k in range(-24, 25, 10):
                d.line([(cx + k - 6, cy + 18), (cx + k + 6, cy - 18)], fill=0, width=2)
        elif kind == 'wreck':
            d.line([(cx - 16, cy - 16), (cx + 16, cy + 16)], fill=0, width=6)
            d.line([(cx + 16, cy - 16), (cx - 16, cy + 16)], fill=0, width=6)
        elif kind == 'fish':
            d.ellipse([cx - 20, cy - 10, cx + 8, cy + 10], fill=0)
            d.polygon([(cx + 6, cy), (cx + 22, cy - 12), (cx + 22, cy + 12)], fill=0)
        elif kind == 'note':
            d.text((cx, cy), 'Aa', font=small, fill=0, anchor='mm')
        d.text((x + 80, cy), label, font=small, fill=40, anchor='lm')

img.save(OUT)
print(OUT)
