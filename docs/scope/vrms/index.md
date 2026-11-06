# Scope: WeLinc VRMS

VRMS (Vehicle Repair Management System) lets WeLinc Logistics log, assign, track, verify and cost truck repairs across its three garages. Admin and office staff use it on laptops; mechanics use it on phones. Seeded from Jira project `VRMS` (epics WL-E1 to WL-E11) on 2026-10-22; Jira wins when it disagrees with this file. Part of the [suite scope map](../index.md).

**Build approach:** Tracer Bullet (each feature built end to end through every layer and working before the next; later slices thicken one strand at a time). The UI refresh phase overrides this with `· Facade`: build the UI first on the data it already has. (basis: vertical slices ship real value early; your 5 weeks to deployment)
**Workflow:** Beta (after `/develop`: `/check verify`, then `/test`). The project default level of rigor. `/architect` is the recommended first stop for a feature with a real decision, but skippable when you already know the build. Any feature can carry its own tag (e.g. `· GA`) to do more or less.

_These are recommendations to keep your build orderly, not requirements. Skip anything that does not fit: if you already know how to build a feature, use `/develop` and skip `/architect`. You decide when a feature is `done`._

**Deadline:** deployed by the end of November 2026, about 5 weeks from this plan. The whole plan is in scope; nothing is set aside for trimming. Documentation and QA tasks (WL-E10, WL-E11) stay in Jira, not here.

**Integration:** the meeting with VMMS and BMS is planned for after the first week of November 2026 (features 55 and 56). Work tagged "feature 56 may change it" is safe to build before then, but expect changes after.

## Epics

| Epic | File | Status |
|---|---|---|
| Foundations | [foundations.md](foundations.md) | 8 existing, 7 done, 1 planned |
| UI refresh | [ui-refresh.md](ui-refresh.md) | 3 done, 6 in-progress, 3 planned |
| Repair workflow | [repair-workflow.md](repair-workflow.md) | 12 done, 1 in-progress, 7 planned, 1 dropped |
| Platform | [platform.md](platform.md) | 2 in-progress, 8 planned |
| Outsourcing | [outsourcing.md](outsourcing.md) | 4 planned |
| Operations | [operations.md](operations.md) | 5 planned, 1 dropped |
| Reports & AI | [reports-ai.md](reports-ai.md) | 4 planned |

## At a glance

| # | Feature | Phase | Status |
|---|---------|-------|--------|
| A | Login, OTP and password reset | Built | existing |
| B | User management | Built | existing |
| C | Repair tickets | Built | existing |
| D | Repair history | Built | existing |
| E | Audit log page | Built | existing |
| F | Dashboard | Built | existing |
| G | AI diagnosis and knowledge base | Built | existing |
| H | Analytics dashboards | Built | existing |
| 1 | Coding standards & tooling | Foundation | done |
| 2 | Auth service boundary | Foundation | done |
| 3 | Analytics & AI service boundary | Foundation | done |
| 4 | Data model v2 | Foundation | done |
| 5 | Permission matrix & enforcement | Foundation | done |
| 6 | Design system & UI foundation | Foundation | done |
| 7 | Language support (English + Filipino) | Foundation | planned |
| 52 | Configurable settings & modules | Foundation | done |
| 55 | Integration kickoff prep | Integration | in-progress |
| 60 | Portal system picker for shared accounts | Integration | planned |
| 56 | Cross group integration contract | Integration | planned |
| 61 | Suite admin model | Integration | planned |
| 8 | App shell & role badge | UI refresh | done |
| 9 | Login & profile pages | UI refresh | done |
| 10 | Dashboard | UI refresh | in-progress |
| 11 | Repair list & detail | UI refresh | in-progress |
| 12 | Repair form | UI refresh | in-progress |
| 13 | History & audit log pages | UI refresh | done |
| 14 | User management page | UI refresh | in-progress |
| 15 | Knowledge base page | UI refresh | in-progress |
| 50 | Portal on the design system | UI refresh | planned |
| 51 | Analytics page | UI refresh | planned |
| 64 | Audit log page redesign | UI refresh | planned |
| 65 | Ticket detail redesign | UI refresh | in-progress |
| 16 | Ticket status lifecycle | Slice 1 | done |
| 17 | Chief Mechanic role | Slice 1 | done |
| 18 | New repair ticket & assignment | Slice 1 | done |
| 53 | Admin ticket editing | Slice 1 | done |
| 19 | Mechanic status updates | Slice 1 | done |
| 20 | File upload & storage | Slice 1 | done |
| 21 | Vehicle photos | Slice 1 | dropped |
| 22 | Proof of completion | Slice 1 | done |
| 23 | Chief Mechanic verification | Slice 1 | done |
| 24 | Full ticket audit trail | Slice 1 | done |
| 25 | Vehicle availability | Slice 1 | done |
| 57 | Mechanic workload on the Users page | Slice 1 | done |
| 58 | Per ticket checklist edits | Slice 1 | in-progress |
| 63 | Chief dashboard rework with a Team section | Slice 1 | done |
| 26 | Hosting, CI/CD & environments | Release | in-progress |
| 27 | Error monitoring | Release | planned |
| 28 | In-app notifications | Slice 2 | planned |
| 29 | Notification badge & queue counts | Slice 2 | planned |
| 30 | Transfer requests | Slice 2 | planned |
| 31 | On hold for parts | Slice 2 | planned |
| 32 | Repair history timeline | Slice 2 | planned |
| 33 | Admin status override | Slice 2 | planned |
| 62 | Costs after close | Slice 2 | planned |
| 34 | Admin OTP | Slice 3 | planned |
| 35 | reCAPTCHA on login | Slice 3 | planned |
| 36 | Outsourced shop directory | Slice 4 | planned |
| 37 | Transfer to outsourced shop | Slice 4 | planned |
| 38 | Close outsourced repair | Slice 4 | planned |
| 39 | Management approval for outsourced repairs | Slice 4 | planned |
| 40 | Lookup lists & fewer typed fields | Slice 5 | planned |
| 41 | Common issues picker | Slice 5 | dropped |
| 42 | Deadlines & fix time estimates | Slice 5 | planned |
| 43 | Stuck and stale ticket alerts | Slice 5 | planned |
| 44 | Driver role | Slice 5 | planned |
| 59 | Mechanic home garage | Slice 5 | planned |
| 45 | Reports module with filters & export | Slice 6 | planned |
| 46 | Ready made reports | Slice 6 | planned |
| 47 | AI repair suggestions | Slice 6 | planned |
| 54 | Account changes view | Slice 6 | planned |
| 48 | Mechanic mobile app (shared with VMMS) | Slice 7 | planned |
| 49 | Offline save & sync | Slice 7 | planned |

## Why this order

- **Foundations first.** The auth boundary, data model and permission matrix are the costliest things to redo, and every Jira story depends on them. (basis: foundations before features; data model is the costliest thing to redo; Jira dependencies on WL-109 and WL-200)
- **UI refresh right after the design system.** You asked for every page, modal and prompt to look better, and for something visible to show at the 2026-10-23 update. Restyling before Slice 1 means the new screens are built once, on the new components. (basis: your request; `design.md`)
- **Slice 1 is the walking skeleton.** It is the thinnest real path from ticket creation to verification, and it follows the stakeholder confirmed flow. (basis: walking skeleton; WL-E2 confirmed by the stakeholder)
- **Release straight after Slice 1.** Every later slice then demos from staging, and the end of November go live is not a single risky jump. (basis: Jira WL-902 planned for Sprint 3)
- **Unanswered stakeholder items are planned on Jira's proposed rules** (WL-108, WL-303, WL-403, WL-501), as you chose. Change them if WL-1101 brings different answers.
- **GA tags** mark auth, permissions and uploads, where a mistake exposes data. (basis: OWASP authorization, file upload and MFA guidance)
- **Mobile app last.** It reuses the finished API, and the responsive web covers mechanics until then. (basis: your choice; WL-801 platform decision)

## Legend

**The decision box.** Every feature carries exactly one, the sub-task whose label ends with `(spec)`. Its wording varies (`Design it (spec)` normally), so skills locate it by that `(spec)` suffix, never by an exact label. Every other box is an execution box and `/architect` never ticks one.

**Feature lifecycle**: the scope updates as a feature moves; each row is what it shows and who sets it:

| State | Set by | The feature shows |
|---|---|---|
| `planned` · needs a decision | `/scope` | one box: `Design it (spec): /architect <feature>` |
| `in-progress` (designed) | **`/architect` at spec capture** | `Design it` ticked; spec linked; `Build it: /develop <feature>` + **2 to 5 milestones**; the tier's closing boxes (`Verify it` Alpha+, `Test it` Beta+, `Review it` + `Document it` GA); any surfaced follow-up enrolled |
| `in-progress` (building) | `/develop` | milestone sub-boxes tick one by one; code pointer filled |
| `in-progress` (verified) | `/check verify` | `Build it` + milestones ticked; `Verify it` ticked |
| `done` | **you, when you decide it is** (any skill sets it when you say so); `/sync` reconciles | boxes you ran ticked, skipped ones marked skipped; the tier's last stage (`Prototype` → after `/develop`; `Alpha` → after `/check verify`; `Beta`/`GA` → after `/test`) is the suggested point to call it done; `/sync` captures conventions |

- **Next step** = the first unticked box (always a command or a tracked milestone).
- **Polish it / Extra skills** = one optional box after a feature's last pipeline box, listing the ask first skills that fit it (`impeccable` or `emil-design-eng`, never both on one change; `web-design-guidelines`; `break-ui`; `docker-patterns` and the Azure skills for hosting). It is never the next step while a pipeline box is open, and it never blocks `done`. Tick it once you ran or skipped what you wanted.
- **needs a decision** = run `/architect` first; otherwise straight to `/develop` (or `/audit` for standards & tooling). The tag drops once the spec is captured.
- **Atomic build tasks live in the spec's `## Build plan`, not here**: the scope carries only the milestone rollup.
- **Status** `planned` → `in-progress` → `done`, plus `existing` (pre-workflow) and `dropped` (de-scoped, kept for history).
- **Approach tag** beside a heading (e.g. `· Facade`) overrides the project default for that feature; no tag = inherits it.
- **Workflow tier tag** beside a heading (e.g. `· GA`) sets that one feature's rigor above or below the project default; no tag inherits the default.
- **Workflow** (header line) is the project default, what runs after `/develop`: **Prototype** = nothing; **Alpha** = `/check verify`; **Beta** = `/check verify` then `/test`; **GA** = adds a fresh model `/check review` then `/document`. A feature built on an unratified decision (an `Assumed` spec) stays flagged, but that never blocks `done`.
- **Pointer line** (`spec <n> · code in <path>`): the spec link added by `/architect`, the code path by `/develop`.
- **WL-xxx** are the Jira story IDs each feature comes from.

## References

**Project sources**
- Jira project `VRMS` (epics WL-E1 to WL-E11, 48 stories and tasks), read 2026-10-22
- Root `AGENTS.md`, `design.md`, `docs/context/vrms/` (system overview, roles, glossary)
- The code in `welinc-web-vrms`, `welinc-backend-vrms`, `welinc-backend-vrms-analytics-ai`

**Practices & standards**
- Tracer bullets and vertical slices (Hunt and Thomas)
- Walking skeleton (Alistair Cockburn)
- Foundations before features; the data model is the costliest thing to redo
- Deny by default, enforced on the server (OWASP)
- WCAG 2.2 Level AA

**Links** (web verified 2026-10-22)
- Tracer Bullets and Prototypes, Hunt and Thomas interview: https://www.artima.com/intv/tracer.html
- Start with a walking skeleton (quotes Cockburn's definition): https://www.mattblodgett.com/2020/09/start-with-walking-skeleton.html
- W3C WCAG 2.2 Recommendation: https://www.w3.org/TR/WCAG22/
- Understanding SC 1.4.3 Contrast (Minimum): https://w3c.github.io/wcag/understanding/contrast-minimum.html
- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- OWASP Multifactor Authentication Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html
- Google reCAPTCHA, verifying the user's response: https://developers.google.com/recaptcha/docs/verify
- Tailwind CSS v4 upgrade guide: https://tailwindcss.com/docs/upgrade-guide
- XState docs, state machines: https://stately.ai/docs/machines
