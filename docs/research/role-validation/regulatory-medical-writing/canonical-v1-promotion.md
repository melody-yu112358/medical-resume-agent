# 法规医学写作 / Regulatory Medical Writing Canonical v1 promotion record

## Scope

本 promotion 新增 `regulatory_medical_writing_v1` 作为唯一 canonical source。
它不修改 Scientific / Medical Communications、既有 Role Pack 语义、runtime、routing、
workflow contract、UI、Claim Gate、Confirmation Gate 或 graduation policy。

## Evidence and domain validation

- Candidate evidence 位于
  `docs/research/role-validation/regulatory-medical-writing/candidate-evidence-v1.json`。
  覆盖 8 条 qualifying 中国市场 JD、8 家 employer；每条可计数记录保留 employer、岗位、
  地点、URL、保存的职责/资格摘录与可复算 SHA-256 digest。两条 historical records 明确不计入。
- 固定 8 个 personas 覆盖 direct、transferable、partial 与 negative/gap 情形；每个 persona
  对应至少 3 条、且来自不同 employer 的 qualifying JD。
- Stable core 限于 Protocol、CSR、IB、clinical summary 等受控临床/注册文件的已确认
  撰写或审阅支持，文献与临床数据综合，模板/SOP/GCP/ICH/质量支持，以及受限的跨职能
  review comment、版本与交付协调。
- 文档/项目写作策略、最终法规提交、客户所有权、监管机构沟通、复杂 CSR/Protocol 主笔、
  项目级策略、时间线谈判、mentoring 与管理均为 JD-dependent 或 direct-evidence-required，
  不进入 Pack 的稳定核心。
- 静态 domain evaluation 覆盖 positive、transferable、partial、negative 四类 case；
  median usefulness 为 4/5，factuality `PASS`，ownership `PASS`，critical unsupported
  claims 为 0。完整 evidence、review、evaluation 与 graduation audit 记录保存在同一
  regulatory-medical-writing 目录。

## Guardrails

academic writing 不等于 regulatory medical writing；literature synthesis 不等于
CSR/Protocol author ownership；drafting/review support 不等于 submission ownership；
document review 不等于 regulatory strategy；internal coordination 不等于
client/program ownership；translation/editing 不等于 authorship authority。

## Verification and limitations

canonical JSON 通过 role-pack schema 校验。Skill projections 只由
`generate_skill_role_pack_reference.py` 从 canonical JSON 生成。focused canonical
cases 和 existing-pack execution-projection invariant 均有回归覆盖。

Cross-model validation 是 `pending/not yet performed`。本 promotion 不声称已有模型
ID、provider configuration、conformance output 或跨模型结果；这不是 Canonical v1
domain-validation failure。

## Non-goals

本 promotion 不添加 runtime target、不自动 merge。最终保留和 merge 仍要求可追溯的人类
GitHub review/approval。
