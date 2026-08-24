#!/usr/bin/env python3
"""Build an editable, data-driven resume bundle without rewriting content."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

VALID_TIERS = {"conservative", "professional", "high_impact"}
VALID_THEMES = {"clinical-blue", "academic-green", "ats-mono"}


def load_resume_data(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "medical-resume-data-v1":
        raise ValueError("schema_version must be medical-resume-data-v1")
    tiers = data.get("tiers")
    if not isinstance(tiers, dict) or set(tiers) != VALID_TIERS:
        raise ValueError("tiers must contain conservative, professional, and high_impact")
    for tier in VALID_TIERS:
        markdown = tiers[tier].get("markdown") if isinstance(tiers[tier], dict) else None
        if not isinstance(markdown, str) or not markdown.strip():
            raise ValueError(f"tiers.{tier}.markdown must contain the complete resume")
    selected = data.get("selected_tier", "professional")
    if selected not in VALID_TIERS:
        raise ValueError("selected_tier is invalid")
    if data.get("theme", "clinical-blue") not in VALID_THEMES:
        raise ValueError("theme is invalid")
    return data


def inline_markup(value: str) -> str:
    value = html.escape(value, quote=True)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    return re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', value)


def markdown_to_html(markdown: str) -> str:
    output: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for raw in markdown.replace("\r", "").split("\n"):
        line = raw.strip()
        if not line:
            close_list()
            continue
        if line.startswith("- "):
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{inline_markup(line[2:])}</li>")
            continue
        close_list()
        if line.startswith("### "):
            output.append(f"<h3>{inline_markup(line[4:])}</h3>")
        elif line.startswith("## "):
            output.append(f"<h2>{inline_markup(line[3:])}</h2>")
        elif line.startswith("# "):
            output.append(f"<h1>{inline_markup(line[2:])}</h1>")
        elif line.startswith("> "):
            output.append(f"<blockquote>{inline_markup(line[2:])}</blockquote>")
        else:
            output.append(f"<p>{inline_markup(line)}</p>")
    close_list()
    return "\n".join(output)


def static_document(markdown: str, theme: str, title: str) -> str:
    accent = {"clinical-blue": "#215d87", "academic-green": "#17664e", "ats-mono": "#111"}[theme]
    body = markdown_to_html(markdown)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title or 'Resume')}</title><style>
@page {{ size:A4; margin:15mm 16mm; }} * {{ box-sizing:border-box; }}
body {{ margin:0; background:#eef2f3; color:#18232d; font:10.5pt/1.58 "Microsoft YaHei",Arial,sans-serif; }}
main {{ width:210mm; min-height:297mm; margin:12mm auto; padding:15mm 16mm; background:#fff; box-shadow:0 2px 18px #25323c24; }}
h1 {{ margin:0; font-size:25pt; line-height:1.15; }} h2 {{ margin:6mm 0 2.5mm; padding-bottom:1.2mm; color:{accent}; border-bottom:1px solid #dce4e5; font-size:12pt; }}
h3 {{ margin:3mm 0 0; font-size:10.7pt; }} p {{ margin:1.5mm 0; text-align:justify; }} blockquote {{ margin:2mm 0 4mm; padding-bottom:3mm; border-bottom:2px solid {accent}; color:#657282; }}
ul {{ margin:1.5mm 0 0; padding-left:5mm; }} li {{ margin:1.1mm 0; text-align:justify; }} a {{ color:inherit; }}
@media print {{ body {{ background:#fff; }} main {{ width:auto; min-height:auto; margin:0; padding:0; box-shadow:none; }} }}
</style></head><body><main>{body}</main></body></html>"""


def build_bundle(data_path: Path, output: Path, skill_root: Path | None = None) -> list[Path]:
    data = load_resume_data(data_path)
    skill_root = skill_root or Path(__file__).resolve().parents[1]
    output.mkdir(parents=True, exist_ok=True)
    selected = data["selected_tier"]
    markdown = data["tiers"][selected]["markdown"].strip() + "\n"
    theme = data.get("theme", "clinical-blue")
    name = str(data.get("candidate", {}).get("name", "Resume"))

    normalized_data = output / "resume-data.json"
    normalized_data.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    resume_md = output / "resume.md"
    resume_md.write_text(markdown, encoding="utf-8")
    resume_html = output / "resume.html"
    resume_html.write_text(static_document(markdown, theme, name), encoding="utf-8")

    editor_template = (skill_root / "assets" / "resume-editor.html").read_text(encoding="utf-8")
    editor = editor_template.replace("__INITIAL_MARKDOWN_JSON__", json.dumps(markdown, ensure_ascii=False)).replace("__THEME__", theme)
    editor_path = output / "resume-editor.html"
    editor_path.write_text(editor, encoding="utf-8")

    photo = data.get("candidate", {}).get("photo")
    if photo:
        source_photo = (data_path.parent / photo).resolve()
        if not source_photo.is_file():
            raise ValueError(f"candidate.photo does not exist: {photo}")
        shutil.copy2(source_photo, output / source_photo.name)
    return [normalized_data, resume_md, resume_html, editor_path]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path, default=Path("resume-output"))
    args = parser.parse_args()
    try:
        created = build_bundle(args.data.resolve(), args.output.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
