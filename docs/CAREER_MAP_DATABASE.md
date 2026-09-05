# 医学职业地图关系型数据库 v1

## 目标与边界

本数据库把当前 Role Pack 的职业侧真值投影为可查询、可版本化和可审计的关系数据，服务未来的“职业画像 ↔ Role Pack ↔ 真实转型案例”解释型匹配。它不替代现有 Role Pack JSON，不产生岗位匹配、录用、薪资或职业成功结论，也不改变任何运行时 routing、Claim Gate 或责任边界。

## Source of truth

`data/role-packs/*.json` 是 Canonical Role Pack 的唯一可编辑真值。`skill-lite/medical-resume-skill/references/role-packs.md` 与 `role-pack-rules.json` 是生成投影，不可手改。SQL 同样是可重建投影：导入器保存每个 JSON 的原文、相对路径和 SHA-256，再把其可关系化字段写入数据库。

当前 canonical source 共 10 个，数量以 `data/role-packs/*.json` 的实际文件集合为准。导入器将每一个文件记录为 `canonical_v1 + canonical_source`；此状态仅表示职业语义和执行 guardrail 是 Canonical source，**不表示**该方向已经是 runtime target 或已经通过 Cross-model validation。

## 表与关系

- `roles`、`role_pack_versions`、`source_artifacts`：稳定角色标识、内容版本及原始 JSON provenance。
- `role_skills`、`role_requirements`、`negative_mappings`、`role_expression_policies`、`role_pack_evaluation_cases`：当前 JSON 中的能力优先级、证据门槛、职责边界、表达规则和测试定义。
- `ecosystems`、`lifecycle_stages`、`function_families` 及其关系表：产业生态 × 生命周期 × 职能族的机器可读地图。`data/career-map/directions-v1.json` 是该地图的人工维护种子；它不反向修改 Role Pack。
- `career_directions` 及其三维关联表：未形成 Canonical Pack 的方向。`JD-driven` 方向被明确标记为 `research + jd_driven + not_routable`，必须附具体 JD；未来 Beta/Candidate 方向可登记为 `beta/candidate + explore_only + not_routable`，不会被误当作 Canonical。
- `career_cards`、`career_card_claims` 及关联表：职业卡的版本、职责/交付物/可迁移性/缺口/JD-dependent 范围与逐条 JD 证据关系。职业卡只解释已有关联 Role Pack，不能生成新 Role Pack 或改变其职责边界。
- `jd_evidence`、`jd_evidence_snapshots`、`role_jd_evidence`：公开 JD 来源、不可变的保留摘录、来源链接、采集日期、声明摘要与实际摘录摘要。若历史证据的声明摘要与保留摘录不一致，两个值都会保留并显式标记，绝不静默改写来源。
- `validation_runs`：保存实际 schema、domain、cross-model 或 regression 运行结果；`evaluation_cases` 只是测试定义，绝不被当作已通过的运行。
- `career_profiles`、`transition_cases`、`profile_role_matches`：只预留未来关系，v1 不导入 synthetic profile，也不处理个人或案例数据。

## 迁移与幂等性

本地开发使用 SQLite；DDL 只使用 PostgreSQL 可表达的基础表、外键、唯一键和检查约束，生产迁移可用 PostgreSQL 的 `uuid`、`jsonb` 和 `timestamptz` 等等价类型替换文本存储。

```powershell
python scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite
```

导入器先以 `schemas/role-pack.schema.json` 校验全部 JSON。其后使用 `external_key + content_sha256` 去重：相同文件重复导入不会增加 Role Pack 版本或规则行；内容变更会创建新的不可变版本、把前一版本标记为非当前版本，并保留原始工件。不会覆盖或删除旧职业语义。

职业地图种子还登记了 6 个长期 JD-driven 方向：市场准入、医疗产品、医疗咨询、商业/业务分析、医疗/项目运营、医学销售/商业。它们是可探索的职业方向，不是泛化的 Role Pack；数据库会保留其所需 JD 语境和边界提示。

## 职业卡与 JD 证据试点

本阶段导入五张**已有冻结候选证据**的职业卡：药物警戒 / 药物安全、法规医学写作、临床研究协调 / CRA 支持、临床数据管理 / CDM 支持、医疗器械临床 / 应用支持。卡片文件位于 `data/career_cards/*.json`，分别链接对应的 `docs/research/role-validation/**/candidate-evidence-v1.json`。这些卡片是可重建的 SQL 投影，不替代 `data/careers/` 中仍标为 draft 的探索卡，也不把 Candidate evidence 升级为新的 Canonical 状态。

每个卡片均保留：稳定职责、典型交付物、岗位特定要求提示、直接/可迁移/部分可迁移事实、显性缺口、JD-dependent 范围及投递前核验动作。首轮不会抓取实时 JD，也不会自动产生匹配分数。

## Synthetic 解释查询 MVP

`career_card_match_rules` 只记录人工维护的匹配规则，绝不从职业卡自然语言猜测能力对应关系。`CareerCardExplanationService` 以一个 synthetic、逐条 `confirmed` 的 profile 和一个指定 Role Pack 为输入，统一返回 `direct`、`transferable`、`partial`、`gap`、`unsupported` 五类解释；每条均保留 profile evidence、Career Card claim、Role Pack 边界和 JD snapshot provenance。它不输出百分比分数、不排序、不写入 profile，也不改变既有 `/api/career-comparisons` 百分比接口。首版规则只覆盖本批的 CDM 支持与医疗器械临床 / 应用支持；其余职业卡在具备独立规则与回归用例前不会被该服务查询。

```powershell
python scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite
python scripts/query_career_card_explanation.py --database .local/career-map.sqlite `
  --profile-id synthetic-cdm-support-001 --role-pack clinical_data_management_v1
```

三条虚构 profile 位于 `data/career-map/career-card-explanation-test-profiles-v1.json`，仅用于验证直接、可迁移、部分、缺口与禁止推断边界，不能作为真实用户数据或职业结论。

## 最小查询示例

```sql
-- 当前 Canonical 集合与其运行时边界。
SELECT v.external_key, v.label, s.maturity_status, s.execution_status
FROM role_pack_versions v
JOIN role_status_history s ON s.role_pack_version_id = v.role_pack_version_id
WHERE v.is_current = 1
ORDER BY v.external_key;

-- 某方向不可升级的职责或表达。
SELECT n.mapping_kind, n.mapping_text
FROM negative_mappings n
JOIN role_pack_versions v ON v.role_pack_version_id = n.role_pack_version_id
WHERE v.external_key = 'pharmacovigilance_drug_safety_v1' AND v.is_current = 1
ORDER BY n.mapping_kind, n.mapping_text;

-- Canonical、Beta 与 JD-driven 方向以同一目录视图检索。
SELECT external_key, label, knowledge_maturity, service_mode, requires_specific_jd
FROM career_map_entries
ORDER BY service_mode, external_key;

-- 读取一张职业卡及其关联的 Role Pack；不改变 Role Pack 的 Canonical 状态。
SELECT c.career_card_id, c.summary, v.external_key AS role_pack, c.scope_note
FROM career_cards c
JOIN role_pack_versions v ON v.role_pack_version_id = c.role_pack_version_id
WHERE c.is_current = 1
ORDER BY c.career_card_id;

-- 查某职业卡的“岗位特定”原始 JD 摘录和证据状态。
SELECT s.employer, s.job_title, s.retrieved_at, s.status, s.source_snapshot
FROM jd_evidence_snapshots s
JOIN role_jd_evidence r ON r.jd_evidence_id = s.jd_evidence_id
JOIN role_pack_versions v ON v.role_pack_version_id = r.role_pack_version_id
WHERE v.external_key = 'clinical_research_associate_v1'
  AND v.is_current = 1 AND r.evidence_scope = 'jd_dependent'
ORDER BY s.retrieved_at DESC, s.external_snapshot_id;
```

## 暂不实现

不引入向量检索、真实用户档案、转型案例/导师数据、自动匹配分数或 JD 抓取。它们须在取得授权、明确数据保留规则并有对应 source/provenance 后分别实现。
