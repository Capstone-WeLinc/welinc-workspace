# Verify: Crew edit layout and Analytics & AI label

Checklist derived from [index.md](index.md). Tick only what was actually checked.

## Build

- [x] `npm run lint` (0 errors), `typecheck` and `build:prod` pass in `welinc-web-bms`.
- [ ] `npm test`: the 4 session test files fail to load (vitest "reading 'config'") on `development` too; not caused by this change.

## Web: Edit driver

- [ ] Cards in order: Profile, License, Emergency contact; no Work details card.
- [ ] Profile shows Full name, Email, Contact number, "Edit in portal", then Status under a divider.
- [ ] Changing Status and saving still works.

## Web: Edit helper

- [ ] Cards in order: Profile, Emergency contact.
- [ ] Status in the Profile card saves.

## Web: Sidebar

- [ ] Admin sidebar shows "Analytics & AI" and opens `/admin/reports`.
- [ ] `tests/ecosystem-screens.spec.ts` passes with the new label.
