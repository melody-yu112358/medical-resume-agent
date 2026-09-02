# 医疗器械临床 / 应用支持 Canonical v1 promotion record

## Scope

本 promotion 新增 `medical_device_clinical_application_specialist_v1` 作为
canonical source。它不改变 routing、runtime、workflow contract、UI、Claim
Gate、Confirmation Gate、graduation policy 或既有 Role Pack 的语义。

## Evidence and domain validation

- Candidate evidence 位于
  `docs/research/role-validation/device-clinical-application/candidate-evidence-v1.json`。
- 覆盖为 8 条 qualifying 中国市场 JD、8 家 employer。每条可计数记录保留
  employer、岗位、地点、URL、保存的职责摘录和 digest；historical、partial 与
  search extract 记录明确不计数。
- 固定 personas 覆盖 direct、transferable、partial 和 gap/negative 场景，并在多
  个 JD/employer 中演练。
- Stable core 限于产品专属临床/应用培训、受限产品范围内的技术/工作流支持、用户
  反馈收集/传递、内部或渠道赋能与学术活动支持。
- JD-dependent / senior scope 不进入 Pack：产品组合/区域、销售 KPI/收入、临床
  决策、患者照护、手术责任、产品路线图/研发、注册申报、专家网络和人员管理。
- Domain evaluation 记录中位 usefulness 4/5、factuality `PASS`、ownership
  `PASS`、critical unsupported claims `0`。

## Guardrails

应用或培训支持不等于临床决策、手术/操作或患者照护。用户反馈和技术问题处理不等于
产品路线图、研发、客户/医院所有权。销售、渠道或学术活动支持不等于收入、KPI、区域
策略或商业所有权；协调和支持不等于项目所有权。

## Verification and limitations

canonical JSON 按 role-pack schema 校验。Skill projections 仅由
`generate_skill_role_pack_reference.py` 从 canonical JSON 生成；positive、
transferable、partial 和 negative cases 均有 focused regression 覆盖。

Cross-model validation 是 `pending/not yet performed`。本文档不声称已有模型 ID、
provider configuration、conformance output 或跨模型结果；这不是 Canonical v1
domain-validation failure。

## Non-goals

本 promotion 不添加 runtime target，不自动 merge，也不修改其他 Role Pack。最终
保留和 merge 仍要求可追溯的人类 GitHub review/approval。
