# Additional service details: View details on Services Offered and in the booking wizard

Status: pushed, not yet in a pull request. Branch `BMS/additional-service-details` in
`welinc-backend-bms` and `welinc-web-bms`, into `development`.

Decision history: [rationale.md](rationale.md). Verification: [verify.md](verify.md).

Adds the client's service sheet ("View Details") to each additional service. Touches only
BMS-owned repos (`welinc-backend-bms`, `welinc-web-bms`). No change to shared auth, portal, the
suite gateway or the mobile app. One database migration in `bms-booking-service`.

## Problem

- The **Additional Services** tab on Services Offered showed only a name, description, duration
  and price. There was no way to see what each service includes.
- In the New Booking wizard (step 3), **View details** opened empty. The wizard had the details
  in its own code, but replaced them with blank lists as soon as the services loaded from the
  backend, which didn't store any details.
- The details the wizard did have were out of date with the client's sheet (for example
  "2 Manpower" instead of "2 staff members", and "Cash (with ₱300 charge)" where the sheet says
  an additional ₱500).
- Paying in cash only ever added the booking's ₱300 cash-on-delivery surcharge. The ₱500 that the
  sheet adds for paying some services in cash wasn't charged anywhere.

## What it does

### The details

Each additional service now has three lists, taken from the client's sheet:

| Service | Inclusions | Payment options |
|---|---|---|
| Basic Packing Service | 2 staff members, 1 cling wrap, 1 packaging tape, used cartons, 6 hours of packing service | Cash (with an additional PHP 500 charge), GCash or bank transfer (no additional charge) |
| Standard Packing Service | 4 staff members, 1 cling wrap, 1 packaging tape, used cartons, 6 hours of packing service | Same as Basic |
| Premium Packing Service | 4 staff members, 1 cling wrap, 1 packaging tape, 10 boxes, 1 roll of bubble wrap, used cartons, 6 hours of packing service | Same as Basic |
| Custom Packing Service | 1 staff member, 1 cling wrap, 1 packaging tape, 1 bubble wrap, 6 boxes, up to 6 hours of packing service | Same as Basic |
| Ocular / Site Inspection (NCR) | 1 motorized staff member, 2 hours of ocular/site inspection | Same as Basic |
| Ocular / Site Inspection (Outside NCR) | 1 motorized staff member, 2 hours of ocular/site inspection | Cash, GCash, credit/debit card, bank transfer |
| Motorized Helper (₱990) | 1 motorized staff member, fuel, up to 6 hours of service, an additional PHP 100 per succeeding hour | Cash upon delivery, GCash, bank transfer |
| Motorized Helper Premium (₱1,490) | Same as Motorized Helper | Same as Motorized Helper |

Every service excludes **condominium and subdivision entry and exit fees**.

The sheet lists Ocular Inspection twice with different payment options: the first version is
used for NCR, the second for Outside NCR. **Unit to Unit Transfer** is also on the sheet, but it
is a main service, not an additional one, so it was left out.

### Services Offered page (Admin)

Files: `src/pages/admin/ServicesOffered.tsx`, `src/components/services/ServiceDetails.tsx` (new),
`src/components/services/detailLists.ts` (new)

- On the **Additional Services** tab, each card has a **View** icon (eye) before Edit and Delete.
  It opens a window titled with the service's name, with four titled cards in the One UI section
  style (gold bar and navy uppercase title, no icon):
  1. **Overview**: labelled **Duration** (as a tag) and **Price** side by side, then
     **Description**
  2. **Inclusions**
  3. **Payment options**
  4. **Exclusions**

  A list with nothing in it shows "None listed." so every window has the same layout.
- The add/edit form for an additional service has a new **Service terms** section with three lists,
  Inclusions, Payment options and Exclusions. Each item is its own input row with a remove (×)
  button, and **+ Add item** adds a row below the list (pressing Enter in a row adds one under
  it). Removing the last row clears it instead, so there's always a row to type in. Blank rows
  are dropped on save. At 20 items the button reads "20 items at most" and is disabled.
- Every field in the additional service form is required, with a red asterisk and an error on
  leaving the field or saving, like the existing fields: Name, Description, Duration, Price,
  **Cash payment charge** (enter 0 when paying in cash adds nothing; an existing service opens
  with its amount, 0 included), and the three lists (at least one item, at most 20 items, 200
  characters per item, the backend's limits).
- The other two tabs (Services, Protective Materials) are unchanged.

### New Booking wizard (step 3)

Files: `src/components/booking/NewBookingWizard.tsx`

- **View details** under each additional service now shows the lists from Services Offered, so
  what Admin enters there is what the wizard shows.
- Each card's details open and close on their own, so two services side by side can both show
  their details at once. Before, opening one closed the other. A card no longer stretches to the
  height of an open card next to it.
- If the catalog can't be read, the wizard falls back to its built-in list, which now has the
  same details as the sheet.

### Paying in cash: two separate charges

Files: `src/components/booking/CostSummary.tsx`, `src/components/booking/NewBookingWizard.tsx`,
`src/pages/admin/ServicesOffered.tsx`

When the customer picks **Cash on Delivery**, the total gets:

1. **The cash-on-delivery surcharge: ₱300**, once per booking, as before.
2. **Each selected additional service's own cash charge.** ₱500 for the services whose sheet says
   "Cash (with an additional PHP 500 charge)": Basic, Standard, Premium and Custom Packing, and
   Ocular / Site Inspection (NCR). ₱0 for the rest.

Example: Basic Packing Service (₱3,450) paid in cash adds ₱300 + ₱500, so ₱4,250 before any truck,
materials or insurance.

- Each charge is its own line in the cost summary, named for what it's for so Customer Service
  can tell them apart: each service's fee first ("Cash payment fee for Basic Packing Service
  +₱500"), then "Cash on Delivery fee +₱300".
- The payment step's notice names them: "A ₱300 cash-on-delivery surcharge has been added to your
  total. Paying in cash also adds ₱500 for Basic Packing Service."
- The service charges are saved with the booking (`cashCharge` on each additional service), so
  the booking details and job order show the same lines later. Bookings made before this change
  have no service cash charges and look as they did.
- Admin sets each service's charge in the Services Offered form (**Cash payment charge**,
  required; 0 for none). The charge isn't shown in the View window; the Payment options list
  already says it.
- The ₱300 late cancellation/reschedule fee in the wizard's policy is a different fee and is
  unchanged.

### Backend (`bms-booking-service`)

- `service_offerings` gets `inclusions`, `payment_options` and `exclusions` (text lists, empty by
  default), and `cash_charge` (an amount, 0 by default).
- The catalog API returns and accepts `cashCharge` (0 or more). A `PATCH` without it leaves it
  alone.
- `POST /booking` accepts an optional `cashCharge` on each additional service and saves it with
  the booking.
- `GET /bms/config/services-offered` returns them as `inclusions`, `paymentOptions` and
  `exclusions`. `POST` and `PATCH` accept them: at most 20 lines each, 200 characters per line,
  trimmed, blank lines dropped. A `PATCH` changes only the lists it sends. Re-adding a removed
  service replaces its old lists.
- `prisma/seeds/catalogs.sql` inserts the details with the default services, for new databases.

## Database migration

`bms-booking-service/prisma/migrations/20261125120000_service_offering_details/migration.sql`

1. Adds the three list columns, empty by default, and `cash_charge`, 0 by default. Nothing is
   dropped.
2. Fills in the sheet's details for the eight services, matched by name. A service whose lists
   aren't all empty is left alone, so nothing Admin entered is overwritten.
3. Sets the ₱500 cash charge on the five services above, only where it's still 0.

Running the old code on the migrated database is safe: it ignores the new columns.

## Testing

- `bms-booking-service`: typecheck clean; new tests in `src/catalog/catalog.details.spec.ts`
  (6): lists trimmed and blank lines dropped, empty lists by default, re-adding a removed service,
  partial updates, the cash charge (saved as a number, 0 by default, kept on a partial update,
  no negatives), and the 20-line / 200-character limits. The full backend CI sequence passes
  locally.
- The migration was applied to the local booking database: all eight services got their
  details, with the NCR and Outside NCR ocular versions as above. The updated seed was run on a
  deleted service inside a transaction (rolled back): it re-created the service with its details.
- `welinc-web-bms`: typecheck clean; changed files lint with no errors and no new warnings (the
  10 there were there before); unit tests pass (18).
- Not yet checked by hand in the running app.

## Deploy notes

- Run `prisma migrate deploy` for `bms-booking-service` with the new code.
- Bookings made before this change are unaffected: their cost breakdown and total look as before.
- **Check with the client:** Ocular / Site Inspection (NCR) costs ₱300 but adds ₱500 when paid in
  cash. That follows the sheet's first Ocular version, as the team decided, but it's unusual.
- The mobile app doesn't use the cash charges or these details, so it's unaffected.
