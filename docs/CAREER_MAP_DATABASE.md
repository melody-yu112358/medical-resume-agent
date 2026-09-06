# 医学职业地图关系型数据库 v1

## 目标与边界

本数据库把当前 Role Pack 的职业侧真值投影为可查询、可版本化和可审计的关系数据，服务未来的“职业画像 ↔ Role Pack ↔ 真实转型案例”解释型匹配。它不替代现有 Role Pack JSON，不产生岗位匹配、录用、薪资或职业成功结论，也不改变任何运行时 routing、Claim Gate 或责任边界。

## Source of truth

`data/role-packs/*.json` 是 Canonical Role Pack 的唯一可编辑真值。`skill-lite/medical-resume-skill/references/role-packs.md` 与 `role-pack-rules.json` 是生成投影，不可手改。SQL 同样是可重建投影：导入器保存每个 JSON 的原文、相对路径和 SHA-256，再把其可关系化字段写入数据库。

当前资产与关联只见 [生成状态页](CAREER_CATALOG_STATUS.md)，最终以其机器源为准。导入器将每一个文件记录为 `canonical_v1 + canonical_source`；此状态仅表示职业语义和执行 guardrail 是 Canonical source，**不表示**该方向已经是 runtime target 或已经通过 Cross-model validation。

## 表与关系

- `roles`、`role_pack_versions`、`source_artifacts`：稳定角色标识、内容版本及原始 JSON provenance。
- `role_skills`、`role_requirements`、`negative_mappings`、`role_expression_policies`、`role_pack_evaluation_cases`：当前 JSON 中的能力优先级、证据门槛、职责边界、表达规则和测试定义。
- `ecosystems`、`lifecycle_stages`、`function_families` 及其关系表：产业生态 × 生命周期 × 职能族的机器可读地图。`data/career-map/directions-v1.json` 是该地图的人工维护种子；它不反向修改 Role Pack。

三个维度可交叉而非层级，生命周期不是必填。`lifecycle_applicability` 及可选审核元数据保存在 taxonomy 原始 artifact，由 manifest 固定版本，不增加重复 SQL 列。详见 [筛选与适用性契约](CAREER_MAP_DATABASE.md#taxonomy-and-filtering)。

分类仅用于知识导航，不是医学生转岗适配模型；当前目录对象粒度仍有差异。Profile 解释依据 claim、已确认事实和显式规则，不因网页筛选标签而改变结论。

逐项对象类型与资产关联见 [职业目录结构和覆盖清单](CAREER_CATALOG_STRUCTURE.md)。清单中的类型为整理建议，尚未写入 taxonomy 或 SQL，不是新的 source of truth。
- `career_directions` 及其三维关联表：未形成 Canonical Pack 的方向。`JD-driven` 方向被明确标记为 `research + jd_driven + not_routable`，必须附具体 JD；未来 Beta/Candidate 方向可登记为 `beta/candidate + explore_only + not_routable`，不会被误当作 Canonical。
- `career_cards`、`career_card_claims` 及关联表：职业卡的版本、职责/交付物/可迁移性/缺口/JD-dependent 范围与带来源粒度的 JD snapshot 关系。职业卡只解释已有关联 Role Pack，不能生成新 Role Pack 或改变其职责边界。
- `jd_evidence`、`jd_evidence_snapshots`、`role_jd_evidence`：公开 JD 来源、不可变的保留摘录、来源链接、采集日期、声明摘要与实际摘录摘要。若历史证据的声明摘要与保留摘录不一致，两个值都会保留并显式标记，绝不静默改写来源。
- `validation_runs`：保存实际 schema、domain、cross-model 或 regression 运行结果；`evaluation_cases` 只是测试定义，绝不被当作已通过的运行。
- `career_profiles`、`transition_cases`、`profile_role_matches`：只预留未来关系，v1 不导入 synthetic profile，也不处理个人或案例数据。

## 迁移与幂等性

本地使用 SQLite。基础关系类型可映射到 PostgreSQL；本次增加的不可变内容触发器和表重建迁移使用 SQLite 语法，未来迁移 PostgreSQL 时需要适配，不宣称 DDL 可直接跨库执行。

```powershell
python scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite
```

导入器先以 `schemas/role-pack.schema.json` 校验全部 JSON。其后使用 `external_key + content_sha256` 去重：相同文件重复导入不会增加 Role Pack 版本或规则行；内容变更会创建新的不可变版本、把前一版本标记为非当前版本，并保留原始工件。不会覆盖或删除旧职业语义。

### 增量投影与 revision（importer v4）

Source of truth 不变：Pack、Card、规则 registry、taxonomy registry 与 JD evidence 文件分别拥有其原有职责；SQL 和 manifest 都是生成投影。无需修改 Canonical Pack 或 Career Card JSON 来升级已有数据库。

导入器把一次输入视为**完整源集合**，不是局部 patch。先捕获源文件字节并校验，再在一个 `BEGIN IMMEDIATE` 事务内完成 schema 升级、版本导入、当前关联替换和 manifest 激活。先插入新版本，再设置旧版本的 successor，避免引用尚不存在的外键。提交前执行 `foreign_key_check`；任何失败连同 schema 升级一起回滚。

- Pack：继续以文件内容标识 revision；保留 `is_current`、`superseded_by_version_id` 和失效时间。
- Card：新增 `revision_sha256` 和 `jd_artifact_id`。revision 由 **Card 原文 hash + Role Pack revision ID + JD artifact ID** 决定，`role_pack_version_id` 是该 revision 的明确绑定。即使 Card 文本没变，Pack 或 JD artifact 更新也会产生新 Card revision。该绑定记录导入依赖，不代表自动完成新的领域语义审查。
- Match rule：新增 `career_card_id`、独立规则内容 `content_sha256`、`rule_json`、`lifecycle_status` 和 `superseded_by_rule_id`。规则 revision ID 同时绑定 Card revision；修改单条规则不要求修改 Card，也不为其他未变规则生成 revision。数据库触发器禁止原地改写规则内容。
- Rule 生命周期：同一身份（Card ID + rule key）的新版替代旧版时为 `superseded`；从完整输入集合消失时为 `revoked`。重新引入完全相同的规则及依赖可重新激活原 revision，状态变化保存在 `career_card_match_rule_events`。允许空规则集合，以便撤销最后一条规则。没有单独的人工 revoke API；移除源规则就是本阶段的撤销操作。
- Taxonomy：六张关联表和三个分类词典是当前投影，事务内按完整 registry 替换，移除的关系不会残留。移除的 career direction 标记失效；历史分类和方向文本由 manifest 指向的原始 registry artifact 追踪。
- JD：`jd_evidence_snapshots.revision_sha256` 覆盖 snapshot 的完整 JSON（含元数据）；`career_card_jd_snapshots` 固定某 Card revision 使用的准确 snapshot 集合。`jd_evidence` 是 URL/摘录标识下的来源目录，描述性元数据随当前输入更新；历史元数据保留在不可变 snapshot 和 artifact。`role_jd_evidence` 是当前关联投影，历史关联按 Card revision 查询。

部分唯一索引分别约束每个 Pack、Card、rule 身份和全局 knowledge snapshot 至多一个 current；成功导入为当前源集合中的每个身份激活恰好一个 revision。不存在于输入中的对象不会继续有效。

“fresh build = incremental build”指当前语义行、关系、解释和 manifest 一致；历史行数量、首次导入时间、首次捕获 artifact 和激活日志自然可能不同。重复导入不新增 revision、manifest 或生命周期事件。回退到旧源集合可重新激活旧 manifest；每次实际切换保留 activation 记录。

### Knowledge snapshot / manifest

`knowledge_snapshots` 保存 canonical JSON、SHA-256、解释器版本、导入器版本和 current 指针；`knowledge_snapshot_activations` 保存切换记录。manifest 内容不允许原地更新。`import_batches.source_digest_sha256` 和 CLI 的 `source_digest` 现在指整个 manifest digest，不再只是 Pack 文件集合摘要。CLI 同时返回 `knowledge_snapshot_id`。

```json
{
  "schema_version": "career-map-knowledge-snapshot-v2",
  "importer_version": "career-map-import-v4",
  "explanation_interpreter": {"version": "career-card-explanation-v2", "source_sha256": "..."},
  "sources": [{"path": "data/role-packs/....json", "content_sha256": "..."}],
  "taxonomy_revision": "source artifact ID",
  "match_rule_registry_artifact_id": "source artifact ID",
  "role_pack_revisions": [{"external_key": "...", "role_pack_version_id": "...", "content_sha256": "...", "artifact_id": "..."}],
  "career_card_revisions": [{"career_card_id": "...", "career_card_version_id": "...", "role_pack_version_id": "...", "content_sha256": "...", "revision_sha256": "...", "artifact_id": "...", "jd_artifact_id": "..."}],
  "match_rule_revisions": [{"career_card_id": "...", "rule_key": "...", "career_card_match_rule_id": "...", "career_card_version_id": "...", "content_sha256": "..."}],
  "jd_snapshot_revisions": [{"career_card_version_id": "...", "jd_evidence_snapshot_id": "...", "jd_evidence_id": "...", "external_snapshot_id": "...", "revision_sha256": "...", "source_artifact_id": "...", "source_digest_sha256": "...", "declared_source_digest_sha256": "..."}]
}
```

manifest 排除本机绝对目录和导入时间，并固定全部当前依赖。v2 另记录 explanation_contracts、claim_evidence_links 和来源状态。Python service / CLI 可按 knowledge_snapshot_id 回放兼容快照；不保存 Profile，不新增 HTTP API。内部三个语义维度和非互斥五类投影见 [解释契约 v2](CAREER_EXPLANATION_CONTRACT.md)。

### 已有数据库升级

继续运行同一导入命令即可升级。`scripts/career_map_revisions.py` 检测旧列并事务重建 `career_cards`、`jd_evidence_snapshots`、`career_card_match_rules`，保留原有主键、内容、引用与原始 artifact。新增当前 revision 与其历史并存。迁移仅在专用连接开始事务前暂时关闭即时 FK enforcement，提交前完整验证 FK；失败恢复原 schema 和数据。

旧库没有 manifest，也可能已存在过去导入造成的关联累积。迁移会保存这些历史行及 legacy digest，旧 Card 的 `jd_artifact_id` 保持 NULL（未能可靠确定），不会虚构其当年的精确依赖。升级后产生完整 manifest；升级前的记录可追踪，但不能声称可精确重放。

```sql
-- 当前知识快照。
SELECT knowledge_snapshot_id, manifest_sha256, manifest_json
FROM knowledge_snapshots WHERE is_current = 1;

-- 所有历史规则内容与生命周期。
SELECT rule_key, career_card_match_rule_id, content_sha256, rule_json,
       lifecycle_status, superseded_by_rule_id
FROM career_card_match_rules WHERE career_card_id = 'clinical_data_management';

-- 某次快照记录的原始 taxonomy（manifest 中取 taxonomy_revision）。
SELECT relative_path, content_sha256, raw_content
FROM source_artifacts WHERE artifact_id = :taxonomy_revision;
```

职业地图种子还登记 JD-driven 方向（清单见状态页）。它们是可探索的职业方向，不是泛化的 Role Pack；数据库会保留其所需 JD 语境和边界提示。

## 职业卡与 JD 证据试点

导入器读取具有冻结来源引用的 Career Card。卡片文件位于 `data/career_cards/*.json`，分别链接对应的 `docs/research/role-validation/**/candidate-evidence-v1.json`。其数据库记录是可重建的 SQL 投影，不替代 `data/careers/` 中仍标为 draft 的探索卡，也不把 Candidate evidence 升级为新的 Canonical 状态。

每个卡片均保留：稳定职责、典型交付物、岗位特定要求提示、直接/可迁移/部分可迁移事实、显性缺口、JD-dependent 范围及投递前核验动作。首轮不会抓取实时 JD，也不会自动产生匹配分数。

## Synthetic 解释查询 MVP

`career_card_match_rules` 只记录人工维护的匹配规则，绝不从职业卡自然语言猜测能力对应关系。`CareerCardExplanationService` 以一个 synthetic、逐条 `confirmed` 的 profile 和一个指定 Role Pack 为输入，输出三个独立语义维度及 `direct`、`transferable`、`partial`、`gap`、`unsupported` 五个非互斥展示分组；每条保留 profile evidence、Career Card claim、适用的 Role Pack 边界和 JD snapshot provenance；默认 JD 引用仅为 background research source。它不输出百分比分数、不排序、不写入 profile，也不改变既有 `/api/career-comparisons` 百分比接口。可解释方向由状态页所引规则源确定；其余职业卡在具备独立规则与回归用例前不会被该服务查询。

```powershell
python scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite
python scripts/query_career_card_explanation.py --database .local/career-map.sqlite `
  --profile-id synthetic-cdm-support-001 --role-pack clinical_data_management_v1
```

虚构 profile 位于 `data/career-map/career-card-explanation-test-profiles-v1.json`，仅用于验证直接、可迁移、部分、缺口与禁止推断边界，不能作为真实用户数据或职业结论。

## 最小查询示例

无需数据库 GUI 的网页试用：运行 `python scripts/serve_career_map.py`，浏览器打开 `http://127.0.0.1:8765`。职业地图、已有卡片和 synthetic 解释均只读；详细步骤见 [本地试用台](CAREER_MAP_DATABASE.md#local-read-only-viewer)。

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

## Taxonomy and filtering

职能族回答“做什么”，作为浏览主轴；产业生态回答“通常在哪里”，允许多选；生命周期回答“关联产品或证据的哪个阶段”，可不适用或尚待确认。三个维度不是上下级层级，也不是必填的三层职业分类。生命周期不是个人的初级/高级职业成长阶段。

### 真值与投影

`data/career-map/directions-v1.json` 仍是地图关联及适用性的人工维护源。Canonical Role Pack、Career Card、解释规则不随筛选逻辑改变。此修订保留原有的所有职业标签，不新增高校与上市阶段的推断关联。

每个 canonical assignment / JD-driven / beta direction 可带 `lifecycle_applicability`：

- `mapped`：至少一个阶段已标注，不表示标注穷尽所有适用阶段。
- `pending`：没有阶段标注，适用性待确认。
- `not_applicable`：没有阶段标注，且必须有 `lifecycle_review`，包含非空 `reviewed_by`、ISO 日期/时间 `reviewed_at`、`reason`。只在人工确认后使用。

初始化采用保守映射：空阶段为 pending，有阶段为 mapped；这不是“不适用”人工审核。旧 registry 未带字段时仍兼容：有阶段按 mapped、无阶段按 pending；绝不自动升级为 not_applicable。

SQL 的六张关联表继续投影阶段/生态/职能标签，不增加“待确认”或“不适用”伪阶段。适用性元数据由现有 `source_artifacts.raw_content` 保存，current manifest 的 `taxonomy_revision` 指向准确版本。网页只读取该已导入 artifact，不能越过导入器读取磁盘上更新的 taxonomy 文件。这一规模无需添加一套重复的元数据表；后续 SQL 场景需要适用状态索引时再做独立关系投影。

导入时校验状态、阶段有无及不适用审核记录；失败不激活新快照。修改/移除元数据、替换阶段标签，仍走完整源集合导入；同一源文件下 fresh 与 incremental 的当前状态一致，旧 registry 及 manifest 保留。

### 筛选契约

- 同维度多选为 OR；跨维度为 AND；不选即不限。
- 选项旁数量先忽略本维度选择，再应用其他维度条件，统计带该标签的方向数。多选数量可能重叠，不能直接相加；不是 JD 数量。
- 勾选或取消后立即发起 GET 查询，显示更新中状态，数量与结果随页面一起刷新；脚本不可用时回退为“应用筛选”按钮。0 项仍可选择和撤销，系统不悄悄修改用户筛选。
- 生命周期状态数量应用职能与生态条件、忽略阶段条件。选定阶段会排除 pending/not_applicable，并明确提示。
- 空结果表达为“当前知识库没有同时标注这些条件的方向”，不表示职业不存在；提供取消阶段限制且保留其他条件的链接。
- 方向标签的交集不证明特定“机构 × 阶段 × 职能”场景成立，也不生成匹配分数或改变 Profile 解释。

例如：选择某生态和阶段后出现空结果，只能说明当前标注没有该交集；取消阶段限制后可继续浏览该生态。不能据此断言某机构没有相关工作。

### 后续人工整理

典型/条件关联需要逐条领域依据，当前不将旧种子批量升级为已审核关系。未来可在 taxonomy source 增加审核后的关系元数据及场景约束；待有真实需求时再投影，不提前设计大型 ontology，也不依据文本相似度生成关联。

## Local read-only viewer

复用 SQLite 与解释器的独立只读页面，不挂载到原简历应用。不新增职业、职业卡、真实 Profile、JD 输入或 runtime target。

在仓库根目录运行：

```powershell
python -m pip install -e ".[schema_validation]"
python scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite
python scripts/serve_career_map.py
```

用浏览器打开 http://127.0.0.1:8765 。保持终端开启；按 Ctrl+C 停止。已安装并导入过的用户只需最后一条命令。端口占用时使用 `--port 8766`；`--database` 可指定另一个已导入的本地库。

1. 先按职能族浏览，按需选择生态或生命周期；同维度多选为 OR，跨维度为 AND，不选则不限。勾选或取消立即提交只读查询，数量与结果一起刷新，保留在操作的维度附近；脚本不可用时才显示“应用筛选”按钮。
2. 打开已有职业卡，阅读职责、交付物和边界。
3. 在有规则的方向选择已有虚构档案，查看解释。
4. 展开“证据与条件”，对照 all-of / any-of、缺失项、原始经历与 scope。
5. 展开来源，区分背景研究与人工支持关系，查看摘要差异及 revision。

生命周期区分已标注、待确认、不适用。选择具体阶段会排除后两者，页面显示其数量；空结果可取消生命周期限制并保留其他筛选。阶段不是每个职业的必填属性；标签交集不证明具体机构和阶段组合成立。完整规则及 taxonomy 源字段见 [筛选契约](CAREER_MAP_DATABASE.md#taxonomy-and-filtering)。

解释条目只展示一次，标签可以重叠。未命中可选迁移路径与没有 JD 的条件项不会被默认为 gap。当前页面不接受 JD 上下文，也不提供历史快照选择；历史回放仍使用已有 CLI。页面选择当前快照后，显式把其 ID 传给解释器，避免后续导入改变本次查询版本。

所有数据库连接均使用 SQLite `mode=ro`；目录连接另启用 query_only。页面只接受已有 synthetic profile ID，不接受档案内容或上传，也不写日志文件、缓存或数据库。访问仅限 loopback，启动器固定 127.0.0.1、关闭 debug/reloader；仅加载本机筛选增强脚本，无外部资源或第三方请求。终端可能显示常规 HTTP 请求日志（仅目录选项和虚构 ID）。这是本地开发试用台，不是公网部署入口；生产入口与真实用户隐私接入不在此试用台范围。

数据库缺失或版本过旧时先导入，不由网页自动建库。解释器不兼容时页面提示重新导入；保留旧知识与用户本地数据库，不自动迁移或修改它们。
