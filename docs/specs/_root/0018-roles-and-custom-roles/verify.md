# 0018. Verify: Roles page and custom roles

Run at `/check verify roles page` (child 0001) and `/check verify custom roles` (child 0002), locally, with the shared and VRMS stacks up and the seed accounts (`docs/integration/seed-accounts.md`). Never use a real email address. Major flows first.

## Board comparison (child 0001, AC-19), no screenshots

1. Read the board source from [boards/](boards/) (`Roles9`, `DraftMarks`, `SaveBar9`, `Picks8`, `Confirm6`; copies of the canvas boards, so any account works). Pull each element's values from the markup and its script: text, font size and weight, colors, gaps, paddings, radii, shadows, and the states its controls show.
2. Open the built page at 1280px with Playwright and take one `browser_snapshot` (structure and wording) and one `browser_evaluate` that returns `getComputedStyle` for the same elements (list pane, role row, draft bubble, header tile, name, chip, facts, tabs, group header, permission row, switch, save bar, change list, review dialog, delete dialog).
3. List every difference. Allowed only: (a) Plex Mono instead of the boards' JetBrains Mono, and Inter instead of Inter Tight for headings (spec 0016, amended 2026-11-23); (b) spec 0016 token values that changed after the boards (`muted-foreground` `#5b6779`, `destructive` and `error` `#b42318`, `background` `#f3f5f9`, its radius and shadow tables); (c) shadcn based parts with their spec 0016 styles; (d) real data lengths. Also expected, decided after the boards: descriptions under labels, the "Find a permission" field, no Rename or Delete on built in roles, no Reset to defaults on custom roles. Anything else is a bug to fix before the PR.

Run 2026-11-26 (computed styles at 1280px against `Roles9` and `SaveBar9`): accepted differences, all from spec 0016 tokens and shared components: the type scale (tab 14px, group name 16px, blurb 14px, pills 12px), Plex Mono for the facts numbers and the Last changed date, the shared `RoleChip` and `Button` styles, and the system switch and Find a role sizes. Fixed: the permission row and group name at 52px, the group meter at 96px, the tab padding and gap.

## Major flows, child 0001

- [x] `suite.admin@` opens Roles: VRMS, VMMS, BMS switch; Chief mechanic shows its header, facts, tabs and the first group open with descriptions (AC-1 to AC-4)
- [x] Change one switch on Chief mechanic and one on Mechanic: two draft bubbles, "2 unsaved changes in 2 roles", the change list grouped by role (AC-7, AC-8)
- [x] Review: a removal opens the note as required and Save stays disabled until it's filled; save; both roles' History tabs show the change with the note (AC-9, AC-11, AC-15)
- [x] Leave for People and come back: the toast, then "Kept from [time]" (AC-12)
- [x] Stale save from a second browser: the warning toast and only still valid entries kept (AC-11)
- [x] Reset to defaults on a changed built in role stages the differences (AC-10)
- [x] Refused save: lock a cell in the catalog (or archive a custom role) after drafting a change on it, then save: the error toast names "[permission] for [role]" (or "[Role] was deleted…"), the entry leaves the draft, the rest stays (AC-11)
- [x] Network failure in review: stop welinc-auth, press Save: the dialog stays open with the error inline and Save enabled; start it again and save (AC-11)
- [ ] Kept draft on a deleted role: draft a change on a custom role, delete the role from a second browser, come back: "1 change to a role that was deleted was removed from your draft." and the other entries stay (AC-11, AC-12)
- [x] "Find a permission" with "cost" (AC-5)
- [ ] `vrms.admin@`: On and Off text, no bar, Add people works; moving the last admin answers the `LAST_ADMIN` message and nobody moves (AC-6, AC-13, AC-14)
- [x] `bms.admin@`: only the People tab with the help line (AC-3)
- [ ] Download as spreadsheet: one row per permission (28 for VRMS), the People row, one column per role; a role named "=SUM(1)" stays text (AC-16)
- [x] `/admin/permissions?system=VRMS` lands on `/admin/roles/VRMS` (AC-1)
- [x] Phone width (375px): list and role are separate screens; keyboard pass and one axe pass (AC-1, AC-18)

## Major flows, child 0002

- [ ] New role "Tire specialist" from Mechanic: toast, landing flash, opens on Permissions with Mechanic's values (AC-20, AC-23)
- [ ] Duplicate Chief mechanic: "Copy of Chief mechanic", Start from fixed (AC-21)
- [ ] "chief MECHANIC" refused as taken (AC-22)
- [ ] Rename and Edit description on the custom role; History shows both; built in roles have neither (AC-24, AC-26)
- [ ] Give "Tire specialist" to a mechanic through Add people; they sign in to web-vrms, work a ticket, appear in the assign picker; AI is refused after turning off "Use AI diagnosis" (AC-28, AC-32, AC-33, AC-36)
- [ ] Turn off "Can be assigned tickets" on it: the person leaves the picker within one sync (AC-33)
- [ ] The same person gets `APP_NOT_ALLOWED` from the shared mobile app; a Chief mechanic still signs in (AC-31)
- [ ] Delete with a holder shows the DB dialog; after moving them, delete archives it; History still reads (AC-25)
- [ ] VMMS shows no New role (AC-27)
- [ ] Before create ships: a VMMS person and a BMS person each holding a `C_` VRMS role use VMMS and BMS normally (AC-37)
- [ ] Copy from Admin: the New role dialog warns about team and settings (umbrella security model)

## API checks (curl through the gateway, cookie session or service token)

- [ ] `GET /auth/admin/roles/VRMS` answers the umbrella's shape; as `vrms.admin@`, `canEdit` is false; as `bms.admin@` for VRMS, 403 `NOT_ADMIN_OF_SYSTEM` (AC-17)
- [ ] `POST /auth/admin/roles/VMMS` answers 409 `CUSTOM_ROLES_NOT_SUPPORTED`; the 21st VRMS custom role answers 409 `CUSTOM_ROLE_LIMIT` (AC-22, AC-27)
- [ ] `DELETE` on a held role answers 409 `ROLE_IN_USE` with the count; on a built in role 400 `BUILT_IN_ROLE` (AC-25, AC-26)
- [ ] `GET /auth/systems` shows `builtIn` and no archived role; `/auth/permissions/VRMS` (service token) includes the custom role's grants (AC-29)
- [ ] `npm run catalog:sync` with a custom role held reports no change; a catalog code starting with `C_` is refused (AC-30)
- [ ] Restart welinc-backend-vrms with welinc-auth stopped: the roster is unchanged (AC-33)
- [ ] The roster parity test passes in welinc-backend-vrms (AC-33)
- [ ] `npm run openapi:check` in welinc-auth and `node scripts/check-contract-routes.mjs welinc-auth/docs/openapi.json` pass (AC-18, AC-36)

## Milestone 3 steps (child 0002, welinc-auth routes), added 2026-11-27

Run as `suite.admin@` with a portal cookie session (`Origin: http://localhost:8000`, `Content-Type: application/json`). Seen passing during `/develop` on 2026-11-27; `/check verify` runs them again and ticks them.

- [ ] `POST /auth/admin/roles/VRMS` `{name: "Tire specialist", from: "MECHANIC"}` → 201 with code `C_TIRE_SPECIALIST`, a cell for every VRMS key with Mechanic's saved values, and `version` one higher; `permission_changes` gets one row per cell, note "Created from Mechanic" → AC-23
- [ ] `GET /auth/admin/roles/VRMS/C_TIRE_SPECIALIST/history` → a single `CREATED` entry, the copied cell rows not listed one by one → AC-23
- [ ] Create refusals: "chief MECHANIC" and "tire SPECIALIST" → 409 `ROLE_NAME_TAKEN`; "!!" → "Use letters or numbers in the name."; "A" → "Name needs 2 to 40 characters."; a 40 character name passes and its code is at most 30; `from: "NOPE"` → 400 `UNKNOWN_ROLE` → AC-22
- [ ] `POST /auth/admin/roles/VMMS` → 409 `CUSTOM_ROLES_NOT_SUPPORTED` → AC-27
- [ ] As `vrms.admin@`: create, `PATCH` and `DELETE` → 403 `NOT_SUITE_ADMIN` → AC-22
- [ ] `PATCH …/C_TIRE_SPECIALIST` with a new name, then a new description → `RENAMED` and `DESCRIBED` events; a rename to "Mechanic" → 409 `ROLE_NAME_TAKEN`; an empty body → 400 `VALIDATION_FAILED`; `PATCH` or `DELETE` on `MECHANIC` → 400 `BUILT_IN_ROLE` → AC-24, AC-26
- [ ] Give the role to 2 people, then `DELETE` → 409 `ROLE_IN_USE` with `details.count` 2; move them off, `DELETE` → 200, `deleted_at` set, cells removed and logged with after null, version raised; `DELETE` again → 404 → AC-25
- [ ] After the delete: giving the archived code through `PATCH /auth/users/:id`, `attachExisting` and a temporary grant each answer 400 `UNKNOWN_ROLE`; `GET /auth/systems` doesn't list it → AC-29
- [ ] Create "Tire specialist" again → code `C_TIRE_SPECIALIST_2` (a code is never reused) → AC-22
- [ ] A person in their deletion grace period holding the role doesn't block `DELETE`; restoring them drops the archived role and records `RESTORED` with the role change → AC-25
- [ ] Not yet run: 20 live custom roles, then the 21st create → 409 `CUSTOM_ROLE_LIMIT` with "VRMS has 20 custom roles, the most it can have. Delete one to make another." → AC-22
- [ ] Not yet run: a `DELETE` and an Add people on the same role fired at once (two shells, `&`), ten times: each round ends with either `ROLE_IN_USE` or `UNKNOWN_ROLE`, never an archived role still held → AC-25
- [ ] AC-37 (passed 2026-11-27): `multi.lead@` with `C_NIGHT_SHIFT_LEAD` in VRMS gets the same answers from 13 VMMS routes, 15 BMS routes and both web apps as with `CHIEF_MECHANIC`, and no backend logs an error → AC-37
- [ ] `vmms-mobile` client still allows only MECHANIC and CHIEF_MECHANIC for VRMS (`prisma/seeds/clients.seed.ts` unchanged) → AC-31
- [ ] `npm run openapi:check` in welinc-auth and `node scripts/check-contract-routes.mjs welinc-auth/docs/openapi.json` pass; contract 0001 reads version 8.1 → AC-29

### Coverage, milestone 3
- AC-22: name rules, taken, limit (open), suite admin only · AC-23: create copy and logs · AC-24, AC-26: rename, describe, built in refusals · AC-25: in use, archive, grace period, race (open) · AC-27: VMMS refusal · AC-29: archived role unknown everywhere, contract 8.1 · AC-31: mobile client unchanged · AC-37: other systems tolerate a `C_` code
- Note: the umbrella's `peopleCount` line says Delete counts every holder row, but AC-25 and the rules line say grace period holders don't block. The build follows AC-25; the umbrella line is owed a fix in `/architect`.
