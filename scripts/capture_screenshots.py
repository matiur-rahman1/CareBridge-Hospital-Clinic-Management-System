"""Capture genuine CareBridge UI screenshots from a running local application.

Prerequisites:
  1. Django API is running at http://127.0.0.1:8000
  2. Vite frontend is running at http://localhost:5173
  3. `pip install -r scripts/requirements-screenshots.txt`
  4. `python -m playwright install chromium`

This script uses the visible React application and real Django API responses.
It deliberately fails instead of generating placeholders when either service,
a demo login, or a required page is unavailable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FRONTEND = "http://localhost:5173"
DEFAULT_BACKEND_HEALTH = "http://127.0.0.1:8000/api/health/"
DEFAULT_OUTPUT = ROOT / "docs" / "screenshots"


def check_http(url: str, label: str) -> None:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"{label} returned HTTP {response.status}: {url}")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"{label} is not reachable at {url}. Start the service in its own terminal first. Details: {exc}"
        ) from exc


def wait_for_page_content(page: Page, heading: str | None = None) -> None:
    page.locator(".app-shell").wait_for(state="visible", timeout=25_000)
    if heading:
        page.locator(".page-header h1").filter(has_text=heading).wait_for(
            state="visible", timeout=20_000
        )
    # Allow initial API requests, Recharts layout and fonts to settle.
    try:
        page.wait_for_load_state("networkidle", timeout=5_000)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(900)


def require_demo_content(page: Page, selector: str, minimum: int, page_name: str) -> None:
    count = page.locator(selector).count()
    if count < minimum:
        raise RuntimeError(
            f"{page_name} did not show the expected demo records "
            f"(found {count}, expected at least {minimum}; selector: {selector}). "
            "Run `python manage.py seed_demo` and check the browser/API responses."
        )


def save_page(
    page: Page,
    output: Path,
    filename: str,
    heading: str | None = None,
    content_selector: str | None = None,
) -> dict[str, Any]:
    if heading:
        page.locator(".page-header h1").filter(has_text=heading).wait_for(
            state="visible", timeout=20_000
        )
    elif page.locator(".login-form-wrap").count():
        page.locator(".login-form-wrap").wait_for(state="visible", timeout=20_000)
    else:
        page.locator(".app-shell").wait_for(state="visible", timeout=20_000)
    try:
        page.wait_for_load_state("networkidle", timeout=5_000)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(700)
    if content_selector:
        require_demo_content(page, content_selector, 1, filename)
    path = output / filename
    page.screenshot(path=str(path), full_page=True, animations="disabled")
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 10_000:
        raise RuntimeError(f"Screenshot does not look like a real rendered PNG: {path}")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    if width < 1000 or height < 600:
        raise RuntimeError(f"Unexpected screenshot dimensions {width}x{height}: {path}")
    print(f"CAPTURED {filename} ({width}x{height}, {len(data):,} bytes)")
    return {
        "file": filename,
        "width": width,
        "height": height,
        "bytes": len(data),
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def login(page: Page, frontend_url: str, email: str, password: str, role_label: str) -> None:
    page.goto(f"{frontend_url.rstrip('/')}/login", wait_until="domcontentloaded")
    page.locator(".login-form-wrap").wait_for(state="visible", timeout=20_000)
    page.get_by_label("Email address").fill(email)
    page.get_by_label("Password").fill(password)
    page.locator(".login-submit").click()
    try:
        page.locator(".app-shell").wait_for(state="visible", timeout=25_000)
    except PlaywrightTimeoutError as exc:
        error = page.locator(".form-error").inner_text() if page.locator(".form-error").count() else "No login error was rendered."
        raise RuntimeError(f"Could not sign in using the {role_label} demo account ({email}): {error}") from exc
    page.wait_for_timeout(500)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend-url", default=os.getenv("CAREBRIDGE_FRONTEND_URL", DEFAULT_FRONTEND))
    parser.add_argument("--backend-health-url", default=os.getenv("CAREBRIDGE_HEALTH_URL", DEFAULT_BACKEND_HEALTH))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--admin-email", default=os.getenv("CAREBRIDGE_ADMIN_EMAIL", "admin@carebridge.demo"))
    parser.add_argument("--admin-password", default=os.getenv("CAREBRIDGE_ADMIN_PASSWORD", "Admin@12345"))
    parser.add_argument("--patient-email", default=os.getenv("CAREBRIDGE_PATIENT_EMAIL", "patient@carebridge.demo"))
    parser.add_argument("--patient-password", default=os.getenv("CAREBRIDGE_PATIENT_PASSWORD", "Patient@12345"))
    args = parser.parse_args()

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    check_http(args.backend_health_url, "CareBridge Django API")
    check_http(args.frontend_url, "CareBridge Vite frontend")

    manifest: dict[str, Any] = {
        "application": "CareBridge",
        "capture_method": "Playwright Chromium against running React + Django services",
        "frontend_url": args.frontend_url,
        "backend_health_url": args.backend_health_url,
        "screenshots": [],
    }
    browser_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            device_scale_factor=1,
            color_scheme="light",
        )
        page = context.new_page()
        page.set_default_timeout(15_000)
        page.on("pageerror", lambda error: browser_errors.append(str(error)))

        # 1. Login screen, captured before authentication.
        page.goto(f"{args.frontend_url.rstrip('/')}/login", wait_until="domcontentloaded")
        manifest["screenshots"].append(save_page(page, output, "login.png"))

        # Admin-only workspace pages: dashboard, patient/doctor directories,
        # appointment calendar, prescription records and billing.
        login(page, args.frontend_url, args.admin_email, args.admin_password, "admin")
        wait_for_page_content(page)
        manifest["screenshots"].append(save_page(page, output, "dashboard.png", content_selector=".dashboard-bottom-grid .table-wrap tbody tr"))

        admin_pages = [
            ("/patients", "Patient management", "patients.png"),
            ("/doctors", "Doctor directory", "doctors.png"),
            ("/appointments", "Appointments", "appointments.png"),
            ("/prescriptions", "Prescriptions", "prescriptions.png"),
            ("/billing", "Billing & payments", "billing.png"),
        ]
        for route, heading, filename in admin_pages:
            page.goto(f"{args.frontend_url.rstrip('/')}{route}", wait_until="domcontentloaded")
            wait_for_page_content(page, heading)
            content_selectors = {
                "patients.png": ".section-card .table-wrap tbody tr",
                "doctors.png": ".section-card .table-wrap tbody tr",
                "appointments.png": ".day-appointment",
                "prescriptions.png": ".section-card .table-wrap tbody tr",
                "billing.png": ".section-card .table-wrap tbody tr",
            }
            manifest["screenshots"].append(
                save_page(page, output, filename, heading, content_selectors[filename])
            )

        # Patient portal is deliberately captured with the patient demo role,
        # not with an administrator session.
        page.locator(".logout-btn").click()
        page.locator(".login-form-wrap").wait_for(state="visible", timeout=15_000)
        login(page, args.frontend_url, args.patient_email, args.patient_password, "patient")
        page.goto(f"{args.frontend_url.rstrip('/')}/portal", wait_until="domcontentloaded")
        page.locator(".portal-welcome-card").wait_for(state="visible", timeout=20_000)
        wait_for_page_content(page)
        manifest["screenshots"].append(save_page(page, output, "patient-portal.png", content_selector=".portal-record-list .portal-record"))

        browser.close()

    expected = {
        "login.png", "dashboard.png", "patients.png", "doctors.png",
        "appointments.png", "prescriptions.png", "billing.png", "patient-portal.png",
    }
    actual = {item["file"] for item in manifest["screenshots"]}
    if actual != expected:
        raise RuntimeError(f"Screenshot set mismatch. Missing: {sorted(expected - actual)}")
    if browser_errors:
        raise RuntimeError("Browser runtime errors were detected:\n" + "\n".join(browser_errors))

    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nSUCCESS: captured and verified {len(actual)} real application screenshots.")
    print(f"Screenshot directory: {output}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SCREENSHOT CAPTURE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
