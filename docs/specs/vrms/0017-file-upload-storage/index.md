# 0017. File upload and storage: private Blob storage, signed links, and vehicle photos

**Date**: 2026-11-01
**Status**: Accepted

## Summary

Repair tickets get one private place for files: vehicle photos, proof of completion, outsourced receipts and other documents. The files live in Azure Blob Storage (Azure's file store), with Azurite (its local copy) in Docker. The browser only gets a link that works for one file, for 10 minutes, after the server checks the person may see it. Every upload goes through the backend, which checks the real file type, turns iPhone HEIC photos into JPEG, shrinks photos, rebuilds PDFs without scripts, and records ticket, kind, uploader and time. This feature also builds the vehicle photos screens (scope feature 21 is folded in): take or choose up to 5 photos from a phone, watch the upload progress, retry failures, see thumbnails in Issue Details and swipe through them in a zoomable viewer.

## Requirements

**User stories**:
- As a Mechanic, I want to take photos of the problem with my phone camera and attach them to my ticket, so the Admin and Chief Mechanic see what I see.
- As an Admin or Chief Mechanic, I want to see thumbnails in Issue Details and zoom into a full size photo, so I understand the problem without asking.
- As an Admin or Chief Mechanic, I want to attach receipts and other documents that mechanics can't see, so cost paperwork stays with the ticket and private.
- As the team, we want one upload service with the same rules for every kind of file, so proof (feature 22) and receipts (outsourcing) only add their own screens.
- As the system owner, I want files to be private and checked, so a leaked link expires fast and a malicious file can't do harm.

**Acceptance criteria**:

*Storage and links*
- **AC-1**: File bytes live in one private Blob container (public access off). Locally that's an `azurite` service in `docker-compose.vrms.yml` with a named volume. Keys follow `tickets/<ticketId>/<attachmentId>/file.<ext>` and `.../thumb.webp`. Nothing is written to the container's disk, and backend-vrms no longer serves `/uploads/` (the static route in `main.ts` is removed).
- **AC-2**: Every link the API returns is a read only SAS link (shared access signature, a signed URL) for exactly one blob. Its window is stable, so the browser cache can reuse it:
  - it starts at the current 10 minute boundary minus 5 minutes (clock skew)
  - it expires at the next 10 minute boundary plus 10 minutes, so a link always has 10 to 20 minutes left when issued, and every list call inside one window returns the same URL
  - HTTPS only in Azure; Azurite links are http
  - it forces `Content-Type` to the stored type, sets `Content-Disposition` (format in *Backend layout*), and sets `Cache-Control: private, max-age=600`

  In Azure the links are user delegation SAS signed through the backend's managed identity. The delegation key is requested from now minus 15 minutes to now plus 24 hours (the SAS window must sit inside the key's window) and renewed when under 1 hour is left. Locally they're signed with Azurite's account key from the connection string. A link opened after it expires answers 403 from storage.
- **AC-3**: With no storage configured (neither `STORAGE_ACCOUNT_URL` nor `STORAGE_CONNECTION_STRING`), the app still starts. Every attachment route answers **503** `{ code: 'STORAGE_UNAVAILABLE', message: 'File storage is not available right now.' }`, and the ticket detail shows that message in place of the photos and documents.

*Upload rules*
- **AC-4**: `POST /vrms/repairs/:id/attachments` takes multipart `file` (one file), `kind` and an optional `issueId`. Kinds and their accepted types, judged by the file's first bytes (magic bytes), never its name or the browser's type:
  - `VEHICLE_PHOTO`: JPEG, PNG or HEIC/HEIF
  - `PROOF` and `RECEIPT`: JPEG, PNG, HEIC/HEIF or PDF
  - `OTHER_DOCUMENT`: PDF only

  Anything else answers **415** `{ code: 'FILE_TYPE_NOT_ALLOWED', message: '<Kind label> accepts <list>. This file is <detected or "not a recognised type">.' }`. A renamed executable is rejected this way.
- **AC-5**: The size limit is the setting `uploads.max_file_mb` (int, default 10, min 1, max 25, unit MB, group `Files`), read through `SettingsService`. Multer holds the upload in memory with `limits: { fileSize: 25 MB + 1 byte, files: 1, fields: 5 }`. Multer's `LIMIT_FILE_SIZE` answers **413** `{ code: 'FILE_TOO_LARGE', message: 'Files can be up to <n> MB. This one is over 25 MB.' }`. Otherwise, a `buffer.length` over the setting answers 413 with 'Files can be up to <n> MB. This one is <x.y> MB.' A request with no file, or `LIMIT_UNEXPECTED_FILE`, is **400** `{ code: 'NO_FILE' }`.
- **AC-6**: Photos (any image kind): HEIC/HEIF is first converted to JPEG with `heic-convert` (quality 0.92). Then `sharp` (with `limitInputPixels` 40,000,000) rotates the image upright from its EXIF orientation, converts it to sRGB (`.toColorspace('srgb')`, so iPhone Display P3 photos keep their colors once the profile is dropped), drops all metadata (EXIF, GPS, ICC), flattens transparency onto white, and writes:
  - a display copy: JPEG quality 82, longest edge at most 2048 px, never enlarged
  - a thumbnail: WebP, 320 × 320, cover crop

  The row stores the display copy's `mimeType` (`image/jpeg`), `sizeBytes`, `width` and `height`. An image that can't be decoded, or that is over the pixel cap, answers **422** `{ code: 'FILE_UNREADABLE', message: 'This image could not be read. Try taking the photo again.' }`. The original upload is not kept.
- **AC-7**: PDFs:
  - must start with `%PDF-`
  - must load in `pdf-lib` (`ignoreEncryption: false`, `updateMetadata: false`); an encrypted PDF is **422** `FILE_ENCRYPTED` ("Password protected or locked PDFs can't be attached. Save or print it as a new PDF first."), and this includes owner password only PDFs, any other parse failure is **422** `FILE_UNREADABLE`
  - must have 1 to 20 pages, else **422** `PDF_TOO_MANY_PAGES`

  An accepted PDF is rebuilt before storage (disarm and rebuild). Form fields are flattened (best effort), then every page is copied into a new document. The new document carries no document JavaScript, no `OpenAction`, no embedded files and no page `/AA` actions. Every annotation is dropped except `/Link` annotations whose action is `/URI` with an `http`, `https`, `mailto` or `tel` scheme and at most 2048 characters (`javascript:`, `file:` and the rest are dropped). Only the rebuilt file is stored. PDFs get no thumbnail. Test fixtures cover inherited MediaBox and Resources, a scanned (image only) PDF, a filled form, and a PDF with `OpenAction` JavaScript and an embedded file.
- **AC-8**: The `sha256` column holds the lowercase hex SHA-256 of the bytes as uploaded, computed before any processing. If a live (not deleted) attachment on the same ticket with the same kind and hash exists, the endpoint stores nothing and answers **200** with that attachment and `duplicate: true`. This is checked twice: once before processing (to skip the work), and again under the ticket row lock before the caps (AC-9), so a retry at 5 of 5 photos gets 200, not 409. In that case the blobs just written are deleted. The partial unique index is only a backstop: a P2002 aborts the transaction, so it's caught outside the transaction, the blobs are deleted, and the existing row is read again and returned with 200.
- **AC-9**: Limits, counted over live attachments on the ticket:
  - vehicle photos at most `uploads.max_vehicle_photos` (int, default 5, min 1, max 20, group `Files`), else **409** `{ code: 'PHOTO_LIMIT_REACHED', message: 'This ticket already has <n> photos, the most allowed. Remove one to add another.' }`
  - receipts plus other documents together at most `uploads.max_documents` (int, default 20, min 1, max 100, group `Files`), else **409** `DOCUMENT_LIMIT_REACHED`

  The count is checked once before processing (fast fail), then again inside the insert transaction after `SELECT id, repair_status FROM repair_tickets WHERE id = $1 FOR NO KEY UPDATE`. That lock serializes uploads to one ticket without blocking other writers' child inserts. Lock order is ticket, then attachment, then audit. So two parallel uploads can't pass the limit. The interactive transaction sets `timeout: 10000`, and holds no blob I/O. Proof has no count cap in this feature.
- **AC-10**: Files can be added or removed only while the ticket is in an open status (`OPEN_STATUSES`, via `isFinished`). A finished ticket answers **409** `{ code: 'TICKET_FINISHED', message: 'This ticket is <Closed|Cancelled>. Files can no longer change.' }`, checked again under the row lock.
- **AC-11**: `issueId` is accepted only with `VEHICLE_PHOTO` and must be an issue on the same ticket, else **400** `{ code: 'ISSUE_NOT_ON_TICKET' }`. It's checked before processing and again inside the lock transaction, so an issue deleted in between gives the 400, not a foreign key 500. If that issue is later deleted, the photo's `issueId` becomes null and the photo stays on the ticket.
- **AC-12**: Uploads are rate limited per user to 30 a minute, in memory per replica, on the upload route only. `ThrottlerModule.forRoot` registers no global guard. The POST route carries `@UseGuards(UploadAccessGuard, UserThrottlerGuard)` plus `@Throttle({ default: { limit: 30, ttl: 60000 } })`, where `UserThrottlerGuard` extends `ThrottlerGuard` with `getTracker` returning `req.user.sub` (these run after the global JWT and permission guards, so `req.user` exists). The route keeps `@Authenticated()` for `route-permissions.spec.ts`. Over the limit answers **429** `{ code: 'UPLOAD_RATE_LIMITED', message: 'Too many uploads in a minute. Wait a moment and try again.' }`.
- **AC-12a**: The upload's body is not read until the caller is known to see the ticket. `UploadAccessGuard` runs the ticket visibility check (AC-16) for `:id` (404 otherwise), then the throttle, and only then does the `FileInterceptor` buffer the file. So nobody can make the server load 25 MB for a ticket they can't see.
- **AC-12b**: Error order is fixed, the first failing check wins. Upload: 404 ticket, 429 rate, 400 `kind`/DTO, 403 `FORBIDDEN_KIND`, 409 `TICKET_FINISHED`, 413 size, 400 `NO_FILE`, 415 type, 400 `ISSUE_NOT_ON_TICKET`, 200 duplicate (pre check), 409 caps (pre check), 422 pipeline. Then under the lock: 409 finished, 400 issue, 200 duplicate, 409 caps. Delete: 404 (ticket or attachment not visible), 204 if already deleted, 403 `NOT_YOUR_FILE`, 409 `TICKET_FINISHED`.
- **AC-13**: Adding or removing a file never writes the `repair_tickets` row (its `updatedAt` and the 409 stale check are unaffected), even though the transaction locks it.
- **AC-14**: The blobs are written before the database insert. If the insert (or anything after the first blob write) fails, the backend deletes the blobs it wrote before it answers. The gateway accepts bodies up to 26 MB on `/vrms` and `/repairs` (`client_max_body_size 26m` in `welinc-auth/nginx.conf`); without it nginx answers 413 before the backend sees the request. The same locations get `proxy_read_timeout 120s`, because a queued HEIC conversion on a cold replica can pass nginx's 60 s default.

*Permissions*
- **AC-15**: New permission keys in `catalog.ts` (group `Tickets`):
  - `ticket.files.add`: "Add vehicle photos and proof", described as "on the tickets you can see". Admin on, Chief on, Mechanic on.
  - `ticket.documents.add`: "Add receipts and other documents". Admin on, Chief on, Mechanic off.
  - `ticket.files.remove_any`: "Remove anyone's files". Admin on, Chief on, Mechanic off and locked.

  CASL shape: `AppAction` gains `addFiles`, `addDocuments` and `removeAny`, all on `RepairTicket`.
  - `ticket.files.add` follows the caller's ticket visibility: `can('addFiles', 'RepairTicket')` with no condition when the caller also holds `ticket.view_all`, else `can('addFiles', 'RepairTicket', mine)`. So Admin and Chief add on every ticket and a Mechanic on their assigned ones. If an Admin grants a Mechanic `ticket.view_all`, that Mechanic can add wherever they can see.
  - `ticket.documents.add` gives `can('addDocuments', 'RepairTicket')`, and `ticket.files.remove_any` gives `can('removeAny', 'RepairTicket')`, both with no condition. They're useful only on tickets the caller can see, which the 404 check already ensures.
  - `catalog.spec.ts` and the ability tests cover the three keys, including a Mechanic with `ticket.view_all`.

  Upload of `VEHICLE_PHOTO` or `PROOF` needs `addFiles` on the ticket. `RECEIPT` or `OTHER_DOCUMENT` needs `addDocuments` **and** `ticket.costs.view`, so nobody can upload what they can't see, and a duplicate answer can't leak a hidden file. Both are checked in the service, since the route serves every kind. Without the right: **403** `{ code: 'FORBIDDEN_KIND' }`.
- **AC-16**: Ticket visibility is one helper, `findVisibleTicket(ability, id)`. It runs `prisma.repairTicket.findFirst({ where: { id, AND: [accessibleBy(ability, 'read').RepairTicket] }, select: { id, repairStatus } })` and throws 404 when it finds nothing. It's exported for the guard and the service. Anyone who can see the ticket sees its vehicle photos and proof. Receipts and other documents are listed and linked only for callers with `ticket.costs.view`. For others they are left out of the list and their delete answers 404. Their audit events are hidden by one shared `where` fragment, `hideDocumentEvents(canViewCosts)`, which excludes `ATTACHMENT_ADDED` and `ATTACHMENT_REMOVED` rows whose `changes` hold `{ field: 'kind' }` with `RECEIPT` or `OTHER_DOCUMENT`. Both readers apply it: the ticket's activity and the global `findAuditEvents` (`GET /vrms/audit`), which now receives the caller's ability. A test covers each reader.
- **AC-17**: `DELETE /vrms/repairs/:id/attachments/:attachmentId` soft deletes: it sets `deletedAt`, `deletedByUserId` and `deletedByName`. The uploader may remove their own file when they still hold the add key for its kind and can see the ticket. Anyone with `ticket.files.remove_any` may remove any file they can see. Otherwise it's **403** `{ code: 'NOT_YOUR_FILE' }`. An already deleted attachment answers 204 again (idempotent). Each item in the list carries `canRemove`, computed by the same rule.
- **AC-18**: Adding writes the audit event `ATTACHMENT_ADDED` and removing writes `ATTACHMENT_REMOVED`, both in the same transaction as the row, with the actor from `auditActor(user)`. `changes` holds three elements:
  - `{ field: 'attachment', before, after }`, with `'<Kind label>: <fileName>'` in `after` on add and in `before` on remove
  - `{ field: 'attachmentId', before: null, after: id }`
  - `{ field: 'kind', before: null, after: KIND }`

  This is the way `KNOWLEDGE_LINK` carries `issueId`, as elements of `changes`, since `AuditLog` has no extra columns. A duplicate answer (AC-8) writes nothing.

*Retention*
- **AC-19**: A retention pass runs daily at 03:00 Asia/Manila (`@nestjs/schedule`). Staging scales to zero and may be asleep at 03:00, so the pass also runs once 2 minutes after boot, but only when a due row exists. It runs on one replica only: a transaction holds `pg_try_advisory_xact_lock` (the pattern in `embedding.service.ts`, with a raised transaction `timeout`), and a replica that doesn't get the lock skips. It does two things:
  - deletes the blobs of attachments deleted more than 30 days ago that aren't purged yet, 100 at a time (a missing blob counts as deleted), and sets `purgedAt` after the blob delete, so a crash in between is harmless; the row stays, so the audit trail can still name the file
  - deletes blobs under `tickets/` whose `attachmentId` has no row and whose blob `createdOn` (never `lastModified`) is older than 24 hours (orphans), which leaves in flight uploads alone

  Both are idempotent. A purged attachment never appears in the list.

*Web: vehicle photos (folds in scope feature 21, WL-209 and WL-210)*
- **AC-20**: `IssuesSection` shows a Photos strip at the top for untagged photos, and one under each issue for photos tagged to it. Each thumbnail is an `<img loading="lazy">` with its stored `width` and `height` (so space is reserved before it loads) and an alt text of "Photo by <name>, <date>". With no photos, a mechanic who can add sees a short empty state with the add buttons, and others see nothing.
- **AC-21**: With `ticket.files.add` on an open ticket, the top strip and each issue offer two buttons. "Take photo" is `<input type="file" accept="image/*" capture="environment">` and opens the rear camera directly. "Choose photos" is `accept="image/*"` with `multiple`. Buttons inside an issue tag the photo to that issue. On desktop only "Choose photos" shows, and the strip also accepts drag and drop. The buttons are disabled with "Photo limit reached (5 of 5)" when the count is at the limit. On a finished ticket they don't render.
- **AC-22**: Before upload, the browser shrinks each photo it can decode (`createImageBitmap` with `imageOrientation: 'from-image'`). The longest edge goes to at most 2560 px, as JPEG quality 0.85, named `<original base name>.jpg`. If decoding fails (for example HEIC on desktop Chrome), or the result is bigger than the original, the original is sent. The browser also checks the size limit and the accepted types from the list response's `limits` and `kinds` (labels and accepted types come from the server, so the web keeps no copy) and shows the same message as the server. The server stays the authority.
- **AC-23**: Selected files go into an in memory queue per ticket and upload one at a time. Each shows a tile with its state (waiting, uploading with a percentage from `onUploadProgress`, done, failed). A network error or a 5xx retries automatically twice (after 2 s, then 6 s), then the tile shows the error with Retry and Remove. A 4xx never retries and shows the server's `message`. A 200 `duplicate` counts as done. Leaving the page drops unfinished uploads (persisting the queue is the offline feature's job).
- **AC-24**: Tapping a thumbnail opens the photo viewer: `yet-another-react-lightbox`, imported lazily on first open, with only the Zoom and Captions plugins. It shows every live photo on the ticket in list order, with swipe, Previous and Next, arrow keys, pinch and double tap zoom, and a caption with uploader name, date and time (Asia/Manila), plus the issue's name when tagged. It's themed only through its CSS variables mapped to `design.md` tokens, and with `prefers-reduced-motion` its animations are off. Escape and the close button return focus to the thumbnail.
- **AC-25**: A thumbnail the user may remove (`canRemove`) has a remove button with the accessible name "Remove photo". It opens a confirm dialog ("Remove this photo? It disappears from the ticket for everyone."), and after the 204 the photo leaves the strip and the viewer.
- **AC-26**: Links are refreshed without the user noticing. The list query has `staleTime` 8 minutes and refetches on window focus. The first image load error refetches the list once, and a second failure shows "Could not load photo" on that tile.

*Web: documents*
- **AC-27**: `TicketSidePanel` shows a Documents card only to callers with `ticket.costs.view`. It lists receipts and other documents (kind label, file name, uploader, date) with Open (the signed link in a new tab, `rel="noopener noreferrer"`) and Remove (when `canRemove`, same confirm pattern as AC-25). With `ticket.documents.add` on an open ticket, "Add document" uploads one PDF as `OTHER_DOCUMENT` through the same queue and error handling. The card hides "Add document" at the documents limit and shows "Document limit reached".
- **AC-28**: The photo and document UI works at 375 px with no horizontal scroll, every control is reachable by keyboard and has an accessible name, and axe reports no serious or critical issues on the ticket detail with photos and documents at 375 px and 1280 px, for all three roles.

## Decision

**Chosen option**: Option 1: Azure Blob Storage behind a `FileStore` seam, uploads processed in backend-vrms, read through short lived user delegation SAS links.

One private Blob container per environment (Azurite locally). backend-vrms validates, converts, shrinks, disarms and hashes every upload in memory, then writes it. The SPA reads files only through 10 minute, single blob, read only links issued after a permission check.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` and `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-client-api/`, `.claude/skills/prisma-cli/`) · `azure-blob-storage` (`microsoftdocs/agent-skills`, `.claude/skills/azure-blob-storage/`, ask first) · `vercel-react-best-practices` (`.claude/skills/vercel-react-best-practices/`) · `shadcn` (`.claude/skills/shadcn/`) · `ask-sonner` (`.claude/skills/ask-sonner/`) · `tailwind-4-docs` (`.claude/skills/tailwind-4-docs/`) · `docker-patterns` (`.claude/skills/docker-patterns/`, ask first, for the Azurite service)

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch**

New enum `AttachmentKind`: `VEHICLE_PHOTO`, `PROOF`, `RECEIPT`, `OTHER_DOCUMENT`. Labels in code: "Vehicle photo", "Proof of completion", "Receipt", "Other document".

New table `Attachment` (`@@map("attachments")`), spec 0010's design with the changes noted:

| Field | Type | Null | Notes |
|---|---|---|---|
| `id` | uuid | no | **PK**, generated by the backend before the blob write (it's part of the key) |
| `repairTicketId` | uuid | no | **FK** → `RepairTicket.id`, `onDelete: Restrict` |
| `issueId` | uuid | yes | **FK** → `RepairIssue.id`, `onDelete: SetNull`. New vs 0010. `VEHICLE_PHOTO` only, same ticket |
| `kind` | `AttachmentKind` | no | |
| `storageKey` | varchar 300 | no | unique |
| `thumbnailKey` | varchar 300 | yes | images only |
| `fileName` | varchar 255 | no | the upload's name: path parts and control characters removed, trimmed, cut to 255. A shrunk photo is `<base>.jpg`. Empty becomes `file.<ext>` |
| `mimeType` | varchar 100 | no | of the stored bytes |
| `sizeBytes` | int | no | of the stored bytes |
| `width`, `height` | int | yes | display copy, images only. New |
| `sha256` | char 64 | no | uploaded bytes. New |
| `uploadedByUserId` | uuid | no | welinc-auth id, no FK |
| `uploadedByName` | varchar 100 | no | name copied at upload |
| `createdAt` | timestamptz | no | default now |
| `deletedAt` | timestamptz | yes | |
| `deletedByUserId`, `deletedByName` | uuid, varchar 100 | yes | New |
| `purgedAt` | timestamptz | yes | New |

Indexes: `(repairTicketId, kind)` and `storageKey` unique. Two more are written as raw SQL in the migration: a partial unique `(repair_ticket_id, kind, sha256) WHERE deleted_at IS NULL`, and a partial `(deleted_at) WHERE purged_at IS NULL AND deleted_at IS NOT NULL` for the purge.

Relationships: `RepairTicket` 1 : N `Attachment`, `RepairIssue` 1 : N `Attachment` (optional).

Change from spec 0010: `outsourcedJobId` is left out, because its table doesn't exist yet. The outsourcing feature adds it in its own migration.

Settings (spec 0012 catalog, new group `Files`): `uploads.max_file_mb`, `uploads.max_vehicle_photos`, `uploads.max_documents`, as in AC-5 and AC-9.

Audit (spec 0010's event table gets two rows): `ATTACHMENT_ADDED` and `ATTACHMENT_REMOVED`, with field `attachment` and extras `attachmentId` and `kind`.

**State transitions**: an attachment is live (`deletedAt` null), then removed (`deletedAt` set, bytes kept), then purged (`purgedAt` set, bytes gone, row kept). Only these forward moves exist. Restoring a removed file within the 30 days is a manual database fix, not a feature.

**Backend layout** (backend-vrms):
- `src/modules/attachments/`
  - `attachments.module.ts`
  - `attachments.controller.ts`
  - `attachments.service.ts`: rules, transaction, audit
  - `file-store.ts`: the `FileStore` interface (`put`, `delete`, `readUrl`, `list`)
  - `blob-file-store.ts`: the Azure SDK implementation, `@azure/storage-blob` and `@azure/identity`
  - `file-sniff.ts`: magic bytes for JPEG `FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`, HEIC/HEIF (an `ftyp` box with brand `heic`, `heix`, `hevc`, `hevx`, `mif1` or `msf1`) and PDF `%PDF-`; no dependency
  - `image-pipeline.ts`: heic-convert, sharp
  - `pdf-pipeline.ts`: pdf-lib checks and rebuild
  - `attachment-purge.job.ts`
  - `attachment-kinds.ts`: kind labels, accepted types, which add key each kind needs
- `attachments.guard.ts`: `UploadAccessGuard` (AC-12a), and `UserThrottlerGuard` (AC-12).
- Only `blob-file-store.ts` imports the Azure SDK. Processing runs before the transaction. Per replica semaphores allow 1 HEIC conversion and 2 other images to process at once (others wait), and `sharp.concurrency(1)` keeps CPU and memory steady on a 0.5 vCPU, 1 GiB container. `/check verify` measures peak memory with a 48 MP iPhone HEIC.
- Credential choice, read once at startup: `STORAGE_CONNECTION_STRING` wins and uses `StorageSharedKeyCredential` (shared key SAS). Else `STORAGE_ACCOUNT_URL` uses `DefaultAzureCredential` and `getUserDelegationKey`. Neither set means 503 (AC-3). Both set logs a warning and uses the connection string.
- Container: `createIfNotExists` (private) is best effort on startup and never fatal (a role assignment can take minutes to apply). On failure it logs a warning and tries again on first use. In Azure the Bicep creates the container anyway.
- Blob writes set `blobContentType`, `blobContentDisposition` and `blobCacheControl`, and send `transactionalContentMD5`, so Azure verifies the bytes on write and keeps the MD5.
- `Content-Disposition`, one string used for the blob property and the SAS `rscd` override: `inline; filename="<ASCII fallback>"; filename*=UTF-8''<encoded>`. `<encoded>` is `encodeURIComponent(fileName)` with `'`, `(`, `)` and `*` also percent encoded. The ASCII fallback replaces non ASCII characters, `"` and `\` with `_`.
- SAS link URL: signed over the container and blob name. The URL is `${STORAGE_PUBLIC_URL ?? accountUrl}/${container}/${key}?${sas}`. Locally the backend talks to `http://azurite:10000/devstoreaccount1`, but the browser needs `http://localhost:10000/devstoreaccount1`, and the account name stays in the path, so the signature still holds. A unit test pins the URL shape for both paths.
- Uploader and remover names: `whoName(user)` from `audit-events.ts`, cut to 100 characters.
- Docker: the image stays `node:24-alpine`, since sharp ships `linuxmusl-x64` prebuilt binaries and heic-convert is pure WebAssembly, so no apk packages are needed. Production installs must not use `--omit=optional` (sharp's binary is an optional dependency). After pulling new dependencies, run `docker compose ... up --build -V`, because the anonymous `/app/node_modules` volume hides them.
- Azurite service: `mcr.microsoft.com/azure-storage/azurite`, blob only, `azurite-blob --blobHost 0.0.0.0 --loose --skipApiVersionCheck`, port 10000, a named volume, a healthcheck, and `vrms-backend` `depends_on` it.

**API surface**

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/repairs/:id/attachments` | POST | multipart `file` (req), `kind`: `AttachmentKind` (req), `issueId`: uuid (opt) | 201 `AttachmentView`; 200 `AttachmentView` + `duplicate: true` | `@Authenticated()`, then the add key for the kind in the service (AC-15) | 400 `NO_FILE` / `ISSUE_NOT_ON_TICKET`, 403 `FORBIDDEN_KIND`, 404 ticket, 409 `TICKET_FINISHED` / `PHOTO_LIMIT_REACHED` / `DOCUMENT_LIMIT_REACHED`, 413 `FILE_TOO_LARGE`, 415 `FILE_TYPE_NOT_ALLOWED`, 422 `FILE_UNREADABLE` / `FILE_ENCRYPTED` / `PDF_TOO_MANY_PAGES`, 429 `UPLOAD_RATE_LIMITED`, 503 `STORAGE_UNAVAILABLE` |
| `/vrms/repairs/:id/attachments` | GET | none | `{ items: AttachmentView[], urlsExpireAt, limits: { maxFileMb, maxVehiclePhotos, maxDocuments, vehiclePhotoCount, documentCount }, kinds: [{ kind, label, accepts: mime[], acceptsLabel }], can: { addFiles, addDocuments } }` | `@Authenticated()` + `findVisibleTicket` | 404 ticket, 503 |
| `/vrms/repairs/:id/attachments/:attachmentId` | DELETE | none | 204 | `@Authenticated()` + AC-17 rule | 403 `NOT_YOUR_FILE`, 404, 409 `TICKET_FINISHED`, 503 |

`AttachmentView`: `{ id, kind, issueId, fileName, mimeType, sizeBytes, width, height, uploadedBy: { id, name }, createdAt, url, thumbnailUrl | null, canRemove }`.

The list has no pagination on purpose. It's bounded by the settings caps (at most 20 photos and 100 documents) plus proof, which the rate limit bounds. Order: `createdAt` ascending, then `id`.

**Value sourcing**

| Action | Value produced / displayed | Source |
|---|---|---|
| Upload | detected type | first bytes, `file-sniff.ts` |
| Upload | size limit | setting `uploads.max_file_mb` |
| Upload | photo and document caps | settings `uploads.max_vehicle_photos`, `uploads.max_documents` |
| Upload | ticket open or finished | `RepairTicket.repairStatus`, read under the row lock, `isFinished` |
| Upload | right for the kind | CASL ability from `PermissionsService.abilityFor(user)`, the action (`addFiles` / `addDocuments`, plus `ticket.costs.view` for documents) from `attachment-kinds.ts` |
| Upload | ticket visible | `findVisibleTicket(ability, id)` (AC-16) |
| Upload | `uploadedByUserId`, `uploadedByName` | `req.user.sub` and `whoName(user)`, cut to 100 |
| Upload | `sha256` | computed over the multer buffer before processing |
| Upload | `id`, `storageKey`, `thumbnailKey` | `randomUUID()` in the service, then the key pattern in AC-1 |
| Upload | `fileName` | multer `originalname`, cleaned (data model note) |
| Upload | `mimeType`, `sizeBytes`, `width`, `height` | output of the image or PDF pipeline |
| Upload | rate limit identity | `req.user.sub` |
| List | `url`, `thumbnailUrl`, `urlsExpireAt` | `FileStore.readUrl(key, fileName, mimeType)`, window from AC-2 (10 minute boundaries); host from `STORAGE_PUBLIC_URL` or the account URL |
| List | `kinds[]` labels and accepted types | `attachment-kinds.ts` |
| Activity, `/vrms/audit` | which attachment events show | `hideDocumentEvents(canViewCosts)` over `changes` `kind` (AC-16) |
| List | which kinds show | `ticket.costs.view` on the caller's ability (AC-16) |
| List | `canRemove` | AC-17 rule over `uploadedByUserId`, the add key for the kind, `ticket.files.remove_any`, and `isFinished` |
| List | `limits.*` | the three settings, plus live counts from `attachments` |
| List | `can.addFiles`, `can.addDocuments` | ability for `ticket.files.add` / `ticket.documents.add` on this ticket, and not finished |
| Viewer caption | uploader name, date and time | `uploadedBy.name`, `createdAt` shown in Asia/Manila (the app's fixed zone) |
| Viewer caption | issue name | the ticket's issues already loaded by `useRepairTicket`, matched by `issueId` |
| Delete | `deletedByUserId`, `deletedByName` | `req.user.sub` and `whoName(user)`, cut to 100 |
| Purge | due rows | `deletedAt < now() - 30 days AND purgedAt IS NULL` |
| Orphan sweep | orphan blobs | blob list under `tickets/`, the `attachmentId` parsed from the key, blob `createdOn` older than 24 h, no row |
| Audit | kind label, file name | `attachment-kinds.ts`, the row's `fileName` |

**Key invariants**
- Bytes are reachable only through a signed link issued after the permission check. The container never allows public access.
- A stored image is always a re-encoded JPEG or WebP without metadata, and a stored PDF is always a rebuilt one. No uploaded bytes are stored unchanged.
- At most one live attachment per (ticket, kind, sha256) (database index).
- Live vehicle photos ≤ `uploads.max_vehicle_photos`, and live receipts plus other documents ≤ `uploads.max_documents`, checked under the ticket row lock.
- No attachment changes on a finished ticket.
- A row exists for every blob older than 24 hours, and a blob exists for every live row (writes before insert, cleanup on failure, nightly sweep).
- Attachment writes never touch `repair_tickets`.
- Every add and remove has its audit row in the same transaction.

**Security model**
- Rights: AC-15 to AC-17. Adding photos and proof follows ticket visibility ("assigned to me" via the same `mine` condition as `ticket.work`, unless the caller holds `ticket.view_all`). No role names in code; everything goes through CASL. The upload body is never read before the visibility check (AC-12a).
- Cost data: receipts and other documents are hidden from anyone without `ticket.costs.view` in the list, delete and activity, matching "mechanics never see cost data" (roles-and-users).
- File attacks: types come from magic bytes, images are re-encoded (this strips hidden payloads, polyglots and GPS), PDFs are disarmed and rebuilt, `limitInputPixels` stops decompression bombs, and the upload size has a hard cap at multer and the gateway.
- Serving: files come from the storage domain, a different origin from the app, so nothing in a file can read the app's token. The forced `Content-Type` and `inline` disposition, plus `nosniff` (sent by Blob Storage), stop type confusion.
- Links: one blob, read only, 10 minutes, HTTPS in Azure. A leaked link works until it expires. That's the accepted tradeoff.
- Credentials: managed identity with the "Storage Blob Data Contributor" role on its own account only. No account key in Azure. Locally the Azurite connection string is the public development key.
- Abuse: 30 uploads per user per minute, plus the caps. QA's security tests (Jira VRMS-291, VRMS-294) target AC-4 to AC-7 and AC-12.

**Configuration required** (backend-vrms `.env.example`, values never committed):
- `STORAGE_CONNECTION_STRING`: local only, the Azurite connection string (signs links with the shared key). Unset in Azure.
- `STORAGE_ACCOUNT_URL`: Azure only, `https://<account>.blob.core.windows.net`, used with `DefaultAzureCredential` (managed identity).
- `STORAGE_CONTAINER`: container name, default `vrms-attachments`. Created on startup if missing (`createIfNotExists`, private).
- `STORAGE_PUBLIC_URL`: optional, the host the browser uses for links (local: `http://localhost:10000/devstoreaccount1`).
- Azure resources (storage account per environment, container, role assignment, backend app identity) belong to spec 0008's Bicep; see Follow-up.

**Critical test scenarios**
- Happy path: as the seed Mechanic at 375 px, take a photo on an assigned In progress ticket. It shrinks, uploads with progress, the thumbnail appears in the issue, the viewer zooms, and the signed link opens. Verifies AC-1, AC-2, AC-6, AC-20 to AC-24.
- Duplicate on retry: upload the same file twice. The second gets 200 `duplicate`, the count stays the same, and there's one audit row. Verifies AC-8, AC-18.
- Race on the cap: 2 parallel uploads with 4 photos present. Exactly one succeeds, the other gets 409 `PHOTO_LIMIT_REACHED`, and no orphan blob is left. Verifies AC-9, AC-14.
- Hostile files: an `.exe` renamed `.jpg` (415), a 30 MB file (413 from the gateway or the backend), a pixel bomb PNG (422), an encrypted PDF (422), and a PDF with `OpenAction` JavaScript and an embedded file (stored rebuilt; the stored copy has neither). Verifies AC-4 to AC-7, AC-14.
- HEIC: an iPhone HEIC from desktop Chrome is converted on the server and displays. Verifies AC-6, AC-22.
- Expiry: a link fetched again after 11 minutes gets 403 from storage, and the page refreshes it without the user noticing. Verifies AC-2, AC-26.
- Permissions: a Mechanic can't upload to an unassigned ticket (404), can't upload `RECEIPT` (403 `FORBIDDEN_KIND`), doesn't see a receipt in the list or activity, and can't remove a Chief's photo (403); the Chief can (`remove_any`). Verifies AC-15 to AC-17.
- Finished: upload or delete on a Closed ticket gives 409 `TICKET_FINISHED`, and the buttons are gone. Verifies AC-10, AC-21.
- No storage: unset both storage variables. The app starts, the ticket detail loads, and the attachment routes answer 503. Verifies AC-3.
- Purge: a row deleted 31 days ago loses its blob and gets `purgedAt`, and an orphan blob older than a day is removed, on one replica only. Verifies AC-19.

## Build plan

Tracer Bullet: the first slice runs one real photo through every layer (Azurite, backend, database, signed link, web). Later slices thicken the rules, phone UX, documents and retention.

1. **Thin thread, one photo end to end.**
   - Add the `azurite` service (with a volume) to `docker-compose.vrms.yml`, and set `STORAGE_*` for `vrms-backend`.
   - Write the migration for `Attachment`, the enum and all indexes, partial ones as raw SQL.
   - Build `FileStore` + `BlobFileStore` (shared key path, container creation, `readUrl`), and `POST`/`GET` for `VEHICLE_PHOTO` with JPEG and PNG through sharp (display copy + thumbnail), behind `ticket.files.add` with its catalog entry and CASL rule.
   - On the web, `useTicketAttachments` and a plain thumbnail strip in `IssuesSection` with "Choose photos".
   - Remove the `/uploads/` static route from `main.ts`.
   - Satisfies **AC-1**, **AC-2**, **AC-6** (JPEG, PNG), **AC-15** (`ticket.files.add`), **AC-20**.
2. **Upload rules.**
   - `file-sniff.ts` and the kind and type table, plus `kinds` in the GET.
   - The three settings in the `Files` group.
   - `UploadAccessGuard` before the interceptor, multer limits and the size checks, HEIC through heic-convert, sRGB and the pixel cap, the semaphores.
   - `sha256` and duplicate handling (pre check, under lock, P2002 backstop), caps under `FOR NO KEY UPDATE`, the finished and `issueId` checks in both places, the error order.
   - The user throttler on the upload route, blob cleanup on failure, the credential choice and the 503 when unconfigured.
   - Gateway `client_max_body_size 26m` and `proxy_read_timeout 120s` in `welinc-auth/nginx.conf`.
   - Satisfies **AC-3** to **AC-6**, **AC-8** to **AC-14** (with **AC-12a**, **AC-12b**).
3. **Permissions, remove and audit.**
   - `addFiles`, `addDocuments` and `removeAny` in `AppAction`, the three catalog keys and their CASL rules (`addFiles` follows `ticket.view_all`), and the matrix labels.
   - The per kind check with `ticket.costs.view` for documents, `findVisibleTicket`, and cost based visibility in the list.
   - `DELETE` with the soft delete fields and `canRemove`.
   - `ATTACHMENT_ADDED` and `ATTACHMENT_REMOVED` in `audit-events.ts`, `hideDocumentEvents` in the ticket activity and `findAuditEvents`, and their rows in spec 0010's event table.
   - Satisfies **AC-15** to **AC-18**.
4. **Phone photo UX.**
   - "Take photo" and "Choose photos" per strip and per issue, drag and drop on desktop, browser shrink, the upload queue with progress and two automatic retries, error messages from the server.
   - The lazy `yet-another-react-lightbox` viewer with Zoom and Captions, themed from tokens, with reduced motion.
   - The remove confirm and silent link refresh.
   - Satisfies **AC-21** to **AC-26**.
5. **Documents.**
   - `pdf-pipeline.ts` (checks, form flatten, rebuild without active content, page cap), `OTHER_DOCUMENT` and `RECEIPT` through the API.
   - The Documents card in `TicketSidePanel` with Add document (PDF), Open and Remove.
   - Satisfies **AC-4**, **AC-7**, **AC-27**.
6. **Retention and sweep.**
   - `attachment-purge.job.ts` with the transaction advisory lock, the 03:00 cron and the run after boot: purge after 30 days, the orphan sweep.
   - Backend unit tests for the sniff, pipelines, rules and job.
   - Web tests for the queue and shrink logic.
   - axe at 375 px and 1280 px for Admin, Chief and Mechanic.
   - Lint, typecheck and build in backend-vrms, web-vrms and the gateway config check.
   - Satisfies **AC-19**, **AC-28**.

## Consequences

**Positive**:
- Proof (feature 22) and receipts (outsourcing) add only a `kind` value and their screens. Storage, checks, links, audit and retention are done once.
- Private by default: no public bucket and no long lived links, and no account key in Azure.
- Stored files are small and clean (no GPS, no scripts), so storage and mobile data stay cheap.

**Negative / tradeoffs**:
- Six new backend dependencies (`@azure/storage-blob`, `@azure/identity`, `sharp`, `heic-convert`, `pdf-lib`, `@nestjs/throttler`) and one web dependency (`yet-another-react-lightbox`). sharp ships a native binary, so the Docker image must stay on a glibc or musl base that sharp has prebuilt binaries for.
- Processing runs on the backend's CPU and memory. A HEIC conversion takes about 1 to 3 s on 0.5 vCPU, and the semaphores (1 HEIC, 2 images) make bursts queue. A 48 MP HEIC is the memory risk and must be measured.
- pdf-lib is barely maintained. If it fails on real receipts, the pipeline is the one place to swap.
- Originals are not kept. A full resolution or EXIF timestamp question can't be answered later.
- A leaked link works for up to 10 minutes.
- PDF rebuild drops interactive form behavior and non link annotations (comments, highlights). A receipt keeps its look, but not those extras.
- The throttler counts per replica, so with 2 replicas a user could get up to 60 a minute.
- This crosses four repos: backend-vrms, web-vrms, the workspace compose file, and `welinc-auth/nginx.conf` (the shared gateway). This spec is the cross repo record the rules require.

**Neutral**:
- One new migration after the baseline. No data to migrate.
- The scope's feature 21 is folded into this feature. Feature 22 builds on `PROOF` and adds move M4's `proof` need.
- The Settings page grows a `Files` group with three numbers.

## Follow-up

- [ ] Spec 0008 (hosting, not built yet): add one Standard LRS storage account per environment (public network on, blob public access off, minimum TLS 1.2), the `vrms-attachments` container, a system assigned identity on the backend Container App with "Storage Blob Data Contributor" on that account, `STORAGE_ACCOUNT_URL` and `STORAGE_CONTAINER` as app settings, and the gateway's `client_max_body_size 26m` in its nginx template.
- [x] Install `microsoftdocs/agent-skills@azure-blob-storage` (done 2026-11-01, in `.agents/skills/azure-blob-storage/`, linked into `.claude/skills/`).
- [ ] Record it in root `AGENTS.md` `## Agent skills` as ask first with the other Azure skills, and record `microsoft/azure-skills@azure-storage` and `mn-youssef/security-skills@file-upload-and-ssrf` as declined (/sync owns `AGENTS.md`).
- [ ] Azure MCP server (`@azure/mcp`, Storage tools): not connected, noted for later. Useful to inspect staging blobs during `/check verify` once hosting exists.
- [ ] backend-vrms `AGENTS.md` gains an attachments line (FileStore seam, only `blob-file-store.ts` talks to Azure, processing rules, Azurite and `STORAGE_PUBLIC_URL`) via /sync.
- [ ] Feature 22 (proof): decide whether proof gets a count cap, and add `proof` to move M4's needs.
- [ ] Outsourcing (WL-402): add `outsourcedJobId` to `Attachment` with that feature's migration, and the receipt upload in its close dialog.
- [ ] Offline feature: persist this upload queue (IndexedDB) so uploads survive leaving the page, and reconsider background retry.
- [ ] When the SPA host (Static Web Apps, spec 0008) gets a Content Security Policy, `img-src` must allow the storage account host.
- [ ] Auth's profile pictures still live on an Azure Files mount (spec 0008). Moving them onto this store is a separate decision in welinc-auth.
