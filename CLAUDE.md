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
  (`PAPER32` / `INK32`, shifted by the day/night palette). UI colours are `#ebe7dc` / `#1b1a17` tinted halfway toward the
  day/night palette (`UI_TINT` = 0.5, `uiPalette`): the dithered widgets and the HTML panels (`--paper` / `--ink`) follow the light.
- **World:** 7200×7200 torus (wraps on all sides). Home at the centre. Use `wdx/wdy/wdist/wrapX/wrapY` for any distance.
  Regions: `archipelago(x,y)` is a smooth field (new each game, tiles the torus): ~1 = archipelago (more, slightly
  smaller islands, tight channels ~40–90 px), ~0 = open sea (few islands, wide water, most whirlpools, big waves up to
  ~2× as often). It multiplies the older rule that the sea gets wilder with distance from home (`danger`).
- **Villages** (cardinal, ~2475 px from home), one course each, two specialties (1 unit each, all at `DISH_PRICE` = 6
  coins) + a gift: Nordania (N) Antipasti: Fiori di Zucca, Mozzarelle, gift Tarallini. Estolia (E) Primi: Orecchiette
  con Cime di Rapa, Lasagne, gift Olio Santo. Sudia (S) Secondi: Zampina, Pesce Arrosto, gift Vino Rosso. Westa (W)
  Dessert: Cartellate, Tiramisu, gift Limoncello. The gift is never for sale: the merchant adds it when you buy both dishes.
  **Endings** (dock home with at least one dish of every course): Bare Minimum (one dish per village), Nice Dinner
  (both dishes from at least one village), Banquet (all 8 dishes). See `VILLAGES`, `dinnerTier`, `ENDINGS`.
  **No spoilers:** intro and list name only the four courses; dishes are discovered at the stalls, and the gifts are
  a surprise: never mention them anywhere before one is earned (not in the intro, list, or market).
  Each has a bay, a wooden pier, a lighthouse with a sweeping beam, a pixel-art town, 24 buoys at ~880 px (`BUOYS_PER_VILLAGE`) (toasts "Entering / Leaving the waters of …"; leaving counts 150 px past the buoys).
- **Home waters** (`SAFE_R` = 950 px round home): no whirlpools (pull ring included) and no big waves (any that drift in
  die down harmlessly); a ring of 32 buoys marks the edge, with toasts "Leaving home waters" / "Back in home waters".
  Inside them, a calm **lagoon** (`LAGOON_R` = 650 px round home): no islands and no rocks, room to learn the controls.
- **Guiding wind:** from the start until you first tie up at Nordania, the wind always blows toward Nordania from
  wherever you are (shortest way round the torus; `guideWind`); after that the normal shifting winds apply.
- **Ruins** on the diagonals: dock there for a random power (friendly wind 60 s, blessed nets ×3, full hull).
- **Fish:** sardines (N), mackerel (E), red mullet (S), sea bream (W). Banks denser far from home; home waters have all kinds.
  Fishing: stop on a bank for 2 s and the nets go over; drop anchor on a bank and they go over after 0.25 s.
  **Market = barter table** (left: your hold, every fish a unit; right: the stall: only the dishes not yet bought; no fish for sale).
  The top of the market panel shows how to trade (`MK_TIP`), not the merchant's flavour line.
  Drag or tap units across; balance = fish sold − goods taken. Fish sell for coins: 2 if from other waters, 1 if local.
  "Trade" is disabled if the purse can't cover a negative balance; a positive balance goes to the purse.
  Repairs are automatic at any pier (1 fish = +15 hull; at a village it never spends what the next dish will cost).
  The market is a centred window over a 90% black shade; while it's open the sail badge, compass (with its fish
  counters) and wheel/anchor are hidden. Buttons: Quit (left) and Trade (right); both close it and leave you moored
  with the anchor back, so you can linger; a market opens once per docking (leave and come back to trade again).
- **Compass** (76 px, `CMP_PX`, bottom left, just above the logbook icon, same width; hidden in the tutorial
  until the sail step): points home, a dot per village filled once a dish is bought there; drawn like the
  wheel (greys into a low-res canvas, then dithered): brass bezel with rivets, shaded card, wind rose, glass glare.
  The old fish counters round it are hidden (`#wood`); the cargo is shown on the logbook's right page.
- **Intro:** on "Set sail" the card rolls up into a scroll that is tossed into the list button (skipped with reduced motion).
- **Tutorial** (first voyage, `tut` in the Tutorial section): controls appear one at a time, hidden and disabled
  (keys too) until their step: logbook shimmers (open and close it) -> the sail badge appears, wiggles and sends out rings until tapped
  -> the anchor hub appears with pulsing rings (weigh anchor) -> two curved arrows on the wheel for ~4.5 s (or until
  you steer) -> free. The smoke test skips it with `tutSet("done")`.
- **Controls:** wheel (drag in a circle; half a turn = full lock). The wheel has no backing disc: the sea shows between the spokes; its wood
  is a mid grey (`WOOD`, `WOOD_SH`, `WOOD_RIM` in drawWheel) so it stands out from the pale sea.
  Layout (no panel behind the controls: a wooden dashboard was tried and dropped, it hid too much sea): compass over
  logbook bottom left, wheel bottom centre, sail badge bottom right (level with the logbook).
  Hub of the wheel = anchor only:
  **long press 0.5 s = anchor**. At anchor the wheel fades out and only the hub (bigger, dark) remains. The hub is
  shaded in greys and dithered like the rest of the UI: sailing, a light face (r 14.5) with a big ink anchor; at
  anchor, a single dark knob with one light rim and a paper anchor.
  **Sail badge** (`#sail`, `drawSail`, section "Sail badge"; the old halyard rope is gone): a paper disc with a dark rim,
  bottom right, 76 px, showing the sail state; tap it (or Enter/Space on it, or S) to switch sail (full /
  minimum) with a clack and a buzz; it pops when it switches. The voyage starts with the sail furled.
  The boat gathers way slowly (`BOAT_ACCEL` = 0.4, a quarter of the original 1.6; slowing down unchanged).
  Top speed is kept modest (`WIND_BOOST` = 0.8; running dead downwind adds only up to +10%, `downwindBonus`).
  Oars never come out because of the anchor (nor while getting under way after weighing it).
  The **logbook** button (bottom left corner, under the compass) is just the book, no round knob: a 76 px icon
  (`LOG_PX`) drawn like the wheel (greys, then dithered: dark leather, spine bands, metal corners, strap; drawn in 56
  units and scaled; `drawLogbookIcon`) with a thin paper halo; the cover is plain (no emblem). Its cover swings open to an open-book icon.
  When a course is first crossed off (its first dish bought), the book shimmers (a glint across the cover and a
  wiggle, class `news`) until the logbook is opened; there the new line is drawn across live (`freshCourses`). Its panel is an open book
  that arrives in two steps: the shut book slides down centred (cover up), then the front cover swings open on the
  spine (`.leaf`, its inside is the left page) as the book re-centres; closing reverses it (`toggleList`). The book: stitched leather cover with metal corners (`#book-corner`), the
  dinner list on the left page (4 course names, crossed off once a dish of it is aboard), a crease, and the **Cargo** on the
  right page (`holdHTML`: purse, every fish as a small icon, then every dish and gift bought as an icon only, name on
  hover; the book grows to fit). Each dish and gift has its own 24×24 ink icon (`ITEM_ICONS`, `itemIcon(name)`), used at the market stall too.
  Opening/closing it plays `Sfx.book(open)`: paper flutter, and the cover's thump on closing. The list also shows the day of the voyage
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
Trade routes · Wind · Input · Haptics · Sound · Ship's wheel · Sail badge · Intro · Tutorial · UI refs · Dialog · Fishing · Fog of war ·
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
