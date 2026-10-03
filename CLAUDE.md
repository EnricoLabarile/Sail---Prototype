# Vento e Vele — project notes for Claude Code

## How to work with me
- **Always reply to me (Enrico) in Italian.** All text inside the game stays in **English**.
- Keep changes small and focused; after every change run the smoke test (see below).
- I test on an Android phone: haptics (Vibration API) matter, iOS ignores them.
- Commit after every working change with a short message in English.
- **Push after every commit** to GitHub (`origin` = https://github.com/EnricoLabarile/Sail---Prototype, branch `master`;
  public repo). Enrico reads and edits files there from the browser: if he says he changed something on GitHub, `git pull`
  first. The game is also served by GitHub Pages at https://enricolabarile.github.io/Sail---Prototype/ (from `master`,
  root; `.nojekyll` keeps it served as is), updated by each push, besides the claude.ai artifact link for the phone.
- **Keep the Texts section up to date.** Every word the player reads lives in `TEXT`, the `// ---------- Texts ----------`
  section at the very top of the script (intro, villages and their dishes/gifts/lines, fish, toasts, popups, tutorial,
  market, logbook, ruins, endings, sinking, HUD). Enrico authors them by hand. New player-facing text goes there, never
  as a literal in the code; parts the game fills in are `{placeholders}` filled with `fmt(text, {…})`. Texts written in
  the HTML (intro card, buttons, labels) are filled from `TEXT` at start (`applyTexts`). Dish and gift icons are keyed
  by a fixed `icon` id in `VILLAGES`, so renaming a dish keeps its icon.
- **Keep the Tuning block up to date.** All the main gameplay knobs live in one place, the `// ---------- Tuning ----------`
  section at the top of the script (boat, hull and dangers, fishing and market, world, ruins' powers, tutorial, look),
  one line of comment each. Enrico edits them by hand. When a feature adds or changes a main knob, declare it there (not
  deep in the code), keep its comment current, and mark with (world) the ones that change world generation.

## What the game is
A top-down sailing game in a single HTML file (`index.html`, no dependencies, canvas 2D + Web Audio).
You sail from home to four villages to buy the courses of a dinner (selling fish for coins), then return home.

- **Screen:** made for a phone held upright. On a wide screen (`min-aspect-ratio: 4/5`: a computer, a tablet on its side)
  the game plays in a phone-shaped frame in the middle (`#wrap`, at most 880 px tall, ~0.47 wide), dark around it, so the
  view of the world, the grain and the controls match the phone. `--fw` / `--fh` are the frame size in CSS; in the code
  use `viewW()` / `viewH()` (never `window.innerWidth/innerHeight`) for anything that depends on the view size.
- **Look:** 1-bit. Everything is drawn in greys into a low-res buffer, then ordered-dithered (Bayer 4×4) to two colours
  (`PAPER32` / `INK32`, shifted by the day/night palette). UI colours are `#ebe7dc` / `#1b1a17` tinted halfway toward the
  **Performance:** the dither (and the night darkness) runs on the GPU: a WebGL fragment shader (`glSetup`, `ditherPass`)
  uploads the grey buffer as a texture each frame and draws straight to the screen canvas; the JS pixel loop is only
  a fallback when WebGL is missing (it cost ~10 ms a frame and a 1.2 MB allocation, the cause of the hiccups). The
  WebGL context is rebuilt if the browser drops it. With WebGL the screen canvas is one pixel per game pixel (GW×GH) and CSS
  (`image-rendering: pixelated`) blows it up, so the shader runs once per game pixel (9× less work on a 3× phone screen).
  The fps counter in the logbook says `gl` or `js` (which dither runs), the JS ms per frame and, in brackets, how much of
  it goes on copying the frame to the GPU (`upMs`, `workMs`): Firefox on Android ran at 24 fps with only
  5.6 ms of JS (up 0.4): the time went on the 2D canvas drawn on the graphics card, so the tiny scene buffer is now a
  memory canvas (`SCENE_ON_CPU` in Tuning, `willReadFrequently`); `?scene=gpu` / `?scene=cpu` in the address compares the two. Result on Enrico's phone: Firefox 24 -> 48–60 fps
  (Firefox on Android seems to cap at 60), Opera 120. No gradient is made per frame: the soft round shadows (swell, fish banks) are a
  cached sprite stamped scaled (`softDot`, `stampDot`), lighthouse beams and whirlpools keep their gradients (`.grads`).
  Every picture drawn into the scene (baked islands, cloud sprites, fog, soft dots) is a memory canvas too (`sceneCtx`):
  a graphics-card canvas drawn into a memory one is read back from the card, which gave 26 ms stalls one frame in 20.
  The frame goes to the GPU with `texSubImage2D` (same texture, written in place). The night light mask is built per
  light (each touches only the cells round it; beams test their cone cheaply), it cost up to 9 ms by a village.
  The UI palette (`uiPalette`) changes at most twice a second (each change restyles the page). Cloud sprites repaint
  every ~0.35 s, out of step. Profiling tip: a 2D canvas draws lazily, so time a section only after forcing it
  (`getImageData(0,0,1,1)`), or its cost shows up in the upload. Aim: 60 fps on the phone. The wheel and compass are only redrawn
  (and re-dithered) when something on them changes (`wheelKey`, `cmpKey`, `sailKey`; a shut compass lid is a still
  picture); hidden HUD elements are not updated every frame; the hull meter is written only when it changes.
  day/night palette (`UI_TINT` = 0.5, `uiPalette`): the dithered widgets and the HTML panels (`--paper` / `--ink`) follow the light.
- **World:** `WORLD_SIZE` = 5040 px square torus (wraps on all sides; was 7200, area halved). Distances in Tuning scale with it (× `WORLD_K`) and counts with its area (× `WK2`), so the sea keeps the same density: change one number to resize the world. Home at the centre. Use `wdx/wdy/wdist/wrapX/wrapY` for any distance.
  Regions: `archipelago(x,y)` is a smooth field (new each game, tiles the torus): ~1 = archipelago (more, slightly
  smaller islands, tight channels ~40–90 px), ~0 = open sea (few islands, wide water, most whirlpools, big waves up to
  ~2× as often). It multiplies the older rule that the sea gets wilder with distance from home (`danger`).
- **Villages** (cardinal, ~1733 px from home: `VILLAGE_DIST`; each game nudged by `placeVillages`: pushed out by up to
  `VILLAGE_OUT_MAX`, slid sideways by up to `VILLAGE_SIDE_MAX`, kept `VILLAGE_EDGE` from the map edge, never closer to
  each other or to the ruins than in the plain cross, measured on the map; across the wrapped edge N–S and E–W do get closer), one course each, two specialties (1 unit each, all at `DISH_PRICE` = 6
  coins) + a gift: Nordania (N) Antipasti: Fiori di Zucca, Mozzarelle, gift Tarallini. Estolia (E) Primi: Orecchiette
  con Cime di Rapa, Lasagne, gift Olio Santo. Sudia (S) Secondi: Zampina, Pesce Arrosto, gift Vino Rosso. Westa (W)
  Dessert: Cartellate, Tiramisu, gift Limoncello. The gift is never for sale: the merchant adds it when you buy both dishes.
  **Endings** (dock home with at least one dish of every course): Bare Minimum (one dish per village), Nice Dinner
  (both dishes from at least one village), Banquet (all 8 dishes). See `VILLAGES`, `dinnerTier`, `ENDINGS`.
  **No spoilers:** intro and list name only the four courses; dishes are discovered at the stalls, and the gifts are
  a surprise: never mention them anywhere before one is earned (not in the intro, list, or market).
  Each has a bay, a wooden pier, a lighthouse with a sweeping beam, a pixel-art town, 17 buoys at ~616 px (`BUOYS_PER_VILLAGE`, `BUOY_R`) (toasts "Entering / Leaving the waters of …"; leaving counts 150 px past the buoys).
- **Home waters** (`SAFE_R` ≈ 665 px round home): no whirlpools (pull ring included) and no big waves (any that drift in
  die down harmlessly); a ring of 22 buoys (`HOME_BUOYS`) marks the edge, with toasts "Leaving home waters" / "Back in home waters".
  Inside them, a calm **lagoon** (`LAGOON_R` ≈ 455 px round home): no islands and no rocks, room to learn the controls.
- **Guiding wind:** from the start until you first tie up at Nordania, the wind always blows toward Nordania from
  wherever you are (shortest way round the torus; `guideWind`); after that the normal shifting winds apply.
- **Ruins** on the diagonals: dock there for a random power (friendly wind 60 s, blessed nets ×3, full hull).
- **Fish:** sardines (N), mackerel (E), red mullet (S), sea bream (W). Banks denser far from home; half the open-sea banks
  (`ROUTE_BANK_SHARE`) lie along the sea roads, home to each village and village to village, within `ROUTE_BANK_SPREAD` of
  the straight line (`routeSpot`), so the fish lead from place to place; home waters have all kinds and plenty of banks (`HOME_BANKS` = 9 in the smaller world, same density as 18 before; refilled as they are fished).
  Fishing: stop on a bank for 2 s and the nets go over; drop anchor on a bank and they go over after 0.25 s.
  A bank counts a little past its drawn circle (`FISH_REACH` = 1.35 × radius). The net is thrown toward the bank's
  middle (24–46 px from the boat, flying out in a small arc as it opens; `netPos`) and hauled back to the boat.
  **Market = barter table** (left: your hold, every fish a unit; right: the stall: only the dishes not yet bought; no fish for sale).
  The top of the market panel shows how to trade (`TEXT.market.tip`), not the merchant's flavour line.
  Drag or tap units across; balance = fish sold − goods taken. Fish sell for coins: 3 if from other waters (`COIN_FOREIGN`), 1 if local (`COIN_LOCAL`): 4 foreign fish buy both dishes of a village.
  "Trade" is disabled if the purse can't cover a negative balance; a positive balance goes to the purse.
  Repairs are free and automatic at any pier (+15 hull every half second, the hold is never touched); making them a
  cost the player has to think about is planned for later (see the TickTick list "Vento e Vele: playtest suggestions").
  The market is a centred window over the world (no dark backdrop; a clear `#mk-shade` still catches stray taps); while it's open the compass (with its fish
  counters) and wheel/anchor are hidden. Buttons: Quit (left) and Trade (right); both close it and leave you moored
  with the anchor back, so you can linger; a market opens once per docking (leave and come back to trade again).
- **Compass** (95 px, `CMP_PX`, top centre of the screen (the open logbook covers it); in its tutorial step the bubble hangs under it; hidden in the tutorial
  until its own tutorial step): points home, a dot per village filled once a dish is bought there; drawn like the
  wheel (greys into a low-res canvas, then dithered): brass bezel with rivets, shaded card, wind rose, glass glare.
  It has a hinged brass **lid** (engraved rings, a small star, hinge on top, catch below; `lidOpen`, `toggleLid`): shut at
  the start of every voyage, a tap (or Enter/Space) swings it up on the hinge and shows the compass, another tap shuts it.
  The old fish counters round it are hidden (`#wood`); the cargo is shown on the logbook's right page.
- **Intro:** on "Set sail" the card rolls up into a scroll that is tossed into the list button (skipped with reduced motion).

- **Tutorial** (first voyage, `tut` in the Tutorial section): controls appear one at a time, hidden and disabled
  (keys too) until their step: logbook shimmers (open and close it; an open made while the intro scroll is still
  flying in counts, and if the book is already open when the step starts, closing it is enough) -> the compass appears and
  shimmers with its bubble ("tap to open it"); opening the lid ends the step, else after `TUT_COMPASS_T` = 4.5 s it moves on
  -> the anchor hub appears with pulsing rings (weigh anchor) -> two curved arrows on the wheel for ~4.5 s (or until
  you steer) -> 3 s later (`TUT_DROP_WAIT`) the hub pulses again with "Hold here to drop anchor and stop." (optional:
  gone after `TUT_DROP_T` = 3 s, or as soon as the anchor goes down) -> free. The smoke test skips it with `tutSet("done")`. At each step a speech bubble (`#tut-tip`,
  `TUT_TIPS`, `placeTip`) sits by the control with its tail pointing at it and says in a few words what it does. When a step is done its highlight
  goes at once and the next step comes after a pause (`TUT_PAUSE` = 1.5 s, `tutNext`).
- **Controls:** wheel (drag in a circle; half a turn = full lock). Inside the rim a dark backing (a radial grey 70→44, dithered to a deep dotted texture) fills the gaps between the spokes, so the light wood reads clearly; the wood
  is a mid grey (`WOOD`, `WOOD_SH`, `WOOD_RIM` in drawWheel) so it stands out from the pale sea.
  Layout (no panel behind the controls: a wooden dashboard was tried and dropped, it hid too much sea): compass over
  logbook bottom left (compass at the top centre), wheel bottom centre; nothing bottom right (the sail is automatic).
  Hub of the wheel = anchor only:
  No rudder gauge above the wheel (removed): the wheel's turn and the rudder on the boat show the helm.
  **long press 0.5 s = anchor**. At anchor the wheel fades out and only the hub (dark) remains. The hub is always drawn big (`hubScale` = 2, the
  size it once grew to only at anchor); while sailing its grip is just the hub (`HUB_SAIL_R`), so the spokes still steer. The hub is
  drawn like the compass, in greys then dithered: a light brass bezel (lit top left) with four rivets round a shaded
  face with a glint; sailing, a light face with an ink anchor; at anchor, a dark face, one light rim and a paper anchor (same size both ways). Over a fish bank (not fishing, not
  at anchor) the anchor on the hub turns into a little fish (ink silhouette, paper eye) to point at its use there.
  **Sail: automatic** (no button; the old switch `#sail` / `drawSail` is hidden and unused, the halyard rope before it is
  gone). The sail is up by default. When she's slower than `ROW_ENTER` and the wind can't drive her past it either
  (head to wind, or nearly), after `ROW_DELAY` the sail is brailed up and the oars come out (`sailLevel` = `SAIL_MIN`:
  rowing pace `ROW_SPEED`, turning `ROW_TURN_MULT` × quicker); once the sail could give more than `ROW_EXIT` it's set
  again and the oars come in. Never because of the anchor: while it's down (or going down) the sail stays up and the oars
  in; weighing it head to wind, the oars take her. Turning is easier in general (`TURN_RATE` = 0.6). To stop on a fish
  bank, drop anchor (the nets go over after 0.25 s).
  The boat gathers way slowly (`BOAT_ACCEL` = 0.4/1.2: the speed approaches its target at that rate, so it was divided by 1.2 when the top speed went up 20%, keeping the same push in px/s²; slowing down unchanged).
  Top speed is kept modest (`WIND_BOOST` = 0.96, ~52 px/s dead downwind in full wind; running dead downwind adds only up to +10%, `downwindBonus`).
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
  (`dayNo`, +1 at each dawn). A tiny faint frame-rate counter (`#fps`, refreshed twice a second while the logbook is open) sits on the
  paper, in the bottom right corner of the right page. Keyboard: arrows, Space = anchor.
- **Hazards:** rocks, faraglioni, whirlpools (appear/disappear/wander; none on day 1: they start opening from day 2, `WHIRL_FROM_DAY`), rollers (big waves: within ~66° of their travel = surf boost (`SURF_COS`), otherwise they hurt).
- **Atmosphere:** macchia (tree-spurge domes + Mediterranean pines), clouds with parallax and shadows, gulls, wind streaks,
  traders (`TRADERS` = 12 motor boats on A* lanes from home to each village and between neighbouring villages, dealt
  home lanes first, so they show the way out; they don't avoid the player, a collision just shoves them aside
  with no damage, then they drift back to their lane; they hail with a speech bubble), fog of war (buoys and a
  340 px radius round each village always show through), clouds see-through at the rim and denser in the middle, each with its shadow at a fixed offset down-right,
  a third of them rain clouds (darker; rain falls from the cloud onto its shadow on the sea, with a rain sound when you're near: a broad soft wash (between a hiss and a murmur) in gusts plus a patter of soft noise ticks (no watery bubble 'plips': tried and dropped as too intense), sparse at the edge, thick beneath; `rain()` and `rainDrop()` in Sound),
  day/night palette cycle (6 min), afternoon cicada chorus (kept low; only within ~220 px of a wild island's shore, never at home or on village islands,
  from early afternoon to before the golden hour: 3 Cicada orni + 1 Lyristes plebejus,
  pulsed ~5–8 times a second around 4–5 kHz, in bouts with rests; see `cicadas()` in Sound) with dark nights lit by lanterns, lighthouses and windows.

## Map of index.html (search for these section headers: `// ---------- Name ----------`)
Texts · Tuning · World setup · Islands · Home island · Piers · Villages · Ruins · Rocks · Whirlpools · Fish banks · Boat ·
Trade routes · Wind · Input · Haptics · Sound · Ship's wheel · Sail switch (unused) · Intro · Tutorial · UI refs · Dialog · Fishing · Fog of war ·
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
