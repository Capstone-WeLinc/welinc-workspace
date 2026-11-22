# 0018. Verify: Roles page and custom roles

Run at `/check verify roles page` (child 0001) and `/check verify custom roles` (child 0002), locally, with the shared and VRMS stacks up and the seed accounts (`docs/integration/seed-accounts.md`). Never use a real email address. Major flows first.

## Board comparison (child 0001, AC-19), no screenshots

1. Read the board source from [boards/](boards/) (`Roles9`, `DraftMarks`, `SaveBar9`, `Picks8`, `Confirm6`; copies of the canvas boards, so any account works). Pull each element's values from the markup and its script: text, font size and weight, colors, gaps, paddings, radii, shadows, and the states its controls show.
2. Open the built page at 1280px with Playwright and take one `browser_snapshot` (structure and wording) and one `browser_evaluate` that returns `getComputedStyle` for the same elements (list pane, role row, draft bubble, header tile, name, chip, facts, tabs, group header, permission row, switch, save bar, change list, review dialog, delete dialog).
3. List every difference. Allowed only: (a) IBM Plex instead of the boards' Inter, Inter Tight and JetBrains Mono (spec 0016 F1); (b) spec 0016 token values that changed after the boards (`muted-foreground` `#5b6779`, `destructive` and `error` `#b42318`, `background` `#f3f5f9`, its radius and shadow tables); (c) shadcn based parts with their spec 0016 styles; (d) real data lengths. Also expected, decided after the boards: descriptions under labels, the "Find a permission" field, no Rename or Delete on built in roles, no Reset to defaults on custom roles. Anything else is a bug to fix before the PR.

## Major flows, child 0001

- [ ] `suite.admin@` opens Roles: VRMS, VMMS, BMS switch; Chief mechanic shows its header, facts, tabs and the first group open with descriptions (AC-1 to AC-4)
- [ ] Change one switch on Chief mechanic and one on Mechanic: two draft bubbles, "2 unsaved changes in 2 roles", the change list grouped by role (AC-7, AC-8)
- [ ] Review: a removal opens the note as required and Save stays disabled until it's filled; save; both roles' History tabs show the change with the note (AC-9, AC-11, AC-15)
- [ ] Leave for People and come back: the toast, then "Kept from [time]" (AC-12)
- [ ] Stale save from a second browser: the warning toast and only still valid entries kept (AC-11)
- [ ] Reset to defaults on a changed built in role stages the differences (AC-10)
- [ ] "Find a permission" with "cost" (AC-5)
- [ ] `vrms.admin@`: On and Off text, no bar, Add people works; moving the last admin answers the `LAST_ADMIN` message and nobody moves (AC-6, AC-13, AC-14)
- [ ] `bms.admin@`: only the People tab with the help line (AC-3)
- [ ] Download as spreadsheet: one row per permission (28 for VRMS), the People row, one column per role; a role named "=SUM(1)" stays text (AC-16)
- [ ] `/admin/permissions?system=VRMS` lands on `/admin/roles/VRMS` (AC-1)
- [ ] Phone width (375px): list and role are separate screens; keyboard pass and one axe pass (AC-1, AC-18)

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
