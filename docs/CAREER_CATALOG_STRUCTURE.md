# 医学背景职业目录：结构审查与覆盖清单

核对日期：2026-09-06。性质：REFERENCE / 目录整理建议，不是职业分类标准、市场调查、晋升记录或新的运行契约。本文不新增职业条目，不改变现有 Pack、Card、taxonomy、规则或 runtime target。对象类型及主归属是本次结构审查建议，尚未写入应用。

## 1. 一套知识，两条使用路径

- 简历路径：已选目标 → 关联 Pack → 在事实和边界约束下组织表达。Pack 可以服务升学或研究申请，不必等于一个职业。
- 探索/匹配路径：浏览职业 → 看具体职责和要求 → 对照已确认经历 → 查看直接/可迁移/部分/缺口/禁止推断。存在 Pack 不等于已有 Profile 解释规则。

建议的目录主结构为 **职能族 → 具体岗位角色**。机构、业务领域、产品阶段是可选关联；具体 JD 是角色在特定雇主、产品与责任范围下的实例，不是固定第三层分类。职业路径与升学申请路径分别浏览，继续共用已有证据表达能力。

这是一项整理方向，不以“医学生可直接进入”为收录条件；资格、职责层级和 JD 要求需独立核验。职业汇总广度与单角色知识深度分别建设，不用新名字的数量替代覆盖质量。

## 2. 当前状态从哪里读取

[当前资产状态](CAREER_CATALOG_STATUS.md) 是唯一生成的当前库存与关联清单；最终真值为其列明的机器文件。本文只维护对象类型、名称歧义和分类建议，不复制 Pack、Card、规则、入口或 JD 引用数量。

## 3. 目录对象的结构审查示例（2026-09-06）

类型含义：**升学路径**不是职业；**宽方向**跨多个具体岗位；**角色簇**在同一工作领域内混合若干角色；**有界岗位范围**已有较明确的工作与责任边界，但不冒充标准职业编码或所有级别岗位。主职能仅作为未来浏览建议，保留现有多职能关联。

| 现有目录对象及稳定 key | 建议对象类型 | 审查时职能关联 | 名称、相邻角色与后续整理 |
| --- | --- | --- | --- |
| 考博 / 保研 `doctoral_v1` | 升学路径 | Research | 移至独立申请路径展示；不删除或改名 Pack，不计入就业岗位覆盖率 |
| 临床科研 `clinical_research_v1` | 宽方向 | Research；Clinical Development / Operations | 含医院科研、研究支持和研究申请；先区分工作目标与申请目标，不与 CRA 等同 |
| MSL / 医学事务 `medical_affairs_v1` | 角色簇 | Medical Affairs | MSL 是其中的具体方向，不能将所有医学事务/医学信息岗位视为 MSL 别名 |
| 医疗数据 / 健康科技 `health_ai_data_v1` | 宽方向 | Data / Statistics；Product / Technology | 不直接等同数据分析、生物统计、算法或 AI 产品经理；先识别职责与交付物差异 |
| 临床运营协调 `clinical_operations_v1` | 角色簇 | Clinical Development / Operations | 执行、资料、跟进和协调支持；与研究中心执行、独立监查及项目所有权区分 |
| 临床研究协调 / CRA 支持 `clinical_research_associate_v1` | 角色簇 | Clinical Development / Operations | CRA 是源标签中的名称，不自动把 CRC、CRA 和研究中心支持合并为同义词；先梳理监查/协调边界 |
| 临床数据管理 / CDM 支持 `clinical_data_management_v1` | 有界岗位范围 | Data / Statistics | CDM 为源中缩写；与普通数据分析、统计编程及数据库锁定所有权区分 |
| 医疗器械临床 / 应用支持 `medical_device_clinical_application_specialist_v1` | 有界岗位范围 | Device Clinical / Application | 与器械销售、注册和临床决策区分；“支持”不等于全部独立应用职责 |
| 药物警戒 / 药物安全支持 `pharmacovigilance_drug_safety_v1` | 有界岗位范围 | Safety | 保留个例/安全信息支持边界；不自动覆盖签署、信号负责人或 QPPV 责任 |
| 法规医学写作支持 `regulatory_medical_writing_v1` | 有界岗位范围 | Regulatory；Medical Writing / Scientific Communications | 建议写作作为主浏览归属、Regulatory 作为交叉关联；不与一般注册事务、科学传播或科普写作合并 |
| 市场准入 `market_access_jd_driven` | 宽方向 | RWE / HEOR / Access | 以具体支付方、产品和职责核验；不把 RWE、HEOR 与市场准入当同一职业 |
| 医疗产品 `healthcare_product_jd_driven` | 宽方向 | Product / Technology | 医疗 AI 产品是可能的细分场景；不能从临床理解推出 roadmap 或商业所有权 |
| 医疗咨询 `healthcare_consulting_jd_driven` | 宽方向 | Commercial | 当前归属较粗，需据实际项目/交付物审查；研究分析不自动成为 client delivery |
| 商业 / 业务分析 `commercial_business_analytics_jd_driven` | 宽方向 | Commercial；Data / Statistics | 与临床数据、一般科研分析分开；商业名称相近不证明职责一致 |
| 医疗 / 项目运营 `healthcare_project_operations_jd_driven` | 宽方向 | Clinical Development / Operations | 与临床运营协调容易混淆；需要组织、产品和具体运营对象才能确定归属 |
| 医学销售 / 商业 `medical_sales_commercial_jd_driven` | 宽方向 | Commercial | 商业比销售更宽；产品培训/医学交流不能自动变为销售 quota 或区域所有权 |

上表是有日期的分类审查样本，不是自动随目录扩展的库存；申请目标、宽方向、角色簇与有界岗位范围不能混算为同粒度职业。完整当前集合只见状态页。

## 4. Pack、Card、规则和产品入口分别核对

这些资产是独立轴，不是单一成熟度等级。Pack 提供表达与边界；Card 承载结构化知识；规则决定哪些 claim 可解释；workflow contract 决定显式入口。逐项关联只在 [当前资产状态](CAREER_CATALOG_STATUS.md) 生成展示。

Card 的 JD 引用数不等于独立雇主数或逐 claim 支持数。历史文件名中的 Candidate 不决定当前 Canonical 状态；精确 target_scope 和禁止推断以 Pack 源为准。JD-driven 目录存在不代表已有通用职业匹配接口。

## 5. 旧探索卡与别名：保留来源，不自动建立等价关系

以下是审查时旧探索卡的别名样本，而非本次新确认的职业同义词。目录整理时要核对职责后再决定 alias、子角色或相邻角色关系，不能按名字相近复制成熟度。

| 旧探索卡 | 原文件中的名称/别名示例 | 可核对的现有范围 | 审查建议 |
| --- | --- | --- | --- |
| [clinical-research-associate.cn.json](../data/careers/clinical-research-associate.cn.json) | 临床监查员、临床研究监查员、Clinical Research Associate | CRA 支持 Pack | 保留来源；独立监查与已有支持边界不能等同 |
| [medical-science-liaison.cn.json](../data/careers/medical-science-liaison.cn.json) | 医学科学联络官、医学联络官、Medical Science Liaison | 医学事务角色簇 | 保留来源；MSL 不代表整个医学事务职能 |
| [pharmacovigilance-specialist.cn.json](../data/careers/pharmacovigilance-specialist.cn.json) | 药物警戒专员、药物安全运营专员、PV Specialist | PV 支持 Pack/Card | 保留来源；不能当成另一个已导入成熟 Card 重复计数 |
| [medical-writer.cn.json](../data/careers/medical-writer.cn.json) | 医学写作、医学撰写、医学编辑、Medical Writer | 文件自述聚焦临床开发/注册写作 | 先与法规医学写作核对；不能用其广名称证明科学传播方向已覆盖 |
| [healthcare-ai-product-manager.cn.json](../data/careers/healthcare-ai-product-manager.cn.json) | 医疗 AI 产品经理、健康 AI 产品经理 | 医疗产品 JD-driven 与健康科技宽方向 | 保留来源；不自动把两边 Pack/目录合并或新增通用产品经理 Pack |

## 6. 待审范围的分类示例

下列来自已有 [覆盖矩阵](research/china-career-coverage-matrix-v1.md) 和 [岗位边界总览](CAREER_ROLE_PACK_LANDSCAPE.md)，仅说明容易混淆的研究范围，不作为当前落地状态或内部任务队列。

| 已有规划名称 | 当前应区分的范围 | 独立收录前应核验 |
| --- | --- | --- |
| Medical Writing / Scientific Communications | 区别于法规医学写作与健康科普 | 具体角色边界、独立目录身份与针对性 corpus；不能继承 RMW Canonical 状态 |
| 一般 Regulatory Affairs | 区别于写作；药物/器械差异待 JD 研究确认 | 不预设通用 RA Pack；需要独立 scope 与证据 |
| Biostatistics / SAS | 生物统计是职业方向，SAS 是技术线索，不是同级职业 | 统计职责与统计编程的边界审查；不能仅凭技术名认定独立职业 |
| RWE | 证据研究不等于市场准入策略 | 独立目录、职责证据、解释与负向案例；共享 taxonomy 标签不代表已落地角色 |
| HEOR | 与 RWE、定价/支付方职责分别核验 | 独立目录、经济模型等要求的适用性与证据；不继承其他角色成熟度 |

覆盖目标、分母和 breadth / depth 口径只在 [广度扩展方法](research/career-catalog-breadth-plan-v1.md) 维护。

## 7. 广度与深度如何衔接

来源采集 → 最小职责去重 → 候选范围审查 → 浅层收录。完整 Pack、Card 或匹配规则不是候选收录的前置条件。后续深化依据来源质量、用户需求、职责稳定性与边界风险选择，不由标题热度或候选数量自动决定。具体排期在 PR 或任务记录维护。

## 8. 维护与验证

新增资产后重新生成并校验状态页；本文仅在分类原则或范围判断变化时更新。现有职能标签继续承载导航，不另建一套平行运行分类表。

最小验证项：状态页与源文件集合一致；Card 的 role_pack 引用存在；规则的 role_pack/career_card_id 对齐；workflow 目标单独列示；引用文件存在；draft/规划对象不误计为已导入对象。本文是审查清单，不由导入器消费，不影响 SQL 快照或解释器指纹。
