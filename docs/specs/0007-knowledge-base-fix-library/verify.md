# Verify: knowledge base refresh · spec 0007 · updated 2026-10-25
_Steps derived from spec 0007 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

Seed logins: `vrms.admin@welinc.com` / `admin1234`, `vrms.chief@welinc.com` / `mechanic1234`, `mech.juan@welinc.com` / `mechanic1234`. Restart `welinc_vrms_backend` and `welinc_vrms_frontend` first (they miss Windows edits).

## UI / manual

*Roles*
- [x] Sign in as the chief mechanic → the header badge reads "Chief mechanic", the nav is the mechanic nav, the dashboard is the mechanic dashboard → AC-1, AC-2
- [x] Users page as admin → New user offers Admin, Chief mechanic, Mechanic; the role filter lists Chief mechanic → AC-1
- [x] Deactivate a chief mechanic with an open assigned ticket → blocked like a mechanic → AC-1
- [x] As the chief, open an unassigned ticket → "This ticket isn't assigned to you"; an assigned one shows no costs and no Complete or Cancel → AC-2
- [x] As a mechanic, open `/knowledge-base/new`, `/knowledge-base/suggestions`, `/knowledge-base/categories` → each sends you to the dashboard → AC-3

*Library and entry*
- [x] `/knowledge-base` as admin → header "Knowledge base", subtitle "Known fixes from your own repairs.", New entry, tabs Library, Suggestions (badge when open mechanic suggestions), Categories → AC-6
- [x] Search band: 44px search with clear button, category chips with counts that scroll inside their row at 375px, Status and Sort selects for editors only → AC-7
- [x] Type "squeel braking" (typo) → after about 300ms `q` lands in the URL and "Brake pads worn" still matches; change a chip → page resets to 1, history entry replaced; `?status=DRAFT` as a mechanic is ignored → AC-8
- [x] A result row is one link of at least 44px with name, category badge, symptoms on one line, and "Seen 12× · last YYYY-MM-DD · usually 2 h · about ₱3,450" (cost for editors only); a never seen entry reads "Not seen on a ticket yet" → AC-9
- [x] Sort Most seen, Recently updated, A to Z order the rows as named → AC-10
- [x] Throttle the network → 6 skeleton rows; block the API → "Couldn't load the knowledge base." with Retry; no match → "No entries match your search." with Clear filters (and Suggest an entry for a mechanic); `welinc_kb_articles` is gone from localStorage → AC-11
- [x] Entry page: back link returns to the same library search; name, category, suggested priority badge; Safety callout first, numbered Fix steps, Typical parts, Symptoms, Description template (editors); history cards on the right from 1024px, after the content on a phone → AC-12
- [x] "From your repairs": with 2 hour samples the work time shows the typed estimate labelled "Estimate"; with 3 it shows the median "From 3 repairs"; typical cost only for editors → AC-13
- [x] "Keeps coming back" lists plates with 2+ linked issues in the last 365 days, most first, at most 5; hidden when none → AC-14
- [x] "Recent tickets" (editors) lists up to 5 linked tickets with repair number link, plate, status, date → AC-15
- [x] Editor ⋮ menu: Publish (draft), Deactivate (active, confirm text "It leaves the repair form picker…"), Reactivate (inactive), Change history dialog newest first; a mechanic gets "Suggest a change"; a mechanic opening a draft gets "This entry isn't available." → AC-16

*Editor and categories*
- [x] `/knowledge-base/new`: sections Basics, What it looks like, Fix steps (Move up, Move down, Remove with aria-labels, Add step), Typical parts, Safety → AC-17
- [x] Save empty → inline errors: name 3 to 100, category, suggested priority, symptoms 10 to 1000, at least one step; hours 0.3 → "steps of 0.25"; empty step rows are dropped → AC-18
- [x] New entry: "Save as draft" and "Publish"; edit: "Save changes"; spinner while saving; toast and the entry page after → AC-19
- [x] Open the editor in two tabs, save in one, then the other → "Someone else changed this entry…" with Reload (asks first); a duplicate name shows under Name → AC-20
- [x] Change a field, click a nav link → discard prompt; reload the tab → browser prompt → AC-21
- [x] Categories tab: table in order with entries, status, ⋮ Edit, Move up, Move down, Deactivate; New category dialog 2 to 50 and up to 200 → AC-22
- [x] Deactivate Brakes while it has an active entry → toast "Move or deactivate its 1 entry first." → AC-23

*Repair form and ticket*
- [x] `/repairs/new` as admin → each issue starts with "Common issue": grouped by category, "Seen n×", search by symptom, "Other (describe it yourself)" last; System lists the active categories → AC-24
- [x] Pick "Brake pads worn" with priority Medium → System Brakes, Description gets the template, priority goes to High, "Usually 2 h of work" shows; with priority Critical it stays Critical; pick Other → link cleared, fields kept → AC-25
- [x] Create the ticket → the linked issue has the entry's steps as a checklist; the Other issue has none; an inactive entry id returns 400 before anything is saved → AC-26
- [x] Ticket detail: each issue shows its category; linked issues show the Known fix panel (entry link, Inactive badge if deactivated, Safety, steps, parts, "Usually n h of work"); unlinked issues on Pending or In progress offer "Link a known fix" → AC-27
- [x] As the assigned chief on an In progress ticket, tick a step → it shows at once and survives a reload; hover shows who and when; "x of y steps done" updates; on Pending the boxes are disabled → AC-28
- [x] Change the known fix with a ticked step → "Replace the checklist? 1 ticked step will be cleared."; Remove link works; Activity shows "Linked known fix: …" and "Removed known fix"; a stale tab gets the reload toast → AC-29
- [x] Send for verification → one block per issue: linked ones have "Followed the known fix" ticked and an optional note; unlinked ones need 5 to 500 characters; submit stays disabled until then; hours accept steps of 0.25 → AC-30
- [x] After sending, each issue shows "What fixed it", hours and "Followed the known fix" → AC-31

*Suggestions*
- [x] Suggestions tab: groups of 3+ similar unlinked issues, biggest first, "n similar issues", category when shared, 3 newest with "What fixed it" and repair numbers, Show all, Create entry, Dismiss → AC-32
- [x] Create entry from a group → editor prefilled (symptoms without "[System] ", category), "Link these issues" all ticked; untick one and publish → toast "Linked n of m issues…"; the entry shows "Seen n times"; reload the editor before saving → "The suggestion group was lost…" and no links → AC-33
- [x] Dismiss a group → confirm, the group disappears and never returns → AC-34
- [x] As a mechanic, "Suggest a change" on an entry, "Suggest an entry" on the library no match state and on a ticket's unlinked issue → toast "Thanks, an editor will review it."; as an editor they appear under "From mechanics" with Open or Create entry, Mark done, Dismiss → AC-35
- [x] Empty states "No recurring problems right now." and "Nothing from mechanics yet."; the tab badge counts open mechanic suggestions only → AC-36

*Cleanup and quality*
- [x] `KnowledgeBasePage.tsx` and `getKnowledgeArticles` no longer exist; the AI service's `/ai/knowledge/articles` is untouched → AC-37
- [x] Every entry and category write adds change rows, one per changed field (Change history dialog, or `knowledge_entry_changes`) → AC-38
- [x] axe finds no WCAG 2.1 AA violations on the library, entry, editor, ticket and send dialog at 375px and 1280px for admin, chief mechanic and mechanic → AC-39

## Value sourcing (vary the input; the edge that breaks if the source is wrong)
- [x] "linked issue": cancel a ticket with a linked issue → the entry's Seen count drops by one → linked issue
- [x] `seenCount`: link two issues on one ticket to the same entry → Seen counts 2 (issues, not tickets) → seenCount
- [x] `lastSeenAt`: link an issue on an older ticket → "last" does not move back; a newer ticket moves it forward → lastSeenAt
- [x] `typicalHours`: hours on a For verification ticket do not count until it is Completed; under 3 completed samples the estimate shows → typicalHours
- [x] `typicalDays`: two linked issues on one completed ticket count that ticket once → typicalDays
- [x] `typicalCost`: a completed ticket with two issues never feeds it; a ticket with no total cost is skipped; a mechanic's response has no `typicalCost` → typicalCost
- [x] `repeatVehicles`: two linked issues on one vehicle 400 days apart do not show; 100 days apart they do → repeatVehicles
- [x] `categoryCounts`: a search does not change the chip counts; the status filter does → categoryCounts
- [x] Library search: a part name ("pad set") finds the entry; a misspelling still finds it by similarity; `%` typed in search matches only a literal % → search match
- [x] Groups: a dismissed or linked issue never appears; issues in different categories never group; a reworded report with no shared words stays out → groups
- [x] Copied steps: edit the entry's steps after linking → the ticket's checklist stays as it was → copied steps
- [x] Priority raise: Low < Medium < High < Critical; a High entry never lowers Critical → priority raise order
- [x] Who: change rows and ticked steps carry the signed in email → who
- [x] Constants: `KNOWLEDGE_SETTINGS` in `welinc-backend-vrms/src/modules/knowledge/knowledge.settings.ts` is the only place 3, 2, 365, 0.4, 0.3 and 500 live → constants

## Commands
- [x] `cd welinc-backend-vrms && npx jest` → 123 tests pass, including `knowledge-stats.spec.ts`, `knowledge-grouping.spec.ts`, `ticket-knowledge.spec.ts`, `repairs.knowledge.spec.ts` → AC-13, AC-14, AC-26, AC-29, AC-31, AC-32
- [x] `cd welinc-backend-vrms && npm run build` → succeeds → AC-39
- [x] `cd welinc-web-vrms && npm run lint && npm run typecheck && npm run build` → all pass → AC-37, AC-39
- [x] `docker exec welinc_auth_service npm run build && docker exec welinc_auth_service npx jest` → pass (local Node is 22; auth requires 24) → AC-39
- [x] `docker exec welinc_vrms_db psql -U welinc_vrms_user -d welinc_vrms_db -c "select name, sort_order from issue_categories order by sort_order"` → the 7 seeded categories (plus any added) → AC-4

## Acceptance-criteria coverage
- AC-1 to AC-3 roles steps · AC-4 category query · AC-5 duplicate name step (AC-20) · AC-6 to AC-16 library and entry · AC-17 to AC-23 editor and categories · AC-24 to AC-31 repair form and ticket · AC-32 to AC-36 suggestions · AC-37 to AC-39 cleanup, commands and axe
