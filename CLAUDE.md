# Vento e Vele — project notes for Claude Code

## How to work with me
- **Always reply to me (Enrico) in Italian.** All text inside the game stays in **English**.
- Keep changes small and focused; after every change run the smoke test (see below).
- I test on an Android phone: haptics (Vibration API) matter, iOS ignores them. Every vibration goes through `buzz()`,
  scaled by the player's **Vibration** slider on the first screen (`#wg-haptics`, 0..1, `TEXT.worldGen.vibration`;
  `haptics`, kept in `localStorage` as `vv.haptics`; first visit `HAPTICS_DEFAULT` = 0, i.e. no vibration until it's
  raised). The API has no strength, so it scales each pulse's length (× 1.6·haptics; under 4 ms dropped).
- Commit after every working change with a short message in English.
- **Push after every commit** to GitHub (`origin` = https://github.com/EnricoLabarile/Sail---Prototype, branch `master`;
  public repo). Enrico reads and edits files there from the browser: if he says he changed something on GitHub, `git pull`
  first. The game is also served by GitHub Pages at https://enricolabarile.github.io/Sail---Prototype/ (from `master`,
  root; `.nojekyll` keeps it served as is), updated by each push. **Don't republish the claude.ai artifact** (it costs Enrico tokens): just commit and push; GitHub Pages is the way he plays it, unless he asks for the artifact.
- **Tuning and Texts sit at the very top of `index.html`**, in their own `<script>` in `<head>` (right after
  `<title>`): first the Tuning block, then `CHANGES` / `BUILD`, then the Texts (and `fmt`). Their top-level `const`s are
  shared with the game script further down (which starts with `applyTexts`). **Keep them there**: new knobs and texts
  go into that first script, the code that uses them after; never let the Tuning block drift down the file again.
  That first script must only hold plain values (it runs before the page's body exists: no DOM, no game functions).
- **Build stamp**: `BUILD` (between the Tuning block and the Texts) is the time of the last commit, Italian time, shown at the
  top of the first screen ("Build 2026-10-05 14:05", `TEXT.worldGen.build`), so Enrico can tell the phone runs the
  latest version. The pre-commit hook `tools/hooks/pre-commit` stamps it on every commit touching `index.html`;
  **enable it once in each fresh clone/session: `git config core.hooksPath tools/hooks`**.
  Under it, **`CHANGES`** (next to `BUILD`): what's new, **a group per build** (`{build, items}`, newest first), shown
  in a dashed box as numbered lists: "New in this build" (`TEXT.worldGen.changes`, the first group), then up to
  three earlier builds, each headed "Earlier: build …" (`TEXT.worldGen.earlier`, a little paler). All lines look
  alike (no bold). **Update it with every commit**: a new build starts a new first group, and the old first group
  gets the `BUILD` time it had; one plain line per change Enrico should look for; drop groups past the fourth.
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
You run a little restaurant at home: every day brings an order for dinner (fish, and from day 2 village dishes too),
which you must bring home by 19:00; the guests' mood goes up or down with how it went. No ending: the days go on.

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
  Island land is baked in tiles (`ISL_TILE` = 256 px, `islandTile`; `CACHE_MAX` = 160 tiles kept, least recently seen
  dropped): a tile is baked when it comes into view, or up to 160 px ahead of it at one a frame; while baking, only the
  bushes, tufts, specks, stones, pines, scrub patches and clearings on that tile are drawn (`bakeR`, `inBake`). The
  shallows round each island (the two pale rings and the island's shadow) are baked the same way in their own tiles
  (`islandBox(isl, true)`, `drawIslandWaterStatic`); only the crawling surf line is drawn live, cut into dashes by hand
  and only where it's in sight (`surfDashes`, flat ends: a canvas `setLineDash` ran round the whole of a big island
  every frame). Rocks and stacks are painted once each into a little sprite (`rockSprite`, `drawRocks`; a stack's column
  was 15–30 fills a frame); their surf rings stay live, one stroke for all. The fog of war is stretched into `fogBig`
  only when the view crosses into another fog cell or a cell is explored (`fogVer`); otherwise it's one plain stamp.
  The sea's flecks and wavelets are stroked in batches, one path per shade (`seaPaths`), not one stroke each. Near the
  world's seam the trembling compass needle is redrawn every other frame. (Measured in headless Chromium: the scene
  without the dither went from ~4.8 / 5.4 / 6.9 ms (open sea / cluster / village at night) to ~2.8 / 3.2 / 4.0 ms; the
  slowest tile bake from ~23 to ~13 ms.) The island layers are drawn on the
  wrapped copies of the world out to `320 + MAX_RMAX` past the edge, so a big island never pops at the seam.
  Every picture drawn into the scene (baked islands, cloud sprites, fog, soft dots) is a memory canvas too (`sceneCtx`):
  a graphics-card canvas drawn into a memory one is read back from the card, which gave 26 ms stalls one frame in 20.
  The frame goes to the GPU with `texSubImage2D` (same texture, written in place). The night light mask is built per
  light (each touches only the cells round it; beams test their cone cheaply), it cost up to 9 ms by a village.
  The UI palette (`uiPalette`) changes at most twice a second (each change restyles the page). Clouds keep their shape: there are only `CLOUD_MODELS` shapes, each
  painted once into a sprite (plus a darker rain version and its shadow) and shared by all the clouds. Profiling tip: a 2D canvas draws lazily, so time a section only after forcing it
  (`getImageData(0,0,1,1)`), or its cost shows up in the upload. Aim: 60 fps on the phone. The wheel and compass are only redrawn
  (and re-dithered) when something on them changes (`wheelKey`, `cmpKey`, `sailKey`; a shut compass lid is a still
  picture; a window resize clears the wheel's canvas, so it also clears `wheelKey` to force a redraw); hidden HUD elements are not updated every frame; the hull meter is written only when it changes.
  day/night palette (`UI_TINT` = 0.5, `uiPalette`): the dithered widgets and the HTML panels (`--paper` / `--ink`) follow the light.
- **World:** `WORLD_SIZE` = 5040 px square torus (wraps on all sides; was 7200, area halved). Distances in Tuning scale with it (× `WORLD_K`) and counts with its area (× `WK2`), so the sea keeps the same density: change one number to resize the world. Home at the centre. Use `wdx/wdy/wdist/wrapX/wrapY` for any distance.
  Regions: `archipelago(x,y)` (new each game, tiles the torus) is a field of six crossing waves (`SEA_WAVES`, `seaField`)
  cut sharply at a level (`SEA_CUT`, found by sampling) so `CLUSTER_SHARE` (0.32) of the sea is **clusters** (~1 there)
  and the rest **open water** (~0): the density changes abruptly. Clusters are packed with small and middling islands
  (radius ×0.35–0.85, tight channels); open water gets only `OPEN_ISLANDS` (6) little ones (×0.22–0.38), and the most
  whirlpools and big waves (up to ~2× as often): room to run free and surf. Villages may land in either. Up to
  `ISLAND_COUNT` (~58) wild islands, the clusters filling up first. It multiplies the older rule that the sea gets
  wilder with distance from home (`danger`).
  **Spiral** (`SPIRAL` in Tuning and in the world generator, world, 0 = off; by default **random each new world**
  between `SPIRAL_MIN` 0.5 and `SPIRAL_MAX` 1, shown in its field; a value set in the generator stays): the field is mixed
  with `spiralField`, `SPIRAL_ARMS` (3) logarithmic arms winding out from home (`SPIRAL_TWIST` 2.4) plus a denser
  heart round it, each fading with distance and summed over home's neighbouring copies on the wrapped map, so the
  arms meet seamlessly at the edges; both fields are scaled to the same spread (`WAVE_SD`, `SPIRAL_SD`) and mixed
  (1 − SPIRAL)·waves + SPIRAL·spiral, so at ~0.6–0.85 the clusters string along the arms like a galaxy and the old
  waves still make them lumpy; `CLUSTER_SHARE` still holds (the cut is sampled from the mixed field).
  **Island size**: `ISLAND_SCALE` (world, 2.5) scales every wild island (atolls too: ring ×scale, islets ×√scale);
  `ISLAND_COUNT` (wild islands only) falls with its square.
  **Island shapes** (`shapeProfile`, `makeIsland(x,y,R,kind)`; still one radius per angle round a centre): round-ish
  blobs, plus shares set in Tuning (world): `ISLAND_L` (two long arms meeting at a corner), `ISLAND_C` (a horseshoe round
  a deep bay), `ISLAND_BIG` (about 1.7× the size), `ISLAND_ATOLL` (`tryAtoll`: a ring of low sandy islets lying along
  it round a lagoon, 2–3 gaps left open to sail in; no rocks round them; an atoll counts as one island). The shaped
  ones are placed first (they need room), then the blobs fill in.
  **L, C and atolls are off for now** (their shares are 0 in Tuning; the code stays): only blobs and big islands.
  **Foliage** is scattered at any angle (`vegPoint`, `sandAt`; the spurge in `scatterMacchia` by uniform tries over the
  island's box), never along the ISL_N spokes, which on big islands showed as lines; the spurge thins out in irregular
  open patches (a smooth noise of four crossing waves, new per island).
- **Villages** (for now three: E, S, W; Nordania's place is the Temple of Eolus' while `EOLUS_ON`) (cardinal, ~1733 px from home: `VILLAGE_DIST`; each game nudged by `placeVillages`: pushed out by up to
  `VILLAGE_OUT_MAX`, slid sideways by up to `VILLAGE_SIDE_MAX`, kept `VILLAGE_EDGE` from the map edge, never closer to
  each other or to the ruins than in the plain cross, measured on the map; across the wrapped edge N–S and E–W do get closer), one course each, two specialties (1 unit each, all at `DISH_PRICE` = 6
  coins) + a gift: Nordania (N) Antipasti: Fiori di Zucca, Mozzarelle, gift Tarallini. Estolia (E) Primi: Orecchiette
  con Cime di Rapa, Lasagne, gift Olio Santo. Sudia (S) Secondi: Zampina, Pesce Arrosto, gift Vino Rosso. Westa (W)
  Dessert: Cartellate, Tiramisu, gift Limoncello. The stall offers both dishes at every visit; bought dishes wait in the
  hold (`dishHold`, by icon id) until delivered. The gift is never for sale: the merchant adds it, once per voyage, the
  first time both of a village's dishes have been bought (`boughtEver`). The gifts are a surprise: never mention them
  anywhere before one is earned. (The course names in `TEXT.villages` are no longer shown.)
  **Orders: off for now** (`ORDERS_ON` = false: no order in the logbook, no deliveries, no dinner verdict or order
  toasts; the logbook's left page shows the day and the cargo, the right page the **wind card**). When on:
  **Orders** (the `// ---------- Orders ----------` section; no endings any more): every day an `order` for the
  restaurant at home. Day 1: `FIRST_ORDER_FISH` (3) fish of any kind. From day 2: `ORDER_FISH_MIN`–`ORDER_FISH_MAX`
  fish of one kind plus one village dish (two from day `ORDER_TWO_DISHES_FROM` = 4), named in the logbook (the player
  finds which village sells it). Tying up at home before dinner delivers whatever of it is aboard (`deliverOrder`:
  fish and dishes leave the hold, popups, a toast); at `DINNER_HOUR` (19, the mark on the watch) dinner is served
  (`serveDinner`): complete → the guests' mood `satisfaction` rises by `SAT_GAIN`, otherwise it falls by `SAT_LOSS` ×
  the share missing. At first light (`dayNo`++) comes a new order (`newOrder`; toast, the logbook shimmers). The mood is
  the bar top right (`#mood`: a plate icon and a bar, no words, starts at `SAT_START`, pulses when it changes); there's
  no game over for it. **The mood is off for now** (`SATISFACTION_ON` = false: no bar, dinners don't move it, so the
  masseria keeps the look of `SAT_START`). The voyage still ends only by sinking (`#gameover`).
  Each has a bay, a wooden pier, a lighthouse with a sweeping beam, a pixel-art town, 17 buoys at ~616 px (`BUOYS_PER_VILLAGE`, `BUOY_R`) (toasts "Entering / Leaving the waters of …"; leaving counts 150 px past the buoys).
- **Home: a fortified masseria** (`drawHomeBuildings`, home units ×`HOME_BLD`): a walled court with crenellated white
  walls (north gate to our pier, south gate to the guests'), a square watchtower on the north-east corner, the owner's
  house along the south wall, a well, and five trulli (whitewashed drums under grey stone cones) outside the east wall;
  the drying net on the west beach stays. Its look follows the guests' mood, `homeStage` = round(satisfaction×4), 0..4:
  breaches in the walls with rubble (3 − stage), standing trulli (stage + 1, the rest fallen in), weeds in the court at
  0–1; tables with chairs (2 × stage), a pergola of vines and an awning from 2, a string of lanterns from 3 (and the court
  lit at night), a pennant on the tower and the trulli lit at 4. It's baked into the island's tiles, so `rebakeHome`
  drops them when the stage changes. **Guest pier and clients' boats: off for now** (`GUESTS_ON` = false: no pier, no
  boats; `GUEST_PIER` is null). When on: **Guest pier** (`GUEST_PIER`, south side, solid but the player can't moor there):
  the clients' boats (`guests`, drawn with the player's boat model, `drawBoat(g)`, sail furled when tied up) take up to
  `GUEST_BOATS_MAX` (4) berths, two a side (one alongside, one rafted outside it); round(satisfaction × 4) of them: one
  more sails in from the open sea (`GUEST_IN_T` = 10 s, foam at the bow) or one sails away when the mood changes.
- **Home's three looks** (`baseLevel`, starting at `BASE_LEVEL` = 0, the hut, in Tuning; for now a preview, switched from the
  logbook's third spread): 0 a **fisherman's hut** (`drawHut`: a stone hut under a pitched tiled roof, a fire pit,
  a fenced vegetable patch, crates and oars, the drying net), 1 the **masseria** above (its look still follows
  `homeStage`), 2 a **fortified palace** (the masseria at its best, stage 4, plus a longer house with an arcaded
  loggia, a second tower with a pennant on the south-west corner, a fountain with four paths in the court, and
  outside the walls `drawPalaceGrounds`: a whitewashed chapel with an apse, a bell gable and a cross to the
  north-west, an olive grove in three rows to the south; no drying net). Home's `yard` also clears the palace's
  ground of macchia at every level. Night lights follow the level (court and trulli lit at the palace, plus the chapel).
- **Home waters** (`SAFE_R` ≈ 665 px round home): no whirlpools (pull ring included) and no big waves (any that drift in
  die down harmlessly); a ring of 22 buoys (`HOME_BUOYS`) marks the edge, with toasts "Leaving home waters" / "Back in home waters".
  Inside them, a calm **lagoon** (`LAGOON_R` ≈ 455 px round home): no islands and no rocks, room to learn the controls.
- **Wind:** random from the start (the old guiding wind toward Nordania, `guideWind`, is off), then the normal shifting winds.
  **Fair wind** (a power, the medallion button bottom right, `#btn-power`, drawn like the logbook icon in
  `drawLogbookIcon`: a dark brass medallion with a gust; pale and dotted once spent; wiggles while it blows):
  **locked until the Temple of Eolus gives it** (`powerOwned`; until then the button isn't there at all: class `locked`, hidden and disabled);
  `POWER_USES` (1) uses; a spent use comes back `POWER_RECHARGE` (60 s) after it was used (`powerT`, `rechargePower`,
  counted from the moment it's used, so also while it blows; no more refill at the piers); each makes the wind blow
  from astern whichever way she steers for `POWER_WIND_T` (30 s) (the same spell as the ruins' friendly wind:
  `boonWindT`, the badge top left shows the seconds).
- **Temple of Eolus** (`EOLUS_ON` in Tuning, world): it stands in the north, where **Nordania** was, as far out as the
  villages (`VILLAGE_DIST`, not nudged): a ruin island (`makeRuinIsland`, an entry in `RUINS` with `eolus: true`, stone
  pier, temple with columns) whose fog is always clear for `VILLAGE_CLEAR` like a village. Docking there the first time
  gives the fair wind (`startRuin`: bell, flutter, `TEXT.eolus.gift`); later visits just say `TEXT.eolus.again`.
  While it's on, **Nordania is gone**: `VILLAGES` holds only Estolia, Sudia and Westa (its texts stay in `TEXT.villages.nord`,
  unused; sardines still swim in the north). The compass has one dot per village (`DOT_ANG` from each village's
  direction), the trade lanes are home to each village plus each village to the next round (`pairs`, any number), and
  the world generator's preview marks temples with a small diamond.
- **Messages in a bottle** (section "Messages in a bottle"; texts in `TEXT.bottles`): `BOTTLE_COUNT` (6, Tuning, world)
  bottles float about the open sea (`bottles`, `spawnBottle`: not on land, not at a quay, not near home), drifting
  slowly downwind (2.2 px/s) and bobbing; one washed ashore is replaced elsewhere. Drawn by `drawBottle` (with the
  fish banks' layer): a patch of darker water round it (the fish banks' soft dot), a glass bottle on its side with a rolled note inside, a cork, a ripple ring, `BOTTLE_SIZE` (1.8)
  times true scale so it reads. Fished like a fish bank (stop on it, or drop anchor: `bottleUnderBoat`, within
  `BOTTLE_REACH`; fish banks come first): the net goes over, and after `BOTTLE_TIME` (1.2 s) it's hauled in with the
  bottle ("a message in a bottle!", the logbook shimmers) and another one drifts in out of sight. Aboard it takes a
  hold slot (`bottleHold`, counted in `slotsUsed` and `mkSlotsAfter`; a full hold leaves it in the sea), shown in the
  Cargo after the spare sail as a tappable slot (`bottleSlotHTML`, a dot while unread). A tap reads it (`readBottle`):
  the unrolled message `#letter` over everything (a tap rolls it up), and the first reading puts an ink cross on the
  sea chart (`marks`, at a random spot at sea with room round it: no land within 0.8 × `WRECK_LEN`, away from piers,
  home waters, rocks and other wrecks; drawn by `renderMap` whether that sea is explored or not) with a toast, and
  **a wreck lies there** (`addWreck`, `wrecks`): a modern white cruise ship, `WRECK_LEN` (190 px) long, broken in two
  on a reef, each half turned a little off the line (`sa`, `ba`) and listing (its dark hull side showing), decks with
  rows of windows, lifeboats (some gone), a pool and a funnel aft, the bridge forward, the broken ends gutted and
  jagged, the bow going under, a dark slick with foam and flotsam round it, a shadow down-right (`paintWreck`, a
  sprite painted once; `drawWreck` adds a dashed surf ring, live, in the rocks' layer). It's solid: a row of hidden
  rocks along each half (`hidden`, skipped when drawing) plus four real rocks by the break; the first time she comes
  within 220 px a toast ("The wreck from the message!", `TEXT.bottles.wreck`). A new voyage clears them
  (`clearWrecks`, `rockGrid.remove`). 12 messages (placeholder lorem ipsum for now, `TEXT.bottles.texts`), dealt in a shuffled order (`msgQueue`)
  so they don't repeat until all have come up. A new voyage clears them all (`resetBottles`).
- **Ruins** on the diagonals (the temples): **off for now** (`RUINS_ON` = false in Tuning: `RUINS` is empty). When on: dock there for
  a random power (friendly wind 60 s, blessed nets ×3, full hull).
- **Fish:** sardines (N), mackerel (E), red mullet (S), sea bream (W). Banks denser far from home; half the open-sea banks
  (`ROUTE_BANK_SHARE`) lie along the sea roads, home to each village and village to village, within `ROUTE_BANK_SPREAD` of
  the straight line (`routeSpot`), so the fish lead from place to place; home waters have all kinds and plenty of banks (`HOME_BANKS` = 9 in the smaller world, same density as 18 before; refilled as they are fished).
  **Every bank looks alike** (`BANK_LOOK` in Tuning: 4–5 big dark fish going round over the darker water, the old sea
  bream's look), so what's in it is only known when the net comes up.
  Fishing: stop on a bank for 2 s and the nets go over; drop anchor on a bank and they go over after 0.25 s.
  **Hold: `HOLD_MAX` = 9 slots**, each fish or dish takes one, and the spare sail one (`slotsUsed` = `fishAboard` + `dishesAboard` + `spareSlots`; the gifts
  are kept apart, below the slots, and take none): with a full hold the nets stay aboard (a popup "the hold is full",
  once per bank; the hub doesn't turn into a fish), and a haul brings in only what fits. The Cargo shows the slots as a
  3×3 grid (fish first, then dishes, empty slots dashed) and the count ("n/9", `TEXT.logbook.holdCount`). At the
  market a trade that would leave more than 9 in the hold is refused ("No room in the hold", `TEXT.market.balFull`),
  and dishes aboard can be sold back at any stall for `DISH_RESALE` (3) coins.
  **Throwing things overboard** (to make room): in the Cargo a tap on a fish, a dish or a bottle picks it (`cargoSel`,
  outlined; a tap again lets it go; tapping a bottle also reads it), and a "Throw overboard" button appears under the
  slots (`throwOverboard`: it leaves the hold, a splash, a buzz and a popup "… overboard"). The spare sail can't be
  thrown away (its tap rigs it); gifts take no slot.
  A bank counts a little past its drawn circle (`FISH_REACH` = 1.35 × radius). The net is thrown toward the bank's
  middle (24–46 px from the boat, flying out in a small arc as it opens; `netPos`) and hauled back to the boat.
  **Market = barter table** (left: your hold, every fish and dish a unit; right: the stall: both dishes, every visit; no fish for sale).
  The top of the market panel shows how to trade (`TEXT.market.tip`), not the merchant's flavour line.
  Drag or tap units across; balance = fish sold − goods taken. Fish sell for coins: 3 if from other waters (`COIN_FOREIGN`), 1 if local (`COIN_LOCAL`): 4 foreign fish buy both dishes of a village.
  "Trade" is disabled if the purse can't cover a negative balance; a positive balance goes to the purse.
  Repairs are free and automatic at any pier (+15 hull every half second, the hold is never touched); making them a
  cost the player has to think about is planned for later (see the TickTick list "Vento e Vele: playtest suggestions").
  The market is a centred window over the world (no dark backdrop; a clear `#mk-shade` still catches stray taps); while it's open the compass (with its fish
  counters) and wheel/anchor are hidden. Buttons: Quit (left) and Trade (right); both close it and leave you moored
  with the anchor back, so you can linger. **Nothing opens by itself on docking**: tied up at a village or at home, a
  round badge bobs beside the quay where it leaves the beach, on the far side from the boat (`#dock-btn`, `updateDockBtn`, placed from the camera each frame; coins at
  a village, a crate at home; hidden while the table is open); a tap opens the market (with the purse's jingle, `Sfx.coins`), or at home the **storehouse** (a creak of its door
  and a wooden thump, `Sfx.crate`),
  as many times as you like while moored.
  **Home storehouse** (`homeStore` = {fish, dish, bottles}; texts in `TEXT.store`; cleared on a new voyage by
  `resetStore`): the same table (`openStore` → `openMarket(STORE)`, a `store` branch in `stockTable`, `drawTable` and
  the deal): the hold on the left, the store on the right, every fish, dish and bottle a unit, no prices; drag or tap
  them across, "Done" (the only button) moves them (popups "n stored" / "n taken aboard"); taking aboard more than the
  hold's free slots is refused ("No room in the hold"). Sails not rigged sit on the table too (`homeStore.sails`; one left at home
  is not aboard: `sailsInHold` skips it, so it takes no slot); the village markets never show them, so they can't be sold. Goods left at home are meant to count toward the end goal.
- **Compass** (95 px, `CMP_PX`, top centre of the screen (the open logbook covers it); in its tutorial step the bubble hangs under it; hidden in the tutorial
  until its own tutorial step): points home, a dot per village filled once a dish is bought there; drawn like the
  wheel (greys into a low-res canvas, then dithered): brass bezel with rivets, shaded card, wind rose, glass glare.
  The hinged brass **lid** is gone for now (`lidOpen` always true, `lidT` 0; the drawing is still there). A tap
  (or Enter/Space) turns the face over like a card (`watchOn`, `watchT`: squeezed sideways, then the other side opens out) to a
  **24-hour watch** and back: one hand, 0 at the top, 0/6/12/18 numbered, a tick every hour, and a mark on the rim at
  `WATCH_MARK` = 19 (`drawWatchFace`). The time is `watchHour()` = `DAWN_HOUR` (5) + `dayT`×24, so the golden hour
  falls at about 19.
  The old fish counters round it are hidden (`#wood`); the cargo is shown on the logbook's right page.
- **First screen: the world generator** (the intro card; `worldGen`, `TEXT.worldGen`; the old intro lines in
  `TEXT.intro` aren't shown for now): a 200 px preview of this world (land in ink, the clusters' zones dotted, home a
  square, the villages rings), a field per world knob (named as in Tuning: `ISLAND_SCALE`, `ISLAND_COUNT`,
  `CLUSTER_SHARE`, `SPIRAL`, `SPIRAL_ARMS`, `OPEN_ISLANDS`, `ISLAND_BIG`, `ISLAND_L`, `ISLAND_C`, `ISLAND_ATOLL`, `OPEN_ROCK_TRIES`, `TRADERS_HOME`,
  `TRADERS_VILLAGES`, `ROLLER_RATE`, `CLOUD_COUNT`; a changed field turns dark), **Generate** (reloads the page with the
  changed fields, and those already there, in the address: `?ISLAND_SCALE=1.5&…`; untouched knobs keep their own rule,
  e.g. `ISLAND_COUNT` follows `ISLAND_SCALE`) and **Defaults** (reloads with a bare address). In Tuning those knobs are
  `knob('NAME', value)`: a value in the address wins. Under the build time the card has **folding sections**
  (`<details class="wg-sec">`, a tap on the heading opens or shuts it, a little triangle turns): "What's new"
  (`#wg-sec-changes`, the list of changes, `TEXT.worldGen.changesTitle`), "Settings" (the Vibration slider,
  `TEXT.worldGen.settings`), "Sails" (below), "Dangers" (`#wg-sec-dangers`, `TEXT.worldGen.dangersTitle`: fields like the World's for the sharks' and whirlpools' knobs, `SHARK_ON` 1/0, `SHARK_CHANCE`, `SHARK_COOLDOWN`, `SHARK_SPEED`, `SHARK_DAMAGE`, `SHARK_GIVE_UP`, `WHIRL_FOLLOW`, `WHIRL_FOLLOW_SPEED`, all `knob(...)` in Tuning; its Apply, like Generate, reloads with the changed fields of both sections in the address) and "World" (the preview, the knobs and Generate / Defaults; `TEXT.worldGen.title`), **all
  shut at first**;
  **Sails** (`#wg-sec-sails`, `sailEditor`, texts `TEXT.worldGen.sails*`, between Settings and World): per sail its
  polar (`polarPath`, the same drawing as the wind card; the other sail dashed) redrawn live, a slider per angle of its
  `SAIL_POLAR_*` (0–1.5) and for its `RIG_*` values (and the square's run bonus, `squareRunBonus`, which
  `downwindBonus` reads instead of `SQUARE_RUN_BONUS`); they change the Tuning arrays/objects in place, so the game
  uses them at once. A changed row is bold; under each sail a selectable line of the values to paste into Tuning and
  "Reset this sail". Kept in `localStorage` `vv.sails` with the Tuning defaults they were made from: once the
  defaults in Tuning change, the stored values are dropped.
  "Set sail" stays outside them, always in reach. The card is an **open scroll**: a roll at the top and one at
  the bottom (`.card-roll`, the look of the scroll it rolls into on setting sail), the sheet between them scrolls
  (`.scroll-body`, no scrollbar) and each row near a roll fades out as if the paper curved away into it, staying
  straight (`curlScroll`, `CURL_BAND` 42 px, opacity down to 0.15; no distortion: Enrico's choice), with a dotted shade on the paper by each roll (`.curl-shade`). Then "Set sail": the card rolls up into a scroll that is tossed into the list button (skipped with reduced motion).

- **Tutorial**: **off for now** (`TUTORIAL_ON` = false: `tutSet` goes straight to 'done', every control shows at once).
  When on (first voyage, `tut` in the Tutorial section): controls appear one at a time, hidden and disabled
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
  **long press 0.32 s = anchor** (weighing it: `Sfx.anchor(false)`, the chain's links an octave lower than at first and louder, ×2.4, over a low rumble of chain running in) (`HUB_HOLD`, was 0.5). At anchor the wheel fades out and only the hub (dark) remains. The hub is always drawn big (`hubScale` = 2, the
  size it once grew to only at anchor); while sailing its grip is just the hub (`HUB_SAIL_R`), so the spokes still steer. The hub is
  drawn like the compass, in greys then dithered: a light brass bezel (lit top left) with four rivets round a shaded
  face with a glint; sailing, a light face with an ink anchor; at anchor, a dark face, one light rim and a paper anchor (same size both ways). Over a fish bank (not fishing, not
  at anchor) the anchor on the hub turns into a little fish (ink silhouette, paper eye) to point at its use there.
  **The boat in 3D** (`drawBoat`): she is a small 3D model projected each frame: a point (x, y, z) of hers (bow +x,
  starboard +y, up +z) is rolled (`B.roll`, + lifts starboard) and pitched (`B.pitch`, + lifts the bow), then seen from
  above with the view tilted toward the south (`BOAT_TILT` 0.45 in Tuning: height shows as a shift up the screen, like
  the trees); `P(x,y,z)` projects a point, `L(z)` sets the canvas to draw flat on the plane at height z. The hull is a
  few slices from the waterline up to the gunwale (freeboard `FB` 3, dark: her side shows where she dips or the view
  looks at it), then the deck at the gunwale; the helmsman's shoulders and head sit higher; the mast is a line from the
  deck to `MAST_H` (26); the square sail is a curtain from the yard near the masthead down to its foot (slices of its
  curve, the two leeches, the foot drawn up to the yard when furled); the lateen's yard climbs from the tack (low by the
  bow) to the peak (`MAST_H`), the cloth's corners each at their own height. Roll and pitch are damped springs
  (updated in `drawBoat`, per boat, guests too) pulled toward the swell (× `BOAT_SEA_MOTION`), a heel to leeward with
  the sail drawing (`BOAT_HEEL` 0.3 rad at full drive with the wind on the beam), a lean out of a turn, the bow lifting
  as she gathers way and dipping as she slows or surfs; knocks (`B.rock`) shake her. (The old look was a flat 2D drawing
  squeezed and skewed by the swell.)
  **The helmsman**: a black silhouette seen from above (shoulders and head) sits aft on the starboard side of the
  tiller, his arm on its end, so he follows the helm (drawn in `drawBoat`, on every boat).
  **Bow foam**: a small cushion of ragged white lumps at the stem that boil and flicker (in `drawBoat`, under the hull),
  and spray (`bowSpray`, updated with the wake, drawn in its layer): white bits of random size peel off both sides of
  the stem, flung outward, more and bigger with speed; the water stays put, so they fall astern as she sails on, grow,
  then break into a few specks and fade (none below ~6% of top speed, none when moored).
  The boat's square sail is drawn `SAIL_SIZE` (1.3) times the old size, its cloth a dotted grey `SAIL_TONE` (0.72; 1 =
  paper), darker when slack or reefed. At anchor (and moored) the cloth is drawn gathered up to the yard (`boat.furl`,
  eased; a look only: the sail stays set as far as the physics goes), and it spreads again as the anchor comes up.
  **Two sails** (`SPARE_SAIL` in Tuning): **she sets out with no sail rigged** (`START_RIG` = null, `boat.rig` null:
  the wind gives her nothing, `speedFactor` is 0, only the bare mast is drawn; she goes on the oars) and **both sails
  ride in the hold**: every sail not rigged takes one of the `HOLD_MAX` slots (`sailsInHold`, `spareSlots`, counted in
  `slotsUsed` and at the market in `mkSlotsAfter`), first in the Cargo grid, a tappable slot with its own icon in
  `ITEM_ICONS` (`spareHTML(rig)`); a tap on one rigs it (`swapSail(rig)`: toast "… rigged", a thunk and a buzz, the
  new sail bent on furled and spreading) and the one she carried (if any) goes into the hold in its place. Each sail has its own speed curve, in Tuning
  (`SAIL_POLAR_SQUARE`, `SAIL_POLAR_LATEEN`: [degrees off the wind, share of top speed]; `POLARS` picks by `boat.rig`):
  made **starker than real life** so each sail forces its own way of sailing: the **square** one is for the open sea
  with the wind aft of the beam (Enrico's curve: 90° 0.55, 110° 0.97, 130° 1.12, 150° 1.13, 170° 1.04, 180° 1.03, plus `SQUARE_RUN_BONUS` 0.25 running downwind: `downwindBonus` is the square
  sail's only) and nearly dead on the wind (35° 0.02, 50° 0.05, 70° 0.12); the **lateen**
  is for the wind on the beam (50° 0.90, 70° 1.06, beam 1.10, 110° 1.02) and can point up (35° 0.60, 20° 0.22); a
  rounder curve aft of the beam, falling off gently to 0.55 dead downwind (130° 0.88, 150° 0.72, 170° 0.60): pick the sail by the course to the next port. The wind card
  draws the curves with the square's run bonus (radius 40, room for 1.25×).
  **Beyond the curves** (Tuning, each `{square, lateen}`, 1 with no sail; `rigK(tbl)`): the square is the open sea's sail,
  the lateen the islands'. (1) **The wind where she is** (`updateLocalWind`, every frame: `boat.windMul`, `boat.windOff`,
  used for her angle off the wind and the drive as `localWind` / `localStrength`): on open sea steady and
  `OPEN_WIND_BONUS` (0.12) fresher; among the islands (`archipelago`) gusts and lulls every `GUST_EVERY` (3.5 s ±40%,
  +`GUST_RISE` 0.3 / −`GUST_DROP` 0.45) and veering ±`GUST_SHIFT` (35°); in the lee of land within `LEE_DIST` (140 px)
  upwind it drops by up to `LEE_DROP` (0.6). (2) **Retrim** (`boat.trimA` follows her angle off the wind at
  `RIG_RETRIM` 0.4 / 3.5 a second; the drive × max(`RETRIM_FLOOR` 0.3, 1 − mis-trim/`RETRIM_SPAN` 60°·0.7)): after a 60°
  shift the square needs ~5 s to be back to 90%, the lateen ~0.5 s; sharp turns cost the square too. (3) **The
  lateen's tack**: while its yard swings across (`boat.swingAcross`) the drive is × `LATEEN_TACK_DRIVE` (0.35), and on its
  bad tack (wind from port, `sailSide` < 0, 'a la mala') × `LATEEN_MALA` (0.85). (4) **Handling**: turning × `RIG_TURN`
  (0.8 / 1.25), gathering way × `RIG_ACCEL` (0.7 / 1.4). (5) **Leeway** (`boat.lwx/lwy`, added to her motion): to
  leeward, × `RIG_LEEWAY` (0.35 / 0.08) × her speed, full close-hauled (≤50° off), none from 130°. (6) **Big waves**:
  surfing push and length × `RIG_SURF` (1.35 / 0.7, `boat.surfK`), damage × `RIG_WAVE_HIT` (0.6 / 1.4), the slew round
  × `RIG_BROACH` (0.6 / 2.2). Measured (sail-only target): open sea, square at 150° ~51 px/s, lateen at 70° ~55; among
  the islands both drop (gusts, lulls, lee) and the square most. The lateen is drawn by
  `drawLateenSail` (`LATEEN_SIZE` 0.6 in Tuning, on top of `SAIL_SIZE`): a long slanted yard on a short mast near the bow, the triangle of cloth trailing aft, eased out
  to leeward about half the wind's angle off the bow (`boat.boomSigned`), bellied to leeward, a sheet to the stern
  quarter; it furls along the yard at anchor.
  (Wind lines on the sail were tried several ways, fixed streamlines, faint squiggles, short curls along both faces after a sketch, and dropped: they didn't work.) Changing tack, the heavy yard swings across slowly (`LATEEN_SWING` in
  Tuning, 0.9 against the usual trim rate of 3; `boat.swingAcross` until it's settled on the new side). A new voyage
  starts with `START_RIG` again.
  **Wind card** (the logbook's right page, first spread; `windHTML`, texts in `TEXT.sails`): a polar diagram in ink,
  the wind blowing down from the top (an arrow): the filled curve is the share of top speed the sail she carries gives
  on each heading (its `SAIL_POLAR_*`; none with no sail rigged: "No sail: the oars"), a dashed curve for each sail in the hold, a little boat in the middle (paper hull, two thwarts, mast;
  rotated to her heading) with a dotted line on from her bow to a dot where her heading meets the curve; under it "Square sail: 47%" (that share, `speedFactor` at her angle off the wind) and the breeze
  (`windStrength`). It follows her heading live while the book is open on it (`windCardKey`, refreshed in
  `refreshList`, only when the rounded angle, the sail or the breeze changes).
  (Oar handles on the screen's sides, dragged down in time, were tried after a sketch and dropped: they didn't work
  well; the round button below is back.)
  **The spring and the crank** (`SPRING_PADDLES` in Tuning, on; false = the old rhythmic oar button below): the
  paddle wheels run off a wound spring (`spring` 0..1). The crank (`#crank`, 132 px, at the top right of the wheel: a toothed gear
  (16 teeth, a dotted pattern fill `#crank-dots`) turning with the arm, a hatched plate with three rivets, an arm with a
  big knob that follows the finger round, a dashed track and a thick ring round it that fills with the charge; the
  plate inked when full): a finger on it turned **clockwise** winds the spring (`windSpring`:
  `SPRING_TURNS` 1 full turn in one go fills it (`windProg`, shown on the ring while winding; it only counts once complete: let go before and it slips back to 0, nothing charged or locked, start again; Enter/Space winds a whole turn at once); turning back does nothing, a ratchet; the gears rattle, `Sfx.ratchet` (one `chainLink`
  at the anchor chain's original pitch, loudness `CRANK_VOL`; the anchor chain itself now plays an octave lower), once a tooth, with a heavier, lower step and a buzz every
  quarter turn; `Sfx.oarHit` and a buzz when it's full, and then the crank **locks** (`crankLocked`, class `locked`: arm and gear faded, no input, no sound) until the spring has run right down to 0, a cooldown). While it holds a charge
  and she isn't at anchor, moored or in a whirlpool, and the sail alone gives her less than `SPRING_SPEED` (14 px/s),
  the wheels drive her on their own: `oarSpin` eases to 1, `boat.rowV` = `SPRING_SPEED` × `oarSpin` (a steady push, no
  surges or kicks), and the spring runs down over `SPRING_TIME` (30 s) of driving; otherwise it rests. `updateSpring`
  (called by `updateOarCtl`) also turns the wheels (`oarRate`, 1.4 × `OAR_RATE`); the steady churn (`Sfx.rowBed`) is
  silent in this mode: instead `drawBoat` plays `Sfx.paddle` (a low lowpassed splash and a 105→62 Hz thud, loudness
  `PADDLE_VOL` × `oarSpin`) each time a paddle comes round (eight a turn of `B.wheelA`), so the sound follows the wheels;
  when the spring runs down `Sfx.springOff` (the gear's last links slowing, a slack clunk). A new voyage starts with it empty.
  **Paddle wheels, not oars** (pedalò style; in `drawBoat`, every boat): two upright wheels, one a side amidships
  (axle across her at the gunwale, `R` 7, eight flat paddles drawn as quads through `P`, only what's above the water,
  both rims and the hub), turned by the pedalling (`oarRate` × 2π: one turn a stroke of the oar button) or, under sail, freewheeling with the water going by (her speed / R × 0.9), whichever is quicker (`B.wheelA`);
  while pedalling a little foam churns astern of each wheel. The oars are no longer drawn; the rowing logic, sounds and
  the button are unchanged (their names still say 'oar').
  **Oars: rowed by hand, in rhythm** (like grinding berries in Pokémon Emerald; `MANUAL_OARS` in Tuning; false brings
  back the old automatic oars below): a round **oar button** on the right (`#oar-ctl`, above the fair-wind medallion;
  hidden when moored or at the market): a paper disc with a pointer (a triangle on a dashed ring) that turns once a
  stroke, under a **fixed mark** (an ink triangle above it). The first press sets her rowing slowly (power `oarSpin` =
  `OAR_START` 0.2, an ordinary stroke sound) and the pointer sets off from the mark; it goes round at one **steady beat**, `OAR_RATE`
  0.624 turns a second (20% quicker than the old 0.52) whatever the power (`oarCycle`, `oarRate`; calm, so there's time to look at the sea too), easing
  in as she starts rowing and winding down to a halt when she stops (`OAR_RATE_EASE`). Each time it comes back up to the mark is the moment to press: the disc **swells** as it nears (`OAR_WARN` =
  0.2 of a turn, class `ready`) and **goes ink for the whole window** to press (class `now`, pressed or not: a cue to
  catch from the corner of the eye), and at that same instant a dry wooden **clunk** of the oar in its thole sounds
  (`Sfx.oarCue`: noise only, a band at 520 Hz and a click at 2200 Hz, no pitch that moves; loudness `OAR_CUE_VOL` in Tuning), so it can be rowed by ear: hear the clunk, press. A press **on time** (within `OAR_WINDOW` = 0.13 of a turn either side) adds
  `OAR_GOOD` (0.22, less near full), a little pop (class `hit`), a **kick** of extra way (`oarKick` = `OAR_KICK` 20 px/s, half of it added to her speed at once, a
  jolt, the rest carried by the oars and fading at `OAR_KICK_FADE` 1.3 a second: a long glide), a **hard catch** of the blade (`Sfx.oarHit`: a short splash of noise 1400→600 Hz and a dull
  thump low-passed at 260 Hz; loudness × `OAR_HIT_VOL`; the pitched tocks and blips before it sounded like drops), a firm buzz and a **powerful stroke** sound
  (`Sfx.oar(k, true)`: a fuller, brighter swish); **too early or too late** only `OAR_MISS` (0.04), a light
  buzz and an **ordinary stroke** (softer, never a "wrong" sound); one press a turn counts (`oarPressedTurn`). A mark
  passed with no press keeps only `OAR_SKIP` (0.65) of the power (`oarSkipped`; no sound); below 0.06 she stops; plus
  a slow steady drain (`OAR_SPIN_FADE` = 0.05 a second). In rhythm the power climbs to full in ~8 strokes (peaks of
  ~15 px/s); off rhythm she crawls at ~2. Her way is `OAR_MAX` (14 px/s) × power on average (+ the kick), `boat.rowV`, **in
  surges**: the pull, the first half of each turn as the blades sweep aft, drives her on and the recovery lets her
  coast: × (1 − `OAR_SURGE` + `OAR_SURGE`·π·max(0, sin 2π·phase)), `OAR_SURGE` = 0.5; the oars bite quickly (rate
  3.5); wherever she points, even head to wind; it counts only when it's more than the sail gives (`targetSpeed` =
  max(sail, `rowV`)); at anchor or moored the power is 0. `Sfx.oar`: no gloop (the falling sine was dropped as too liquid): a short, dry
  swish of band-passed noise sweeping down (1100→550 Hz; 1500→700 and a little louder for a powerful stroke). **Under the strokes** a steady, low churn of water while the oars are out
  (`Sfx.rowBed`, on the ambience bus, `rowL`): **pink** noise band-passed ~480 Hz (Q 0.9), the 'pad' that sounds like water rushing past the blades;
  quiet on the recovery and swelling on each pull (the first half of the turn), brighter as she picks up way (a brown
  low-passed churn was tried in its place and lost the water; drips as the blades came out were tried
  and dropped: they sounded like a bird); loudness `OAR_BED_VOL` in Tuning, × the oars out (`boat.oarK`) × (0.4 + 0.6 × power). Enter/Space on the button press it too. On the boat the oars come out while
  there's power, the blades sweep with the cycle (`oarPh`: forward at the catch, aft at the finish) with a splash
  ring mid-pull (rowing, the stroke never flips as the helm crosses the middle). The stroke never jumps or freezes: when
  she stops rowing the beat winds down to a halt as the oars come in, and a press while they're
  still out carries on from where the blades are (no reset to the mark). **No rowing when the sail drives her
  fast**: once the sail alone would give her more than `OAR_LOCK_SPEED` (16 px/s, `boat.sailV`; free again below 0.8 ×)
  the oars are shipped (power 0, they come in) and the button is greyed and dashed, untouchable (class `locked`,
  label `TEXT.oars.locked`); rowing is for slow going, e.g. close to the wind. Turning is `ROW_TURN_MULT` × quicker while rowing (`boat.rowing`). With manual oars the sail is never
  brailed up.
  **Sail badge** (`#sail-btn`, a round badge on the right under the oar button, which sits above it; shown only while
  a sail is rigged and the market is shut; `updateSailBtn`): it shows the rigged sail's icon. A **tap** sets or furls
  the sail (`boat.sailFurled`: no drive, the cloth gathered to the yard, the badge inked). **Hold it**: past
  `SAIL_SHAKE_AFTER` (0.2 s) it shakes, and at `SAIL_STOW_HOLD` (1.1 s) the sail is unbent and stowed in the hold
  (`boat.rig` = null, toast "… stowed in the hold"; refused with "the hold is full" if no slot is free), leaving her on
  the oars. Both knobs in Tuning.
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
  day's **order** on the left page ("Tonight's order", the day, one line per item, crossed off once delivered, with
  "got/n" while partly delivered, and a note: due by 19:00 / all delivered / dinner served; `freshLines` animates a line
  crossed off since the book was last opened), a crease, and the **Cargo** on the
  right page (`holdHTML`: purse, every fish as a small icon, then every dish aboard and gift as an icon only, name on
  hover; the book grows to fit). Each dish and gift has its own 24×24 ink icon (`ITEM_ICONS`, `itemIcon(name)`), used at the market stall too.
  **Three spreads**: a sideways swipe across the open book turns the page (left = forward: the list and cargo, the
  **sea chart**, then **home's look**; right = back; `turnPage`, `logSpread` 0..2): a sheet swings over on the spine (copies of the pages, `snapPage`), with
  `Sfx.pageTurn()` and a buzz; the book remembers the spread it was left on and opens there. The **sea chart** (`renderMap`)
  is drawn across both pages and the crease, square, `MAP_RES` pixels a side then dithered like the widgets: only the
  cells the boat has seen (fog of war's `explored`; land inked round its coast) and nothing else: no marks for home,
  ports, ruins or the boat (Enrico's choice: you find your way by the coastlines). It is drawn only when
  shown (book opened on it, or a page turned to it), never while sailing (~3 ms; the land under each pixel is worked out
  once, ~10 ms, on the first showing).
  **Home's look** (third spread, class `on-base`; `renderBase`, texts in `TEXT.base`): the left page has a title, a
  hint and three buttons, each a little ink drawing (`BASE_ICONS`: hut, walled court with a tower, palace with two
  towers and a flag) and its name, the chosen one inked solid; the right page a preview of home as it would look
  (`drawBasePreview`: home's water and land drawn into a 150 px canvas, then dithered like the widgets) with its
  name. A tap switches home itself (`baseLevel`, `rebakeHome`), with a thunk and a buzz.
  Opening/closing it plays `Sfx.book(open)`: paper flutter, and the cover's thump on closing. The list also shows the day of the voyage
  (`dayNo`, +1 at each dawn). A tiny faint frame-rate counter (`#fps`, refreshed twice a second while the logbook is open) sits on the
  paper, in the bottom right corner of the right page. Keyboard: arrows, Space = anchor.
- **Hazards:** rocks, faraglioni (**spacing**, Tuning, world: two rocks, or a rock and the shore, either touch or have at
  least `ROCK_GAP` 64 px of water between them, about twice the boat's length, so she never gets stuck in a slot:
  `tooTight`, `shoreTight` in `tryRock` / `tryStack`; stacks stand `ROCK_GAP` + 20–60 px off the cliffs; this left ~555
  rocks instead of ~760 and no tight pairs instead of ~930. **Sizes** vary: `rockSize`, a share `ROCK_BIG` 0.4 drawn
  bigger, up to `ROCK_BIG_MAX` 2.2 ×), whirlpools (appear/disappear/wander; from day 1, `WHIRL_FROM_DAY` = 1; **they creep after her** while she's within `WHIRL_FOLLOW` (2) × their radius, at `WHIRL_FOLLOW_SPEED` (7 px/s), never out of open water (`whirlWaterOK`); **once one catches her** in its core it's set to fade out (`phase` 'out', held until she's flung); drawn as flowing water (`drawWhirlpool`): `WP_ARMS` broad pale arms winding in and curved foam streaks along a tighter spiral (C 1.6), each a smooth curve in three segments swelling in the middle, wobbling a little; **slingshot**:
  running round a whirlpool's outer ring with its swirl, heading within ~37° of the way it turns (`WHIRL_FLING_COS`),
  she gains speed, `WHIRL_FLING` px/s² × how well she follows it × how deep in she is (0.35 at the rim → 1 at the core),
  up to `WHIRL_FLING_MAX` above her normal speed, fading once she's out; once a pass a whoosh, a buzz and a "flung!"
  popup (`boat.flingW`); the swirl's way round in the physics (`tx`, `ty`, and the drift) matches the drawn foam
  spiralling in (it was flipped: the fling worked going against the drawn swirl); the pull toward the eye still works, so going deeper is a gamble), rollers (big waves: within ~66° of their travel = surf boost (`SURF_COS`), otherwise they hurt). How often: every
  ~2–6 s (`ROLLER_RATE` = 2, twice the old pace; a little rarer near home and among islands, most in open water), at
  most 12 about in open water (8 elsewhere); quieter while the nets are out. **Deep water** (section "Deep water",
  Tuning: `DEEP_SHORE` 70 px from any land, `DEEP_PIER` 280 px from any pier, and out of home waters, `SAFE_R` + 120):
  the only sea where they rise (`rollerAt`: the spot and 120 px ahead of it must be deep) and run (on leaving it,
  40 px ahead, a wave jumps to the last quarter of its life and dies down). It's worked out per `DEEP_CELL` (24 px)
  cell the first time a cell is needed (`deepGrid`, `deepCell`, `deepAt`) and **drawn as a darker sea**
  (`drawDeep`, right after `drawSea`: ink at `DEEP_TINT` 0.13, a pixel a cell stretched smoothly like the fog, redone
  only when the view crosses into another cell), so the player sees where the big waves can come. A quiet hand on
  the waves near the boat (`rollerPace`, eased): one coming up astern (within 220 px, full effect within 140) while she
  runs with it hurries to her pace + `ROLLER_CATCH` (25 px/s, at most 3× its own) and lives a little longer, so it
  catches her and she surfs; one about to hit her badly slows to `ROLLER_SPARE` (0.55) of its pace, time to turn away.
  **Surf waves** (`surfWaves`, `rollerAt`): after `SURF_WAVE_AFTER` (3 s) running downwind (wind at least `DOWNWIND_DEG`
  = 120° round from her bow, the same angle from which `downwindBonus` starts adding speed; moving, not at anchor or
  fishing), each second there's a `SURF_WAVE_CHANCE` (0.3) of a wave of her own: it rises `SURF_WAVE_BACK` (100 px)
  astern, up to `SURF_WAVE_SIDE` (45 px) off to either side (so catching it takes a touch of the helm), already at her
  pace + `ROLLER_CATCH`, living 5.5–6.5 s; one at a time. `rollerPace` then does the rest (it hurries only while she's
  in line with its crest).
- **Sharks** (section "Sharks"; Tuning `SHARK_ON`, `SHARK_CHANCE` 0.25 an encounter per minute at sea out of home
  waters, `SHARK_COOLDOWN` 90 s between encounters, `SHARK_SPEED` 38 px/s, `SHARK_DAMAGE` 8, `SHARK_GIVE_UP` 30 s;
  texts `TEXT.popups.sharkSeen` / `sharkBite`): one at a time (`shark`, `updateShark`, `drawShark`, cleared by
  `resetShark` on a new voyage). It comes in from 330 px off, out of sight, aiming a little ahead of her and weaving in
  long S-curves, a bit quicker once close; a popup "a fin!" when it comes within 230 px; at the hull it bites (damage,
  flash, shake, rock, buzz, `Sfx.crash`) and makes off at ~1.9× speed, gone once 420 px away. It gives up (makes off
  without biting) after `SHARK_GIVE_UP` s, or when she's back in home waters or moored; it swerves off land. Drawn
  under the water as a dark torpedo with pectoral fins and a beating tail (faster when it flees), the dorsal fin in
  ink above the surface with a pale rim and a curl of foam at its front.
- **Atmosphere:** macchia (tree-spurge domes + trees: **olive trees** after Enrico's sketch, `TREE_KIND` 'olive' in Tuning ('pine' brings back the old stone pines, `makePine` / `drawStonePine`); `makeOlive` / `drawOlive`: a short, thick, twisted paper trunk outlined in ink with bark marks, flaring onto a little mound with roots and pebbles, forking into 3–4 outlined branches in a V, a wide flattish crown lifted above the fork: a solid ink mass (a dot per spray) edged with sprays of narrow pointed leaves fanned outward (spiky at the rim, drooping underneath), a few pale veins, a paper halo; a low branch or two with its own spray; `PINE_MODELS` = 4 tree shapes made each game, each maybe mirrored, stored in `isl.umbrellas`), clouds with parallax and shadows (`CLOUD_MODELS` = 4 shapes, made each game, still: they only drift), gulls, wind streaks (`updateStreaks` / `drawStreaks`: following the wind where she is, gusts included, `boat.windOff`, and more often in a gust; `WIND_STREAK_RATE` 2, `_WIDTH` 1.8, `_ALPHA` 0.85, `_LEN` 1.5 in Tuning),
  traders (motor boats on A* lanes: `TRADERS_HOME` = 2 on the four home-to-village lanes, two of them picked at random,
  and `TRADERS_VILLAGES` = 4 between neighbouring villages, one a lane; they don't avoid the player, a collision just shoves them aside
  with no damage, then they drift back to their lane; they hail with a speech bubble), fog of war (buoys and a
  340 px radius round each village always show through), clouds see-through at the rim and denser in the middle, each with its shadow at a fixed offset down-right,
  a third of them rain clouds (darker; rain falls from the cloud onto its shadow on the sea, with a rain sound when you're near: a broad soft wash (between a hiss and a murmur) in gusts plus a patter of soft noise ticks (no watery bubble 'plips': tried and dropped as too intense), sparse at the edge, thick beneath; `rain()` and `rainDrop()` in Sound),
  day/night palette cycle (`DAY_LEN` = 720 s = 12 min a day, was 6), afternoon cicada chorus (kept low; only within ~220 px of a wild island's shore, never at home or on village islands,
  from early afternoon to before the golden hour: 3 Cicada orni + 1 Lyristes plebejus,
  pulsed ~5–8 times a second around 4–5 kHz, in bouts with rests; see `cicadas()` in Sound) with dark nights lit by lanterns, lighthouses and windows.

## Map of index.html (search for these section headers: `// ---------- Name ----------`)
Texts · Tuning · World setup · Islands · Home island · Piers · Villages · Orders · Ruins · Rocks · Whirlpools · Fish banks · Boat ·
Trade routes · Wind · Input · Haptics · Sound · Ship's wheel · Sail switch (unused) · Intro · Tutorial · UI refs · Dialog · Fishing · Fog of war ·
Rollers · Powers from the ruins · Village market · Cicadas · Night sounds · Town sounds · Wind streaks · Shopping list · Sea chart · Turning the logbook's pages ·
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
The smoke test checks there are no JS errors (the market and the storehouse are opened from the quay badge,
`press_dock`). With the orders off (now): the fair wind locked, a visit to the Temple of
Eolus that gives it, then a trip to a village to buy a dish with foreign
fish (after fishing up a message in a bottle, reading it: a cross on the chart, and throwing it overboard), back home
(a fish left in the storehouse), a new day, the
logbook shows it, and a tap on the spare sail rigs it. With `ORDERS_ON`: two days of orders (day 1: 3 fish home before
dinner; day 2: the ordered dish bought at its village, everything brought home and delivered).
For quick manual testing on the phone: `python -m http.server 8000` and open `http://<pc-ip>:8000` on the same Wi-Fi.
