# 0003. Rationale: sessions, refresh and logout

The decision record behind [index.md](index.md). `/develop` doesn't need this file.

## Context

The suite has no real session. welinc-auth signs a 15 minute access token at login, and since spec 0002 that token carries the system it is for. But nothing on the server remembers the login. welinc-auth has a `refresh_tokens` table that nothing writes, and no refresh or logout route. The portal hands the token to VRMS in the URL (`?token=`), and VRMS keeps it, the user and a last active stamp in `localStorage`. When the token runs out, the user logs in again. "Logout" only clears the browser. Idle sign out is a timer in each app (`SessionMonitor`, 15 minutes in VRMS, a different copy in the portal), so closing the laptop lid or opening a second tab defeats it.

That leaves four real problems. First, a token in a URL or in `localStorage` can be read by any script on the page and lands in history and logs. Second, there is no way to end a session: deactivating a user, a stolen phone or "log out everywhere" can't take effect until the token expires, and VRMS's account check (spec 0009) can only catch deactivation, not a logout. Third, users get a hard sign in every 15 minutes, or a token that lasts longer. Fourth, VMMS keeps its own refresh and logout copy, with sessions bound to web or mobile, and can't drop it until welinc-auth offers the same.

Contract 0001 already fixed the outside shape: 15 minute access tokens, a refresh token rotated on every use with a 10 second grace and reuse ending the session, a web session of 30 minutes idle or 12 hours, a 7 day rolling mobile session, an HttpOnly refresh cookie held by each system's backend, a 30 second session check, and the routes. What it left open is how welinc-auth stores and rotates all this, where S3 ends and S4 begins, and how the apps behave. While tracing the values, one contract rule turned out to break the idle rule: refreshes counted as activity, while a web app refreshes on its own every 15 minutes.

The forces: this is GA work where a mistake exposes every system; the team is small and the deadline is the end of November 2026; there is one welinc-auth replica today, but there may be more hosted; and IP addresses and user agents become personal data under the Philippine Data Privacy Act once stored.

## Options considered

### Option 1: Server side sessions, chained token rows, the web transport in S3

welinc-auth gets a `sessions` table (the `sid`), one row per issued refresh token linked to the one it replaced, and the login request and code tables. The grace answer is stored encrypted under the old token. S3 also builds the authorize routes, the SSO cookie and VRMS's session routes, so VRMS web runs on the real flow the moment S3 lands.

**Pros**:
- Every rule in the contract can be enforced: reuse of any old token maps to its session, logout and admin actions end the session everywhere, idle is tracked on the server.
- The grace answer works across replicas and needs no new secret.
- VRMS proves the whole web thread now (tracer bullet), and nothing built in S3 is thrown away in S4.

**Cons**:
- The biggest S row: four repos, four new tables, and a hard switch.
- One row per refresh means many rows (a 12 hour session refreshes about 48 times), so a purge job is required.

### Option 2: Server side sessions in S3, web transport left in S4

The same storage, but S3 stops at welinc-auth's routes and the session check. VRMS web keeps the `?token=` handoff with interim pings and logout until S4 builds the code exchange.

**Pros**:
- A smaller S3, and the S3/S4 split stays as the contract drew it.

**Cons**:
- A web app can only get a refresh cookie through the code exchange callback, so S3 can't give VRMS a real refresh or activity ping. It would need a throwaway path (refresh tokens in `localStorage`, or pings with the access token) that S4 then deletes.
- The thread isn't proven end to end until S4, against the project's build approach.

### Option 3: One row per session and client, current and previous hash

Instead of a chain, each (session, client) row keeps the current hash and the previous hash with a rotation time.

**Pros**:
- Fewer rows and a simpler query.

**Cons**:
- A token two or more rotations old matches nothing, so a thief replaying an older token is never detected, and the contract's "reusing an old token ends the session" holds only for the last one.
- The grace answer still needs the new token in a readable form, so it doesn't save the encryption step.

### Option 4: A hosted identity provider for sessions

Move sessions and the code flow to a hosted provider and keep welinc-auth as a user and role store.

**Pros**:
- Rotation, reuse detection and the code flow come built and reviewed.

**Cons**:
- Contract 0001 already chose welinc-auth as the authorization server, with ES256 keys and clients built in S2. Moving now discards S2 and reopens the contract.
- Each of the three groups would learn a new provider's SDK, paid tiers apply past the free limits, and per system tokens with server side idle tracking need custom work in most providers.

## Rationale

Option 1 is the only one that keeps every promise contract 0001 already made to the other groups. Reuse detection over the whole family needs the chain (Option 3 fails it for older tokens). Ending a session everywhere needs the `sid` on the server. And the 10 second grace across replicas needs the new token stored somewhere that only the old token can open. Encrypting it with a key derived from the old token (HKDF) gives that with no new secret: the database alone can't open it, and the row is wiped after 10 seconds.

The S3/S4 boundary was moved because of how the web flow works, not to make S3 bigger for its own sake. The refresh cookie is set by the system backend at the code exchange callback. Without the exchange there is nothing for refresh, activity or logout to run on, so Option 2 would build a throwaway path in S3 and remove it in S4. That breaks the Tracer Bullet approach the suite epic follows, and it would leave tokens in `localStorage` for one more row. With the transport in S3, S4 is left with what is actually about choosing a system: the launcher list, the launcher page and Switch system.

The contract's idle rule was corrected rather than worked around. If a background refresh counted as activity, the 30 minute cutoff could never fire for an open tab, which defeats the reason for idle sign out on a shared shop PC. Making only real input pings count for web (mobile still rolls on refresh, as designed) keeps the rule meaningful. The read only status route lets the warning dialog ask for the true cutoff without faking activity.

A hosted provider (Option 4) would be the right default for a team starting from zero, since rolling your own auth is a known failure pattern. Here the decision was already made in 0001 and S2 is built on it. The risk is managed instead by the GA workflow (fresh model review), standard building blocks (the OAuth code flow with PKCE, rotation with reuse detection as in the OAuth security best current practice), `jose` for every signature, and the e2e scenarios in the build plan.

The smaller calls follow the same forces. Lazy cutoffs mean correctness never depends on the job running. The advisory lock avoids a second scheduler. The cap of 10 sessions bounds the damage of a leaked password without bothering real users. The 90 day retention gives S7 and incident questions some history while keeping personal data bounded.

### Update (2026-11-08): the absolute end in the token answer

The build found that AC-16's cookie max age had no source: `session_expires_at` is the earlier of the two cutoffs, so backend-vrms couldn't learn the absolute end. The `/auth/token` user grants now also answer `session_absolute_expires_at` for web sessions (an additive field, contract 0001 stays version 1). The runner up was a cookie that lives 12 hours from each set, which outlives the session and breaks AC-16's wording. Decided by Samuel during `/develop`.
