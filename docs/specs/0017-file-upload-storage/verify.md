# Verify: file upload & storage · spec 0017 · updated 2026-11-01
_Steps derived from spec 0017 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Milestone 3: permissions, remove and audit

### UI / manual
- [ ] As Admin, open Settings → Roles and permissions → the Tickets group shows "Add receipts and other documents" (Admin, Chief on; Mechanic off) and "Remove anyone’s files" (Admin, Chief on; Mechanic off and locked, can't be toggled) → AC-15
- [ ] As the seed Mechanic, upload a photo on an assigned ticket → `GET /vrms/repairs/:id/attachments` shows it with `canRemove: true`; as Chief on the same ticket it is also `canRemove: true` (remove any) → AC-17
- [ ] As Chief, upload a photo; as the Mechanic the same row shows `canRemove: false`, and `DELETE` on it answers 403 `NOT_YOUR_FILE` → AC-17
- [ ] As the Mechanic, `DELETE` your own photo → 204; the photo leaves the list; the same `DELETE` again → 204 and no second audit row → AC-17, AC-18
- [ ] As Admin, open the ticket's Activity → "… added a file to REP-…" with "Vehicle photo: <name>.jpg" under it, and "… removed a file from …" after the delete → AC-18
- [ ] Close the ticket, then `DELETE` a photo as Chief → 409 `TICKET_FINISHED`, and every item shows `canRemove: false` → AC-10, AC-17

### API / permissions
- [ ] As the Mechanic, `POST` with `kind=RECEIPT` → 403 `FORBIDDEN_KIND` (no `ticket.documents.add`, no `ticket.costs.view`) → AC-15
- [ ] Grant a Chief `ticket.documents.add` but take away `ticket.costs.view` → `RECEIPT` upload is still 403 `FORBIDDEN_KIND` → AC-15
- [ ] Grant a Mechanic `ticket.view_all` → they can add photos on an unassigned ticket (addFiles follows visibility); without it the upload is 404 → AC-15, AC-16
- [ ] (Once documents land in milestone 5) a receipt on a ticket: the Mechanic's list leaves it out, their `DELETE` on its id is 404, and its add and remove events are missing from the ticket Activity and from `GET /vrms/repairs/audit-logs` for any caller without `ticket.costs.view` → AC-16
- [ ] Audit filter on real Postgres: a caller without `ticket.costs.view` sees `ATTACHMENT_*` rows whose `kind` is `VEHICLE_PHOTO` or `PROOF`, never `RECEIPT` or `OTHER_DOCUMENT`, and no other event type is hidden (checked once on 2026-11-01 in a rolled back transaction: 3 of 3 document rows hidden correctly, 2,291 of 2,291 other rows kept) → AC-16

### Value sourcing
- [ ] `uploadedByName`, `deletedByName`: change the account's display name in welinc-auth, upload and delete → the row and the audit actor carry the new name, cut to 100 → Value sourcing (Upload, Delete)
- [ ] `canRemove` varies with each input: own file vs someone else's, holding vs losing the add key for its kind (revoke `ticket.files.add` from Mechanic → own photo `canRemove: false`), holding `remove_any`, open vs finished ticket → Value sourcing (List, canRemove)
- [ ] `can.addFiles`, `can.addDocuments`: false on a finished ticket, and `addDocuments` false without `ticket.costs.view` even with the key → Value sourcing (List, can.*)
- [ ] Audit kind label and file name come from `attachment-kinds.ts` and the row: a PNG upload named `bremse.png` logs "Vehicle photo: bremse.jpg" → Value sourcing (Audit)

### Commands
- [ ] `npm run test` in welinc-backend-vrms → passes (catalog, ability, route list and both audit readers) → AC-15, AC-16
- [ ] `npm run lint`, `npm run typecheck`, `npm run build` in welinc-web-vrms → pass

## Acceptance-criteria coverage (milestone 3)
- AC-15: the matrix step, the FORBIDDEN_KIND steps, the view_all step, the backend tests
- AC-16: the receipt visibility step, the audit filter step
- AC-17: the canRemove, NOT_YOUR_FILE, own delete and finished steps
- AC-18: the Activity step and the idempotent delete step
