# Phase 8 – Final GitHub Release Package

## Release status

The final project source ZIP has been assembled as a GitHub-ready project package. It includes the Django backend, React frontend, migrations, demo seed command and tests, screenshot automation, previous phase reports, Windows setup instructions, GitHub publishing commands, and seven authentic application screenshots.

The developer reports that the Patient Portal screenshot was captured locally, but the image could not be uploaded in the current conversation because of an attachment limit. It is therefore not present in this release. No synthetic image, blank placeholder PNG, or broken Markdown image reference has been added.

## Included real screenshots

- `docs/screenshots/login.png`
- `docs/screenshots/dashboard.png`
- `docs/screenshots/patients.png`
- `docs/screenshots/doctors.png`
- `docs/screenshots/appointments.png`
- `docs/screenshots/prescriptions.png`
- `docs/screenshots/billing.png`

Each image was supplied by the developer from the locally running CareBridge application. The README embeds the seven files using repository-relative Markdown links.

## Add the eighth screenshot later

1. Save the real Patient Portal browser screenshot as `docs/screenshots/patient-portal.png`.
2. From the project root run:

   ```powershell
   python scripts/finalize_patient_portal_screenshot.py
   python scripts/verify_release.py
   ```

3. Review the updated `README.md`, then commit and push the new image and README to GitHub.

The finalizer checks for a PNG file and replaces the documented pending section with the relative Markdown image link. The verification script checks that README image links resolve and reports whether all eight screenshots exist.

## Verification evidence

- Seven image files exist and are valid PNGs.
- Every Markdown image link included in the README resolves to a file in the package.
- The README explicitly marks the Patient Portal image as pending and explains how to insert it later.
- The user confirmed the local Django health endpoint returned `{"application":"CareBridge API","status":"ok"}` and supplied a screenshot showing successful React administrator login and dashboard rendering.
- The developer also supplied five more real page screenshots in a ZIP: Patients, Doctors, Appointments, Prescriptions and Billing.
- This packaging environment did not run the Django automated tests, Vite build, Vitest suite or a full eight-page Playwright pass. Their status must not be represented as passed.

## Recommended final local checks

Backend terminal:

```powershell
cd backend
venv\\Scripts\\activate
python manage.py check
python manage.py test
```

Frontend terminal:

```powershell
cd frontend
npm test
npm run build
```

Release verification (from project root):

```powershell
python scripts/verify_source_contract.py
python scripts/verify_release.py
```

## GitHub publication

The root README contains step-by-step GitHub repository creation and `git push` commands. Review `.gitignore` and `git status` before committing; do not publish `.env` files, database files, uploaded media, secrets, or real patient data.
