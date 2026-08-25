from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, redirect, request, send_from_directory

from .adapters.json_career_repository import JsonCareerRepository
from .adapters.file_session_store import FileSessionStore
from .adapters.json_job_repository import JsonJobRepository
from .adapters.json_profile_repository import JsonMedicalProfileRepository
from .adapters.openai_compatible_model_gateway import (
    ModelGatewayError,
    OpenAICompatibleModelGateway,
)
from .application.career_explorer import CareerExplorationAgent
from .application.orchestrator import CareerTransitionAgent
from .ports.repositories import ModelGateway
from .services.career_target import CareerTargetService
from .services.career_explainer import (
    CareerExplanationService,
    ModelOutputRejectedError,
)
from .services.career_comparator import CareerComparator
from .services.profile_drafter import (
    ALLOWED_PROFILE_CAPABILITIES,
    ProfileDraftInputError,
    ProfileDraftOutputRejectedError,
    ProfileDraftService,
    confirmed_profile_from_payload,
)
from .services.resume_intake import ResumeIntakeService
from .services.resume_rewriter import (
    ResumeRewriteRejectedError,
    ResumeRewriteService,
    evidence_preserving_rewrite,
)
from .services.resume_reviewer import ResumeReviewService
from .services.resume_parser import extract_text_from_path
from .services.resume_structurer import ResumeStructurer
from .services.resume_translation import ResumeTranslationService
from .services.experience_draft import ExperienceDraftService
from .services.confirmation_gate import ConfirmationGateService
from .services.bullet_composer import BulletComposerService
from .services.claim_ledger import ClaimLedgerService
from .services.claim_gate import ClaimGateService
from .services.resume_conversation_agent import ResumeConversationAgent
from .services.conversation_model_gateway import ModelGatewayConversationGateway


def _model_gateway_from_environment() -> OpenAICompatibleModelGateway | None:
    base_url = os.environ.get("LLM_BASE_URL", "").strip()
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()
    if not all((base_url, api_key, model)):
        return None
    return OpenAICompatibleModelGateway(
        base_url=base_url,
        api_key=api_key,
        model=model,
    )


def _load_local_llm_environment(path: Path) -> None:
    if not path.exists():
        return
    allowed = {"LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in allowed and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def create_app(
    data_path: str | Path | None = None,
    *,
    profiles_path: str | Path | None = None,
    careers_path: str | Path | None = None,
    model_gateway: ModelGateway | None = None,
    load_model_from_environment: bool = True,
) -> Flask:
    app = Flask(__name__)
    root = Path(__file__).parents[2]
    path = Path(data_path) if data_path else root / "data" / "jobs.sample.json"
    jobs = JsonJobRepository(path)
    agent = CareerTransitionAgent(jobs)
    profiles = JsonMedicalProfileRepository(
        Path(profiles_path) if profiles_path else root / "data" / "profiles"
    )
    careers = JsonCareerRepository(
        Path(careers_path) if careers_path else root / "data" / "careers"
    )
    explorer = CareerExplorationAgent(profiles, careers)
    resume_intake = ResumeIntakeService()
    resume_reviewer = ResumeReviewService()
    resume_structurer = ResumeStructurer()
    resume_translator = ResumeTranslationService()
    experience_drafter = ExperienceDraftService()
    confirmation_gate = ConfirmationGateService()
    bullet_composer = BulletComposerService()
    claim_ledger = ClaimLedgerService(root / "data" / ".sessions")
    claim_gate = ClaimGateService()
    career_targets = CareerTargetService()
    gateway = model_gateway
    if gateway is None and load_model_from_environment:
        _load_local_llm_environment(root / ".env")
        gateway = _model_gateway_from_environment()
    explainer = CareerExplanationService(gateway) if gateway else None
    resume_rewriter = ResumeRewriteService(gateway) if gateway else None
    profile_drafter = ProfileDraftService(gateway) if gateway else None
    demo_directory = root / "demo"
    sessions = FileSessionStore(root / "data" / ".sessions")
    conversations = ResumeConversationAgent(
        sessions=sessions,
        experience_drafter=experience_drafter,
        confirmation_gate=confirmation_gate,
        bullet_composer=bullet_composer,
        claim_gate=claim_gate,
        claim_ledger=claim_ledger,
        language_gateway=ModelGatewayConversationGateway(gateway) if gateway else None,
    )

    def comparison_from_payload(payload: dict[str, object]):
        maximum_hypotheses = int(payload.get("maximum_hypotheses", 3))
        if "profile" in payload:
            profile = confirmed_profile_from_payload(payload["profile"])
            return explorer.compare_profile_record(
                profile=profile,
                maximum_hypotheses=maximum_hypotheses,
            )
        return explorer.compare_profile(
            profile_id=str(payload.get("profile_id", "")),
            maximum_hypotheses=maximum_hypotheses,
        )

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "scoring_version": "deterministic-v1",
            "career_comparison_version": "career-comparison-v0.1",
            "llm_configured": explainer is not None,
            "profile_drafting_configured": profile_drafter is not None,
        }

    @app.get("/")
    def launch_resume_beta():
        return redirect("/demo/resume-beta/index.html", code=302)

    @app.get("/api/jobs")
    def list_jobs():
        location = request.args.get("location")
        return jsonify([asdict(job) for job in jobs.list(location=location)])

    @app.get("/api/profiles")
    def list_profiles():
        return jsonify(
            [
                {
                    "profile_id": profile.profile_id,
                    "profile_type": profile.profile_type,
                    "education": {
                        "field": profile.education_field,
                        "stage": profile.education_stage,
                    },
                    "evidence_count": len(profile.evidence),
                    "locations": profile.constraints.locations,
                }
                for profile in profiles.list()
            ]
        )

    @app.post("/api/career-comparisons")
    def compare_careers():
        payload = request.get_json(silent=True) or {}
        try:
            run = comparison_from_payload(payload)
        except (TypeError, ValueError, LookupError, ProfileDraftInputError) as exc:
            return {"error": str(exc)}, 400
        return jsonify(run.to_dict())

    @app.post("/api/profile-drafts")
    def create_profile_draft():
        if profile_drafter is None:
            return {
                "error": (
                    "LLM is not configured; set LLM_BASE_URL, LLM_API_KEY, "
                    "and LLM_MODEL"
                )
            }, 503

        payload = request.get_json(silent=True) or {}
        try:
            constraints = payload.get("constraints", {})
            if not isinstance(constraints, dict):
                raise ProfileDraftInputError("constraints must be an object")
            locations = constraints.get("locations", [])
            non_negotiables = constraints.get("non_negotiables", [])
            if not isinstance(locations, list) or not isinstance(
                non_negotiables, list
            ):
                raise ProfileDraftInputError(
                    "locations and non_negotiables must be arrays"
                )
            weekly_learning_hours = constraints.get("weekly_learning_hours")
            if weekly_learning_hours in (None, ""):
                weekly_learning_hours = None
            else:
                weekly_learning_hours = float(weekly_learning_hours)
            draft = profile_drafter.draft(
                education_field=str(payload.get("education_field", "")),
                education_stage=str(payload.get("education_stage", "")),
                experience_text=str(payload.get("experience_text", "")),
                locations=tuple(locations),
                weekly_learning_hours=weekly_learning_hours,
                non_negotiables=tuple(non_negotiables),
                consent_confirmed=payload.get("consent_confirmed") is True,
            )
        except (TypeError, ValueError, ProfileDraftInputError) as exc:
            return {"error": str(exc)}, 400
        except (ModelGatewayError, ProfileDraftOutputRejectedError) as exc:
            return {"error": str(exc)}, 502
        return jsonify(
            {
                "profile_draft": draft.to_dict(),
                "allowed_capabilities": ALLOWED_PROFILE_CAPABILITIES,
                "privacy": {
                    "persisted_by_backend": False,
                    "sent_to_configured_model": True,
                },
            }
        )

    @app.post("/api/career-explanations")
    def explain_careers():
        if explainer is None:
            return {
                "error": (
                    "LLM is not configured; set LLM_BASE_URL, LLM_API_KEY, "
                    "and LLM_MODEL"
                )
            }, 503

        payload = request.get_json(silent=True) or {}
        try:
            run = comparison_from_payload(payload)
            explanation = explainer.explain(run)
        except (TypeError, ValueError, LookupError, ProfileDraftInputError) as exc:
            return {"error": str(exc)}, 400
        except (ModelGatewayError, ModelOutputRejectedError) as exc:
            return {"error": str(exc)}, 502
        return jsonify(
            {
                "comparison": run.to_dict(),
                "explanation": explanation.to_dict(),
            }
        )

    def resume_target_text(payload: dict[str, object]) -> str:
        jd_text = str(payload.get("jd_text", "")).strip()
        if jd_text:
            return jd_text
        career_id = str(payload.get("career_id", "")).strip()
        if not career_id:
            raise ValueError("provide career_id or jd_text")
        return career_targets.build(careers.get(career_id)).generated_jd_text

    @app.get("/api/career-targets/<career_id>")
    def get_career_target(career_id: str):
        try:
            target = career_targets.build(careers.get(career_id))
        except (LookupError, ValueError) as exc:
            return {"error": str(exc)}, 404
        return jsonify(target.to_dict())

    @app.post("/api/resume-intake")
    def analyze_resume_intake():
        payload = request.get_json(silent=True) or {}
        try:
            result = resume_intake.analyze(
                resume_text=str(payload.get("resume_text", "")),
                jd_text=resume_target_text(payload),
            )
        except (ValueError, LookupError) as exc:
            return {"error": str(exc)}, 400
        return jsonify(result.to_dict())

    @app.post("/api/resume-rewrites")
    def rewrite_resume():
        payload = request.get_json(silent=True) or {}
        try:
            intake = resume_intake.analyze(
                resume_text=str(payload.get("resume_text", "")),
                jd_text=resume_target_text(payload),
            )
            facts = tuple(str(item) for item in payload.get("confirmed_facts", []))
            result = (
                resume_rewriter.rewrite(intake=intake, confirmed_facts=facts)
                if resume_rewriter
                else evidence_preserving_rewrite(intake)
            )
        except (TypeError, ValueError) as exc:
            return {"error": str(exc)}, 400
        except (ModelGatewayError, ResumeRewriteRejectedError) as exc:
            return {"error": str(exc)}, 502
        return jsonify(result.to_dict())

    @app.post("/api/resume-structures")
    def structure_resume():
        """Return imported evidence grouped by explicit medical-resume headings.

        This endpoint is local, deterministic, and intentionally returns
        extracted candidates rather than automatically confirmed resume facts.
        """
        payload = request.get_json(silent=True) or {}
        try:
            result = resume_structurer.structure(
                resume_text=str(payload.get("resume_text", ""))
            )
        except ValueError as exc:
            return {"error": str(exc)}, 400
        return jsonify(result.to_dict())

    @app.post("/api/experience-drafts")
    def draft_experience():
        """Extract facts from a raw experience text and provide guidance."""
        payload = request.get_json(silent=True) or {}
        try:
            result = experience_drafter.draft(
                experience_text=str(payload.get("experience_text", "")),
                context_hint=payload.get("context_hint"),
                consent_confirmed=payload.get("consent_confirmed") is True,
            )
        except ValueError as exc:
            return {"error": str(exc)}, 400
        return jsonify(result.to_dict())

    @app.post("/api/experience-confirmations")
    def confirm_experience():
        """Confirm, modify, or reject an experience draft to create canonical experience."""
        payload = request.get_json(silent=True) or {}
        try:
            result = confirmation_gate.confirm_experience(
                experience_draft=payload.get("experience_draft", {}),
                user_actions=payload.get("user_actions", {}),
                evidence_records=payload.get("evidence_records", []),
                previous_experience_id=payload.get("previous_experience_id"),
            )
        except ValueError as exc:
            return {"error": str(exc)}, 400
        return jsonify(result.to_dict())

    @app.post("/api/bullet-composer")
    def compose_bullets():
        """Generate 1-3 bullet claims from canonical experience for a specific role pack."""
        payload = request.get_json(silent=True) or {}
        try:
            result = bullet_composer.compose_bullets(
                canonical_experience=payload.get("canonical_experience", {}),
                role_pack_name=str(payload.get("role_pack_name", "")),
            )
            return jsonify([bullet.to_dict() for bullet in result])
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.post("/api/claim-ledger/record")
    def record_claim():
        """Record a bullet claim in the ledger with audit trail."""
        payload = request.get_json(silent=True) or {}
        try:
            session_id = str(payload.get("session_id", ""))
            if not session_id:
                return {"error": "session_id is required"}, 400

            bullet_claim = payload.get("bullet_claim", {})
            gate_status = str(payload.get("gate_status", ""))
            user_disposition = payload.get("user_disposition")

            if not bullet_claim:
                return {"error": "bullet_claim is required"}, 400
            if not gate_status:
                return {"error": "gate_status is required"}, 400

            result = claim_ledger.record_claim(
                session_id=session_id,
                bullet_claim=bullet_claim,
                gate_status=gate_status,
                user_disposition=user_disposition,
            )
            return jsonify(result.to_dict())
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.get("/api/claim-ledger/session/<session_id>")
    def get_session_claims(session_id: str):
        """Get all claims for a session."""
        try:
            claims = claim_ledger.get_session_claims(session_id)
            return jsonify([claim.to_dict() for claim in claims])
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.get("/api/claim-ledger/claim/<session_id>/<claim_id>")
    def get_claim(session_id: str, claim_id: str):
        """Get a specific claim by ID."""
        try:
            claim = claim_ledger.get_claim(session_id, claim_id)
            if claim is None:
                return {"error": "claim not found"}, 404
            return jsonify(claim.to_dict())
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.get("/api/claim-ledger/experience/<session_id>/<experience_id>")
    def get_experience_claims(session_id: str, experience_id: str):
        """Get all valid claims for a specific experience."""
        try:
            claims = claim_ledger.get_valid_claims_for_experience(session_id, experience_id)
            return jsonify([claim.to_dict() for claim in claims])
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.get("/api/claim-ledger/role-pack/<session_id>/<role_pack>")
    def get_role_pack_claims(session_id: str, role_pack: str):
        """Get all valid claims for a specific role pack."""
        try:
            claims = claim_ledger.get_valid_claims_for_role_pack(session_id, role_pack)
            return jsonify([claim.to_dict() for claim in claims])
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.post("/api/claim-ledger/invalidate/experience")
    def invalidate_experience_claims():
        """Invalidate all claims for a specific experience."""
        payload = request.get_json(silent=True) or {}
        try:
            session_id = str(payload.get("session_id", ""))
            experience_id = str(payload.get("experience_id", ""))
            reason = str(payload.get("reason", "experience_superseded"))

            if not session_id:
                return {"error": "session_id is required"}, 400
            if not experience_id:
                return {"error": "experience_id is required"}, 400

            invalidated_ids = claim_ledger.invalidate_claims_by_experience(
                session_id=session_id,
                experience_id=experience_id,
                reason=reason,
            )
            return jsonify({"invalidated_claim_ids": invalidated_ids})
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.post("/api/claim-ledger/invalidate/claims")
    def invalidate_specific_claims():
        """Invalidate specific claims by their IDs."""
        payload = request.get_json(silent=True) or {}
        try:
            session_id = str(payload.get("session_id", ""))
            claim_ids = payload.get("claim_ids", [])
            reason = str(payload.get("reason", "user_rejected"))

            if not session_id:
                return {"error": "session_id is required"}, 400
            if not isinstance(claim_ids, list) or not claim_ids:
                return {"error": "claim_ids must be a non-empty array"}, 400

            invalidated_ids = claim_ledger.invalidate_claims_by_ids(
                session_id=session_id,
                claim_ids=claim_ids,
                reason=reason,
            )
            return jsonify({"invalidated_claim_ids": invalidated_ids})
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.get("/api/claim-ledger/invalidated/<session_id>")
    def get_invalidated_claims(session_id: str):
        """Get all invalidated claims for a session."""
        try:
            claims = claim_ledger.get_invalidated_claims(session_id)
            return jsonify([claim.to_dict() for claim in claims])
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.post("/api/claim-gate")
    def validate_claim():
        """Validate a bullet claim against twelve deterministic checks."""
        payload = request.get_json(silent=True) or {}
        try:
            result = claim_gate.validate_claim(
                bullet_claim=payload.get("bullet_claim", {}),
                canonical_experience=payload.get("canonical_experience", {}),
            )
            return jsonify(result.to_dict())
        except ValueError as exc:
            return {"error": str(exc)}, 400

    @app.post("/api/resume-translations")
    def translate_resume_capabilities():
        payload = request.get_json(silent=True) or {}
        try:
            result = resume_translator.translate(
                resume_document=payload.get("resume_document", {}),
                jd_text=str(payload.get("jd_text", "")),
                target_profile=str(payload.get("target_profile", "clinical_research")),
            )
        except ValueError as exc:
            return {"error": str(exc)}, 400
        return jsonify(result.to_dict())

    @app.post("/api/resume-reviews")
    def review_resume():
        payload = request.get_json(silent=True) or {}
        try:
            intake = resume_intake.analyze(
                resume_text=str(payload.get("resume_text", "")),
                jd_text=resume_target_text(payload),
            )
            facts = tuple(str(item) for item in payload.get("confirmed_facts", []))
            result = resume_reviewer.review(
                intake=intake,
                final_resume_text=str(payload.get("final_resume_text", "")),
                confirmed_facts=facts,
            )
        except (TypeError, ValueError) as exc:
            return {"error": str(exc)}, 400
        return jsonify(result.to_dict())

    @app.post("/api/matches")
    def match_resume():
        payload = request.get_json(silent=True) or {}
        try:
            run = agent.match_resume(
                resume_text=str(payload.get("resume_text", "")),
                job_id=str(payload.get("job_id", "")),
            )
        except (ValueError, LookupError) as exc:
            return {"error": str(exc)}, 400
        return jsonify(run.to_dict())

    @app.post("/api/resume-beta/analyze")
    def analyze_resume_for_jd():
        payload = request.get_json(silent=True) or {}
        try:
            run = agent.match_custom_jd(
                resume_text=str(payload.get("resume_text", "")),
                jd_text=str(payload.get("jd_text", "")),
                title=str(payload.get("title", "")),
            )
        except ValueError as exc:
            return {"error": str(exc)}, 400
        return jsonify(run.to_dict())

    @app.post("/api/conversations")
    def create_conversation():
        """Create a persistent bounded resume-conversation session."""
        payload = request.get_json(silent=True) or {}
        session_id = str(payload.get("session_id", "")).strip() or None
        try:
            conversation = conversations.create(session_id)
        except (FileExistsError, ValueError) as exc:
            return {"error": str(exc)}, 409
        return jsonify(conversation), 201

    @app.get("/api/conversations/<session_id>")
    def get_conversation(session_id: str):
        try:
            return jsonify(conversations.read(session_id))
        except (LookupError, ValueError) as exc:
            return {"error": str(exc)}, 404

    @app.post("/api/conversations/<session_id>/messages")
    def post_conversation_message(session_id: str):
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return {"error": "message must be an object"}, 400
        try:
            return jsonify(conversations.handle_message(session_id, payload))
        except (LookupError, ValueError) as exc:
            return {"error": str(exc)}, 400

    @app.get("/api/sessions")
    def list_sessions():
        return jsonify(sessions.list_sessions())

    @app.post("/api/sessions")
    def create_session():
        payload = request.get_json(silent=True) or {}
        session_id = str(payload.get("session_id", "")).strip() or None
        try:
            created = sessions.create(session_id=session_id)
        except (FileExistsError, ValueError) as exc:
            return {"error": str(exc)}, 409
        return jsonify({"session_id": created}), 201

    @app.get("/api/sessions/<session_id>")
    def read_session(session_id: str):
        try:
            return jsonify(sessions.get(session_id))
        except (LookupError, ValueError) as exc:
            return {"error": str(exc)}, 404

    @app.patch("/api/sessions/<session_id>")
    def update_session(session_id: str):
        payload = request.get_json(silent=True) or {}
        state = payload.get("state")
        if not isinstance(state, dict):
            return {"error": "state must be an object"}, 400
        try:
            return jsonify(sessions.update(session_id, state=state))
        except (LookupError, ValueError) as exc:
            return {"error": str(exc)}, 404

    @app.post("/api/sessions/<session_id>/events")
    def append_session_event(session_id: str):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return {"error": "event must be an object"}, 400
        try:
            return jsonify(sessions.append_event(session_id, payload))
        except (LookupError, ValueError) as exc:
            return {"error": str(exc)}, 404

    @app.post("/api/resume/upload")
    def upload_resume():
        uploaded = request.files.get("file")
        if not uploaded:
            return {"error": "please provide file field"}, 400
        extension = Path(uploaded.filename or "").suffix.lower()
        if extension not in {".txt", ".md", ".docx", ".pdf"}:
            return {"error": "unsupported extension"}, 400
        upload_directory = root / "data" / ".uploads"
        upload_directory.mkdir(parents=True, exist_ok=True)
        temporary_path = upload_directory / f"{uuid4().hex}{extension}"
        uploaded.save(str(temporary_path))
        try:
            resume_text = extract_text_from_path(temporary_path)
        except (RuntimeError, ValueError, OSError) as exc:
            return {"error": str(exc)}, 400
        finally:
            temporary_path.unlink(missing_ok=True)
        return jsonify({"resume_text": resume_text})

    @app.get("/demo/")
    def journey_demo():
        return send_from_directory(demo_directory / "journey", "index.html")

    @app.get("/demo/<path:filename>")
    def demo_asset(filename: str):
        return send_from_directory(demo_directory, filename)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)
