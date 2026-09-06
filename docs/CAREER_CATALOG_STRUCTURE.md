# 医学背景职业目录：结构审查与覆盖清单

核对日期：2026-09-06。性质：REFERENCE / 目录整理建议，不是职业分类标准、市场调查、晋升记录或新的运行契约。本文不新增职业条目，不改变现有 Pack、Card、taxonomy、规则或 runtime target。对象类型及主归属是本次结构审查建议，尚未写入应用。

## 1. 一套知识，两条使用路径

- 简历路径：已选目标 → 关联 Pack → 在事实和边界约束下组织表达。Pack 可以服务升学或研究申请，不必等于一个职业。
- 探索/匹配路径：浏览职业 → 看具体职责和要求 → 对照已确认经历 → 查看直接/可迁移/部分/缺口/禁止推断。存在 Pack 不等于已有 Profile 解释规则。

建议的目录主结构为 **职能族 → 具体岗位角色**。机构、业务领域、产品阶段是可选关联；具体 JD 是角色在特定雇主、产品与责任范围下的实例，不是固定第三层分类。职业路径与升学申请路径分别浏览，继续共用已有证据表达能力。

这是一项整理方向，不以“医学生可直接进入”为收录条件；资格、职责层级和 JD 要求需独立核验。职业汇总广度与单角色知识深度分别建设，不用新名字的数量替代覆盖质量。

## 2. 当前资产盘点与计数口径

本次逐文件核对结果：

| 维度 | 当前数量 | 能说明什么 / 不能说明什么 |
| --- | --- | --- |
| 地图目录 | 16：10 个 Pack 关联目标 + 6 个 JD-driven 方向 | 不是 16 个同粒度职业；包含 1 个升学申请目标 |
| Canonical Pack | 10 | 有表达与边界规则，不等于均在产品入口开放 |
| 已导入 Career Card | 5 | 有结构化职业知识，不等于全部具备解释规则 |
| 有解释规则的方向 | 2，合计 11 条规则 | CDM 6 条、器械应用支持 5 条；不代表穷尽其岗位要求 |
| 现有简历 workflow target | 5 | 仅指 workflow-contract.json 中的显式目标，非新增授权 |
| 旧探索卡 | 5，review_status 均为 draft | 位于 data/careers，不是上述 5 张已导入 Card；不能加成 10 张成熟卡 |
| 当前 beta_directions | 0 | 研究文档中的 Beta 建议，不等于目录已登记或已验证 |
| 当前 Card 的人工逐 claim JD 支持注释 | 0 | Card 所引 JD 目前是背景研究，不能称为逐 claim 直接证据 |

计数来源：[地图 registry](../data/career-map/directions-v1.json)、[Canonical Pack](../data/role-packs/)、[Career Card](../data/career_cards/)、[规则 registry](../data/career-map/career-card-match-rules-v1.json)、[workflow targets](../skill-lite/medical-resume-skill/references/workflow-contract.json)、[旧探索卡](../data/careers/)。文件变化后应重新核对，不将本文计数当作真值。

## 3. 现有 16 个目录对象的结构审查

类型含义：**升学路径**不是职业；**宽方向**跨多个具体岗位；**角色簇**在同一工作领域内混合若干角色；**有界岗位范围**已有较明确的工作与责任边界，但不冒充标准职业编码或所有级别岗位。主职能仅作为未来浏览建议，保留现有多职能关联。

| 现有目录对象及稳定 key | 建议对象类型 | 当前职能关联 | 名称、相邻角色与后续整理 |
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

上表建议归并为：1 个申请目标、8 个宽方向、3 个角色簇、4 个有界岗位范围。后 15 个对象仍不是 15 个经过独立验证的具体职业；暂不能据此计算中国医学背景岗位总覆盖率。

## 4. Pack、Card、规则和产品入口分别核对

下表以现有 key 为关联依据；“有 Pack”仅表示 Canonical 源存在。“入口”仅指当前 workflow target 清单；“无规则”不代表职业不成熟或不能写简历。“JD 引用”是 Card 的 snapshot_ids 数量，不是已验证的独立雇主数量或逐 claim 支持数。

| Pack key | 已导入 Card 文件 | JD 引用数 | 解释规则数 | workflow 入口 |
| --- | --- | --- | --- | --- |
| `doctoral_v1` | — | — | 0 | 是 |
| `clinical_research_v1` | — | — | 0 | 是 |
| `medical_affairs_v1` | — | — | 0 | 是 |
| `health_ai_data_v1` | — | — | 0 | 是 |
| `clinical_operations_v1` | — | — | 0 | 是 |
| `clinical_research_associate_v1` | [clinical_research_associate.v1.json](../data/career_cards/clinical_research_associate.v1.json) | 8 | 0 | 否 |
| `clinical_data_management_v1` | [clinical_data_management.v1.json](../data/career_cards/clinical_data_management.v1.json) | 8 | 6 | 否 |
| `medical_device_clinical_application_specialist_v1` | [medical_device_clinical_application_specialist.v1.json](../data/career_cards/medical_device_clinical_application_specialist.v1.json) | 8 | 5 | 否 |
| `pharmacovigilance_drug_safety_v1` | [pharmacovigilance_drug_safety.v1.json](../data/career_cards/pharmacovigilance_drug_safety.v1.json) | 10 | 0 | 否 |
| `regulatory_medical_writing_v1` | [regulatory_medical_writing.v1.json](../data/career_cards/regulatory_medical_writing.v1.json) | 10 | 0 | 否 |

这五张 Card 各自的 `jd_evidence.source_file` 指向其现有 candidate-evidence 工件；旧文件名中的 Candidate 不推翻后来已完成的 Canonical promotion。每条 Pack 的精确 target_scope 与禁止推断以其 `skill_reference`、`forbidden_claims` 等字段为准，不从本表重新生成。

六个 JD-driven 对象目前均未绑定独立 Canonical Pack、未有上述已导入 Card、无解释规则、未列为独立 workflow target。它们在目录中的存在只代表探索模式，不代表已实现一个通用职业匹配接口。

## 5. 旧探索卡与别名：保留来源，不自动建立等价关系

以下别名来自现有 draft 卡，而非本次新确认的职业同义词。目录整理时要核对职责后再决定 alias、子角色或相邻角色关系，不能按名字相近复制成熟度。

| 旧探索卡 | 原文件中的名称/别名示例 | 可核对的现有范围 | 当前处理 |
| --- | --- | --- | --- |
| [clinical-research-associate.cn.json](../data/careers/clinical-research-associate.cn.json) | 临床监查员、临床研究监查员、Clinical Research Associate | CRA 支持 Pack | draft 保留；独立监查与已有支持边界不能等同 |
| [medical-science-liaison.cn.json](../data/careers/medical-science-liaison.cn.json) | 医学科学联络官、医学联络官、Medical Science Liaison | 医学事务角色簇 | draft 保留；MSL 不代表整个医学事务职能 |
| [pharmacovigilance-specialist.cn.json](../data/careers/pharmacovigilance-specialist.cn.json) | 药物警戒专员、药物安全运营专员、PV Specialist | PV 支持 Pack/Card | draft 保留；不能当成另一个已导入成熟 Card 重复计数 |
| [medical-writer.cn.json](../data/careers/medical-writer.cn.json) | 医学写作、医学撰写、医学编辑、Medical Writer | 文件自述聚焦临床开发/注册写作 | 先与法规医学写作核对；不能用其广名称证明科学传播方向已覆盖 |
| [healthcare-ai-product-manager.cn.json](../data/careers/healthcare-ai-product-manager.cn.json) | 医疗 AI 产品经理、健康 AI 产品经理 | 医疗产品 JD-driven 与健康科技宽方向 | draft 保留；不自动把两边 Pack/目录合并或新增通用产品经理 Pack |

## 6. 已在仓库规划、尚未形成独立目录对象的事项

下列来自已有 [覆盖矩阵](research/china-career-coverage-matrix-v1.md) 和 [版图路线图](CAREER_ROLE_PACK_LANDSCAPE.md)，不属于本次新增职业，也不计入当前 16 项。只指出资产缺口，不声称没有任何相关研究材料。

| 已有规划名称 | 当前应区分的范围 | 尚缺的独立结构/验证 |
| --- | --- | --- |
| Medical Writing / Scientific Communications | 区别于法规医学写作与健康科普 | 具体角色边界、独立目录身份与针对性 corpus；不能继承 RMW Canonical 状态 |
| 一般 Regulatory Affairs | 区别于写作；药物/器械差异待 JD 研究确认 | 不预设通用 RA Pack；需要独立 scope 与证据 |
| Biostatistics / SAS | 生物统计是职业方向，SAS 是技术线索，不是同级职业 | 统计职责与统计编程的边界审查；尚无独立目录/Pack/Card/解释规则 |
| RWE | 证据研究不等于市场准入策略 | 独立目录、职责证据、解释与负向案例；共享 taxonomy 标签不代表已落地角色 |
| HEOR | 与 RWE、定价/支付方职责分别核验 | 独立目录、经济模型等要求的适用性与证据；不继承其他角色成熟度 |

用户希望将职业覆盖扩展到 75–85%，这是未来扩展目标，不是已经实现的结果。应保留该目标，并在广度收集中明确覆盖范围与参照目录后计算进度，而不是因尚无分母继续推迟扩展。地区、人群、医学相关及通用转岗支线分别记录；JD 样本覆盖、目录覆盖与可解释覆盖不混算。具体采集步骤见 [广度优先计划](research/career-catalog-breadth-plan-v1.md)。

## 7. 下一步优先级与完成条件

| 优先级 | 工作 | 完成条件 | 本次是否实施 |
| --- | --- | --- | --- |
| 已完成 | 修正资产/规划文档漂移 | PV/RMW 当前状态一致；区分未来 75–85% 扩展目标与当前进度；申请路径不混入职业计数 | 本次文档修正 |
| P0 / 下一阶段第一项 | 扩目录广度：建立带来源的候选岗位清单 | 先广泛采集、去重与分组，记录未覆盖职能及转岗支线；候选条目不要求先建 Pack/Card/匹配规则；按明确参照集合跟踪 75–85% 目标 | 本次制定采集计划，尚未大批采集或注册新职业 |
| P1 / 服务于广度 | 处理阻碍收录的名称与范围歧义 | 对新收集岗位做最小职责/交付物核对；等价、子范围、相邻、待确认分别记录，不必先完成全部旧角色簇深审 | 仅提出；不改 Pack |
| P2 / 广度首轮后 | 梳理临床科研 / CRA 支持 / 临床运营协调等重点角色簇 | 依据现有与新增 JD 决定是否拆分；同时整理医学事务和健康科技的宽范围 | 仅提出 |
| P2 / 广度首轮后 | 补已有 Card 的解释深度 | CRA、PV、RMW 中选一个补 claim 规则、人工来源支持和 synthetic 正/部分/负例；不占用首轮广度工作的优先级 | 仅提出 |

优先级按用户“已有深度、先补广度”的目标调整，不是市场需求、录用概率或用户适配排序。旧资产维护仅处理事实或边界错误，不把完整深审作为候选目录扩充的前置条件。当前两种 Profile 解释方向继续保持原边界。

## 8. 维护与验证

任何新增目录/Pack/Card/规则后，分别核对第 2、3、4 节；这些状态是相互独立的轴，不是单一“成熟度等级”。已有 11 个职能标签可以继续承载导航，不另建一套平行分类表。

最小验证项：地图 key 与本表逐一对应；Card 的 role_pack 引用存在；规则的 role_pack/career_card_id 对齐；workflow 目标单独列示；引用文件存在；draft/规划对象不误计为已导入对象。本文是审查清单，不由导入器消费，不影响 SQL 快照或解释器指纹。
