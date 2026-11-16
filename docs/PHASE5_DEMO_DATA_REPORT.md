# CareBridge – Phase 5 Demo Data Audit & Verification

## Scope

Reviewed the Phase 4 project source and audited `backend/accounts/management/commands/seed_demo.py`, all six domain model groups, migrations, existing API tests and demo credential documentation. No schema change was required for the seed corrections, so no migration was added.

## Findings in the original seed command

1. **Calendar-dependent duplicate appointments:** appointments were looked up using doctor + date + start time. Running the command on a later day could create a second full set of demo appointments rather than refreshing the existing records.
2. **Existing demo accounts were not repaired:** if a demo account already existed with an incorrect role, inactive state, staff flags or changed password, the command left it unchanged. This could make documented credentials or portal permissions inconsistent.
3. **Existing patient/doctor profiles were not fully reconciled:** defaults only applied on creation, so stale profile values or links could persist between runs.
4. **Invoice coverage was incomplete:** the original sample data demonstrated Unpaid and Partially Paid only; it did not reliably include a Paid invoice.
5. **Legacy payment reference could double-count:** the old `DEMO-PAY-001` reference was not reconciled when a new seed payment identifier was introduced.
6. **Seed verification coverage was missing:** the previous suite did not exercise seed counts, role/password repair, record relationships, date-shift idempotency or isolation from unrelated appointments.

## Changes applied

- Made the whole `seed_demo` command atomic.
- Added package initializers for Django management-command discovery.
- Changed demo users to upsert and repair the documented role, active/staff/superuser flags, display names and password.
- Upserted profiles by linked user first, then by demo email, repairing profile relationships and sample fields.
- Reconciled all seven weekly availability windows for each of three doctors.
- Reused seeded appointments by stable identity (demo creator + patient + doctor + scenario reason), not by the current date. Existing rows are shifted to the current demo calendar dates on rerun.
- Selected another free 30-minute slot between 09:00 and 17:00 when a non-demo appointment conflicts with a preferred demo time. Canceled appointments do not occupy a slot.
- Reconciled the prescription and its two medicine lines, removing unexpected medicine lines from that seeded prescription.
- Reconciled three invoice scenarios: **Partially Paid**, **Unpaid**, and **Paid**. Totals are recalculated from consultation fees, item lines, discounts and payments.
- Added stable payment references and cleanup for the previous `DEMO-PAY-001` payment reference. Invoice totals are recalculated after legacy payment cleanup.
- The command does not delete unrelated users or appointments. Payment cleanup is scoped to the seeded demo invoice and known demo payment references.

## Expected clean-database data

| Record | Expected count |
|---|---:|
| Demo users | 4 |
| Doctor profiles | 3 |
| Patient profiles | 5 |
| Appointments | 5 |
| Availability windows | 21 |
| Prescriptions | 1 |
| Prescription medicine lines | 2 |
| Invoices | 3 |
| Invoice items | 3 |
| Payments | 2 |

The appointments include Pending, Confirmed, Completed and Cancelled. The invoices represent Unpaid, Partially Paid and Paid. All data is fictional.

## Added automated tests

`backend/accounts/tests/test_seed_demo.py` adds six tests:

1. Creates the four documented accounts and expected data graph; validates role, staff flags, passwords, availability, appointment statuses, prescription ownership, invoice ownership and all three payment states.
2. Runs the command twice and asserts unchanged object counts and no duplicate availability, appointment or payment rows.
3. Repairs a demo account after its role and password have been changed.
4. Advances the demo calendar by ten days and verifies appointments are updated in place rather than duplicated.
5. Preserves an unrelated appointment.
6. Reconciles the legacy `DEMO-PAY-001` payment reference without double-counting and rechecks the invoice payment status.

There are now **26 Django test methods** across the backend test suite (20 existing + 6 seed tests).

## Checks executed in this build environment

| Check | Result |
|---|---|
| Python `compileall` over backend sources | Passed |
| Offline source-contract script | Passed |
| Demo seed command AST/source parsing | Passed |
| Seed test source AST parsing and test count | Passed |
| Django `manage.py test accounts.tests.test_seed_demo` | Not run: Django is not installed (`ModuleNotFoundError: No module named 'django'`) |
| `pip install -r requirements.txt` | Attempted; package-index DNS resolution failed (`Temporary failure in name resolution`), so dependencies could not be installed here |
| Full Django test suite / migrations / database execution | Not run for the same missing Django/DRF dependencies |
| Vite build and Vitest | Not run: `node_modules` is absent (`vite: not found`, `vitest: not found`) |
| Browser / API end-to-end verification | Not captured |

These are honest source-level checks, not evidence that the command has been executed against a live Django database. On Windows, install `backend/requirements.txt`, then run:

```bat
cd backend
venv\Scripts\activate
python manage.py migrate
python manage.py test accounts.tests.test_seed_demo
python manage.py test
python manage.py seed_demo
```

After the first seed run, run `python manage.py seed_demo` a second time and check that the clean-database record counts stay constant. The four demo credentials are in the root `README.md`.
