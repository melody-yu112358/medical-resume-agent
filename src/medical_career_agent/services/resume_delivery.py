from __future__ import annotations

import html
import json
from importlib.resources import files
from typing import Any


class ResumeDeliveryError(ValueError):
    """Raised when a conversation is not ready for candidate-facing export."""


class ResumeDeliveryService:
    """Render the audited conversation document without creating another resume brain."""

    THEMES = {"clinical-blue", "academic-green", "ats-mono"}
    TARGET_LABELS = {
        "doctoral_v1": "学术升学与科研申请",
        "clinical_research_v1": "临床研究与医院科研",
        "clinical_operations_v1": "临床运营与试验协调",
        "medical_affairs_v1": "医学事务 / MSL",
        "health_ai_data_v1": "医疗数据与数字健康",
    }

    def build_bundle(
        self,
        *,
        conversation: dict[str, Any],
        basics: dict[str, Any] | None = None,
        theme: str = "clinical-blue",
        tier_documents: dict[str, dict[str, Any] | None] | None = None,
    ) -> dict[str, Any]:
        state = conversation.get("state") or {}
        document = state.get("resume_document")
        if state.get("stage") != "delivery" or not isinstance(document, dict):
            raise ResumeDeliveryError("conversation must reach delivery before export")
        if theme not in self.THEMES:
            raise ResumeDeliveryError("theme is invalid")
        experiences = document.get("research_experience") or []
        if not any(item.get("bullets") for item in experiences):
            raise ResumeDeliveryError("at least one ClaimGate-ready bullet is required")

        document_basics = document.get("basics") or {}
        confirmed_contact = " · ".join(
            str(document_basics.get(field) or "").strip()
            for field in ("phone", "email", "location")
            if str(document_basics.get(field) or "").strip()
        )
        profile_confirmed = (state.get("candidate_profile") or {}).get("status") == "confirmed"
        resolved_basics = {
            "name": str(
                document_basics.get("name")
                or ("" if profile_confirmed else (basics or {}).get("name", ""))
            ).strip(),
            "contact": confirmed_contact or (
                "" if profile_confirmed else str((basics or {}).get("contact", "")).strip()
            ),
        }
        selected_tier = str(state.get("selected_resume_tier") or "professional")
        if selected_tier not in {"conservative", "professional", "high_impact"}:
            selected_tier = "professional"
        documents = {
            tier: ((tier_documents or {}).get(tier) or document)
            for tier in ("conservative", "professional", "high_impact")
        }
        tier_markdown = {
            tier: self._markdown(tier_document, resolved_basics)
            for tier, tier_document in documents.items()
        }
        markdown = tier_markdown[selected_tier]
        target_value = (document.get("target") or {}).get("role") or "医学相关方向"
        target = self.TARGET_LABELS.get(target_value, target_value)
        delivery_data = {
            "schema_version": "medical-resume-data-v1",
            "session_id": conversation.get("session_id"),
            "candidate": {
                "name": resolved_basics["name"], "target_direction": target,
                "contact": resolved_basics["contact"], "photo": None,
            },
            "fact_card": {
                "confirmed_experience_ids": [
                    item.get("item_id") for item in document.get("research_experience", [])
                    if item.get("item_id")
                ],
                "evidence_bound": True,
            },
            "tiers": {tier: {"markdown": value} for tier, value in tier_markdown.items()},
            "selected_tier": selected_tier,
            "theme": theme,
            "edit_status": "generated",
            "audit": {"status": "ready", "claim_gate_results": state.get("claim_gate_results", {})},
            "basics": resolved_basics,
            "resume_document": document,
            "audit_status": state.get("claim_gate_results", {}),
        }
        evidence = {
            "session_id": conversation.get("session_id"),
            "evidence": document.get("evidence", []),
            "claim_gate_results": state.get("claim_gate_results", {}),
        }
        editor = self._editor(markdown, theme)
        return {
            "files": {
                "resume.md": markdown,
                "resume.html": self._html(markdown, theme),
                "resume-editor.html": editor,
                "resume-data.json": json.dumps(delivery_data, ensure_ascii=False, indent=2),
                "evidence-summary.json": json.dumps(evidence, ensure_ascii=False, indent=2),
                "rewrite-comparison.md": self._rewrite_comparison(document),
                "export-instructions.txt": "下载 resume.html 后可直接打开；在浏览器中选择打印并另存为 PDF。",
            },
            "privacy": {
                "backend_persistence": "local_session_json",
                "export_written_to_server": False,
            },
        }

    @staticmethod
    def _markdown(document: dict[str, Any], basics: dict[str, str]) -> str:
        target_value = (document.get("target") or {}).get("role") or "医学相关方向"
        target = ResumeDeliveryService.TARGET_LABELS.get(target_value, target_value)
        lines = [
            f"# {basics['name'] or '姓名（请填写）'}",
            f"> {target}" + (f" · {basics['contact']}" if basics["contact"] else ""),
        ]
        summary = str((document.get("basics") or {}).get("summary") or "").strip()
        if summary:
            lines.extend(["", "## 候选人定位", summary])
        education = document.get("education") or []
        if education:
            lines.extend(["", "## 教育背景"])
            for item in education:
                heading = " · ".join(
                    value for value in (
                        str(item.get("institution") or "").strip(),
                        str(item.get("degree") or "").strip(),
                        str(item.get("major") or "").strip(),
                    ) if value
                )
                period = item.get("period") or {}
                end = "至今" if period.get("ongoing") else str(period.get("end") or "").strip()
                dates = " - ".join(value for value in (str(period.get("start") or "").strip(), end) if value)
                lines.append(f"### {heading or '教育经历'}" + (f" · {dates}" if dates else ""))
        lines.extend(["", "## 科研与实践经历"])
        for experience in document.get("research_experience", []):
            project_name = str(experience.get("project_name") or "").strip()
            organization = "" if experience.get("organization") == "待补充" else str(experience.get("organization") or "").strip()
            role_title = str(experience.get("title") or "").strip()
            period = experience.get("period") or {}
            end = "至今" if period.get("ongoing") else str(period.get("end") or "").strip()
            dates = " - ".join(value for value in (str(period.get("start") or "").strip(), end) if value)
            if project_name:
                lines.append(f"### {project_name}")
                metadata = " · ".join(value for value in (organization, role_title, dates) if value)
                if metadata:
                    lines.append(metadata)
            else:
                heading = " · ".join(value for value in (organization, role_title) if value) or "已确认经历"
                lines.append(f"### {heading}" + (f" · {dates}" if dates else ""))
            lines.extend(f"- {item['text']}" for item in experience.get("bullets", []) if item.get("text"))
        skill_groups = (
            ("研究方法", "research"),
            ("数据与工具", "data"),
            ("文献与证据资源", "medical_information"),
        )
        grouped = [
            (label, [item["name"] for item in document.get("skills", []) if item.get("category") == category and item.get("name")])
            for label, category in skill_groups
        ]
        if any(items for _, items in grouped):
            lines.extend(["", "## 研究方法与技能"])
            lines.extend(f"- **{label}：** {'、'.join(items)}" for label, items in grouped if items)
        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _editor(markdown: str, theme: str) -> str:
        template = files("medical_career_agent").joinpath(
            "assets/resume-editor.html"
        ).read_text(encoding="utf-8")
        return template.replace(
            "__INITIAL_MARKDOWN_JSON__", json.dumps(markdown, ensure_ascii=False)
        ).replace("__THEME__", theme)

    @staticmethod
    def _rewrite_comparison(document: dict[str, Any]) -> str:
        evidence = [
            item.get("statement", "") for item in document.get("evidence", [])
            if str(item.get("evidence_id", "")).startswith("ev_") and item.get("statement")
        ]
        bullets = [
            bullet.get("text", "")
            for experience in document.get("research_experience", [])
            for bullet in experience.get("bullets", []) if bullet.get("text")
        ]
        lines = ["# 改写对照", "", "## 用户确认的原始依据"]
        lines.extend(f"- {item}" for item in evidence)
        lines.extend(["", "## 已采用的审计后要点"])
        lines.extend(f"- {item}" for item in bullets)
        lines.extend(["", "## 说明", "- 仅使用已确认事实；未推断数量、成果或更高责任等级。"])
        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _html(markdown: str, theme: str) -> str:
        body: list[str] = []
        in_list = False
        for raw in markdown.splitlines():
            line = raw.strip()
            if line.startswith("- "):
                if not in_list:
                    body.append("<ul>")
                    in_list = True
                body.append(f"<li>{html.escape(line[2:])}</li>")
                continue
            if in_list:
                body.append("</ul>")
                in_list = False
            if line.startswith("### "):
                body.append(f"<h3>{html.escape(line[4:])}</h3>")
            elif line.startswith("## "):
                body.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.startswith("# "):
                body.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("> "):
                body.append(f'<p class="contact">{html.escape(line[2:])}</p>')
            elif line:
                body.append(f"<p>{html.escape(line)}</p>")
        if in_list:
            body.append("</ul>")
        colors = {
            "clinical-blue": ("#205f87", "#eef2f4"),
            "academic-green": ("#17664e", "#eef3ef"),
            "ats-mono": ("#111", "#f3f3f3"),
        }
        accent, background = colors[theme]
        return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>医学简历</title><style>
@page{{size:A4;margin:15mm 16mm}}*{{box-sizing:border-box}}body{{margin:0;background:{background};color:#17242d;font:10.5pt/1.6 "Microsoft YaHei",Arial,sans-serif}}main{{width:210mm;min-height:297mm;margin:12mm auto;padding:15mm 16mm;background:#fff;box-shadow:0 2px 18px #1c334022}}h1{{margin:0;font-size:25pt}}h2{{margin:6mm 0 2mm;padding-bottom:1mm;border-bottom:1px solid #ccdbe5;color:{accent};font-size:12pt}}h3{{margin:3mm 0 1mm;font-size:11pt}}.contact{{color:#62727d;border-bottom:2px solid {accent};padding-bottom:3mm}}p{{margin:1.5mm 0}}ul{{margin:1.5mm 0;padding-left:5mm}}li{{margin:1.1mm 0;text-align:justify}}@media print{{body{{background:#fff}}main{{width:auto;min-height:auto;margin:0;padding:0;box-shadow:none}}}}
</style><body><main>{"".join(body)}</main></body></html>'''
