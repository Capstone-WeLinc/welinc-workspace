# 0017. File upload and storage: rationale

The decision record for [index.md](index.md). `/develop` builds from the index; this file explains why.

## Context

Three Jira stories need files on a repair ticket: vehicle photos (WL-209, WL-210), proof of completion (WL-211) and outsourced receipts (WL-402). WL-218 asks for one service with the same rules for all of them: JPG, PNG, HEIC and PDF, a configurable size (default 10 MB), private files opened only through signed or authorized links, and a record of ticket, kind, uploader and time. QA's security tests (VRMS-291, VRMS-294) will try wrong types, oversized files and renamed executables. The team added a fourth kind, other documents (PDF only), for office paperwork Jira doesn't name.

The forces:
- **Hosting.** Production runs on Azure Container Apps (spec 0008): scale to zero, at most 2 replicas, 0.5 vCPU each. A container's disk is lost on every restart and isn't shared between replicas. Nothing is deployed yet, so the storage resource can join spec 0008's Bicep before first deploy.
- **Browser auth.** The SPA keeps its bearer token in `localStorage` and sends it as a header. A plain `<img src>` can't carry it, so images need either a link that needs no header or a fetch to blob URL dance.
- **Users.** Mechanics work on phones, often on weak mobile data, and iPhones shoot HEIC, which desktop Chrome, Edge and Firefox can't display.
- **Cost data.** Receipts show costs, and mechanics must never see cost data (BRD, roles-and-users).
- **What exists.** Spec 0010 already designed the `Attachment` table and left "where the bytes live" to this feature. backend-vrms has an unused public `/uploads/` static route with a one day public cache, and the gateway sets no body size (nginx's 1 MB default).
- **Approach and scope.** The project builds Tracer Bullet, and GA level care applies to uploads (scope index). The team folded vehicle photos (feature 21) into this feature, so the first real consumer ships with the service.

## Options considered

### Option 1: Azure Blob Storage, processed in the backend, user delegation SAS links (chosen)

A private Blob container per environment, Azurite locally. Uploads go through backend-vrms, which checks and processes them, then writes. Reads are short lived signed links.

**Pros**:
- Object storage is the normal home for user files: cheap, durable, shared by every replica, and survives restarts.
- SAS links let `<img src>` work, and the bytes skip the backend and gateway on every view.
- Managed identity signing means no storage key in secrets. Azurite runs the same SDK path locally.

**Cons**:
- A new Azure resource, new SDKs and a native image library to operate.
- A link copied in its 10 minute window works for anyone holding it.

### Option 2: Azure Files share mounted into backend-vrms, backend streams every file

Mount a share at a path, like auth's profile pictures, and serve files from a guarded `GET .../content` that the SPA fetches with its token and turns into a blob URL.

**Pros**:
- No storage SDK. Every view is checked and could be logged.
- Revoking access works at once.

**Cons**:
- Every image passes through 2 small replicas and the gateway.
- SMB mounts are slow for many small reads, and the SPA needs blob URL plumbing for every thumbnail.

### Option 3: PostgreSQL `bytea`

Store the bytes in the database next to the row.

**Pros**:
- One backup and one transaction cover file and row. No new service.

**Cons**:
- Bloats the Burstable server and its backups.
- Every image view holds one of 5 pooled connections (`DB_POOL_MAX`).
- Still needs the streaming plumbing of Option 2.

### Option 4: Direct to Blob uploads with a write SAS, then confirm

Same storage as Option 1, but the phone uploads straight to Blob with a write link, then calls the backend to confirm and process.

**Pros**:
- Upload bytes skip the backend and gateway.

**Cons**:
- Unvalidated bytes land in storage first and need a quarantine and cleanup path.
- The storage account needs CORS.
- The backend must still download each file to sniff, convert and shrink it, so the bandwidth saving mostly disappears.

## Rationale

Container disks don't survive restarts and aren't shared, so the bytes need a shared store. Among the shared stores, only Blob gives signed links, and signed links are what make `<img src>` work with a header based token. Option 2's per view control is what a bank statement needs, not a truck photo. Its cost (every thumbnail through two 0.5 vCPU replicas) lands exactly where this project is weakest. Option 3 puts image traffic on the scarcest resource, the 5 connection pool.

The team chose uploads through the backend (over Option 4) because every upload must be sniffed, converted, shrunk or rebuilt anyway. Doing it before anything is stored means no quarantine state and one place for every rule. 10 MB (at most 25) in memory is small, and a 3 slot semaphore bounds memory per replica.

Smaller calls, each made with the team:
- **HEIC: the phone first, the server as fallback.** iPhone Safari sends JPEG when the input asks for `image/*`. The server converts whatever still arrives as HEIC with `heic-convert`, because sharp's prebuilt binaries can't decode HEVC. Browser side conversion (heic2any) was rejected as heavy and slow on cheap phones.
- **Normalized copies only.** Re-encoding strips GPS and hidden payloads, and saves storage and data. The team accepted losing full resolution originals.
- **PDF disarm and rebuild over antivirus.** ClamAV needs about 2 GB of RAM with a slow cold start on scale to zero, and Defender for Storage costs about USD 10 per account per month. Both catch only known malware. Copying pages into a fresh document without scripts, actions or embedded files removes the main PDF attack paths, known or not, for free.
- **Short links.** 10 minutes over 2 (fewer refreshes for a slow phone in the viewer), with silent refresh on stale data or the first load error.
- **sharp** over jimp (several times slower and heavier on 12 MP photos), `@napi-rs/image` (smaller community) and ImageMagick (process per image, a history of untrusted input bugs).
- **The lightbox** over a hand built Dialog. Reviewers zoom into damage on phones, and swipe plus pinch zoom inside the viewer is that job. It's lazy loaded, so the ticket page doesn't pay for it.
- **Magic bytes by hand** over the `file-type` package: four signatures, no dependency, and no ESM only import in a CommonJS Nest build.
- **Keys by audience, not topic.** Work files (photos, proof) are visible to everyone on the ticket. Documents (receipts, other) sit behind `ticket.costs.view`, because the uploader can't be trusted to tell a parts invoice from a warranty card.
- **`ticket.files.add` follows visibility** ("add where you can see") instead of a `ticket.work` / `ticket.administer` style pair (`add` mine plus `add_any`). That's one matrix row instead of two, and no odd combinations. The cost is that the key's reach changes when `ticket.view_all` is granted, which the key's description states.
- **Cross check.** An independent read by another model found 22 gaps and 8 soundness issues in the first draft. The main ones: the CASL shape, multer reading the body before the access check, the error order (a duplicate retry at the cap), receipt events leaking through `/vrms/audit`, the delegation key window, the session advisory lock, and the cron under scale to zero. All were fixed in the spec.
- **Soft delete with a 30 day purge** keeps spec 0010's rule that audit rows can point at a file, while the bytes really go away. The usual objection to soft deletes (polluted queries, broken unique constraints) is handled by the partial unique index and by every query filtering live rows in one service.
- **Retries.** Two automatic retries, then a button. The team kept the persistent background queue for the offline feature, which owns surviving a closed app.
