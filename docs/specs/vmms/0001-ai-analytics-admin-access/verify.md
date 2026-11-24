# Verification — 0001 AI/Analytics Admin and Operations access

Checks are pending. They are derived from the acceptance criteria in
[index.md](index.md). This documentation update did not run runtime or API
tests.

## Web access

- [ ] Sign in as Admin; confirm Analytics navigation and direct
  `/ai-analytics` access → AC-1
- [ ] Sign in as Operations; confirm Analytics navigation and direct
  `/ai-analytics` access → AC-1
- [ ] Confirm Chief Mechanic and Mechanic cannot use the web Analytics route
  or general fleet analytics API → AC-2

## API role boundaries

- [ ] Confirm Admin and Operations can call representative fleet-read
  analytics endpoints and Chief Mechanic and Mechanic receive authorization
  denial → AC-2
- [ ] Confirm Admin can trigger analytics sync while Operations and
  mobile-only roles are denied → AC-3
- [ ] Confirm work-order detail/advisory endpoints retain their current
  assignment checks and response filtering → AC-4
- [ ] Confirm the separate maintenance-schedule prediction endpoint remains
  Operations-only → AC-5

## Acceptance-criteria coverage

| AC | Planned evidence |
| --- | --- |
| AC-1 | Admin and Operations navigation and direct-route checks |
| AC-2–AC-3 | Fleet-read and Admin-only sync role matrix |
| AC-4 | Assigned work-order access regression checks |
| AC-5 | Maintenance-schedule prediction role check |

## Implementation evidence

The existing web navigation/route and analytics API fleet policy were
inspected and appear to match the approved decision. No code changes or
runtime checks were performed.
