from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .adapters.openai_compatible_model_gateway import (
    ModelGatewayError,
    OpenAICompatibleModelGateway,
)
from .ports import ModelGateway
from .services.resume_intake import ResumeIntakeService
from .services.resume_reviewer import ResumeReviewService
from .services.resume_rewriter import (
    ResumeRewriteRejectedError,
    ResumeRewriteService,
    evidence_preserving_rewrite,
)


def _load_local_llm_environment(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() in {"LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"}:
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _model_from_environment() -> OpenAICompatibleModelGateway | None:
    values = {key: os.environ.get(key, "").strip() for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")}
    if not all(values.values()):
        return None
    return OpenAICompatibleModelGateway(
        base_url=values["LLM_BASE_URL"], api_key=values["LLM_API_KEY"], model=values["LLM_MODEL"]
    )


def create_app(*, model_gateway: ModelGateway | None = None, load_model_from_environment: bool = True) -> Flask:
    app = Flask(__name__)
    root = Path(__file__).parents[2]
    if load_model_from_environment:
        _load_local_llm_environment(root / ".env")
    gateway = model_gateway or _model_from_environment()
    intake_service = ResumeIntakeService()
    rewrite_service = ResumeRewriteService(gateway) if gateway else None
    review_service = ResumeReviewService()
    demo_directory = root / "demo" / "resume-beta"

    @app.get("/api/health")
    def health():
        return {"status": "ok", "llm_configured": rewrite_service is not None}

    @app.post("/api/resume-intake")
    def analyze_resume_intake():
        payload = request.get_json(silent=True) or {}
        try:
            result = intake_service.analyze(
                resume_text=str(payload.get("resume_text", "")), jd_text=str(payload.get("jd_text", ""))
            )
        except ValueError as exc:
            return {"error": str(exc)}, 400
        return jsonify(result.to_dict())

    @app.post("/api/resume-rewrites")
    def rewrite_resume():
        payload = request.get_json(silent=True) or {}
        try:
            intake = intake_service.analyze(
                resume_text=str(payload.get("resume_text", "")), jd_text=str(payload.get("jd_text", ""))
            )
            facts = tuple(str(item) for item in payload.get("confirmed_facts", []))
            result = rewrite_service.rewrite(intake=intake, confirmed_facts=facts) if rewrite_service else evidence_preserving_rewrite(intake)
        except (TypeError, ValueError) as exc:
            return {"error": str(exc)}, 400
        except (ModelGatewayError, ResumeRewriteRejectedError) as exc:
            return {"error": str(exc)}, 502
        return jsonify(result.to_dict())

    @app.post("/api/resume-reviews")
    def review_resume():
        payload = request.get_json(silent=True) or {}
        try:
            intake = intake_service.analyze(
                resume_text=str(payload.get("resume_text", "")), jd_text=str(payload.get("jd_text", ""))
            )
            facts = tuple(str(item) for item in payload.get("confirmed_facts", []))
            result = review_service.review(
                intake=intake, final_resume_text=str(payload.get("final_resume_text", "")), confirmed_facts=facts
            )
        except (TypeError, ValueError) as exc:
            return {"error": str(exc)}, 400
        return jsonify(result.to_dict())

    @app.get("/")
    def resume_demo():
        return send_from_directory(demo_directory, "index.html")

    @app.get("/<path:filename>")
    def resume_asset(filename: str):
        return send_from_directory(demo_directory, filename)

    return app
