# Portal redo boards (sign in left side, arrival, launcher), 2026-11-25

Every board in this round is on the Design canvas **"WeLinc portal redo: sign in, arrival, launcher"**, https://claude.ai/artifact/5otXp8raWCCbFNWXQJQwfE (codesamtm account), across three pages: Sign in, Arrival and Launcher. Nothing is picked yet.

## On the canvas (28 boards, all screenshotted before publishing)

- **Sign in, left side:** `Main` (copy options), S1 `SignLivery`, S2 `SignPhoto`, S3 `SignCutouts`, S4 `SignVan`, S5 `SignRoute`, S6 `SignType`, S7 `SignPreview`, S8 `SignFacts`, S9 `SignPhotoCard`.
- **Arrival** (each has Replay and Slow; Slow is 3 times slower): A1 `ArrSweep` (the navy side widens, then folds up into the band), A2 `ArrHandoff` (the sign in page rolls up like a shutter), A3 `ArrPark` (the van pulls out of the garage once, then the cards rise), A4 `ArrQuiet` (fade and 12px rise, about 600 ms), A5 `ArrDeal` (the band drops in, the cards drop out from under it), A6 `ArrFocus` (sign in steps back and blurs, the launcher comes forward).
- **Launcher** (Corazon Villareal, three systems): L1 `LauScenes` (slim header, a line drawing on each card), L2 `LauLivery` (white band, navy line drawing), L3 `LauPhoto`, L4 `LauRows`, L5 `LauVan`, L6 `LauLineup` (L300, closed van and wing van parked in three bays), L7 `LauRoute` (one trip out and back on a map), L8 `LauWhite` (no band, gold hairline).
- **Admin launcher** (Victor Ramos, VRMS Admin; tile names from `SuiteEntry.tsx`, counts are sample values): M1 `AdmStrip` (Suite management as a row under the VRMS card), M2 `AdmColumn` (beside it, same height), M3 `AdmSide` (a right column overlapping the band), M4 `AdmBand` (the counts sit in the band).

## Round 47 (Nov 25, night): S27 picked plain, its style options

You picked S27 plain (the map under the whole page, the form on navy glass), without S28's garage turn-taking. On Round 46, S27 is marked picked and its traffic dots are gone (the twelve trucks still run). The new canvas page **"Round 47: S27 styles"** (the canvas opens there) holds the options, each screenshotted with the animations paused:

- `R47Notes` (read first), `R47Plain` (S27 as picked, the reference).
- The form's surface: S27a `R47Frost` (heavier frost, gold hairline edge), S27b `R47Card` (a floating glass card, the map on every side), S27c `R47Open` (no surface, a navy pool behind the form).
- The map's look: S27d `R47Quiet` (roads dimmed, only runs and garages lit), S27e `R47Etch` (fine gold roads, white runs), S27f `R47Lights` (the dense streets glow warm gold, white runs).
- The angle: S27g `R47Flat` (straight down, true to scale; the network is tall, so it stays left of the form instead of running under it).
- Generator: `python3 -I gen/gen48.py <out> [Board,Board]` (imports `gen47.py`; `gen47.py R46Bleed` rewrites S27 without the traffic dots).
- **Picked: S27d `R47Quiet`** (marked on the canvas): S27's glass panel unchanged, the base map at 42% opacity, the runs at 90% and 3.8 units wide, labels for garages and drops only.

## Round 46 (Nov 25, night): S18b picked, redrawn on the real map, nine options

You picked S18b and asked for 6 to 10 options that make the sign in better with its map, with "WeLinc Logistics Operations Workspace" as the title, and whether the map is accurate. All on the new canvas page **"Round 46: S18b on the real map"** (the canvas now opens there), each screenshotted; S18b is marked "picked, redrawn in Round 46".

- **The map check:** S18b was drawn by hand. Fitted against OpenStreetMap coordinates, its pins were 8.4 km off on average and 19 km at worst (San Rafael, Tanay, Baliwag), Pulilan to Sta. Rosa read as 60 km (really 71), and Laguna de Bay was about half its size. Round 46 rebuilds the map from OpenStreetMap: the coast, Laguna de Bay with Talim Island, Taal Lake, every motorway, trunk and primary road, secondary and tertiary streets as texture. The twelve trips are routed on those roads (the route's longest road is the "via" on S29). Garages sit on each town's centre, since the yard addresses aren't in the repo.
- `R46Notes`: the check and the build suggestions (credit "© OpenStreetMap contributors" as ODbL asks, form first and the map loaded after it, no live data before sign in, reduced motion parks the trucks, phones get the form only, one title in the heading and the tab, upright labels).
- S26 `R46Real` (S18b's layout on the real map, labels upright and shrinking with distance), S27 `R46Bleed` (the map runs under the whole page, the form on navy glass), S28 `R46Spot` (the garages take turns, 18 s a loop, a card with that garage's four runs), S29 `R46Board` (a departures board of the regular runs, real km and road), S30 `R46Chart` (a flat navigator's chart: true north, lat and long ticks, a 10 km scale, the title in a cartouche), S31 `R46Horizon` (a steep tilt into a night sky), S32 `R46Trails` (no route lines, the trucks leave gold trails), S33 `R46Drift` (a slow camera, 60 s a loop), S34 `R46Low` (the map fills the panel, the title sits low).
- Generator: `python3 -I gen/gen47.py <out> [Board,Board]` (imports `gen45.py` and `realmap.py`; reads `gen/drawnmap.json`). `realmap.json` is built by `python3 -I gen/prep_map.py <osm dir> gen/realmap.json` from three Overpass downloads over 13.95,120.45,15.15,121.55 (`roads.json`: `way["highway"~"^(motorway|trunk|primary)$"]` with `out body geom`; `coast.json`: `way["natural"="coastline"]`; `lake.json`: the Laguna de Bay and Taal Lake relations) plus `minor.json` (`secondary|tertiary` over 14.05,120.6,15.1,121.4); the raw downloads (about 40 MB) are not kept. Map data © OpenStreetMap contributors, ODbL.
- **Replaced the same night with the drawn map** (you liked the hand-drawn look better, and the full street map was 164 KB compressed). Same nine boards and notes, same canvas page. The map is still traced from OpenStreetMap, so the pins are exact and roads and shores sit within about 0.3 km (the simplification tolerance), but it keeps only the expressways and about 25 main roads, smooths them, lines the shores like an old chart, and shows the city as dots where the street network is dense. About 25 KB compressed for the whole map (S18b was 14 KB).
- **The map credit lives in the page footer** (your call): the map side carries no text of its own; the footer under the form reads "© 2026 WeLinc Logistics · © OpenStreetMap" (linked to openstreetmap.org/copyright). It can't go entirely, because the map is traced from OpenStreetMap data and ODbL asks for the credit where the map is shown.
- Files: `gen/prep_drawn.py <osm dir> gen/realmap.json gen/drawnmap.json` builds the drawn map from the raw downloads plus `realmap.json` (shores, lakes and the routed trips); `realmap.py` draws `drawnmap.json`; `gen47.py` writes the boards.

## Round 45, second pass (Nov 25, night): S18b and six more sign ins

You liked S18 (the tilted map) and S19 (headlights at the garage door), and asked for S18 with more and longer routes that look like real roads, plus six more options on the same page. All on "Round 45: sign in, dark split", each screenshotted (moving states checked with the animations paused at a set second); S18 and S19 are marked "liked" there.

- S18b `R45SignRoads`: the same tilted map, drawn like a dark road map: NLEX and SLEX with shields, EDSA, C-5, Marcos Highway and the other arterials, street grids in each town, Manila Bay, Laguna de Bay and the Pasig. Twelve trips, four per garage, each driving out along the roads to a named drop pin and back (San Fernando, Port Area, Baliwag, Malolos; Tanay, Rodriguez, Taguig, Sampaloc; Pasay, Sto. Tomas, Tagaytay, Dasmariñas), with quiet traffic dots on the big roads.
- S20 `R45SignNav`: navigation view, the map rolls under the van on NLEX, one quiet trip line at the bottom.
- S21 `R45SignWing`: the wing van at the loading bay at night, its wing lifts to show the lit cargo, then closes.
- S22 `R45SignToll`: the toll gate, RFID light turns green, the arm lifts and the truck rolls through toward you.
- S23 `R45SignYard`: the yard from above at night: workshop roof, three lit bays, trucks parked in angled stalls, one pulling out through the gate.
- S24 `R45SignTrails`: long exposure light trails on a cloverleaf interchange, white one way, red the other, amber for the trucks.
- S25 `R45SignCab`: from the driver's seat: the road through the windshield, a rosary swinging from the mirror, the gauges, a phone with the route to Sta. Rosa.
- Generator: `python3 -I gen/gen46.py <out> [Board,Board]` (imports `gen45.py`, which rewrites the Round 45 boards unchanged).

## Round 45 (Nov 25, night): dark split sign in, launchers with their own layouts

Your notes on Round 44: none of it works (it is marked "out" on the canvas). The sign in goes back to dark navy all around, like the original on `development` (dark form side, dark fields, gold Sign in), but keeps the split. The Round 44 launchers reused one layout and one drawing, so every launcher in this round has its own layout. Be creative: the built map sign in looked better than Round 44, but still not good enough.

- **"Round 45: sign in, dark split"**: S16 `R45SignRoad` (a 3D night road, the van ahead with tail lights, lamps going by), S17 `R45SignIso` (the depot as an isometric model at night, a truck driving out), S18 `R45SignMap` (the real branch map tilted into 3D, trips out and back), S19 `R45SignFront` (a truck's headlights at the garage door). A fifth, the logo's slashes, was dropped after its screenshot.
- **"Round 45: launcher, own layouts"**: L15 `R45LaunchRoad` (the night road in the band, cards that show each system's first screen), L16 `R45LaunchModel` (the depot model fills the band, one bar of three under it), L17 `R45LaunchSplit` (split like the sign in, the last opened system leads), L18 `R45LaunchBento` (pick up where you left off, a Manila clock, your account), L19 `R45LaunchPanels` (three panels, the one you point at opens up).
- The screen previews in the launcher cards are drawings with seed-like sample rows (plates from the VRMS seed), not live data. Live counts would need each system's API, which is a cross-system spec.
- Generator: `python3 -I gen/gen45.py <out>`.

## Round 44 (Nov 25, late): launcher and sign in again, on two new canvas pages

Your notes on the first 28 boards: S1 looked good, and you liked S4 and S6 to S8 too. The whole sign in page is open, with no system codes on it. Pick the launcher before the arrival. The launcher was too bare, and the cards' icon tile, role pill and "Open [system]" arrow row looked AI made. L3, L4 and L8 are out.

- **"Round 44: launcher"** (Corazon Villareal, three systems): L9 `R44Depot`, L10 `R44Tall`, L11 `R44Preview`, L12 `R44Light`, L13 `R44Words`, L14 `R44Account`. Every one is built on one connected depot drawing: the dock for bookings, the service lane for maintenance and the repair bay for repairs, with a few quiet loops (a box loading, checklist ticks, the lift rising, lamps, a van passing one way). No card has an icon tile, a pill or an Open row. The role is plain text. The page is filled with real things only: what each system does, and your own last sign in and devices.
- **"Round 44: sign in"**: S10 `R44SignDock`, S11 `R44SignType`, S12 `R44SignCentre`, S13 `R44SignPreview`, S14 `R44SignBand`, S15 `R44SignFleet`.
- Generator: `python3 -I gen/gen44.py <out>` writes all 12 boards (it imports `parts.py`). `canvas.json` here is the index as published with this round.

## Your calls this round

- **The truck photo is out** (Nov 25): S2, S9 and L3 are marked "out: the photo" on the canvas and left in place. S3's fleet cut-outs are other photos and still stand.
- Orange and blue are for the trucks only. Pages use the suite navy `#0f1445` and gold `#e8b800`, never the company site's `#013062` and `#F4D839`.
- Your screenshot's copy ("WeLinc Logistics / Operations / Workspace") beats "Keep the fleet moving"; the arrival boards use copy 2 ("Operations Workspace").

## Files

- `project/`: every board's `.dc.html` and the canvas index `canvas.json`. The photo boards in `project/` still carry the old account's asset ids (see below).
- `gen/`: the generator for the 15 boards built on Nov 25 (`python3 -I gen/gen_lau.py <out>`, the same for `gen_adm.py` and `gen_arr.py`; `parts.py` holds the shared pieces: top bar, cards, the van, L300 and wing van drawings). The first 13 boards were written by hand.
- `photos/`: the four photos, uploaded to the canvas as assets.

## Publishing again from another account

1. Create a canvas from the Design type, upload `photos/*` as assets, and swap the ids in the photo boards. In `project/` the ids are `558553c08b7729b5c0d84643e8938bd3` (`welinc-truck.jpg`), `9430c3c2ce7a7300a0b4204302db9881` (`10ft-closed-van.png`), `2809126484fb24cb07c5e16120cb4be9` (`4w-l300.png`) and `4ab7e4f0cc56bbc0cec298f1ef913b9e` (`6w-14ft.png`). On the current canvas they are `d95a6ae0…`, `363a9972…`, `30f406ee…` and `070ff923…`.
2. Publish `project/canvas.json` first, then the boards.
3. To preview locally, serve a copy with `python3 -I -m http.server`, add an empty `project/support.js` and a `_blob/<id>` copy of each photo, and open `sheet.html?b=SignVan,SignRoute` (four boards at half size). Close the browser afterwards.
