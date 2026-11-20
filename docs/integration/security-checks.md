# Security checks (ZAP, headers, secrets)

How the suite checks itself for security weaknesses, where each group reads its results, and what VMMS and BMS can copy so their reports come back as clean as VRMS's. Nothing here blocks your work. It gives you findings to fix before the panel finds them, and evidence for your paper.

The VRMS side is scope feature 69 (`docs/scope/vrms/platform.md`). This page is the short version for every group.

## What runs, and where you see it

| Check | What it looks at | When | Where the results are |
|---|---|---|---|
| **OWASP ZAP baseline** | Your web app on staging, from the outside | Mondays 02:00 Philippine time, and on demand | Workspace repo → Actions → ZAP baseline → a run → Artifacts (`zap-vmms`, `zap-bms`, …) |
| **GitHub secret scanning with push protection** | Every push to your repos | Always (while the repos are public, until Dec 5) | Your repo → Security → Secret scanning |
| **gitleaks** (optional for you) | A pull request's commits | Every PR | The PR's checks |

## The ZAP scan

[OWASP ZAP](https://www.zaproxy.org/) is the standard free tool for testing a running website for security weaknesses. The **baseline** scan is passive: it crawls your site for a couple of minutes and only reads what comes back (headers, cookies, leaked versions, content loaded from other sites). It sends no attacks, so it's safe against staging any time.

It runs from the workspace (`.github/workflows/zap.yml`) against five sites: the portal, the gateway, and each system's web app. You don't need to set anything up. Your report is already there every Monday.

**Reading your report:** download your zip from the run's Artifacts and open `report_html.html` in a browser. A quick look without downloading: open your job (`baseline (vmms)` or `baseline (bms)`) and read the last lines of its log. Findings come as High, Medium, Low and Informational. Fix High and Medium. Fix Low when it's one line. Informational is usually noise.

**Run it yourself:** Actions → ZAP baseline → Run workflow. Do it after you change your headers, to see the result straight away.

> **Right now your report describes Azure's placeholder page, not your app.** Until your `deploy.yml` publishes your build to your Static Web App, `staging-vmms.welinc.app` and `staging-bms.welinc.app` serve an empty page with no headers. So ignore your report until your first staging deploy. (`hosting.md` has the hosting ready list.)

## Fix most findings with one file

Your web app's headers come from `public/staticwebapp.config.json`. You both already have a good start in `development`. Add these to match what fixed VRMS's and the portal's reports (web-vrms #80, portal #43):

```json
{
  "responseOverrides": {
    "404": { "rewrite": "/index.html", "statusCode": 404 }
  },
  "globalHeaders": {
    "Content-Security-Policy": "<yours> ; object-src 'none'; base-uri 'self'; form-action 'self'",
    "Strict-Transport-Security": "max-age=31536000",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin"
  }
}
```

- **`responseOverrides` (most of the Medium findings):** without it, a missing file like `/robots.txt` gets Azure's own error page, which loads jQuery and Bootstrap from Microsoft's CDN with none of your headers. With it, your app answers its own 404s.
- **The CSP additions:** `form-action`, `base-uri` and `object-src` don't fall back to `default-src`, so ZAP flags them when they're missing. BMS already has `object-src` and `base-uri`; VMMS has neither.
- **Keep your own CSP allowances.** BMS loads Google Maps and Google Fonts, so keep its `maps.googleapis.com`, `maps.gstatic.com`, `fonts.googleapis.com` and `fonts.gstatic.com` entries. After any CSP change, open your app with the browser console open: a blocked resource shows as a CSP error there.
- **`Permissions-Policy`:** if your app asks for the user's location, camera or microphone, change that entry from `()` to `(self)`, or the browser will refuse.
- **Leave out `Cross-Origin-Embedder-Policy`.** It blocks images from blob storage unless the storage sends extra headers.

## Findings we accept on purpose

These stay in every report, VRMS's included. Write them in your paper as accepted risks, with the reason:

- **`CSP: style-src unsafe-inline` (Medium):** React libraries and toast popups add inline styles. Removing it needs a fresh nonce for each request, which a static host can't produce. This is the usual tradeoff for single page apps on static hosting.
- **`Cross-Origin-Embedder-Policy` missing (Low):** see above.
- **`Timestamp Disclosure` (Low) and the Informational items:** numbers and comments inside your built JavaScript. Not a real leak.

## Your API

Once your backend is on staging, the gateway already sets HSTS and `X-Content-Type-Options` on every answer it passes through (workspace #82), so you don't need to add those to NestJS. Tell the lead when your API is live, and its health route gets added to the scan.

## Secrets

- **Push protection** is on in all 12 public repos: GitHub refuses a push that contains a known key format and tells you why. If it stops you, remove the secret from the commit; don't click "allow" unless the value is a public test value.
- **gitleaks (optional):** VRMS runs `.github/workflows/secrets.yml` on every PR (copy it from `welinc-backend-vrms`). It catches more formats than GitHub does, and it keeps working after the repos go private again on Dec 5, when push protection stops.
- If a real secret ever reaches a commit: rotate it first, then remove it.

## Check your grades (optional)

Two free graders give you a letter grade to quote:

- **Mozilla Observatory** (https://developer.mozilla.org/en-US/observatory): enter your staging address. It grades your headers.
- **SSL Labs** (https://www.ssllabs.com/ssltest/): enter your staging address. It grades your HTTPS setup (Azure manages the certificate).

## What to send the lead

After your first staging deploy and a ZAP run: your report's High and Medium counts, and anything you decided to accept with its reason. That goes in the suite's security summary for the defense.
