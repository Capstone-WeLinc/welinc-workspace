# 0006. Bulk fuel statement import: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Fuel statements contain many fill-ups and may use varied layouts across
worksheets. The parser must recognize supported columns without treating
unrelated text or totals as transactions. Historical and duplicate readings
must preserve existing fuel and vehicle data.

Operations needs a resumable review flow because workbook cleanup and
correction require multiple steps and may end in partial success.

## Options considered

### Option 1: Import workbooks directly on upload

Parse and save all rows during one request.

**Pros**:
- Smallest implementation.
- Fewest UI states.

**Cons**:
- No visible station or vehicle mapping review.
- One bad row can block or obscure the whole batch.
- Operators cannot edit OCR/parser guesses before saving.

### Option 2: Preview, editable review, private resumable draft, row save (chosen)

Parse workbook rows without writes, let Operations map stations and vehicles,
persist editable draft state, and save valid rows independently.

**Pros**:
- Makes incomplete and malformed values explicit.
- Supports multiple worksheet layouts and manual corrections.
- Allows partial success and resumption.
- Keeps the source workbook private and unpersisted.

**Cons**:
- Requires draft persistence, mapping, pagination, and per-row result states.
- Save-time validation must repeat preview checks against current database
  state.

### Option 3: Restrict import to one canonical workbook template

Require exact headers and a single worksheet.

**Pros**:
- Simple parser and validation.

**Cons**:
- Does not support supplied or real-world workbook variations.
- Creates user friction without an approved input standard.

## Rationale

Option 2 is the complete operator workflow. Preview and draft persistence do not
create fuel records. Every save revalidates against current vehicles, stations,
history, and submitted rows, and records each result independently.

The source workbook is not retained, so imports persist only reviewed values
and mapping state. This keeps sensitive statement data bounded while allowing
Operations to resume and correct work safely.
