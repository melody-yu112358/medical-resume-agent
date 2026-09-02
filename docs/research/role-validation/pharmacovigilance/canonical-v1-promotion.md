# 药物警戒 / 药物安全支持 Canonical v1 promotion record

## Scope

本 promotion 新增 `pharmacovigilance_drug_safety_v1` 作为 canonical source。
它不改变 routing、runtime、workflow contract、UI、Claim Gate、Confirmation Gate、
graduation policy 或既有 Role Pack 的语义。

## Evidence and domain validation

- Candidate evidence 位于
  `docs/research/role-validation/pharmacovigilance/candidate-evidence-v1.json`。
- 覆盖为 10 条 qualifying 中国市场 JD、8 家 employer。每条可计数记录保留
  employer、岗位、地点、URL、保存的职责摘录和 SHA-256 digest；历史、partial 与
  search extract 记录不得计入。
- 固定 8 个 personas 覆盖 direct、transferable、partial 与 gap/negative 场景，且各
  persona 对应至少 3 条 JD。
- Stable core 限于受监管 AE/安全信息记录、资料核对与随访支持，安全文档、文献、
  对账和质量支持，GVP/SOP 对齐的归档及审计准备，以及已确认范围内的安全信息协调。
- JD-dependent / senior scope 不进入 Pack：ICSR 提交/签发、信号检测、获益风险、
  DSUR/PSUR/PBRER/RMP 主笔、法规机构沟通、PV-system、PSMF/QPPV、医学判断、
  客户/项目/预算和团队管理所有权。
- 静态 domain evaluation 覆盖 positive、transferable、partial、negative 四类 case；
  median usefulness 4/5、factuality `PASS`、ownership `PASS`、critical unsupported
  claims `0`。

## Guardrails

AE documentation 不等于 ICSR 处理或提交所有权；文献或安全资料支持不等于信号检测、
获益风险或聚合报告作者责任；归档、培训、质量支持不等于 PV-system、PSMF、QPPV 或
最终质量责任；研究协调不等于法规代表或安全策略。所有更强责任均需候选人直接证据。

## Verification and limitations

canonical JSON 按 role-pack schema 校验。Skill projections 仅由
`generate_skill_role_pack_reference.py` 从 canonical JSON 生成；positive、
transferable、partial 和 negative cases 均有 focused regression 覆盖。

Cross-model validation 为 `pending/not yet performed`。本文档不声称已有模型 ID、
provider configuration、conformance output 或跨模型结果；这不是 Canonical v1
domain-validation failure。

## Non-goals

本 promotion 不添加 runtime target、不自动 merge，也不修改其他 Role Pack。最终保留
和 merge 仍要求可追溯的人类 GitHub review/approval。
