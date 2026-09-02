# 中国医学背景职业 Role Pack 版图

## 1. 文档目的

本页是中国医学背景转职方向、Role Pack 成熟度、验证方式与近期路线图的总览入口。它用于解释仓库当前已经具备的职业语义和边界；不创建 routing target，不替代 `data/role-packs/*.json` 的规则，也不构成对任何候选人的岗位匹配或录用判断。

**状态读取规则：** canonical 状态以 `data/role-packs/*.json` 为准；Candidate 的证据状态以 `docs/research/role-validation/**` 为准；毕业条件以 `docs/ROLE_PACK_GRADUATION.md` 为准。下表和说明均以这些资产为准，而非聊天记录或规划中的数量。

## 2. 当前岗位版图总览

| 成熟度池 | 当前方向 | 说明 |
| --- | --- | --- |
| Canonical v1（domain validated） | 考博 / 保研、临床科研、MSL / 医学事务、医疗数据 / 健康科技、临床运营协调、临床研究协调 / CRA 支持、临床数据管理 / CDM 支持、医疗器械临床 / 应用支持 | 当前有 canonical JSON，并已生成 Skill projection。是否已接入具体运行时仍是独立决策。 |
| Candidate（有专门中国 JD 证据） | Pharmacovigilance / Drug Safety（PV） | 有独立 corpus、personas、映射和负向边界；截至本文档状态，尚无 canonical JSON，不应称为可执行或可路由 Role Pack。 |
| 研究/规划中的候选方向 | Medical Writing / Scientific Communications、Regulatory Affairs、RWE、HEOR | 覆盖矩阵记录其产品策略；除非存在对应 Candidate corpus，不能把“研究过”称为 Candidate 或 Canonical。 |
| JD-driven Generalist | Market Access、Healthcare Product、Healthcare Consulting、Commercial / Business Analytics、Healthcare / Project Operations、Medical Sales / Commercial | 这些方向的雇主、行业与 ownership 差异很大，当前应以具体 JD 和明确缺口为中心服务，而非强行建立通用 Deep Pack。 |

### 2.1 Canonical v1（domain validated）

| 中文岗位族 | 英文名称 / 常见别名 | Role Pack ID | canonical source | Skill projection | Cross-model validation |
| --- | --- | --- | --- | --- | --- |
| 考博 / 保研 / 学术申请 | Doctoral / academic application | `doctoral_v1` | 是 | 是 | pending / not yet recorded |
| 临床科研 | Clinical Research | `clinical_research_v1` | 是 | 是 | pending / not yet recorded |
| MSL / 医学事务 | Medical Affairs / Medical Science Liaison | `medical_affairs_v1` | 是 | 是 | pending / not yet recorded |
| 医疗数据 / 健康科技 | Health AI / Data / digital health | `health_ai_data_v1` | 是 | 是 | pending / not yet recorded |
| 临床运营协调 | Clinical Operations / trial coordination | `clinical_operations_v1` | 是 | 是 | pending / not yet recorded |
| 临床研究协调 / CRA 支持 | Clinical Research Associate / CRA support | `clinical_research_associate_v1` | 是 | 是 | pending / not yet recorded |
| 临床数据管理 / CDM 支持 | Clinical Data Management / CDM support | `clinical_data_management_v1` | 是 | 是 | pending / not yet recorded |
| 医疗器械临床 / 应用支持 | Medical Device Clinical / Application Specialist | `medical_device_clinical_application_specialist_v1` | 是 | 是 | pending / not yet recorded |

`pending / not yet recorded` 表示当前没有可复核的 cross-model conformance 记录；它不是 Canonical v1 domain validation 的否定，也不应被写成该职业不正式。

### 2.2 Candidate / future promotion pipeline

| 方向 | 当前仓库状态 | 不应误写为 |
| --- | --- | --- |
| Pharmacovigilance / Drug Safety（PV） | Candidate evidence：10 条 qualifying JD、8 家 employer；有固定 personas、机器可读负向映射和 domain-evaluation asset。尚无 canonical JSON 或 promotion PR。 | 已 Canonical v1、可把安全支持直接写成 ICSR/信号/获益风险所有权。 |

## 3. Canonical / Candidate 岗位职业卡

以下职业卡总结保存的 JD 与 canonical/Candidate 语义。职责中的“稳定”表示跨多份 JD 的共同信号；“JD-dependent / senior”表示不能自动套用到每一位求职者的范围。

### 3.1 考博 / 保研 / 学术申请

- **英文 / ID：** Doctoral / academic application；`doctoral_v1`。
- **范围：** 保研、夏令营、直博、博士申请与研究型项目申请。
- **稳定表达重点：** 研究问题、方法深度、证据检索、分析、学术产出与研究潜力。
- **不得升级：** 协助研究、课程项目或局部实验不能自动成为独立课题所有权、第一作者贡献、课题管理或未提供的成果。

### 3.2 临床科研

- **英文 / ID：** Clinical Research；`clinical_research_v1`。
- **常见标题：** Clinical Research Assistant、临床科研助理、医院科研支持。
- **稳定表达重点：** 以临床问题为中心的研究设计支持、方案/资料、数据或文献工作、受控研究流程与团队协作。
- **不得升级：** 研究协助、文档或 CRF 工作不自动成为独立监查、研究中心全周期、PI 或 sponsor 所有权。

### 3.3 MSL / 医学事务

- **英文 / ID：** Medical Affairs / Medical Science Liaison；`medical_affairs_v1`。
- **常见标题：** MSL、Medical Affairs Associate、医学信息支持。
- **稳定表达重点：** 文献与证据解读、疾病领域知识、医学信息转译与内部医学支持。
- **不得升级：** 内部汇报、论文或文献阅读不自动成为外部 KOL、客户、执行层或医学策略所有权。

### 3.4 医疗数据 / 健康科技

- **英文 / ID：** Health AI / Data / digital health；`health_ai_data_v1`。
- **范围：** 医疗数据、数字健康、健康科技相关的研究或早期岗位材料。
- **稳定表达重点：** 数据准备、分析框架、临床领域解释与结果沟通。
- **不得升级：** 学术分析、课程模型或脚本不自动等于生产模型、数据产品、临床验证或产品路线图所有权。

### 3.5 临床运营协调

- **英文 / ID：** Clinical Operations / trial coordination；`clinical_operations_v1`。
- **常见标题：** Clinical Operations、Clinical Trial Coordinator、临床项目协调。
- **稳定职责：** 研究资料、数据质量跟进、既定 SOP/流程支持与受限范围内的协调。
- **不得升级：** coordination 不等于项目/运营/KPI/供应商/患者/团队所有权；文档支持不等于流程最终责任。

### 3.6 临床研究协调 / CRA 支持

- **英文 / ID：** Clinical Research Associate、CRA I、Clinical Research Associate I；`clinical_research_associate_v1`。
- **典型 junior / mid-level 范围：** 已确认的研究执行支持、资料/CRF 维护、缺失数据和 query 跟进、GCP 流程支持及内部研究团队协调。
- **真实 qualifying JD（8 条 / 6 家 employer）：**

| 公司 | 岗位名称 | 城市 | 来源类型 | qualifying | 主要职责信号 |
| --- | --- | --- | --- | --- | --- |
| Fosun Kite (Shanghai) Biotechnology | Clinical Research Associate (CRA) | 上海 | employer careers page | 是 | 中心/资料、源数据、CRF/query、AE/SAE 跟进 |
| Risen Pharma | Clinical Research Associate (CRA) | 上海/苏州 | employer careers page | 是 | 试验实施/监查、数据完整性、研究者沟通 |
| InventisBio | Clinical Research Associate (CRA) | 上海 | employer careers page | 是 | 伦理资料、监查、源文件、AE 跟进 |
| KangaBio | Clinical Research Associate (CRA) | 上海 | employer careers page | 是 | 中心访视、合规、数据质量 |
| Cellgenes Biotechnology | Clinical Research Associate (CRA) | 广州 | employer careers page | 是 | 分配中心、SDV/CRF、GCP/SOP |
| ICON China | Clinical Research Associate I / Clinical Research Associate | 上海 | employer careers page | 是 | set-up/monitoring coordination、status report、sponsor query support |

- **稳定职责：** 受限范围内的研究执行支持、研究资料/CRF 维护、缺失数据与 query 跟进、GCP 对齐流程支持和内部协调。
- **JD-dependent / senior：** 独立监查、中心全周期、招募/预算、项目/项目群、PI/sponsor 对外沟通、团队管理或最终合规责任。
- **医学背景迁移：** 已确认的 CRF、资料、研究执行或 GCP 训练可直接/部分映射；临床轮转、病例讨论可提供语境但不自动构成 CRA 经验证据；纯实验研究应保留为 gap。
- **关键边界：** study coordination ≠ site ownership；CRF/document support ≠ independent monitoring；内部沟通 ≠ PI/sponsor ownership。
- **验证：** 8 条 JD / 6 employer、固定 personas、正/可迁移/部分/负向 domain cases；中位 usefulness 4/5，factuality `PASS`，ownership `PASS`，critical unsupported claims `0`。cross-model validation pending。

### 3.7 临床数据管理 / CDM 支持

- **英文 / ID：** Clinical Data Management、Clinical Data Management Specialist、Clinical Data Administrator；`clinical_data_management_v1`。
- **典型 junior / mid-level 范围：** 临床研究数据质量、query 跟进、CRF/EDC 支持和受控数据文档支持。
- **真实 qualifying JD（8 条 / 8 家 employer）：**

| 公司 | 岗位名称 | 城市 | 来源类型 | qualifying | 主要职责信号 |
| --- | --- | --- | --- | --- | --- |
| 3D Medicines | Clinical Data Management | 中国 | 保存的 JD snapshot | 是 | CRF/数据质量/受控流程 |
| Beijing Immunochina Pharmaceuticals | Clinical Data Management Specialist | 北京 | 保存的 JD snapshot | 是 | 数据问题与资料支持 |
| Primera | Clinical Data Management Manager | 北京 | 保存的 JD snapshot | 是 | CDM 流程信号（管理范围为 JD-dependent） |
| AstraZeneca China | Senior/Principal Clinical Data Manager | 中国 | 保存的 JD snapshot | 是 | 数据管理/质量（资深范围为 JD-dependent） |
| Novotech | Clinical Data Administrator (DM) | 北京 | 保存的 JD snapshot | 是 | 受控资料与数据支持 |
| 上海市临床研究中心 | Clinical Data Manager | 上海 | 保存的 JD snapshot | 是 | 临床研究数据流程 |
| Beijing Norhomme Pharmaceutical Technology | Clinical Data Management Manager (CRO) | 中国 | 保存的 JD snapshot | 是 | CRO 数据管理信号 |
| 江苏恒瑞医药 | Clinical Data Management Project Manager | 中国 | 保存的 JD snapshot | 是 | 项目级职责仅作 JD-dependent 信号 |

- **稳定职责：** 数据核对/清理、缺失数据或 discrepancy/query 跟进、受控数据文档、GCP/SOP 对齐的数据质量支持、数据问题协调与对账支持。
- **JD-dependent / senior：** database lock、最终交付、预算/客户/供应商、EDC build/configuration、CRF 设计、编码/编程专长、团队管理和最终质量责任。
- **医学背景迁移：** CRF/query、受控资料和研究数据质量经历可直接支持；R/Python 数据分析可迁移但不等于 CDM、GCP 或 EDC 经验；database lock / EDC build 必须有直接证据。
- **关键边界：** data cleaning/review ≠ database-lock ownership；CRF/EDC support ≠ EDC-build authority；analysis ≠ CDM project/client/team ownership；support/coordination ≠ project management。
- **验证：** 8 条 JD / 8 employer、可复算 digest、固定 personas 与四类 domain cases；中位 usefulness 4/5，factuality `PASS`，ownership `PASS`，critical unsupported claims `0`。cross-model validation pending。

### 3.8 医疗器械临床 / 应用支持

- **英文 / proposed ID：** Clinical Application Specialist、IVD Application Specialist、Clinical Support Specialist；`medical_device_clinical_application_specialist_v1`（proposed，尚非 canonical source）。
- **范围：** 初中级的产品/应用培训、受限产品范围内的现场技术与工作流支持、用户反馈传递、内部/渠道赋能及学术活动支持。
- **真实 qualifying JD（8 条 / 8 家 employer）：**

| 公司 | 岗位名称 | 城市 | 来源类型 | qualifying | 主要职责信号 |
| --- | --- | --- | --- | --- | --- |
| Dabo Medical | Clinical Application Specialist | 北京 | employer-identified public posting | 是 | 术前/术中/术后设备支持、培训、反馈 |
| Kangli Bio Medical | Clinical Application Specialist | 南京 | employer-identified public posting | 是 | 产品培训、问题闭环、销售支持 |
| China National Medical Device (Wuxi) | Clinical Application Specialist | 南京 | verified employer posting | 是 | 设备应用、培训、技术问题、反馈 |
| Gaush Meditech | Clinical Application Specialist | 北京 | public listing | 是 | 医院产品说明、应用培训 |
| 成都佳宝医疗器械 | Clinical Application Specialist | 成都 | verified employer posting | 是 | 临床技术支持、产品培训、反馈 |
| 深圳鼎识生物 | Clinical Application Specialist / Sales | 深圳 | employer-identified public posting | 是 | 操作培训、客户沟通、售前/售后支持 |
| 湖南科度医疗 | Clinical Application Specialist | 长沙 | employer-identified public posting | 是 | 产品说明、操作培训、应用支持 |
| 木瓦医疗 | Clinical Application Specialist | 济南 | employer-identified public posting | 是 | 临床使用指导、前线问题响应 |

- **non-countable / pending：** Mindray 的历史镜像、Gaoshi Medical 与 Mindray 的 search extract、Eyebright Medical 的 partial official snapshot 均保留为研究上下文，但不计入覆盖数。
- **稳定职责：** 产品专属临床/应用培训、产品范围内的技术与工作流支持、用户反馈收集/传递、内部/渠道赋能和学术活动支持。
- **JD-dependent / senior：** 产品组合或区域所有权、销售 KPI/收入/市场覆盖、临床决策或患者照护、手术责任、产品路线图/研发、注册申报、专家网络和人员管理。
- **医学背景迁移：** 医学、检验、影像、护理或临床沟通可支持产品理解；不能替代设备实操、客户培训或现场技术支持。临床轮转与学术活动组织仅为部分映射。
- **关键边界：** application/training support ≠ clinical decision/procedure ownership；feedback ≠ product roadmap；application support ≠ sales KPI；coordination/support ≠ project ownership。
- **当前成熟度：** Canonical v1（domain validated）。`medical_device_clinical_application_specialist_v1` 已是 canonical source，并已有 generated Skill projection。它不因此自动成为 runtime target；Cross-model validation 仍为 pending，且不能以缺少该 hardening 证据否定 Canonical v1。

### 3.9 Pharmacovigilance / Drug Safety（PV，Candidate）

- **英文 / proposed ID：** Pharmacovigilance Associate、Drug Safety Specialist、Safety Operations、PV Physician；`pharmacovigilance_drug_safety_v1`（proposed，尚非 canonical source）。
- **范围：** 受监管安全信息接收/处理/跟进支持、安全文档/文献/reconciliation 支持、GVP/SOP 质量与检查准备支持，以及分配范围内的安全信息协调。
- **真实 qualifying JD（10 条 / 8 家 employer）：**

| 公司 | 岗位名称 | 城市 | 来源类型 | qualifying | 主要职责信号 |
| --- | --- | --- | --- | --- | --- |
| AbbVie China | China Regional PV Associate | 上海 | employer careers page | 是 | AE/ICSR、文献/QC/reconciliation、PSUR 支持 |
| IQVIA KunTuo | PV Physician；Safety Operations Intern | 北京/上海；大连 | employer careers page | 是 | 安全信息处理、AE 跟进、数据库/QC 支持 |
| Akeso Biopharma | Drug Safety Operations Specialist；Drug Safety Physician | 北京/广州 | university career board with employer link | 是 | 事件处理、aggregate-report 支持；医师级范围保留为 JD-dependent |
| MSD R&D (China) | Japanese/Korean Pharmacovigilance | 北京 | university career-board republication | 是 | 受监管 AE case-management（监督范围） |
| 江苏恒瑞医药 | PV Medical Review Specialist | 上海 | public recruitment platform | 是 | individual safety report、QC/供应商/检查支持 |
| Shanghai Biojie Pharmaceutical | Senior Pharmacovigilance Specialist | 上海 | public recruitment platform | 是 | 资深 signal/risk/报告范围，仅作 JD-dependent |
| Immunochina | Pharmacovigilance Specialist | 北京 | employer careers page | 是 | 安全报告、数据库、资料与一致性检查 |
| HaiboWei Pharmaceutical | Pharmacovigilance | 成都 | public recruitment platform | 是 | PV system、信号/报告等资深范围，仅作 JD-dependent |

- **稳定职责：** 受监管安全 case 支持、安全文档/文献/reconciliation、GVP/SOP 质量支持、指定范围内协调和直接分配时的报告支持。
- **JD-dependent / senior：** safety strategy、signal detection/benefit-risk、QPPV/PSMF、监管机关沟通、IND/NDA/RMP、团队管理和超出直接证据的医学判断。
- **医学背景迁移：** AE 记录/随访协助、受控安全资料和流程培训可支持受监督 PV 支持；医学文献与严谨记录可迁移但不替代 GVP/ICSR；临床轮转和病历记录仅提供部分临床语境。
- **关键边界：** AE documentation ≠ ICSR submission ownership；literature/safety support ≠ signal detection 或 benefit-risk ownership；filing/support ≠ QPPV / PSMF；研究协调 ≠ safety strategy 或最终监管责任。
- **当前成熟度：** Candidate；有 8 个 fixed personas、machine-readable negative rules 和 domain-evaluation asset，但尚无 canonical JSON 或 promotion PR。

## 4. Role Pack 如何毕业

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

## 5. 当前测试体系

| 测试层 | 核查内容 |
| --- | --- |
| Evidence / provenance | qualifying JD 和 employer count、digest 可复算、excluded/pending 证据不计数。 |
| Domain cases | positive、transferable、partial、gap/negative persona 在多个 JD/employer 中的映射。 |
| Factuality / ownership | 不得把 contributed 改为 led，support 改为 ownership，partial 改为 full，或新增数字、成果、监管/商业/管理责任。 |
| Role Pack invariants | Role Pack 只能改变 priority/emphasis；confirmed facts、evidence IDs、责任范围与依赖关系不得漂移。 |
| Generated artifacts | canonical JSON 通过 generator 生成 Skill references；`generate_skill_role_pack_reference.py --check` 发现 drift。 |
| Frozen release regression | 正常经历、信息不足、责任模糊、可能夸大与模型不可用降级等固定案例。 |
| Full pytest | 以当前 `pytest -q` 实际收集和通过结果为准，不把历史测试数量写成长期事实。 |

## 6. Domain validation 与 Cross-model validation

**Canonical v1（domain validated）** 验证职业语义是否稳定：真实 JD/company 覆盖、stable core、personas、证据/负向映射、usefulness、factuality、ownership、0 critical unsupported claims，以及回归测试和 human approval。

**Cross-model validated** 是 Canonical v1 之后的 hardening：需要真实 exact model/version/config、isolated runs、prompt/input/output 和 digest、跨模型 unsupported-claim rate 及 model-version regression。缺少模型配置不能被写成 domain validation 失败，也不能伪造为已通过。

## 7. 中国市场覆盖策略与下一阶段路线图

本仓库的覆盖目标不是为每个职位制造一个 Role Pack。当前的 `75–85%` 覆盖表述是产品规划 heuristic，不是市场份额、职位空缺量或录用概率。

### 近期

1. 在不放宽 evidence/ownership 标准的前提下，完成 PV 的 Candidate → Canonical v1 graduation audit 与独立 promotion PR。
2. 若 PV 尚未满足正式 promotion gate，应保持 Candidate，而不是以规划名称提前升级。
3. Device 的 Cross-model validation 保留为后续 hardening，不阻止其 Canonical v1 状态。

### 下一批 Deep / Candidate research

1. Medical Writing / Scientific Communications。
2. Regulatory Affairs；后续真实 JD 研究决定 Medical Device RA 与 Drug RA 是否需要拆分为两个 Candidate corpus，不能预设共用一个 Pack。
3. RWE / HEOR evaluation；两者应分别评估，不默认共用职业语义。

### 长期保持 JD-driven 的方向

Market Access、Healthcare Product、Healthcare Consulting、Commercial / Business Analytics、Healthcare / Project Operations 与 Medical Sales / Commercial 目前不应做 universal Role Pack：它们通常受公司类型、客户/支付方、产品/区域、商业目标和实际 ownership 强烈影响。产品应要求用户提供具体 JD，并明确缺少 pricing、payer、roadmap、client delivery、quota、territory、budget、vendor 或 people-management 的直接证据。

## 8. Source of truth 与文档治理

| 信息 | authoritative source |
| --- | --- |
| Role Pack 语义与当前 canonical 数量 | `data/role-packs/*.json` |
| Generated Skill rules | `skill-lite/medical-resume-skill/references/role-packs.md`、`role-pack-rules.json`（生成物，禁止手改） |
| Role Pack 毕业门槛 | `docs/ROLE_PACK_GRADUATION.md` |
| CRA/CDM/Device/PV 的 JD 与 domain evidence | `docs/research/role-validation/**` |
| 中国职业覆盖规划 | `docs/research/china-career-coverage-matrix-v1.md` |
| 岗位体系总览与路线图 | 本文档 |
| 文档分类规则 | `docs/DOCUMENTATION_SOURCES.md` |

当说明性文档与 machine-readable source 冲突时，以 machine-readable source 为准；历史文档只保留追溯价值，不能改变运行时或 canonical 语义。
