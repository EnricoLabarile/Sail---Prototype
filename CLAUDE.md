# Vento e Vele — project notes for Claude Code

## How to work with me
- **Always reply to me (Enrico) in Italian.** All text inside the game stays in **English**.
- Keep changes small and focused; after every change run the smoke test (see below).
- I test on an Android phone: haptics (Vibration API) matter, iOS ignores them.
- Commit after every working change with a short message in English.

## What the game is
A top-down sailing game in a single HTML file (`index.html`, no dependencies, canvas 2D + Web Audio).
You sail from home to four villages to buy food for a banquet, paying with fish, then return home.

- **Look:** 1-bit. Everything is drawn in greys into a low-res buffer, then ordered-dithered (Bayer 4×4) to two colours
  (`PAPER32` / `INK32`, shifted by the day/night palette). UI panels use fixed colours `#ebe7dc` / `#1b1a17`.
- **World:** 7200×7200 torus (wraps on all sides). Home at the centre. Use `wdx/wdy/wdist/wrapX/wrapY` for any distance.
- **Villages** (cardinal, ~2475 px from home): Nordania (N, panzerotti), Estolia (E, lasagna), Sudia (S, mozzarelle), Westa (W, limoncello).
  Each has a bay, a wooden pier, a lighthouse with a sweeping beam, a pixel-art town, 8 buoys at ~880 px (toast "Entering the waters of …").
- **Ruins** on the diagonals: dock there for a random power (friendly wind 60 s, blessed nets ×3, full hull).
- **Fish:** sardines (N), mackerel (E), red mullet (S), sea bream (W). Banks denser far from home; home waters have all kinds.
  Fishing: stop on a bank for 2 s and the nets go over; drop anchor on a bank and they go over at once.
  **Market = barter table** (left: your hold, every fish a unit; right: the stall: the village's food + 3 local fish).
  Drag or tap units across; balance = fish sold − goods taken. Fish sell for coins: 2 if from other waters, 1 if local.
  Food costs 6 coins. "Trade" is disabled if the purse can't cover a negative balance; a positive balance goes to the purse.
  Repairs are automatic at any pier (1 fish = +15 hull; at a village it never spends what the food will cost).
- **Controls:** wheel (drag in a circle; half a turn = full lock). Hub of the wheel = anchor only:
  **long press 0.5 s = anchor**. At anchor the wheel fades out and only the hub (bigger, dark) remains.
  **Halyard** (rope hanging from a block, bottom right): grab it and it follows the finger at a fixed length (sags
  when slack); pulled taut it runs out through the block, clicking (haptic + sound), and past the mark it switches
  sail (full / minimum) with a clack; on release it swings back. Badge on top shows the sail state.
  Oars never come out because of the anchor (nor while getting under way after weighing it).
  Left button: shopping list overlay. Keyboard: arrows, Space = anchor, S = sail.
- **Hazards:** rocks, faraglioni, whirlpools (appear/disappear/wander), rollers (big waves: head-on hurts, from astern = surf boost).
- **Atmosphere:** macchia (tree-spurge domes + Mediterranean pines), clouds with parallax and shadows, gulls, wind streaks,
  traders (motor boats on A* lanes between villages; they don't avoid the player, a collision just shoves them aside
  with no damage, then they drift back to their lane; they hail with a speech bubble), fog of war (buoys and a
  340 px radius round each village always show through), clouds see-through at the rim and denser in the middle,
  a third of them rain clouds (darker, with a shower on the sea below and a rain hiss when you're near),
  day/night palette cycle (6 min) with dark nights lit by lanterns, lighthouses and windows.

## Map of index.html (search for these section headers: `// ---------- Name ----------`)
World setup · Islands · Home island · Piers · Villages · Ruins · Rocks · Whirlpools · Fish banks · Boat ·
Trade routes · Wind · Input · Haptics · Sound · Ship's wheel · Halyard · Intro · UI refs · Dialog · Fishing · Fog of war ·
Rollers · Powers from the ruins · Village market · Night sounds · Town sounds · Wind streaks · Shopping list ·
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
