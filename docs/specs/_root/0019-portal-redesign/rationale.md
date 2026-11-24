# 0019. Portal redesign: rationale

## Context

The portal is the first screen everyone in the suite sees, and the defense panel sees it first too. Spec 0016 gave it the Control room look, but the launcher, sign in and Suite management screens were still the pre redesign layouts. Rounds 12 to 37 (Nov 24) settled every screen on the canvas: the navy band launcher with a line drawing and livery trucks, sign in A with the branch map, four step forgot password, the Suite management shell, the filter popover, Add a user, the toasts, the 404 page, the reset email and the logo by place.

Three gaps sit under the boards. First, `screenForAnswer` sends anyone with one web system and no `ADMIN` there straight into that system, and the launcher answer doesn't say who is a suite admin, so a suite admin whose only role is temporary never reaches Suite management. Second, the Suite management strip shows counts, but the only route with them (`/auth/admin/report`) asks for the admin step up code, which would pop a prompt on the launcher. Third, Add a user checks the email as you type, but `users/lookup` matches partially and leaves out people who already hold the system, so it can't say "free" honestly.

The "Signed in until" pill drawn on early boards shows the 12 hour limit, while the 30 minute idle limit usually ends the session first, so the time is often wrong. The portal and web-vrms already warn with a banner two minutes before the cutoff (spec 0016 AC-12 to AC-12b), with careful timing, retry and cross tab rules.

The portal has no animation library (only `tw-animate-css` for shadcn parts). The launcher motion has three linked pieces: an arrival that must hand a truck into a running loop at the same speed, the loop itself, and a launch that plays while the browser leaves the page. The deadline is moving (final by Dec 20 at the latest, mock defense first), so the plan must survive losing the last milestone.

## Options considered

### Option 1: Restyle the existing screens in place

Keep the current launcher, sign in and shell structure and restyle them toward the boards, with CSS only motion.

**Pros**:
- Smallest change, no new dependency, no welinc-auth change.

**Cons**:
- The boards change structure, not only style (the strip, the switcher, the four step forgot password, the one screen dialog), so a restyle can't reach them.
- Leaves the suite admin gap and the step up prompt on the launcher.
- The arrival to loop hand off is hand written timing code.

### Option 2: Rebuild from the boards in milestones, motion last, with Motion and additive auth routes (chosen)

Build each board on spec 0016's tokens and components, add `suiteAdmin`, a counts only summary route and an exact email check to welinc-auth, and add Motion lazily as the last milestone.

**Pros**:
- Matches the picks exactly, closes all three gaps with additive changes.
- Motion handles exit animations, value hand off and reduced motion out of the box; loaded only where it's used.
- A static launcher is a complete, demoable state if motion slips.

**Cons**:
- A new dependency and three contract changes.
- More screens to verify against boards.

### Option 3: Rebuild with CSS keyframes and Web Animations only

As Option 2 but without a library: the loop as an infinite CSS translate, the arrival and launch with `element.animate()`.

**Pros**:
- No dependency; the lightest bundle.

**Cons**:
- Matching the arrival truck's position and speed into the loop, and cancelling cleanly on navigation or reduced motion, is custom code nobody else on the team knows.
- No exit animation story for the cards and toasts beyond what shadcn gives.

### Option 4: GSAP timelines

**Pros**:
- The strongest timeline tool, free since 2025.

**Cons**:
- Heavy for three short sequences, imperative and not idiomatic in React, and a second mental model beside Tailwind's motion tokens.

## Rationale

Option 2 is the only one that reaches the boards: they change structure, so restyling (Option 1) stops short, and the three data gaps need welinc-auth changes anyway. Each auth change is additive (a field and two read routes), which contract 0001 allows cheaply while the shared repos are closed.

Motion over CSS only (Option 3) is a team cost call: the arrival must hand off into the loop at the same speed, and the launch must cancel or fade cleanly under reduced motion. Motion's declarative API, `useReducedMotion` and `AnimatePresence` make that ordinary React code; with `LazyMotion` and `domAnimation` it costs about 15 to 20 kB, only on the sign in and launcher screens. GSAP (Option 4) solves a bigger problem than this one.

Ordering motion last answers the moving deadline: every milestone before it leaves a complete screen, and a parked truck launcher is already the reduced motion design, so it is not a stopgap.

**Smaller calls made in this spec** (the runner up in brackets):
- **Counts only summary route, no step up** (require step up): three numbers with no person data don't justify a code prompt on the front page; every list behind them still asks.
- **A new exact email check route** (reuse `users/lookup`): lookup matches partially and leaves out people already in the system, so it can't tell "free" from "already here"; a narrow route with five statuses gives the dialog honest answers and exposes less.
- **Arrival flag in memory only** (a `sessionStorage` flag): spec 0003 AC-36 keeps session hints out of storage, and a reload not replaying the arrival is the intended behaviour.
- **Launch 3 never delays navigation** (play, then navigate): the animation hides load time instead of adding it, and real links keep new tab clicks working.
- **The idle toast keeps 0016's timing modules** (rewrite them): only the surface changes; the retry, clock gap and cross tab rules were hard won and are tested.
- **A soft navy ring on the sign in split fields** (0016 AC-7's border only): the board shows it and sign in is a brand surface; working pages keep AC-7.
- **"Your profile" hidden until S23** (link to a placeholder): a menu item that lands on a 404 looks broken in a demo.
- **Code email layout for all four code emails** (reset only): they share helpers in `code-emails.ts`, and mixed looks read as a bug.

## Interview record (2026-11-24)

- Delivery: everything before the mock defense, motion as the last milestone.
- Motion library: Motion, lazy loaded. Launch 3: in scope.
- Strip counts: new counts only route, no step up; "Users need a look" is People's Needs attention group.
- Idle warning: 2 minutes, a toast in the portal and web-vrms, "Still there?" wording, the 12 hour end as the same toast without an action.
- Screen fix: `suiteAdmin` in the launcher answer.
- Reduced motion: parked scene. Loop: pause when hidden. Arrival: only right after sign in. Launch: about 900 ms with navigation at once. Phones: short band, parked trucks.
- Switcher: the held launcher answer. Email check: any admin, exact email only. Emails: all code emails, one layout. Wait: busy buttons and reloads, skeletons stay.
- Tab titles: page first, "WeLinc" last. Sign in messages: endings as toasts, errors inline. 404: any unknown address.
