# 0012. Team Management reads drivers and helpers from Auth: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

The head developer's review of Team Management found that BMS kept its own copy of each driver
and helper: an Employee ID no other system has, a Total trips count nothing kept up to date,
stored initials, and its own name, email and contact number. Admin also added and deleted crew
in BMS with **Add Driver / Add Helper** and **Delete**, separately from their sign-in account.

Every driver and helper already has an account in Auth with the Driver or Helper role in BMS:
the mobile app (spec 0010) signs them in with it, and every local crew row already had its
`user_id`. Auth's directory (`GET /auth/directory/users`) lists everyone with a role in the
caller's system. It includes the phone number for a client holding `directory.contact`, and the
`bms` client already does. So BMS could read crew from Auth without any change to shared
services.

## Options considered

### Option 1: Keep BMS copies and sync them from Auth

Keep the name, email and contact columns, and copy them from Auth on a schedule or through the
directory change feed.

**Pros**:
- Screens keep reading one table; no directory call while listing crew.
- Works while Auth is down.

**Cons**:
- Two copies that can disagree until the next sync.
- A sync job, its cursor and its failures to look after.
- Doesn't answer the review: the details still live in BMS.

### Option 2: Read account details live from the directory (chosen)

BMS stores only its dispatch details. Each list read takes the BMS roster from the directory and
joins it to the BMS rows by `user_id`, creating a row for any account it hasn't seen.

**Pros**:
- One source of truth for name, email and contact number: the account.
- A new account shows up by itself, with no BMS step.
- Removing the role in the portal takes the person off the team and blocks assigning them, with
  no BMS clean-up.
- The erased-person job can go, since BMS keeps no personal details.

**Cons**:
- The crew list and assignment checks now depend on Auth answering. This was already partly
  true: the old code looked each linked person up to check their role.
- The directory allows 120 calls a minute per client, so the roster is reused for 30 seconds. A
  new account can take up to 30 seconds to appear.

## Rationale

Option 2 is what the review asked for. It also removes a class of bugs instead of managing it:
there is no copy to fall out of date.

### Smaller decisions

- **Employee ID removed.** Auth has no such field and no other system uses one. Rows are told
  apart by their BMS ID and their account.
- **Total trips removed, not computed.** The review allowed either. Nothing counted trips; the
  numbers were seed data, and only the availability window showed them. Counting from confirmed
  assignments can be added later if a screen needs it, without a stored column.
- **Initials worked out from the name** on screen. A stored copy would go stale when the name
  changes in the portal.
- **Delete removed along with Add.** While the person holds the role, the roster would recreate
  or revive any row BMS deleted. The portal is the one place to take someone off the team.
- **A BMS row is made when the account is first seen.** Admin then fills in the dispatch details
  with Edit. The alternative, a separate "set up" step, would bring back the Add button the review
  asked to remove.
- **One Edit button per row, no menu.** An "Edit account in portal" row action was tried and
  dropped: the edit form already has an **Edit in portal** link. A note next to the Account title
  ("Edited in the portal") was also dropped for the same reason.
- **Account fields refused on save** (400), not silently ignored, so a client still sending them
  finds out.
- **Leave requests keep the name as filed.** A request is a record, like the names on past job
  orders.
- **Rows without an account are turned off, not deleted.** Old assignments still point at their
  IDs. None exist on any local database today.
