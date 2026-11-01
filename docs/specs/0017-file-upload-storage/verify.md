# Verify: file upload & storage · spec 0017 · updated 2026-11-01
_Steps derived from spec 0017 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones._

## Milestone 3: permissions, remove and audit

### UI / manual
- [x] As Admin, open Settings → Roles and permissions → the Tickets group shows "Add receipts and other documents" (Admin, Chief on; Mechanic off) and "Remove anyone’s files" (Admin, Chief on; Mechanic off and locked, can't be toggled) → AC-15
- [x] As the seed Mechanic, upload a photo on an assigned ticket → `GET /vrms/repairs/:id/attachments` shows it with `canRemove: true`; as Chief on the same ticket it is also `canRemove: true` (remove any) → AC-17
- [x] As Chief, upload a photo; as the Mechanic the same row shows `canRemove: false`, and `DELETE` on it answers 403 `NOT_YOUR_FILE` → AC-17
- [x] As the Mechanic, `DELETE` your own photo → 204; the photo leaves the list; the same `DELETE` again → 204 and no second audit row → AC-17, AC-18
- [x] As Admin, open the ticket's Activity → "… added a file to REP-…" with "Vehicle photo: <name>.jpg" under it, and "… removed a file from …" after the delete → AC-18
- [x] Close the ticket, then `DELETE` a photo as Chief → 409 `TICKET_FINISHED`, and every item shows `canRemove: false` → AC-10, AC-17

### API / permissions
- [x] As the Mechanic, `POST` with `kind=RECEIPT` → 403 `FORBIDDEN_KIND` (no `ticket.documents.add`, no `ticket.costs.view`) → AC-15
- [x] Grant a Chief `ticket.documents.add` but take away `ticket.costs.view` → `RECEIPT` upload is still 403 `FORBIDDEN_KIND` → AC-15
- [x] Grant a Mechanic `ticket.view_all` → they can add photos on an unassigned ticket (addFiles follows visibility); without it the upload is 404 → AC-15, AC-16
- [x] (Once documents land in milestone 5) a receipt on a ticket: the Mechanic's list leaves it out, their `DELETE` on its id is 404, and its add and remove events are missing from the ticket Activity and from `GET /vrms/repairs/audit-logs` for any caller without `ticket.costs.view` → AC-16
- [x] Audit filter on real Postgres: a caller without `ticket.costs.view` sees `ATTACHMENT_*` rows whose `kind` is `VEHICLE_PHOTO` or `PROOF`, never `RECEIPT` or `OTHER_DOCUMENT`, and no other event type is hidden (checked once on 2026-11-01 in a rolled back transaction: 3 of 3 document rows hidden correctly, 2,291 of 2,291 other rows kept) → AC-16

### Value sourcing
- [x] `uploadedByName`, `deletedByName`: change the account's display name in welinc-auth, upload and delete → the row and the audit actor carry the new name, cut to 100 → Value sourcing (Upload, Delete)
- [x] `canRemove` varies with each input: own file vs someone else's, holding vs losing the add key for its kind (revoke `ticket.files.add` from Mechanic → own photo `canRemove: false`), holding `remove_any`, open vs finished ticket → Value sourcing (List, canRemove)
- [x] `can.addFiles`, `can.addDocuments`: false on a finished ticket, and `addDocuments` false without `ticket.costs.view` even with the key → Value sourcing (List, can.*)
- [x] Audit kind label and file name come from `attachment-kinds.ts` and the row: a PNG upload named `bremse.png` logs "Vehicle photo: bremse.jpg" → Value sourcing (Audit)

### Commands
- [x] `npm run test` in welinc-backend-vrms → passes (catalog, ability, route list and both audit readers) → AC-15, AC-16
- [x] `npm run lint`, `npm run typecheck`, `npm run build` in welinc-web-vrms → pass

## Acceptance-criteria coverage (milestone 3)
- AC-15: the matrix step, the FORBIDDEN_KIND steps, the view_all step, the backend tests
- AC-16: the receipt visibility step, the audit filter step
- AC-17: the canRemove, NOT_YOUR_FILE, own delete and finished steps
- AC-18: the Activity step and the idempotent delete step

## Milestone 4: phone photo UX

### UI / manual
- [x] On a phone (or DevTools touch emulation) at 375 px, assigned In progress ticket: "Take photo" opens the rear camera, "Choose photos" opens the picker with multiple select → AC-21
- [x] A desktop window at any width (narrow it below 768 px too) shows only "Choose photos", and dropping photos on a strip queues them → AC-21
- [x] Buttons inside an issue tag the photo to that issue (it appears under that issue, not the top strip) → AC-21
- [x] At 5 of 5 photos both buttons are disabled with "Photo limit reached (5 of 5)"; choosing 3 with 2 slots left queues 2 and says the rest were left out; on a Closed ticket the buttons don't render → AC-21
- [x] Upload a 12 MP JPEG: the request carries a JPEG, longest edge ≤ 2560 px, named `<base>.jpg` → AC-22
- [x] An iPhone HEIC from desktop Chrome goes up unchanged and displays after the server converts it → AC-22
- [x] A GIF shows "Vehicle photo accepts JPEG, PNG or HEIC photos. This file is not a recognised type." with no request sent; a file over the size setting shows the server's size message → AC-22
- [x] Choose 3 photos: they upload one at a time, each tile showing waiting, then a percentage → AC-23
- [x] Go offline mid upload: it retries after 2 s and 6 s, then shows the error with Retry and Remove; back online, Retry finishes it → AC-23
- [x] A 4xx (for example a 409 limit) shows the server's message and does not retry; uploading the same file twice counts the second as done (duplicate) → AC-23
- [x] Tap a thumbnail: the viewer shows every photo on the ticket in list order, swipe and arrow keys move, pinch and double tap zoom, the caption shows uploader, date and time in Asia/Manila, and the issue name when tagged → AC-24
- [x] Escape and the close button return focus to the thumbnail; with reduced motion on there is no animation; the viewer chunk loads only on first open (Network tab) → AC-24
- [x] "Remove photo" (only where `canRemove`) asks "Remove this photo? It disappears from the ticket for everyone.", and after the 204 the photo leaves the strip and the viewer → AC-25
- [x] Leave the tab for over 8 minutes and return: the list refetches with fresh links → AC-26
- [x] Block the storage host once: the first image error refetches the list and the photo loads; keep it blocked: the tile shows "Could not load photo" → AC-26

### Commands
- [x] `npx vitest run src/features/repair/lib/photoUpload.test.ts` (in welinc-web-vrms) → 12 pass (shrink size, names, type and size messages, retry rule, room left, Manila caption) → AC-21 to AC-24

## Acceptance-criteria coverage (milestone 4)
- AC-21 by the first four UI steps · AC-22 by the shrink, HEIC and GIF steps · AC-23 by the queue, offline and 4xx steps · AC-24 by the two viewer steps · AC-25 by the remove step · AC-26 by the two refresh steps

## Milestone 5: documents and retention

### API / files
- [x] As Admin, `POST` a PDF with `OpenAction` JavaScript and an embedded file as `OTHER_DOCUMENT` → 201; open its signed link → `application/pdf`, `inline` disposition, same page count, and the stored bytes contain no `JavaScript`, `OpenAction`, `EmbeddedFile` or `Filespec` (checked live on 2026-11-01) → AC-7
- [x] A PDF with links: `https`, `mailto` and `tel` links still work in the stored copy; `javascript:`, `file:`, `Launch` actions, comments and links over 2048 characters are gone → AC-7
- [x] A filled form PDF: the stored copy shows the typed values but has no fillable fields → AC-7
- [x] A scanned (image only) receipt PDF and one whose pages inherit MediaBox and Resources: stored, same size and look → AC-7
- [x] An `.exe` renamed `.pdf` → 415 `FILE_TYPE_NOT_ALLOWED` "Other document accepts PDF files. This file is not a recognised type."; a PDF sent as `VEHICLE_PHOTO` → 415 "… This file is PDF." → AC-4
- [x] An encrypted PDF (owner password only included) → 422 `FILE_ENCRYPTED`; 21 pages → 422 `PDF_TOO_MANY_PAGES` "PDFs can have 1 to 20 pages. This one has 21."; `%PDF-` followed by junk → 422 `FILE_UNREADABLE` → AC-7
- [x] Documents get no thumbnail (`thumbnailUrl: null`) and the stored name ends in `.pdf` → AC-7, data model
- [x] A real receipt from a supplier (scanned at the shop, or an e-invoice): it uploads and looks the same after the rebuild. pdf-lib is the risk named in the spec's Consequences → AC-7

### UI / manual
- [x] As Admin or Chief at 375 px: the Documents card sits under People, lists kind label, file name, uploader and Manila date and time; a long name wraps with no horizontal scroll (checked at 375 and 1280 px on 2026-11-01) → AC-27, AC-28
- [x] Open opens the signed link in a new tab (`rel="noopener noreferrer"`) → AC-27
- [x] Add document: choose a PDF → a tile shows waiting and the percentage, then the document joins the list; choose a JPEG → the tile fails with "Other document accepts PDF files. This file is JPEG." and no request is sent (checked live) → AC-22, AC-23, AC-27
- [x] Document uploads never show in a photo strip, and photo uploads never show in the Documents card → AC-23, AC-27
- [x] Remove (only where `canRemove`) asks "Remove this document? It disappears from the ticket for everyone.", then the row leaves the list → AC-27
- [x] Set `uploads.max_documents` to the current count → "Add document" is gone and "Document limit reached" shows → AC-27, AC-9
- [x] As the Mechanic: no Documents card, the list response has no receipts or other documents, and `DELETE` on a document id is 404 → AC-16, AC-27
- [x] On a Closed ticket: no "Add document", no Remove → AC-10, AC-27
- [x] With storage unset: the card shows "File storage is not available right now." → AC-3
- [x] axe on the ticket detail with photos and documents, at 375 px and 1280 px, as Admin, Chief and Mechanic → no serious or critical issues. Not run yet: loading axe from a CDN was blocked during /develop → AC-28

### Retention
- [x] Set a removed attachment's `deleted_at` to 31 days ago, run the pass (wait for 03:00 Manila, or restart the backend and wait 2 minutes) → its blobs are gone, `purged_at` is set, the row and its audit events stay, and it never comes back in the list → AC-19
- [x] A row removed 29 days ago keeps its blobs → AC-19
- [x] Put a blob under `tickets/<ticketId>/<random uuid>/file.jpg` in Azurite → it survives a pass while younger than 24 hours by `createdOn` (no row), and goes on the first pass after that → AC-19
- [x] Restart with no due rows → the after boot pass does not run (no "Retention" log line) → AC-19
- [x] Two replicas (or two parallel `run()` calls) → one takes the advisory lock, the other skips → AC-19

### Value sourcing
- [x] Purge due rows: vary `deleted_at` either side of 30 days and `purged_at` null or set → only `deleted_at < now() - 30 days AND purged_at IS NULL` rows purge → Value sourcing (Purge)
- [x] Orphan blobs: a blob whose id has a row (even a purged or removed one) is never swept; `createdOn`, never `lastModified`, decides the 24 hours → Value sourcing (Orphan sweep)
- [x] `mimeType`, `sizeBytes` of a document are the rebuilt file's (smaller than the upload for the hostile PDF), `width` and `height` null → Value sourcing (Upload)
- [x] `limits.documentCount` counts live receipts plus other documents, and is 0 for a caller without `ticket.costs.view` → Value sourcing (List, limits)

### Commands
- [x] `npx jest src/modules/attachments` in welinc-backend-vrms → 57 pass (PDF rebuild fixtures, sniff, image pipeline, keys and links, canRemove, purge job) → AC-1 to AC-7, AC-17, AC-19
- [x] `npx vitest run src/features/repair/lib/photoUpload.test.ts` in welinc-web-vrms → passes, including document room and the PDF type message → AC-27

## Acceptance-criteria coverage (milestone 5)
- AC-4 by the renamed exe and PDF as photo steps · AC-7 by the hostile PDF, links, form, scanned and inherited, encrypted and page count steps, plus the real receipt step · AC-19 by the five retention steps · AC-27 by the Documents card steps · AC-28 by the 375 px step and the axe step (still owed)
