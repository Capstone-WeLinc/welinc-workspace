# 0013. Additional service details: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

The client provided a service sheet ("View Details") listing, for each additional service, what
it includes, how it can be paid and what it excludes. The request was to show these on the
Additional Services tab of Services Offered (with a View icon) and in the New Booking wizard,
which already had a **View details** link.

The wizard's link opened empty. The details lived only in the wizard's code, and were replaced
with blank lists as soon as the services loaded from the backend, because the catalog
(`service_offerings`) had no place for them. Services Offered, where Admin manages these
services, couldn't show or edit them at all.

## Options considered

### Option 1: Keep the details in the web app

Store a fixed list of details in the web code, matched to each service by name, and use it on
both screens.

**Pros**:
- No backend change or migration.
- Quick to build.

**Cons**:
- Changing a detail needs a code change and a deploy.
- Renaming a service in Services Offered silently loses its details.
- Admin manages the service in one place, but its details in another.

### Option 2: Store the details with each service in the catalog (chosen)

Add three lists to `service_offerings`, return them from the existing catalog API, and let Admin
edit them in the Services Offered form. Both screens read the same data.

**Pros**:
- One source: what Admin edits in Services Offered is what customers see in the wizard.
- Details follow the service through a rename.
- Fixes the empty View details for good, not only for today's services.

**Cons**:
- A migration and API change in `bms-booking-service`.
- The wizard still needs a fallback list for when the catalog can't be read, which has to be kept
  in step with the seed.

## Rationale

Option 2 matches how the rest of the catalog already works: name, description, duration and
price come from `service_offerings`, so the details belong there too. The team chose it over the
quicker option when asked.

### Smaller decisions

- **Three plain text lists, not a structured schema.** The sheet is bullet lists of free text
  ("An additional PHP 100 per succeeding hour"). Lists keep Admin editing simple: one item per line.
- **The migration fills only empty details.** It runs on databases where Admin may already have
  typed details by the time it deploys; their text wins.
- **Two cash charges, not one.** The booking's cash-on-delivery surcharge stays ₱300, once per
  booking. The sheet's "additional PHP 500" is a separate charge per service, added when that
  service is paid in cash. A first version wrongly raised the booking surcharge to ₱500; the team
  corrected it.
- **The service cash charge is an amount in the catalog,** not read from the payment text. Admin
  can change it without the wording and the charge drifting apart, and services without it (the
  Motorized Helpers, Ocular Outside NCR) simply have 0.
- **The charge is saved with each booking,** not looked up when the booking is shown. A later
  catalog change doesn't rewrite what an old booking was charged, older bookings without it show
  as before, and Operations (who can't read the services catalog) still sees it on job orders.
- **The two Ocular Inspection versions on the sheet** map to the two ocular services: the first
  (cash with surcharge, GCash, bank transfer) to NCR, the second (cash, GCash, card, bank
  transfer) to Outside NCR. Decided by the team.
- **Unit to Unit Transfer is left out.** It's on the sheet but is a main service, shown on the
  Services tab and wizard step 1, not an additional one. The team chose not to add it now.
- **"Motorized Helper (990)" and "(1490)"** on the sheet are matched by price to Motorized Helper
  and Motorized Helper Premium.
