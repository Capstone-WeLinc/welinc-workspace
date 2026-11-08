# Verify: user directory for systems · spec 0005 · updated 2026-11-09
_Steps derived from spec 0005's acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Helpful setup: a VRMS service token comes from VRMS's own client (the `DIRECTORY_TOKENS` client in backend-vrms). A small script run inside `welinc_vrms_backend` with `NestFactory.createApplicationContext(AppModule)` can fetch one and call welinc-auth at `AUTH_INTERNAL_URL`. Feed rows are easiest to read with `psql` in `welinc_auth_db`.

Already checked during the build (2026-11-09, local stack): the migration applied with no Prisma drift, the backfill wrote 73 rows, a rename reached the VRMS roster on the next tick, losing the VRMS role set the row inactive with its last role kept, getting it back reactivated it, the lookup answered roles for VRMS only with `phone: null` and put unknown and other system ids in `missing`, a service token on `/auth/users` got 403, `limit=0` got `VALIDATION_FAILED`, `after=abc` got `INVALID_CURSOR`, and the recovery sync ran.

## UI / manual
- [ ] Sign in to VRMS as an admin, open the Users page → the network panel shows no `POST /vrms/mechanics/sync` → AC-20
- [ ] Open New repair as an admin → no `POST /vrms/mechanics/sync` → AC-20
- [ ] On the Users page, add a mechanic → one `POST /vrms/mechanics/<new id>/refresh` answers 200, and the New repair picker lists them at once → AC-18, AC-20
- [ ] Edit a mechanic's name, then deactivate and reactivate them → each save calls the refresh route for that person's id, and the picker follows at once → AC-20
- [ ] Stop welinc-auth's container, then save on the Users page (the save itself fails while auth is down, so instead block only the refresh, for example with the browser's request blocking on `*/refresh`) → the save stays, and the warning toast reads "Saved, but VRMS couldn't update its mechanic list. It will catch up within a minute." → AC-20
- [ ] In the portal (or welinc-auth's admin routes), give someone the VRMS Mechanic role → within about 30 s they appear active in VRMS's picker without opening the Users page → AC-2, AC-5, AC-12, AC-13
- [ ] Edit your own profile name in the portal while you hold a VRMS mechanic role → VRMS's roster shows the new name within about 30 s → AC-3, AC-12

## Commands
- [ ] `docker exec welinc_auth_service npm run test:db` → 21 passing, including the 15 feed tests (every write path, no row for no change, rollback, hard delete, seed rerun, last role lost, late commit) → AC-1, AC-2, AC-3, AC-5
- [ ] `npm run test` in welinc-auth → the directory suite passes (cursors, inputs, mapping, guard, rate limit, `/auth/users` without a service scope) → AC-4 to AC-9
- [ ] `npm run test` in welinc-backend-vrms → `directory-sync.service.spec.ts` and `mechanic-roster.service.spec.ts` pass → AC-12 to AC-18
- [ ] `docker exec welinc_auth_service npx prisma migrate diff --from-config-datasource --to-schema prisma/schema.prisma --script` → "This is an empty migration." → AC-1
- [ ] `docker exec welinc_vrms_backend npx prisma migrate diff --from-config-datasource --to-schema prisma/schema.prisma --script` → empty, and `SELECT * FROM directory_sync_state` shows one row `auth` → AC-11
- [ ] Run `npm run seed` in welinc-auth twice on a throwaway copy of the database (it wipes users the seed does not make) → the second run adds no `directory_changes` rows → AC-3
- [ ] With a VRMS service token: `GET /auth/directory/users?limit=2` → 2 users ordered by id, `next` set, `changesCursor` set; follow `next` to the end → the last page has `next: null`; `cursor=abc` → 400 `INVALID_CURSOR` → AC-4
- [ ] `GET /auth/directory/changes` with no `after` → starts at the backfill; `limit=1` → `hasMore: true` and `next` equals the change's cursor; a page shorter than `limit` → `next` is the safe point, so asking again from it returns no rows → AC-5
- [ ] Take a valid cursor, change its epoch part (decode, swap the uuid, encode) → 400 `INVALID_CURSOR` → AC-5
- [ ] `limit=0` and `limit=501` on each of the three routes → 400 `VALIDATION_FAILED` → AC-5
- [ ] `POST /auth/directory/users/lookup` with a VRMS mechanic, a BMS only admin, a random uuid and a soft deleted VRMS person → the mechanic and the deleted person (with `deleted: true`) in `users`, the other two in `missing` → AC-6
- [ ] Lookup with 0 ids, 201 ids, a repeated id, a non uuid, or an extra field → 400 `VALIDATION_FAILED` → AC-6
- [ ] Lookup someone who lost their only VRMS role → returned with `roles: []` → AC-6
- [ ] Compare one user across `/users`, `/changes` and `/lookup` → the same `DirectoryUser` shape, roles for VRMS only, `phone: null` for the VRMS client, `phoneVerified: false`, `picture` as stored → AC-7
- [ ] A person's (admin's) token on each directory route → 403 `FORBIDDEN`; no token → 401; 121 calls inside a minute from one client → 429 `RATE_LIMITED` with `Retry-After` → AC-8
- [ ] A service token on `GET /auth/users` → 403 `WRONG_TOKEN_USE`; an admin's token there still works → AC-9
- [ ] Open contract 0001 sections 9, 10 and 12 and the gap map → they carry the safe point, one change per user per transaction, the backfill, `INVALID_CURSOR` after a restore, `phoneVerified` false until S8, and `/auth/users` for admins only → AC-10 (open: owed to `/architect`)
- [ ] Set `directory_sync_state.cursor` to null → the next tick runs the full read and saves a new cursor; a mechanic row whose person is no longer in VRMS goes inactive → AC-12
- [ ] Stop welinc-auth for three ticks (about 90 s) → backend-vrms logs exactly one warning and sets `failing_since`; start it again → one line "welinc-auth's directory is back after N s" and `failing_since` is null; VRMS requests meanwhile still work for cached sessions → AC-15
- [ ] Set `lease_until` to an hour from now with another `lease_owner` → ticks do nothing and log nothing; `POST /vrms/mechanics/sync` → 409 `SYNC_RUNNING`; clear the lease → the sync answers `{ created, updated, deactivated }` → AC-16, AC-17
- [ ] Run two backend-vrms copies against the same database (or two ticks at once) → only one claims the lease per tick → AC-16
- [ ] `POST /vrms/mechanics/<random uuid>/refresh` → `{ mechanicId: null }`; with welinc-auth stopped → 503 `AUTH_UNAVAILABLE`; `/vrms/mechanics/abc/refresh` → 400 → AC-18
- [ ] Release a departed mechanic's tickets on the Users page (deactivate with release) → still works, now through the lookup → AC-18
- [ ] Sign in as a mechanic whose name changed in welinc-auth → their row updates on that first request, as before → AC-19
- [ ] `grep -rn "auth/users" welinc-backend-vrms/src` (skipping test files) → nothing → AC-21

## Value sourcing
- [ ] Caller's system: sign a service token for the `vmms` client and read `/auth/directory/users` → only VMMS people, roles VMMS only → caller's system from `oauth_clients.system`
- [ ] May see phone: a token with `directory.contact` (the `vmms` client's scopes) → `phone` filled; the VRMS client (no `directory.contact`) → `phone: null` → token `scope`
- [ ] Snapshot: change a user's `contact` → the feed row's snapshot shows the new value, and roles sorted by system then role → `users` and `user_roles` at commit
- [ ] Snapshot on a hard delete: hard delete a test user → the `deleted` row holds their old name and their last roles → `OLD` row plus the previous snapshot's roles
- [ ] Previous snapshot: two saves in one transaction → one row; the next save's type compares against that row, not an older one → latest row from another transaction
- [ ] Systems: move someone from VRMS to VMMS only → that row's `systems` holds both, so VRMS hears they left → new plus previous snapshot systems
- [ ] Type: run deactivate, activate, a roles change, a rename and a soft delete → `deactivated`, `activated`, `roles_changed`, `updated`, `deleted` in that order of rules → snapshot comparison, first match wins
- [ ] Epoch: the cursor's epoch equals `SELECT epoch FROM directory_feed` → `directory_feed.epoch`
- [ ] Which rows are safe: hold a transaction open in `psql` after a write, then commit another change elsewhere → neither appears in `/changes` until the first ends → `pg_snapshot_xmin`
- [ ] `next` on a short page: equals the safe point (decode it: its txid and seq match the newest safe row overall, even one for another system) → the safe point
- [ ] `changesCursor`: start the feed from the first page's `changesCursor` after making a change during the scan → that change arrives (perhaps twice) → safe point taken before the scan
- [ ] Once held a role: look up someone who left VRMS last month → returned with `roles: []`; someone who was only ever in BMS → `missing` → a feed row naming the system
- [ ] Lease owner: during a tick, `lease_owner` is a fresh uuid that differs between ticks → made by the claiming tick
- [ ] `phoneVerified`: false for everyone → decided until S8
- [ ] `updatedAt`: equals the user's `updated_at` in `/users` and `/lookup`, and the snapshot's `updatedAt` in `/changes` → column
- [ ] VRMS cursor: after each tick `directory_sync_state.cursor` equals the last change applied or the safe point → `directory_sync_state.cursor`
- [ ] Mechanic role: someone with both VRMS Mechanic and Chief Mechanic → their row stores `CHIEF_MECHANIC` → `roleOf`, Chief wins
- [ ] Whose row to refresh: create a user on the Users page → the refresh call uses the id from the create response → welinc-auth's save response

## Acceptance-criteria coverage
- AC-1 test:db migration tests, the Prisma diff command · AC-2 test:db write path tests, systems and type rows · AC-3 test:db write paths, the seed rerun, the portal profile step · AC-4 the `/users` paging step · AC-5 the `/changes` steps, epoch swap, limits, the late commit test · AC-6 the lookup steps · AC-7 the shape comparison, phone and caller's system rows · AC-8 the guard step · AC-9 the `/auth/users` step · AC-10 the contract step (owed) · AC-11 the VRMS Prisma diff · AC-12 the null cursor and portal role steps · AC-13 the picker steps · AC-14 the directory sync unit test (stop on failure) · AC-15 the auth down step · AC-16 the lease steps · AC-17 the recovery sync step · AC-18 the refresh steps · AC-19 the first request step · AC-20 the Users page and New repair steps · AC-21 the grep
