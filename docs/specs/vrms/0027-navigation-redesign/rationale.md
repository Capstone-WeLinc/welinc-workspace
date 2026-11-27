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

## Update 2026-11-28: the Suite management frame

### Context

After build steps 1 to 4, suite spec 0019 shipped the Suite management shell from boards `Shell20` and `Switcher16`: a white top bar with the breadcrumb on the left and a grid switcher and avatar on the right, a sidebar that opens with the area name and your role and closes with a darker "WeLinc Logistics" strip holding the collapse button. Spec 0027 predated those boards. Its AC-9 put a switcher menu at the top of the VRMS sidebar, its AC-10 an account menu at the bottom, and its AC-12 asked the portal to copy that frame. Step 4 did so in commit `f6e4985`, undoing `Shell20` on desktop. The result was two frames in one suite: Suite management on `Shell20` on phones and the old frame on desktop, and VRMS on a third variant. You decided (scope note 2026-11-28) that VRMS takes the Suite management frame instead.

Open questions this left: what the sidebar keeps at its top and bottom, whether the breadcrumb leaves `PageHeader`, what the VRMS switcher lists, who sees it, what the avatar menu holds, what happens to the phone Account tab, and where the feature 28 bell goes.

### Options considered

**A. VRMS takes the Suite management frame (chosen).** One frame for both apps, already designed, drawn and built once.
- Pros: the suite reads as one product; the boards and the portal's built code exist, so VRMS copies rather than designs; the top bar gives the bell a natural place.
- Cons: rework of steps 1 and 4; 64px of height on every VRMS page; two copies of the switcher to keep in step.

**B. Keep spec 0027's sidebar frame and ask the portal to match (as built in `f6e4985`).** 
- Pros: no rework in VRMS; the sidebar holds everything, no top bar height.
- Cons: throws away spec 0019's picked and built `Shell20` and `Switcher16` (picked over many rounds); the bell has no good place; the switcher hides in a dark sidebar menu, where the suite's other surfaces put it top right.

**C. Each app keeps its own frame.**
- Pros: no rework at all.
- Cons: people who move between VRMS and Suite management find the avatar and the switcher in different places; the board comparison can't pass for both.

### Rationale

A wins because the frame was already a deliberated pick (spec 0019 rounds 13 to 23) and is already in code, so VRMS reuses rather than invents, and the suite gets one mental model: where you are on the left of the top bar, where else you can go and who you are on the right.

The sub decisions, your picks on 2026-11-28:
- **Sidebar top: the title with the role line**, as Suite management's (spec 0019 AC-17). The role used to sit in the account menu row; with that row gone, the title line is where `Shell20` puts it. New repair stays under it, because it is VRMS's most frequent action and the top bar would get crowded beside the bell, grid and avatar. Runner up: the title with "Vehicle repairs", which loses the role from the desktop view.
- **Sidebar bottom: the `Shell20` footer strip** (option 5), for parity; a bare collapse row would be the one difference between the two shells.
- **Breadcrumb in the top bar, system first** ("VRMS › Repair tickets › Waiting for sign off"), matching "Suite management › Users". Keeping it in `PageHeader` too would show two breadcrumbs. Runner up: page first, shorter, but unlike Suite management.
- **Switcher: VRMS first and ticked, then BMS and VMMS, then Suite management.** The current place on top mirrors the portal's switcher (Suite management first there); the rest keep the launcher's BMS, VMMS order. Suite management is last because it is an admin's side door, as on the launcher where its tile comes after the systems. The switcher reads the roles VRMS already holds and the catalog it already loads, so no new route and no cross repo change. Runner up: strict launcher order, where the ticked card moves around.
- **Who sees it: spec 0007's rule, unchanged.** A VRMS only mechanic has no launcher (spec 0019 AC-5 sends them straight in), so a grid with one ticked card and Home is the "menu with one choice" `Switcher16` rejected.
- **Avatar menu: Your profile and Sign out** (spec 0019 AC-19), the role being in the sidebar title.
- **No Account tab on phones.** The avatar is in the top bar at every size, as in the portal, whose bottom bar holds only views. This frees a tab, so someone with Analytics but no Admin page now gets the tab bar.
- **The bell left of the grid** (bell, grid, avatar), the order Google and Atlassian use for notifications beside the app switcher and account. Settled now so feature 28 doesn't reopen the shell; nothing is drawn until it ships.

Choices made without asking, with the reason:
- VRMS copies the portal's **built** values, not the boards', where they differ (64px bar, not 56px), so the two apps match each other.
- The breadcrumb's last crumb on a record comes from the page through a small context (`useBreadcrumbTail`) rather than a route table, because only the page knows the ticket number once it loads.
- The system icons, one lines and the ///L mark are copied from the portal, with no drift checker: three small constants and one icon. Runner up: a checker like `check-scenes.mjs`, more than this needs.
