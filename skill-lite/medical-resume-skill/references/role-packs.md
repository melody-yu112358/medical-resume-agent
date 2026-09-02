<!-- GENERATED FILE — DO NOT EDIT MANUALLY.
Source: data/role-packs/*.json
Canonical packs: clinical_data_management_v1, clinical_operations_v1, clinical_research_associate_v1, clinical_research_v1, doctoral_v1, health_ai_data_v1, medical_affairs_v1, medical_device_clinical_application_specialist_v1, pharmacovigilance_drug_safety_v1
Schema: medical-role-pack-schema-v1 (https://example.invalid/schemas/role-pack.schema.json)
Schema SHA-256: 3f07f6ce53967928d271780ec6fdc8fb638ca94d98299d734051e5a261a632e7
Source digest SHA-256: f65a99bbba43645e0dc4d8b13875d520ba7b9f989da08b35f682ed70d48ebc11 -->

# Target paths

This reference is generated from the canonical Role Pack configuration. A target changes the ordering and emphasis of confirmed facts; it never adds facts or upgrades responsibility.

## 临床数据管理 / CDM 支持 (`clinical_data_management_v1`)

初级至中级临床数据管理、数据质量、查询跟进及受控数据文档支持岗位；只转换已确认的临床研究数据支持事实。

### Prioritize

- CRF 核对、缺失数据与查询跟进
- 受控数据文档、可追溯性与既定 GCP/SOP 流程支持
- 已确认范围内的数据问题协调与研究数据质量支持
- 数据审阅或对账支持，不主张最终交付所有权

### Role-pack boundary

数据清理、核对、CRF/EDC 支持或与 CRC/CRA 的问题沟通不等于数据库锁定、EDC 建库、最终数据交付、项目/客户/供应商所有权或团队管理；一般数据分析也不自动证明临床试验数据管理、GCP 或 EDC 经历。

### Execution guardrails

- Restricted wording: 负责、主导、管理、领导、独立完成、统筹、拥有.
- Forbidden claims: 数据库锁定所有权、最终数据交付所有权、独立 EDC 建库或配置权、CRF 设计所有权、CDM 项目负责人、客户、供应商或预算所有权、团队管理或人员分配、CDISC、SDTM、MedDRA 或编程专长、确保数据合规或最终质量.

## 临床运营协调 (`clinical_operations_v1`)

初级至中级的临床运营、试验协调、研究资料、数据质量与既定流程支持岗位；只转换已确认的具体执行经历。

### Prioritize

- 临床或研究流程中的资料完整性与文档维护
- 数据核对、查询跟进与质量支持
- 已确认的试验或研究团队协调支持
- 按既定方案、SOP 或流程进行的执行支持

### Role-pack boundary

协调、排期、文件维护或内部沟通不等于项目/流程所有权、运营管理、中心/供应商/患者/提供者管理、KPI 所有权或外部、客户及高管沟通；不得泛化为 healthcare/business operations 或管理层运营。

### Execution guardrails

- Restricted wording: 负责、主导、管理、领导、独立完成、统筹、拥有.
- Forbidden claims: 项目或项目群所有权、临床运营负责人、独立负责临床试验运营、流程或运营所有者、KPI 所有者、团队管理、管理研究中心、供应商、预算或合同管理、患者或提供者所有权、对外、客户或高管沟通、确保合规、独立制定或改造流程.

## 临床研究协调 / CRA 支持 (`clinical_research_associate_v1`)

初级至中级 CRA、临床研究协调和研究中心执行支持岗位；仅转换已确认的研究执行支持事实。

### Prioritize

- 研究资料与 CRF 维护
- 缺失数据和查询跟进
- GCP 下的既定研究流程支持
- 研究团队内部协调

### Role-pack boundary

资料准备、CRF维护、数据跟进或内部协调不等于独立中心监查、中心生命周期、受试者招募、预算、项目所有权、PI/赞助方或外部沟通所有权。

### Execution guardrails

- Restricted wording: 负责、主导、管理、领导、独立完成、统筹、拥有.
- Forbidden claims: 独立中心监查、研究中心生命周期所有权、受试者招募所有权、预算所有权、项目或项目群所有权、PI、赞助方或外部沟通所有权、团队管理、确保合规.

## 临床科研 (`clinical_research_v1`)

医院科研、临床研究支持和以临床问题为中心的研究申请。

### Prioritize

- 临床问题与研究设计
- 受试者或队列流程
- 数据质量与分析
- 已确认的伦理、GCP 与协作工作

### Role-pack boundary

不得把参与研究或数据任务写成临床试验运营、中心管理、合规保证或独立方案设计。

### Execution guardrails

- Restricted wording: 负责、主导、管理、领导、独立完成.
- Forbidden claims: 负责临床试验运营、确保合规、管理研究中心、独立设计研究方案、主导数据收集.

## 考博 / 保研 (`doctoral_v1`)

学术升学、保研、夏令营、博士申请与研究型项目申请。

### Prioritize

- 研究问题与设计
- 方法学严谨性
- 可确认的独立贡献
- 学术产出与研究潜力

### Role-pack boundary

不要用泛泛的“科研能力强”替代已确认的方法、责任和产出；未确认时不得写成课题负责人或研究领导者。

### Execution guardrails

- Restricted wording: 独立设计、创新开发、领导团队、管理项目.
- Forbidden claims: 独立设计课题、形成创新方法、主导发表、领导研究团队、管理研究中心.

## 医疗数据 / 健康科技 (`health_ai_data_v1`)

医疗数据、数字健康与健康科技相关的研究或早期岗位材料。

### Prioritize

- 数据来源与处理
- 分析方法与工具链
- 验证和结果沟通
- 医学问题与数据场景的关联

### Role-pack boundary

不得将分析或研究辅助工作描述为已上线临床产品、算法开发、AI 模型训练、产品设计或系统架构责任。

### Execution guardrails

- Restricted wording: 开发、训练、主导、负责、独立完成.
- Forbidden claims: 训练AI模型、开发算法、独立负责数据科学项目、主导产品设计、负责AI系统架构.

## MSL / 医学事务 (`medical_affairs_v1`)

医学事务、MSL 与医学信息相关的早期求职材料。

### Prioritize

- 疾病领域与证据解读
- 文献综合
- 科学沟通
- 医学信息转译与合规表达

### Role-pack boundary

没有明确事实时，不得声称 KOL 管理、外部拜访、医学策略制定、商业决策支持或独立负责医学信息。

### Execution guardrails

- Restricted wording: 管理、制定、主导、负责、领导.
- Forbidden claims: KOL管理、制定医学策略、支持商业决策、独立负责医学信息、主导医学沟通.

## 医疗器械临床 / 应用支持 (`medical_device_clinical_application_specialist_v1`)

初级至中级医疗器械临床/应用支持、产品培训、受限产品范围内的现场技术与工作流支持岗位；只转换已确认的应用支持事实。

### Prioritize

- 产品专属的使用培训、演示与技术问题跟进
- 已确认范围内的临床应用与工作流支持
- 用户反馈、案例资料和技术问题的受控记录与传递
- 内部、渠道或学术活动支持，不主张临床或商业所有权

### Role-pack boundary

设备培训、演示、现场技术支持或用户反馈不等于临床决策、手术/操作、患者照护、产品路线图、研发、客户/医院所有权、销售KPI、收入、区域策略或项目所有权。

### Execution guardrails

- Restricted wording: 负责、主导、管理、领导、独立完成、统筹、拥有.
- Forbidden claims: 临床决策或患者照护所有权、手术、操作或治疗责任、产品路线图或研发所有权、客户、医院、医生或渠道所有权、销售KPI、收入、配额、区域或商业策略所有权、项目所有权或项目负责人、器械注册申报或科学作者责任、人员管理或团队分配、确保临床结果、产品疗效或合规.

## 药物警戒 / 药物安全支持 (`pharmacovigilance_drug_safety_v1`)

初级至中级药物警戒、药物安全运营、受监管安全资料与质量支持岗位；只转换已确认的安全信息支持事实。

### Prioritize

- 受监管范围内的 AE 安全信息记录、资料核对与随访支持
- 受控安全文档、文献资料、对账与质量检查支持
- GVP/SOP 对齐的记录、归档与审计准备支持
- 已确认责任范围内的安全信息协调，不主张最终安全或法规所有权

### Role-pack boundary

AE 记录、资料整理、文献筛选、质量检查、归档、培训或协调支持不等于 ICSR 处理或提交所有权、信号检测、获益风险评估、PV 体系、PSMF/QPPV、法规代表、聚合报告主笔、项目所有权或团队管理。

### Execution guardrails

- Restricted wording: 负责、主导、管理、领导、独立完成、统筹、拥有.
- Forbidden claims: ICSR 处理、签发或提交所有权、信号检测、信号评估或获益风险所有权、DSUR、PSUR、PBRER、RMP 或安全报告主笔责任、PV 体系、PSMF、QPPV 或最终质量责任、监管机构代表、法规提交或安全策略所有权、临床安全医学判断或医疗决策责任、项目、客户、供应商、预算或团队管理所有权、确保药物安全、合规或最终监管结果.
