# 0007. Rationale: knowledge base as a fix library

Decision record for [index.md](index.md). `/develop` does not need this file.

## Context

> ⚠️ Premise note: the request was a visual redesign, but the page's real problem is its data, not its look. Restyling it would ship a nicer screen over made up content that nobody can share. This spec treats it as a product redesign (what the knowledge base is and where it is used), with the visuals following from that. It also spans what scope tracks as two features (15, the page, and 41, the picker) plus the role part of feature 17, because the library only gets used if the picker and the ticket use it.

**How the current page works** (`welinc-web-vrms/src/features/knowledge-base/pages/KnowledgeBasePage.tsx`, 1441 lines):
- Articles live in the browser's `localStorage` (`welinc_kb_articles`), seeded from 8 hardcoded SOPs in the file. Create, edit and delete never reach a server, so each browser has its own copy and a mechanic never sees an admin's edit.
- "Sync Catalog" pulls `/ai/knowledge/articles` from the Python service, which returns 14 SOPs typed into `ai_service.py`; when that fails it resets to the 8 local ones.
- The stats ("Avg Labor SLA", "Subsystems", "Steps & Supplies") are counts over that fake list. Hand rolled modals and toast, raw palette colors (`cyan-50`, `teal-600`), `bg-white`, no link to tickets.

**What Jira asks for**: WL-704 (VRMS-216) defines the knowledge base as a list of *common issues* (name, category, description template, suggested priority, suggested fix steps) managed by Admin and Chief Mechanic, seeded from past tickets, with changes audit logged. WL-702 (VRMS-222) is the repair form picker that uses it: searchable, grouped by category, most used first, filling issue type, description, priority and estimate, with an Other option and usage counts. Jira says it "works without any AI". WL-104 confirms the Chief Mechanic role; its exact permissions wait on the stakeholder flowchart.

**Forces**:
- About 5 weeks to deployment (end of November 2026), with most of the Jira backlog still planned.
- The AI service will be rebuilt from scratch inside welinc-backend-vrms (feature 3), so nothing here may depend on today's Python AI.
- The engineer wants the knowledge base to be *actually used* and to work with the AI that comes later.
- Today's data: tickets store issues as free text `[System] rootCause: text`, costs per ticket, and no work hours (`durationHours` is never written). Mechanics never see costs. The repair form already has a hardcoded "System" picker that matches the categories.
- The engineer wants things configurable later (settings and modules), so categories and thresholds should not be baked into code.
- welinc-auth owns users and roles in its own database; welinc-backend-vrms keeps a copy and matches mechanics to logins by email.

## Options considered

### Option 1: Restyle the existing page

Rebuild the screen on the design system and keep the SOP content, either read only from the Python service or still in `localStorage`.

**Pros**: smallest change; fits the Facade approach of the UI refresh.
**Cons**: the content stays fake or browser only; nothing in daily work sends anyone to the page; the AI rework would replace its only data source.

### Option 2: Common issues library in welinc-backend-vrms, wired into tickets (chosen)

Real tables for categories, entries, steps and parts; the repair form picks entries; tickets copy the steps as a checklist; finished repairs record what fixed them; `pg_trgm` groups recurring unlinked issues into suggestions; stats come from tickets.

**Pros**: matches Jira WL-704 and WL-702; used on every ticket; grows from real work; shared and audited; no AI dependency, yet gives the AI clean ground truth.
**Cons**: three repos and seven build slices; a new required note for mechanics; stats are thin until enough tickets exist; needs a migration that breaks Facade.

### Option 3: Server backed SOP library

Keep today's idea (long step by step procedures with parts and hours) but store it in a table.

**Pros**: richer procedures; simple CRUD.
**Cons**: no Jira ticket asks for it; someone has to write every SOP; sits beside a separate common issues list from feature 41, so two libraries drift apart.

### Option 4: Knowledge base inside the AI service

Store entries in the analytics AI service, next to its pgvector store.

**Pros**: keeps AI data together.
**Cons**: that service does not check JWTs and is about to be rebuilt elsewhere; the data would move twice.

## Rationale

The page fails because nothing makes anyone open it and nothing fills it, not because of its look, so a restyle (Option 1) fixes the wrong thing. Option 2 answers both: the picker and the ticket checklist bring people to the content on every repair, and the "What fixed it" note plus suggestion groups make the library grow from work that is happening anyway. It is also the shape Jira already asks for, so it closes WL-704 and WL-702 instead of adding a third concept. Owning the data in welinc-backend-vrms means the AI rework reads the same tables with no contract beyond the schema, which is exactly what the engineer's plan to rebuild the AI needs.

Smaller calls and why:
- **Steps copied onto each issue** (the engineer's pick over live references): ticks and history stay true when an entry is edited mid repair.
- **Typical cost from single issue tickets only**: cost is per ticket, so splitting a two issue ticket would blend a cheap fix with an expensive one.
- **Hours asked in the fix note**: `durationHours` is never written and calendar time includes waiting for parts; a quick optional number is the only honest source of work hours, and the AI can use it later.
- **Medians and a minimum of 3 samples**: one odd repair should not set the estimate; below 3 the page says "Estimate" honestly.
- **`pg_trgm` for grouping and search**: it ships with the Postgres image already running, runs inside the database, and sits behind one function the AI rework can swap for embeddings.
- **Change log table instead of widening `AuditLog`**: `AuditLog.repairTicketId` is required and the spec 0003 timeline is built on it; a sibling table shaped the same way keeps that page untouched.
- **"Who" as email, no foreign key**: user rows live in welinc-auth; `AuditLog` already uses this pattern.
- **Categories reuse the form's System list**: it already exists, it matches every past issue's `[System]` prefix (so history backfills on day one), and feature 40 can adopt it as the issue type list.
- **Constants in one `KNOWLEDGE_SETTINGS` object**: the settings spec can replace one file rather than hunting thresholds.
- **`CHIEF_MECHANIC` added here, with mechanic ticket rules**: the engineer confirmed the role is agreed across groups and that the other groups are not on this schema yet, so the enum risk only appears at integration. Giving the chief mechanic rules on tickets avoids inventing permissions that WL-104 still has open.
- **Full page editor, search first list, most seen first**: steps need room; the most common problems should be the fastest to reach; Jira asks for most used first.

### Evidence: the current page's inventory

| Piece | Today | After this spec |
|---|---|---|
| Storage | `localStorage` `welinc_kb_articles`, 8 seeded SOPs | `knowledge_entries` and related tables |
| Server data | `/ai/knowledge/articles`, 14 SOPs hardcoded in `ai_service.py` | not called (retired in feature 3) |
| Categories | `CATEGORIES` array in the page, `VEHICLE_SYSTEM_OPTIONS` in `repairOptions.ts` | `issue_categories`, one list for both |
| Stats tiles | averages over the fake list | per entry history from tickets |
| Modals and toast | hand rolled `ModalOverlay`, `Toast` | `ResponsiveDialog`, `confirm()`, sonner |
| Link to tickets | none | picker, Known fix checklist, fix notes, suggestions |
