# CareBridge Phase 4 – Integration Review

## API contract mapping

| React client path | Django endpoint | Main operations |
|---|---|---|
| `/auth/token/` | `CareBridgeTokenObtainPairView` | Email/password login; returns access, refresh and user |
| `/auth/token/refresh/` | SimpleJWT `TokenRefreshView` | Rotates refresh token and returns new access token |
| `/auth/me/` | `MeView` | Read/update profile; POST changes password |
| `/dashboard/summary/` | `DashboardSummaryView` | Role-aware dashboard analytics |
| `/patients/` | `PatientViewSet` | Patient list/create/retrieve/update/delete (role-scoped) |
| `/doctors/` | `DoctorViewSet` | Doctor list/create/retrieve/update/delete (role-scoped) |
| `/availabilities/` | `DoctorAvailabilityViewSet` | Doctor weekly availability |
| `/appointments/` | `AppointmentViewSet` | Booking, list, retrieve, status update, delete, today action |
| `/prescriptions/` | `PrescriptionViewSet` | Prescription and nested medicine records |
| `/invoices/` | `InvoiceViewSet` | Invoice create/list/retrieve/update/delete with nested items |
| `/payments/` | `PaymentViewSet` | Payment list and record payment |

All paths above are mounted beneath `/api`.

## Corrections made in Phase 4

- Declared and loaded doctor records in the billing page before using the selected appointment's consultation fee.
- Imported the shared `Badge` component in the profile page to avoid a runtime `ReferenceError`.
- Corrected weekday mapping from JavaScript's Sunday-based index to Django's Monday=0 through Sunday=6 convention.
- Moved availability-slot generation into a small utility and added tests for weekdays, occupied intervals and cancelled visits.
- The booking dialog now fetches the selected doctor's appointments for the selected date independently of table search/status filters, so hidden rows do not make a booked slot appear free.
- Updated the Axios list helper to follow Django REST Framework pagination links instead of silently dropping records after the first page.
- Kept the JWT refresh request single-flight so concurrent 401 responses share one refresh operation; retry requests now safely initialize headers.
- Account name edits now synchronize the linked Patient/Doctor directory name.
- Appointment time/date/doctor edits and reactivation of a cancelled booking now re-check availability and interval conflicts on the backend, not just in the UI.
- Added backend API regression tests for appointment edits and cancelled-slot reactivation conflicts.

## Role-to-API behavior

- **Admin:** broad access to patient, doctor, appointment, prescription and billing operations.
- **Receptionist:** patient/doctor administration, appointment management and invoice/payment management; prescription and medical records are read-only.
- **Doctor:** only own appointments and prescriptions, patients connected through appointments, own doctor profile and related invoices/payments; can complete own appointments and write prescriptions under the linked profile.
- **Patient:** only own patient record, appointments, prescriptions, invoices and payments; can book and cancel their own upcoming appointments; can browse active doctors and availability.

The backend queryset filters and permission checks remain the security boundary. Frontend route guards/navigation are only a user-experience layer.

## Verification performed in this workspace

- Python source compilation (`python -m compileall -q backend`): passed.
- JavaScript source checks with Node for non-JSX modules: passed.
- Frontend local relative-import existence scan: passed.
- Frontend stack dependency declaration check: passed.
- Node syntax checks for standalone JavaScript modules: passed.
- TypeScript compiler API parsed/transpiled all 16 JSX source files for syntax: passed (this is not a Vite production build).
- Scheduling utility runtime assertions with Node: 3 assertions passed.
- Included automated tests: 20 Django API tests and 7 Vitest cases; neither full suite could run here.
- Django management check, migrations and DRF API tests: **not run** because Django/DRF packages are absent. `python manage.py check` was attempted and stopped with `ModuleNotFoundError: No module named 'django'`.
- Vite production build and Vitest suite: **not run** because `npm install` timed out and `node_modules` is absent. `npm run build` and `npm test` were attempted and stopped with `vite: not found` / `vitest: not found`.
- Browser/API end-to-end testing and screenshots: **not run**. No screenshots are represented as captured.

## Local verification commands (Windows 11)

Backend terminal:

```bat
cd backend
venv\Scripts\activate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
python manage.py runserver
```

Frontend terminal:

```bat
cd frontend
npm install
npm run test
npm run build
npm run dev
```

The frontend base API URL is configured in `frontend/.env` via `VITE_API_BASE_URL`; the default is `http://127.0.0.1:8000/api`.
