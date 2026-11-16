# CareBridge Backend

Django REST Framework API for **CareBridge – Hospital & Clinic Management System**.

## Stack

- Python 3.11
- Django 5.2
- Django REST Framework
- Simple JWT authentication
- SQLite
- django-cors-headers
- django-filter

## Windows 11 setup

Open Command Prompt or the PyCharm terminal:

```bat
cd CareBridge\backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

The backend is available at `http://127.0.0.1:8000/`.

Health check: `http://127.0.0.1:8000/api/health/`
Django admin: `http://127.0.0.1:8000/admin/`
OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

The React frontend will run separately at `http://localhost:5173/` after Phase 3. CORS is preconfigured for those local frontend origins.

## Demo accounts

Run `python manage.py seed_demo` before using these accounts. All data is fictional and intended only for local demonstration.

| Role | Email | Password |
|---|---|---|
| Admin | `admin@carebridge.demo` | `Admin@12345` |
| Receptionist | `reception@carebridge.demo` | `Reception@12345` |
| Doctor | `doctor@carebridge.demo` | `Doctor@12345` |
| Patient | `patient@carebridge.demo` | `Patient@12345` |

Change demo passwords before exposing any instance to a network. These credentials are public demo credentials, not suitable for production.

## Authentication

Obtain a token:

```http
POST /api/auth/token/
Content-Type: application/json

{
  "email": "admin@carebridge.demo",
  "password": "Admin@12345"
}
```

Use the returned access token on protected endpoints:

```http
Authorization: Bearer <access-token>
```

Refresh an access token with `POST /api/auth/token/refresh/` and `{ "refresh": "<refresh-token>" }`.

Public patient registration: `POST /api/auth/register/`. Public registration always creates a Patient account; it cannot create admin, receptionist, or doctor accounts.

`GET /api/auth/me/` returns the signed-in user's profile. `PATCH /api/auth/me/` updates first and last name. `POST /api/auth/me/` changes the password using `old_password` and `new_password`.

## API resources

All list endpoints support page-number pagination. Most resources also support `search`, `ordering`, and the listed filter fields.

| Endpoint | Purpose | Main filters |
|---|---|---|
| `/api/dashboard/summary/` | Role-aware dashboard metrics and recent appointments | — |
| `/api/patients/` | Patient records | `gender`, `blood_group` |
| `/api/doctors/` | Doctor directory and profiles | `specialization`, `is_active` |
| `/api/availabilities/` | Doctor availability windows | `doctor`, `weekday`, `is_active` |
| `/api/appointments/` | Bookings and appointment status | `patient`, `doctor`, `status`, `appointment_date` |
| `/api/appointments/today/` | Today's appointments | same appointment filters |
| `/api/prescriptions/` | Prescriptions and medicine lines | `patient`, `doctor`, `prescription_date` |
| `/api/invoices/` | Invoices and invoice items | `patient`, `payment_status`, `issue_date` |
| `/api/payments/` | Payment history | `invoice`, `method`, `payment_date` |

### Example: book an appointment

```json
{
  "patient": 1,
  "doctor": 1,
  "appointment_date": "2027-01-12",
  "start_time": "10:00:00",
  "end_time": "10:30:00",
  "reason": "Routine check-up"
}
```

The selected doctor must be active and have an availability window covering the requested day and time. The API rejects past dates, unavailable periods, and overlapping active appointments. Cancelled appointments do not occupy the time slot. A conditional database uniqueness constraint also prevents two active appointments for the same doctor, date, and start time.

### Example: create a prescription

```json
{
  "patient": 1,
  "doctor": 1,
  "diagnosis": "Seasonal allergy",
  "instructions": "Return if symptoms persist.",
  "medicines": [
    {
      "medicine_name": "Cetirizine",
      "dosage": "10 mg",
      "duration": "5 days",
      "quantity": 5,
      "instructions": "Take one tablet at night."
    }
  ]
}
```

### Example: generate an invoice

```json
{
  "patient": 1,
  "consultation_fee": "1000.00",
  "discount_amount": "100.00",
  "items": [
    {"description": "Blood test", "quantity": 1, "unit_price": "500.00"}
  ]
}
```

Invoice totals are calculated by the backend. `POST /api/payments/` records a payment against an invoice and updates its `UNPAID`, `PARTIALLY_PAID`, or `PAID` status. Overpayments are rejected.

## Role permissions

- **Admin:** full access to all modules.
- **Receptionist:** patient and doctor records, appointments, invoices, and payments; prescriptions are read-only.
- **Doctor:** own appointments and availability, assigned patients, own prescriptions, and relevant invoice/payment views. Doctors can mark their own appointments completed and create/update their own prescriptions.
- **Patient:** only their own profile, appointments, prescriptions, invoices, and payments; can browse active doctors/availability and book appointments for their linked profile.

Querysets are scoped on the backend. Frontend route hiding is not considered an authorization boundary.

## Automated tests

```bat
python manage.py test
```

The tests cover JWT authentication, role escalation prevention, patient creation and visibility, doctor creation, appointment booking and overlapping-slot rejection, prescription creation, invoice calculations, payment status updates, and overpayment rejection.

## Database and files

The local database is `db.sqlite3` (created by migrations). Uploaded patient profile images are stored under `media/patients/`. Neither database files nor uploaded patient media should be committed to GitHub.

## Development security notes

- `DEBUG=True` and the default `SECRET_KEY` are for local development only.
- Configure a unique secret key, `DEBUG=False`, trusted hosts, HTTPS, secure cookies, backups, logging, and a production database before deployment.
- SQLite's `select_for_update()` does not provide the same row-level concurrency guarantees as PostgreSQL. For a production multi-user deployment with concurrent booking traffic, migrate to PostgreSQL and enforce scheduling conflicts with database-level exclusion/locking strategy.
- This is a portfolio/demo backend, not a certified clinical system. Do not store real patient data in the public demo.


## Demo seed data

Run `python manage.py seed_demo` after migrations. It creates or refreshes four fictional logins (Admin, Receptionist, Doctor and Patient), three doctor profiles, five patient profiles, five appointments using all four statuses, 21 weekly availability windows, one two-medicine prescription, three invoices representing Unpaid / Partially Paid / Paid, and two payments. The command is transactional and idempotent, including when it is rerun on a later calendar date. It preserves unrelated users and clinical/billing records.

Demo logins:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@carebridge.demo` | `Admin@12345` |
| Receptionist | `reception@carebridge.demo` | `Reception@12345` |
| Doctor | `doctor@carebridge.demo` | `Doctor@12345` |
| Patient | `patient@carebridge.demo` | `Patient@12345` |

Seed tests: `python manage.py test accounts.tests.test_seed_demo`. All records and credentials are fictional and for local demonstration only.
