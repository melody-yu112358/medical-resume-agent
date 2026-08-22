from __future__ import annotations

from ..domain.models import CareerRun
from ..ports.repositories import JobRepository
from ..services.evidence_matcher import EvidenceMatcher
from ..services.resume_diagnostor import ResumeDiagnostor
from ..services.jd_analyzer import JdAnalyzer


class CareerTransitionAgent:
    """PAEG-inspired diagnose -> retrieve -> evaluate -> adapt workflow."""

    def __init__(
        self,
        jobs: JobRepository,
        diagnostor: ResumeDiagnostor | None = None,
        evaluator: EvidenceMatcher | None = None,
        jd_analyzer: JdAnalyzer | None = None,
    ) -> None:
        self.jobs = jobs
        self.diagnostor = diagnostor or ResumeDiagnostor()
        self.evaluator = evaluator or EvidenceMatcher()
        self.jd_analyzer = jd_analyzer or JdAnalyzer()

    def match_resume(self, *, resume_text: str, job_id: str) -> CareerRun:
        if not resume_text.strip():
            raise ValueError("resume_text cannot be empty")

        trace = ["diagnose_resume"]
        profile = self.diagnostor.diagnose(resume_text)
        trace.append("retrieve_job")
        job = self.jobs.get(job_id)
        trace.append("evaluate_evidence")
        report = self.evaluator.evaluate(profile, job)
        trace.append("propose_next_actions")
        return CareerRun(profile=profile, job=job, report=report, trace=tuple(trace))

    def match_custom_jd(
        self, *, resume_text: str, jd_text: str, title: str = ""
    ) -> CareerRun:
        if not resume_text.strip():
            raise ValueError("resume_text cannot be empty")
        trace = ["diagnose_resume"]
        profile = self.diagnostor.diagnose(resume_text)
        trace.append("analyze_user_jd")
        job = self.jd_analyzer.analyze(jd_text=jd_text, title=title)
        trace.append("evaluate_evidence")
        report = self.evaluator.evaluate(profile, job)
        trace.append("ask_for_missing_facts")
        return CareerRun(profile=profile, job=job, report=report, trace=tuple(trace))

