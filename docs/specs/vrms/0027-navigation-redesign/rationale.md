# 0027. Rationale: Navigation redesign

## Context

The web-vrms sidebar today is a flat list in four sections (General, Vehicle repairs, Analytics and AI or Knowledge base, Administration), gated by permission keys in `components/layout/navItems.ts`. Profile and New repair are nav items, "Switch system" hides in the user menu (shown for two or more systems or a VRMS Admin, spec 0007), and nothing tells you that work is waiting. Phones get a bottom tab bar when every item fits in 5, else a sheet. The portal's Admin sidebar is its own flat list with "Permissions" under Access.

The S18 rounds settled the look on `Sidebars8` and in spec 0016 (navy, section labels with lines, no folding sections, only pages with pages under them open, mono count bubbles that turn gold only when hot, the icon collapse). They also drew contents the app doesn't have yet:
- sub pages under Repair tickets and Knowledge base with counts;
- a Fleet section with a Vehicles page;
- a New repair button;
- a system switcher and an account menu.

Spec 0016's AC-16 left "which sections and pages each role sees" to this feature.

Constraints: VMMS owns the fleet (vehicle records live in VMMS and are shared through its fleet API; VRMS keeps only repair side fields), so a Vehicles page in VRMS would overlap VMMS's job. The repair list already keeps its filters in the address (`useRepairListFilters`). There is no counts endpoint, and features 28 and 29 (notifications and badges) aren't designed. The UI refresh phase builds Facade first.

## Options considered

### Option 1: Restyle only

Keep today's pages and flat list; apply spec 0016's look, move Profile to the account menu.

**Pros**:
- Smallest change, no backend work.

**Cons**:
- Misses the point of the board: nothing says what waits on you.
- `Sidebars8`'s sub pages and counts stay unbuilt, so the board comparison fails by design.

### Option 2: Sub pages with counts, minus Fleet (chosen)

Build `Sidebars8`'s sections and sub pages as presets of the repair list, add one counts endpoint, a New repair button, the switcher by spec 0007's rule, and the account menu. Leave Fleet out.

**Pros**:
- The sidebar shows the queues that matter, with gold only where you must act.
- Reuses the repair list and its address filters; one small endpoint.
- Covers the queue count half of feature 29.

**Cons**:
- Backend work (views and counts) inside a UI feature.
- A new poll per open tab.

### Option 3: Sub pages without counts

Build the sub pages as links now; counts wait for feature 29.

**Pros**:
- No backend change now.

**Cons**:
- The hot rule, the reason for gold in the Signature, has nothing to show.
- Feature 29 would revisit the same sidebar.

## Rationale

Option 2 delivers what the board was for: a sidebar that tells a chief mechanic three tickets wait for sign off, and a mechanic that one was sent back. Building sub pages as `view` presets of the existing list keeps one list page and one set of rules, and putting the same rules behind `/vrms/nav/counts` guarantees a count always equals the list you land on. Fleet is left out because VMMS owns the trucks. A Vehicles page in VRMS would look like the place to manage them, and feature 56 decides how VRMS and VMMS share vehicles. The switcher keeps spec 0007's rule (two or more systems, or a VRMS Admin) because everyone else has nowhere to switch to. New repair moves out of the nav into a button, because it is an action, not a place. The portal gets the same frame so the suite reads as one product, with a pending deletion count as its one hot item.
