# 0007. App initiated login and the portal launcher: rationale

The decision record behind [index.md](index.md). `/develop` builds from index.md and can skip this file.

## Context

WeLinc has three systems on one login. Some people work in more than one: every mechanic holds VRMS and VMMS, some chiefs and admins hold two, and `multi.lead@` holds all three. Until now welinc-auth picked a system for them in a fixed order (`PICK_ORDER`), so a VMMS Operations person who is also a VRMS Chief Mechanic always landed in VRMS with no way to choose, and the VRMS "switch to VMMS" link could never show, because the VRMS token only carries VRMS roles.

Spec 0003 already built the hard part of the web login: each app starts its own sign in (`/<sys>/session/start`), welinc-auth checks the exact redirect address, the app gets a one time code back and swaps it on its backend, and return paths are checked against the app's own origin. Tokens never touch a URL. What is missing is the human side: where someone with several systems chooses, how they move between systems, and what the portal shows when an app sends them back with an error while they are still signed in.

The forces: the change crosses the shared repos (welinc-auth, the portal) and VRMS, so it must keep the contract stable for VMMS and BMS, who move in S11. It must add no role or permission. It must not open a redirect hole, since the portal is the one page every system trusts. One system users (most office staff) must not get an extra click. And the portal's look is weak today (gradients and glows that design.md bans, a hand made toast, Tailwind v3 while web-vrms is on v4), and this is the natural time to fix its foundations.

Not deciding means people in several systems keep landing in whatever system the fixed order picks, S11 has no picture of how a moved app fits in, and the portal stays on a stack nobody else uses.

## Options considered

### Option 1: A portal launcher on top of the app initiated login (chosen)

Each app keeps starting its own login. The portal, when opened directly, asks welinc-auth which systems you hold and shows a launcher for two or more, or forwards you for one. Apps get a `user.systems` list in their grant answer so they know whether to show Switch system, which links back to the launcher.

**Pros**:
- Matches the app launcher pattern of Okta and Microsoft My Apps, which people already know.
- Reuses everything spec 0003 built; the code flow doesn't change.
- Only welinc-auth knows who holds what; the portal and apps just read it.
- Cards open the app's own address, so an app that already has a session opens instantly, and the portal never mints codes itself.

**Cons**:
- A new answer shape for `/auth/login` and `/auth/sso`, so welinc-auth and the portal merge together.
- One more page to design, test and keep accessible.
- Until S11, cards for VMMS and BMS open their own logins.

### Option 2: A picker during login (the original VRMS feature 60)

After the password, the portal asks which system to open, every time, for anyone with two or more systems.

**Pros**:
- No page to come back to; the choice sits in the login itself.
- No `from` tag or focus checks.

**Cons**:
- It asks even when an app started the login and already knows where to go, which breaks deep links or needs special cases.
- No way to move between systems later without signing out, or reopening the picker through a hidden path.
- People who always work in one of their systems answer the same question every morning.

### Option 3: A separate login page per system

Each system draws its own login form and talks to welinc-auth directly, with no shared portal.

**Pros**:
- Each group controls its own login look.
- No shared page to coordinate.

**Cons**:
- Passwords typed into three different front ends, and three copies of the lockout, OTP and reset screens to keep in step.
- No single sign on across systems: moving means signing in again.
- Throws away the SSO cookie and code flow that S3 built.

### Option 4: A launcher that starts the login itself (identity provider initiated)

The launcher's cards link straight to each backend's `session/start`, or welinc-auth mints the code when you click.

**Pros**:
- Saves one refresh call when opening a system.
- The portal can promise a fresh session per click.

**Cons**:
- The portal must know every backend's route, coupling it to each system's prefix.
- It mints a new code even when the app already holds a session, piling up refresh tokens.
- Identity provider initiated logins are the classic place for login CSRF and mixed up sessions; app initiated keeps the app in charge of its own `state`.

## Rationale

Option 1 is the only one that keeps both halves of what S3 built (app initiated logins with checked return paths, and one SSO session across systems) while giving people with several systems a real choice. Options 2 and 3 each break one of those: the picker gets in the way of deep links and offers no way to move later, and per system logins undo single sign on. Option 4 keeps the launcher but gives up the property that only the app starts its own login, which is what makes the redirect checks and `state` cookie meaningful.

Engineer choices that shaped it: the Quiet workspace look (white canvas, greeting, large cards) for the launcher, built to design.md; the login kept as it is, only its states improved, which leaves a documented design.md exception for the login hero; the portal moved to Tailwind v4 and shadcn now rather than later; the order BMS, VMMS, VRMS; a "You're here" tag when coming from Switch system; a confirm before signing out everywhere; and focus checks so a forgotten tab stays honest.

One choice was reversed during the conversation. A "coming soon" card and an `sso_ready` flag for VMMS and BMS were considered, to avoid sending people into apps that don't use the shared login yet. You decided against it: the launcher should show the contract as it is meant to work, and VMMS and BMS adjust their apps in S11. That keeps welinc-auth free of a temporary flag that would only exist for a few weeks, at the price of a second password prompt for anyone who opens VMMS or BMS from the launcher before S11.
