# Phase 7 – Screenshot Embedding Report

## Result

Seven real CareBridge application screenshots supplied by the developer have been copied into `docs/screenshots/` and embedded in the root `README.md` using relative Markdown image references.

The images are preserved as PNG files. No images were generated or altered to imitate application screenshots.

## Included images

| README section | File | Dimensions | Source |
|---|---|---:|---|
| Login page | `docs/screenshots/login.png` | 1915 × 898 | Screenshot supplied earlier in this conversation |
| Admin dashboard | `docs/screenshots/dashboard.png` | 1918 × 879 | Screenshot supplied earlier in this conversation |
| Patient management | `docs/screenshots/patients.png` | 1918 × 877 | `New Compressed (zipped) Folder.zip` |
| Doctor management | `docs/screenshots/doctors.png` | 1918 × 880 | `New Compressed (zipped) Folder.zip` |
| Appointment management | `docs/screenshots/appointments.png` | 1918 × 876 | `New Compressed (zipped) Folder.zip` |
| Prescription management | `docs/screenshots/prescriptions.png` | 1918 × 877 | `New Compressed (zipped) Folder.zip` |
| Billing and payments | `docs/screenshots/billing.png` | 1918 × 882 | `New Compressed (zipped) Folder.zip` |

## Outstanding image

`docs/screenshots/patient-portal.png` is not included because it was not present in the supplied ZIP or earlier screenshot attachments. The README calls this out explicitly and does not contain a fake image or broken image link.

To complete the eight-image requirement, sign in to the local CareBridge frontend with the fictional patient demo account, navigate to the Patient Portal, capture the actual browser view, and save it as `docs/screenshots/patient-portal.png`. Add this Markdown reference to the README under section 8:

```markdown
![CareBridge patient portal](docs/screenshots/patient-portal.png)
```

## Verification

- All seven files exist in the expected directory.
- All seven files have valid PNG signatures and readable image data.
- Dimensions are greater than 1,700 pixels wide and 800 pixels high.
- Every included README image reference resolves to an existing file.
- The eighth image is documented as outstanding and is not linked until it exists.

These images are developer-supplied captures of the locally running application. This report does not claim that this build environment itself captured them through Playwright.
