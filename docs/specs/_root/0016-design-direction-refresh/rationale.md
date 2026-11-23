# 0016. Design direction refresh: rationale

The decision record behind [index.md](index.md). `/develop` doesn't read this file.

## Context

- **The problem.** You said the screens look plain, stale and AI made. The cause is the suite `design.md` itself: together, its rules ask for the exact look AI tools fall back to. Inter as the only font with titles capped at 24px, a slate canvas with white hairline bordered cards and `shadow-xs` at most, small uppercase labels, and KPI cards with an icon in a tinted square. Its ban list covers the 2023 clichés (gradients, glass, purple) but requires the 2025 ones, and it is almost all "don'ts" with no signature "dos".
- **The forces.** Mock defense Nov 28, integration Dec 4, final Dec 5, with hosting still unfinished, so the rollout must not block deploy work and must wait for your go. Two separate repos (portal, web-vrms) share one look but have no shared package. Mechanics read the app on phones in garages: weak connections, bright light, thumbs. The guardrails that work today (tokens only, the lint that bans raw colors, contrast, status pills, four states, touch targets, no cards in cards) must survive.
- **What not deciding costs.** S19, S20, S21 and feature 70 would each invent their own look on top of the old rules, and the panel sees a template.
- **How it was decided.** Eleven rounds of clickable boards on the canvas "WeLinc design directions" (rounds 1 to 9 recorded in the Nov 18 handoff, rounds 10 and 11 in this session).

## Options considered

### Option 1: Rewrite the standard in place, then sweep every page (chosen)

Keep shadcn, Tailwind v4 and the token lint; replace the token values, the fonts and the component rules; add a Signature section, the missing components and a token check.

**Pros**: reuses everything that already works (lint, tokens, components); one standard for both apps; the boards already prove the look.
**Cons**: a large UI sweep across two apps; it only changes what the standard says, so rules need discipline as much as tokens.

### Option 2: New colors only

Keep `design.md` and swap a few values (canvas, shadows, gold use).

**Pros**: small, fast, low risk.
**Cons**: the "AI made" feel comes from type, surfaces and patterns, not color; the screens would still read as the starter.

### Option 3: Adopt a ready made theme or dashboard kit

Take a published shadcn theme or a dashboard component kit and follow its look.

**Pros**: polished parts out of the box.
**Cons**: it is someone else's look, so it is exactly the "seen it before" problem; it fights the token lint and the existing components.

### Option 4: A custom component library from scratch

Drop shadcn and build WeLinc's own primitives.

**Pros**: full control.
**Cons**: far too much work before the defenses; rebuilds accessibility that radix already gives for free.

Enforcement was weighed the same way: document only (weakest), enforce going forward with old pages as debt, or one sweep of every page. You chose every page, started on your call.

## Rationale

- **Why Option 1.** The look problem sits in the rules, not the stack, so the cheapest real fix is new rules on the same stack. The lint and tokens from VRMS spec 0001 already make a rule change reach every page through the base components, which is what makes a sweep of two apps possible in the time left.
- **Why IBM Plex (F1) and not Inter.** Inter is the most used UI font today, so it reads as "any app". Plex is one engineered family with a matching mono, made for tools, readable at 14px and on phones, and the mono gives the Signature "printed job card" numbers with no second family to match. Runner up: Barlow (road sign feel), which reads as more decorative in dense tables.
- **Why text went back to Inter, with Plex Mono kept (2026-11-23).** Once Plex Sans was in both apps, you chose Inter for text, the font staging already uses. Inter is narrower, so dense tables keep their widths, and the text looks like what the groups and the panel have already seen. The mono stays Plex because it carries the Signature numbers on its own. Before milestone 1, `--font-mono` named Plex Mono but nothing loaded it, so numbers fell back to the system mono, which differs between Windows and Mac. The Plex reasoning above still explains the board picks; it no longer decides the text font. Runner up: keep Plex Sans as built (no extra work, but you didn't want it).
- **Why gold stays rare.** If gold marks the primary button everywhere, it stops meaning anything. Kept to hot counts, the draft bubble, the logo and the commit, gold becomes a signal: when you see it, something waits on you. Gold text on white also fails contrast, so it stays a fill with navy text.
- **Why uppercase labels stay (L3).** You compared L1 to L3 on a real screen and preferred L3. It keeps one old tell, but the fonts, the surfaces and the Signature carry the change, so the cost is small.
- **Why the KPI card is K15 with the whole card a link.** You picked K15 on `Kpis13` after K0 to K14. A number with no way into it is a dead end on a dashboard; making the card a link adds no visual noise. The period moves to a dashboard filter, so no card has to say "last 7 days".
- **Why one neutral role chip.** Custom roles (S21) make a fixed color per role impossible to keep; color is reserved for status.
- **Why a 640px save bar.** You picked it on `SaveWidths10`; long role names get an ellipsis in the sub line, and the full name stays in the change list header.
- **Why icon collapse stays.** You chose to keep it, without the flyouts you had ruled out (N2, N6); labels hide and tooltips carry the names.
- **Why the selected state splits (A).** Moving between views and picking a value are different jobs; the white pill reads as "where you are", solid navy as "what you chose". Both pass contrast.
- **Why a markdown table plus a check, not a package.** A shared npm package needs a registry and release steps the team has no time for. The table is already the human source; a small script turns it into a gate.
- **Why one motion curve.** One enter curve makes everything feel like one product. The two old curves (`ease-snappy`, `ease-drawer`) differ too little to justify two names.
- **Why S1 for the switch.** Every approved board uses it, and position plus the off track border already show the state without color. S3 stays a fallback.
- **Why `muted-foreground` darkens to `#5b6779`.** The cross check found that `#64748b` falls to about 4.4:1 on the new canvas, table header and navy tint; `#5b6779` passes 4.5:1 on all of them and still reads as secondary.
- **Why destructive moves to `#b42318`.** It matches the error color on every board and passes AA on its tint, so one red serves errors and destructive actions.
- **Why Admin calls `/auth/sso` on a cold mount (2026-11-23, AC-12b).** The build found that Admin's mount check is `GET /auth/admin/me`, which answers admin standing, not session times, so a reload or deep link into Admin had no cutoff. One `/auth/sso` call, only when the store is empty, keeps the launcher answer the one source of session times and needs no second contract change. Runner up: add the three fields to `/auth/admin/me` (zero extra calls, but session timing on an admin standing route and two answer shapes feeding one store). The cost is one call per reload, well inside `/auth/sso`'s 60 a minute per address.
