# 0007. Knowledge base as a fix library that fills itself from repairs

**Date**: 2026-10-25
**Updated**: 2026-10-30 (`KNOWLEDGE_SETTINGS` replaced by stored settings, spec 0012 AC-3)
**Status**: In Progress

## Summary

This spec replaces the knowledge base page (today a browser only list of made up SOPs) with a real library of **common issues**: known problems with their symptoms, fix steps, parts and safety notes, stored in welinc-backend-vrms and shared by everyone. The library is used inside daily work: the repair form picks an issue instead of typing (Jira WL-702), the ticket shows the known fix as a checklist, and every finished repair adds a "What fixed it" note that turns recurring unknown problems into suggested new entries. History numbers (how often seen, typical hours and cost, vehicles that keep coming back) are calculated from real tickets. It covers scope features 15 and 41, adds the `CHIEF_MECHANIC` role (the role part of feature 17), needs no AI, and is the data the AI rework (feature 3) will build on.

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Requirements

**User stories**:
- As a mechanic, I want to see the known fix for an issue right on my ticket, as a checklist, so that I don't have to search anywhere while I work.
- As a mechanic, I want to search the library by describing what I see, so that I can find a fix for a problem I don't know the name of.
- As an admin creating a ticket, I want to pick a common issue instead of typing, so that the category, description and priority fill in and every ticket is logged the same way.
- As an admin or chief mechanic, I want recurring problems that have no entry to show up as suggestions, so that the library grows from real repairs without anyone sitting down to write it.
- As an admin or chief mechanic, I want each entry to show how often we see it and what it usually takes, so that estimates and decisions come from our own fleet.
- As a mechanic, I want to suggest a change when an entry is wrong, so that what I know on the floor reaches the library.

**Acceptance criteria**:

*Roles*

- **AC-1**: `CHIEF_MECHANIC` is added to the `UserRole` enum in welinc-auth (schema plus migration) and welinc-backend-vrms (schema plus migration), and to `UserRole` in `welinc-web-vrms/src/types/index.ts`. The Users page (spec 0006) offers it: `UserFormDialog` role options read Admin, Chief mechanic, Mechanic; `EDITABLE_ROLES` and the role filter in `UserListFilters` include it; `RoleBadge` already has its style. The open work check in `openWork.ts` and `useUserActions.ts` treats `CHIEF_MECHANIC` like `MECHANIC`. welinc-auth's seed gains `vrms.chief@welinc.com` (role `CHIEF_MECHANIC`, system `VRMS`), and welinc-backend-vrms's `prisma/seeds/users.seed.ts` gains a matching VRMS `User` row (same email) plus an in house `Mechanic` row linked to it by `userId`, the same way the seeded mechanics are made, so `getMechanicForUser` finds it.
- **AC-2**: Until feature 17 ships, a chief mechanic has the mechanic rules on tickets. Every `@Roles(UserRole.ADMIN, UserRole.MECHANIC)` in `repairs.controller.ts` and `config.controller.ts` also lists `CHIEF_MECHANIC`, and `RepairsService.isMechanic` returns true for `MECHANIC` or `CHIEF_MECHANIC`, so a chief sees only assigned tickets, no costs, and cannot complete or cancel. In the web app, a helper `isMechanicRole(role)` in `src/lib/roles.ts` returns true for both, and `DashboardPage`, `getNavSections` and `nextAction` callers use it, so a chief gets the mechanic dashboard and nav.
- **AC-3**: **Editors** are `ADMIN` and `CHIEF_MECHANIC`; **readers** are editors plus `MECHANIC`. Every editor only endpoint in AC-38's table returns 403 for `MECHANIC`. `RequireRole` in `App.tsx` accepts `role: UserRole | UserRole[]`, and the editor only routes (`/knowledge-base/new`, `/knowledge-base/:id/edit`, `/knowledge-base/suggestions`, `/knowledge-base/categories`) use `['ADMIN', 'CHIEF_MECHANIC']`.

*Data and migration*

- **AC-4**: One welinc-backend-vrms migration creates the data model in *Feature design*: the enums, `pg_trgm` (`CREATE EXTENSION IF NOT EXISTS pg_trgm`), the new tables, the new nullable `RepairIssue` columns, and GIN trigram indexes on `KnowledgeEntry.name` and `KnowledgeEntry.symptoms`. It seeds `IssueCategory` with Brakes, Engine, Electrical, Suspension, Cooling, Transmission (`sortOrder` 1 to 6, the current `VEHICLE_SYSTEM_OPTIONS`) and General (`sortOrder` 99). It backfills `RepairIssue.categoryId` by matching the `[System]` prefix of `description` (the format `create()` writes today) to a category name, ignoring case; an issue with no match keeps `categoryId` null. No existing row is changed otherwise.
- **AC-5**: Names are unique ignoring case and outer spaces: `IssueCategory.nameKey` and `KnowledgeEntry.nameKey` (the trimmed, lowercased name, set by the service on every write) carry `@unique`. A duplicate returns 409 "An entry named '{name}' already exists." (or "A category named …").

*Library page `/knowledge-base`*

- **AC-6**: The page is rebuilt from scratch in `features/knowledge-base/` (pages, components, hooks, lib). `PageHeader` reads "Knowledge base", subtitle "Known fixes from your own repairs.", icon `BookOpen`; editors get a primary "New entry" button (`Plus`) in the `action` slot. Editors see route tabs under the header: Library, Suggestions (with the open count as a badge when above 0), Categories.
- **AC-7**: Under the header, a search band (`card` surface, border, `p-4` phone and `p-5` desktop) holds a search `Input` at `h-11 text-base` with a `Search` icon, placeholder "Describe the problem, like 'squeal when braking'", `maxLength` 100, and a clear button (`aria-label` "Clear search") while it has text. Below it, category chips: a single select `toggle-group` with "All" plus every active category with its count of entries in the current status filter, in `sortOrder`; the chips scroll sideways inside their row on a phone and the page never scrolls sideways. Editors also get a status `Select` (Active by default, Draft, Inactive, All) and a sort `Select` (Most seen, Recently updated, A to Z); mechanics always get Active and Most seen.
- **AC-8**: `q`, `category` (category id), `status`, `sort` and `page` live in the URL, read and written by `features/knowledge-base/lib/libraryFilters.ts` (same pattern as `repairListFilters.ts`). Invalid values read as the default. Search text is local state and only the 300ms debounced value is written to `q`. Each filter change writes with `replace` and resets `page` to 1 inside its `onChange`. A mechanic's URL `status` is ignored.
- **AC-9**: Results come from `GET /vrms/knowledge/entries` (AC-38), 20 per page with the shared `Pagination`. Each result is one row that links to `/knowledge-base/:id` (the whole row is the link, at least 44px tall): the name (`font-semibold`), a category badge, a status badge when not Active (editors only), the symptoms on one line (truncated), and a meta line with `tabular-nums`: "Seen {n}× · last {YYYY-MM-DD}" when seen, plus "· usually {h} h" when the median work time exists (AC-13) or else "· est. {h} h" when only `estimatedHours` is set, plus "· about ₱{cost}" for editors when a typical cost exists. A never seen entry shows "Not seen on a ticket yet". On a phone the rows stack as cards; from 1024px the rows sit in one bordered list.
- **AC-10**: Default order is Most seen: `seenCount` descending, then name A to Z. Recently updated is `updatedAt` descending. A to Z is by name.
- **AC-11**: States: loading shows 6 skeleton rows shaped like results. Error shows `ErrorState` with "Couldn't load the knowledge base." and a Retry button. An empty library (no entries in any status) shows `EmptyState`: editors get "No entries yet. Start from suggestions, or add one." with "Open suggestions" and "New entry"; mechanics get "No known fixes yet." No match shows "No entries match your search." with "Clear filters", plus "Suggest an entry" for mechanics (opens AC-35's dialog with kind New entry). On mount the page removes the old `welinc_kb_articles` `localStorage` key inside a `try`.

*Entry page `/knowledge-base/:id`*

- **AC-12**: Shows a back link "Knowledge base" (keeps the previous library URL), the name as the page title, the category badge, the suggested priority with `PriorityBadge`, and a status badge when not Active. Sections: **Safety** (when `safetyNotes` is set: a warning `Callout` with `TriangleAlert`), **Fix steps** (an ordered list, numbered), **Typical parts** (when any), **Symptoms**, and **Description template** (editors only). From 1024px the history cards (AC-13 to AC-15) sit in a right column; on a phone the order is Safety, Fix steps, Typical parts, Symptoms, then history.
- **AC-13**: A "From your repairs" card shows: "Seen {n} times", "Last seen {YYYY-MM-DD}", typical work time, typical calendar time "Usually closed in {d} days", and, for editors only, typical cost "About ₱{cost}". Typical work time shows the median `hoursSpent` labelled "From {n} repairs" when at least `MIN_SAMPLES` (3) samples exist, else the typed `estimatedHours` labelled "Estimate", else "No estimate yet". Typical calendar time and typical cost show only with at least 3 samples. All sources are in *Value sourcing*.
- **AC-14**: A "Keeps coming back" card lists vehicles with at least `REPEAT_THRESHOLD` (2) linked, not cancelled issues on tickets created in the last `REPEAT_WINDOW_DAYS` (365): plate, count, last date, most repeats first, at most 5. Hidden when none.
- **AC-15**: For editors, a "Recent tickets" card lists the last 5 tickets with an issue linked to this entry: repair number (links to the ticket), plate, `StatusBadge`, created date. Hidden when none.
- **AC-16**: Actions: editors get "Edit" (primary) and a `⋮` menu with "Publish" (Draft), "Deactivate" (Active), "Reactivate" (Inactive) and "Change history". Status changes ask through `confirm()` ("Deactivate this entry? It leaves the repair form picker. Tickets already linked keep it."), call AC-38's status endpoint, and toast the result. "Change history" opens a `ResponsiveDialog` listing `KnowledgeEntryChange` rows newest first (who, when, field, before and after). Mechanics get one "Suggest a change" button (AC-35). A mechanic opening a Draft or Inactive entry gets the not found state ("This entry isn't available.") because the API answers 404. Loading shows a skeleton, an error shows `ErrorState` with Retry.

*Editor `/knowledge-base/new` and `/knowledge-base/:id/edit`*

- **AC-17**: A full page form (React Hook Form with a zod schema in `lib/entryFormSchema.ts`) in `FormSection` blocks: **Basics** (Name, Category `Select` of active categories, Suggested priority `toggle-group` Low, Medium, High, Critical, Estimated hours number input), **What it looks like** (Symptoms textarea, Description template textarea with helper "Fills the issue description when picked in the repair form."), **Fix steps** (a list with numbered rows, each a text input with "Move up", "Move down" and "Remove" icon buttons carrying `aria-label`s, plus "Add step"), **Typical parts** (the same list shape, "Add part"), **Safety** (Safety notes textarea).
- **AC-18**: Field rules, shown inline under each field in `text-xs` `destructive`: name 3 to 100 characters; category required; suggested priority required; estimated hours optional, 0.25 to 200 in steps of 0.25; symptoms 10 to 1000; description template up to 1000; safety notes up to 500; steps 1 to 20, each 3 to 300 (empty rows are dropped before checking); parts 0 to 20, each 2 to 100. The API enforces the same limits and answers 400 with the field messages.
- **AC-19**: A new entry has two buttons: "Save as draft" (secondary) and "Publish" (primary), which create it as `DRAFT` or `ACTIVE`. Editing has one "Save changes" button and keeps the status. Buttons disable while saving and show a spinner. Success toasts ("Entry saved" or "Entry published") and opens the entry page.
- **AC-20**: An edit sends the `lastUpdatedAt` it loaded. A 409 keeps the form as typed and shows a `FormAlert`: "Someone else changed this entry. Reload to see their changes." with a "Reload" button that refetches and resets the form after a `confirm()`. A 409 for a duplicate name shows under Name instead.
- **AC-21**: Leaving a changed form asks through the existing `useLeaveGuard` (spec 0005), and the browser `beforeunload` prompt covers reloads.

*Categories `/knowledge-base/categories`*

- **AC-22**: A `DataTable` of all categories in `sortOrder`: name, description, number of entries (all statuses), status badge (Active or Inactive), and a `⋮` menu with Edit, Move up, Move down, Deactivate or Reactivate. "New category" opens a `ResponsiveDialog` with Name (2 to 50) and Description (up to 200); Edit opens the same dialog filled in. Saves send `lastUpdatedAt` and handle 409 like AC-20.
- **AC-23**: Deactivating a category with any Active or Draft entry is refused with 400 "Move or deactivate its {n} entries first." and the toast shows that message. An inactive category leaves the repair form and library chips, and its existing tickets and entries keep it.

*Repair form (spec 0005), the common issue picker (Jira WL-702)*

- **AC-24**: Each issue row in `IssueLoggingSection` gets a "Common issue" `Combobox` as its first field, fed by `GET /vrms/knowledge/entries/options` (loaded once with the other form options in `useRepairFormOptions`). Options are grouped by category, most seen first inside each group, searchable by name and symptoms, and each option shows its name and "Seen {n}×". The last option is always "Other (describe it yourself)". The "System" select keeps its place, now fed by the active categories from `GET /vrms/knowledge/categories` instead of the hardcoded `VEHICLE_SYSTEM_OPTIONS`, which is deleted.
- **AC-25**: Picking an entry sets the row's System to its category, fills Description with `descriptionTemplate` when Description is empty (when it isn't, a "Use template" text button appears under it), raises the ticket's Priority to the entry's suggested priority when the current one is empty or lower (never lowers it), and shows an info line under the row: "Usually {h} h of work" (from AC-13's typical work time, else the estimate), plus "· about ₱{cost}" (the form is admin only). Nothing about the estimate is saved. Choosing Other clears the link and leaves the other fields as they are. Root cause stays a manual field.
- **AC-26**: `CreateRepairDto` issues replace `vehicleSystem` with `categoryId` (UUID, required, must be an active category, else 400) and gain optional `knowledgeEntryId` (UUID, must be an Active entry, else 400). `create()` still writes `description` as `[{category name}] {rootCause}: {description}`, sets `categoryId` and `knowledgeEntryId`, and copies the entry's steps into `RepairIssueStep` rows for linked issues, all inside the existing create. Create writes no `KNOWLEDGE_LINK` rows (the `CREATED` row covers it, and the issue shows its link); link, relink, unlink and backfill do (AC-29, AC-33). `repairFormSchema.ts`, `RepairSummaryDialog` and the payload builder follow the rename.

*Ticket detail (spec 0004)*

- **AC-27**: `IssuesSection` becomes one block per issue: the description, the category badge, and when linked, a "Known fix" panel with the entry name (links to the entry page), an "Inactive" badge if the entry is no longer active, the Safety callout, the copied steps as a checklist, the typical parts, and "Usually {h} h of work". When not linked and the ticket is Pending or In progress, the panel offers a "Link a known fix" `Combobox` (Active entries, same option shape as AC-24).
- **AC-28**: Step checkboxes (44px rows) are enabled for the assigned mechanic or chief and for admins while the ticket is In progress, and read only otherwise. Each tick calls AC-38's step endpoint right away, updates the row optimistically, and on failure reverts it with an error toast. Ticked steps show who and when on hover and focus. Every linked issue shows "{x} of {y} steps done".
- **AC-29**: "Change" on a linked panel (Pending or In progress only) opens the same `Combobox`, plus "Remove link". Choosing asks through `confirm()` when any step is ticked ("Replace the checklist? {n} ticked steps will be cleared."), then calls AC-38's link endpoint with the ticket's `updatedAt`; a 409 reloads the ticket with the existing `STALE_TICKET_MESSAGE`. The ticket's Activity shows the change ("Linked known fix: Brake pads worn", "Removed known fix").
- **AC-30**: "Send for verification" (the existing `TicketNoteDialog` for the move) adds one block per issue. A linked issue shows "Followed the known fix" (a `Checkbox`, ticked by default) and an optional "What fixed it?" textarea; an unlinked issue shows a required "What fixed it?" textarea (5 to 500 characters, helper "A few words is enough, like 'replaced front pads, rotors fine'."). Every issue gets an optional "Hours spent" number input (0.25 to 200, steps of 0.25). The dialog's submit stays disabled until every required note is valid.
- **AC-31**: `UpdateRepairStatusDto` gains optional `resolutions: { issueId, resolutionNote?, hoursSpent?, followedKnownFix? }[]`. Moving In progress to For verification requires one resolution for every issue on the ticket (400 "Add what fixed each issue." listing the missing ones) and a `resolutionNote` of 5 to 500 characters for every unlinked issue (400). The service saves the fields and `resolvedAt` on each `RepairIssue` in the same transaction as the status change. Other moves ignore `resolutions`. The ticket view shows each issue's note, hours and "Followed the known fix" once saved.

*Suggestions `/knowledge-base/suggestions`*

- **AC-32**: Section "Recurring problems": groups of at least `GROUP_MIN_SIZE` (3) unlinked, not dismissed issues on not cancelled tickets that are similar (see *Grouping*), biggest first, at most 20 groups. Each group is a card: "{n} similar issues", the category when they share one, the 3 newest issue descriptions with their "What fixed it" notes and repair numbers, "Show all" to expand, and actions "Create entry" (primary) and "Dismiss".
- **AC-33**: "Create entry" opens `/knowledge-base/new` with the group passed in router state: symptoms prefilled from the newest description (its `[System] ` prefix removed, cut to 1000), the category preset when shared, and a "Link these issues" list with every group issue ticked. On save, the API links every still ticked issue (AC-38, `linkIssueIds`) in the same transaction as the create: sets `knowledgeEntryId` (and `categoryId` when null), writes a `KNOWLEDGE_LINK` audit row per issue, copies the steps only for issues on `PENDING` or `IN_PROGRESS` tickets (closed tickets get none), and never touches any ticket's `updatedAt`. An issue that is already linked, dismissed or on a cancelled ticket is skipped and reported in the toast ("Linked 11 of 12 issues. 1 was skipped."). If the editor page loads without the group state (a reload), it opens as a plain new entry with an info `Callout`: "The suggestion group was lost. Open it again from Suggestions to link its issues."
- **AC-34**: "Dismiss" asks through `confirm()` and sets `suggestionDismissedAt` on the group's issues, so they never group again. The page refetches.
- **AC-35**: Section "From mechanics": open `KnowledgeSuggestion` rows, newest first: kind (Change or New entry), the entry name for a change (links to it), the body, who and when, and the source ticket when given. Actions: "Open entry" (change) or "Create entry" (new entry, prefills symptoms from the body), "Mark done" and "Dismiss", which set the status to Accepted or Dismissed. Readers create suggestions through a `ResponsiveDialog` ("Suggest a change" on an entry, "Suggest an entry" on the library no match state, and "Suggest an entry" on a ticket's unlinked issue): one textarea, 5 to 1000 characters; success toasts "Thanks, an editor will review it."
- **AC-36**: Empty states: no groups shows "No recurring problems right now."; no mechanic suggestions shows "Nothing from mechanics yet."; errors show `ErrorState` with Retry per section. The Suggestions tab badge counts open mechanic suggestions only, from `GET /vrms/knowledge/suggestions/count`, so the library never runs the grouping query; the Suggestions page shows "{n} recurring problems" from its own response.

*Cleanup and quality*

- **AC-37**: The old `KnowledgeBasePage.tsx` (with its `DEFAULT_ARTICLES`, `localStorage` copy, hand rolled modals and toast) and `getKnowledgeArticles` in `aiApi.ts` are deleted. No component in `features/knowledge-base/` uses a raw color or palette class (`npm run lint` passes). The analytics AI service and its `/ai/knowledge/articles` endpoint are not changed (feature 3 retires them).
- **AC-38**: The API in *Feature design* exists as listed, with `class-validator` DTOs and the roles shown; every write that changes an entry or category writes `KnowledgeEntryChange` rows, one per changed field (Jira WL-704: "changes are audit logged").
- **AC-39**: Lint, typecheck and build pass in welinc-web-vrms; lint (for the touched files, see spec 0006's note on the existing failures), build and tests pass in welinc-backend-vrms and welinc-auth. New Jest tests cover the stats rules (AC-13, AC-14), the resolution rules (AC-31), link and relink (AC-26, AC-29) and grouping (AC-32). The library, entry page, editor, ticket panel and send for verification dialog pass axe and work at 375px and 1280px for an admin, a chief mechanic and a mechanic.

## Decision

**Chosen option**: Option 2: A common issues library owned by welinc-backend-vrms, wired into the repair form and ticket, that fills itself from finished repairs.

Build the knowledge base as relational data in welinc-backend-vrms, used by the repair form and ticket detail, fed by "What fixed it" notes and `pg_trgm` text grouping, with no AI dependency.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`) · `shadcn` (`shadcn-ui/ui`, `.claude/skills/shadcn/`) · `vercel-react-best-practices` (`vercel-labs/agent-skills`, `.claude/skills/vercel-react-best-practices/`) · `react-hook-form` (`.claude/skills/react-hook-form/`) · `tailwind-4-docs` (`lombiq/tailwind-agent-skills`, `.claude/skills/tailwind-4-docs/`)

## Feature design

**Repos touched**: welinc-backend-vrms (new `src/modules/knowledge/` module, `repairs.*`, `config.controller.ts`, schema, migration, seed), welinc-web-vrms (`features/knowledge-base/` rewrite, repair form, ticket detail, users page, roles, routes), welinc-auth (enum, migration, seed only). This spec is the cross repo spec AGENTS.md asks for.

**Data model sketch** (Prisma, welinc-backend-vrms; "who" fields follow `AuditLog`: the JWT email, no foreign key, because user rows live in welinc-auth):

```prisma
enum UserRole { ADMIN MECHANIC CHIEF_MECHANIC CUSTOMER_SUPPORT OPERATIONS }   // also in welinc-auth
enum RepairPriority { LOW MEDIUM HIGH CRITICAL }       // feature 18 reuses it for the ticket
enum KnowledgeEntryStatus { DRAFT ACTIVE INACTIVE }
enum SuggestionKind { CHANGE NEW_ENTRY }
enum SuggestionStatus { OPEN ACCEPTED DISMISSED }

model IssueCategory {
  id          String   @id @default(uuid()) @db.Uuid
  name        String   @db.VarChar(50)
  nameKey     String   @unique @map("name_key") @db.VarChar(50)   // trim + lowercase
  description String?  @db.VarChar(200)
  isActive    Boolean  @default(true) @map("is_active")
  sortOrder   Int      @default(0) @map("sort_order")
  createdAt / updatedAt (timestamptz, as elsewhere)
  entries KnowledgeEntry[]   issues RepairIssue[]   changes KnowledgeEntryChange[]
  @@map("issue_categories")
}

model KnowledgeEntry {
  id                  String               @id @default(uuid()) @db.Uuid
  name                String               @db.VarChar(100)
  nameKey             String               @unique @map("name_key") @db.VarChar(100)
  categoryId          String               @map("category_id") @db.Uuid
  status              KnowledgeEntryStatus @default(DRAFT)
  symptoms            String               @db.Text      // 10..1000
  descriptionTemplate String?              @map("description_template") @db.Text  // ..1000
  suggestedPriority   RepairPriority       @map("suggested_priority")
  estimatedHours      Decimal?             @map("estimated_hours") @db.Decimal(5, 2)
  safetyNotes         String?              @map("safety_notes") @db.Text  // ..500
  createdByEmail      String               @map("created_by_email") @db.VarChar(255)
  updatedByEmail      String               @map("updated_by_email") @db.VarChar(255)
  createdAt / updatedAt
  category IssueCategory @relation(fields: [categoryId], references: [id])   // Restrict
  steps KnowledgeEntryStep[]  parts KnowledgeEntryPart[]  issues RepairIssue[]
  suggestions KnowledgeSuggestion[]  changes KnowledgeEntryChange[]
  @@index([status, categoryId])
  @@index([name(ops: raw("gin_trgm_ops"))], type: Gin)
  @@index([symptoms(ops: raw("gin_trgm_ops"))], type: Gin)
  @@map("knowledge_entries")
}

model KnowledgeEntryStep {   // 1..20 per entry, replaced as a set on edit
  id String @id @default(uuid()) @db.Uuid
  entryId String @map("entry_id") @db.Uuid   position Int   text String @db.VarChar(300)
  entry KnowledgeEntry @relation(fields: [entryId], references: [id], onDelete: Cascade)
  @@unique([entryId, position])  @@map("knowledge_entry_steps")
}

model KnowledgeEntryPart {   // 0..20 per entry, replaced as a set on edit
  id String @id @default(uuid()) @db.Uuid
  entryId String @map("entry_id") @db.Uuid   position Int   name String @db.VarChar(100)
  entry KnowledgeEntry @relation(fields: [entryId], references: [id], onDelete: Cascade)
  @@unique([entryId, position])  @@map("knowledge_entry_parts")
}

model RepairIssue {          // existing; new columns all nullable
  ...existing fields
  categoryId            String?   @map("category_id") @db.Uuid
  knowledgeEntryId      String?   @map("knowledge_entry_id") @db.Uuid
  resolutionNote        String?   @map("resolution_note") @db.Text      // 5..500
  hoursSpent            Decimal?  @map("hours_spent") @db.Decimal(5, 2)
  followedKnownFix      Boolean?  @map("followed_known_fix")
  resolvedAt            DateTime? @map("resolved_at") @db.Timestamptz(6)
  suggestionDismissedAt DateTime? @map("suggestion_dismissed_at") @db.Timestamptz(6)
  category IssueCategory?  @relation(fields: [categoryId], references: [id])
  knowledgeEntry KnowledgeEntry? @relation(fields: [knowledgeEntryId], references: [id])
  steps RepairIssueStep[]  suggestions KnowledgeSuggestion[]
  @@index([knowledgeEntryId])
  @@index([knowledgeEntryId, suggestionDismissedAt])
}

model RepairIssueStep {      // copied from the entry when linked
  id String @id @default(uuid()) @db.Uuid
  repairIssueId String @map("repair_issue_id") @db.Uuid   position Int   text String @db.VarChar(300)
  checkedAt DateTime? @map("checked_at") @db.Timestamptz(6)
  checkedByEmail String? @map("checked_by_email") @db.VarChar(255)
  repairIssue RepairIssue @relation(fields: [repairIssueId], references: [id], onDelete: Cascade)
  @@unique([repairIssueId, position])  @@map("repair_issue_steps")
}

model KnowledgeSuggestion {
  id String @id @default(uuid()) @db.Uuid
  kind SuggestionKind   status SuggestionStatus @default(OPEN)
  entryId String? @map("entry_id") @db.Uuid               // required when kind = CHANGE
  repairIssueId String? @map("repair_issue_id") @db.Uuid  // where it came from, optional
  body String @db.Text                                   // 5..1000
  createdByEmail String @map("created_by_email") @db.VarChar(255)
  resolvedByEmail String? @map("resolved_by_email") @db.VarChar(255)
  resolvedAt DateTime? @map("resolved_at") @db.Timestamptz(6)
  createdAt DateTime @default(now()) @map("created_at") @db.Timestamptz(6)
  entry KnowledgeEntry? @relation(...)   repairIssue RepairIssue? @relation(..., onDelete: SetNull)
  @@index([status, createdAt])  @@map("knowledge_suggestions")
}

model KnowledgeEntryChange {  // the WL-704 audit log, shaped like AuditLog
  id String @id @default(uuid()) @db.Uuid
  entryId String? @map("entry_id") @db.Uuid   categoryId String? @map("category_id") @db.Uuid
  userId String? @map("user_id") @db.Uuid     email String @db.VarChar(255)
  action String @db.VarChar(50)   // ENTRY_CREATED, ENTRY_UPDATED, ENTRY_STATUS, CATEGORY_CREATED, CATEGORY_UPDATED, CATEGORY_STATUS
  fieldName String? @map("field_name") @db.VarChar(50)
  previousValue String? @map("previous_value") @db.Text   newValue String? @map("new_value") @db.Text
  createdAt DateTime @default(now()) @map("created_at") @db.Timestamptz(3)
  @@index([entryId, createdAt])  @@map("knowledge_entry_changes")
}
```

Relationships: category 1:N entries, category 1:N repair issues, entry 1:N steps, parts, suggestions, changes, repair issues; repair issue 1:N issue steps. Categories and entries are never deleted.

**State transitions** (`KnowledgeEntry.status`, editors only, each writes an `ENTRY_STATUS` change row): `DRAFT → ACTIVE` (Publish), `DRAFT → INACTIVE`, `ACTIVE → INACTIVE` (Deactivate), `INACTIVE → ACTIVE` (Reactivate). Any other move is 400. Only `ACTIVE` entries appear in the picker, the ticket link `Combobox` and a mechanic's library. Ticket statuses gate the ticket side: link, relink and unlink in `PENDING` or `IN_PROGRESS`; step ticks in `IN_PROGRESS`; resolutions on the move to `FOR_VERIFICATION`.

**API surface** (controller `@Controller('vrms/knowledge')` in `src/modules/knowledge/knowledge.controller.ts`, plus three repair routes; all behind `JwtAuthGuard` and `RolesGuard`; "Readers" = `ADMIN, CHIEF_MECHANIC, MECHANIC`, "Editors" = `ADMIN, CHIEF_MECHANIC`):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/knowledge/categories` | GET | `includeInactive?` (editors only, else ignored) | `[{ id, name, description, isActive, sortOrder, entryCount, updatedAt }]` in `sortOrder` | Readers | |
| `/vrms/knowledge/categories` | POST | `name` 2..50, `description?` ..200 | category | Editors | 400, 409 dup |
| `/vrms/knowledge/categories/:id` | PATCH | `name?`, `description?`, `isActive?`, `sortOrder?`, `lastUpdatedAt` (req) | category | Editors | 400 (deactivate with entries, AC-23), 404, 409 stale or dup |
| `/vrms/knowledge/entries` | GET | `q?` ..100, `categoryId?`, `status?` (`ACTIVE` default, `DRAFT`, `INACTIVE`, `ALL`; forced `ACTIVE` for mechanics), `sort?` (`seen` default, `updated`, `name`), `page?` | `{ data: [{ id, name, category {id,name}, status, symptoms, seenCount, lastSeenAt, typicalHours, typicalCost* }], total, categoryCounts: {categoryId: n} }`, 20 per page | Readers | 400 |
| `/vrms/knowledge/entries/options` | GET | | all `ACTIVE` entries: `[{ id, name, categoryId, categoryName, symptoms, suggestedPriority, descriptionTemplate, seenCount, typicalHours, typicalCost* }]` by `seenCount` desc | Readers | |
| `/vrms/knowledge/entries/:id` | GET | | entry with `steps`, `parts`, `stats { seenCount, lastSeenAt, typicalHours, hoursSamples, estimatedHours, typicalDays, typicalCost* }`, `repeatVehicles [{plate, count, lastAt}]`, `recentTickets*`, `updatedAt` | Readers | 404 (missing, or not `ACTIVE` for a mechanic) |
| `/vrms/knowledge/entries` | POST | entry fields (AC-18), `status` (`DRAFT` or `ACTIVE`), `linkIssueIds?` UUID[] ..200, `suggestionId?` | entry, `linked`, `skipped` | Editors | 400, 409 dup |
| `/vrms/knowledge/entries/:id` | PATCH | all entry fields incl. full `steps[]`, `parts[]`, `lastUpdatedAt` (req) | entry | Editors | 400, 404, 409 stale or dup |
| `/vrms/knowledge/entries/:id/status` | PATCH | `status`, `lastUpdatedAt` (req) | entry | Editors | 400 bad move, 404, 409 |
| `/vrms/knowledge/entries/:id/changes` | GET | | change rows newest first, max 200 | Editors | 404 |
| `/vrms/knowledge/suggestions` | GET | | `{ groups: [{ issueIds, size, categoryName?, issues: [{ issueId, ticketId, repairNumber, description, resolutionNote, createdAt }] }], suggestions: [...OPEN rows], openCount }` | Editors | |
| `/vrms/knowledge/suggestions/count` | GET | | `{ openCount }` (open `KnowledgeSuggestion` rows) | Editors | |
| `/vrms/knowledge/suggestions` | POST | `kind`, `entryId?` (req for `CHANGE`, must exist), `repairIssueId?`, `body` 5..1000 | suggestion | Readers | 400, 404 |
| `/vrms/knowledge/suggestions/:id` | PATCH | `status` (`ACCEPTED` or `DISMISSED`) | suggestion | Editors | 400 (not `OPEN`), 404 |
| `/vrms/knowledge/suggestions/dismiss-group` | POST | `issueIds` UUID[] 1..200 | `{ dismissed: n }` | Editors | 400 |
| `/vrms/repairs` | POST | issues gain `categoryId` (req), `knowledgeEntryId?`; `vehicleSystem` removed | ticket | ADMIN (unchanged) | 400 inactive category or entry |
| `/vrms/repairs/:id/issues/:issueId/knowledge` | PATCH | `knowledgeEntryId` UUID or `null`, `lastUpdatedAt` (req) | ticket | ADMIN, assigned MECHANIC or CHIEF_MECHANIC | 400 (status, inactive entry), 403, 404, 409 stale |
| `/vrms/repairs/:id/issues/:issueId/steps/:stepId` | PATCH | `checked` boolean | the step | ADMIN, assigned MECHANIC or CHIEF_MECHANIC | 400 (not `IN_PROGRESS`), 403, 404 |
| `/vrms/repairs/:id/status` | PATCH | existing body + `resolutions?` (AC-31) | ticket | unchanged + CHIEF_MECHANIC | 400 missing or short notes |

`*` = omitted from the response for `MECHANIC` (cost) and for non editors (`recentTickets`). `formatTicket` issues gain `categoryId`, `categoryName`, `knowledgeEntry { id, name, status, safetyNotes, parts, typicalHours }` or null, `steps [{ id, position, text, checkedAt, checkedByEmail }]`, `resolutionNote`, `hoursSpent`, `followedKnownFix`. A step tick does not touch the ticket's `updatedAt` (so ticking never causes a 409 on other edits); link and relink do.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Any stat | "linked issue" | `RepairIssue.knowledgeEntryId = entry.id` and the ticket's `repairStatus` is not `CANCELLED` |
| Library, entry, options | `seenCount` | count of linked issues |
| Library, entry | `lastSeenAt` | max `RepairTicket.createdAt` over linked issues |
| Entry, options, picker info line | `typicalHours` | median `RepairIssue.hoursSpent` over linked issues on `COMPLETED` tickets with `hoursSpent` not null; null under `MIN_SAMPLES`; the client falls back to `estimatedHours` |
| Entry | `typicalDays` | median of (`completedAt` − `createdAt`) in days, one decimal, over `COMPLETED` tickets with a linked issue; null under `MIN_SAMPLES` |
| Entry, options (editors) | `typicalCost` | median `RepairTicket.totalCost` over `COMPLETED` tickets whose only issue is linked to this entry and `totalCost` is not null; null under `MIN_SAMPLES` |
| Entry | `repeatVehicles` | linked issues grouped by `RepairTicket.vehicleId` where `createdAt` ≥ now − `REPEAT_WINDOW_DAYS`, count ≥ `REPEAT_THRESHOLD`; plate from `Vehicle.plateNumber` |
| Stats queries | medians | one `$queryRaw` per call in `knowledge-stats.ts` using `percentile_cont(0.5)`, grouped by entry for list calls |
| Library | `categoryCounts` | count of entries per category under the current status filter (not `q`) |
| Library search | match | `name ILIKE %q%` or `symptoms ILIKE %q%` or any part `ILIKE %q%` or `word_similarity(q, name || ' ' || symptoms) >= SEARCH_SIMILARITY` (0.3); search results still use the chosen sort |
| Suggestions | groups | see *Grouping* |
| Create ticket, link | copied steps | the entry's `KnowledgeEntryStep` rows at link time, same `position` and `text` |
| Repair form | priority raise order | `LOW < MEDIUM < HIGH < CRITICAL` (`RepairPriority`) |
| Any write | who | the JWT `email` (and `sub` as `userId` on change rows) |
| Constants | `MIN_SAMPLES` 3, `REPEAT_THRESHOLD` 2, `REPEAT_WINDOW_DAYS` 365, `GROUP_MIN_SIZE` 3, `GROUP_SIMILARITY` 0.4, `SEARCH_SIMILARITY` 0.3, `GROUP_CANDIDATE_LIMIT` 500 | replaced by spec 0012 (AC-3): `MIN_SAMPLES`, `REPEAT_THRESHOLD`, `REPEAT_WINDOW_DAYS` and `GROUP_MIN_SIZE` are now settings an Admin changes in the Settings hub (`knowledge.min_samples`, `knowledge.repeat_threshold`, `knowledge.repeat_window_days`, `knowledge.group_min_size`), read through `SettingsService`; `GROUP_SIMILARITY`, `SEARCH_SIMILARITY` and `GROUP_CANDIDATE_LIMIT` stay in code as `KNOWLEDGE_TUNING` in `knowledge.tuning.ts`. `knowledge.settings.ts` is gone |

**Grouping** (`knowledge-grouping.ts`): candidates are up to `GROUP_CANDIDATE_LIMIT` newest issues with `knowledgeEntryId` null, `suggestionDismissedAt` null, ticket not cancelled. Each candidate's text is its description without the `[System] ` prefix plus its `resolutionNote`. One `$queryRaw` self join returns pairs with `a.id < b.id`, the same `categoryId` (or both null; pairing only inside a category keeps it to a few thousand comparisons) and `similarity(a.text, b.text) >= GROUP_SIMILARITY`. The trigram indexes don't serve this computed text or the combined search expression; at this table size a plain scan is fine. The service joins the pairs into groups (connected components), keeps groups of at least `GROUP_MIN_SIZE`, and sorts them by size then newest issue. It runs on each GET (no stored groups). The AI rework can swap the pair query for embeddings behind the same function.

**Key invariants**:
- An issue's checklist is a copy: editing an entry never changes `RepairIssueStep` rows on existing tickets.
- Relinking or unlinking deletes the issue's steps and (for a relink) copies the new entry's steps, in one transaction with a `KNOWLEDGE_LINK` audit row (`fieldName` is the issue id, `previousValue` and `newValue` are the entry names, or empty) and the ticket `updatedAt` touch.
- Only `ACTIVE` entries can be newly linked; an issue stays linked when its entry becomes `INACTIVE`.
- A category with any `ACTIVE` or `DRAFT` entry cannot be deactivated, and an entry can only be created in, or moved to, an active category (else 400).
- `nameKey` is always `trim(lower(name))`; entry steps and parts are saved as a full replace with positions 1..n.
- Every entry or category write and its `KnowledgeEntryChange` rows commit in one transaction.
- `KNOWLEDGE_LINK` is added to `audit-events.ts` so the ticket Activity (spec 0004) and the audit timeline (spec 0003) render it.

**Security model**: Readers read active entries, categories and their stats, tick steps and link fixes only on tickets they are assigned to (the existing assignment check), and create suggestions. Editors also read drafts, inactive entries, suggestions and change history, and write entries and categories. Costs (typical cost) are never sent to `MECHANIC`, matching `formatTicket`. A chief mechanic is an editor for the knowledge base and a mechanic for tickets (AC-2). No personal data beyond the actor's email is stored. Inputs are length capped by DTOs; raw SQL takes `q` and ids only as bound parameters through `Prisma.sql`.

**Configuration required**: none (no new environment variables; `pg_trgm` ships with `postgres:16-alpine`).

**Critical test scenarios**:
- Happy path: admin picks "Brake pads worn" in the repair form, the ticket is created with the link and copied steps, the mechanic ticks 3 of 5 steps, sends for verification with hours 2, and the entry page shows the new count, verifies **AC-24** to **AC-28**, **AC-30**, **AC-31**, **AC-13**.
- Self filling: three tickets with unlinked "squeal when braking" issues complete with notes; Suggestions shows one group; Create entry links all three and the new entry shows "Seen 3 times", verifies **AC-32**, **AC-33**, **AC-13**.
- Stats edges: with 2 hour samples the entry shows the typed estimate labelled "Estimate"; a two issue ticket never feeds typical cost; a cancelled ticket never counts, verifies **AC-13**.
- Failure: sending for verification with an unlinked issue and no note returns 400 and the dialog blocks it; two editors save the same entry and the second gets 409 with the reload prompt, verifies **AC-20**, **AC-31**.
- Relink: relinking an issue with 2 ticked steps asks first, replaces the checklist, and logs `KNOWLEDGE_LINK`; a stale `lastUpdatedAt` returns 409, verifies **AC-29**.
- Auth: a mechanic calling `POST /vrms/knowledge/entries` gets 403, opening a draft gets 404, and the entry response has no `typicalCost`; a chief mechanic can edit entries but gets 403 on an unassigned ticket, verifies **AC-2**, **AC-3**, **AC-16**.

## Build plan

The project default is Tracer Bullet; this UI refresh feature breaks Facade on purpose (like specs 0003, 0004 and 0006) because there is no real data to restyle. Each slice runs end to end (schema, API, UI) before the next.

1. **Role and schema.** Add `CHIEF_MECHANIC` to welinc-auth (enum, migration, seed user) and welinc-backend-vrms (enum, seed mechanic); write the one welinc-backend-vrms migration for the whole data model with the category seed and backfill (generate it with `prisma migrate dev --create-only`, then put `CREATE EXTENSION IF NOT EXISTS pg_trgm;` first, before the GIN indexes, and append the seed and backfill SQL); widen `@Roles`, `isMechanic`, `RequireRole`, `isMechanicRole`, nav, dashboard and the Users page options. Satisfies **AC-1** to **AC-5**.
2. **Read thread.** `KnowledgeModule` with categories GET, entries GET (list with search, filters, sort, counts), entry GET with stats, repeat vehicles and recent tickets (`knowledge-stats.ts`, `knowledge.settings.ts`); new `knowledgeApi.ts`; library page and entry page with every state; delete the old page and `getKnowledgeArticles`. Satisfies **AC-6** to **AC-15**, **AC-37**.
3. **Editing.** Entry POST, PATCH, status PATCH and changes GET with change log rows and 409 handling; categories POST and PATCH; editor page, entry actions and change history dialog, categories page. Satisfies **AC-16** to **AC-23**, **AC-38**.
4. **Repair form picker.** `entries/options`, categories in `useRepairFormOptions`, the `Combobox` row field, template and priority fill, the info line; `CreateRepairDto` and `create()` changes with copied steps and audit rows. Satisfies **AC-24** to **AC-26**.
5. **Ticket detail.** `formatTicket` issue fields, link and step endpoints, `KNOWLEDGE_LINK` in `audit-events.ts`, the Known fix panel, checklist, change and remove link; `resolutions` on the status move and the send for verification dialog blocks. Satisfies **AC-27** to **AC-31**.
6. **Suggestions.** `knowledge-grouping.ts`, suggestions GET, POST, PATCH and dismiss group; `linkIssueIds` and `suggestionId` on entry POST; the Suggestions page, the create from group flow and the suggest dialogs. Satisfies **AC-32** to **AC-36**.
7. **Sweep.** Jest tests for stats, resolutions, link and grouping; lint, typecheck and build in all three repos; axe plus 375px and 1280px checks for the three roles. Satisfies **AC-39**.

## Migration plan

**Strategy**: no feature flag; the old page holds no real data, so it is replaced directly.
**Phases**:
1. welinc-auth migration (`ALTER TYPE "UserRole" ADD VALUE 'CHIEF_MECHANIC'`), then the welinc-backend-vrms migration (enums, extension, tables, nullable columns, seed, `categoryId` backfill), both additive.
2. Deploy welinc-backend-vrms, then welinc-web-vrms. The repair form and the create DTO change together, so deploy the backend first and the web app right after; an old web app sending `vehicleSystem` gets 400 until it reloads.
**Rollback**: revert the code; the new tables and nullable columns are unused by the old code and can stay. Removing an enum value from Postgres is not possible, so `CHIEF_MECHANIC` stays once added (no user should hold it after a rollback).
**Risks**: the `[System]` backfill skips issues whose prefix doesn't match a category (they stay null and still group by text); other groups' services reading welinc-auth `user_roles` with an old schema would fail on a `CHIEF_MECHANIC` row, which only matters at integration (accepted, see rationale).

## Consequences

**Positive**:
- The knowledge base is real shared data with an audit trail, used every time a ticket is created or worked on.
- The library grows from repairs: unlinked issues become suggestion groups and one click turns a group into an entry with its history.
- Feature 41's picker, feature 17's role and feature 40's issue type list get a working start, and the AI rework gets clean ground truth (entries, links, notes, hours).

**Negative / tradeoffs**:
- A large spec for a 5 week deadline: three repos and seven slices. Slices 1 to 4 are the minimum that makes the library useful; 5 and 6 are what keep it alive.
- Mechanics get a new required note at For verification for unlinked issues, which is friction.
- Stats need volume: under 3 samples the page shows estimates, so early numbers are thin.
- `pg_trgm` similarity groups by shared word fragments, so differently worded reports of one problem won't group until the AI rework.
- Adding `CHIEF_MECHANIC` to the shared enum ahead of the agreed data model v2 (feature 4) means the other groups must add it before integration.

**Neutral**:
- The analytics AI service keeps running untouched; its `/ai/knowledge/articles` simply has no caller.
- `RepairPriority` exists as an enum before tickets store priority (feature 18).
- The ticket's `[System] rootCause: text` description format stays, so history, exports and the old AI embed keep working.

## Follow-up

- [ ] Feature 17 widens the chief mechanic from mechanic rules to all tickets and the verification queue, and feature 5 (permission matrix) should take over the Readers and Editors lists here.
- [ ] Feature 40 (lookup lists) should reuse `IssueCategory` as the issue type list instead of creating a new one.
- [ ] Feature 3 (AI and analytics into welinc-backend-vrms): embeddings over entries and issues, grounded triage, search by meaning, cleaning "What fixed it" notes, AI drafted entries replacing `pg_trgm` grouping, duplicate ticket warnings; it also removes `autoEmbedIssues` and the Python `/ai/knowledge/articles`.
- [x] The future configurable settings spec replaces `KNOWLEDGE_SETTINGS` with stored settings (done by spec 0012, AC-3; merged in backend-vrms #22).
- [ ] Existing gap, not caused by this spec: no flow creates a VRMS `Mechanic` row when a mechanic or chief mechanic account is added on the Users page (only seeds do), so new accounts can't be assigned tickets. Belongs to feature 2 (auth service boundary).
- [ ] Tell the other groups that `CHIEF_MECHANIC` now exists in the shared `UserRole`, before integration.
- [ ] `docs/context/roles-and-users.md` and the web and backend `AGENTS.md` role lines go stale once this ships (`/sync`).
- [ ] The `react-hook-form` skill is installed but not listed in root `AGENTS.md` `## Agent skills`; it is frontend wide, so it belongs in `welinc-web-vrms/AGENTS.md`.
