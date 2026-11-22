# VRMS design rules

VRMS specific design rules for `welinc-web-vrms`, on top of the suite design direction in the root [design.md](../../../design.md). Where the two disagree for a VRMS screen, this file wins. Token values live in `welinc-web-vrms/src/index.css`.

## Who it is for

Mechanics work from a phone on the garage floor; Admin and office staff work on laptops. Mechanic screens are designed at 375px wide first, Admin screens at 1280px first. On phones the sidebar becomes a bottom tab bar for mechanics and a sheet menu for Admin.

## Hot counts

The suite's gold "needs you" mark goes only on these counts (never on a count of 0):

| Count | Hot for |
|---|---|
| Tickets waiting for sign off (`FOR_VERIFICATION`) | Admin, Chief mechanic |
| Tickets sent back to me | Mechanic |
| Fix library suggestions to review | Roles that can edit the fix library |

## Ticket status colors

Every status pill follows the suite shape (`BadgePill`). Five color groups cover the nine ticket statuses; the token names are the group names.

| Group | Ticket statuses | Style (tokens) |
|---|---|---|
| Waiting | Open, Assigned, On hold, Pending approval | amber tint, amber 800 text (`status-pending-bg` / `-fg`) |
| Working | In progress, Outsourced | navy tint, `primary` text (`status-in-progress-bg` / `-fg`) |
| Needs sign off | For verification | violet tint, violet 800 text (`status-for-verification-bg` / `-fg`; the one allowed extra hue: it marks "needs Admin") |
| Finished | Closed | emerald tint, emerald 800 text (`status-completed-bg` / `-fg`) |
| Stopped | Cancelled | slate tint, slate 600 text (`status-cancelled-bg` / `-fg`, also used for any unknown value) |

**Charts that show statuses** (the dashboard pipeline, the analytics status breakdown) color each status with its group's text color (`--status-pending`, `--status-in-progress`, `--status-for-verification`, `--status-completed`, `--status-cancelled`), so a status looks the same in a pill and in a chart. `chart-1` to `chart-5` are only for series that are not statuses (spend, counts, garages).

## Priority badges

Critical uses solid `destructive`, High a soft gold tint (`highlight/25`, `highlight-foreground` text), Medium and Low use `secondary` with `muted-strong` text. Solid gold is not used for pills: other gold pills (Returned, Unlocked) take the same soft tint. This is for badges only. A priority picker is a suite `ChoiceChip`, with the priority color shown only as a small dot beside the label.

## Plate chip

`PlateChip` is VRMS's one product signature. A truck's plate in `font-mono` 600 uppercase `text-body`, `foreground` text on `card`, a 1px `input` border, `rounded-sm`, `h-6 px-2`. No color, so it never competes with status or priority. Used wherever a truck is named: list rows, phone cards, the ticket title, the dashboard lists and the vehicle picker. `rounded-sm` is reserved for it.

## Naming a ticket

People name a truck by its plate ("the Isuzu with NDG 5821"), not by its ticket ID. So the plate leads and the ID is metadata.

- **Order:** plate chip, then make and model, then the status pill. The ticket ID (`REP-20261030-5EBC`, in `font-mono`) goes on a smaller `muted-foreground` line below, with the garage.
- **Ticket title** on the detail page: the plate chip and the main issue; the ID sits alone under the title (the garage shows in Details, not the header).
- **IDs never break mid ID.** Use `whitespace-nowrap` on the ID, and let the line wrap before it.

## List rows

- **Desktop table:** first column is the truck (plate chip, make and model, ID below). The issue column wraps to 2 lines (`line-clamp-2`) and is the widest column, because it is what you decide on. Priority shows as a badge. Then status, mechanic, and dates.
- **Phone card:** line 1 plate chip and status pill, line 2 the issue (2 lines max), line 3 priority badge, mechanic and due date in `text-caption` `muted-foreground`, ID last. The card is a `divider` row inside the list, not a card inside a card.
- **Filters on phones:** search stays visible; the other filters fold into one "Filters" button with a count of active filters, so the first ticket shows in the first screen.

## Detail page order on phones

Below 768px, a ticket reads top to bottom in the order you decide: issues and what fixed them, then costs, then people, then details and activity. The primary action lives only in the fixed bottom bar on phones; the same button is not repeated in a card above it.

## Inside ticket cards

- Repeated items (issues on a ticket, cost lines, checklist steps) follow the suite rule: `divider` lines or a small heading, never a bordered box per item.
- Cancel ticket beside Verify and close follows the suite rule for destructive actions: in the `⋮` menu or a `destructive` button, never two filled buttons side by side.

## Tooling

- Confirm prompts go through the shared `confirm()` helper (an alert dialog centered at every size).
- `warning-text` stays a VRMS token beside the suite table.
