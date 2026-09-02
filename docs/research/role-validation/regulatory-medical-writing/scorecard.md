# 中国 Regulatory Medical Writing Candidate scorecard

**Current tier:** Candidate — domain graduation audit complete.
**Release Gate:** `PASS — eligible for canonicalization review`; no Canonical v1
promotion, merge, runtime target, or human approval is implied by this record.

## 可计数中国 JD 覆盖

- **Qualifying JDs:** 8 / 8
- **Qualifying employers:** 8 / 5
- **证据口径：**只计入保存了 employer、title、city、URL、职责/资格摘录与可复算
  SHA-256 digest 的 current/recent 公共岗位。两条 historical public JD 只用于职业语义
  背景，不进入 coverage。
- **层级/公司混合：**包含 entry/assistant、specialist、3-5 年 writer，以及
  senior/manager 岗位；后者只用于划定 senior scope，不进入初中级 stable core。

## 稳定职业核心

跨药企、CRO、AI 药物研发与生物技术雇主，稳定出现的是：受控 protocol、CSR、clinical
summary 等临床文件的撰写/审阅支持；基于文献和临床数据的资料综合；template、style、
SOP、ICH/GCP 与质量支持；以及跨职能 review comment、版本和交付协调。

## 必须保留的边界

文献综述、学术论文、翻译或草稿支持不等于 regulatory author ownership；文件审核不等于
submission/strategy ownership；内部协调不等于 client、vendor、budget 或项目所有权。独立
protocol/CSR lead、CTD/IND/NDA 递交、法规沟通、program strategy、mentoring 和管理均为
JD-dependent 或 direct-evidence-required。

## Candidate assets

- 8 个固定 personas，包含 direct、transferable、partial 和 negative/gap 场景；每个
  persona 映射到至少 3 条 qualifying JD。
- 包含 direct/transferable/partial/gap mappings、4 条 machine-readable negative rules，
  以及 positive/transferable/partial/gap eval cases。
- 尚未进行模型 conformance 或 Canonical v1 promotion；这些不是 Beta → Candidate 的替代物。

## Domain review and evaluation

- 独立只读 Reviewer 已 `APPROVE`：stable core 未混入 senior writer、submission、
  client/program 或法规策略所有权；每个 persona 的演练覆盖至少三家雇主。
- 4 个固定 direct/transferable/partial/gap cases 的中位 usefulness 为 **4/5**；
  factuality 和 ownership 均为 `PASS`，critical unsupported claims 为 **0**。
- `docs/research/role-validation/regulatory-medical-writing/domain-review-v1.md`、
  `domain-evaluation-v1.json` 和 graduation audit 是本次可复核记录。

## 下一步

`eligible_for_canonicalization`，`human_required=true`：等待人类批准是否开始一个
**单独的** Canonical v1 promotion PR。Scientific / Medical Communications 仍是独立
Beta/scoping，不与本 corpus 合并；Cross-model validation 也仍为 pending，且不阻塞
本次 domain graduation 结论。
