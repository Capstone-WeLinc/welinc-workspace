# 0013. Outsourced provider lifecycle: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

Provider names are stored directly on maintenance schedules as historical
snapshots; schedules do not reference the provider catalog by ID. Renaming or
removing a provider already used by a schedule would therefore make the
catalog inconsistent with retained schedule history.

## Options considered

### Allow unrestricted rename and deletion

**Rejected**: removes or changes the current catalog identity while retained
work orders and maintenance logs still show the old provider name.

### Freeze used provider identity; allow status changes (chosen)

Allow edits and hard deletion only when no schedule references the provider.
When used, preserve the provider name and permit only activation changes.

**Advantages**:
- Protects historical schedule snapshots without a data migration.
- Lets Operations stop new assignments without rewriting history.
- Keeps the existing active-provider validation for new schedules.

**Tradeoff**: a provider with any retained schedule history cannot be renamed
or deleted. A future normalized provider-ID migration would need its own
approved data migration and history-preservation plan.

## Smaller decisions

- A soft-deleted schedule still counts as use because the schedule remains
  retained history.
- Matching is case-insensitive to align with provider duplicate validation.
- An existing schedule can keep its unchanged inactive provider when edited;
  the inactive provider cannot be chosen for a new schedule or replacement.
