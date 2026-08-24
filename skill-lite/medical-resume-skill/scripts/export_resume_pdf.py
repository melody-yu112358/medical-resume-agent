#!/usr/bin/env python3
"""Export resume HTML to PDF with explicit browser fallbacks."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def edge_candidates() -> list[Path]:
    candidates: list[Path] = []
    for command in ("msedge", "msedge.exe"):
        found = shutil.which(command)
        if found:
            candidates.append(Path(found))
    for root in (Path("C:/Program Files (x86)"), Path("C:/Program Files")):
        candidates.append(root / "Microsoft/Edge/Application/msedge.exe")
    return candidates


def export_with_playwright(source: Path, target: Path) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(source.as_uri(), wait_until="networkidle")
            page.emulate_media(media="print")
            page.pdf(path=str(target), format="A4", print_background=True)
            browser.close()
        return target.is_file() and target.stat().st_size > 0
    except Exception:
        return False


def export_with_edge(source: Path, target: Path) -> bool:
    edge = next((path for path in edge_candidates() if path.is_file()), None)
    if not edge:
        return False
    result = subprocess.run(
        [str(edge), "--headless", "--disable-gpu", f"--print-to-pdf={target}", source.as_uri()],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    return result.returncode == 0 and target.is_file() and target.stat().st_size > 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source = args.html.resolve()
    target = (args.output or source.with_suffix(".pdf")).resolve()
    if not source.is_file():
        parser.error(f"HTML file does not exist: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if export_with_playwright(source, target):
        print(f"PDF created with Playwright: {target}")
        return 0
    if export_with_edge(source, target):
        print(f"PDF created with Microsoft Edge: {target}")
        return 0
    print("Automatic PDF export was unavailable. Open resume-editor.html and use Print / PDF; do not report a PDF as delivered until the file exists.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
