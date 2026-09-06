# 历史资料与归档索引

这是唯一总归档入口。普通历史资料已迁移，原文日期与结论保留；每份移动原件标注原路径、Git 版本与当前承接入口。历史数量不是当前库存，当前资产只见 [生成状态页](../CAREER_CATALOG_STATUS.md)，活跃阅读路径见 [文档导航](../README.md)。子目录不另设 README 或阶段总结。

## 已移动的历史原件

| 保存范围 | 原件位置 | 当前承接职责 |
| --- | --- | --- |
| 开发日志 | [BUILD_LOG](history/BUILD_LOG.md) | 当前产品和架构说明；旧测试数按原日期读取 |
| 早期 Career Cards / conversation pilot | [Career Cards](pilots/CAREER_CARDS.md)、[LLM-first PoC](pilots/llm-first-conversation-poc.md) | [研究方法](../RESEARCH_METHOD.md)、[当前产品](../RESUME_AGENT_PRODUCT.md) |
| 产品与工作流旧说明 | [PRODUCT](product/PRODUCT.md)、[WORKFLOW](product/WORKFLOW.md) | [产品原则与路径边界](../RESUME_AGENT_PRODUCT.md#product-principles-and-exploration-boundary)；legacy 规则原文保留 |
| Schema 迁移提案 | [SCHEMA_COMPATIBILITY](product/SCHEMA_COMPATIBILITY.md) | [现有契约关系](../RESUME_SCHEMA_V1.md#contract-relationships)；提案不冒充已实现兼容性 |
| 分类与试用台旧说明 | [TAXONOMY](catalog/CAREER_MAP_TAXONOMY.md)、[VIEWER](catalog/CAREER_MAP_LOCAL_VIEWER.md) | [数据库：筛选](../CAREER_MAP_DATABASE.md#taxonomy-and-filtering)、[只读试用](../CAREER_MAP_DATABASE.md#local-read-only-viewer) |
| 审计与确认门设计 | [Action 4](audits/action4_reuse_map.md)、[Action 5](audits/action5_role_pack_gap.md)、[文档审计](audits/documentation-boundaries-2026-09-06.md)、[确认门测试设计](design/action4_confirmation_gate_tests.md) | 保存发现、负向测试设计与当时决策；当前实现见产品说明 |
| 一次性执行模板 | [Wave 2](plans/wave2_launch_templates.md) | 不作为新任务指令；新执行记录放对应 Issue / PR |
| 已结束来源扫描 | [相邻方向扫描](../research/archive/adjacent-career-job-source-inventory-2026-08-17.md)、[医疗 AI 产品研究](../research/archive/healthcare-ai-product-manager-jobs-2026-08-17.md) | [广度方法](../research/career-catalog-breadth-plan-v1.md)及新批次记录；原始招聘状态只代表采集时所见 |

## 逻辑归档：历史证据保留原路径

以下只改变阅读归属，文件与其相邻的 JSON、快照、digest 和机器引用保持原样。历史证据仍能支持现有资产的审计，不作为新的运行规则或当前状态页。

| 原路径 | 保留原因 |
| --- | --- |
| [Candidate 成熟度评估](../ROLE_VALIDATION_CANDIDATE_MATURITY.md) | 2026-08-30 阶段判断与当时门槛，不能改写成后来的晋升结果 |
| [CRA](../research/role-validation/cra/) | scorecard、promotion、post-merge validation 原件 |
| [CDM](../research/role-validation/cdm/) | scorecard、domain review、promotion 原件 |
| [Device](../research/role-validation/device-clinical-application/) | scorecard、promotion 原件 |
| [PV](../research/role-validation/pharmacovigilance/) | scorecard、domain review、promotion 原件 |
| [RMW](../research/role-validation/regulatory-medical-writing/) | scorecard、domain review、promotion、graduation audit 原件 |

v2 foundation、正在使用的验证方法、工具契约与 legacy 旅程说明保持活跃。归档不删除 provenance、不重写历史验收、不更改审批或执行规则。旧文中的仓库路径按当时 Git 版本解释；可点击相对链接已随迁移修复。
