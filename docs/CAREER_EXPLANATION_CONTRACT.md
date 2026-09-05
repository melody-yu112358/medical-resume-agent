# Career Card 解释契约 v2

本契约仅服务 synthetic Profile ↔ 已配置 Career Card 的确定性解释。它不改变 Canonical Role Pack、runtime target、Claim Gate、旧百分比接口或个人资料入口。当前仍只解释 CDM 与器械应用支持两张已有卡，规则 registry 在原文件路径上升级为 `career-card-match-rules-v2`。

## 三个内部维度

每个 `items[]` 元素针对一条具体 Card claim，含稳定 `explanation_id` 和独立的边界目标 `boundary_target`：

| 维度 | 值 | 定义 |
| --- | --- | --- |
| evidence_relation | direct / transferable / none | 当前合法范围内的已确认事实与目标 claim 的关系；没有命中证据时为 none |
| support_completeness | complete / partial / no_evidence | 条件满足程度；人工声明的 support_ceiling 可把完整命中限制为 partial |
| inference_boundary | supported / unsupported / jd_dependent | supported 表示没有附加禁止推断边界，不等于已证明全部 claim；unsupported 描述不能从这些事实推出 boundary_target；jd_dependent 表示尚不能确定条件适用性 |

这三个维度不是互斥分类。例：R 数据分析可对数据严谨性提供 `transferable + partial` 支持，同时具有“不能推出数据库锁定所有权”的 `unsupported` 边界。禁止把 unsupported 翻译为“用户不适合这个职业”。

## 五个展示分组的稳定投影

`items` 是规范结果集合。`explanations` 保留 direct / transferable / partial / gap / unsupported 五个数组；同一 explanation_id 可以出现于多个分组，不应累加为匹配数量或得分。

| 条件 | 展示标签 |
| --- | --- |
| 可评估 + direct + complete | direct |
| 可评估 + transferable + complete 或 partial | transferable |
| 可评估 + partial | partial（可与 transferable 同时出现） |
| 当前明确适用 + no_evidence + supported boundary | gap |
| 有命中事实 + unsupported boundary | unsupported（可与其他标签同时出现） |
| 条件适用性尚不明确 | 不进入 gap；在 items 中保留 jd_dependent 和 assessment_status |

`classification` 留作规则的声明类别及 claim-kind 合法性约束，不直接决定展示分组。部分 direct 条件命中会输出 partial，不再消失；transferable 永远不会因为命中多项而升级为 direct。

## 逐 claim 条件与 gap

`match_mode=all_capabilities_present` 表示 all-of，`any_capability_present` 表示 any-of。不再使用 all-capabilities-absent 的大 gap 规则。

每项返回 requirement_operator、conditions_satisfied、capability_findings、matched_capability_codes、missing_capability_codes、required_missing_capability_codes。all-of 缺一个条件时为 partial；any-of 命中一个即可满足该组，其他未观察到的替代项保留在 missing_capability_codes，但不属于 required_missing_capability_codes。

`gap` 只表示当前提交的 Profile 对**已明确适用的具体 claim**没有证据；不是“不会”，不是“不适合”，也不为每个未命中的可选迁移路径制造 gap。部分缺失在 partial 的逐 capability 结果中显示，不需要捏造另一条笼统 gap。

applicability 分为 role_core、evidence_mapping、jd_dependent、senior_only、ownership。只有 role_core 和经明确 JD 上下文确认适用的条件项可产生 gap；evidence_mapping 是可选映射。Card 的 explicit_gap / jd_dependent_scope 不允许作为默认 role_core。

现有 CDM 数据库锁定和独立 EDC 建库已分别绑定各自 Card claim；器械独立支持也单独指向已有内容拆出的 jd_dependent_scope。Card 中 CDM direct 文本移除了当前三个条件不能证明的“受控资料归档”，与既有 Pack 直接支持例子的范围一致。没有修改 Canonical Pack。

## JD 上下文

没有 JD 时，条件项返回 `not_assessable_without_jd`。调用者可以提供经确认的上下文：

```json
{
  "jd_evidence_snapshot_ids": ["selected retained snapshot revision ID"],
  "applicable_rule_keys": ["cdm-lock-gap"],
  "confirmation_status": "confirmed",
  "seniority": "senior"
}
```

该上下文是显式的适用性声明，不是系统从 JD 文本自动推断的结论，也不会创建 claim_support。引用必须属于所选知识快照的目标 Card；未列出的条件项为 not_applicable_to_jd。senior_only 还要求 senior 上下文；失效 JD 不能用来确认适用性。分别返回 not_assessable_without_senior_jd 或 not_assessable_with_deprecated_jd。一般医学背景和协调支持不会因此被升级为所有权证据。

## 来源粒度

新表 `career_card_claim_snapshot_evidence` 区分：

- research_background：Card 的研究背景来源，显示为 **background research source**；不是该 claim 的直接支持证明。
- claim_support：仅接受 Card 源文件 `jd_evidence.claim_support` 内显式声明的 claim、snapshot_ids、reviewed_by、reviewed_at、review_note。缺少审核信息、无效引用或重复支持注释会拒绝导入。

现有所有卡默认只有 research_background；不会从全连接或文本相似度生成 claim_support。旧 `career_card_claim_jd_evidence` 历史行保留，但不再生成新的旧式全连接；迁移时仅将它们标为背景来源。

支持边固定到 snapshot revision。来源失效不会删除历史审核边，但 `claim_support_snapshot_ids` 仅列出所选快照中可用的支持来源。完整 provenance 仍显示失效关系、来源状态和摘要差异。分类依赖已确认个人事实和规则；JD 背景引用不充当个人经历。

## Provenance 与回放

每项 provenance 返回：profile_evidence_ids、career_card_claim_id、career_card_revision、role_pack_revision、role_pack_boundary_id（可为 null）、match_rule_revision、knowledge_snapshot_id、jd_evidence_snapshot_ids、jd_evidence_status、input_digest。另保留原有嵌套 Pack/Card/claim/negative mapping/JD 引用。

manifest 升级为 `career-map-knowledge-snapshot-v2`，增加：

- explanation_contracts：能力 registry、Profile schema、rule schema、JD context schema 的不可变 artifact IDs；
- claim_evidence_links：准确的背景/支持边及审核元数据；
- JD snapshot/source 状态及摘要核验标记；
- v2 解释器及其两个执行模块的源码指纹。

当前查询先选择 current manifest，此后**只读该 manifest 列出的 revisions**，不按后来的 is_current 或 rule 生命周期重新选取。historical query 使用指定 manifest；来源状态取该快照记录值，不混入未来状态。input_digest 对 Profile、目标和显式 JD 上下文计算，不保存 Profile；结果可重复计算，解释 ID 不含时间。

```powershell
python scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite
python scripts/query_career_card_explanation.py --database .local/career-map.sqlite `
  --profile-id synthetic-cdm-support-001 --role-pack clinical_data_management_v1
python scripts/query_career_card_explanation.py --database .local/career-map.sqlite `
  --profile-id synthetic-cdm-support-001 --role-pack clinical_data_management_v1 `
  --knowledge-snapshot-id knowledge-...
```

Python service 同样接受 knowledge_snapshot_id 和 jd_context。CLI 可用 `--jd-context path.json`。两者都需要已有的 schema_validation extra；本 PR 没有增加新的依赖包。

PR1/v1 快照仍可通过 SQL 查证，但 v2 服务不会用新语义伪造旧解释。manifest 版本、解释器版本或源码指纹不兼容时明确拒绝，必须使用其记录的解释器执行。没有新增 HTTP API 或修改 Flask 入口。

## 输入与规则校验

服务在执行判断前使用所选快照的 schema 校验完整 Profile（仍为 synthetic-only），并拒绝重复 evidence_id、非 confirmed 状态、未知 capability code 和非法 scope。合法但不在规则 allowed_scopes 内的事实不会满足该条件。允许 evidence=[] 表达明确的空证据集合。

规则在导入和查询时都校验 schema、能力词典、scope、classification/claim-kind、证据关系及所有权适用性组合。缺少可解释 Card/规则时明确失败，未知 code 不会被静默忽略。未接入真实用户、入口授权或隐私 PR3。
