# Verify: Additional service details · spec 0013

Steps derived from [index.md](index.md). Ticked items were checked on 2026-11-25 on the local
stack.

## API / automated

- [x] `POST` and `PATCH /bms/config/services-offered` save `inclusions`, `paymentOptions` and
  `exclusions`, trimmed and without blank lines (`catalog.details.spec.ts`)
- [x] A new service without details gets empty lists; re-adding a removed service replaces its
  old lists (`catalog.details.spec.ts`)
- [x] A `PATCH` changes only the lists it sends (`catalog.details.spec.ts`)
- [x] More than 20 lines, a line over 200 characters, or a non-list is refused
  (`catalog.details.spec.ts`)
- [ ] `GET /bms/config/services-offered` returns the three lists through the gateway

## Database

- [x] The migration applies to the local booking database; all eight services get the sheet's
  details, with the NCR and Outside NCR ocular versions as in the index, and a ₱500 cash charge on
  exactly the five services listed (the others 0)
- [x] The updated seed re-creates a missing service with its details (run in a rolled-back
  transaction)
- [ ] A service whose details were already edited is left alone by the migration

## Web / manual

- [ ] Services Offered → Additional Services: each card has a View (eye) icon; it opens the
  service's description, Inclusions, Payment options and Exclusions
- [ ] The View icon isn't on the Services or Protective Materials tabs
- [ ] Editing an additional service shows the three lists, one item per line; saving changes what
  View shows
- [ ] Adding an additional service with any field empty shows its error and doesn't save; an
  empty list shows "Add at least one item."
- [ ] Details lists: + Add item adds a row; × removes one (the last row is cleared instead);
  Enter adds a row below; the button disables at 20 items; an item can't go over 200 characters
- [ ] Editing Motorized Helper opens with Cash payment charge 0 and saves without errors
- [ ] New Booking wizard, step 3: View details under each additional service shows the same lists
  as Services Offered
- [ ] Opening View details on two services side by side shows both; closing one leaves the other
  open
- [ ] Payment step: Cash on Delivery still reads "Pay on pickup (+₱300)"
- [ ] With Basic Packing Service selected and Cash on Delivery: the cost summary shows
  "Cash payment fee for Basic Packing Service +₱500" followed by "Cash on Delivery fee +₱300",
  and the total includes
  both; the notice names both
- [ ] With Motorized Helper and Cash on Delivery: only the ₱300 surcharge is added
- [ ] Paying by GCash: no cash charges at all
- [ ] The saved booking's details show the same lines and total
- [ ] Services Offered: the form has Cash payment charge; the View window has no separate cash
  line and no icons beside the card titles (the gold bar stays)
- [ ] An existing cash booking still shows its stored total and its old lines

## Commands

- [x] `bms-booking-service`: `npx tsc --noEmit`
- [x] `bms-booking-service`: `npx jest src/catalog` (6 tests)
- [x] `POST /booking` keeps `cashCharge` on an additional service (`booking.service.ts`); not yet
  covered by a test
- [x] `welinc-web-bms`: `npm run typecheck`
- [x] `welinc-web-bms`: eslint on the changed files (no errors; 10 warnings, all pre-existing)
- [x] `welinc-web-bms`: `npm test` (18 tests)
- [x] `welinc-web-bms`: full CI sequence run locally (`npm run lint`: 0 errors; `typecheck`;
  `npm test`; `build:prod` with the CI build settings)
- [x] `welinc-backend-bms`: full CI sequence run locally (`npm run lint:ci`, `typecheck`,
  `build`, `test`; booking service 99 tests, up from 93)
