"""Fourth drawing (2026-10-10): before import_map.py, wipe from the picture what is not land: the hatched driftwood
bars (DRAWN_DEBRIS), the two whirlpool spirals (DRAWN_WHIRLS), the labels and the dashed border of the boiling sea
(DRAWN_BOIL); it prints their world positions for Tuning. Then:
    python map4_prep.py && python import_map.py clean.png --frame=84.2,239.5,1040.8,1196.1 --write
(run it in a scratch folder holding the drawing as map4.jpg)."""
import cv2, numpy as np, json
im = cv2.imread('map4.jpg')
# hatched obstacles across channels: (x0,y0,x1,y1,thick) in picture px
OBS = {'H1':(867,254,897,254,22), 'C3':(410,468,447,455,22), 'B5':(262,675,296,690,22), 'D5':(508,688,538,700,20),
       'E5':(598,722,646,722,20), 'F4':(720,565,720,610,22), 'H2':(862,435,862,478,22)}
SPIR = {'D2':(490,357,52), 'B3':(288,486,50)}
mask = np.zeros(im.shape[:2], np.uint8)
import math
for k,(x0,y0,x1,y1,t) in OBS.items():
    L=math.hypot(x1-x0,y1-y0); ux,uy=(x1-x0)/L,(y1-y0)/L; e=6
    cv2.line(mask,(round(x0-ux*e),round(y0-uy*e)),(round(x1+ux*e),round(y1+uy*e)),255,t+14)
# the labels (HOME SEA, MARE MONSTRUM, BOILING SEA) and the dashed border of the boiling sea: not land
for (a,b,c,d) in [(515,555,595,640),(185,790,362,908),(628,850,822,952)]: cv2.rectangle(mask,(a,b),(c,d),255,-1)
DASH = [[(574,893),(612,860),(652,834),(690,813)], [(890,812),(990,824)]]
for pl in DASH: cv2.polylines(mask,[np.array(pl,np.int32)],False,255,16)
for k,(x,y,r) in SPIR.items(): cv2.circle(mask,(x,y),r,255,-1)
# erase only ink/hatching that isn't land shading (shading is mid grey ~150-170): keep grey, whiten dark ink
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
er = (mask>0) & (g<120)
im[er] = (255,255,255)
cv2.imwrite('clean.png', im)
F = (84.2,239.5,1040.8,1196.1); S = 5040/(F[2]-F[0])
w = lambda x,y: [round((x-F[0])*S), round((y-F[1])*S)]
print(json.dumps({k:[*w(x0,y0),*w(x1,y1),round(t*S*0.8)] for k,(x0,y0,x1,y1,t) in OBS.items()}))
print(json.dumps({k:[*w(x,y),round(r*S)] for k,(x,y,r) in SPIR.items()}))
print(json.dumps([[w(*p) for p in pl] for pl in DASH]))
