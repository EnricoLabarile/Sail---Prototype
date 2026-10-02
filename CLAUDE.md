# Vento e Vele — project notes for Claude Code

## How to work with me
- **Always reply to me (Enrico) in Italian.** All text inside the game stays in **English**.
- Keep changes small and focused; after every change run the smoke test (see below).
- I test on an Android phone: haptics (Vibration API) matter, iOS ignores them.
- Commit after every working change with a short message in English.
- **Keep the Tuning block up to date.** All the main gameplay knobs live in one place, the `// ---------- Tuning ----------`
  section at the top of the script (boat, hull and dangers, fishing and market, world, ruins' powers, tutorial, look),
  one line of comment each. Enrico edits them by hand. When a feature adds or changes a main knob, declare it there (not
  deep in the code), keep its comment current, and mark with (world) the ones that change world generation.

## What the game is
A top-down sailing game in a single HTML file (`index.html`, no dependencies, canvas 2D + Web Audio).
You sail from home to four villages to buy the courses of a dinner (selling fish for coins), then return home.

- **Look:** 1-bit. Everything is drawn in greys into a low-res buffer, then ordered-dithered (Bayer 4×4) to two colours
  (`PAPER32` / `INK32`, shifted by the day/night palette). UI colours are `#ebe7dc` / `#1b1a17` tinted halfway toward the
  **Performance:** the dither (and the night darkness) runs on the GPU: a WebGL fragment shader (`glSetup`, `ditherPass`)
  uploads the grey buffer as a texture each frame and draws straight to the screen canvas; the JS pixel loop is only
  a fallback when WebGL is missing (it cost ~10 ms a frame and a 1.2 MB allocation, the cause of the hiccups). The
  WebGL context is rebuilt if the browser drops it. Aim: 60 fps on the phone. The wheel, compass and sail switch are only redrawn
  (and re-dithered) when something on them changes (`wheelKey`, `cmpKey`, `sailKey`; a shut compass lid is a still
  picture); hidden HUD elements are not updated every frame; the hull meter is written only when it changes.
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
- **Fish:** sardines (N), mackerel (E), red mullet (S), sea bream (W). Banks denser far from home; home waters have all kinds and plenty of banks (`HOME_BANKS` = 18, refilled as they are fished).
  Fishing: stop on a bank for 2 s and the nets go over; drop anchor on a bank and they go over after 0.25 s.
  A bank counts a little past its drawn circle (`FISH_REACH` = 1.35 × radius). The net is thrown toward the bank's
  middle (24–46 px from the boat, flying out in a small arc as it opens; `netPos`) and hauled back to the boat.
  **Market = barter table** (left: your hold, every fish a unit; right: the stall: only the dishes not yet bought; no fish for sale).
  The top of the market panel shows how to trade (`MK_TIP`), not the merchant's flavour line.
  Drag or tap units across; balance = fish sold − goods taken. Fish sell for coins: 3 if from other waters (`COIN_FOREIGN`), 1 if local (`COIN_LOCAL`): 4 foreign fish buy both dishes of a village.
  "Trade" is disabled if the purse can't cover a negative balance; a positive balance goes to the purse.
  Repairs are free and automatic at any pier (+15 hull every half second, the hold is never touched); making them a
  cost the player has to think about is planned for later (see the TickTick list "Vento e Vele: playtest suggestions").
  The market is a centred window over a 90% black shade; while it's open the sail switch, compass (with its fish
  counters) and wheel/anchor are hidden. Buttons: Quit (left) and Trade (right); both close it and leave you moored
  with the anchor back, so you can linger; a market opens once per docking (leave and come back to trade again).
- **Compass** (76 px, `CMP_PX`, bottom left, just above the logbook icon, same width; hidden in the tutorial
  until its own tutorial step): points home, a dot per village filled once a dish is bought there; drawn like the
  wheel (greys into a low-res canvas, then dithered): brass bezel with rivets, shaded card, wind rose, glass glare.
  It has a hinged brass **lid** (engraved rings, a small star, hinge on top, catch below; `lidOpen`, `toggleLid`): shut at
  the start of every voyage, a tap (or Enter/Space) swings it up on the hinge and shows the compass, another tap shuts it.
  The old fish counters round it are hidden (`#wood`); the cargo is shown on the logbook's right page.
- **Intro:** on "Set sail" the card rolls up into a scroll that is tossed into the list button (skipped with reduced motion).
- **Saving** (sections "Seed" at the top and "Saving" at the end): the world is generated from a seed (`SEED`; during
  world-building `Math.random` is a seeded mulberry32, then the real one is restored, so runtime chance stays random).
  The voyage is saved in localStorage (`SAVE_KEY`, ~4 KB: seed, world fingerprint `WORLD_SIG`, boat, sail, fish, coins,
  dishes and gifts, day and time, tutorial done, guide wind, compass lid, boons, explored fog packed as bits) every 10 s,
  on tying up, and when the page is hidden or closed. With a save the intro shows "Continue · Day N" (resumes at anchor
  where it was) and "New voyage" (clears the save and reloads for a new world). Sinking or serving the dinner clears it.
  If an update changes world generation, `WORLD_SIG` won't match and the old save is dropped. No storage = fresh start.
  **Keep world generation deterministic**: anything random during setup must go through `Math.random` (or `rand`).

- **Tutorial** (first voyage, `tut` in the Tutorial section): controls appear one at a time, hidden and disabled
  (keys too) until their step: logbook shimmers (open and close it) -> the compass appears and
  shimmers with its bubble ("tap to open it"); opening the lid ends the step, else after `TUT_COMPASS_T` = 4.5 s it moves on -> the sail switch appears, sends out rings and its thumb nudges up until it is slid (or tapped)
  -> the anchor hub appears with pulsing rings (weigh anchor) -> two curved arrows on the wheel for ~4.5 s (or until
  you steer) -> 3 s later (`TUT_DROP_WAIT`) the hub pulses again with "Hold here to drop anchor and stop." (optional:
  gone after `TUT_DROP_T` = 3 s, or as soon as the anchor goes down) -> free. The smoke test skips it with `tutSet("done")`. At each step a speech bubble (`#tut-tip`,
  `TUT_TIPS`, `placeTip`) sits by the control with its tail pointing at it and says in a few words what it does. When a step is done its highlight
  goes at once and the next step comes after a pause (`TUT_PAUSE` = 1.5 s, `tutNext`).
- **Controls:** wheel (drag in a circle; half a turn = full lock). Inside the rim a dark backing (a radial grey 70→44, dithered to a deep dotted texture) fills the gaps between the spokes, so the light wood reads clearly; the wood
  is a mid grey (`WOOD`, `WOOD_SH`, `WOOD_RIM` in drawWheel) so it stands out from the pale sea.
  Layout (no panel behind the controls: a wooden dashboard was tried and dropped, it hid too much sea): compass over
  logbook bottom left, wheel bottom centre, sail switch bottom right (as tall as the compass and logbook).
  Hub of the wheel = anchor only:
  **long press 0.5 s = anchor**. At anchor the wheel fades out and only the hub (dark) remains. The hub is always drawn big (`hubScale` = 2, the
  size it once grew to only at anchor); while sailing its grip is just the hub (`HUB_SAIL_R`), so the spokes still steer. The hub is
  drawn like the compass, in greys then dithered: a light brass bezel (lit top left) with four rivets round a shaded
  face with a glint; sailing, a light face with an ink anchor; at anchor, a dark face, one light rim and a paper anchor (same size both ways). Over a fish bank (not fishing, not
  at anchor) the anchor on the hub turns into a little fish (ink silhouette, paper eye) to point at its use there.
  **Sail switch** (`#sail`, `drawSail`, section "Sail switch"; the old halyard rope is gone): a vertical iPhone-style
  switch bottom right, 76×160 px (as tall as compass + logbook). The thumb is the sail badge, a crisp disc (pure ink and
  paper, hard threshold; full sail: paper disc, ink drawing; furled: inverted). Slide it up = set the sail, down = furl
  (`thumbPos` 0..1; a click and buzz passing the middle; let go past the middle and it switches with a clack, else it
  springs back); a tap toggles too, so do Enter/Space on it and S. The track (dithered pill with a groove) is light
  with the sail set, dark when furled. In the tutorial the thumb nudges upward. The voyage starts with the sail furled.
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
  paper, in the bottom right corner of the right page. Keyboard: arrows, Space = anchor, S = sail.
- **Hazards:** rocks, faraglioni, whirlpools (appear/disappear/wander; none on day 1: they start opening from day 2, `WHIRL_FROM_DAY`), rollers (big waves: within ~66° of their travel = surf boost (`SURF_COS`), otherwise they hurt).
- **Atmosphere:** macchia (tree-spurge domes + Mediterranean pines), clouds with parallax and shadows, gulls, wind streaks,
  traders (motor boats on A* lanes between villages; they don't avoid the player, a collision just shoves them aside
  with no damage, then they drift back to their lane; they hail with a speech bubble), fog of war (buoys and a
  340 px radius round each village always show through), clouds see-through at the rim and denser in the middle, each with its shadow at a fixed offset down-right,
  a third of them rain clouds (darker; rain falls from the cloud onto its shadow on the sea, with a rain sound when you're near: a broad soft wash (between a hiss and a murmur) in gusts plus a patter of soft noise ticks (no watery bubble 'plips': tried and dropped as too intense), sparse at the edge, thick beneath; `rain()` and `rainDrop()` in Sound),
  day/night palette cycle (6 min), afternoon cicada chorus (kept low; only within ~220 px of a wild island's shore, never at home or on village islands,
  from early afternoon to before the golden hour: 3 Cicada orni + 1 Lyristes plebejus,
  pulsed ~5–8 times a second around 4–5 kHz, in bouts with rests; see `cicadas()` in Sound) with dark nights lit by lanterns, lighthouses and windows.

## Map of index.html (search for these section headers: `// ---------- Name ----------`)
Seed · Tuning · World setup · Islands · Home island · Piers · Villages · Ruins · Rocks · Whirlpools · Fish banks · Boat ·
Trade routes · Wind · Input · Haptics · Sound · Ship's wheel · Sail switch · Intro · Tutorial · UI refs · Dialog · Fishing · Fog of war ·
Rollers · Powers from the ruins · Village market · Cicadas · Night sounds · Town sounds · Wind streaks · Shopping list ·
Buoys · Traders · Update · 1-bit rendering · Day and night · Draw · Villages (pixel art) · Ruins (pixel art) ·
Cloud shadows (clouds) · Ambient life: gulls · Saving

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
