# Verify: hosting & CI/CD · spec 0008 · updated 2026-10-26
_Steps derived from spec 0008 acceptance criteria. `/check verify` runs these; `/test` locks the durable ones. Only the CI milestone (AC-1, AC-2, AC-11) is written so far; `/develop` adds the steps for each later milestone when it lands._

## UI / manual
- [ ] Open a pull request into `development` in each of web-vrms, web-portal, backend-vrms, auth and analytics-ai → a check named `CI / ci` appears on the PR and finishes green → AC-1
- [ ] On a throwaway PR in backend-vrms, add an unused variable to any `src` file → the `CI / ci` check goes red at the lint step and the PR shows a failed check → AC-2
- [ ] On a throwaway PR in auth, make an existing test fail (for example change an expected value in `app.controller.spec.ts`) → the check goes red at the test step → AC-2
- [ ] In a CI run log for a Node repo, open the setup-node step → it reports Node 24 (from `.nvmrc`) → AC-1
- [ ] Push a second commit to the same open PR quickly → the older run is cancelled and only the newest run finishes → AC-1
- [ ] Merge a PR into `development` → a run starts for the push on `development` and finishes green → AC-1

## Commands
- [ ] `npm run lint:ci` in `welinc-backend-vrms` and `welinc-auth`, then `git status --short` → lint exits 0 and no file changed (it must not fix files) → AC-1, AC-2
- [ ] In a clean clone of each Node repo on Node 24: the commands in its `ci.yml` run in order and all exit 0 → AC-1, AC-2
- [ ] `python -m py_compile $(git ls-files '*.py')` in `welinc-backend-vrms-analytics-ai` → exits 0 → AC-1
- [ ] Open each `.github/workflows/ci.yml` → it contains `permissions:` with only `contents: read` and no secrets are referenced → AC-11

## Acceptance-criteria coverage
- AC-1 … covered by steps 1, 4, 5, 6 and the first, second and third commands · AC-2 … covered by steps 2, 3 and the first two commands · AC-11 … covered by the last command (the OpenID login part comes with the Azure milestones)
- AC-3 to AC-10, AC-12 to AC-14 … not written yet, they belong to later milestones
