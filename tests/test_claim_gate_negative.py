import sys
import unittest
from pathlib import Path
import re

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.services.bullet_composer import BulletComposerService, BulletClaim


class ClaimGateNegativeTest(unittest.TestCase):
    """Negative tests for Claim Gate validation focusing on authenticity violations.

    These tests verify that the system properly prevents or flags common authenticity
    violations when generating bullet claims from canonical experiences.
    """

    def setUp(self):
        self.composer = BulletComposerService()

    def test_prisma_false_method_injection(self):
        """Test that PRISMA methodology is not falsely claimed without proper evidence."""
        # Create canonical experience without PRISMA methodology confirmed
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_001",
            "evidence_ids": ["ev_001"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies"],
            "methods": ["systematic_review"],  # Only systematic review, not PRISMA
            "tools": [],
            "objects": ["medical_literature"],
            "collaboration": ["research_team"],
            "artifacts": ["prisma_flowchart"],  # Has flowchart artifact but no PRISMA method
            "outcomes": [],
            "scope": {},
            "unknowns": ["database_count", "screening_criteria"],  # Screening criteria unknown
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="doctoral_v1"
        )

        # Verify no bullet falsely claims PRISMA methodology
        for bullet in bullets:
            self.assertNotIn("PRISMA", bullet.wording)
            self.assertNotIn("遵循PRISMA", bullet.wording)
            self.assertNotIn("按照PRISMA", bullet.wording)

    def test_unconfirmed_database_tool_injection(self):
        """Test that specific databases are not claimed without confirmation."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_002",
            "evidence_ids": ["ev_002"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "tools": [],  # No tools confirmed
            "objects": ["medical_literature"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknowns": ["database_count"],  # Database count explicitly unknown
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="doctoral_v1"
        )

        # Verify no specific databases are mentioned
        forbidden_databases = ["PubMed", "Embase", "Cochrane", "Web of Science", "CNKI", "万方", "维普"]
        for bullet in bullets:
            for db in forbidden_databases:
                self.assertNotIn(db, bullet.wording)

    def test_fake_statistical_numbers_injection(self):
        """Test that fabricated statistical results are not generated."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_003",
            "evidence_ids": ["ev_003"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["analyze_data"],
            "methods": ["statistical_analysis"],
            "tools": ["r"],
            "objects": ["clinical_data"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],  # No outcomes confirmed
            "scope": {},  # No numerical scope confirmed
            "unknowns": ["project_outcomes", "study_count"],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="health_ai_data_v1"
        )

        # Verify no fabricated statistical numbers appear
        number_patterns = [
            r"\d+%",                    # Percentages
            r"p\s*<\s*0\.\d+",         # P-values
            r"[OR|HR|RR]\s*=\s*\d+\.\d+", # Odds ratios, hazard ratios
            r"\d+\s*例",               # Number of cases
            r"\d+\s*篇",               # Number of papers
            r"\d+\s*患者",             # Number of patients
            r"\d+\.\d+\s*%",           # Decimal percentages
        ]

        for bullet in bullets:
            for pattern in number_patterns:
                match = re.search(pattern, bullet.wording)
                if match:
                    self.fail(f"Bullet contains fabricated numbers: '{bullet.wording}' (matched: {match.group()})")

    def test_responsibility_upgrade_independent(self):
        """Test that 'independent' responsibility is not falsely claimed."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_004",
            "evidence_ids": ["ev_004"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},  # Only participated
            "actions": ["retrieve_literature", "screen_studies"],
            "methods": ["systematic_review"],
            "tools": [],
            "objects": ["medical_literature"],
            "collaboration": ["research_team"],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknowns": ["specific_responsibilities"],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="doctoral_v1"
        )

        # Verify no independent responsibility claims
        forbidden_independent_phrases = ["独立", "独自", "solely", "independently", "自主"]
        for bullet in bullets:
            for phrase in forbidden_independent_phrases:
                self.assertNotIn(phrase, bullet.wording)

    def test_responsibility_upgrade_leading(self):
        """Test that 'leading/dominating' responsibility is not falsely claimed."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_005",
            "evidence_ids": ["ev_005"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "owned_component"},  # Component owner only
            "actions": ["analyze_data", "interpret_results"],
            "methods": ["statistical_analysis"],
            "tools": ["r"],
            "objects": ["clinical_data"],
            "collaboration": ["supervisor"],
            "artifacts": ["data_extraction_sheet"],
            "outcomes": [],
            "scope": {},
            "unknowns": [],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="clinical_research_v1"
        )

        # Verify no leading/dominating responsibility claims
        forbidden_leading_phrases = ["主导", "领导", "带领", "manage", "lead", "direct"]
        for bullet in bullets:
            for phrase in forbidden_leading_phrases:
                self.assertNotIn(phrase, bullet.wording)

    def test_fake_business_impact_outcomes(self):
        """Test that fabricated business impact outcomes are not generated."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_006",
            "evidence_ids": ["ev_006"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "tools": [],
            "objects": ["medical_literature"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],  # No outcomes confirmed
            "scope": {},
            "unknowns": ["publication_status", "project_outcomes"],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="medical_affairs_v1"
        )

        # Verify no fabricated business impact claims
        forbidden_impact_phrases = [
            "提升效率", "降低成本", "增加收入", "改善患者预后",
            "优化流程", "enhanced efficiency", "reduced cost", "improved outcomes"
        ]
        for bullet in bullets:
            for phrase in forbidden_impact_phrases:
                self.assertNotIn(phrase, bullet.wording)

    def test_disguised_role_value_as_factual_outcomes(self):
        """Test that role value statements are not disguised as factual outcomes."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_007",
            "evidence_ids": ["ev_007"],
            "context": {"domain": "data_analysis", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["analyze_data"],
            "methods": ["statistical_analysis"],
            "tools": ["python"],
            "objects": ["research_data"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],  # No outcomes confirmed
            "scope": {},
            "unknowns": ["project_outcomes"],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="health_ai_data_v1"
        )

        # Verify no role value disguised as outcomes
        role_value_phrases = [
            "体现", "展现", "证明", "demonstrates", "shows", "proves", "highlights"
        ]
        for bullet in bullets:
            # Allow these phrases only if they refer to actual confirmed facts
            # But since we have no confirmed outcomes, they shouldn't appear
            for phrase in role_value_phrases:
                if phrase in bullet.wording:
                    # If the phrase appears, it should be followed by actual confirmed activities
                    # not fabricated capabilities
                    self.assertTrue(
                        any(activity in bullet.wording for activity in ["数据分析", "统计分析", "文献检索"]),
                        f"Role value phrase '{phrase}' should reference actual activities: {bullet.wording}"
                    )

    def test_meta_analysis_without_confirmation(self):
        """Test that Meta-analysis is not falsely claimed without proper evidence."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_008",
            "evidence_ids": ["ev_008"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature", "screen_studies"],
            "methods": ["systematic_review"],  # Only systematic review, not meta-analysis
            "tools": [],
            "objects": ["medical_literature"],
            "collaboration": ["research_team"],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknowns": ["study_count", "statistical_methods"],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="doctoral_v1"
        )

        # Verify no false Meta-analysis claims
        for bullet in bullets:
            self.assertNotIn("Meta分析", bullet.wording)
            self.assertNotIn("荟萃分析", bullet.wording)
            self.assertNotIn("meta-analysis", bullet.wording)

    def test_unconfirmed_software_tools(self):
        """Test that specific software tools are not claimed without confirmation."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_009",
            "evidence_ids": ["ev_009"],
            "context": {"domain": "data_analysis", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["analyze_data"],
            "methods": ["statistical_analysis"],
            "tools": [],  # No tools confirmed
            "objects": ["research_data"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknowns": ["software_used"],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="health_ai_data_v1"
        )

        # Verify no specific software tools are mentioned
        forbidden_tools = ["SPSS", "Stata", "SAS", "RevMan", "EndNote", "NoteExpress"]
        for bullet in bullets:
            for tool in forbidden_tools:
                self.assertNotIn(tool, bullet.wording)

    def test_fabricated_publication_outcomes(self):
        """Test that publication outcomes are not fabricated."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_010",
            "evidence_ids": ["ev_010"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["write_manuscript"],
            "methods": ["systematic_review"],
            "tools": [],
            "objects": ["research_paper"],
            "collaboration": ["research_team"],
            "artifacts": ["research_paper"],
            "outcomes": [],  # No publication status confirmed
            "scope": {},
            "unknowns": ["publication_status"],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="doctoral_v1"
        )

        # Verify no fabricated publication claims
        forbidden_publication_phrases = [
            "已发表", "published", "accepted", "in press", "录用", "SCI", "核心期刊"
        ]
        for bullet in bullets:
            for phrase in forbidden_publication_phrases:
                self.assertNotIn(phrase, bullet.wording)

    def test_exaggerated_scope_claims(self):
        """Test that scope/exaggerated scale claims are not fabricated."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_011",
            "evidence_ids": ["ev_011"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["screen_studies"],
            "methods": ["systematic_review"],
            "tools": [],
            "objects": ["clinical_studies"],
            "collaboration": [],
            "artifacts": [],
            "outcomes": [],
            "scope": {},  # No scope confirmed
            "unknowns": ["study_count"],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="clinical_research_v1"
        )

        # Verify no exaggerated scope claims
        scope_patterns = [
            r"上千", r"数百", r"hundreds of", r"thousands of",
            r"\d{3,}\s*篇", r"\d{3,}\s*研究"  # 3+ digit numbers
        ]
        for bullet in bullets:
            for pattern in scope_patterns:
                self.assertIsNone(re.search(pattern, bullet.wording))

    def test_invalid_responsibility_level_combinations(self):
        """Test that responsibility levels are not combined inappropriately."""
        canonical_experience = {
            "schema_version": "canonical-experience-v1",
            "experience_id": "exp_012",
            "evidence_ids": ["ev_012"],
            "context": {"domain": "clinical_research", "setting": "research_project", "topic": None},
            "role": {"title": None, "responsibility_level": "participated"},
            "actions": ["retrieve_literature"],
            "methods": ["systematic_review"],
            "tools": [],
            "objects": ["medical_literature"],
            "collaboration": ["research_team"],
            "artifacts": [],
            "outcomes": [],
            "scope": {},
            "unknowns": [],
            "status": "user_confirmed"
        }

        bullets = self.composer.compose_bullets(
            canonical_experience=canonical_experience,
            role_pack_name="doctoral_v1"
        )

        # Verify that participated-level experience doesn't use higher-level verbs
        high_level_verbs = ["主导", "独立", "负责整体", "管理", "领导"]
        for bullet in bullets:
            for verb in high_level_verbs:
                self.assertNotIn(verb, bullet.wording)


if __name__ == "__main__":
    unittest.main()