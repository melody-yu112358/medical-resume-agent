# MVP 发布冻结案例


## 评价入口与适用范围

这里统一提供评价阅读入口；下文保留各条路径自己的规则、人工门槛和案例，不把一种方法移植成另一种服务的验收。机器测试结果与真实模型运行、人工验收分别留证，不能互相冒充。

| 路径 | 适用方法 | 边界 |
| --- | --- | --- |
| 当前简历工作流 | 本页冻结回归与 [用户流程清单](#current-resume-user-flow) | 事实确认、责任、隔离、审计和交付；产品行为见 [产品说明](RESUME_AGENT_PRODUCT.md) |
| 当前 Career Card 解释服务 | [解释契约](CAREER_EXPLANATION_CONTRACT.md)及其测试 | synthetic-only、逐 claim、三个语义维度和非互斥展示；无百分比或排序 |
| Legacy career comparator / exploration | [合成档案方法](#legacy-synthetic-profile-evaluation)、[首阶段验收](#legacy-first-milestone-acceptance) | 保留原有假设上限、硬约束与人工测试门槛；不适用于新的无分数解释服务 |
| 真实对话模型 | [模型评价 harness](conversation_model_eval.md) | 离线测试不等于真实模型评价；没有模型配置时仍按 harness 记录 SKIPPED |
| Role Pack 领域与模型验证 | [晋升规则](ROLE_PACK_GRADUATION.md)及 [历史证据](archive/README.md) | 原有审批、domain / cross-model 门槛不变 |

当前解释服务的 all-of / any-of、partial、JD-dependent、未知 capability 拒绝、来源粒度和 snapshot replay 以解释契约及对应回归测试为准。Legacy 的“最多三个假设”、排序或百分比不能用于验收该解释服务；unsupported 也不是职业适配否定。这里不新增评价枚举或阈值。

## 用途

这是一组小而固定的回归案例。它不替代完整测试，也不评估模型的文采；它只检查最容易伤害用户信任的边界：事实是否被补写、责任是否被升级、未知是否被隐藏，以及模型不可用时系统是否诚实降级。

在修改提示词、模型、Schema、Role Pack、交付模板或核心工作流后，先运行这组案例；准备发布时，再运行完整测试。

```powershell
python scripts/run_release_regression.py
python -m pytest -q
```

只想确认本次会跑哪些测试时：

```powershell
python scripts/run_release_regression.py --dry-run
```

## 五个冻结案例

| ID | 场景 | 要守住的边界 | 主要依据 |
| --- | --- | --- | --- |
| RR-01 | 正常、可确认的科研经历 | 已确认事实可以走完整链路；不同岗位可改变表达重点，但不增加未知事实。 | `meta-analysis-end-to-end-example.json` |
| RR-02 | 信息不足的经历 | 缺失信息必须保留为未知或待确认，不能补成方法、成果或责任。 | `information-insufficient-end-to-end-example.json` |
| RR-03 | 责任边界模糊的经历 | “负责”“参与”等模糊说法不能自动升级为独立或项目级所有权。 | `responsibility-ambiguous-end-to-end-example.json` |
| RR-04 | 可能夸大的输入 | 主导、论文、影响因子和成果等未核实说法不能直接进入可投递表述。 | `user-exaggeration-end-to-end-example.json` |
| RR-05 | 模型不可用时的降级 | 不能编造替代答案；应保留已有证据，并清楚告诉用户模型改写当前不可用。 | `test_resume_rewriter.py`、`test_api.py` |

完整机器可读清单在 `data/evaluations/release-regression-manifest-v1.json`。

## 每次变更要留下什么

每次发布或重要改动，在 PR、发布记录或团队日志中写下：

- 当前 Git commit；
- 模型名称与配置；
- 提示词或 Skill 包版本；
- Role Pack / Schema / 模板的变更；
- 冻结案例与完整测试的结果；
- 是否存在已知限制，及负责人。

如果涉及真实模型运行，还应另存一份不含真实用户材料的评测记录：模型、模型版本、提示词、包摘要、合成输入、输出、人工结论与日期。不要将 API Key、真实简历或敏感材料写入仓库或日志。

## 通过与失败

通过不等于“输出最好看”，而是五个案例都守住了各自的边界。任何一项失败，都先判断是代码、规则、提示词、模型还是样例预期发生了变化；不要为了让测试变绿而放宽事实确认或 Claim Gate。

## Current resume user flow

以下逐项承接原用户验收清单，包含原发布前人工安全核对；没有删减或降低条件。

1. 用户逐题填写并显式确认姓名、主要教育背景及可选的奖项、语言、证书和研究兴趣；未确认资料不得进入交付文件；
2. 用户选择经历章节并填写真实的经历名称、机构、角色、时间与一段不完整的原始描述；
3. 系统原样保留用户输入，并将每段经历绑定到独立的 evidence 集合；
4. 后端提取候选行动、方法、工具、技术、协作与产出，但不自动提升责任；
5. 页面每轮只突出一个后端问题，支持单选或多选、自由补充和“不确定 / 不记得”；
6. 配置模型时，每个 intake turn 最多调用模型一次；模型只能选择白名单 fact/evidence/option ID，用户可见摘要由后端模板生成；
7. 用户逐项核对活动、执行方式、覆盖范围和个人边界，确认、修改或拒绝后才生成岗位无关的 Canonical Experience；
8. 用户可新增和切换多段经历；每段经历的证据、Canonical Experience 和后续 claim 必须保持隔离；
9. 用户选择目标方向后，系统只生成一段代表样板；未经显式批准不得组合完整简历；
10. 批准样板后，系统为所有已确认经历生成通过各自 Claim Gate 的要点，不得借用当前 active 经历的事实；
11. 用户可比较稳妥版、专业版和高竞争力版；切换版本只改变表达，不确认新事实；
12. 用户可展开查看证据和审计风险，编辑或改写后必须重新通过 Claim Gate；
13. 只有 Profile 已确认、代表样板已批准且至少一条 claim 为 ready 时，才能进入交付并下载完整文件包；
14. 刷新页面后本机会话、Profile、多经历与确认状态能够恢复；开始新简历会删除当前会话和 claim ledger；
15. DeepSeek 不可用、超时或输出未通过结构校验时，原始回答仍被保留，系统安全降级且不展示模型自由 prose。

### 每次发布前的人工安全核对

- 在未显式确认事实卡的会话中尝试生成或导出：必须被阻止，且不得出现可投递简历内容；
- 修改任一已审计要点后尝试交付或导出：必须先回到 factual audit，并重新通过 Claim Gate；
- 建立两段经历并分别确认后，核对每段生成的 claim 只引用其自身的 evidence，且切换 active experience 不改变另一段的事实、责任或证据。

## Legacy synthetic profile evaluation

这部分保留 legacy 路径原有评价条件，不代表对应人工验证已经完成，也不授权采集真实用户资料。

<details>
<summary>展开完整原方法与门槛</summary>

### Purpose

Synthetic profiles let the team test recommendation behavior before collecting
real participant data. They are deliberately fictional and may be committed to
Git. They do not describe a real student, a typical student, or a successful
transition story.

The first evaluation set contains three contrasting cases:

1. a clinical communicator with evidence-translation experience;
2. a research builder with small user-research and prototyping experience;
3. a safety coordinator with documentation and process evidence.

The variation is designed to test evidence handling and constraints, not to
create personality types.

### How to interpret expected hypotheses

The records in `data/evaluations/synthetic-profile-cases.cn.json` are evaluation
boundaries, not answer keys. A listed career is a reasonable hypothesis to
explore if the system cites the specified personal evidence, shows the stated
counter-evidence and unknowns, and proposes a low-cost test.

The system is not required to give every listed hypothesis or preserve their
file order. It must return no more than three. A different hypothesis is
acceptable only when its personal evidence and market claims are traceable and
its conflicts are visible.

The evaluation must never treat a hypothesis as:

- a claim that the person is naturally suited to the career;
- a prediction of employment, salary, or success;
- permission to ignore a location, travel, time, or other hard constraint;
- evidence for a capability that the profile does not contain.

### Review procedure

For each case:

1. load the synthetic profile and verified career cards;
2. apply hard constraints before comparison;
3. produce at most three career hypotheses;
4. map every supporting statement to an `evidence_id`;
5. include counter-evidence and unresolved questions;
6. use career-card sources for market claims;
7. propose one feasible action that creates new evidence;
8. check the case's `forbidden_conclusions`.

The first three failure classes to track are:

- **invented support**: the output claims a capability not present in the
  profile;
- **hidden conflict**: a hard constraint or material gap is omitted;
- **verdict language**: a revisable hypothesis is presented as a fixed fit or
  destiny.

### Privacy boundary

Only synthetic cases belong in this directory. Real resumes, names, contact
details, interview transcripts, and identifiable health information must stay
outside Git. Consenting-user tests should use an approved storage process and
feed only anonymized aggregate findings back into the repository.

</details>

## Legacy first-milestone acceptance

这部分保留 legacy 路径原有评价条件，不代表对应人工验证已经完成，也不授权采集真实用户资料。

<details>
<summary>展开完整原方法与门槛</summary>

### Correctness

- All career facts shown to a user map to a stored source record.
- All personal evidence in a recommendation maps to the user's supplied data.
- Each capability claim identifies the experience that supports it and whether
  the claim is user-provided, inferred, or still unverified.
- Hard constraints exclude incompatible paths before ranking.
- Unknown, conflicting, and stale information is labelled.
- Each hypothesis includes at least one counter-evidence or unresolved item
  when one exists; the system does not hide it to improve apparent fit.
- The output makes no employment, salary, or guaranteed-fit promise.
- Resume output and interview feedback do not invent experience, credentials,
  numbers, job facts, or hiring predictions.

### Usability

- A user can complete intake without answering more than one question at once.
- A user can save a possibility glimpse and leave before completing the full
  exploration flow.
- The result contains no more than three career hypotheses.
- Each hypothesis includes support, counter-evidence, gaps, and a concrete next step.
- A user can identify which of their experiences led to each hypothesis.
- A user can correct the profile and reject, pause, or select a hypothesis.
- A selected direction leads to sourced real-job postings before resume work.
- Selecting a `job_id` starts resume diagnosis without requiring the user to
  paste the JD again.
- The experience does not frame staying in medicine, pausing exploration, or
  declining application preparation as failure.

### Application-preparation loop

- Every job shows company, location, status, source, and last verification date.
- Resume diagnosis separates original evidence, gaps, follow-up questions, and
  generated wording.
- Resume revisions show the original text, revised text, and reason for change.
- HR questions are grounded in the selected JD and confirmed resume evidence.
- Interview feedback points to the user's answer and the relevant job
  requirement without estimating hiring probability.
- The user can change direction or job and can remove transient personal data.

### Initial evaluation gate

Test with at least three consenting users using data kept outside Git. The first
milestone passes when:

- at least two users identify one hypothesis worth testing and can explain the
  evidence and uncertainty behind it;
- at least one user selects a sourced job, completes a grounded resume revision,
  and finishes one HR screening simulation;
- the participant can explain which JD requirements and personal evidence
  produced the resume and interview feedback;
- participants can correct or reject a system inference without losing their
  original evidence.

Visual polish and additional career coverage are optional after correctness and
usability pass.

</details>

原方法版本见 [acceptance 原件](archive/evaluation/ACCEPTANCE.md)、[synthetic evaluation 原件](archive/evaluation/SYNTHETIC_EVALUATION.md)、[用户流程清单原件](archive/evaluation/user_flow_acceptance_checklist.md)。历史原件不再单独维护，后续有效修订在本页进行，并遵循原有审查规则。
