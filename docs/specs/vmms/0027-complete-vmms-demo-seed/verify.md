# Verify: Complete VMMS development seed

Steps derived from the acceptance criteria in [index.md](index.md).

## Repeatability and fixture refresh

- [ ] Run the seed twice against an empty disposable development
      database; verify stable fixture IDs and no duplicates → AC-1, AC-2
      Evidence: both runs exited successfully inside `welinc_vmms_backend`.
      The follow-up query found 15 deterministic schedule fixtures, six
      recurrence rows, four fuel fill-ups and four fill-up audit rows, with no
      duplicate pending schedule keys. The database was later found to contain
      manual integration fixtures, so the empty-database condition was not met.
      Before the latest seed rerun, all six integration models were snapshotted;
      their counts, IDs, and full-row hashes were unchanged afterward. This
      verifies those protected records. Counts across all 38 Prisma models also
      matched before and after the latest rerun. The clean-database condition
      and full initial-population check remain outstanding.
- [x] Change a mutable fixture row with a deterministic seed ID, rerun the
      seed, and verify that row returns to the defined fixture values → AC-2, AC-3
      Evidence: the TGD 908 Engine Tune-up title, cost, dates, and progress JSON
      were mutated, then restored by the seed.
- [x] Edit a seeded completed schedule's scalar fields and `workOrderProgress`,
      rerun the seed, and verify fixture values and recurrence dates refresh while
      generated work-order/log numbers remain stable → AC-2, AC-4, AC-5
      Evidence: the work-order number and log number were unchanged; the
      completion timestamp matched the restored progress timestamp, and the
      recurrence remained pending with start/due dates matching the refreshed
      completion date and interval.
- [x] Snapshot unrelated records, append-only audit rows, and singleton
      configuration other than the two demo thresholds; run the seed and verify
      those values remain unchanged → AC-3, AC-7
      Evidence: audit tables, DirectorySyncState, VehicleMaintenanceDefault,
      and an unrelated FuelStation probe were unchanged after reseeding.
- [x] Snapshot the six manual VRMS/BMS integration models before a seed rerun
      and verify their rows remain unchanged → AC-3, AC-7
      Evidence: counts, IDs, and SHA-256 hashes of complete rows matched for
      VrmsRepairIntegrationState (1), VrmsRepairEventReceipt (3),
      VmmsRepairReferral (2), VrmsRepairReferralEventReceipt (1),
      BmsVehicleAvailabilityEvent (6), and BmsFleetChangeEvent (6). The seed
      source contains no references to these Prisma delegates.
- [x] Snapshot append-only audit and workflow-history rows before a seed rerun
      and verify their values remain unchanged → AC-7
      Evidence: counts and full-row hashes matched across nine models:
      FuelAnomalyThresholdAudit, FuelAuditLog,
      MaintenanceCostingThresholdAudit, MaintenanceCostingExportAudit,
      VehicleAuditLog, MaintenanceScheduleCancellation,
      MaintenanceScheduleExtensionAudit, MaintenanceScheduleRescheduleAudit,
      and MaintenanceLogEditAudit.
- [ ] Verify existing manual-upload metadata and links remain unchanged
      → AC-3, AC-8
      Evidence: both attachment metadata tables were empty before and after;
      preservation of uploaded metadata was not exercised.
- [x] Change both global thresholds, run the seed, and verify values reset to
      20% and PHP 4,000 with correctly attributed audit entries showing the actual
      previous/new values; run it again and verify no extra threshold audit rows
      are added when values already match → AC-3, AC-9
      Evidence: changing the thresholds to 37.5% and PHP 5,500 produced the
      expected reset values and one audit row per setting with the prior values;
      a second unchanged seed run added no threshold audit rows.
- [ ] Verify the Admin Settings catalog displays those values and non-Admin
      access remains restricted → AC-9
      Evidence: no authenticated browser session was available; direct navigation
      redirected to portal sign-in with LOGIN_FAILED. Neither role was verified.
- [ ] Verify a non-seed row conflicting with a seed fixture's natural unique
      key surfaces an error instead of being adopted or overwritten → AC-3
- [ ] Verify duplicate pending schedule keys are reported and skipped without
      changing the existing schedule → AC-3, AC-5

## Model and relationship coverage

- [x] Static inventory confirms seed delegates for all 30 in-scope models.
      Six VRMS/BMS integration models are excluded for manual testing, and two
      attachment models require upload. This does not verify persisted rows or
      foreign-key consistency → AC-1
- [x] Query the 30 seed-owned models and six manually tested integration models
      for persisted rows → AC-1
      Evidence: all 30 seed-owned models had rows; the six integration models
      had their existing manual-test rows. Both attachment models were empty,
      as expected before authorized uploads.
- [ ] Verify both attachment models after manual upload
      → AC-1, AC-8
- [x] Validate seeded foreign keys and logical links: vehicle plates, garage
      assignments, active mechanic/person identities, checklist templates,
      schedule progress, recurrence, fuel station/vehicle, and anomaly/fill-up
      → AC-4
      Evidence: all 33 database foreign-key constraints were validated.
      Across 21 schedules there were no missing vehicle, garage, mechanic,
      chief-mechanic, checklist, or provider links; completed work-order
      progress matched completion timestamps and service odometers; and all six
      recurrence links resolved to completed predecessors for the same vehicle
      and maintenance type. The four demo fill-ups linked to TGD 908 and the
      demo station; the anomaly linked to the final fill-up.
- [x] Verify maintenance status, trigger, odometer bounds, recurrence,
      outsourced provider, and pending-key constraints → AC-5
      Evidence: all 21 schedules had valid trigger fields; no negative
      odometers, start references ahead of the vehicle master odometer, invalid
      recurrences, or duplicate pending vehicle/title keys were found. All
      completed schedules were verified and the outsourced fixture resolved to
      an active provider.
- [x] Verify fuel history ordering, cost arithmetic, full-tank anomaly linkage,
      and anomaly detection against the persisted 20% setting → AC-6, AC-9
      Evidence: the four TGD 908 demo fill-ups were chronological by date and
      odometer (88,000–91,000 km), were full-tank/non-voided, and each total
      matched liters × PHP 60.50. The 2.5 km/L anomaly linked to the 400 L
      fill-up and was below the 10 km/L rolling average at the persisted 20%
      threshold. A separate master-odometer ownership action was not exercised.
- [x] Verify the current-month TGD 908 Engine Tune-up is completed, verified,
      costs PHP 4,400, and exceeds the PHP 4,000 threshold → AC-5, AC-9
      Evidence: the persisted schedule meets those eligibility and value
      conditions for the current month.
- [ ] Verify the costing dashboard displays and flags that fixture → AC-5, AC-9
      Evidence: authenticated dashboard access was unavailable.
- [x] Verify scheduled report snapshots match current fixture source data
      → AC-2, AC-6
      Evidence: current daily operations metrics and the October 2026 monthly
      costs report matched recomputed source counts and totals. Mutating the
      deterministic current-day report row and rerunning the full seed restored
      its source-derived values.

## Audits, integrations, and attachments

- [x] Verify synthetic append-only audit rows insert once and are never
      updated or deleted → AC-7
      Evidence: nine audit/workflow-history model counts and full-row hashes
      were unchanged across a seed rerun; repeated seed runs added no rows to
      these tables.
- [x] Verify this seed creates no VRMS/BMS integration or outbox rows → AC-7
      Evidence: all six integration models had identical counts, IDs, and
      full-row hashes before and after the seed rerun; the seed source does not
      reference their Prisma delegates.
- [ ] Run the seed with external services unavailable and verify it performs
      no network calls or blob writes → AC-7, AC-8
      Evidence: seed source inspection found no network or blob-storage calls;
      the unavailable-service runtime check was not run.
- [x] Supply a clearly marked synthetic receipt PNG for the manual upload
      workflow → AC-8
- [ ] Manually upload the [synthetic receipt PNG](synthetic-demo-fuel-receipt.png)
      through the authorized fuel receipt and anomaly attachment flows; verify
      each stored object can be downloaded through the application and both
      metadata rows reference the correct parent → AC-8

## Commands and runtime

- [x] `npm run build` passed, including Prisma Client generation and NestJS
      compilation. This validates types/compilation only; it is not database
      relationship or repeatability evidence.
- [x] Run the seed in `welinc_vmms_backend`; it exited successfully on the
      latest rerun. All 38 model counts and all nine audit/workflow-history
      snapshots remained unchanged.
- [ ] Run the full seed twice against an empty disposable development database.
      Evidence: two runs exited successfully, but the tested database contained
      manual integration fixtures; repeatability on a confirmed empty database
      remains outstanding.
- [x] Complete the database-level fixture-refresh, relationship, and
      protected-data checks above, excluding manual-upload metadata.
- [ ] Complete the manual upload and download checks above.
- [ ] Do not run full-seed verification against production or a database whose
      data must be retained.

## Acceptance-criteria coverage

- AC-1–3: model coverage, repeatability, and seed-owned fixture refresh.
- AC-4–6: relational, lifecycle, and business-data consistency.
- AC-7–8: audit/integration safety and manual attachment persistence.
