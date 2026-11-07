# 0002. Signing keys and service identity: rationale

The decision record behind [index.md](index.md). `/develop` builds from `index.md` and can skip this file.

## Context

Today welinc-auth signs every token with HS256 and one shared password, `JWT_SECRET`. The same value sits in welinc-auth, backend-vrms, the BMS services and the compose files, and it both makes and checks tokens. So any service holding it can mint a token for any user in any system, and a leak from the least careful service is a leak everywhere. Spec 0001 already settled the outside of the fix: ES256 keys only welinc-auth holds, published at a JWKS address, with a `status` per key for rotation, a client registry, and `private_key_jwt` (each backend signs a short proof with its own key) for service calls. This spec decides the inside: how the keys are stored, loaded, rotated and checked, what the registry looks like in the database, and how VRMS gets there before sessions (S3) and the code exchange (S4) exist.

Three forces shape it. First, the order: S2 lands before S3 and S4, so the portal still logs in with `POST /auth/login` and hands VRMS the token in the URL for a while. The token format has to become the final one (one system per token, `aud` checked) without waiting for the new login. Second, the other groups: VMMS and BMS move in S11 and copy whatever VRMS proves here, and their stacks differ (Nest with passport, Nest with `@nestjs/jwt` only, and `bms-gateway`, a plain Node server with only `pg`). Third, the deadline: a deployed suite by the end of November 2026, a student team, and the spec 0008 hosting model where secrets live in a private file per environment applied by `set-secrets.sh`.

Without this spec the contract's promises stay on paper: the hard switch away from `JWT_SECRET` has no tooling, nobody knows how to rotate a key without logging people out, and every group would write its own token check.

> ⚠️ Premise note: key handling is a classic place to roll your own crypto by accident (hand parsing JWKs, comparing signatures, inventing a rotation scheme). The guard here is that every signature, key import and key set lookup goes through `jose`, a widely used library built for exactly this, and the only code we write is policy (which claims, which audiences, when a key may change status). The rotation script exists to enforce timing rules, not to do cryptography.

### Current state (read on 2026-11-08)

| Where | What it does today |
|---|---|
| `welinc-auth/src/auth/auth.module.ts` | `JwtModule` with `JWT_SECRET` and `JWT_ACCESS_EXPIRY` (HS256) |
| `welinc-auth/src/auth/auth.service.ts` | `login` signs `{ sub, email, roles }` with every role in every system |
| `welinc-auth/src/auth/strategies/jwt.strategy.ts` | passport-jwt with `JWT_SECRET`; picks the system from `?system=`, then `Origin` and `Referer` ports, then path patterns, then the request body, then the user's first role |
| `welinc-auth/src/main.ts` | no `trust proxy`, so `req.ip` is the gateway's address |
| `welinc-auth` | no rate limiting anywhere |
| `welinc-backend-vrms/src/auth/strategies/jwt.strategy.ts` | passport-jwt with `JWT_SECRET`, passes `sub` and `exp` on; the guard then asks `/auth/me?system=VRMS` (spec 0009 account check, 30 s cache) |
| `welinc-backend-vrms/src/modules/vrms/mechanic-roster.service.ts` | calls `/auth/users?system=VRMS` with the caller's own token, from the admin sync (`config.controller.ts`) and from `mechanic-work.service.ts` (`refreshOne`), which can run as a non admin caller against an admin only route |
| `welinc-web-portal/src/pages/auth/Login.tsx`, `src/App.tsx` | logs in, decodes the token in the browser, picks the system (one system: that one; holds VRMS: VRMS; else the first), redirects with `?token=` |
| `welinc-web-vrms` | decodes the token payload only; never checks the signature |
| `docker-compose.shared.yml`, `docker-compose.vrms.yml` | set `JWT_SECRET`, `JWT_REFRESH_SECRET`, `JWT_ACCESS_EXPIRY`, `JWT_REFRESH_EXPIRY` inline; both already read the repo `.env` through `env_file` |
| Other groups | VMMS backend: Nest 11, passport-jwt. BMS booking, dispatch, completion: Nest 11, `@nestjs/jwt` only. `bms-gateway`: plain Node ESM, only `pg`. `welinc-backend-vmms-analytics-ai` pins Node 20 (end of life since April 2026); `bms-gateway` allows Node 20 |

## Options considered

The contract fixed ES256, JWKS and `private_key_jwt`. The options here are about how to build them.

### Option 1: `jose` everywhere, keys in the environment, a tested reference module, scripted rotation

welinc-auth signs, publishes and checks assertions with `jose`. Every other backend checks tokens with `jose`'s remote key set and signs its own assertions with `jose`. Signing keys stay in `AUTH_SIGNING_KEYS` as 0001 says, and a small script edits that value in the private secrets file while enforcing the timing rules. The client registry is one table seeded per environment. VRMS builds the check as a self contained folder the other groups copy.

**Pros**:
- One JOSE library in every backend, including `bms-gateway`, which has no Nest or passport. Every backend needs it anyway to sign its assertion.
- `jose` covers the 0001 caching rules (5 minute cache, refetch on an unknown `kid` at most once a minute) with two settings.
- No new infrastructure: keys reuse the spec 0008 secrets path.
- The timing rules that prevent logouts are enforced by code, not memory.

**Cons**:
- `jose` 6 ships only ESM, so each repo's Jest needs a transform setting.
- VMMS and BMS rewrite their token check (a copy, but still a change they test).
- The private key lives in an environment variable, so anyone with access to the Container App's secrets can read it.
- A small update to 0001 section 5, which names passport and `jwks-rsa`.

### Option 2: `jose` in welinc-auth, passport-jwt with `jwks-rsa` in the others

What 0001 section 5 wrote. welinc-auth uses `jose`; verifiers keep passport-jwt and add `jwks-rsa` as the key provider.

**Pros**:
- The least change for VMMS, whose strategy is already passport-jwt.
- `jwks-rsa` is mature and handles EC keys.

**Cons**:
- Every backend still needs `jose` (or similar) to sign its client assertion, so each carries two JWT stacks.
- `bms-gateway` has no passport, so it needs a third approach.
- The BMS Nest services use `@nestjs/jwt` without passport, so they change code anyway.

### Option 3: keys in Azure Key Vault, signing through the vault

welinc-auth never holds the private key. It asks Key Vault to sign each token (an HSM backed key), and rotation is a vault operation.

**Pros**:
- The strongest key protection: the private key can't be read, even by an admin of the Container App.
- Rotation, versioning and access logs come from the platform.

**Cons**:
- A network call to Key Vault on every token signed, with its own latency, throttling and outage mode.
- A managed identity and access policies per environment, and no local equivalent (local dev needs a second code path).
- Overturns 0001's `AUTH_SIGNING_KEYS`.
- New Azure surface for a team already learning Container Apps, with weeks left.

### Option 4: a shared `welinc-auth-verify` package instead of a reference module

Same as Option 1, but the check ships as a package installed from GitHub by tag.

**Pros**:
- One copy of the code, tested once; a fix reaches everyone through a version bump.

**Cons**:
- The repos are private, so every developer machine, every Docker build and CI need a GitHub token just to install.
- A release step, peer dependency clashes across Nest versions, and a fourth shared repo to own.
- A bug ships to all three systems at once.

## Rationale

Option 1 fits the forces best. The library choice follows from the other groups' real stacks. Every backend that calls welinc-auth must sign an assertion, which passport cannot do. `bms-gateway` will be client `bms` and has no passport at all. So a single library that signs and verifies is less to learn and less to copy than Option 2's two stacks. The engineer first leaned toward Option 2 because 0001 named it. Once the stacks were on the table, the engineer chose `jose` everywhere. The 0001 line is guidance, not a route or claim, so changing it is additive.

Option 3 is the right answer for a bank and the wrong one for this deadline. It adds a network dependency to every login and a second code path for local development. The threat it removes (someone with Container App secret access reading the key) is already a total compromise of that environment in this setup. It stays a follow up for after the capstone.

The reference module beats the package (Option 4) because of the private repo token problem in Docker and CI. That cost lands on all three groups every day; copying a folder costs it once. Scripted rotation beats a runbook alone because the dangerous step (promoting a key before verifiers have fetched it, or deleting one while its tokens are alive) is a timing rule people forget. The script refuses those steps, with an explicit `--now` path for a leaked key, where logging everyone out is the point. Rotation runs on demand plus one rehearsal on staging before launch, rather than on a calendar nobody will own after the capstone.

The interim login rule moves the portal's "which system" choice to the server because the portal only learns the roles after login. A second call would double count lockout attempts, and returning a token per system would leave several live tokens in `localStorage`. Removing the system guessing now, not in S5, follows from the hard switch: once every token carries `aud`, the guessing code can never run, and untested dead code in an auth guard is a liability.
