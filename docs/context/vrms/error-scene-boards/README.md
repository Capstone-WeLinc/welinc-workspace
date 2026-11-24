# Error scene boards (picked)

Copies of the picked boards from the "WeLinc design directions" canvas (pages "Round 38" to "Round 43"), so the design no longer depends on the canvas account. The build source for the error scenes in web-vrms (and the portal later).

| Situation | Board | What it shows |
|---|---|---|
| Crash inside the app (staff and admin) | `R39CrashGlow.dc.html` | Truck stopped on a dark road, hazards light the asphalt, steam from the engine |
| Page didn't load (`ErrorState`) | `R39LoadIdle.dc.html` | Truck idling, cargo box open, empty spots blink in turn |
| Record not found ("Repair ticket not found") | `R40NotFoundRandom.dc.html` | Random pick on each visit of `R40NotFoundBay.dc.html` (empty bay, lamps flicker) and `R39NotFoundDrawer.dc.html` (the 0999 folder missing) |
| No access to a page (`ForbiddenPage`) | `R43Gate.dc.html` | Gate chained shut, no sign; CCTV aimed down and panning, amber beacon, lit guard hut |
| Module turned off (`ModuleOffPage`) | `R38OffA.dc.html` | Shutter down with a Closed for now sign |
| Full page crash (the shell itself) | `R43FullPole.dc.html` | Depot in a blackout, snapped line sparks; one lamp flickers, two nearly out, one dark |
| Permissions didn't load (`PermissionsGate`) | `R43PermSwitch.dc.html` | Random pick on each visit: blank pass tapped on the card reader, or the lanyard rack with your pass blank |
| Small errors in cards and dialogs | `R39SmallMatched.dc.html` | Light line-art tile matching what failed |

The 404 and "No VRMS access" reuse the portal's Round 34 scenes, kept in `docs/specs/_root/0019-portal-redesign/boards/` (`R34NotFound`, `R34NoAccess`).

To view one: serve this folder (`python3 -m http.server`) with an empty `support.js` beside the boards and open the file. Without the canvas runtime, the two random-pick boards show both scenes stacked and their switch button does nothing.
