# BMS integration checklist

Requirements: [Move BMS](../../integration/move-bms.md), suite spec 0014.
Design: [BMS spec](../../specs/bms/0001-shared-services-integration/index.md).
Evidence: [verification record](verification.md), 16 November 2026.

Implementation is complete on the BMS side. Cross-system acceptance and delivery
remain open. An implemented item below is not a claim of shared-lead sign-off.

| Lead checklist section | Status | Implementation / evidence |
|---|---|---|
| 1. Stack and keys | Implemented locally; PR pending | BMS Compose, seven Node 24 Dockerfiles, owned databases, generated local BMS client key, migrations and repeatable seeds. Shared setup's operational steps were executed; clone/PR steps do not apply to these plain source copies. |
| 2. Environment | Implemented | One backend root identity/configuration, generated dedicated internal/tracking secrets, documented variable names, required boot checks, browser API/portal names. Analytics root identity overrides standalone defaults. |
| 3. NestJS gateway | Implemented; tested | Port 3020, explicit route ownership, unchanged bearer forwarding, raw streams, 10 MB limit, request IDs, cookie parser, trusted proxy setting, health for all five upstreams. No auth proxy or database code. |
| 4. Token checks | Implemented; tested | Full VRMS verifier and tests copied/adapted into all five person-facing services; ES256, BMS audience, session/account confirmation and role checks. Wrong audience is covered by unit tests; shared live VRMS-token case awaits VRMS runtime. |
| 5. Session routes | Implemented; tested | Reference BMS session routes/cookies, PKCE, CSRF, refresh, APP_NOT_ALLOWED, expiry, shared sign-out and deep-link restoration. Real portal browser test passed. |
| 6. Names and activity | Implemented; local checks passed | Directory-based approval/audit names, own work feed, direct shared account/profile feeds, admin confirmation handling, one-use deletion reauthentication, temporary-role filtering and daily crew erasure sync. Actual account erasure was not performed. |
| 7. Drivers and trucks | BMS implemented; fleet acceptance pending | Owned drivers/helpers and vehicle profiles, preserved slot index, 12/20 crew links, VMMS service-token consumer, 30-second list cache, fresh assignment reads, explicit 409/503 and unavailable labels. Current VMMS checkout lacks the fleet API. |
| 8. Analytics | Implemented; local checks passed | Separate PostgreSQL read model/report storage on 5437, API 3025, projection 3024, dispatch resource forwarding, no foreign/auth database mappings. Live report storage test passed. |
| 9. Web app | Implemented; tested | Portal login/recovery, in-memory credentials, reference refresh/idle/tab behavior, Switch system, portal account management, separate crew page, profile/deletion APIs, public tracking, port 8003. |
| 10. Seed people | Implemented; verified | Three byte-identical manifest copies; official seed checker passed; repeatable crew seed preserves edits and creates no auth accounts. |
| 11. Prove it | Local verification passed; suite acceptance pending | Static 3/3; builds, unit/contract/UI/browser tests passed. Local suite login slice: 15 passed, one external VRMS-runtime prerequisite failed. Full lead run and live fleet workflow remain open. |
| 12. PRs and sign-off | Awaiting leads | No Git repositories were created in the BMS source copies. Lead arranges coordinated PR delivery, written confirmation, cross-system checks, scope ticks and remote legacy-repo archive. |

## Remaining acceptance gates

- [ ] VRMS backend/session runtime available so the shared checker can obtain a
  real VRMS user token and test rejection at BMS.
- [ ] VMMS fleet API available: verify service-token-only access, plate parity,
  assignment freshness, unavailable/deleted vehicles and concurrent slot conflict.
- [ ] Run a representative booking → dispatch → completion/payment workflow
  against real VMMS fleet resources and verify populated analytics projections.
  Existing dispatch workflow regressions pass with controlled providers; current
  live BMS databases contain no booking/assignment fixtures.
- [ ] Shared services lead runs the full unchanged checker with every required
  line `ok`, and posts its output on the coordinated delivery PRs.
- [ ] BMS group lead confirms completion in writing; shared lead records login
  and fleet acceptance separately.
- [ ] Leads arrange the source-repository handoff/PRs and archive the old remote
  backend only after the prescribed checks pass. The user already deleted the
  local `bms-legacy` folder.

## Scope

Application changes are confined to the three BMS code folders, the BMS Compose
file, and BMS-owned docs/specs. At the client's request, completion boxes and
evidence notes in `docs/integration/move-bms.md` are also updated. Shared and
other groups' application source and the shared checker were not edited. Shared runtime setup
used its shipped key/migration/seed tools and ignored configuration/dependencies.
Unrelated Docker projects and their volumes were left alone.
