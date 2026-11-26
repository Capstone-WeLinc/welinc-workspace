# Crew details redesign and vehicle documents removal: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Two requests for the Vehicle & Team Availability details modals, kept in one spec as the team prefers for UI batches:

1. Rearrange and redesign the contents of the Driver details and Helper details modals.
2. Remove the Documents section from Vehicle details and drop anything related in the database, after checking whether VMMS keeps vehicle documents such as registration and insurance expiry.

## Options considered

### Crew details layout

- **Summary tiles plus two-column sections, like Vehicle details** (chosen). Pros: the three modals read the same way; the most-asked facts (truck, license status, contact) are visible without scrolling; the empty space left by the join-date removal is used. Cons: a slightly wider modal (760px instead of 640px).
- Keep one column and just reorder. Cons: the driver modal stays long and the helper modal stays mostly empty.

Tile choices: "Assigned truck" was missing from the modal although the card shows it, so it leads. The driver's second tile is the license *status* (coloured) rather than the license type, because status is what blocks dispatch; the type moved into the role line.

### Vehicle documents

- **Remove from the UI and types only** (chosen). Neither VMMS nor BMS stores registration or insurance dates, so nothing exists to migrate or drop.
- Ask VMMS to add the fields and keep the section. Cons: that's another group's system and not what was asked; the section would stay empty until then.
- Keep the section. Cons: it can only ever say "Not recorded".

### License expiry badge (added later)

- **Date only in the License section** (chosen by the team). The coloured License tile in the summary already says Valid / Expiring soon / Expired, so the badge beside the date repeated it.

## Rationale

- Checking VMMS first, as the team asked, showed there is no source for these dates anywhere in the suite, so the section was dead UI. Removing the fields from the types stops anyone wiring them up by mistake.
- No database change is safer than a speculative one: no BMS column ever held these values.
- If VMMS ever adds vehicle documents, BMS can show them again by reading them from the VMMS fleet API.
