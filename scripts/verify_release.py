"""Verify the GitHub release contents without requiring Django or Node.js.

Run from any directory with: python scripts/verify_release.py
The Patient Portal screenshot is optional until the developer adds the supplied
real capture; all screenshots already referenced by README must exist.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "docs" / "screenshots"
REQUIRED = (
    "login.png",
    "dashboard.png",
    "patients.png",
    "doctors.png",
    "appointments.png",
    "prescriptions.png",
    "billing.png",
    "patient-portal.png",
)


def is_png(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            return stream.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def main() -> int:
    required_files = (
        ROOT / "README.md",
        ROOT / ".gitignore",
        ROOT / "backend" / "manage.py",
        ROOT / "backend" / "requirements.txt",
        ROOT / "frontend" / "package.json",
        ROOT / "scripts" / "capture_screenshots.py",
    )
    missing = [str(path.relative_to(ROOT)) for path in required_files if not path.is_file()]
    if missing:
        print("FAIL: missing release files:\n- " + "\n- ".join(missing))
        return 1

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    image_targets = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", readme)
    broken = []
    for target in image_targets:
        local_target = target.split("#", 1)[0].split("?", 1)[0]
        if re.match(r"^[a-z]+://", local_target, re.I):
            continue
        if not (ROOT / local_target).is_file():
            broken.append(target)
    if broken:
        print("FAIL: README references missing images:\n- " + "\n- ".join(broken))
        return 1

    print("PASS: required project files are present")
    print(f"PASS: all {len(image_targets)} README image references resolve")
    present = []
    absent = []
    invalid = []
    for filename in REQUIRED:
        path = SCREENSHOTS / filename
        if not path.exists():
            absent.append(filename)
        elif not is_png(path):
            invalid.append(filename)
        else:
            present.append(filename)
    if invalid:
        print("FAIL: invalid PNG files: " + ", ".join(invalid))
        return 1
    print(f"PASS: {len(present)} of {len(REQUIRED)} required screenshot PNGs are present and valid")
    if absent:
        print("PENDING screenshot(s): " + ", ".join(absent))
        if absent != ["patient-portal.png"]:
            return 1
        print("The single pending Patient Portal image is documented; no broken README link exists.")
    else:
        print("All eight required screenshot files are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
