-- Medical career map v1.
--
-- The relational types can be translated to PostgreSQL. The immutable-content
-- triggers below and the transactional migration adapter target SQLite. JSON is
-- stored as TEXT in v1 because JSON Role Packs remain the editable source of
-- truth; the relational rows are a queryable, rebuildable projection.

CREATE TABLE IF NOT EXISTS import_batches (
    import_id TEXT PRIMARY KEY,
    source_root TEXT NOT NULL,
    source_digest_sha256 TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    importer_version TEXT NOT NULL,
    UNIQUE (source_root, source_digest_sha256)
);

CREATE TABLE IF NOT EXISTS roles (
    role_id TEXT PRIMARY KEY,
    canonical_key TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    role_kind TEXT NOT NULL CHECK (role_kind IN ('role_pack_family', 'career_card')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT
);

CREATE TABLE IF NOT EXISTS source_artifacts (
    artifact_id TEXT PRIMARY KEY,
    relative_path TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    raw_content TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    UNIQUE (relative_path, content_sha256)
);

CREATE TABLE IF NOT EXISTS role_pack_versions (
    role_pack_version_id TEXT PRIMARY KEY,
    role_id TEXT NOT NULL REFERENCES roles(role_id),
    external_key TEXT NOT NULL,
    version_label TEXT NOT NULL,
    label TEXT NOT NULL,
    target_scope TEXT NOT NULL,
    boundary_note TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    artifact_id TEXT NOT NULL REFERENCES source_artifacts(artifact_id),
    is_current INTEGER NOT NULL CHECK (is_current IN (0, 1)),
    imported_at TEXT NOT NULL,
    deprecated_at TEXT,
    superseded_by_version_id TEXT REFERENCES role_pack_versions(role_pack_version_id),
    UNIQUE (external_key, content_sha256)
);

CREATE TABLE IF NOT EXISTS role_status_history (
    role_status_history_id TEXT PRIMARY KEY,
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    maturity_status TEXT NOT NULL CHECK (maturity_status IN ('beta', 'candidate', 'canonical_v1')),
    execution_status TEXT NOT NULL CHECK (execution_status IN ('not_routable', 'canonical_source', 'runtime_enabled', 'deprecated')),
    status_reason TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    UNIQUE (role_pack_version_id, maturity_status, execution_status, status_reason)
);

CREATE TABLE IF NOT EXISTS ecosystems (
    ecosystem_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lifecycle_stages (
    lifecycle_stage_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS function_families (
    function_family_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS role_ecosystems (
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    ecosystem_id TEXT NOT NULL REFERENCES ecosystems(ecosystem_id),
    provenance_note TEXT,
    PRIMARY KEY (role_pack_version_id, ecosystem_id)
);

CREATE TABLE IF NOT EXISTS role_lifecycle_stages (
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    lifecycle_stage_id TEXT NOT NULL REFERENCES lifecycle_stages(lifecycle_stage_id),
    provenance_note TEXT,
    PRIMARY KEY (role_pack_version_id, lifecycle_stage_id)
);

CREATE TABLE IF NOT EXISTS role_function_families (
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    function_family_id TEXT NOT NULL REFERENCES function_families(function_family_id),
    provenance_note TEXT,
    PRIMARY KEY (role_pack_version_id, function_family_id)
);

-- Directions without a Canonical Role Pack live separately. This prevents a
-- Beta, Candidate, or JD-driven direction from being mistaken for a canonical
-- execution source merely because it has a familiar occupational name.
CREATE TABLE IF NOT EXISTS career_directions (
    career_direction_id TEXT PRIMARY KEY,
    external_key TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    knowledge_maturity TEXT NOT NULL CHECK (knowledge_maturity IN ('research', 'beta', 'candidate')),
    service_mode TEXT NOT NULL CHECK (service_mode IN ('explore_only', 'jd_driven')),
    runtime_status TEXT NOT NULL CHECK (runtime_status IN ('not_routable', 'deprecated')),
    requires_specific_jd INTEGER NOT NULL CHECK (requires_specific_jd IN (0, 1)),
    summary TEXT NOT NULL,
    boundary_note TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT
);

CREATE TABLE IF NOT EXISTS career_direction_ecosystems (
    career_direction_id TEXT NOT NULL REFERENCES career_directions(career_direction_id),
    ecosystem_id TEXT NOT NULL REFERENCES ecosystems(ecosystem_id),
    PRIMARY KEY (career_direction_id, ecosystem_id)
);

CREATE TABLE IF NOT EXISTS career_direction_lifecycle_stages (
    career_direction_id TEXT NOT NULL REFERENCES career_directions(career_direction_id),
    lifecycle_stage_id TEXT NOT NULL REFERENCES lifecycle_stages(lifecycle_stage_id),
    PRIMARY KEY (career_direction_id, lifecycle_stage_id)
);

CREATE TABLE IF NOT EXISTS career_direction_function_families (
    career_direction_id TEXT NOT NULL REFERENCES career_directions(career_direction_id),
    function_family_id TEXT NOT NULL REFERENCES function_families(function_family_id),
    PRIMARY KEY (career_direction_id, function_family_id)
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    skill_kind TEXT NOT NULL CHECK (skill_kind IN ('capability_category', 'skill')),
    created_at TEXT NOT NULL,
    deprecated_at TEXT
);

CREATE TABLE IF NOT EXISTS role_skills (
    role_skill_id TEXT PRIMARY KEY,
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    skill_id TEXT NOT NULL REFERENCES skills(skill_id),
    priority_rank INTEGER NOT NULL CHECK (priority_rank > 0),
    mapping_label TEXT NOT NULL,
    placement_hint TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    UNIQUE (role_pack_version_id, skill_id)
);

CREATE TABLE IF NOT EXISTS role_requirements (
    role_requirement_id TEXT PRIMARY KEY,
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    requirement_kind TEXT NOT NULL,
    requirement_text TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    UNIQUE (role_pack_version_id, requirement_kind, requirement_text)
);

CREATE TABLE IF NOT EXISTS role_deliverables (
    role_deliverable_id TEXT PRIMARY KEY,
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    deliverable_text TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    UNIQUE (role_pack_version_id, deliverable_text)
);

CREATE TABLE IF NOT EXISTS negative_mappings (
    negative_mapping_id TEXT PRIMARY KEY,
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    mapping_kind TEXT NOT NULL CHECK (mapping_kind IN ('boundary_note', 'restricted_verb', 'forbidden_claim')),
    mapping_text TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    UNIQUE (role_pack_version_id, mapping_kind, mapping_text)
);

CREATE TABLE IF NOT EXISTS role_expression_policies (
    role_expression_policy_id TEXT PRIMARY KEY,
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    policy_kind TEXT NOT NULL CHECK (policy_kind IN ('preferred_action', 'allowed_verb', 'sentence_pattern')),
    policy_text TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    UNIQUE (role_pack_version_id, policy_kind, policy_text)
);

CREATE TABLE IF NOT EXISTS role_pack_evaluation_cases (
    evaluation_case_id TEXT PRIMARY KEY,
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    case_ordinal INTEGER NOT NULL CHECK (case_ordinal > 0),
    input_json TEXT NOT NULL,
    expected_output_json TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    UNIQUE (role_pack_version_id, case_ordinal)
);

CREATE TABLE IF NOT EXISTS jd_evidence (
    jd_evidence_id TEXT PRIMARY KEY,
    source_title TEXT NOT NULL,
    source_url TEXT NOT NULL,
    publisher TEXT,
    published_at TEXT,
    accessed_at TEXT,
    market TEXT,
    snapshot_sha256 TEXT,
    source_status TEXT NOT NULL CHECK (source_status IN ('draft', 'reviewed', 'deprecated')),
    created_at TEXT NOT NULL,
    deprecated_at TEXT,
    UNIQUE (source_url, snapshot_sha256)
);

CREATE TABLE IF NOT EXISTS role_jd_evidence (
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    jd_evidence_id TEXT NOT NULL REFERENCES jd_evidence(jd_evidence_id),
    evidence_scope TEXT NOT NULL CHECK (evidence_scope IN ('stable_core', 'jd_dependent', 'boundary')),
    provenance_note TEXT NOT NULL,
    PRIMARY KEY (role_pack_version_id, jd_evidence_id, evidence_scope)
);

-- A JD record describes the public source; its retained excerpt lives in a
-- separate immutable snapshot so the same listing can be captured again
-- without overwriting earlier evidence.
CREATE TABLE IF NOT EXISTS jd_evidence_snapshots (
    jd_evidence_snapshot_id TEXT PRIMARY KEY,
    jd_evidence_id TEXT NOT NULL REFERENCES jd_evidence(jd_evidence_id),
    external_snapshot_id TEXT NOT NULL,
    employer TEXT,
    job_title TEXT,
    location TEXT,
    retrieved_at TEXT,
    status TEXT NOT NULL,
    source_type TEXT,
    snapshot_completeness TEXT,
    qualifying INTEGER CHECK (qualifying IN (0, 1)),
    source_snapshot TEXT NOT NULL,
    source_digest_sha256 TEXT NOT NULL,
    declared_source_digest_sha256 TEXT,
    source_digest_matches INTEGER NOT NULL CHECK (source_digest_matches IN (0, 1)),
    source_artifact_id TEXT NOT NULL REFERENCES source_artifacts(artifact_id),
    created_at TEXT NOT NULL,
    deprecated_at TEXT,
    revision_sha256 TEXT NOT NULL,
    UNIQUE (source_artifact_id, external_snapshot_id, revision_sha256)
);

-- Career cards are a source-controlled explanatory layer over a Canonical
-- Role Pack. They do not create a new runtime target or alter Pack semantics.
CREATE TABLE IF NOT EXISTS career_cards (
    career_card_version_id TEXT PRIMARY KEY,
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    career_card_id TEXT NOT NULL,
    version_label TEXT NOT NULL,
    summary TEXT NOT NULL,
    scope_note TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    artifact_id TEXT NOT NULL REFERENCES source_artifacts(artifact_id),
    is_current INTEGER NOT NULL CHECK (is_current IN (0, 1)),
    imported_at TEXT NOT NULL,
    deprecated_at TEXT,
    superseded_by_version_id TEXT REFERENCES career_cards(career_card_version_id),
    revision_sha256 TEXT NOT NULL,
    jd_artifact_id TEXT REFERENCES source_artifacts(artifact_id),
    UNIQUE (career_card_id, revision_sha256)
);

CREATE TABLE IF NOT EXISTS career_card_claims (
    career_card_claim_id TEXT PRIMARY KEY,
    career_card_version_id TEXT NOT NULL REFERENCES career_cards(career_card_version_id),
    claim_kind TEXT NOT NULL CHECK (claim_kind IN (
        'stable_responsibility', 'typical_deliverable', 'entry_requirement',
        'transferable_direct', 'transferable', 'transferable_partial', 'explicit_gap',
        'jd_dependent_scope', 'validation_action'
    )),
    claim_text TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    UNIQUE (career_card_version_id, claim_kind, claim_text)
);

CREATE TABLE IF NOT EXISTS career_card_claim_jd_evidence (
    career_card_claim_id TEXT NOT NULL REFERENCES career_card_claims(career_card_claim_id),
    jd_evidence_id TEXT NOT NULL REFERENCES jd_evidence(jd_evidence_id),
    PRIMARY KEY (career_card_claim_id, jd_evidence_id)
);

-- Match rules are an explicit, versioned interpretation layer. They are kept
-- separate from Career Card prose so query behavior never infers a mapping
-- from text or alters a Canonical Role Pack's semantics.
CREATE TABLE IF NOT EXISTS career_card_match_rules (
    career_card_match_rule_id TEXT PRIMARY KEY,
    career_card_version_id TEXT NOT NULL REFERENCES career_cards(career_card_version_id),
    career_card_claim_id TEXT REFERENCES career_card_claims(career_card_claim_id),
    rule_key TEXT NOT NULL,
    classification TEXT NOT NULL CHECK (classification IN ('direct', 'transferable', 'partial', 'gap', 'unsupported')),
    match_mode TEXT NOT NULL CHECK (match_mode IN ('all_capabilities_present', 'any_capability_present', 'all_capabilities_absent')),
    required_capability_codes_json TEXT NOT NULL,
    allowed_scopes_json TEXT NOT NULL,
    negative_mapping_text TEXT,
    explanation TEXT NOT NULL,
    artifact_id TEXT NOT NULL REFERENCES source_artifacts(artifact_id),
    imported_at TEXT NOT NULL,
    deprecated_at TEXT,
    career_card_id TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    rule_json TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN ('current', 'superseded', 'revoked')),
    superseded_by_rule_id TEXT REFERENCES career_card_match_rules(career_card_match_rule_id),
    UNIQUE (career_card_version_id, rule_key, content_sha256)
);

CREATE TABLE IF NOT EXISTS validation_runs (
    validation_run_id TEXT PRIMARY KEY,
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    evaluation_case_id TEXT REFERENCES role_pack_evaluation_cases(evaluation_case_id),
    validation_kind TEXT NOT NULL CHECK (validation_kind IN ('schema', 'domain', 'cross_model', 'regression')),
    status TEXT NOT NULL CHECK (status IN ('pass', 'fail', 'pending')),
    model_identifier TEXT,
    configuration_digest TEXT,
    input_digest TEXT,
    output_digest TEXT,
    reviewer_decision TEXT,
    recorded_at TEXT NOT NULL,
    notes TEXT
);

-- Reserved for later product phases. No personal or transition-case data is
-- imported by v1; these tables intentionally do not create matching behavior.
CREATE TABLE IF NOT EXISTS career_profiles (
    career_profile_id TEXT PRIMARY KEY,
    external_key TEXT NOT NULL UNIQUE,
    profile_status TEXT NOT NULL,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('synthetic', 'user_confirmed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS transition_cases (
    transition_case_id TEXT PRIMARY KEY,
    external_key TEXT NOT NULL UNIQUE,
    authorization_status TEXT NOT NULL,
    review_status TEXT,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('synthetic', 'authorized_public', 'private')),
    created_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS profile_role_matches (
    profile_role_match_id TEXT PRIMARY KEY,
    career_profile_id TEXT NOT NULL REFERENCES career_profiles(career_profile_id),
    role_pack_version_id TEXT NOT NULL REFERENCES role_pack_versions(role_pack_version_id),
    match_status TEXT NOT NULL CHECK (match_status IN ('draft', 'reviewed', 'superseded')),
    explanation_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    superseded_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_role_pack_versions_current
    ON role_pack_versions (external_key, is_current);
CREATE INDEX IF NOT EXISTS idx_role_skills_version
    ON role_skills (role_pack_version_id, priority_rank);
CREATE INDEX IF NOT EXISTS idx_negative_mappings_version
    ON negative_mappings (role_pack_version_id, mapping_kind);
CREATE INDEX IF NOT EXISTS idx_jd_evidence_snapshots_evidence
    ON jd_evidence_snapshots (jd_evidence_id, retrieved_at);
CREATE INDEX IF NOT EXISTS idx_career_cards_current
    ON career_cards (career_card_id, is_current);
CREATE INDEX IF NOT EXISTS idx_career_card_match_rules_current
    ON career_card_match_rules (career_card_version_id, classification);

CREATE VIEW IF NOT EXISTS career_map_entries AS
SELECT
    v.role_pack_version_id AS entry_id,
    v.external_key,
    v.label,
    'canonical_v1' AS knowledge_maturity,
    'canonical_role_pack' AS service_mode,
    'canonical_source' AS runtime_status,
    0 AS requires_specific_jd
FROM role_pack_versions v
WHERE v.is_current = 1
UNION ALL
SELECT
    d.career_direction_id AS entry_id,
    d.external_key,
    d.label,
    d.knowledge_maturity,
    d.service_mode,
    d.runtime_status,
    d.requires_specific_jd
FROM career_directions d
WHERE d.deprecated_at IS NULL;


-- Content-addressed manifests exclude machine paths and import timestamps.
CREATE TABLE IF NOT EXISTS knowledge_snapshots (
    knowledge_snapshot_id TEXT PRIMARY KEY,
    manifest_sha256 TEXT NOT NULL UNIQUE,
    manifest_json TEXT NOT NULL,
    interpreter_version TEXT NOT NULL,
    importer_version TEXT NOT NULL,
    is_current INTEGER NOT NULL CHECK (is_current IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_snapshot_activations (
    activation_id TEXT PRIMARY KEY,
    knowledge_snapshot_id TEXT NOT NULL REFERENCES knowledge_snapshots(knowledge_snapshot_id),
    activated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS career_card_match_rule_events (
    event_id TEXT PRIMARY KEY,
    career_card_match_rule_id TEXT NOT NULL REFERENCES career_card_match_rules(career_card_match_rule_id),
    knowledge_snapshot_id TEXT NOT NULL REFERENCES knowledge_snapshots(knowledge_snapshot_id),
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN ('current', 'superseded', 'revoked')),
    recorded_at TEXT NOT NULL
);

-- Exact retained snapshots used by each immutable Career Card revision.
CREATE TABLE IF NOT EXISTS career_card_jd_snapshots (
    career_card_version_id TEXT NOT NULL REFERENCES career_cards(career_card_version_id),
    jd_evidence_snapshot_id TEXT NOT NULL REFERENCES jd_evidence_snapshots(jd_evidence_snapshot_id),
    PRIMARY KEY (career_card_version_id, jd_evidence_snapshot_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_role_pack_current
    ON role_pack_versions (external_key) WHERE is_current = 1;
CREATE UNIQUE INDEX IF NOT EXISTS uq_career_card_current
    ON career_cards (career_card_id) WHERE is_current = 1;
CREATE UNIQUE INDEX IF NOT EXISTS uq_match_rule_current
    ON career_card_match_rules (career_card_id, rule_key) WHERE lifecycle_status = 'current';
CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_snapshot_current
    ON knowledge_snapshots (is_current) WHERE is_current = 1;

CREATE TRIGGER IF NOT EXISTS immutable_match_rule_content
BEFORE UPDATE OF career_card_match_rule_id, career_card_version_id, career_card_claim_id, rule_key,
    classification, match_mode, required_capability_codes_json, allowed_scopes_json,
    negative_mapping_text, explanation, artifact_id, career_card_id, content_sha256, rule_json
ON career_card_match_rules
BEGIN
    SELECT RAISE(ABORT, 'match rule revision content is immutable');
END;

CREATE TRIGGER IF NOT EXISTS immutable_knowledge_manifest
BEFORE UPDATE OF manifest_sha256, manifest_json, interpreter_version, importer_version
ON knowledge_snapshots
BEGIN
    SELECT RAISE(ABORT, 'knowledge manifest is immutable');
END;


-- Background references are not evidence that an individual claim is supported.
-- claim_support is only imported from explicit, reviewed Card source annotations.
CREATE TABLE IF NOT EXISTS career_card_claim_snapshot_evidence (
    career_card_claim_id TEXT NOT NULL REFERENCES career_card_claims(career_card_claim_id),
    jd_evidence_snapshot_id TEXT NOT NULL REFERENCES jd_evidence_snapshots(jd_evidence_snapshot_id),
    relation_kind TEXT NOT NULL CHECK (relation_kind IN ('research_background', 'claim_support')),
    reviewed_by TEXT,
    reviewed_at TEXT,
    review_note TEXT,
    CHECK (relation_kind = 'research_background' OR
           (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL AND review_note IS NOT NULL)),
    PRIMARY KEY (career_card_claim_id, jd_evidence_snapshot_id, relation_kind)
);
