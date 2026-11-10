# 0010. Check every app's environment when it starts

**Date**: 2026-11-11
**Status**: Accepted

## Summary

Each of the four apps (welinc-auth, welinc-backend-vrms, welinc-web-vrms, welinc-web-portal) checks its own environment variables the moment it starts or builds, against one zod schema (a list of every variable with its rule). If anything is missing or malformed, it refuses to start and lists every problem by name, never by value. Addresses and keys are always required, production refuses `localhost`, and tuning numbers keep their defaults. A setup step tops up an old `.env` with any new names, and a test in each repo keeps the schema and `.env.example` in step.

## Requirements

**User stories**:
- As a developer, I want a stale or missing `.env` to stop the app with a clear list of what is wrong, and setup to add new names for me, so I don't debug a broken login for an hour.
- As the team, we want a production build or deploy with a missing or `localhost` address to fail loudly, so the hosted site never calls the visitor's own computer.

**Acceptance criteria**:
- **AC-1**: A backend started with a required variable missing or empty refuses to start. The error lists every problem at once, field rules and production rules together, one line each as `NAME: reason`, and never contains a value.
- **AC-2**: A backend started with a malformed value refuses to start the same way: not an `http` or `https` URL, not a whole number, outside its range, not `true` or `false`, or a `CORS_ORIGINS` entry that is not a bare origin.
- **AC-3**: With `NODE_ENV=production`, a backend refuses to start when: its production only variables are missing (welinc-auth: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`; backend-vrms: `STORAGE_CONNECTION_STRING` or `STORAGE_ACCOUNT_URL`); its cookie flag (`SSO_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`) is not `true`; or `TRUST_PROXY_HOPS` is 0.
- **AC-4**: In production, every URL variable (and each `CORS_ORIGINS` entry) must use `https` and must not point at `localhost`, `127.0.0.1` or `[::1]`. The same holds for `VITE_*` in a frontend production build.
- **AC-5**: In development, SMTP and storage may be unset; Gemini may be unset in every mode. The backend starts and, once its logger is ready, logs one warning per service that is off (or only partly set, naming the missing names), and logs `Environment: <NODE_ENV>`.
- **AC-6**: A tuning number left unset takes its documented default from the schema (table below), the same value the code uses today.
- **AC-7**: `npm run dev` and `npm run build` in web-vrms and web-portal stop with the same kind of list when a required `VITE_*` variable is missing or malformed. No code in `src/` falls back to a `localhost` address any more.
- **AC-8**: `npm run dev` and `npm run build:local` (`vite build --mode development`) pass with the committed `.env.development` and no extra setup, locally and in the Docker stack.
- **AC-9**: Every Jest test that imports `AppModule` (for example `route-permissions.spec.ts`) passes in CI with no `.env`, through a test env fixture. No module reads config at import time.
- **AC-10**: In each of the four repos, a test fails when a name in `.env.example` is missing from the schema, or a schema name is missing from `.env.example`. In the frontends it also fails when `.env.development` and the schema disagree. Names only scripts, compose or the platform read sit on named skip lists matched by name or prefix.
- **AC-11**: In both backends, lint fails on any `process.env` read outside the env files (`src/config/env.ts`, `src/config/check-env.ts`), `prisma/`, `prisma.config.ts`, `scripts/` and test files.
- **AC-12**: `sh scripts/setup.sh <group>` run on a machine with an old `.env` appends every name present in `.env.example` but missing from `.env`, with the example's value. It never changes or removes an existing line, and prints the added names only, never values.
- **AC-13**: Existing behavior is kept: the signing key ring (`signing-keys.ts`) and the client key (`assertion-signer.ts`) still parse and self test at boot with today's messages; the schema checks only that they are present.

## Decision

**Chosen option**: Option 1: one zod schema per app, enforced at boot or build, with a drift test, a lint rule and a setup top up, migrated in one PR per repo.

Each app owns one env schema; nothing else reads raw environment values. Backends plug it into `ConfigModule.forRoot({ validate })`; frontends run it in `vite.config.ts`.

## Standard definition

**Canonical pattern (backends)**, `src/config/env.ts`. `validateEnv` is pure: no logging, no side effects.

```ts
import { z } from 'zod';

// Empty or blank strings count as missing: .env.example ships some names empty.
const blank = (v: unknown) => (typeof v === 'string' && v.trim() === '' ? undefined : v);
const required = z.preprocess(blank, z.string({ error: 'is required' }).trim());
const optional = <T extends z.ZodType>(s: T) => z.preprocess(blank, s.optional());
const httpUrl = z.url({ protocol: /^https?$/, error: 'must be an http or https URL' });
const url = required.pipe(httpUrl); // "is required" first, then "must be a URL"
const whole = (min: number, max: number, fallback: number) =>
  z.preprocess(blank, z.coerce.number().int().min(min).max(max).default(fallback));
const flag = z.preprocess(blank, z.enum(['true', 'false']).default('false')).transform((v) => v === 'true');
/** "a, b," → ['a', 'b']; each entry must be a bare origin (no path, no trailing slash). */
const originList = required.transform((v, ctx) => {
  const items = v.split(',').map((s) => s.trim()).filter(Boolean);
  for (const item of items) {
    const ok = URL.canParse(item) && new URL(item).origin === item;
    if (!ok) ctx.addIssue({ code: 'custom', message: 'each entry must be an origin like https://host' });
  }
  return items;
});

export const envSchema = z.object({
  NODE_ENV: z.preprocess(blank, z.enum(['development', 'production', 'test']).default('development')),
  PORT: whole(1, 65535, 3000),
  CORS_ORIGINS: originList,
  PORTAL_URL: url,
  // ...every runtime variable from the table below
});
export type Env = z.infer<typeof envSchema>;

/** Production rules, checked on the blank normalised raw values so they run even when a field failed. */
function productionIssues(raw: Record<string, unknown>): string[] { /* AC-3, AC-4 */ }

/** ConfigModule's validate hook. Throws one Error listing every problem; never includes a value. */
export function validateEnv(raw: Record<string, unknown>): Env {
  const result = envSchema.safeParse(raw);
  const lines = [
    ...(result.success ? [] : result.error.issues.map((i) => `${String(i.path[0])}: ${i.message}`)),
    ...productionIssues(raw),
  ];
  if (lines.length) throw new Error(`Environment check failed:\n  ${lines.join('\n  ')}`);
  return result.data!;
}

/** The AC-5 warnings, logged by bootstrap() once the app's logger is set. */
export function envWarnings(get: <K extends keyof Env>(key: K) => Env[K]): string[] { /* one line per service off or partly set */ }

/** Valid values for tests (no secrets, no network): loaded by Jest setupFiles. */
export const testEnv: Record<string, string> = { /* every required name */ };
```

Issue lines name only the top level variable (`path[0]`) and a message written in the schema. Never log or rethrow `result.error` itself, since zod issues can carry the input.

```ts
// app.module.ts
ConfigModule.forRoot({ isGlobal: true, validate: validateEnv });

// any module needing config at setup time: never at import
JwtModule.registerAsync({ inject: [ConfigService], useFactory: (c: ConfigService<Env, true>) => ({ /* ... */ }) });

// anywhere else
constructor(private readonly config: ConfigService<Env, true>) {}
const issuer = this.config.get('AUTH_ISSUER', { infer: true });

// main.ts, after NestFactory.create and app.useLogger(...)
const config = app.get(ConfigService<Env, true>);
const log = new Logger('Env');
log.log(`Environment: ${config.get('NODE_ENV', { infer: true })}`);
envWarnings((key) => config.get(key, { infer: true })).forEach((line) => log.warn(line));
```

`main.ts` reads `PORT`, `CORS_ORIGINS` and `TRUST_PROXY_HOPS` through `ConfigService`. `src/config/check-env.ts` runs `validateEnv(process.env)` alone and exits non zero on failure; `npm run env:check` calls it, and the production start runs it before `prisma migrate deploy`, since the Prisma CLI reads `process.env` directly.

**Canonical pattern (frontends)**, `env.schema.ts` at the repo root:

```ts
// vite.config.ts
export default defineConfig(({ mode }) => {
  if (!process.env.VITEST) checkEnv(loadEnv(mode, process.cwd(), 'VITE_'), mode); // same list style; https and no localhost when mode === 'production'
  return { /* plugins, server, test as today */ };
});
```

`package.json` gains `"build:local": "vite build --mode development"`. `src/vite-env.d.ts` declares each `VITE_*` name as a required `string` (web-portal gains this file). `src/` reads `import.meta.env.VITE_...` with no `||` fallback.

### Variables

Rules: **required** = set and not blank; **URL** = an `http` or `https` URL (in production `https` and not `localhost`, AC-4); **prod** = required when `NODE_ENV=production`, a warning in development (AC-5); numbers show min, max and default (AC-6).

**welinc-auth**

| Name | Rule |
|---|---|
| `NODE_ENV` | `development`, `production` or `test`, default `development` |
| `PORT` | 1 to 65535, default 3000 |
| `TRUST_PROXY_HOPS` | 0 to 10, default 0; at least 1 in production |
| `CORS_ORIGINS` | required, comma list of origins |
| `PORTAL_URL` | required, URL |
| `DATABASE_URL` | required |
| `AUTH_ISSUER` | required |
| `AUTH_SIGNING_KEYS` | required (parsed by `signing-keys.ts`, AC-13) |
| `ACCESS_TOKEN_MINUTES` | 1 to 60, default 15 |
| `SERVICE_TOKEN_MINUTES` | 1 to 60, default 5 |
| `WEB_SESSION_IDLE_MINUTES` | 1 to 1440, default 30 |
| `WEB_SESSION_MAX_HOURS` | 1 to 168, default 12 |
| `MOBILE_SESSION_IDLE_DAYS` | 1 to 90, default 7 |
| `REFRESH_REUSE_GRACE_SECONDS` | 1 to 60, default 10 |
| `MAX_SESSIONS_PER_USER` | 1 to 100, default 10 |
| `SESSION_RETENTION_DAYS` | 1 to 3650, default 90 |
| `SSO_COOKIE_SECURE` | `true` or `false`, default `false`; `true` in production |
| `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` | prod; SMTP counts as on only when all three are set |
| `SMTP_PORT` | 1 to 65535, default 587 |
| `SMTP_FROM` | default `WeLinc Logistics <no-reply@welinc.com>` |

Cross checks: `WEB_SESSION_IDLE_MINUTES` at most `WEB_SESSION_MAX_HOURS` × 60; `ACCESS_TOKEN_MINUTES` at most `WEB_SESSION_IDLE_MINUTES`.

Skip lists: scripts `SEED_ALLOW`, `API_PUBLIC_URL`, prefix `CLIENT_` (`CLIENT_<ID>_JWKS`, `CLIENT_<ID>_WEB_ADDRESS`); platform prefixes `AZURE_`, `POSTGRES_`, `PRISMA_`, and `TZ`, `NODE_OPTIONS`.

**welinc-backend-vrms**

| Name | Rule |
|---|---|
| `NODE_ENV`, `PORT`, `TRUST_PROXY_HOPS` | as welinc-auth |
| `CORS_ORIGINS` | required, comma list of origins |
| `DATABASE_URL` | required |
| `AUTH_ISSUER`, `AUTH_CLIENT_ID` | required |
| `AUTH_JWKS_URL`, `AUTH_INTERNAL_URL` | required, URL (`AUTH_INTERNAL_URL` is container to container, so it is exempt from the production `https` and `localhost` rule) |
| `AUTH_CLIENT_PRIVATE_KEY` | required (parsed by `assertion-signer.ts`, AC-13) |
| `WEB_APP_URL`, `API_PUBLIC_URL`, `PORTAL_URL`, `AUTH_PUBLIC_URL` | required, URL |
| `SESSION_COOKIE_SECURE` | `true` or `false`, default `false`; `true` in production |
| `GEMINI_API_KEY` | optional in every mode; unset warns that the AI module is off, in production too |
| `GEMINI_MODEL` | default `gemini-3.5-flash-lite` |
| `GEMINI_EMBED_MODEL` | default `gemini-embedding-2` |
| `STORAGE_CONNECTION_STRING` or `STORAGE_ACCOUNT_URL` | prod (at least one); when both are set the connection string wins and a warning names the ignored one; `STORAGE_ACCOUNT_URL` must be a URL when set |
| `STORAGE_CONTAINER` | default `vrms-attachments` |
| `STORAGE_PUBLIC_URL` | optional, URL when set (exempt from the production rule while Azurite serves it locally) |

Skip lists: platform prefixes as welinc-auth. (`SEED` is read by the seed only and stays out of both the schema and the example.)

**welinc-web-vrms**: `VITE_API_BASE_URL`, `VITE_PORTAL_URL`, both required, URL.
**welinc-web-portal**: `VITE_API_BASE_URL`, required, URL.

Before the first PR in each repo, the builder greps `process.env`, `config.get`, `getOrThrow` and `import.meta.env` once more and reconciles this table (spec 0009 and other open work may have added names).

**Value sourcing**

| Where | Value | Source |
|---|---|---|
| backends, local | every required name | the repo's `.env` (made from `.env.example` by `scripts/setup.sh`, topped up by `scripts/sync-env.mjs`, keys by `npm run keys:dev`) and the compose `environment` block |
| backends, hosted | every required name, `NODE_ENV=production` | Container Apps settings and secrets (VRMS spec 0008); `Dockerfile.prod` sets `ENV NODE_ENV=production` |
| backends, Jest and CI | every required name | `testEnv` from `src/config/env.ts`, loaded by Jest `setupFiles` |
| frontends, `npm run dev`, `build:local` | `VITE_*` | the committed `.env.development` |
| frontends, CI build | `VITE_*` | `env:` in each repo's `ci.yml`, `https://ci.example.test` style values |
| frontends, production build | `VITE_*` | `ARG` lines in `Dockerfile.prod`, set by the deploy (VRMS spec 0008) |
| drift test | names in `.env.example` | lines matching `NAME=` or `# NAME=` (commented names count as documented) |
| `sync-env.mjs` | names to add, their values | names in `.env.example` absent from `.env`; the example's value for each |

**Setup top up**, `scripts/sync-env.mjs` (workspace repo), run by `setup.sh` after `make_env`: for every repo holding both `.env` and `.env.example`, append each missing name with its example value under one comment line `# Added by sync-env on <date>`. It never edits or removes a line, prints `added <repo>: NAME, NAME` (names only), and changes nothing when nothing is missing.

**Replaces**:
- Scattered presence and format checks: `token-config.ts` (`AUTH_ISSUER`, minute settings), `session-config.ts` and `auth.service.ts` (`PORTAL_URL` in production, whole number settings), `verify.module.ts`'s `required()`, `account-check.ts`'s `getOrThrow`, `session.config.ts` (production addresses), and the `TRUST_PROXY_HOPS` checks in both `main.ts` files.
- Direct `process.env` reads in app code (`PORT`, `CORS_ORIGINS`, `TRUST_PROXY_HOPS`, `SMTP_*`, `GEMINI_*`, `STORAGE_*`, `DATABASE_URL` in `prisma.service.ts`, `NODE_ENV`), and any config read at import time.
- The warnings in `mail.service.ts`, `gemini.provider.ts` and `blob-file-store.ts`, folded into `envWarnings` (AC-5). `mail.service.ts` keeps its throw at send time in production as a second guard.
- Every `|| 'http://localhost:...'` fallback in `src/` of both frontends.

**Enforcement**:
- Boot or build itself refuses a bad environment (AC-1 to AC-4, AC-7).
- ESLint `no-restricted-properties` on `process.env` in both backends' `eslint.config` files, with the exceptions in AC-11 (fails `npm run lint`, already in CI).
- The drift test in each repo's normal test run (Jest in the backends, Vitest in the frontends).

**Rollout**: one migration PR per repo, all reads moved at once. VRMS first as the thin thread (backend-vrms, then web-vrms), then the shared pair (welinc-auth, then web-portal), then a workspace PR for `scripts/sync-env.mjs`, the `setup.sh` call, and the VRMS "build before done" rule in `agents/vrms/AGENTS.md` moving to `npm run build:local`. Each backend PR also updates its `.env.example` so every required name carries a working local value (secrets stay empty, filled by `keys:dev`), adds the Jest `setupFiles` fixture, `env:check`, and `ENV NODE_ENV=production` in `Dockerfile.prod`. Each frontend PR adds `build:local`, the CI `env:` values and the `Dockerfile.prod` `ARG` lines.

**Exceptions**:
- `prisma.config.ts`, `prisma/` seeds and `scripts/` read `process.env` directly: they run outside Nest. `env:check` guards `prisma migrate deploy` in production.
- Unit tests may build `ConfigService` fakes instead of going through `validateEnv`.
- Vitest runs skip the frontend check (`process.env.VITEST`), since unit tests don't use the addresses.
- `AUTH_INTERNAL_URL` and `STORAGE_PUBLIC_URL` are exempt from the production `https` and `localhost` rule (see the table).

## Critical test scenarios

- `validateEnv` per backend: a full valid set passes and fills the table defaults (AC-6); an empty required name, a non `http` URL, `PORT=99999`, `SSO_COOKIE_SECURE=yes` and `CORS_ORIGINS=https://a.test/` each fail with the name (AC-1, AC-2); production with a bad URL and no SMTP lists both (AC-1, AC-3); production with a `localhost` or `http` URL fails (AC-4); `TRUST_PROXY_HOPS=0` in production fails (AC-3).
- Secrets never leak: a sentinel value in every secret bearing name (`DATABASE_URL`, `AUTH_SIGNING_KEYS`, `AUTH_CLIENT_PRIVATE_KEY`, `SMTP_PASS`, `STORAGE_CONNECTION_STRING`, `GEMINI_API_KEY`) with each failure kind triggered; the thrown message never contains it (AC-1).
- `envWarnings`: development without SMTP warns once; SMTP host only warns naming user and pass; both storage settings warn the account URL is ignored (AC-5).
- The frontend `checkEnv`: missing and malformed `VITE_*` fail with names; a `localhost` value fails only in production mode (AC-4, AC-7).
- `route-permissions.spec.ts` and every test importing `AppModule` pass in CI with no `.env` (AC-9).
- The drift test in each repo (AC-10); lint on a file that reads `process.env` (AC-11).
- `sync-env.mjs` on a fixture `.env` missing two names: appends both with example values, leaves other lines byte for byte, prints names only (AC-12).
- By hand: the Docker stack starts clean after `scripts/setup.sh vrms`, and `build:local` passes (AC-8); removing `AUTH_ISSUER` from `welinc-backend-vrms/.env` stops the container with the list in its log (AC-1).

## Consequences

**Positive**:
- A stale `.env` names itself at boot, and setup adds new names without anyone editing by hand.
- A production deploy can't point at `localhost`, run without mail, storage or secure cookies, or count every visitor as the proxy.
- One typed place per app to see every setting.

**Negative / tradeoffs**:
- A new dependency (zod) in both backends and web-portal.
- Every existing `.env` must have the newly required addresses; `sync-env.mjs` fills them from the example, but a value someone changed by hand stays as it was.
- Local frontend builds use `build:local`; plain `npm run build` now needs real values, like CI and hosting.
- Modules that read config at import time must move to `registerAsync` and `useFactory`, which touches module wiring in both backends.
- The schema and the deep key checks stay in two places by design (AC-13).

**Neutral**:
- `/sync` adds the env rules to each repo's `AGENTS.md` after the build.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Follow-up

- [ ] VRMS spec 0008 (hosting): pass `VITE_*` as build arguments in the deploy; set every required backend variable per environment, including `NODE_ENV=production`, `TRUST_PROXY_HOPS` at least 1, `SSO_COOKIE_SECURE=true`, `SESSION_COOKIE_SECURE=true`, SMTP and storage; run `npm run env:check` before `prisma migrate deploy`.
- [ ] The two cookie flags have different names (`SSO_COOKIE_SECURE` in welinc-auth, `SESSION_COOKIE_SECURE` in backend-vrms). Kept as is here; renaming is a separate contract change.
- [ ] After each repo merges, `/sync` records the standard in its `AGENTS.md`.
- [ ] No scope row tracks this yet. Give the PM a line for it if Jira should track the five PRs.
