# 0026. Generated API docs for welinc-auth and backend-vrms

**Date**: 2026-11-16
**Status**: Accepted
**Scope row**: [68. API docs](../../../scope/vrms/platform.md#68-api-docs--planned--needs-a-decision)
**Touches**: `welinc-auth` (shared), `welinc-backend-vrms`, contract [0001](../../_root/0001-shared-services-contract/index.md) (additive), `infra/` and the workspace CI

## Summary

welinc-auth and backend-vrms each get a docs page made from their own code: `/auth/docs` and `/vrms/docs`. The page uses Scalar, a modern API reference viewer, and reads an OpenAPI file (a standard description of every route, its inputs, replies and errors) that `@nestjs/swagger` builds from the controllers and input classes you already have. VMMS and BMS can read the auth API without opening the code, and the panel can see and try the API on staging. The docs are on locally and on staging, never in production. A committed `openapi.json` in each repo plus two CI checks keep the docs and contract 0001 in step with the code.

## Requirements

**User stories**:
- As a VMMS or BMS developer, I want to read every welinc-auth route with its exact inputs, replies and error codes so that I can build my move without reading auth's code.
- As a panel member at the defense, I want to open the API docs on staging and try a request so that I can see the system is real and documented.
- As Samuel, I want CI to tell me when the code and the docs or contract 0001 disagree so that the docs never quietly go stale.

**Acceptance criteria**:
- **AC-1**: With `API_DOCS_ENABLED=true`, `GET /auth/docs` and `GET /vrms/docs` (through the gateway and directly) serve a Scalar page that lists every route of that service except the hidden ones (AC-7), and `GET /auth/docs/openapi.json` and `GET /vrms/docs/openapi.json` serve the same OpenAPI 3 document as JSON.
- **AC-2**: With `API_DOCS_ENABLED=false`, the three docs paths of that service (`/docs`, `/docs/openapi.json`, `/docs/scalar.js` under its prefix) answer the service's usual 404, as for any unknown route. Unset, the switch is `true` when `NODE_ENV` is not `production` and `false` when it is. The Bicep sets it on both apps from the environment name: `true` on staging, `false` on production. It is worked out in the Bicep, not read from a parameter file, so no parameter can turn it on in production.
- **AC-3**: The docs page loads nothing from another origin: the Scalar script is served by the app itself at `/<svc>/docs/scalar.js` from the installed package, Scalar's default fonts are off, and no `proxyUrl` is set. A browser network log of the page shows only same origin requests.
- **AC-4**: Every documented route shows: one tag for its area (one tag per controller, a plain Title Case area name; the health routes share the tag `Operations`), its path, query and body inputs from the DTO classes, the security scheme it needs (AC-8), and its error replies. A route in the contract route index (AC-10) lists each error status with the `code` values the code really answers (`/auth/token`: its OAuth `error` values), including codes contract 0001 leaves out; an error the code answers with no `code` shows its status with no code. Errors from shared guards (`CSRF_REJECTED`, `RATE_LIMITED`, `ACCOUNT_LOCKED`, `TOKEN_EXPIRED` and the like) are listed on each route the guard runs on. Where the code and contract 0001 disagree, the docs follow the code and the gap goes on the Follow-up list, never into the docs as a promise the API doesn't keep. Every other route shows the generic 400, 401 and 403 set from one class level decorator.
- **AC-5**: Every *integration route* has a response schema naming every field its success reply carries. The integration routes are the 12 welinc-auth routes another system calls to plug in, marked `yes` in the *Reply schema* column of the contract route index (AC-10): `GET /auth/.well-known/jwks.json`, `GET /auth/.well-known/oauth-authorization-server`, `POST /auth/token`, `POST /auth/mobile/login`, `POST /auth/mobile/login/verify-email`, `GET /auth/session`, `GET /auth/systems`, `GET /auth/me`, `GET /auth/directory/users`, `POST /auth/directory/users/lookup`, `GET /auth/directory/changes`, `GET /auth/permissions/:system`. These VRMS routes have one too: `GET /vrms/repairs`, `GET /vrms/repairs/:id`, `POST /vrms/repairs`, `PATCH /vrms/repairs/:id/status`. Every other route may have no reply schema (Scalar then shows the status with no body). A field contract 0001 promises that the code doesn't send goes on the Follow-up list. The schema describes the route's success body, with these rules for routes that answer more than one shape:
  - `POST /auth/token`: one `TokenResponse` class. `access_token`, `token_type` and `expires_in` are required; the fields only some grants send are optional, and the description says which grant sends which: `scope` (`client_credentials` only), `refresh_token`, `sid`, `session_expires_at` and `user` (the user grants), `session_absolute_expires_at` (the user grants on a web session). There is no `id_token`.
  - `POST /auth/mobile/login`: a `oneOf` of the success body and the email code step body (`status: "EMAIL_VERIFICATION_REQUIRED"`). The step class (`SignInStepResponse`, in `src/auth/codes/`) lists both step values, because the web login also sends `SIGN_IN_CODE_REQUIRED` for admins, so the web login can reuse it if it ever gets a reply schema. It doesn't now: that would also need a launcher body schema, and the web login is not an integration route.
  - `POST /auth/mobile/login/verify-email`: the success body only. The code never answers the step body here.
  - `GET /auth/systems` and `GET /auth/permissions/:system`: the 200 body gets the schema; the 304 is documented with no body, with its `ETag` reply header and `If-None-Match` request header.
  - A field that can be `null` (such as the directory's `next` cursor) is marked `nullable`.
- **AC-6**: For every route with a response schema (AC-5), a unit test in `src/` (run by `npm test`) sends a request through supertest to a Nest testing module holding the real controller, its guards passed and its services faked with a realistic reply, and fails when the reply differs from that route's schema in the committed `docs/openapi.json` under this rule: arrays are checked through `items`; a field in the schema's `required` list must be present; an optional field may be missing; a reply field the schema does not name fails; a property typed plain `object` is not looked into; `null` counts as a value of the right type when the field is `nullable`; a `oneOf` reply passes when it matches one branch, and each branch has its own test. The check goes two levels deep: level 1 is the reply's own fields, level 2 the fields of the objects inside them (array items included); anything deeper is not checked. The token grant tested is `authorization_code`.
- **AC-7**: Hidden from the docs: `GET /` in both services (the hello routes), `POST /vrms/debug/sentry-test` and `POST /auth/admin/debug/sentry-test` (spec 0025). `GET /auth/health` and `GET /vrms/health` stay in, under the `Operations` tag. Nothing else is hidden; the portal admin routes (`/auth/admin/*`) and the session routes show.
- **AC-8**: The document declares these security schemes, and each route names the ones it accepts: `userToken` (a user access token as `Authorization: Bearer`), `serviceToken` (a client credentials token as `Authorization: Bearer`), `ssoCookie` (welinc-auth's SSO cookie, portal routes), `vrmsSession` (the `vrms_rt` cookie on `/vrms/session`), and `clientAssertion` (a `private_key_jwt` in the form body of `/auth/token`). On staging a person can paste an access token into Scalar's auth panel and send a request to a `userToken` or `serviceToken` route from the page, which reaches the real service on the same origin. `GET /auth/session` names `userToken` (it reads a bearer token, not the cookie). Each cookie route's description says it is called by a web app and that a request from the docs page is refused by the Origin check.
- **AC-9**: `npm run openapi` in each repo builds the app and writes `docs/openapi.json` without a database, network access or a listening port, exits 0 on success and 1 on any error (never hangs), and two runs on the same code write identical bytes. `npm run openapi:check` exits 1 with a one line hint (`run npm run openapi and commit docs/openapi.json`) when the committed file differs from what the code builds, and the repo's `ci.yml` runs it on every pull request and push.
- **AC-10**: Contract 0001 gains a section 16, *Route index*: one row per welinc-auth route the contract promises (method, path, security scheme, contract section, *Reply schema* `yes` for the AC-5 integration routes), routes marked removed left out. `node scripts/check-contract-routes.mjs <openapi.json>` exits 1 and names every index row missing from the document (matching method and path; the table writes `:param` and the document `{param}`, so the script turns `:param` into `{param}` before comparing), and every row marked `yes` under *Reply schema* whose operation has no 200 (or 201) response schema in the document, and prints, without failing, every documented `/auth/*` route that has no index row.
- **AC-11**: The workspace CI runs the check from AC-10 against welinc-auth's `development` branch on every workspace pull request and push, once a day on a schedule, and on demand, using a read only token stored as the workspace secret `AUTH_REPO_READ_TOKEN`. When the secret is missing (including on pull requests from forks, which get no secrets), the job fails with a message naming it, never passes silently.
- **AC-12**: `API_DOCS_ENABLED` is in each repo's `src/config/env.ts` schema and `.env.example`, using the existing `blank` preprocessing so a blank value falls back to the `NODE_ENV` default; `npm run env:check` accepts `true`, `false` or blank and refuses anything else, and the env drift test passes.

## Decision

**Chosen option**: Option 2: `@nestjs/swagger` with its build plugin, Scalar as the viewer, served on local and staging only, with a committed `openapi.json` and a contract route check.

Generate the docs from the code you already have (the input classes), decorate only where it pays (tags, auth, contract route errors and replies), show them with Scalar from your own server, and let CI hold the docs and contract 0001 to the code.

**Implementation skills**: `nestjs-best-practices` (`.claude/skills/nestjs-best-practices/`) · `scalar-api-reference` (`scalar/scalar`, `.claude/skills/scalar-api-reference/`)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch**: none. No table or migration; the feature adds a generated file per repo (`docs/openapi.json`) and one new contract section.

**Where the code goes** (the same layout in both repos; backend-vrms copies welinc-auth's):

| File | Holds |
|---|---|
| `nest-cli.json` | the `@nestjs/swagger` plugin, with `classValidatorShim: true` (reads the class-validator rules: required, lengths, enums), `introspectComments: true` (a `/** */` comment on a route becomes its summary) and `dtoFileNameSuffix: ['.dto.ts', '.entity.ts', '.response.ts']` (the default skips response files) |
| `src/openapi/document.ts` | `buildDocument(app)`: the `DocumentBuilder` (title, version, description, `servers: [{ url: '/' }]`, the five security schemes), `SwaggerModule.createDocument`, then a stable order: `paths`, the operations inside each path, `tags` (by name) and `components.schemas` sorted by key |
| `src/openapi/docs.ts` | `mountDocs(app, config)`: when `API_DOCS_ENABLED` is true, serves `/<prefix>/docs` (Scalar), `/<prefix>/docs/openapi.json` and `/<prefix>/docs/scalar.js`; when false mounts nothing. The bundle path is `require.resolve('@scalar/api-reference/dist/browser/standalone.js')` (confirm the path in the installed version), resolved at startup; if the file is missing the app logs an error and the docs routes answer 404, the API keeps running |
| `src/openapi/write.ts` | the `npm run openapi` script (and `--check` for `openapi:check`). `package.json`: `"openapi": "nest build && node dist/src/openapi/write.js"`, `"openapi:check": "nest build && node dist/src/openapi/write.js --check"`. Its first import is `../config/test-env.setup` (its values override any real env), then `AppModule`; it creates the app, builds the document, writes `JSON.stringify(doc, null, 2)` plus a newline (to `docs/openapi.json`, or with `--check` to a temporary file it compares byte for byte with the committed one), then `await app.close()` and `process.exit(0)`; any thrown error prints and exits 1 |
| `src/openapi/decorators.ts` | `ApiUserToken()`, `ApiServiceToken()`, `ApiSsoCookie()`, `ApiVrmsSession()`, `ApiClientAssertion()`, `ApiErrors(status, codes[])`, `ApiGenericErrors()` (400, 401, 403), `ApiCookieRoute()` (the AC-8 description line) |
| `src/openapi/schemas.ts` | `CodedError` (`statusCode`, `message`, `error`, `code`) and `OAuthError` (`error`, `error_description`), contract 0001 section 11 |
| `src/openapi/expect-reply.ts` | the AC-6 test helper: `expectReplyMatches(body, 'GET /auth/systems', 200)` reads `docs/openapi.json`, resolves `$ref`s, and applies the AC-6 rule two levels deep |
| next to each controller | its response classes (`*.response.ts`), only for the AC-5 routes |

**API surface**:

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/auth/docs`, `/vrms/docs` | GET | none | HTML: the Scalar page, configured with `url: '/<svc>/docs/openapi.json'` (not the document inline, so the page carries no second copy), `cdn: '/<svc>/docs/scalar.js'`, `withDefaultFonts: false`, `authentication.preferredSecurityScheme: 'userToken'`, no `proxyUrl`, no `persistAuth` | none | 404 when the switch is off |
| `/auth/docs/openapi.json`, `/vrms/docs/openapi.json` | GET | none | the OpenAPI 3 document (the same object `buildDocument` returns) | none | 404 when off |
| `/auth/docs/scalar.js`, `/vrms/docs/scalar.js` | GET | none | Scalar's browser bundle from `@scalar/api-reference` in `node_modules` (`Content-Type: application/javascript`, `Cache-Control: public, max-age=3600`) | none | 404 when off |

These routes are mounted in `main.ts` before `listen`, outside the controllers, so they never appear in the document, global guards don't run on them, and they need none of the permission decorators (backend-vrms's `route-permissions.spec.ts` checks controller routes only; welinc-auth has no such test).

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Docs page | the routes, inputs and rules | the controllers and DTO classes, read by the plugin at `nest build`; the plugin writes path params as `{id}` |
| Docs page | which routes get a reply schema | the AC-5 list: for welinc-auth the *Reply schema* column of contract 0001 section 16 mirrors it once milestone 3 writes it; for VRMS the AC-5 sentence alone (VRMS has no route index) |
| Docs page | JWKS key fields | the public JWK shape `SigningKeyRing` publishes (`publicJwk` in `src/auth/keys/signing-keys.ts`) |
| Docs page | directory and permission bodies | `directory.service.ts` (the `users` and `changes` envelopes with `next`) and `matrix.service.ts` |
| Docs page | the four VRMS ticket replies | backend-vrms's repairs service, the object each of those four controller methods returns |
| Docs page | each reply shape | the response class named in `@ApiOkResponse({ type })` (AC-5 routes), its fields read from the service method that builds the reply; else no reply schema |
| Docs page | the error codes per contract route | what the controller, its guards and its service throw for that route (the code wins), cross checked against contract 0001 sections 7 to 11, written into `ApiErrors(...)` by hand; each disagreement goes on the Follow-up list |
| Docs page | `info.title` | fixed: `WeLinc auth API` and `VRMS API` |
| Docs page | `info.version` | the `version` in the repo's `package.json`; it is `0.0.1` in both and stays constant, accepted (the commit is the real version) |
| Docs page | `info.description` | fixed text; auth's links to contract 0001 on GitHub and says the contract wins on behavior |
| Try it out | the target address | `servers: [{ url: '/' }]`; route paths already carry `/auth` or `/vrms`, so the request goes to the origin the page was loaded from (the gateway on staging, the service port locally) |
| Try it out | the token | pasted by the person into Scalar's auth panel; held in memory only (`persistAuth` off) |
| Switch | on or off | `API_DOCS_ENABLED` from `ConfigService`, default from `NODE_ENV` (AC-2); hosted value from the Bicep's existing `var prod` |
| `npm run openapi` | a working app without a database | the test environment values in `src/config/test-env.setup.ts` set before `AppModule` is imported; `NestFactory.create(AppModule, { logger: false })` without `init()` or `listen()`, so no module init hook runs (`PrismaService` only builds a pool in its constructor and never connects; no polls, no jobs) |
| AC-6 tests | a realistic reply | a fake service returning a fixture shaped like the real service's answer, written in the test |
| Route index check | the promised routes | the contract 0001 section 16 table, written by hand from contract sections 3 and 5 to 10a (rows marked removed left out), cross checked against the generated route list, with the AC-8 scheme names in its security column |
| Route index check | the documented routes | welinc-auth's committed `docs/openapi.json` on `development` |

**Key invariants**:
- The document is built from the compiled app (`nest build` output), because the plugin runs only there. Jest never builds the document; the AC-6 helper reads the committed file.
- `docs/openapi.json` always equals what the code builds (AC-9 in CI).
- Every contract index route exists in welinc-auth's document (AC-10, AC-11).
- Production never serves the docs: the Bicep writes `false` there and the default is `false` under `NODE_ENV=production`.
- No example value in a DTO or response class is a real secret, email or token; examples use the seed style (`admin@welinc.com`) or none at all.

**Security model**:
- The docs routes are public wherever they are on (local and staging); they reveal the route map and input rules, not data. Staging holds only seed accounts, so this is accepted. Production shows nothing (OWASP API9, improper inventory: no public route map in production).
- Try it out sends the pasted token only to the same origin; no outside proxy, and the token is not stored.
- The CSRF and Origin guards are unchanged: the docs origin is never added to any allow list, so cookie routes refuse requests from the docs page.
- `AUTH_REPO_READ_TOKEN` is a fine grained GitHub token with only *Contents: read* on `welinc-auth`, expiring after 2026-12-05, stored as a workspace Actions secret and in 1Password.

**Configuration required**:
- `API_DOCS_ENABLED` (both repos): turns the docs routes on; default from `NODE_ENV` (AC-2).
- Bicep (`infra/env.bicep`): `API_DOCS_ENABLED: prod ? 'false' : 'true'` (the existing `var prod = envName == 'prod'`) in `authSettings` and `vrmsSettings`. The migrate and seed jobs share those settings; harmless, they serve nothing.
- Workspace secret `AUTH_REPO_READ_TOKEN` (you make it once in GitHub).
- New packages in both repos: `@nestjs/swagger`, `@scalar/nestjs-api-reference`, `@scalar/api-reference` (the last as a direct dependency so `package-lock.json` pins the bundle you serve). Check the installed `@scalar/nestjs-api-reference` option names (`content`, `cdn`, `withDefaultFonts`) against its types before use; they have changed between versions.

**Critical test scenarios**:
- Happy path: with the switch on, `/auth/docs` renders, search finds `POST /auth/token`, and a pasted user token on `GET /auth/me` returns the caller, verifies **AC-1**, **AC-8**
- Switch off: with `API_DOCS_ENABLED=false`, all three docs paths answer 404; with `NODE_ENV=production` and the switch unset, the same, verifies **AC-2**
- Drift: add a field to a contract reply without updating its response class, and its AC-6 test fails; change a DTO without running `npm run openapi`, and `openapi:check` fails, verifies **AC-6**, **AC-9**
- Contract: delete a contract route's controller method locally, rebuild the file, and `check-contract-routes.mjs` exits 1 naming it, verifies **AC-10**
- Cookie route: sending `POST /auth/admin/...` from the docs page answers 403 `CSRF_REJECTED`, verifies **AC-8**
- Isolation: the page's network log shows no request to jsdelivr, fonts.scalar.com or any proxy, verifies **AC-3**

## Build plan

Tracer Bullet, welinc-auth first: one thin thread through the switch, plugin, viewer, committed file and CI on auth, then thicken auth, then the contract check, then backend-vrms copies the proven setup.

**Milestone 1: thin thread on welinc-auth**
1. Add `@nestjs/swagger`, `@scalar/nestjs-api-reference` and `@scalar/api-reference`; turn on the plugin in `nest-cli.json` with `classValidatorShim` and `introspectComments`, satisfies **AC-1**, **AC-4**
2. `API_DOCS_ENABLED` in `env.ts` (default from `NODE_ENV`) and `.env.example`, satisfies **AC-2**, **AC-12**
3. `src/openapi/document.ts` and `docs.ts`; mount in `main.ts`; serve the Scalar bundle from `node_modules`; hide `GET /` and tag the health route `Operations`, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-7**
4. `src/openapi/write.ts`, `npm run openapi` and `openapi:check`, the first `docs/openapi.json`, and the `openapi:check` step in `ci.yml` after `npm run build`, satisfies **AC-9**

**Milestone 2: welinc-auth thickened**
5. One tag per controller; the five security schemes and their decorators on every route; `ApiCookieRoute()` on every `ssoCookie` route, satisfies **AC-4**, **AC-8**
6. `CodedError` and `OAuthError`; `ApiErrors` on all 85 contract index routes with the codes the code answers, shared guard codes included (AC-4), `ApiGenericErrors()` on every controller; move `GET /auth/session` from `ssoCookie` to `userToken`, satisfies **AC-4**, **AC-8**
7. Response classes for the 12 integration routes, working from the AC-5 list (the contract column comes later, in milestone 3), satisfies **AC-5**
8. `expect-reply.ts` and one AC-6 controller unit test per integration route (supertest on a testing module, services faked, as `token.controller.spec.ts` does); hide `POST /auth/admin/debug/sentry-test` if spec 0025 has built it by then, satisfies **AC-6**, **AC-7**

**Milestone 3: contract and workspace** (start only after the welinc-auth PR with milestones 1 and 2 is merged into `development`, so `docs/openapi.json` exists there)
9. Contract 0001 section 16, *Route index* (sourced as in Value sourcing), and an *Amended* entry (additive, from VRMS spec 0026); a line in section 14 that the generated docs show shapes and the contract wins on behavior, satisfies **AC-10**
10. `scripts/check-contract-routes.mjs` and a `contract-routes` job in the workspace `ci.yml`: add `schedule` (daily) and `workflow_dispatch` to the existing `main` triggers; the job checks out welinc-auth with `actions/checkout` (`repository: Capstone-WeLinc/welinc-auth`, `ref: development`, `path: welinc-auth`, `token: ${{ secrets.AUTH_REPO_READ_TOKEN }}`) after a step that fails with a named message when the secret is empty, then runs the script on `welinc-auth/docs/openapi.json`; you make the token and the secret, satisfies **AC-10**, **AC-11**
11. `API_DOCS_ENABLED` in `infra/env.bicep` for auth and VRMS from `envName`; link `/auth/docs` and the committed file from `docs/integration/` (the move guides and `fleet-api.md` neighbours) and tell VMMS and BMS, satisfies **AC-2**, **AC-1**

**Milestone 4: backend-vrms**
12. Copy `src/openapi/` from welinc-auth, the packages, plugin, switch, mount and `openapi` scripts and CI step; hide `GET /` and `POST /vrms/debug/sentry-test` (if built), tag `GET /vrms/health` `Operations`, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-7**, **AC-9**, **AC-12**
13. Tags, security schemes (`userToken` on API routes, `vrmsSession` on `/vrms/session/*`), `ApiGenericErrors()` on every controller, satisfies **AC-4**, **AC-8**
14. Response classes and AC-6 controller unit tests (supertest, services faked) for the four ticket routes in AC-5, satisfies **AC-5**, **AC-6**

## Consequences

**Positive**:
- VMMS and BMS can read exact auth shapes without the code, during their move, on GitHub (the committed file) or staging.
- Every pull request that changes the API shows it as a diff in `docs/openapi.json`, which makes API changes visible in review.
- The contract and the code can no longer drift apart silently on which routes exist.
- A real, tryable API reference to show at the mock and integration defenses.

**Negative / tradeoffs**:
- Response classes are a second copy of reply shapes next to the services; only the AC-6 tests keep them honest, only for the AC-5 routes, and with faked services they prove the controller's reply against a fixture, not against the real database. The other 73 contract routes show inputs, scheme and errors but no reply schema; the account screen routes are written up in `docs/integration/account-screens.md` instead, with nothing checking that guide.
- Every API change now needs `npm run openapi` and a commit of the file, or CI fails. A small habit cost on every backend PR.
- The contract check runs on workspace changes and daily, so an auth PR that drops a route is caught within a day, not on that PR. On the auth PR itself the guard is `openapi:check`, which shows the removal as a diff in `docs/openapi.json` but doesn't know the contract.
- Three new packages per repo, and Dependabot PRs for them; Scalar moves fast.
- Staging publishes the route map to anyone who finds it.
- One more GitHub token to keep and to let expire after the defense.

**Neutral**:
- `introspectComments` turns existing `/** */` comments on controller methods into public summaries; read them once for anything internal before milestone 1 ships.
- No gateway change: the docs live under the existing `/auth/` and `/vrms/` routes.
- backend-vrms's `route-permissions.spec.ts` only sees controller routes, so the docs routes (mounted in `main.ts`) don't need a permission decorator.

## Follow-up

- [ ] When spec 0025 milestone 1 lands after this feature, hide its test routes then (AC-7).
- [ ] Once S11's cleanup removes the bearer admin routes (contract version 9), drop their rows from the route index in the same change.
- [ ] Decline recorded for `/sync`: Agent Skills `scalar-docs` and `openapi-swagger-nestjs` (weak match or wrong product); MCP servers that turn an OpenAPI file into agent tools (not useful here). `scalar-api-reference` belongs in the VRMS `AGENTS.md` skill list (load on match).
- [ ] VMMS and BMS may copy `src/openapi/` for their own backends after the defense; not planned.
- [ ] If milestone 2 lands with time to spare before Dec 4, widen AC-5 and AC-6 to the account screen routes (`/auth/profile/*` and `/auth/profile/deletion-request`, about 12 more): one response class and one test each, and their *Reply schema* cells in section 16 set to `yes`.
- [ ] Contract 0001 and the code disagree here (found while sourcing AC-4 on 2026-11-16; the docs follow the code). Settle each one in the contract or the code, then regenerate `docs/openapi.json`:
  - Errors with no `code`: the login 401, every 404 "User not found", `SELF_ROLE`, `SELF_DEACTIVATE` and `SELF_DELETE` (bare 409s), the second lookup limiter's 429, the shared account 403, the 403 for a non admin on bearer admin routes, and DTO 400s where the contract says `VALIDATION_FAILED`.
  - Codes the code throws that the contract leaves out: `invalid_request`, `unsupported_grant_type` and `unauthorized_client` on `/auth/token`; `INVALID_CLIENT` on mobile login; `NOT_ACTIVE` on `reset-code`; `FORBIDDEN` on `GET /auth/permissions/:system`; `NOT_ADMIN_OF_SYSTEM` on several portal routes.
  - `POST /auth/admin/verify-password` never answers `ADMIN_CODE_REQUIRED`, though section 10a says it needs the code.
  - `POST /auth/admin/deletion-requests/:id/reject` never answers `LAST_ADMIN`; only approve does.
  - The bearer deletes answer 200 (`{ id }`, `{ ended }`) where their portal twins answer 204.
  - `GET /auth/session` answers 401 `SESSION_ENDED` for a service token, where section 5 implies 403.
  - Section 10 lists the profile group as PATCH, POST, GET; the code serves only `PATCH /auth/profile/password` there.
  - The contract names `GET /auth/users/:id`; the code serves only PATCH and DELETE on that path.
  - `POST /auth/profile/picture` answers 500 for a wrong file type (`fileFilter` passes a plain `Error`, which Nest doesn't map) and for a request with no file (`file.originalname` on `undefined`); confirmed from the code on 2026-11-16. The docs leave the 500 out; the fix is a coded 400 in the code.
- [ ] More contract 0001 and code disagreements, found while building milestone 2 on 2026-11-16 (the docs follow the code). Settle each one in the contract or the code, then regenerate `docs/openapi.json`:
  - `POST /auth/mobile/login` and its two code step routes answer 429 in the OAuth shape (`{ error: "rate_limited" }`); section 12 says coded `RATE_LIMITED` for mobile login.
  - The client assertion form of `/auth/logout` and `/auth/session/activity` answers 400 `invalid_request`, 401 `invalid_client` and 429 `rate_limited`; the contract lists none of them.
  - `POST /auth/admin/code` and `POST /auth/admin/code/verify` answer 429 `RATE_LIMITED` (10 a minute per address); the contract rows leave it out.
  - `GET /auth/admin/me` also answers 403 `ACCOUNT_LOCKED`; the contract lists only 401 `NOT_SIGNED_IN`.
  - `GET /auth/permissions/:system` also answers 403 `FORBIDDEN`, 401 `TOKEN_EXPIRED` and a coded 404 `NOT_FOUND`, and sends `Cache-Control: no-cache`; the contract row leaves them out.
  - Section 8's `POST /auth/mobile/login/verify-email` row lists `CODE_SEND_LIMIT` and `MAIL_FAILED`, which that route never sends (it issues no code), and leaves out its 401, the 403s (`ACCOUNT_LOCKED`, `ACCOUNT_INACTIVE`, `NO_SYSTEM_ACCESS`, `APP_NOT_ALLOWED`) and 400 `INVALID_CLIENT`.
  - An inactive account gets three answers: 403 `ACCOUNT_INACTIVE` on `/auth/login` (right password), 401 `ACCOUNT_INACTIVE` on `GET /auth/session`, and a 401 with no code on every bearer route (`JwtAuthGuard`).
  - Section 6 step 2 says the session check ends for a locked account; section 10 and the code keep a locked account's live session at 200.
  - On routes where `system` is required (the admin lookup, create, edit, status, unlock, reset code and sessions routes), a missing or wrong `system` is a DTO 400 with no code; the contract says `VALIDATION_FAILED`. Routes where `system` is optional do answer `VALIDATION_FAILED`.
