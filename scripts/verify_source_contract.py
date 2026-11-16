"""Offline structural checks for the CareBridge frontend/backend API contract.

This script does not replace Django tests or a Vite build. It intentionally runs
without installing the application's dependencies so developers can detect
simple path/import/configuration drift early.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def check_python_sources() -> None:
    for source in BACKEND.rglob("*.py"):
        if "__pycache__" in source.parts:
            continue
        ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    print("PASS Python source parsing")


def resolve_local_import(source: Path, specifier: str) -> bool:
    base = source.parent / specifier
    candidates = (
        base,
        Path(f"{base}.js"),
        Path(f"{base}.jsx"),
        base / "index.js",
        base / "index.jsx",
    )
    return any(candidate.is_file() for candidate in candidates)


def check_frontend_imports() -> None:
    missing: list[str] = []
    for source in (FRONTEND / "src").rglob("*"):
        if source.suffix not in {".js", ".jsx"}:
            continue
        content = source.read_text(encoding="utf-8")
        for specifier in re.findall(r"from\s*['\"](\.[^'\"]+)['\"]", content):
            if not resolve_local_import(source, specifier):
                missing.append(f"{source.relative_to(ROOT)} -> {specifier}")
    if missing:
        raise AssertionError("Missing local imports:\n" + "\n".join(missing))
    print("PASS frontend local imports")


def check_api_routes() -> None:
    urls = (BACKEND / "config" / "urls.py").read_text(encoding="utf-8")
    api_client = (FRONTEND / "src" / "services" / "api.js").read_text(encoding="utf-8")
    resources_block = api_client.split("export const resources = {", 1)[1].split("};", 1)[0]
    frontend_routes = set(re.findall(r":\s*['\"](/[a-z-]+/)['\"]", resources_block))
    backend_routes = {f"/{name}/" for name in re.findall(r'router\.register\([\'\"]([a-z-]+)', urls)}
    if frontend_routes != backend_routes:
        raise AssertionError(
            f"Resource route mismatch. Frontend={sorted(frontend_routes)}, "
            f"backend={sorted(backend_routes)}"
        )
    required_auth = (
        'path("api/auth/token/"',
        'path("api/auth/token/refresh/"',
        'path("api/auth/me/"',
        'path("api/dashboard/summary/"',
    )
    for route in required_auth:
        if route not in urls:
            raise AssertionError(f"Required backend endpoint missing: {route}")
    print("PASS frontend resource routes match Django router")
    print("PASS authentication and dashboard endpoints are mounted")


def check_declared_stack() -> None:
    package = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    dependencies = package.get("dependencies", {}) | package.get("devDependencies", {})
    required = {"react", "react-dom", "vite", "axios", "react-router-dom", "tailwindcss", "recharts", "lucide-react"}
    missing = sorted(required - dependencies.keys())
    if missing:
        raise AssertionError(f"Frontend packages not declared: {missing}")
    print("PASS required frontend packages are declared")


def check_phase6_screenshot_automation() -> None:
    script = ROOT / "scripts" / "capture_screenshots.py"
    requirements = ROOT / "scripts" / "requirements-screenshots.txt"
    report = ROOT / "docs" / "PHASE6_SCREENSHOT_REPORT.md"
    for required in (script, requirements, report):
        if not required.is_file():
            raise AssertionError(f"Missing Phase 6 artifact: {required.relative_to(ROOT)}")
    ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
    required_images = (
        "login.png", "dashboard.png", "patients.png", "doctors.png",
        "appointments.png", "prescriptions.png", "billing.png", "patient-portal.png",
    )
    script_text = script.read_text(encoding="utf-8")
    missing = [filename for filename in required_images if filename not in script_text]
    if missing:
        raise AssertionError(f"Screenshot automation is missing outputs: {missing}")
    if "playwright" not in requirements.read_text(encoding="utf-8").lower():
        raise AssertionError("Optional Playwright dependency is not declared")
    print("PASS Phase 6 Playwright script, eight output names and instructions")


def check_seed_demo_contract() -> None:
    seed_path = BACKEND / "accounts" / "management" / "commands" / "seed_demo.py"
    tests_path = BACKEND / "accounts" / "tests" / "test_seed_demo.py"
    for required in (seed_path, tests_path, seed_path.parent / "__init__.py", seed_path.parent.parent / "__init__.py"):
        if not required.is_file():
            raise AssertionError(f"Missing demo seed file: {required.relative_to(ROOT)}")

    seed_source = seed_path.read_text(encoding="utf-8")
    test_source = tests_path.read_text(encoding="utf-8")
    required_seed_contract = (
        "@transaction.atomic",
        "DEMO_PASSWORDS",
        "User.Role.ADMIN",
        "User.Role.RECEPTIONIST",
        "User.Role.DOCTOR",
        "User.Role.PATIENT",
        "Appointment.Status.PENDING",
        "Appointment.Status.CONFIRMED",
        "Appointment.Status.COMPLETED",
        "Appointment.Status.CANCELLED",
        "recalculate_totals",
        "update_or_create",
        "DEMO-PAY-001",
    )
    missing = [token for token in required_seed_contract if token not in seed_source]
    if missing:
        raise AssertionError(f"Demo seed implementation is missing required behavior: {missing}")

    parsed_tests = ast.parse(test_source, filename=str(tests_path))
    test_names = {
        node.name for node in ast.walk(parsed_tests)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    }
    if len(test_names) < 5:
        raise AssertionError(f"Expected at least 5 seed tests, found {len(test_names)}")
    print(f"PASS demo seed contract and {len(test_names)} seed test methods present")


def main() -> int:
    checks = (
        check_python_sources,
        check_frontend_imports,
        check_api_routes,
        check_declared_stack,
        check_seed_demo_contract,
        check_phase6_screenshot_automation,
    )
    try:
        for check in checks:
            check()
    except Exception as error:  # print a useful failure for local CI usage
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    print("All offline source-contract checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
