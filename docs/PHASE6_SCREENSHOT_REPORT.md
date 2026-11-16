# CareBridge Phase 6 – Screenshot Preparation and Execution Report

## Outcome

The Phase 5 source was inspected and the Playwright automation script was added. The build environment could not launch Django/Vite because the dependencies were unavailable. After running CareBridge locally on Windows, the developer supplied seven genuine application screenshots. Those PNGs are now stored in `docs/screenshots/` and embedded in the root README. The Patient Portal screenshot remains outstanding. The supplied files are not generated mockups.

## Source inspection

The current React application exposes these routes:

- `/login`
- `/` – role-aware dashboard
- `/patients`
- `/doctors`
- `/appointments`
- `/prescriptions`
- `/billing`
- `/portal` – patient/doctor portal, based on the authenticated role

The capture script logs into the actual login page with the seeded Admin account, captures the six Admin workspace screens, signs out, logs in with the seeded Patient account, then captures the Patient Portal. It checks that the Django health endpoint and Vite frontend are reachable, waits for page content, validates PNG signatures and dimensions, and writes a `manifest.json` only after all eight screenshots have been captured successfully.

## Why capture could not run here

The environment has Playwright Python installed and system Chromium is present, but the application dependencies required to launch CareBridge are not available:

- Runtime Python: 3.13.5; the project setup target is Python 3.11.
- Django/DRF: not installed. `pip install -r backend/requirements.txt` failed because DNS resolution for the package index failed (`Temporary failure in name resolution`).
- Node.js/npm: Node 22.16.0 and npm 10.9.2 are present.
- Frontend dependencies: `frontend/node_modules` is absent. `npm install --no-audit --no-fund` timed out while trying to reach the npm registry.
- The API and Vite server therefore could not be started. Playwright was not pointed at a mock page or a substitute UI.

As a result, this build environment did not capture screenshots itself. The later developer-supplied login, dashboard, patient, doctor, appointment, prescription and billing PNGs have been added to the project. The Patient Portal capture is still missing. This distinction is recorded so the repository does not imply Playwright was executed successfully in the build environment.

## Files added

- `scripts/capture_screenshots.py` – real-browser capture of the eight requested pages.
- `scripts/requirements-screenshots.txt` – optional Playwright Python dependency.

## Exact Windows 11 instructions

Run these commands from the extracted `CareBridge` project root. Use three terminals for the two servers and the screenshot capture.

### 1. Install and prepare the backend (Terminal 1)

```bat
cd backend
py -3.11 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py check
python manage.py test
python manage.py runserver
```

Leave the backend server running at `http://127.0.0.1:8000/`.

### 2. Install and start the frontend (Terminal 2)

```bat
cd frontend
copy .env.example .env
npm install
npm run build
npm run dev
```

Leave Vite running at `http://localhost:5173/`.

### 3. Install Playwright and capture screenshots (Terminal 3)

From the project root, not the `frontend` or `backend` folder:

```bat
py -3.11 -m pip install -r scripts\requirements-screenshots.txt
py -3.11 -m playwright install chromium
py -3.11 scripts\capture_screenshots.py
```

The script signs into the local seeded demo accounts. It expects the default demo credentials:

- Admin: `admin@carebridge.demo` / `Admin@12345`
- Patient: `patient@carebridge.demo` / `Patient@12345`

To use different local credentials, set environment variables before running the script:

```bat
set CAREBRIDGE_ADMIN_EMAIL=admin@carebridge.demo
set CAREBRIDGE_ADMIN_PASSWORD=Admin@12345
set CAREBRIDGE_PATIENT_EMAIL=patient@carebridge.demo
set CAREBRIDGE_PATIENT_PASSWORD=Patient@12345
py -3.11 scripts\capture_screenshots.py
```

### 4. Expected screenshot files

The Playwright script is configured to create and verify these eight real PNG files in `docs/screenshots/` when run locally. Seven are currently present from developer-supplied captures; `patient-portal.png` is still outstanding:

| File | Screen | Role used |
|---|---|---|
| `login.png` | Login page | Signed out |
| `dashboard.png` | Admin dashboard | Admin |
| `patients.png` | Patient management | Admin |
| `doctors.png` | Doctor management | Admin |
| `appointments.png` | Appointment calendar | Admin |
| `prescriptions.png` | Prescription management | Admin |
| `billing.png` | Billing and invoices | Admin |
| `patient-portal.png` | Patient portal | Patient |

The script also writes `docs/screenshots/manifest.json`, containing the capture method, local URLs, filenames, image dimensions and file sizes. If a required service, login, or page is unavailable, the script exits with an error and does not claim a successful eight-image capture.

## README embedding status

Seven available screenshots are embedded in the root `README.md` using relative paths. The eighth image, `docs/screenshots/patient-portal.png`, is not linked because it has not been supplied. See [Phase 7 screenshot embedding report](PHASE7_SCREENSHOT_EMBEDDING_REPORT.md) for file dimensions, sources and the remaining step.

## Checks executed in this workspace

| Check | Result | Evidence |
|---|---|---|
| Python source compilation for capture and source-contract scripts | Passed | `python -m py_compile scripts/capture_screenshots.py scripts/verify_source_contract.py` |
| Offline project contract checks | Passed | `python scripts/verify_source_contract.py` |
| Playwright CLI argument/help loading | Passed | `python scripts/capture_screenshots.py --help` |
| Playwright capture against the actual app in this build environment | Blocked as expected | Script stopped because `127.0.0.1:8000/api/health/` returned connection refused; no PNG was written by this environment |
| Developer-supplied screenshot file validation | Passed | Seven supplied PNGs were opened and their dimensions/signatures verified; see Phase 7 report |
| Django check and tests | Blocked | `ModuleNotFoundError: No module named 'django'` |
| Vite production build | Blocked | `vite: not found` |
| Vitest test suite | Blocked | `vitest: not found` |
| Dependency install | Blocked | pip package-index DNS failure; npm install timed out |

The browser automation is intentionally fail-closed. A successful PNG requires both real servers, valid demo logins, the expected page headings, and at least one rendered seeded record on each data page. The script also detects uncaught page JavaScript errors and validates the PNG signature and image dimensions before writing its manifest.
