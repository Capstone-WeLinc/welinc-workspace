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

## Acceptance-criteria coverage
- AC-1 … the first UI step · AC-2 … the first two command steps · AC-3 … the network log step · AC-4 … the tag, error code and generic set steps · AC-5 … the mobile, 304 and test steps · AC-6 … the drift and test steps · AC-7 … the first and tag steps · AC-8 … the token, CSRF and session steps · AC-9 … the two `openapi` steps · AC-10, AC-11 … milestone 3, not built yet · AC-12 … the `env:check` and blank switch steps
