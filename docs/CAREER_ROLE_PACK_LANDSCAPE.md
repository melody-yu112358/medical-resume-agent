# 中国医学背景职业 Role Pack 版图

## 1. 文档目的

本页是中国医学背景转职方向、Role Pack 边界、验证方式与扩展路径的总览入口。它用于解释仓库当前已经具备的职业语义和边界；不创建 routing target，不替代 `data/role-packs/*.json` 的规则，也不构成对任何候选人的岗位匹配或录用判断。

**状态读取规则：** canonical 状态以 `data/role-packs/*.json` 为准；Candidate 的证据状态以 `docs/research/role-validation/**` 为准；毕业条件以 `docs/ROLE_PACK_GRADUATION.md` 为准。本文说明均以这些资产为准，而非聊天记录或规划中的数量。

**数据库分类规则：** `data/career-map/directions-v1.json` 将本页的“产业生态 × 生命周期 × 职能族”登记为可查询的地图种子。该分类服务于浏览和解释，不反向修改任何 Role Pack 的职责边界、Canonical 状态或 runtime routing。

**目录结构与覆盖清单：** [医学背景职业目录结构审查](CAREER_CATALOG_STRUCTURE.md) 解释目录对象类型、职能与名称范围；当前资产及关联只见 [当前资产状态](CAREER_CATALOG_STATUS.md)。它是参考性审查，不修改现有机器契约。

## 2. 当前资产状态入口

当前 Pack、Card、目录模式、规则与 workflow 关联统一见 [当前资产状态](CAREER_CATALOG_STATUS.md)。本文不复制状态表；存在 Canonical 源不等于已开放入口或完成 cross-model validation。后者须读取对应可复核评价记录。研究方向不能因名称相近继承既有 Pack 的语义或成熟度。

## 3. 职业地图如何分类

### 使用范围：知识导航，不是转岗决策模型

这张地图帮助理解方向之间的区别与工作语境，不能仅凭所选生态、阶段或职能判断医学生适合哪种工作。转岗解释的主线是：具体目标职责/岗位要求 → 已确认个人证据 → 直接或可迁移关系 → 尚缺的证据和禁止推断边界；具体要求的适用性仍需 JD 核验。教育资格、工作条件、个人偏好与实际转型路径等尚未完整进入当前解释服务，不能宣称已经完成全面职业决策支持。

当前目录包含“考博/保研”这样的申请目标、“健康科技”这样的宽方向和 CDM 等职能方向，并非同粒度的完整职业分类。产业生态也混合机构类型与业务领域。因此保留它们作为探索标签，不把标签当成排他职业编码或用户能力；生命周期是其中更偏行业知识的可选维度。未来可逐步规范目录对象类型和关联粒度，本阶段不据此重写 Canonical Pack。

岗位不能只按“药企”“器械”或“上市前/后”单独分类。传统药企、器械和 AI 医疗描述的是**产业生态**；上市前、上市后描述的是**产品生命周期**；CRA、CDM、PV、MSL 等描述的是**职能**。它们是可交叉的观察维度，不是每个职业都必须填满的三层层级。浏览以职能族为主，生态与生命周期为可选条件；高校、教学或其他方向不能被强制贴上产品上市阶段。

方向级标签允许多对多关联，但分别关联多个生态和阶段，不代表任意生态与阶段的组合均已成立。典型关联、条件关联及具体机构场景需进一步人工审查；当前标签不冒充已审核的联合场景或穷尽职业覆盖。具体岗位仍需 JD 核验。

生命周期状态单独记录：`mapped`（有阶段标注）、`pending`（待确认）、`not_applicable`（经审核不适用）。空关联不能自动判定不适用；不适用不是新增阶段。详见 [职业地图筛选契约](CAREER_MAP_DATABASE.md#taxonomy-and-filtering)。

### 3.1 产业生态：岗位在哪类组织中发生

| 产业生态 | 典型组织或场景 |
| --- | --- |
| 医院 / 高校 / 科研 | 医院科研、研究中心、实验室、学术申请 |
| Pharma / Biotech | 药物研发、医学事务、PV、注册、商业化 |
| CRO / SMO | 临床开发外包、研究中心支持、数据和试验运行 |
| Medical Device / IVD | 器械产品、临床应用、培训、售后和注册 |
| Digital Health / AI | 医疗数据、数字健康、算法或产品技术 |
| Consulting / Commercial services | 咨询、市场准入、商业分析和专业服务 |
| Medical Communications | 医学写作、科学传播、内容质量控制 |
| RWE / HEOR / Public-health evidence ecosystem | 真实世界研究、卫生经济、结局与公共卫生证据 |

### 3.2 产品生命周期：岗位服务于哪个阶段

| 生命周期 | 常见工作重点 |
| --- | --- |
| Discovery / Preclinical | 研究问题、实验、早期证据与机制 |
| Clinical Development | 临床研究设计、中心执行、数据和试验运行 |
| Registration / Pre-launch | 注册资料、标准、申报准备和上市前支持 |
| Launch / Medical | 医学事务、科学交流、疾病领域信息 |
| Post-marketing Safety | PV、安全信息、质量与风险管理 |
| Evidence / Access | RWE、HEOR、市场准入和价值证据 |
| Commercial | 销售、客户、商业分析和区域执行 |
| Lifecycle Management | 上市后产品、证据、培训、质量和跨职能维护 |

### 3.3 职能族：岗位实际在做什么

Research、Clinical Development/Operations、Data/Statistics、Safety、Regulatory、Medical Affairs、Medical Writing/Scientific Communications、Device Clinical/Application、RWE/HEOR/Access、Product/Technology、Commercial。

例如，PV 可以位于 Pharma/Biotech 的 Post-marketing Safety 阶段和 Safety 职能族；Device Application 可以位于 Medical Device/IVD 生态、Lifecycle Management 阶段和 Device Clinical/Application 职能族。三维定位帮助保留真实边界，而不是因共享“医学”背景而强行合并 Role Pack。

### 3.4 什么时候值得做 Deep Role Pack

一个职业进入 Canonical Role Pack pipeline，至少同时考虑：

1. 与中国医学背景转职具有明确相关性；
2. 多公司 JD 能证明 stable core，而不是单一雇主的特殊职责；
3. 可以反复使用且可审计的 transferable evidence mappings；
4. 可以定义明确的 negative / ownership boundaries；
5. 岗位含义不高度依赖单个 employer、客户、产品、地区或 JD。

不满足这些条件时，优先保留为 Validated Beta Cluster 或 JD-driven Generalist。覆盖率不是将所有职位强行做成 Deep Pack 的理由。

## 4. 岗位语义与边界摘要

以下是岗位语义摘要，不是 `data/career_cards` 的库存。职责中的“稳定”表示跨多份 JD 的共同信号；“JD-dependent / senior”表示不能自动套用到每一位求职者的范围。精确边界仍以对应 Pack 为准。

### 4.1 考博 / 保研 / 学术申请

- **英文 / ID：** Doctoral / academic application；`doctoral_v1`。
- **范围：** 保研、夏令营、直博、博士申请与研究型项目申请。
- **稳定表达重点：** 研究问题、方法深度、证据检索、分析、学术产出与研究潜力。
- **不得升级：** 协助研究、课程项目或局部实验不能自动成为独立课题所有权、第一作者贡献、课题管理或未提供的成果。

### 4.2 临床科研

- **英文 / ID：** Clinical Research；`clinical_research_v1`。
- **常见标题：** Clinical Research Assistant、临床科研助理、医院科研支持。
- **稳定表达重点：** 以临床问题为中心的研究设计支持、方案/资料、数据或文献工作、受控研究流程与团队协作。
- **不得升级：** 研究协助、文档或 CRF 工作不自动成为独立监查、研究中心全周期、PI 或 sponsor 所有权。

### 4.3 MSL / 医学事务

- **英文 / ID：** Medical Affairs / Medical Science Liaison；`medical_affairs_v1`。
- **常见标题：** MSL、Medical Affairs Associate、医学信息支持。
- **稳定表达重点：** 文献与证据解读、疾病领域知识、医学信息转译与内部医学支持。
- **不得升级：** 内部汇报、论文或文献阅读不自动成为外部 KOL、客户、执行层或医学策略所有权。

### 4.4 医疗数据 / 健康科技

- **英文 / ID：** Health AI / Data / digital health；`health_ai_data_v1`。
- **范围：** 医疗数据、数字健康、健康科技相关的研究或早期岗位材料。
- **稳定表达重点：** 数据准备、分析框架、临床领域解释与结果沟通。
- **不得升级：** 学术分析、课程模型或脚本不自动等于生产模型、数据产品、临床验证或产品路线图所有权。

### 4.5 临床运营协调

- **英文 / ID：** Clinical Operations / trial coordination；`clinical_operations_v1`。
- **常见标题：** Clinical Operations、Clinical Trial Coordinator、临床项目协调。
- **稳定职责：** 研究资料、数据质量跟进、既定 SOP/流程支持与受限范围内的协调。
- **不得升级：** coordination 不等于项目/运营/KPI/供应商/患者/团队所有权；文档支持不等于流程最终责任。

### 4.6 临床研究协调 / CRA 支持

- **英文 / ID：** Clinical Research Associate、CRA I、Clinical Research Associate I；`clinical_research_associate_v1`。
- **典型 junior / mid-level 范围：** 已确认的研究执行支持、资料/CRF 维护、缺失数据和 query 跟进、GCP 流程支持及内部研究团队协调。
- **JD 研究记录：** 来源、保留摘录与当时的 qualifying 判定见 [role-validation 研究索引](research/README.md)。以下边界是源语义摘要，不是逐 claim JD 支持。

- **稳定职责：** 受限范围内的研究执行支持、研究资料/CRF 维护、缺失数据与 query 跟进、GCP 对齐流程支持和内部协调。
- **JD-dependent / senior：** 独立监查、中心全周期、招募/预算、项目/项目群、PI/sponsor 对外沟通、团队管理或最终合规责任。
- **医学背景迁移：** 已确认的 CRF、资料、研究执行或 GCP 训练可直接/部分映射；临床轮转、病例讨论可提供语境但不自动构成 CRA 经验证据；纯实验研究应保留为 gap。
- **关键边界：** study coordination ≠ site ownership；CRF/document support ≠ independent monitoring；内部沟通 ≠ PI/sponsor ownership。

### 4.7 临床数据管理 / CDM 支持

- **英文 / ID：** Clinical Data Management、Clinical Data Management Specialist、Clinical Data Administrator；`clinical_data_management_v1`。
- **典型 junior / mid-level 范围：** 临床研究数据质量、query 跟进、CRF/EDC 支持和受控数据文档支持。
- **JD 研究记录：** 来源、保留摘录与当时的 qualifying 判定见 [role-validation 研究索引](research/README.md)。以下边界是源语义摘要，不是逐 claim JD 支持。

- **稳定职责：** 数据核对/清理、缺失数据或 discrepancy/query 跟进、受控数据文档、GCP/SOP 对齐的数据质量支持、数据问题协调与对账支持。
- **JD-dependent / senior：** database lock、最终交付、预算/客户/供应商、EDC build/configuration、CRF 设计、编码/编程专长、团队管理和最终质量责任。
- **医学背景迁移：** CRF/query、受控资料和研究数据质量经历可直接支持；R/Python 数据分析可迁移但不等于 CDM、GCP 或 EDC 经验；database lock / EDC build 必须有直接证据。
- **关键边界：** data cleaning/review ≠ database-lock ownership；CRF/EDC support ≠ EDC-build authority；analysis ≠ CDM project/client/team ownership；support/coordination ≠ project management。

### 4.8 医疗器械临床 / 应用支持

- **英文 / Role Pack ID：** Clinical Application Specialist、IVD Application Specialist、Clinical Support Specialist；`medical_device_clinical_application_specialist_v1`。
- **范围：** 初中级的产品/应用培训、受限产品范围内的现场技术与工作流支持、用户反馈传递、内部/渠道赋能及学术活动支持。
- **JD 研究记录：** 来源、保留摘录与当时的 qualifying 判定见 [role-validation 研究索引](research/README.md)。以下边界是源语义摘要，不是逐 claim JD 支持。

- **稳定职责：** 产品专属临床/应用培训、产品范围内的技术与工作流支持、用户反馈收集/传递、内部/渠道赋能和学术活动支持。
- **JD-dependent / senior：** 产品组合或区域所有权、销售 KPI/收入/市场覆盖、临床决策或患者照护、手术责任、产品路线图/研发、注册申报、专家网络和人员管理。
- **医学背景迁移：** 医学、检验、影像、护理或临床沟通可支持产品理解；不能替代设备实操、客户培训或现场技术支持。临床轮转与学术活动组织仅为部分映射。
- **关键边界：** application/training support ≠ clinical decision/procedure ownership；feedback ≠ product roadmap；application support ≠ sales KPI；coordination/support ≠ project ownership。

### 4.9 Pharmacovigilance / Drug Safety（PV）

- **英文 / Role Pack ID：** Pharmacovigilance Associate、Drug Safety Specialist、Safety Operations、PV Physician；`pharmacovigilance_drug_safety_v1`。
- **范围：** 受监管安全信息接收/处理/跟进支持、安全文档/文献/reconciliation 支持、GVP/SOP 质量与检查准备支持，以及分配范围内的安全信息协调。
- **JD 研究记录：** 来源、保留摘录与当时的 qualifying 判定见 [role-validation 研究索引](research/README.md)。以下边界是源语义摘要，不是逐 claim JD 支持。

- **稳定职责：** 受监管安全 case 支持、安全文档/文献/reconciliation、GVP/SOP 质量支持、指定范围内协调和直接分配时的报告支持。
- **JD-dependent / senior：** safety strategy、signal detection/benefit-risk、QPPV/PSMF、监管机关沟通、IND/NDA/RMP、团队管理和超出直接证据的医学判断。
- **医学背景迁移：** AE 记录/随访协助、受控安全资料和流程培训可支持受监督 PV 支持；医学文献与严谨记录可迁移但不替代 GVP/ICSR；临床轮转和病历记录仅提供部分临床语境。
- **关键边界：** AE documentation ≠ ICSR submission ownership；literature/safety support ≠ signal detection 或 benefit-risk ownership；filing/support ≠ QPPV / PSMF；研究协调 ≠ safety strategy 或最终监管责任。

### 4.10 法规医学写作支持

- **英文 / Role Pack ID：** Regulatory Medical Writing；`regulatory_medical_writing_v1`。
- **范围：** Protocol、CSR、IB、clinical summary 等受控临床/注册文件的已确认撰写或审阅支持，文献与临床数据综合，模板/SOP/GCP/ICH/质量支持，以及受限的跨职能 review comment、版本与交付协调。
- **JD 研究记录：** 来源、保留摘录与当时的 qualifying 判定见 [role-validation 研究索引](research/README.md)。以下边界是源语义摘要，不是逐 claim JD 支持。

- **稳定职责：** 已确认范围内的受控文件支持、证据综合、质量与版本协调。
- **关键边界：** academic writing 不等于 regulatory medical writing；drafting/review support 不等于 submission ownership；文献综合不等于 CSR/Protocol author ownership；内部协调不等于客户、项目或法规策略所有权。

## 5. Role Pack 如何毕业

```text
中国真实 JD 研究
  → qualifying / provenance 审核
  → JD 与 employer coverage
  → stable core / JD-dependent separation
  → fixed personas 与 persona × JD exercise
  → direct / transferable / partial / gap mappings
  → machine-readable negative mappings
  → Independent Reviewer
  → domain evaluation（usefulness、factuality、ownership、unsupported-claim audit）
  → schema / provenance / invariant tests 与 full regression
  → eligible_for_canonicalization
  → traceable human approval
  → Canonical v1 JSON
  → generated Skill projections
  → Canonical promotion PR
  → human review / merge
```

每一步的目的分别是：不把搜索摘录当证据；不把一家公司的职责当通用语义；不把“参与”变成“所有权”；并让最终的 JSON 规则、生成结果和回归测试都有可审计来源。只有人类 GitHub 身份可以批准 promotion/merge；共享 ChatGPT/Codex 账号不是审批身份。

## 6. 当前测试体系

| 测试层 | 核查内容 |
| --- | --- |
| Evidence / provenance | qualifying JD 和 employer count、digest 可复算、excluded/pending 证据不计数。 |
| Domain cases | positive、transferable、partial、gap/negative persona 在多个 JD/employer 中的映射。 |
| Factuality / ownership | 不得把 contributed 改为 led，support 改为 ownership，partial 改为 full，或新增数字、成果、监管/商业/管理责任。 |
| Role Pack invariants | Role Pack 只能改变 priority/emphasis；confirmed facts、evidence IDs、责任范围与依赖关系不得漂移。 |
| Generated artifacts | canonical JSON 通过 generator 生成 Skill references；`generate_skill_role_pack_reference.py --check` 发现 drift。 |
| Frozen release regression | 正常经历、信息不足、责任模糊、可能夸大与模型不可用降级等固定案例。 |
| Full pytest | 以当前 `pytest -q` 实际收集和通过结果为准，不把历史测试数量写成长期事实。 |

## 7. Domain validation 与 Cross-model validation

**Canonical v1（domain validated）** 验证职业语义是否稳定：真实 JD/company 覆盖、stable core、personas、证据/负向映射、usefulness、factuality、ownership、0 critical unsupported claims，以及回归测试和 human approval。

**Cross-model validated** 是 Canonical v1 之后的 hardening：需要真实 exact model/version/config、isolated runs、prompt/input/output 和 digest、跨模型 unsupported-claim rate 及 model-version regression。缺少模型配置不能被写成 domain validation 失败，也不能伪造为已通过。

## 8. 中国市场覆盖策略与扩展路径

目录广度、来源知识深度、简历 Pack 支持与显式解释支持分别衡量。采集、去重、coverage 分母和内部参考目标统一见 [广度扩展方法](research/career-catalog-breadth-plan-v1.md)；职责整理见 [目录结构](CAREER_CATALOG_STRUCTURE.md)；研究层级建议见 [覆盖矩阵](research/china-career-coverage-matrix-v1.md)。本文不维护批次顺序、工作量或任务优先级。

先收录可追溯的浅层候选，再按独立 graduation gate 深化；名称相近不自动升级。Cross-model hardening 与 domain validation 分别留证。雇主、支付方、产品、区域或商业责任差异大的岗位，继续以具体 JD 确定适用要求，不强建 universal Pack。

## 9. Source of truth 与文档治理

| 信息 | authoritative source |
| --- | --- |
| Role Pack 语义与当前 canonical 数量 | `data/role-packs/*.json` |
| Generated Skill rules | `skill-lite/medical-resume-skill/references/role-packs.md`、`role-pack-rules.json`（生成物，禁止手改） |
| Role Pack 毕业门槛 | `docs/ROLE_PACK_GRADUATION.md` |
| CRA/CDM/Device/PV 的 JD 与 domain evidence | `docs/research/role-validation/**` |
| 中国职业覆盖规划 | `docs/research/china-career-coverage-matrix-v1.md` |
| 岗位边界、验证与扩展入口 | 本文档 |
| 当前库存与 Pack/Card/规则/入口关联展示 | [当前资产状态](CAREER_CATALOG_STATUS.md)，由机器源生成 |
| 文档分类规则 | `docs/DOCUMENTATION_SOURCES.md` |

当说明性文档与 machine-readable source 冲突时，以 machine-readable source 为准；历史文档只保留追溯价值，不能改变运行时或 canonical 语义。
