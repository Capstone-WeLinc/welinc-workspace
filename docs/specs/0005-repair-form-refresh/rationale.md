# 0005. Rationale: repair form refresh

Decision record for [index.md](index.md). `/develop` does not need this file.

## Context

The New repair ticket page (`welinc-web-vrms/src/features/repair/pages/RepairFormPage.tsx`) is the entry point of VRMS: every repair starts here, and only admins use it. It is the last major repair screen still on legacy classes, inline styles and `LegacyButton`. It keeps 20 pieces of `useState`, validates by hand on submit and reports the first problem in one banner at the bottom, so on a phone you can't see what is wrong.

How it actually behaves today, read from the code:
- The plate is typed with a datalist, but the backend only accepts a registered, active plate, so a typo fails on submit with "Vehicle not found".
- Driver suggestions merge the database with a per browser localStorage list; the backend creates a new unverified driver for any new name.
- Garage, vehicle system, root cause and repair shop silently default to the first option, so a ticket can be saved with values nobody chose.
- Busy mechanics are disabled in the picker, enforcing the BRD's "one active ticket per mechanic" rule, which Jira (WL-201) replaced with showing open ticket counts.
- The client invents the repair number, although the server generates one when none is sent.
- The backend validates, then discards, priority, account type, corporation and repair shop: `RepairTicket` has no columns for them. Vehicle system and root cause survive only as text glued onto the issue description.

The forces: the scope row asks for the form "in the stakeholder approved layout, with pickers instead of typing", inline validation, and use with one thumb on a phone. The UI refresh epic is Facade (UI first on the data that exists). WL-201 asks for more than a refresh (issue types, saved priority, open ticket counts, Assigned or Open on create), but that work is feature 18, which depends on feature 16 (status lifecycle) and features 40 and 41 (lookup lists, common issues), none designed yet. No approved mockup exists in the repo or in Jira, so the layout follows `design.md` and the current field set. The app uses the declarative `BrowserRouter`, where React Router cannot block navigation.

## Options considered

### Option 1: Restyle in place

Swap legacy classes and inputs for spec 0001 components but keep the `useState` structure, the submit time validation and today's field behavior.

**Pros**:
- Smallest change and lowest risk.

**Cons**:
- Fails the scope's "validation is inline" and "pickers instead of typing" criteria.
- Keeps the typo prone plate field, the silent defaults and the hand built driver dropdown.

### Option 2: Rebuild on react-hook-form and the design system, on existing data

One react-hook-form form with a zod schema, searchable pickers over the four config endpoints and the fixed lists, a summary confirm, and a leave guard. No backend change.

**Pros**:
- Meets every scope criterion while staying Facade, so it ships without a backend deploy and doesn't wait on features 16, 18 or 40.
- The form can only send values the server accepts, removing the most common create errors.
- Follows the form path spec 0001 chose and spec 0004 already used for its dialogs.

**Cons**:
- Four fields keep looking real while the server throws them away.
- Needs a router change at the app's entry point for the leave guard.

### Option 3: Rebuild plus small backend reads

Option 2, plus new read only API fields (open ticket count per mechanic, vehicle model and last repair date, odometer) with no migration, as specs 0003 and 0004 did.

**Pros**:
- Delivers WL-201's open ticket counts and some WL-202 auto fill sooner.

**Cons**:
- Breaks Facade and adds a backend deploy.
- Designs part of feature 18's API ahead of feature 18's own spec, which would then have to work around it.

### Option 4: Fold feature 18 in

Build all of WL-201 here, including stored priority, issue types and status on create.

**Pros**:
- One pass over the form instead of two.

**Cons**:
- Blocked on feature 16 (status names) and feature 40 (issue type lists); turns a UI refresh into the core slice's biggest feature.

## Rationale

Option 2 is the one that meets the scope row's criteria inside the epic's Facade rule. The real user pain today is not missing WL-201 features but the form itself: typos that fail on submit, defaults that put wrong data on tickets, and errors you can't see on a phone. All of that is fixable on the data the API already returns. Options 3 and 4 pull feature 18's design forward before its dependencies (statuses, lookup lists) exist, which is how a refresh ends up redesigned twice.

The rebuild is the right size rather than a restyle because the scope demands inline validation, and that means one schema and field level state, which the current 20 `useState` hooks can't give without being rewritten anyway. react-hook-form and zod are already installed and are the project's chosen form path (spec 0001).

The cost is honesty about the four discarded fields. Hiding them would mean the client sends fixed values to satisfy the DTO, which is worse: the data would look recorded and be wrong. Keeping them, with a Follow-up to feature 18, keeps the layout final and the gap visible. The data router change is the other cost; wrapping today's `<App />` in a single splat route keeps it to two files, and the payoff is a leave guard that also catches the sidebar and the Back button, which is where half filled forms are actually lost.

On the smaller calls: the summary confirm stays because creating a ticket has side effects the user can't undo from the form (the vehicle is marked under repair, driver and outsourced mechanic records may be created, an audit row is written, tickets can only be cancelled), and a summary gives the confirm something worth reading. Busy mechanics become selectable because Jira, which wins over the BRD, dropped the one ticket rule. The cross check suggested making repair shop optional, since nothing stores it; it stays required because the DTO requires a non empty `shopName`, and an optional field would mean the client sends a made up value, the hidden wrong data this spec removes elsewhere. Per field list errors were chosen over one page error so a failed driver or mechanic list doesn't stop a ticket that can still be created.
