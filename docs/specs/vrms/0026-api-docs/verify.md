# Verify: API docs · spec 0026 · updated 2026-11-16
_Steps derived from spec 0026 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. Milestones 1 and 2 (welinc-auth) are built; the backend-vrms and workspace steps come with milestones 3 and 4._

## UI / manual (welinc-auth, local stack up)
- [ ] Open `http://localhost:3000/auth/docs` → the Scalar page lists every route except `GET /auth` (hello); search finds `POST /auth/token` → AC-1, AC-7
- [ ] Browser network log of that page → only same origin requests (`/auth/docs/scalar.js`, `/auth/docs/openapi.json`), nothing from jsdelivr, fonts.scalar.com or a proxy → AC-3
- [ ] Each route sits under one Title Case tag; `GET /auth/health` is under `Operations` → AC-4, AC-7
- [ ] `PATCH /auth/admin/users/{id}` shows 409 with `LAST_ADMIN`, `SELF_EMAIL` … "or no `code`", and 403 with `CSRF_REJECTED`, `NOT_ADMIN_OF_SYSTEM` → AC-4 (codes the code really answers, guard codes included)
- [ ] `POST /auth/token` shows its 400 and 401 in the OAuth shape (`invalid_grant`, `unsupported_grant_type` …) and its 403 coded (`NO_SYSTEM_ACCESS`, `APP_NOT_ALLOWED`) → AC-4
- [ ] `POST /auth/mobile/login` 200 shows two shapes (the token body and the email code step); its 429 shows both `CODE_SEND_LIMIT` and OAuth `rate_limited` → AC-5, AC-4
- [ ] `GET /auth/systems` and `GET /auth/permissions/{system}` show a 304 with no body, the `ETag` reply header and the `If-None-Match` request header → AC-5
- [ ] Get a user access token (VRMS sign in), paste it in Scalar's auth panel, send `GET /auth/me` from the page → 200 with your account → AC-8
- [ ] From the page, send `POST /auth/admin/code` → 401 `NOT_SIGNED_IN` or 403 `CSRF_REJECTED` (the Origin check refuses the docs page); its description says so → AC-8
- [ ] `GET /auth/session` names `userToken`, not the SSO cookie → AC-8
- [ ] Only `GET /auth/health` still shows the generic "The input failed validation / No valid credentials / Not allowed for this caller" set → AC-4

## Commands (welinc-auth)
- [ ] `API_DOCS_ENABLED=false` in `.env`, restart → `/auth/docs`, `/auth/docs/openapi.json`, `/auth/docs/scalar.js` all answer the usual 404 → AC-2
- [ ] `API_DOCS_ENABLED` blank with `NODE_ENV=production` → same 404s; blank with `NODE_ENV=development` → served → AC-2, AC-12
- [ ] `npm run env:check` with `API_DOCS_ENABLED=maybe` → exits 1 naming it → AC-12
- [ ] `npm run openapi` twice → `git diff docs/openapi.json` empty (identical bytes), exit 0, no database needed (stop Postgres first) → AC-9
- [ ] Add a `@ApiProperty() extra!: string` to `SessionResponse` without regenerating → `npm run openapi:check` exits 1 with `run npm run openapi and commit docs/openapi.json` → AC-9
- [ ] Add a field to a fixture in `src/openapi/integration-replies.spec.ts` (for example `user.surprise` on the token reply) → `npm test` fails naming `reply.user.surprise is not in the schema`; drop a required field → fails naming it as missing → AC-6
- [ ] `npm test` → the 13 reply tests in `integration-replies.spec.ts` pass (12 routes, both branches of mobile login, token on `authorization_code`) → AC-5, AC-6

## Value sourcing checks
- [ ] JWKS keys in the docs carry exactly `kty crv x y kid alg use`, as `publicJwk` publishes → JWKS source row
- [ ] `/auth/directory/users` docs mark `next` and `phone` nullable; `/auth/directory/changes` marks `next` never null → directory source row
- [ ] `/auth/permissions/{system}` shows `grants` as a map of role code to key lists (not looked into by the reply test) → matrix source row
- [ ] `info.title` is `WeLinc auth API`, `info.version` is `0.0.1`, and the description links contract 0001 → info rows
- [ ] Scalar "Try it" on staging sends to the page's own origin (`servers: [{ url: '/' }]`), never to a proxy, and the pasted token is gone after a reload → Try it out rows

## Contract and workspace (milestone 3, added 2026-11-16)
- [ ] `node scripts/check-contract-routes.mjs welinc-auth/docs/openapi.json` → `ok: all 86 rows of contract 0001 section 16 are documented`, exit 0 → AC-10
- [ ] Drop `DELETE /auth/me/sessions/{sid}` and the 200 schema of `GET /auth/systems` from a copy of that file and run the script on it → exit 1, one `missing:` line and one `no reply schema:` line; add a path with no row → a `note:` line that doesn't fail → AC-10
- [ ] Section 16 has 12 `yes` rows under *Reply schema*, exactly the AC-5 integration routes → AC-10, AC-5
- [ ] With `AUTH_REPO_READ_TOKEN` unset, the `contract-routes` job on a workspace PR fails at "AUTH_REPO_READ_TOKEN is set" with the named message; with it set, it checks out welinc-auth `development` and passes. Run it once by hand (Actions, Run workflow) → AC-11
- [ ] The workspace `infra` job compiles `infra/env.bicep`; `az bicep build` output shows `API_DOCS_ENABLED` `true` for staging and `false` for prod on both apps (`apply.sh staging --what-if` and `prod --what-if`) → AC-2
- [ ] `docs/integration/README.md`, `move-vmms.md` and `move-bms.md` link `/auth/docs` and the committed file → AC-1

## backend-vrms (milestone 4, added 2026-11-16, local stack up)
- [ ] Restart `welinc_vrms_backend` (it needs `npm ci` for the new packages, so rebuild with `-V`), open `http://localhost:3000/vrms/docs` and `http://localhost:3002/vrms/docs` → the Scalar page lists every route with one tag each (`Repair Tickets`, `Operations`, `Session` and so on); `GET /` is absent; `/vrms/docs/openapi.json` equals the committed `docs/openapi.json` → AC-1, AC-4, AC-7
- [ ] The page's network log shows only same origin requests (`/vrms/docs/scalar.js`, the JSON), no jsdelivr or fonts → AC-3
- [ ] `API_DOCS_ENABLED=false`, restart → `/vrms/docs`, `/vrms/docs/openapi.json` and `/vrms/docs/scalar.js` answer 404; `NODE_ENV=production` with it blank, the same → AC-2
- [ ] Paste a token from a signed in VRMS session into Scalar's auth panel, send `GET /vrms/repairs` → 200 with your tickets; `POST /vrms/session/refresh` from the page → 403 `CSRF_REJECTED`, and its description says so → AC-8
- [ ] `npm run openapi` twice → identical bytes; change a DTO without regenerating → `npm run openapi:check` exits 1 with the hint; CI runs it after the build → AC-9
- [ ] `npx jest src/openapi` → 6 pass; add a field to the fixture in `ticket-replies.spec.ts` or remove one from `repairs.response.ts` and regenerate → the test fails naming the field → AC-5, AC-6
- [ ] `API_DOCS_ENABLED=maybe npm run env:check` → `API_DOCS_ENABLED: must be true or false`; blank and `true` pass → AC-12
- [ ] The ticket replies come from `RepairsService.formatTicket` and `present`: a caller without the total cost permission gets no `isLumpSum` or `repairParts`, and the schema marks them optional → Value sourcing, the four VRMS ticket replies

## Acceptance-criteria coverage
- AC-1 … the first UI step and both docs page steps · AC-2 … the first two command steps, the Bicep step and the backend-vrms switch step · AC-3 … both network log steps · AC-4 … the tag, error code and generic set steps · AC-5 … the mobile, 304 and test steps, the `yes` rows and the ticket test step · AC-6 … the drift and test steps, the ticket test step · AC-7 … the first and tag steps, `GET /` absent · AC-8 … the token, CSRF and session steps, the VRMS token step · AC-9 … the two `openapi` steps in each repo · AC-10 … the three contract steps · AC-11 … the CI job step · AC-12 … the `env:check` steps in each repo
