# 0009. Configurable settings catalog: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

VMMS currently stores the fuel anomaly percentage and maintenance costing
threshold in separate domain-specific records. Both have distinct validation,
Admin edit controls, and audit history. Vehicle maintenance defaults are
per-vehicle/per-checklist operational data.

## Options considered

### Replace domain settings with one generic settings table

**Rejected**: creates a migration and duplicates or weakens existing
domain-specific validation and audit behavior.

### Catalog the existing global settings (chosen)

Expose stable metadata and current values through a typed registry, and
delegate writes to the existing domain services.

**Advantages**:
- Adds a single discoverable catalog without duplicate persistence.
- Preserves existing audit, API, and computation boundaries.
- Allows settings UI to render from server-owned metadata.

**Tradeoff**: each new setting still needs explicit registry metadata and a
domain update handler; this is intentional rather than arbitrary key/value
configuration.

### Include vehicle defaults

**Rejected**: vehicle/category checklist intervals are relational records with
Operations ownership and are already governed by their own workflow/spec.

## Smaller decisions

- Keep the legacy setting APIs working.
- Use stable snake-case keys; do not use database model names as public keys.
- Keep Operations read access, matching existing setting display behavior,
  while retaining Admin-only writes.
