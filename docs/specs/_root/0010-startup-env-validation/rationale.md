# 0010. Rationale: check every app's environment when it starts

Status: see [index.md](index.md).

## Context

The four apps read about 50 environment variables between them, and nothing checks them together. On 2026-11-11 a sweep found:

- **Backends:** `ConfigModule.forRoot({ isGlobal: true })` with no validation in either. About eight hand written checks are spread over `token-config.ts`, `session-config.ts`, `auth.service.ts`, `verify.module.ts`, `account-check.ts`, `session.config.ts` and both `main.ts` files. Some names are read through `ConfigService`, others straight from `process.env`. SMTP, Gemini and Blob storage only log a warning when missing. Addresses such as `WEB_APP_URL` and `PORTAL_URL` fall back to `localhost` outside production.
- **Frontends:** web-vrms reads two `VITE_*` names, the portal one, each with a `localhost` fallback in code. Neither `Dockerfile.prod` passes any `VITE_*` value in, so a production image built today would call `localhost`, meaning the visitor's own computer.
- **Drift:** nothing ties `.env.example` to what the code reads. The portal had two names for the same setting until a fix the same day.

The cost of not deciding: a stale or missing `.env` shows up as a broken login or a 502 far from its cause, and the hosting work (VRMS spec 0008) would ship builds that silently point at `localhost`. Hosting is due by the end of November 2026, so this needs to land first.

## Options considered

### Option 1: One schema per app, checked at boot or build (chosen)

A zod schema per app, plugged into `ConfigModule`'s `validate` hook and `vite.config.ts`, plus a drift test and a lint rule against raw `process.env`.

**Pros**: fails at the earliest moment with every problem listed; typed config; one place per app; enforced by tooling, not memory.
**Cons**: a new dependency; every repo is touched; old `.env` files that leaned on fallbacks must be fixed.

### Option 2: A workspace check script run by `start.sh`

A shell script compares each `.env` with its `.env.example` by name before Docker starts.

**Pros**: no app code changes; catches a missing name before containers start.
**Cons**: checks names only, not values; doesn't run in CI, hosting or `npm run dev`; the apps still fall back to `localhost`.

### Option 3: Keep the scattered checks, add the missing ones

Add a check wherever one is missing, in the style already used.

**Pros**: smallest change per file.
**Cons**: rules stay spread over a dozen files and can disagree; errors still stop at the first problem; nothing stops a new raw `process.env` read.

## Rationale

The real risk is a deploy that silently points at `localhost`, or a container that starts and fails later. Only checks inside the apps run in every place that matters (local, Docker, CI, hosting), and only a schema checks values as well as names, so Option 2 is out. Option 3 keeps the scattering that caused the drift.

Within Option 1, the picks were:
- **zod**, not class-validator or joi: one schema style across all four apps (web-vrms already uses zod 4), typed output with no casts, clear issue lists. class-validator was the runner up, since it is already installed in both backends, but it needs a config class and gives a different style from the frontends.
- **Presence and format move into the schema; the key parsing stays put**, because the key ring and the client key need crypto and self tests that would make the schema hard to read.
- **Addresses and keys always required, numbers keep defaults.** A silent `localhost` is the bug being fixed. Numbers have safe, documented defaults that nobody needs to set.
- **Frontends required always**, made free locally by the committed `.env.development`, which Vite loads during `npm run dev`.
- **SMTP and storage required in production, warnings in development; Gemini optional everywhere**, because the AI module is optional by design and local SMTP is real Gmail that most developers don't set.
- **Plain zod in `vite.config.ts`**, not a plugin: about 15 lines, no extra dependency to keep current. The runner up was `@julr/vite-plugin-validate-env`.
- **The drift test checks both directions**, so a new schema name nobody documented fails as well as a documented name nobody validates.
- **A lint rule bans raw `process.env`** in app code, the only enforcement that stops the scattering from coming back.

Calls made while writing, not asked:
- **Empty strings count as missing**, because `.env.example` ships secrets empty and `setup.sh` copies it.
- **One error listing every problem, names and reasons only, never values**, because env values include keys and passwords that must not reach logs.
- **Cookie flags must be `true` in production**, since a session cookie without `Secure` on a hosted site is a security bug this check can catch for free.
- **`CORS_ORIGINS` required**, since it is an address list like the others.
- **Vitest skips the frontend check**, because unit tests don't use the addresses and CI would otherwise need a test env file.
- **VRMS repos first**, since they are ours and lower risk, then the shared pair.

Added after a cross check on another model (2026-11-11), all accepted:
- **Production rules run separately from the schema**, because zod skips object level checks once a field fails, which would hide missing SMTP behind a bad URL.
- **A `testEnv` fixture and no config reads at import time**, because `ConfigModule.forRoot` validates when `AppModule` is imported, and `route-permissions.spec.ts` imports it.
- **`build:local` for the frontends**, because a production mode build doesn't load `.env.development`.
- **`scripts/sync-env.mjs`**, because `setup.sh` never touches an existing `.env`, so the stale `.env` problem that started this would otherwise remain.
- **Production refuses `localhost` and plain `http`**, since a valid URL check alone lets the original bug through.
- **Warnings logged in `bootstrap()`, not in the validator**, so the validator stays pure and the app's logger is ready.
- **`NODE_ENV=production` set in `Dockerfile.prod`**, since every production rule keys on it.
- **Tighter URL, origin list and number rules, a secret leak test, platform skip lists, `env:check` before migrations, and `TRUST_PROXY_HOPS` at least 1 in production**, each closing a way a bad value could still slip through.
