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
- `role_deliverables`、`jd_evidence`、`role_jd_evidence`：为经核验的交付物和 JD 证据预留；现有 Role Pack JSON 不含可直接导入的逐条 JD 快照，因此 v1 不伪造记录。
- `validation_runs`：保存实际 schema、domain、cross-model 或 regression 运行结果；`evaluation_cases` 只是测试定义，绝不被当作已通过的运行。
- `career_profiles`、`transition_cases`、`profile_role_matches`：只预留未来关系，v1 不导入 synthetic profile，也不处理个人或案例数据。

## 迁移与幂等性

本地开发使用 SQLite；DDL 只使用 PostgreSQL 可表达的基础表、外键、唯一键和检查约束，生产迁移可用 PostgreSQL 的 `uuid`、`jsonb` 和 `timestamptz` 等等价类型替换文本存储。

```powershell
python scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite
```

导入器先以 `schemas/role-pack.schema.json` 校验全部 JSON。其后使用 `external_key + content_sha256` 去重：相同文件重复导入不会增加 Role Pack 版本或规则行；内容变更会创建新的不可变版本、把前一版本标记为非当前版本，并保留原始工件。不会覆盖或删除旧职业语义。

职业地图种子还登记了 6 个长期 JD-driven 方向：市场准入、医疗产品、医疗咨询、商业/业务分析、医疗/项目运营、医学销售/商业。它们是可探索的职业方向，不是泛化的 Role Pack；数据库会保留其所需 JD 语境和边界提示。

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
```

## 暂不实现

不引入向量检索、真实用户档案、转型案例/导师数据、自动匹配分数或 JD 抓取。它们须在取得授权、明确数据保留规则并有对应 source/provenance 后分别实现。
