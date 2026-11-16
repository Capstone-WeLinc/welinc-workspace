# 0026. Rationale: generated API docs

The decision record for [index.md](index.md). `/develop` reads the index; this file explains why.

## Context

VMMS and BMS are moving onto welinc-auth now (suite row S11). Their only description of the auth API is contract 0001: a 690 line document that states the promises well (which routes, who may call them, limits, behavior) but describes reply shapes in prose, scattered over sections 7 to 11. To learn an exact reply they have to read welinc-auth's code or ask Samuel. backend-vrms has no API description at all beyond its own frontend.

The panel at the mock (Nov 28) and integration (Dec 4) defenses will ask how the services talk to each other. A browsable, tryable API reference is the usual industry answer, and today there is none.

Both services are NestJS 11. Every request body is already a validated input class (class-validator: 66 of 67 bodies), so most of the input side exists. Controller methods have no declared return types, so reply shapes don't. About 170 routes across 31 controllers, with five kinds of caller identity (user token, service token, the portal's SSO cookie, the VRMS session cookie, and a signed client assertion on `/auth/token`). Staging and production both run `NODE_ENV=production`, so the app can't tell them apart on its own. Both repos are private, which matters for any check that reads one from the other.

Not deciding means the groups keep reading code and asking questions during the busiest two weeks, and the contract keeps drifting from the code without anyone noticing.

## Options considered

### Option 1: Hand written docs only (contract 0001 plus a Markdown route reference)

Keep contract 0001 as the only reference and add a Markdown page of reply shapes per route.

**Pros**:
- No new packages, nothing in the running app.
- Reads well on GitHub.

**Cons**:
- A third copy of the API (code, contract, page) with nothing checking it; it goes stale the first busy week.
- Nothing to try; weak at the defense.

### Option 2: `@nestjs/swagger` with the build plugin, Scalar viewer, local and staging only, committed file and contract check (chosen)

Generate an OpenAPI document from the code at build, decorate only tags, auth, contract errors and contract replies, show it with Scalar from the app itself, commit the file and check it in CI, and add a route index to the contract that CI compares with auth's document.

**Pros**:
- Inputs come free from the existing input classes; the work is in the parts that matter to readers.
- CI holds both the file and the contract to the code.
- A modern, tryable reference for the groups and the panel; nothing exposed in production.

**Cons**:
- Response classes duplicate reply shapes; only some are tested.
- A per PR habit (regenerate and commit) and a cross repo token.

### Option 3: Same generation, Swagger UI viewer

Option 2 with the Swagger UI that ships inside `@nestjs/swagger`.

**Pros**:
- No extra package; the look every developer recognises.

**Cons**:
- Dated layout that gets cramped on long schemas; reading 170 routes is noticeably worse than in Scalar.

### Option 4: Docs as the source of truth (strip the contract's route tables)

Generate the docs and replace contract 0001's route tables with a link to them.

**Pros**:
- One less copy of the route list.

**Cons**:
- The contract loses the readable promises (who, limits, behavior) the generated docs can't carry well, and a route deleted in code would vanish from the "contract" with no one noticing.

## Rationale

The groups need exact shapes now, while they move, and the panel needs something real to look at. That rules out Option 1: a hand written page has the same staleness problem the contract already shows, with no check behind it. Generation from code is the only approach that stays true without effort, and the existing input classes mean the input half is already done.

Option 4 was rejected because contract 0001 carries promises, not just shapes. Keeping the contract for behavior and the generated docs for shapes, then tying the two with a route index that CI compares, gives each document the job it does well. The route index is a small, readable table, so a contract change that drops a route is visible in its own diff.

Scalar over Swagger UI (Option 3) because the page exists to be read by people outside the team, and Scalar reads better. Its cost is one package and a script that would normally load from a CDN; serving it from the app's own `node_modules` removes the outside dependency, so the page works on any network at the defense and shows no third party requests. Swagger UI remains the fallback: both read the same document, so switching is about ten lines.

Scope of hand decoration follows the readers. Response classes and error codes per route go only where someone reads the reply without the code: the contract routes (VMMS and BMS) and four VRMS ticket routes (the panel). Everything else shows its inputs, auth and generic errors. Writing classes for all 170 routes would cost most of the remaining time before Dec 4 for routes only your own frontend calls.

Production stays dark because a public route map in production gives attackers an inventory for free (OWASP API9, improper inventory management) and helps nobody: the groups and the panel use staging. Because staging and production both run `NODE_ENV=production`, the guard sits in the Bicep, which knows the environment name, rather than in the app. You first chose "production refuses the switch" in the app; the Bicep keeps exactly that promise, since the value there is worked out from `envName`, not taken from a parameter.

The contract check runs in the workspace, where the contract lives, and reads welinc-auth through a read only token, because both repos are private. A daily schedule covers the case the workspace CI can't see on its own: an auth pull request that removes a route. auth's own `openapi:check` already shows such a removal as a diff on that pull request.

welinc-auth goes first because VMMS and BMS need it during their move and the contract check depends on it; backend-vrms copies a setup that is already proven.

## Narrowing the reply schemas (update, 2026-11-16)

The first version gave a response class and a reply test to every route in the contract route index. Sourcing that index during the build showed it holds 85 of welinc-auth's 86 routes, because sections 10 and 10a cover nearly the whole API. That meant about 85 classes and 85 tests, several days of work mostly on routes no other group reads about.

Options weighed: the 6 backend to backend routes only; the 12 *integration routes* (what another system calls to plug in: discovery, tokens, mobile sign in, session, `me`, systems, directory, the permission read); or those 12 plus the account screen routes (about 24).

Chosen: the 12. They are what VMMS and BMS build against during their move, and nothing else describes their replies. The account screen routes are already written up in `docs/integration/account-screens.md`, and the groups already call them from working pages, so docs there would mostly repeat a guide. The set is easy to widen (one class and one test per route, no rework), so the account screen routes are a Follow-up if time allows before Dec 4. The set lives in contract section 16's *Reply schema* column, so the contract stays the one place that says which replies are guaranteed.

The same pass found places where contract 0001 and the code disagree on error codes. The docs follow the code: a reference that promises an error code the API never sends is worse than one with a gap, because a client built from it breaks. Each disagreement is listed in the index's Follow-up to be settled in the contract or the code.

## Tool discovery (2026-11-16)

A registry search for `@nestjs/swagger` and Scalar found the vendor's `scalar/scalar@scalar-api-reference` (installed, saved to `agents/vrms/skills/`) and `scalar/scalar@scalar-docs` (declined: covers Scalar's hosted docs product). The only `@nestjs/swagger` skill was `davidcastagnetoa/skills@openapi-swagger-nestjs` with 10 installs from an unknown author (declined; `nestjs-best-practices` and the package docs cover it). MCP servers found turn an OpenAPI file into agent tools at runtime; not useful for building this (declined).
