# 0005. Fuel receipt scanning and review

**Status**: Implemented; runtime OCR verification and production configuration pending
**Scope**: [Module 5: Fuel expenses and anomaly handling](../../../scope/vmms/index.md)

## Summary

Add an Operations-only receipt-scanning option to the existing fuel-entry
workflow. VMMS extracts a small allowlist of values from a receipt, presents
them as editable suggestions, and creates a fuel record only after the user
reviews the form and explicitly saves it. Manual entry remains available when
scanning is unavailable or the receipt cannot be read.

This is an approved extension to the existing fuel requirements. Receipt
scanning and image capture are implemented; live OCR accuracy still requires
verification with representative receipts.

## Baseline and rationale

- Module 5 covers receipt-based fuel entries and requires the existing fuel
  fields under FR-16.2. The current scope reconciliation records those fields
  as implemented.
- `FuelFillUp` stores the vehicle, station, date, liters, unit price, odometer,
  full-tank flag, and submitter. Receipt association was added by this
  extension.
- The Operations fuel-entry form accepts these values manually. Its total is
  calculated in the browser for display and again by the backend on save.
- Fuel creation is Operations-only. Existing private Azure Blob storage is
  used for fuel-anomaly attachments, not receipts.
- OCR is not required by the existing listed FR-16.* requirements. This
  proposal adds an assistive entry path without making OCR authoritative.

## User flow

1. Operations opens **Log Fuel Fill-up** and selects **Scan receipt** or
   continues with manual entry.
2. The user selects or captures a JPG, JPEG, or PNG receipt. VMMS sends the
   image to its backend for extraction; the image is not saved at this stage.
3. The form shows the image preview and any extracted suggestions. It marks
   low-confidence or missing values for review. The user can correct every
   field before saving.
4. The user still enters or confirms vehicle, odometer, filled-by, and
   full-tank status; these are not reliably available on a fuel receipt.
5. Station text is matched against active registered stations only as a
   suggestion. The user must select a registered station.
6. The user explicitly saves the reviewed entry. The backend validates the
   edited values, stores the receipt privately, creates the fuel record and
   receipt metadata, and writes the audit record. OCR never creates a fill-up
   by itself.
7. If scanning fails, times out, or returns unusable results, the user sees an
   actionable message and can enter the record manually without a receipt.

Receipt capture should be optional for the first release. Existing manual
entries and the existing JSON creation API remain supported.

## Extraction contract

Extract only fields that can reasonably appear on a fuel receipt:

- merchant or station name, as a text suggestion
- transaction date
- liters
- price per liter
- fuel product description, when recognized from the receipt line
- sales invoice number as the fuel entry's SI number, when recognized
- printed total, used only to compare with the server-calculated total

Do not treat the printed total as the saved total. The backend continues to
calculate `liters * pricePerLiter`. Return only the allowlisted fields; do not
persist payment-card numbers, customer details, full OCR text, or unrelated
receipt fields. Product and SI number remain editable and may be left blank
when the receipt model cannot identify them reliably. A text-based SI fallback
is used only when an explicit invoice-number label is present, and is marked
for review when the provider supplies no confidence.

Return field-level confidence where the provider supports it and mark
missing/low-confidence fields as needing review. Confidence is a review aid,
not proof that a value is correct. The user remains responsible for confirming
all values. Vehicle, odometer, filled-by, and full-tank status require manual
entry or confirmation.

## API, data, and audit impact

- Add an Operations-only `POST /fuel/receipt/scan` endpoint accepting a bounded
  image upload and returning only the allowlisted suggestions and confidence
  metadata, including optional product and SI number. It must not write a fuel
  record or persist the image.
- Add an Operations-only multipart `POST /fuel/with-receipt` path for the
  reviewed OCR flow. It accepts the edited fuel values and original receipt
  image together, persisting product and SI number through the existing fuel
  fields. Keep the existing JSON `POST /fuel` path working for manual entries.
- Persist an optional receipt attachment associated with a `FuelFillUp`, using
  private Blob storage and an authenticated download endpoint. Store only
  metadata and a random storage key in the database, never public URLs or image
  bytes. Receipt downloads are Operations-only.
- Save the fuel record, receipt metadata, and audit event consistently. If
  storage succeeds but the database write fails, delete the uploaded object
  using the existing compensating-cleanup pattern.
- Record the actor and receipt attachment in `FuelAuditLog`; do not store raw
  OCR text or sensitive OCR output in audit details or application logs.
- Configure OCR with `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` and the secret
  `AZURE_DOCUMENT_INTELLIGENCE_KEY`. Both must be set together; scanning stays
  unavailable when they are absent. The endpoint must target an
  organization-approved Azure region.
- Use an additive migration. Existing fill-ups remain valid with no receipt.
- No analytics, mobile, shared auth, portal, gateway, or cross-system API
  change is needed for the initial web flow.

## Security, validation, and failure handling

- Both scanning and saving require the VMMS Operations role on the backend.
- Enforce an image size limit (initial proposal: the existing 10 MB attachment
  ceiling), allow only JPG/JPEG/PNG, and validate actual file content as well
  as the declared MIME type. Reject unsupported and malformed images.
- Keep uploaded receipts in private storage. Authorize every receipt download
  through the backend; do not expose public or long-lived storage URLs.
- Do not log image contents, full OCR text, or extracted personal/payment
  information. The user authorized transmission of the complete receipt
  image to Azure Document Intelligence. Keep the resource in an
  organization-approved region and confirm any required organizational policy
  before enabling a deployment.
- Bound OCR processing time and requests. Surface provider outages, invalid
  images, and extraction failures explicitly; preserve the manual-entry path.
- Re-run all existing server-side validation at save time, including active
  vehicle/station checks, date checks, and odometer monotonicity. Never trust
  OCR values or client-calculated totals.
- Retain each receipt for the same period as its associated fuel record and
  delete it with that record under the approved retention policy.

## Acceptance criteria

1. Operations can scan a supported receipt or choose manual entry; other roles
   cannot call the scan, save-with-receipt, or receipt-download endpoints.
2. Scanning returns only the allowlisted fields and review metadata and does
   not create a fuel record or retain the image.
3. Extracted values are editable, and missing or low-confidence values are
   visibly identified. No value is committed without the user's explicit
   save.
4. Vehicle, odometer, filled-by, full-tank status, and registered station
   selection remain user-confirmed; a receipt cannot silently select an
   unregistered station.
5. The final save associates the submitted receipt with the created fill-up,
   computes total cost on the backend, and writes the existing fuel audit.
   Existing manual JSON creation and fill-ups without receipts continue to
   work.
6. OCR/provider failure leaves no fill-up behind and offers manual entry.
   Invalid or oversized files are rejected with a clear error.
7. Receipt files are private, downloadable only by authorized users through
   the backend, and never exposed through public URLs. Failure after blob
   upload does not leave an orphaned object.
8. OCR text and payment-card data are not persisted or emitted to application
   logs; receipt retention follows the approved policy.

## Affected repositories

- `welinc-backend-vmms`: OCR adapter/provider integration, guarded scan and
  save-with-receipt APIs, receipt persistence/migration, private storage,
  validation, audit, and cleanup.
- `welinc-web-vmms`: receipt selection/preview, scan state and errors,
  editable extracted suggestions, confidence/review indicators, and explicit
  save.
- No initial changes are planned for analytics, mobile, shared services, or
  other system repositories.

## Delivery plan

1. Approved decision: use Azure AI Document Intelligence, with authorization
   to send the full receipt image for extraction. Configure its endpoint for
   an organization-approved processing region before enabling scanning.
   Retain each private receipt for the same period as its associated fuel
   record. One optional receipt per fill-up is sufficient for the first
   release.
2. Before production rollout, run a small accuracy and latency pilot on
   representative, non-sensitive Caltex and Petron receipts. Measure date,
   liters, unit price, merchant, product, and SI-number extraction separately;
   keep human review mandatory regardless of pilot accuracy.
3. Implement the backend scan contract and safe file validation, then the
   editable web review flow.
4. Add the additive receipt metadata migration and final multipart save path;
   preserve existing manual JSON entry behavior.
5. Verify role boundaries, OCR errors/timeouts, low-confidence/missing fields,
   user edits, total-cost recomputation, blob cleanup, receipt authorization,
   and manual fallback before rollout.

## Approved decisions and rollout condition

- **OCR provider**: Azure AI Document Intelligence's receipt model is selected.
  The user authorized transmission of the complete receipt image for OCR.
  Keep the provider behind a VMMS service boundary so it can be changed
  without changing the web contract.
- **Processing region**: The deployment endpoint must target an
  organization-approved Azure region. The endpoint remains required
  configuration and scanning stays unavailable until configured; no region is
  inferred or hardcoded.
- **Retention**: Retain the original receipt privately for the same period as
  its associated fuel record. Receipt deletion must follow any future
  deletion/retention action applied to that record.
- **Receipt cardinality**: Start with zero or one optional receipt per fill-up.
  Add multiple attachments only if an operational use case requires it.
- **Representative formats**: The user supplied one Caltex and one Petron
  receipt as scan references. Product and sales invoice number are editable
  suggestions; no receipt value is treated as authoritative.

## Implementation and verification

The backend scan/save/download APIs, private receipt persistence, and editable
web review flow are implemented. Backend and web production builds pass.
Runtime OCR, database migration deployment, and representative-receipt
accuracy/latency checks have not been performed because no Azure resource
endpoint/key or receipt corpus was configured for this task. Production
rollout remains gated on configuring an endpoint in an organization-approved
region and completing the accuracy/latency pilot.
