# CareBridge Frontend

React single-page application for CareBridge Hospital & Clinic Management System.

## Stack

- React 18 + Vite
- JavaScript
- Tailwind CSS 3
- Axios with JWT access-token and refresh-token handling
- React Router 6
- Recharts
- Lucide React
- date-fns
- Vitest + Testing Library

## Windows 11 setup

Open a **new terminal** (leave Django running in the backend terminal):

```bat
cd CareBridge\frontend
copy .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173/`. The app uses `http://127.0.0.1:8000/api` by default. Change `VITE_API_BASE_URL` in `.env` when the Django API runs elsewhere.

## Backend prerequisite

Start the Django backend in another terminal before using the app:

```bat
cd CareBridge\backend
venv\Scripts\activate
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

## Pages and roles

| Page | Admin | Receptionist | Doctor | Patient |
|---|:---:|:---:|:---:|:---:|
| Dashboard | Yes | Yes | Yes | Yes |
| Patient records | Manage | Manage | Assigned patients, read-only | No |
| Doctor directory | Manage | Manage | No | Browse active doctors |
| Appointments | Manage | Manage | View / complete own | Book / view / cancel own |
| Prescriptions | Manage | Read-only | Create / view own | View own |
| Billing | Manage | Manage | Relevant records, read-only | Own invoices / payments |
| Personal portal | No | No | Doctor portal | Patient portal |
| Profile | Own account | Own account | Own account | Own account |

The backend independently enforces role permissions and record scoping. Hiding a route in the frontend is not treated as authorization.

## API integration

All requests use the shared Axios client in `src/services/api.js`. It attaches the JWT access token, attempts a refresh on an expired access token, and clears the local session if the refresh fails.

| Resource | API route |
|---|---|
| Sign in | `POST /api/auth/token/` |
| Current user | `GET/PATCH /api/auth/me/` |
| Dashboard | `GET /api/dashboard/summary/` |
| Patients | `/api/patients/` |
| Doctors | `/api/doctors/` |
| Doctor availability | `/api/availabilities/` |
| Appointments | `/api/appointments/` |
| Prescriptions | `/api/prescriptions/` |
| Invoices | `/api/invoices/` |
| Payments | `/api/payments/` |

## Development checks

```bat
npm test
npm run build
```

## Demo accounts

Run `python manage.py seed_demo` in the backend first. Demo credentials are listed in the root [README](../README.md). They are intended only for local demonstration.
