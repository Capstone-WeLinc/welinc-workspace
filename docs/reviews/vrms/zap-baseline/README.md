# OWASP ZAP baseline reports (staging)

Passive ZAP baseline scans of the shared portal, VRMS web and the gateway, from the workspace workflow `.github/workflows/zap.yml` (scope feature 69). Open `report_html.html` in any folder for the full report.

| Folder | Run | What it shows |
|---|---|---|
| `2026-11-20/` | [44694186158](https://github.com/Capstone-WeLinc/welinc-workspace/actions/runs/44694186158) | First scan, before the fixes |
| `2026-11-22/` | [45080442690](https://github.com/Capstone-WeLinc/welinc-workspace/actions/runs/45080442690) | Weekly scan after the fixes (web-vrms #80, portal #43, workspace #82) |
| `2026-11-26/` | [45656546174](https://github.com/Capstone-WeLinc/welinc-workspace/actions/runs/45656546174) | Re-scan: same alerts as Nov 22, nothing new |

## Alert counts (distinct alert types)

| Site | Nov 20: High / Med / Low / Info | Nov 22 and Nov 26: High / Med / Low / Info |
|---|---|---|
| Portal (`staging-portal.welinc.app`) | 0 / 4 / 6 / 4 | 0 / 1 / 1 / 4 |
| VRMS web (`staging-vrms.welinc.app`) | 0 / 4 / 7 / 5 | 0 / 1 / 2 / 5 |
| Gateway (`staging-api.welinc.app/health`) | 0 / 0 / 2 / 2 | 0 / 0 / 1 / 2 |

## Fixed after the first scan

- **CSP header not set, and CSP directives with no fallback (Medium):** Azure's default error page answered missing files. The apps now answer their own 404s, and the CSP gained `form-action`, `base-uri` and `object-src`.
- **Sub Resource Integrity missing (Medium) and cross-domain script inclusion (Low):** both came from that default error page loading jQuery and Bootstrap from a CDN. Gone with the 404 fix.
- **HSTS, Permissions-Policy, COOP and CORP missing (Low), web apps:** added to `staticwebapp.config.json`.
- **`X-Content-Type-Options` missing (Low), gateway:** the gateway now sends `nosniff` on every response.

## Still reported, accepted

These are accepted risks. The reasons are in `infra/RUNBOOK.md`, *Security grades*:

- `CSP: style-src 'unsafe-inline'` (Medium)
- No `Cross-Origin-Embedder-Policy` (Low)
- No `Cross-Origin-Resource-Policy` on the API (Low)
- `Timestamp Disclosure` (Low)
- The Informational items
