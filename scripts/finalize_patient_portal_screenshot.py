from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "docs" / "screenshots" / "patient-portal.png"
README = ROOT / "README.md"

def main():
    if not IMAGE.is_file():
        raise SystemExit(f"Screenshot not found: {IMAGE}")

    with IMAGE.open("rb") as f:
        if f.read(8) != b"\x89PNG\r\n\x1a\n":
            raise SystemExit("Invalid PNG file.")

    if not README.is_file():
        raise SystemExit("README.md not found.")

    content = README.read_text(encoding="utf-8-sig")

    image_link = "![CareBridge Patient Portal](docs/screenshots/patient-portal.png)"

    if image_link in content:
        print("Patient Portal screenshot is already embedded.")
        return

    pattern = r"(?im)^#{2,4}[^\r\n]*patient\s+portal[^\r\n]*\r?\n"
    match = re.search(pattern, content)

    section = (
        "## Patient Portal Screenshot\n\n"
        + image_link
        + "\n\n"
        "This is the real Patient Portal screenshot from the running application.\n"
    )

    if match:
        next_heading = re.search(
            r"(?m)^#{1,4}\s+", content[match.end():]
        )
        if next_heading:
            end = match.end() + next_heading.start()
            content = content[:match.start()] + section + "\n" + content[end:]
        else:
            content = content[:match.start()] + section
    else:
        content = content.rstrip() + "\n\n" + section

    README.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("SUCCESS: Patient Portal screenshot added to README.md")

if __name__ == "__main__":
    main()
