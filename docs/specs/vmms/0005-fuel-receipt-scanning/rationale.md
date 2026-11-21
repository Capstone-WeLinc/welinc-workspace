# 0005. Fuel receipt scanning and review: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Operations enters fuel fill-ups manually in VMMS. Receipts contain useful
suggestions for station, date, liters, unit price, product, and sales invoice
number, but OCR is not guaranteed and a receipt is not authoritative for
vehicle, odometer, filled-by, or full-tank status.

The backend already owns private storage patterns, fuel validation, audit,
and total-cost calculation. A receipt feature should assist entry without
changing those responsibilities or bypassing human review.

## Options considered

### Option 1: OCR with automatic fuel-record creation

Upload a receipt, extract values, and create the fill-up immediately.

**Pros**:
- Fastest data entry.

**Cons**:
- OCR uncertainty can create incorrect fuel records.
- Vehicle, odometer, and station context is missing or unreliable.
- Blob storage and database failures can leave unsynchronized results.

### Option 2: OCR suggestions plus explicit reviewed save (chosen)

Extract an allowlist of editable suggestions, require confirmation in the fuel
form, and use existing server validation and manual JSON save behavior.

**Pros**:
- Keeps a person responsible for confirming all values.
- Preserves manual entry and existing JSON API compatibility.
- Lets the user retry or cancel when provider/OCR results fail.

**Cons**:
- OCR accuracy and provider configuration require a rollout pilot.
- A private multipart save path and compensating cleanup are needed.

### Option 3: Manual entry only

Do not add OCR or receipt storage.

**Pros**:
- No provider dependency or private-image handling.

**Cons**:
- Does not provide the approved receipt-entry productivity feature.
- Misses the approved optional receipt attachment flow.

## Rationale

Option 2 makes OCR advisory rather than authoritative. The backend controls
role checks, file type and size, private storage, final validation, total-cost
calculation, and audit creation.

Azure Document Intelligence is selected behind a VMMS service boundary. The
complete image is sent to an organization-approved region, low-confidence values
remain editable, and production rollout remains gated on provider configuration
and a representative receipt pilot.

## Approved hardening extension

The current validation checks extension, declared MIME type, and file
signature, but those checks do not prove that the complete image decodes.
Fully decode supported images with strict size/dimension limits before OCR or
storage, but do not re-encode them: receipt fidelity and the existing private
original-receipt retention contract take precedence over metadata stripping.
Rate-limit final uploads per actor at the same initial five-attempts-per-minute
threshold used for scanning. Apply validation and throttling on the backend;
the browser's file picker is not a security boundary.
