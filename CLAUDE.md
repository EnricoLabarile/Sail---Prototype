# Vento e Vele — project notes for Claude Code

## How to work with me
- **Always reply to me (Enrico) in Italian.** All text inside the game stays in **English**.
- Keep changes small and focused; after every change run the smoke test (see below).
- I test on an Android phone: haptics (Vibration API) matter, iOS ignores them.
- Commit after every working change with a short message in English.

## What the game is
A top-down sailing game in a single HTML file (`index.html`, no dependencies, canvas 2D + Web Audio).
You sail from home to four villages to buy the courses of a dinner (selling fish for coins), then return home.

- **Look:** 1-bit. Everything is drawn in greys into a low-res buffer, then ordered-dithered (Bayer 4×4) to two colours
  (`PAPER32` / `INK32`, shifted by the day/night palette). UI panels use fixed colours `#ebe7dc` / `#1b1a17`.
- **World:** 7200×7200 torus (wraps on all sides). Home at the centre. Use `wdx/wdy/wdist/wrapX/wrapY` for any distance.
- **Villages** (cardinal, ~2475 px from home), one course each, two specialties (1 unit each, price in coins) + a gift:
  Nordania (N) Antipasti: Fiori di Zucca 6, Mozzarelle 5, gift Tarallini. Estolia (E) Primi: Orecchiette con Cime di Rapa 6,
  Lasagne 7, gift Olio Santo. Sudia (S) Secondi: Zampina 6, Pesce Arrosto 7, gift Vino Rosso. Westa (W) Dessert:
  Cartellate 5, Tiramisu 6, gift Limoncello. The gift is never for sale: the merchant adds it when you buy both dishes.
  **Endings** (dock home with at least one dish of every course): Bare Minimum (one dish per village), Nice Dinner
  (both dishes from at least one village), Banquet (all 8 dishes). See `VILLAGES`, `dinnerTier`, `ENDINGS`.
  **No spoilers:** intro and list name only the four courses; dishes are discovered at the stalls, and the gifts are
  a surprise: never mention them anywhere before one is earned (not in the intro, list, or market).
  Each has a bay, a wooden pier, a lighthouse with a sweeping beam, a pixel-art town, 24 buoys at ~880 px (`BUOYS_PER_VILLAGE`) (toasts "Entering / Leaving the waters of …"; leaving counts 150 px past the buoys).
- **Ruins** on the diagonals: dock there for a random power (friendly wind 60 s, blessed nets ×3, full hull).
- **Fish:** sardines (N), mackerel (E), red mullet (S), sea bream (W). Banks denser far from home; home waters have all kinds.
  Fishing: stop on a bank for 2 s and the nets go over; drop anchor on a bank and they go over after 0.25 s.
  **Market = barter table** (left: your hold, every fish a unit; right: the stall: only the dishes not yet bought; no fish for sale).
  The top of the market panel shows how to trade (`MK_TIP`), not the merchant's flavour line.
  Drag or tap units across; balance = fish sold − goods taken. Fish sell for coins: 2 if from other waters, 1 if local.
  "Trade" is disabled if the purse can't cover a negative balance; a positive balance goes to the purse.
  Repairs are automatic at any pier (1 fish = +15 hull; at a village it never spends what the next dish will cost).
  The market is a centred window over a 90% black shade; while it's open the halyard, compass (with its fish
  counters) and wheel/anchor are hidden. Buttons: Quit (left) and Trade (right); both close it and leave you moored
  with the anchor back, so you can linger; a market opens once per docking (leave and come back to trade again).
- **Compass** (top centre, 124 px): points home, a dot per village filled once a dish is bought there; drawn like the
  wheel (greys into a low-res canvas, then dithered): brass bezel with rivets, shaded card, wind rose, glass glare.
  The old fish counters round it are hidden (`#wood`); the hold is in the logbook.
- **Intro:** on "Set sail" the card rolls up into a scroll that is tossed into the list button (skipped with reduced motion).
- **Controls:** wheel (drag in a circle; half a turn = full lock). Hub of the wheel = anchor only:
  **long press 0.5 s = anchor**. At anchor the wheel fades out and only the hub (bigger, dark) remains.
  **Halyard** (rope hanging from a block, bottom right): grab it and it follows the finger at a fixed length (sags
  when slack); pulled taut it runs out through the block, clicking (haptic + sound), and past the mark it switches
  sail (full / minimum) with a clack; on release it swings back. Badge on top shows the sail state. The whole halyard
  is drawn at `ROPE_SCALE` = 1.6 (crisp: the low-res canvas grows too). Its head is lowered (`HEAD_Y`) so the badge's top lines
  up with the top of the wheel; the rope below is short (~45 px), a ~35 px pull switches the sail.
  The boat gathers way slowly (`BOAT_ACCEL` = 0.4, a quarter of the original 1.6; slowing down unchanged).
  Oars never come out because of the anchor (nor while getting under way after weighing it).
  Left button = **logbook** (a leather book icon; its cover swings open on the spine while the panel is open): the dinner (just the 4 course names, crossed off once one dish of it is aboard) + the hold (purse,
  every fish as a unit like at the market, dishes and gifts aboard; live). The list also shows the day of the voyage
  (`dayNo`, +1 at each dawn). Keyboard: arrows, Space = anchor, S = sail.
- **Hazards:** rocks, faraglioni, whirlpools (appear/disappear/wander), rollers (big waves: within ~66° of their travel = surf boost (`SURF_COS`), otherwise they hurt).
- **Atmosphere:** macchia (tree-spurge domes + Mediterranean pines), clouds with parallax and shadows, gulls, wind streaks,
  traders (motor boats on A* lanes between villages; they don't avoid the player, a collision just shoves them aside
  with no damage, then they drift back to their lane; they hail with a speech bubble), fog of war (buoys and a
  340 px radius round each village always show through), clouds see-through at the rim and denser in the middle, each with its shadow at a fixed offset down-right,
  a third of them rain clouds (darker; rain falls from the cloud onto its shadow on the sea, with a rain hiss when you're near),
  day/night palette cycle (6 min), afternoon cicada chorus (kept low; only within ~220 px of a wild island's shore, never at home or on village islands,
  from early afternoon to before the golden hour: 3 Cicada orni + 1 Lyristes plebejus,
  pulsed ~5–8 times a second around 4–5 kHz, in bouts with rests; see `cicadas()` in Sound) with dark nights lit by lanterns, lighthouses and windows.

## Map of index.html (search for these section headers: `// ---------- Name ----------`)
World setup · Islands · Home island · Piers · Villages · Ruins · Rocks · Whirlpools · Fish banks · Boat ·
Trade routes · Wind · Input · Haptics · Sound · Ship's wheel · Halyard · Intro · UI refs · Dialog · Fishing · Fog of war ·
Rollers · Powers from the ruins · Village market · Cicadas · Night sounds · Town sounds · Wind streaks · Shopping list ·
Buoys · Traders · Update · 1-bit rendering · Day and night · Draw · Villages (pixel art) · Ruins (pixel art) ·
Cloud shadows (clouds) · Ambient life: gulls

## Good first tasks in Claude Code
1. Split `index.html` into modules (e.g. `src/world.js`, `src/boat.js`, `src/audio.js`, `src/ui.js`, `src/render.js`)
   with a tiny build (or plain ES modules + a local dev server). Keep a one-file build for sharing.
2. Grow `tests/` from the smoke test: docking, fishing, market purchase, banquet ending.

## Testing
```
pip install playwright && playwright install chromium
python tests/smoke.py
```
The smoke test loads the game, sets sail, docks at a village, buys, returns home and checks for JS errors.
For quick manual testing on the phone: `python -m http.server 8000` and open `http://<pc-ip>:8000` on the same Wi-Fi.
