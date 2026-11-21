# Verify: Fuel receipt scanning and review · spec 0005

Steps derived from the acceptance criteria in [index.md](index.md).

## API / automated

- [ ] Exercise receipt scan and save/download endpoints as Operations; confirm
  Admin and non-Operations roles receive denial → AC-1
- [ ] Scan representative receipts and confirm only allowlisted field suggestions
  and confidence metadata are returned; confirm no image or fill-up is written
  → AC-2
- [ ] Edit extracted fields and confirm missing/low-confidence values remain
  visibly marked until explicit save → AC-3
- [ ] Confirm vehicle, odometer, filled-by, full-tank, and active station remain
  explicitly supplied or confirmed; confirm OCR cannot select an unregistered
  station → AC-4
- [ ] Save a reviewed receipt entry; confirm receipt metadata, fill-up, audit,
  and server-calculated total are consistent; confirm manual JSON entry remains
  working → AC-5
- [ ] Test OCR outage, timeout, unusable result, malformed/unsupported/oversized
  files, and manual fallback; confirm no orphan fill-up is created → AC-6
- [ ] Download a receipt only through the authorized backend endpoint; confirm
  private storage and no public URLs; test blob/database cleanup failures →
  AC-7
- [ ] Search logs and persistence for raw OCR text, payment-card data, and image
  bytes; confirm they are not stored or logged → AC-8
- [ ] Submit truncated images with valid headers and verify full decode rejects
  them before OCR or persistence; exercise dimension/pixel limits while
  confirming valid uploaded bytes are unchanged → AC-9
- [ ] Exceed the final-upload per-actor limit and confirm the request is
  rejected with a rate-limit response before storage or database writes →
  AC-9

## UI / manual

- [ ] Scan a JPG/JPEG/PNG receipt and inspect the editable review form
- [ ] Change extracted values before save and confirm the backend accepts the
  final reviewed values rather than original OCR values
- [ ] Verify mobile or browser provider-failure messaging offers manual entry

## Runtime / rollout

- [ ] Configure Azure Document Intelligence endpoint and key for an
  organization-approved region
- [ ] Run the approved representative-receipt pilot and measure field accuracy
  and latency
- [ ] Verify the private blob migration and compensating cleanup in the deployed
  environment

## Commands

- [x] Build `welinc-backend-vmms`
- [x] Build `welinc-web-vmms`
- [ ] Run the focused receipt scan/save/download test suite
- [ ] Apply and verify the additive receipt migration
- [ ] Run the representative-receipt accuracy and latency pilot

## Acceptance-criteria coverage

- AC-1 through AC-8 by the role, extraction, review, persistence, privacy,
  fallback, and cleanup checks above.
