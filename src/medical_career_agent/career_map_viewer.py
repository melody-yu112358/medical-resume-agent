"""Standalone loopback-only, read-only explorer for the synthetic knowledge pilot."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlencode

from flask import Flask, abort, render_template, request, send_from_directory

from .services.career_card_explanation import CareerCardExplanationService


ROOT = Path(__file__).resolve().parents[2]
PROFILE_SET = ROOT / "data/career-map/career-card-explanation-test-profiles-v1.json"
DIMENSIONS = (("function_families", "function_family_id", "职能族 · 做什么"),
              ("ecosystems", "ecosystem_id", "产业生态 · 在哪里"),
              ("lifecycle_stages", "lifecycle_stage_id", "生命周期 · 可选阶段"))
LIFECYCLE_LABELS = {"mapped": "已标注", "pending": "待确认", "not_applicable": "不适用（已审核）"}
LABELS = {"direct": "直接支持", "transferable": "可迁移", "partial": "部分支持",
          "gap": "当前无证据", "unsupported": "禁止推断边界"}
CLAIMS = {"stable_responsibility": "稳定职责", "typical_deliverable": "典型交付物",
          "entry_requirement": "岗位要求", "transferable_direct": "直接支持的经历",
          "transferable": "可迁移经历", "transferable_partial": "部分可迁移经历",
          "explicit_gap": "需核验的缺口", "jd_dependent_scope": "依赖具体 JD 的责任",
          "validation_action": "投递前核验"}


def matches_filters(entry, selections, exclude=None):
    """OR within each dimension, AND across dimensions; no inferred joint scenario."""
    return all(table == exclude or not codes or set(codes).intersection(x["code"] for x in entry[table])
               for table, codes in selections.items())


@contextmanager
def read_database(path):
    connection = sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")
        yield connection
    finally:
        connection.close()


def create_viewer(database_path):
    database_path = Path(database_path).resolve()
    if not database_path.is_file():
        raise ValueError("知识库不存在。请先运行 scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite")
    with read_database(database_path) as db:
        if db.execute("PRAGMA user_version").fetchone()[0] != 4:
            raise ValueError("知识库版本不兼容，请先重新运行导入脚本。")
    profiles = json.loads(PROFILE_SET.read_text(encoding="utf-8"))["profiles"]
    profiles = {p["profile_id"]: p for p in profiles if p["profile_type"] == "synthetic"}
    app = Flask(__name__, template_folder="assets", static_folder=None)

    @app.before_request
    def local_only():
        # This launcher is not a public deployment or a real-profile API.
        if request.remote_addr not in {"127.0.0.1", "::1"}:
            abort(403)
        if request.host.split(":", 1)[0] not in {"127.0.0.1", "localhost"}:
            abort(403)
        if request.method not in {"GET", "HEAD"}:
            abort(405)

    @app.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    @app.get("/assets/career-map-filters.js")
    def filter_script():
        return send_from_directory(Path(__file__).parent / "assets", "career_map_filters.js")

    @app.get("/")
    def index():
        allowed = {"role", "profile", *(dim[0] for dim in DIMENSIONS)}
        if set(request.args) - allowed or any(len(request.args.getlist(k)) > 1 for k in ("role", "profile")):
            abort(400, "仅支持页面提供的职业、虚构档案与分类选项。")
        selections = {t: sorted(set(filter(None, request.args.getlist(t)))) for t, _, _ in DIMENSIONS}
        role = request.args.get("role")
        profile_id = request.args.get("profile")
        if profile_id and profile_id not in profiles:
            abort(400, "请选择已有虚构档案。")
        with read_database(database_path) as db:
            snapshot = db.execute("SELECT * FROM knowledge_snapshots WHERE is_current = 1").fetchone()
            if snapshot is None:
                abort(503, "没有当前知识快照，请先运行导入脚本。")
            manifest = json.loads(snapshot["manifest_json"])
            # Read metadata from the pinned taxonomy artifact, never a possibly newer disk file.
            taxonomy = json.loads(db.execute("SELECT raw_content FROM source_artifacts WHERE artifact_id=?",
                                            (manifest["taxonomy_revision"],)).fetchone()[0])
            assignments = {a.get("role_pack", a.get("external_key")): a for a in
                           taxonomy["canonical_role_pack_taxonomy"] + taxonomy["jd_driven_directions"] + taxonomy["beta_directions"]}
            entries = [dict(row) for row in db.execute("SELECT * FROM career_map_entries ORDER BY label")]
            options = {}
            for table, key, title in DIMENSIONS:
                options[table] = [dict(row) for row in db.execute(f"SELECT code, label FROM {table} ORDER BY label")]
                if set(selections[table]) - {x["code"] for x in options[table]}:
                    abort(400, "未知职业地图分类。")
                for entry in entries:
                    prefix, identifier = ("role", "role_pack_version_id") if entry["service_mode"] == "canonical_role_pack" else ("career_direction", "career_direction_id")
                    entry[table] = [dict(row) for row in db.execute(
                        f"SELECT t.code, t.label FROM {table} t JOIN {prefix}_{table} r ON t.{key}=r.{key} WHERE r.{identifier}=? ORDER BY t.label", (entry["entry_id"],))]
            cards = {row["role_pack_version_id"]: dict(row) for row in db.execute("SELECT * FROM career_cards WHERE is_current=1")}
            supported = {ref["career_card_version_id"] for ref in manifest["match_rule_revisions"]}
            for entry in entries:
                assignment = assignments.get(entry["external_key"], {})
                entry["lifecycle_applicability"] = assignment.get("lifecycle_applicability", "mapped" if entry["lifecycle_stages"] else "pending")
                entry["lifecycle_review"] = assignment.get("lifecycle_review")
                entry["card"] = cards.get(entry["entry_id"])
                entry["explainable"] = bool(entry["card"] and entry["card"]["career_card_version_id"] in supported)
            selected = next((e for e in entries if e["external_key"] == role), None)
            if role and selected is None:
                abort(404, "当前知识库没有该方向。")
            card_claims, direction = [], None
            if selected and selected["card"]:
                card_claims = [dict(row) for row in db.execute("SELECT * FROM career_card_claims WHERE career_card_version_id=? ORDER BY claim_kind, claim_text", (selected["card"]["career_card_version_id"],))]
            elif selected and selected["requires_specific_jd"]:
                direction = db.execute("SELECT summary, boundary_note FROM career_directions WHERE career_direction_id=?", (selected["entry_id"],)).fetchone()
            filtered = [e for e in entries if matches_filters(e, selections)]
            for table, _, _ in DIMENSIONS:
                candidates = [e for e in entries if matches_filters(e, selections, exclude=table)]
                for option in options[table]:
                    option["count"] = sum(option["code"] in {x["code"] for x in e[table]} for e in candidates)
            stage_candidates = [e for e in entries if matches_filters(e, selections, exclude="lifecycle_stages")]
            lifecycle_counts = {status: sum(e["lifecycle_applicability"] == status for e in stage_candidates) for status in LIFECYCLE_LABELS}
            remove_stage_url = "/?" + urlencode({t: codes for t, codes in selections.items() if t != "lifecycle_stages" and codes}, doseq=True)
            snapshot_id = snapshot["knowledge_snapshot_id"]
        result, error = None, None
        if profile_id:
            if not selected or not selected["explainable"]:
                abort(400, "该方向尚未配置解释规则，请选择页面提供的可解释方向。")
            try:
                result = CareerCardExplanationService(database_path).explain(
                    profile=profiles[profile_id], role_pack=role, knowledge_snapshot_id=snapshot_id)
            except (ValueError, LookupError, sqlite3.Error):
                error = "当前知识快照无法使用此解释器查询。请在当前代码下重新运行导入脚本，再刷新页面。"
        return render_template("career_map_viewer.html", entries=filtered, selected=selected,
                               card_claims=card_claims, direction=direction, profiles=profiles,
                               profile_id=profile_id, result=result, error=error,
                               dimensions=DIMENSIONS, options=options, labels=LABELS,
                               selections=selections, lifecycle_labels=LIFECYCLE_LABELS,
                               lifecycle_counts=lifecycle_counts, remove_stage_url=remove_stage_url,
                               claim_labels=CLAIMS, snapshot_id=snapshot_id,
                               counts=(len(entries), len(cards), sum(e["explainable"] for e in entries))), (503 if error else 200)

    return app
