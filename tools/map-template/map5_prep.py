"""Fifth drawing (2026-10-11): before import_map.py, wipe from the picture what is not land: the dashed border of the
stormy north-west (A5-C5), the dotted line D6-E7 (ignored), the dashed border of the boiling sea (E7-I5), the labels,
the treasures (X), storm clouds and sea monsters (the whirlpools go by themselves); two strokes seal breaks in coasts.
The land isn't closed in (land is outside the drawn coasts), so the sea is given by seeds:
    python map5_prep.py && python import_map.py clean.png --write --seeds="240,893;560,993;740,943;490,1293;190,1293;740,1493;930,943;970,1173;190,1173"
The marks' world positions (Tuning) were read off the check picture: world = (check px + (4.5, 5)) * 5040/954.
(run it in a scratch folder holding the drawing as map5.jpg)."""
import cv2, numpy as np, json
im = cv2.imread('map5.jpg')
OX, OY = 60, 650                                     # (the marks below were read off a crop starting here)
P = lambda pts: [(x + OX, y + OY) for x, y in pts]
mask = np.zeros(im.shape[:2], np.uint8)
DASH = [P([(112,463),(160,478),(200,487),(218,489)]),                  # stormy north-west's border
        P([(397,622),(410,640),(430,665),(450,690),(466,708)]),   # the dotted line D6-E7
        P([(528,676),(545,655),(564,640)]), P([(628,604),(652,600)]), P([(712,590),(742,584)]), P([(802,577),(822,575)]), P([(878,571),(925,565)])]
for pl in DASH: cv2.polylines(mask, [np.array(pl, np.int32)], False, 255, 14)
cv2.rectangle(mask, (470+OX, 325+OY), (575+OX, 425+OY), 255, -1)                      # HOME SEA
cv2.fillPoly(mask, [np.array(P([(578,649),(612,642),(705,614),(805,605),(805,648),(700,652),(640,670),(575,688)]), np.int32)], 255)   # BOILING SEA (slanted, over the C-shaped island)
# the marks drawn with a thick pen (import_map.py would keep them as specks of land): treasures (X), storm clouds,
# sea monsters
for (x, y), r in [((308,105),13), ((741,105),13), ((734,198),13), ((335,455),13), ((896,517),13), ((200,761),13),
                  ((155,326),24), ((240,333),24), ((492,613),24), ((675,363),20), ((370,638),28)]:
    cv2.circle(mask, (x+OX, y+OY), r, 255, -1)
cv2.rectangle(mask, (818+OX, 880+OY), (872+OX, 920+OY), 255, -1)                      # the sea monster in H9
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
im[(mask > 0) & (g < 140)] = (255, 255, 255)
# thin breaks in a coast where the pen skipped: sealed with a short stroke
SEAL = [P([(452,544),(482,532)]), P([(18,490),(45,486)])]
for pl in SEAL: cv2.polylines(im, [np.array(pl, np.int32)], False, (0, 0, 0), 4)
cv2.imwrite('clean.png', im)
