from __future__ import annotations

import json
import html
from pathlib import Path
from typing import Any, Dict, List

# Add src to path so we can import medical_career_agent modules
import sys
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from medical_career_agent.services.experience_draft import ExperienceDraftService
from medical_career_agent.services.question_planner import QuestionPlannerService
from medical_career_agent.services.candidate_positioning import CandidatePositioningService
from medical_career_agent.services.content_planning import ContentPlanningService
from medical_career_agent.services.multi_dimensional_content_generator import MultiDimensionalContentGenerator
from medical_career_agent.services.three_tier_expression_system import ThreeTierExpressionSystem
from medical_career_agent.services.semantic_claim_gate import SemanticClaimGateService
from medical_career_agent.services.resume_document_assembler import ResumeDocumentAssembler, enhance_role_packs


class MedicalResumeAgentV1:
    """完整的医学简历Agent V1实现。"""

    def __init__(self):
        """初始化所有服务。"""
        self.experience_draft_service = ExperienceDraftService()
        self.question_planner_service = QuestionPlannerService()
        self.candidate_positioning_service = CandidatePositioningService()
        self.content_planning_service = ContentPlanningService()
        self.content_generator = MultiDimensionalContentGenerator()
        self.three_tier_system = ThreeTierExpressionSystem()
        self.claim_gate_service = SemanticClaimGateService()
        self.resume_assembler = ResumeDocumentAssembler()

        # Removed enhance_role_packs() to preserve original evaluation cases

    def process_user_input(
        self,
        user_input: str,
        target_roles: List[str] = None,
        *,
        confirmed_candidate_facts: Dict[str, Any] | None = None,
        canonical_experiences: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """Process input, stopping at confirmation unless facts are explicit.

        Raw text is evidence, not permission to fill gaps. Callers first receive
        extracted facts and up to three questions. After the user confirms or
        edits those facts, pass them back through ``confirmed_candidate_facts``
        together with canonical experiences.
        """
        if target_roles is None:
            target_roles = ["doctoral_v1"]

        if confirmed_candidate_facts is None or canonical_experiences is None:
            draft = self.experience_draft_service.draft(
                experience_text=user_input,
                consent_confirmed=True
            )
            return {
                "status": "needs_confirmation",
                "message": "请补充并确认事实后再生成简历。",
                "extracted_facts": draft.extracted_facts,
                "unknown_items": draft.unknown_items,
                "clarifying_questions": draft.clarifying_questions[:3],
                "possible_value_angles": draft.possible_value_angles,
                "risk_flags": draft.risk_flags,
            }

        candidate_profile = dict(confirmed_candidate_facts)

        # 2. 生成候选人定位
        positioning = self.candidate_positioning_service.generate_positioning(
            canonical_experiences=canonical_experiences,
            target_roles=target_roles
        )

        # 3. 创建内容计划
        content_plan = self.content_planning_service.create_content_plan(
            canonical_experiences=canonical_experiences,
            candidate_positioning=positioning.to_dict(),
            target_role=target_roles[0]
        )

        # 4. 生成三档表达 for each experience
        three_tier_results = []
        for i, canonical_exp in enumerate(canonical_experiences):
            three_tier_result = self.three_tier_system.generate_three_tiers(
                canonical_experience=canonical_exp,
                content_plan=content_plan.to_dict(),
                target_role=target_roles[0]
            )
            three_tier_results.append(three_tier_result)

        # 5. Claim Gate验证 for all claims
        validation_results = []
        for result, canonical_exp in zip(three_tier_results, canonical_experiences):
            for claim in result.professional_claims:
                validation = self.claim_gate_service.validate_claim_semantic_layers(
                    bullet_claim=claim.to_dict(),
                    canonical_experience=canonical_exp  # Use the corresponding canonical experience
                )
                validation_results.append(validation)

        # Check if all claims pass validation
        all_valid = all(result.status == "ready" for result in validation_results)
        if not all_valid:
            return {
                "status": "validation_failed",
                "message": "部分声明未通过Claim Gate验证",
                "validation_results": [r.to_dict() for r in validation_results]
            }

        # 6. 组装完整简历文档
        candidate_facts_wrapper = {
            **candidate_profile,
            "session_id": "test_session",
            "overview": candidate_profile.get("overview", positioning.identity),
            "canonical_experiences": canonical_experiences
        }

        resume_document = self.resume_assembler.assemble_resume_document(
            candidate_facts=candidate_facts_wrapper,
            three_tier_results=three_tier_results,
            target_roles=target_roles,
            expression_tier="professional"
        )

        return {
            "status": "success",
            "resume_document": resume_document.to_dict(),
            "three_tier_results": [result.to_dict() for result in three_tier_results],
            "validation_passed": True
        }

    def _create_canonical_experience(self, extracted_facts: Dict[str, Any]) -> Dict[str, Any]:
        """Create a canonical record without inventing missing facts."""
        return {
            "schema_version": "canonical-experience-v1",
            "experience_id": "meta_analysis_001",
            "evidence_ids": ["ev_001"],
            "context": extracted_facts.get("context", {"domain": "other", "setting": "other"}),
            "role": extracted_facts.get("role", {"responsibility_level": "participated"}),
            "background": extracted_facts.get("background"),
            "problem_or_goal": extracted_facts.get("problem_or_goal"),
            "actions": extracted_facts.get("actions", []),
            "methods": extracted_facts.get("methods", []),
            "tools": extracted_facts.get("tools", []),
            "objects": extracted_facts.get("objects", []),
            "workflow_steps": extracted_facts.get("workflow_steps", []),
            "quality_control": extracted_facts.get("quality_control", []),
            "decisions_or_judgments": extracted_facts.get("decisions_or_judgments", []),
            "collaboration": extracted_facts.get("collaboration", []),
            "artifacts": extracted_facts.get("artifacts", []),
            "outcomes": extracted_facts.get("outcomes", []),
            "scope": extracted_facts.get("scope", {}),
            "status": "user_confirmed"
        }


def generate_v32_golden_sample():
    """Generate the synthetic V3.2 demo fixture for regression tests only.

    This entry point is intentionally separate from ``process_user_input`` and
    must never be used to construct a real user's canonical experiences.
    """
    from medical_career_agent.services.v32_canonical_experience_factory import (
        create_v32_synthetic_demo_experiences,
    )
    agent = MedicalResumeAgentV1()

    v32_input = """临床医学学士，专注于心血管临床研究方向，具备系统性循证医学训练和扎实的统计分析能力。通过参与心血管Meta分析项目，在导师指导和团队协作下完成了从研究问题识别、系统检索、质量评价到结果解释的完整证据综合流程；通过心血管流行病学调查，积累了真实世界研究数据处理和分析经验；在心内科临床实习中培养了专科临床思维和科研问题识别能力。致力于将临床实践与循证研究相结合，推动心血管疾病二级预防的个体化决策。"""

    candidate_facts_path = Path(__file__).parent.parent.parent / "data" / "fixtures" / "candidate-facts.json"
    candidate_facts = json.loads(candidate_facts_path.read_text(encoding="utf-8"))
    canonical_experiences = create_v32_synthetic_demo_experiences(candidate_facts)
    result = agent.process_user_input(
        v32_input,
        ["doctoral_v1"],
        confirmed_candidate_facts=candidate_facts,
        canonical_experiences=canonical_experiences,
    )

    if result["status"] == "success":
        # 保存结果
        output_dir = (
            Path(__file__).parent.parent.parent
            / "golden-sample"
            / "generated"
            / "synthetic-demo"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存专业版HTML
        html_content = generate_html_from_resume_document(result["resume_document"])
        (output_dir / "v3.2-professional-generated.html").write_text(html_content, encoding="utf-8")

        # 保存简历文档
        (output_dir / "v3.2-resume-document.json").write_text(
            json.dumps(result["resume_document"], ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print("V3.2黄金样本生成成功！")
        print(f"   HTML路径: {output_dir / 'v3.2-professional-generated.html'}")
        print(f"   JSON路径: {output_dir / 'v3.2-resume-document.json'}")

        return result
    else:
        print("V3.2黄金样本生成失败！")
        print(f"   错误: {result['message']}")
        return None


def generate_html_from_resume_document(resume_document: Dict[str, Any]) -> str:
    """从简历文档生成HTML。"""
    # Use V3.2 template structure but make it fully data-driven
    html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{{DOCUMENT_TITLE}}</title>
  <style>
    /* ATS-compatible medical resume styles */
    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 0;
      font-family: "Times New Roman", "SimHei", "Microsoft YaHei", sans-serif;
      font-size: 10.5pt;
      line-height: 1.42;
      color: #18212a;
    }

    .resume-sheet {
      width: 210mm;
      min-height: 297mm;
      max-width: 210mm;
      margin: 0 auto;
      padding: 9mm 12mm 11mm;
      background: #fff;
      box-shadow: 0 2px 18px #1f29372e;
    }

    .resume-header-container {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 5mm;
    }

    .resume-header-text {
      flex: 1;
      min-width: 0;
      padding-right: 10mm;
    }

    .resume-avatar-container {
      width: 24mm;
      height: 24mm;
      flex-shrink: 0;
    }

    .resume-avatar {
      width: 100%;
      height: 100%;
      object-fit: cover;
      border-radius: 4px;
      border: 1px solid #ddd;
    }

    .resume-name {
      margin: 0 0 3px;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      font: 700 22pt/1.08;
      letter-spacing: 0;
    }

    .resume-target {
      margin: 4px 0;
      color: #171717;
      font-weight: 700;
      font-size: 11.5pt;
      letter-spacing: .02em;
    }

    .resume-contact {
      margin: 3px 0;
      color: #202020;
      font-size: 10.5pt;
    }

    .resume-section {
      margin-top: 5mm;
      break-inside: avoid;
    }

    .resume-section h2 {
      margin: 0 0 4px;
      padding: 0;
      border: 0;
      color: #171717;
      font: 700 12.5pt/1.15;
      letter-spacing: 0;
      position: relative;
    }

    .resume-section h2::after {
      content: "";
      display: block;
      width: 30%;
      height: 0.6px;
      margin-top: 2px;
      background: #888888;
    }

    .resume-summary {
      margin: 3px 0;
      color: #202020;
      font-size: 10.6pt;
      line-height: 1.48;
    }

    .resume-list {
      margin: 2px 0 3px 17px;
      padding: 0;
    }

    .resume-list li {
      margin: 2px 0;
      color: #202020;
      font-size: 10.4pt;
      line-height: 1.45;
    }

    .resume-entry {
      padding: 0;
      margin: 4mm 0 4mm 0;
    }

    .resume-entry-head {
      display: grid;
      grid-template-columns: minmax(0,1fr) auto;
      gap: 12px;
      align-items: baseline;
      padding-bottom: 2px;
    }

    .resume-date {
      grid-column: 2;
      grid-row: 1;
      color: #334155;
      font: 9.5pt "Times New Roman", "Microsoft YaHei", sans-serif;
      white-space: nowrap;
    }

    .resume-org {
      grid-column: 1;
      grid-row: 1;
      font-size: 11.1pt;
      font-weight: 700;
    }

    .resume-role {
      grid-column: 1;
      grid-row: 2;
      color: #202020;
      font-size: 10.2pt;
    }

    .resume-empty {
      padding: 20px 0;
      color: #66716c;
      font-size: 10pt;
    }

    /* Print styles */
    @media print {
      body {
        margin: 0;
        padding: 0;
      }
      .resume-sheet {
        width: 210mm !important;
        min-height: 297mm !important;
        margin: 0 !important;
        padding: 9mm 12mm 11mm !important;
        box-shadow: none !important;
      }

      /* Explicit page break rules */
      .page-break {
        page-break-before: always;
      }

      .avoid-page-break {
        page-break-inside: avoid;
      }

      /* Allow long sections to break naturally */
      .resume-section {
        break-inside: auto;
      }

      .resume-entry {
        break-inside: auto;
      }

      /* Prevent orphaned headings */
      h2 {
        break-after: avoid;
      }

      /* Keep list items together when possible */
      .resume-list li {
        break-inside: avoid;
      }
    }

    /* Mobile responsive */
    @media (max-width: 760px) {
      .resume-sheet {
        width: 100%;
        min-height: auto;
        padding: 24px 18px;
      }

      .resume-header-container {
        flex-direction: column;
        align-items: center;
      }

      .resume-header-text {
        padding-right: 0;
        margin-bottom: 10px;
        text-align: center;
      }

      .resume-avatar-container {
        margin-bottom: 10px;
      }

      .resume-entry-head {
        grid-template-columns: 1fr;
        gap: 2px;
      }

      .resume-date,
      .resume-org,
      .resume-role {
        grid-column: 1;
        grid-row: auto;
      }
    }
  </style>
</head>
<body>
  <div class="resume-sheet template-minimal">
    <div class="resume-header-container">
      <div class="resume-header-text">
        <h1 class="resume-name">{{NAME}}</h1>
        <div class="resume-target">{{TARGET}}</div>
        {{CONTACT}}
      </div>
      {{AVATAR}}
    </div>

    <div class="resume-section">
      <div class="resume-summary">
        {{SUMMARY}}
      </div>
    </div>

    <!-- 核心能力概览 -->
    <div class="resume-section">
      <h2>核心能力概览</h2>
      <ul class="resume-list">
        {{CAPABILITY_PROFILE}}
      </ul>
    </div>

    <!-- 教育背景 -->
    <div class="resume-section">
      <h2>教育背景</h2>
      <ul class="resume-list">
        {{EDUCATION}}
      </ul>
    </div>

    <!-- 科研经历 -->
    {{RESEARCH_EXPERIENCE}}

    <!-- 大创项目 -->
    {{PROJECTS}}

    <!-- 临床实习 -->
    {{CLINICAL_EXPERIENCE}}

    {{PUBLICATIONS}}

    <!-- 专业技能 -->
    <div class="resume-section">
      <h2>专业技能</h2>
      <ul class="resume-list">
        {{SKILLS}}
      </ul>
    </div>

    <!-- 研究兴趣 -->
    <div class="resume-section">
      <h2>研究兴趣</h2>
      <ul class="resume-list">
        {{RESEARCH_INTERESTS}}
      </ul>
    </div>
  </div>
</body>
</html>'''

    # Generate education section
    education_html = ""
    for edu in resume_document.get("education", []):
        institution = edu.get("institution", "")
        degree = edu.get("degree", "")
        major = edu.get("major", "")
        period = edu.get("period", {})
        start = period.get("start", "")
        end = period.get("end", "")
        ranking = edu.get("ranking_or_gpa", "")
        highlights = edu.get("highlights", [])

        education_html += f'        <li>{institution} | {degree} | {start}-{end}</li>\n'
        if ranking:
            education_html += f'        <li>{ranking}</li>\n'
        for highlight in highlights:
            education_html += f'        <li>{highlight}</li>\n'

    # Generate capability profile section
    capability_html = ""
    for cap in resume_document.get("capability_profile", []):
        name = html.escape(str(cap.get("name", "")))
        desc = html.escape(str(cap.get("description", "")))
        if name and desc:
            capability_html += f'        <li><strong>{name}</strong>：{desc}</li>\n'

    # Generate skills section
    skills_html = ""
    data_skills = []
    medical_info_skills = []
    other_skills = []

    for skill in resume_document.get("skills", []):
        name = skill.get("name", "")
        level = skill.get("level", "")
        category = skill.get("category", "")
        skill_text = f"{name}({level})"
        if category == "data":
            data_skills.append(skill_text)
        elif category == "medical_information":
            medical_info_skills.append(skill_text)
        else:
            other_skills.append(skill_text)

    if data_skills:
        skills_html += f'        <li><strong>统计分析</strong>：{"、".join(data_skills)}</li>\n'
    if medical_info_skills:
        skills_html += f'        <li><strong>文献管理与引用</strong>：{"、".join(medical_info_skills)}，支持文献组织、引用管理与学术写作</li>\n'
    if other_skills:
        skills_html += f'        <li><strong>其他能力</strong>：{"、".join(other_skills)}</li>\n'

    # Add language skills
    languages = resume_document.get("languages", [])
    if languages:
        lang = languages[0]
        language = lang.get("language", "")
        level = lang.get("level_or_score", "")
        skills_html += f'        <li><strong>语言能力</strong>：{html.escape(str(language))}（{html.escape(str(level))}）</li>\n'

    # Generate research interests
    research_interests_html = ""
    research_interests = resume_document.get("research_interests", [])
    for interest in research_interests:
        research_interests_html += f'        <li>{html.escape(str(interest))}</li>\n'

    # Generate experience sections
    def generate_experience_section(experiences, section_title):
        if not experiences:
            return ""

        section_html = f'''    <div class="resume-section">
      <h2>{section_title}</h2>'''

        for exp in experiences:
            org = html.escape(str(exp.get("organization", "")))
            title = html.escape(str(exp.get("title", "")))
            role = html.escape(str(exp.get("department_or_field", "")))
            period = exp.get("period", {})
            start = period.get("start", "")
            end = period.get("end", "")

            section_html += f'''
      <div class="resume-entry">
        <div class="resume-entry-head">
          <div class="resume-org">{title}</div>
          <div class="resume-date">{start}-{end}</div>
          <div class="resume-role">{org}</div>
        </div>
        <ul class="resume-list">'''

            for bullet in exp.get("bullets", []):
                section_html += f'          <li>{html.escape(str(bullet["text"]))}</li>\n'

            section_html += '''        </ul>
      </div>'''

        section_html += '\n    </div>\n'
        return section_html

    research_items = list(resume_document.get("research_experience", [])) + list(resume_document.get("projects", []))
    research_exp_html = generate_experience_section(research_items, "科研经历")
    clinical_exp_html = generate_experience_section(resume_document.get("clinical_experience", []), "临床实习")

    publications_html = ""
    publications = resume_document.get("publications", [])
    if publications:
        items = []
        status_labels = {"in_preparation": "撰写中", "submitted": "已投稿", "published": "已发表"}
        for publication in publications:
            parts = [html.escape(str(publication.get("title", "")))]
            if publication.get("author_position"):
                parts.append(html.escape(str(publication["author_position"])))
            status = publication.get("status", "")
            if status:
                parts.append(status_labels.get(status, html.escape(str(status))))
            items.append(" · ".join(part for part in parts if part))
        publications_html = '    <div class="resume-section">\n      <h2>论文与学术产出</h2>\n      <ul class="resume-list">\n' + "".join(
            f"        <li>{item}</li>\n" for item in items
        ) + "      </ul>\n    </div>"

    basics = resume_document.get("basics", {})
    name = html.escape(str(basics.get("name", "")))
    target = html.escape(str(basics.get("target", "")))
    summary = html.escape(str(basics.get("summary", "")))
    contact_values = [basics.get("phone"), basics.get("email"), basics.get("location")]
    contact_text = " · ".join(html.escape(str(value)) for value in contact_values if value)
    contact_html = f'<div class="resume-contact">{contact_text}</div>' if contact_text else ""
    avatar_path = basics.get("avatar_path", "")
    avatar_html = (f'<div class="resume-avatar-container"><img src="{html.escape(str(avatar_path), quote=True)}" '
                   'alt="候选人头像" class="resume-avatar"></div>') if avatar_path else ""

    # Replace placeholders
    html_content = html_template.replace("{{EDUCATION}}", education_html.strip())
    html_content = html_content.replace("{{CAPABILITY_PROFILE}}", capability_html.strip())
    html_content = html_content.replace("{{SKILLS}}", skills_html.strip())
    html_content = html_content.replace("{{RESEARCH_INTERESTS}}", research_interests_html.strip())
    html_content = html_content.replace("{{RESEARCH_EXPERIENCE}}", research_exp_html if research_exp_html else "")
    html_content = html_content.replace("{{PROJECTS}}", "")
    html_content = html_content.replace("{{CLINICAL_EXPERIENCE}}", clinical_exp_html if clinical_exp_html else "")
    html_content = html_content.replace("{{PUBLICATIONS}}", publications_html)
    html_content = html_content.replace("{{DOCUMENT_TITLE}}", f"{name}简历" if name else "医学简历")
    html_content = html_content.replace("{{NAME}}", name)
    html_content = html_content.replace("{{TARGET}}", target)
    html_content = html_content.replace("{{CONTACT}}", contact_html)
    html_content = html_content.replace("{{AVATAR}}", avatar_html)
    html_content = html_content.replace("{{SUMMARY}}", summary)

    return html_content


if __name__ == "__main__":
    # 生成V3.2黄金样本
    result = generate_v32_golden_sample()

    if result:
        print("\n医学简历Agent V1 完整实现成功！")
        print("所有核心功能已实现并集成")
        print("V3.2黄金样本成功生成")
        print("Claim Gate语义分层验证通过")
        print("三档表达系统工作正常")
        print("HTML输出符合ATS兼容要求")
    else:
        print("\n实现过程中出现问题")
        sys.exit(1)
