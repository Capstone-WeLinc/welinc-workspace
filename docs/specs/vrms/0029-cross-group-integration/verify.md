# Verify: cross group integration · spec 0029 · updated 2026-11-27
_Steps derived from spec 0029 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. Milestone 1 (shared setup and plumbing) below; later milestones append their own sections._

## Milestone 1: shared setup and plumbing

### Commands
- [ ] In welinc-auth, `npm run catalog:sync -- --dry-run` after a sync says "VRMS permissions: no changes" → AC-26
- [ ] `oauth_clients.service_scopes` for `vrms`, `vmms` and `bms` holds exactly the scopes in the umbrella's *Auth grants* table, nothing more → AC-26
- [ ] `POST /auth/token` (client credentials) as `vrms` for audience `VMMS`, scope `fleet.repair-status.write` answers a token; as `vrms` for audience `VRMS` answers `invalid_target` → AC-26
- [ ] As `bms`, ask for audience `VRMS` scope `repair.referral.write`: refused `invalid_scope` (only `vmms` holds it) → AC-26
- [ ] The portal's Roles page lists "Answer other systems" under Tickets for VRMS, on for Admin, off for Chief Mechanic and Mechanic → AC-11
- [ ] `docker exec welinc_vrms_backend npx prisma migrate status` says up to date, and `\d referrals`, `\d deliveries` show the tables; `repair_tickets.driver_id` is nullable with its foreign key still `ON DELETE RESTRICT` → AC-1, AC-6, AC-13, AC-21
- [ ] `curl -i http://localhost:3000/vrms/integrations/anything` answers with `Cache-Control: no-store`, also on a 401 or 403 once a route exists → AC-24
- [ ] With `SUITE_GATEWAY_INTERNAL_URL` unset, backend-vrms refuses to start with "SUITE_GATEWAY_INTERNAL_URL: is required" → AC-21
- [ ] Settings, Integration shows "Keep retrying a message for" (24 hours, 1 to 168), "Keep sent messages for" (90 days, 7 to 365) and "Full truck and garage check every" (60 minutes, 15 to 1440) → AC-3, AC-21, AC-23

### Worker, live (VMMS stopped locally, so the gateway answers 502)
- [ ] Insert a `REPAIR_EVENT` delivery for a real ticket: within 15 s it is `PENDING` with `attempts` 1, `last_status_code` 502, `last_error` `UPSTREAM_UNAVAILABLE`, next attempt 30 s after the last → AC-21
- [ ] Set `integration.retryWindowHours` to 1 and backdate `first_attempt_at` by 2 hours: the next attempt makes the row `FAILED` → AC-21 (value source: the setting, not a constant)
- [ ] Insert a second row for the same ticket: it stays at `attempts` 0 while the first is `PENDING`, and while it is `FAILED`; once the first is `DISMISSED` the second is sent → AC-21
- [ ] Two rows inserted in one transaction for one ticket are sent in `seq` order → AC-21
- [ ] With VMMS running and accepting, a sent `REPAIR_EVENT` carries `eventVersion` one above the ticket's `vmms_event_version`, the row ends `SENT`, and the ticket's `vmms_event_version` moves while its `updated_at` does not → AC-13, AC-21
- [ ] Stop welinc-auth: a due row stays `PENDING` with `last_error` `AUTH_UNAVAILABLE` and no status code, and nothing is posted → AC-21

### Guard (once the first `/vrms/integrations` route lands in milestone 2)
- [ ] A person's token answers 403 `WRONG_TOKEN_USE`; a `bms` service token on a `vmms` only route answers 403 `FORBIDDEN` "This route does not accept calls from this service" → AC-24

## Acceptance criteria coverage (milestone 1)
- AC-11: the Roles page step (the route checks come with milestone 2)
- AC-21: the worker steps and the env check
- AC-24: the no-store step and the guard step
- AC-26: the catalog, registry and token steps (staging's `seed:clients` and `catalog:sync` are milestone 5)
