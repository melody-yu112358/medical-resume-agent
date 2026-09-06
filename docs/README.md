# 文档导航与活跃清单

先从核心入口进入，再按需要展开专题清单。“活跃”表示仍承担阅读、维护或验证职责，不表示设计已经实现。文档分类与冲突处理仍遵循 [Documentation sources](DOCUMENTATION_SOURCES.md)。

| 核心入口 | 阅读目的 |
| --- | --- |
| [项目首页](../README.md) | 项目能力与开始使用 |
| 本页：文档导航 | 阅读路径与活跃职责 |
| [架构说明](ARCHITECTURE.md) | 系统分层与实现路径 |
| [当前产品说明](RESUME_AGENT_PRODUCT.md) | 简历产品流程与边界 |
| [生成资产状态](CAREER_CATALOG_STATUS.md) | 当前库存与资产关联 |
| [Role Pack 版图](CAREER_ROLE_PACK_LANDSCAPE.md) | 岗位职责边界与验证依据 |
| [职业目录结构](CAREER_CATALOG_STRUCTURE.md) | 方向、角色簇、角色与别名 |
| [职业地图数据库](CAREER_MAP_DATABASE.md) | 导入、版本与回放 |

<details>
<summary>职业目录、解释与持续研究</summary>

| 要回答的问题 | 负责文档 | 不在该处重复维护 |
| --- | --- | --- |
| 当前有哪些资产，各自支持什么入口？ | [当前资产状态](CAREER_CATALOG_STATUS.md)，由机器源生成 | 其他说明文档不复制当前数量或 Pack/Card/规则/入口关联表 |
| 岗位有哪些职责边界，验证记录在哪里？ | [Role Pack 版图](CAREER_ROLE_PACK_LANDSCAPE.md) | 不维护库存与内部任务队列；精确语义仍来自 Pack JSON |
| 什么算角色，如何处理宽方向、角色簇与别名？ | [目录结构](CAREER_CATALOG_STRUCTURE.md) | 审查示例有日期，不作为持续更新的完整清单 |
| 如何采集、去重、分类并衡量扩展？ | [广度扩展方法](research/career-catalog-breadth-plan-v1.md) | 不维护批次工作量、排期或当前完成率 |
| 哪种方向适合何种研究深度？ | [中国覆盖矩阵](research/china-career-coverage-matrix-v1.md) | 启发式判断不是统计、库存或晋升状态 |
| 数据如何导入、版本化和回放？ | [数据库说明](CAREER_MAP_DATABASE.md) | 不重复职业库存 |
| 解释标签、适用性与来源如何定义？ | [解释契约](CAREER_EXPLANATION_CONTRACT.md) | 具体可解释方向读取规则源及状态页 |
| 如何浏览与筛选？ | [本地试用台](CAREER_MAP_LOCAL_VIEWER.md)、[筛选契约](CAREER_MAP_TAXONOMY.md) | 导航标签不决定转岗适配 |
| 候选研究、JD 来源和历史验证在哪里？ | [研究导航](research/README.md) | 研究词条不自动成为运行资产 |

</details>

<details>
<summary>活跃方法、验证与实现参考</summary>

- [研究方法](RESEARCH_METHOD.md)、[Role Pack 晋升规则](ROLE_PACK_GRADUATION.md)。
- [冻结案例基线](FROZEN_CASES_RELEASE_BASELINE.md)、[合成评估](SYNTHETIC_EVALUATION.md)、[对话模型评估](conversation_model_eval.md)。
- [验收说明](ACCEPTANCE.md)、[用户流程验收](user_flow_acceptance_checklist.md)、[行动质量门](action_quality_gate.md)。
- [数据政策](DATA_POLICY.md)、[简历 schema](RESUME_SCHEMA_V1.md)、[schema 兼容性](SCHEMA_COMPATIBILITY.md)。
- [模型集成](LLM_INTEGRATION.md)、[Meta 分析示例规范](META_ANALYSIS_EXAMPLE_SPEC.md)。

</details>

<details>
<summary>仍承担参考职责的产品设计与 v2 foundation</summary>

以下文档保持活跃入口；阅读时区分计划与已实现行为，当前用户流程以产品说明为准。独有职责尚未被承接时，不因数量目标提前归档。

- [产品手册 v2](PRODUCT_HANDBOOK_V2.md)、[用户旅程 v2](USER_JOURNEY_V2.md)、[领域模型 v2](DOMAIN_MODEL_V2.md)。
- [技术设计 v2](TECHNICAL_DESIGN_V2.md)、[AI 系统 v2](AI_SYSTEM_V2.md)、[MVP 执行计划 v2](MVP_EXECUTION_PLAN_V2.md)。
- [产品参考](PRODUCT.md)、[工作流参考](WORKFLOW.md)、[旅程层级](JOURNEY_LEVELS.md)。

</details>

<details>
<summary>维护工具、协作规则与分发文档</summary>

- [文档职责](DOCUMENTATION_SOURCES.md)、[Agent 治理](AGENT_GOVERNANCE.md)、[远端同步](REMOTE_SYNC_PROTOCOL.md)、[PR review 配置](CODEX_PR_REVIEW_SETUP.md)。
- [研究编排器](research/career-track-orchestrator-v1.md)、[dispatch connector](research/github-dispatch-connector-v1.md)、[event consumer](research/github-event-consumer-codex-task-connector-v1.md)：有对应工具实现，不能仅因版本号归为历史。
- [贡献约束](../AGENTS.md)、[Claude 入口](../CLAUDE.md)、[协作角色](../agents/)、[第三方声明](../THIRD_PARTY_NOTICES.md)、[英文首页](../README.en.md)。
- [Skill Lite](../skill-lite/README.md)、[Skill 入口](../skill-lite/medical-resume-skill/SKILL.md)、[Skill 参考材料](../skill-lite/medical-resume-skill/references/)：保留方法、生成参考、验证与交付文档的现有职责。
- [生态目录](skill-hub/ecosystem-catalog/README.md)、[目录贡献说明](skill-hub/ecosystem-catalog/CONTRIBUTING.md)、[轻量工具说明](../xhs-minitool/medical-experience-lite/README.md)。

</details>

**状态真值关系：** 机器源 → 生成的 `CAREER_CATALOG_STATUS.md` → 其他文档引用。状态页是唯一当前库存展示，不是第二份手工真值；数据库是按源导入的本地投影，未重新导入的数据库不一定等于仓库当前集合。

**历史与计划：** `BUILD_LOG`、`audits`、早期 Career Cards pilot、带阶段或版本的产品计划保留其当时语境；评分卡和 promotion record 保留当时证据及决定，不随库存更新而重写。旧计划中的阶段号、测试数和工作量不能当成当前进度。具体 PR 的实施顺序与工作量留在 PR 描述或任务记录。

历史资料统一从 [归档总入口](archive/README.md) 查找；它先链接原路径，本轮不移动文件。当前清单保留仍有职责的专题，不把最终数量目标当成强制归档条件。具体合并与迁移另行审查，归档子目录不另设重复导航。
