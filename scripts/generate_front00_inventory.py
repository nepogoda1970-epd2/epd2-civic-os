"""Generate the FRONT-00 inventory from the supplied static visual baseline."""

from __future__ import annotations

import csv
import re
import sys
from html import unescape
from pathlib import Path


def title_of(text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    return unescape(re.sub(r"\s+", " ", match.group(1)).strip()) if match else ""


def classify(relative: str, text: str) -> tuple[str, str]:
    if relative.startswith("transparenz/"):
        return "WS-10", "publication"
    if relative.startswith("intern/") or "cockpit" in relative:
        return "WS-02", "internal"
    if "<form" in text.lower() or "login" in relative:
        return "WS-02", "form"
    return "WS-01", "public"


def main(source: Path, output: Path) -> None:
    rows: list[list[str]] = []
    representatives = {
        "index.html": "/foundation/examples/public",
        "intern/dashboard.html": "/foundation/examples/cockpit",
        "intern/kommunikation.html": "/foundation/examples/communication",
        "buerger-login.html": "/foundation/examples/form",
        "struktur/abstimmungen.html": "/foundation/examples/table",
    }
    for path in sorted(source.rglob("*.html")):
        relative = path.relative_to(source).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        workspace, template = classify(relative, text)
        styles = ";".join(re.findall(r'href=["\']([^"\']+\.css)', text, re.IGNORECASE))
        elements = ";".join(
            name
            for name, token in [
                ("header", "<header"),
                ("navigation", "<nav"),
                ("cards", 'class="card'),
                ("form", "<form"),
                ("table", "<table"),
                ("footer", "<footer"),
            ]
            if token in text.lower()
        )
        fixture = representatives.get(relative)
        rows.append(
            [
                relative,
                title_of(text),
                template,
                elements,
                styles,
                workspace,
                fixture or "per authoritative route map",
                "representative_migrated" if fixture else "preserved_not_migrated",
                "yes",
                (
                    "semantic/accessibility/responsive/status corrections only"
                    if fixture
                    else "inventory only; future block decides migration"
                ),
            ]
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "filename",
                "current_title",
                "visual_template",
                "shared_elements",
                "css_rules",
                "target_workspace",
                "target_route",
                "migration_status",
                "visual_preservation",
                "technical_corrections",
            ]
        )
        writer.writerows(rows)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
