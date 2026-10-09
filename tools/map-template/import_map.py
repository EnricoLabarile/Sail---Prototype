"""Turn a sea map drawn on the Supernote template into the game's land.

    pip install numpy opencv-python-headless
    python tools/map-template/import_map.py drawing.jpg [--write]

The drawing: coasts as closed ink lines on the 9x9 squares. Land is whatever
the sea can't reach from home's square (E5), so a line round the whole map
makes a land border and a closed loop in the sea makes an island. Home's own
islet (the loop round E5) is left out: the game draws its own. Small marks
(letters, the house) are dropped; filled dots are listed as villages.

It prints the land as rings of world points (evenodd: the world's square, the
sea's outline, each island) and, with --write, puts them into index.html
between the DRAWN_LAND markers.
"""
import re, sys, cv2, numpy as np

WORLD = 5040
src = sys.argv[1]
im = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
if im is None: sys.exit('cannot read ' + src)

# the grid's frame: the long, dark lines
dark = im < 100
H, W = im.shape
cols = [i for i in range(W) if dark[:, i].sum() > 0.35*W]
rows = [j for j in range(H) if dark[j, :].sum() > 0.35*W]
def runs(v):                                  # centres of runs of neighbouring indices
    out, cur = [], [v[0]]
    for a in v[1:]:
        if a - cur[-1] <= 2: cur.append(a)
        else: out.append(cur); cur = [a]
    out.append(cur)
    return [sum(r)/len(r) for r in out]
cx, cy = runs(cols), runs(rows)
x0, x1, y0, y1 = min(cx), max(cx), min(cy), max(cy)
print(f'frame x {x0:.1f}..{x1:.1f}  y {y0:.1f}..{y1:.1f}', file=sys.stderr)

# inside the frame only; ink = the dark strokes (the template's grey grid is lighter)
pad = 5
gx0, gx1, gy0, gy1 = int(x0)+pad, int(x1)-pad+1, int(y0)+pad, int(y1)-pad+1
ink = (im[gy0:gy1, gx0:gx1] < 105).astype(np.uint8)
h, w = ink.shape
sx, sy = WORLD/(x1 - x0), WORLD/(y1 - y0)
def world(px, py): return ((px + gx0 - x0)*sx, (py + gy0 - y0)*sy)
def pix(wx, wy): return (wx/sx + x0 - gx0, wy/sy + y0 - gy0)

# small marks: letters, the house; filled blobs among them are village dots
n, lab, st, cen = cv2.connectedComponentsWithStats(ink, 8)
dots = []
cell = w/9
for k in range(1, n):
    x, y, bw, bh, area = st[k]
    if max(bw, bh) < 0.4*cell:
        if area > 0.45*bw*bh and min(bw, bh) > 8: dots.append(world(*cen[k]))
        ink[lab == k] = 0
# close small gaps in the lines, then let the sea in from home's square
inkd = cv2.dilate(ink, np.ones((5, 5), np.uint8))
sea = np.zeros((h+2, w+2), np.uint8)
hx, hy = pix(WORLD/2, WORLD/2 + WORLD/9*0.8)  # (a little south of home: open water)
land = (inkd > 0).astype(np.uint8)
cv2.floodFill(land, sea, (int(hx), int(hy)), 2)
sea = (land == 2).astype(np.uint8)
sea = cv2.dilate(sea, np.ones((5, 5), np.uint8))   # the coast runs along the middle of the line
landm = (1 - sea).astype(np.uint8)
# home's islet goes (the game has its own)
n, lab, st, cen = cv2.connectedComponentsWithStats(landm, 8)
hxp, hyp = pix(WORLD/2, WORLD/2)
k = lab[int(hyp), int(hxp)]
if k: landm[lab == k] = 0
# lumps smaller than a speck go too
n, lab, st, cen = cv2.connectedComponentsWithStats(landm, 8)
for k in range(1, n):
    if st[k][4] < 60: landm[lab == k] = 0

# the outline of the land, simplified, in world px; the frame's edge becomes the world's edge
big = np.pad(landm, 1, constant_values=1)
cs, _ = cv2.findContours(big, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
rings = [[0, 0, WORLD, 0, WORLD, WORLD, 0, WORLD]]
for c in cs:
    if cv2.contourArea(c) < 40: continue
    a = cv2.approxPolyDP(c, 0.9, True).reshape(-1, 2) - 1
    if a[:, 0].min() <= 0 and a[:, 1].min() <= 0 and a[:, 0].max() >= w-1 and a[:, 1].max() >= h-1: continue   # the padded frame
    ring = []
    for px, py in a: ring += [round(v) for v in world(px + 0.5, py + 0.5)]
    rings.append(ring)
print(f'{len(rings)} rings, {sum(len(r) for r in rings)//2} points; dots at ' +
      ', '.join(f'({x:.0f},{y:.0f}) {"ABCDEFGHI"[int(x//(WORLD/9))]}{int(y//(WORLD/9))+1}' for x, y in dots), file=sys.stderr)
js = '  const DRAWN_LAND = [\n' + ',\n'.join('    [' + ','.join(map(str, r)) + ']' for r in rings) + '\n  ];'
if '--write' in sys.argv:
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'index.html')
    s = open(path, encoding='utf-8').read()
    s2, k = re.subn(r'  // DRAWN_LAND >>>\n.*?  // <<< DRAWN_LAND\n', lambda m: '  // DRAWN_LAND >>>\n' + js + '\n  // <<< DRAWN_LAND\n', s, flags=re.S)
    if not k: sys.exit('no DRAWN_LAND markers in index.html')
    open(path, 'w', encoding='utf-8').write(s2)
    print('written into index.html', file=sys.stderr)
else:
    print(js)
# a picture to check it by (in the current folder)
cv2.imwrite('drawn_land_check.png', np.where(landm[..., None] > 0, (60, 60, 60), (235, 225, 210)).astype(np.uint8))
