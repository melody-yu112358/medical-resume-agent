> **历史原件 / archived 2026-09-06。** 原路径：`docs/CAREER_MAP_TAXONOMY.md`；归档前最后提交日期：2026-09-06。原文版本：[Git 85701b51](https://github.com/melody-yu112358/medical-resume-agent/blob/85701b516f5889412e9791391c4dedcb2d7b0b38/docs/CAREER_MAP_TAXONOMY.md)。当前承接入口：[有效说明](../../CAREER_MAP_DATABASE.md#taxonomy-and-filtering)。原有日期、数量、计划、验证与结论保留当时语境，不代表当前库存或本次重新验收；归档不改变 legacy 规则。

# 职业地图：交叉维度与适用性

职能族回答“做什么”，作为浏览主轴；产业生态回答“通常在哪里”，允许多选；生命周期回答“关联产品或证据的哪个阶段”，可不适用或尚待确认。三个维度不是上下级层级，也不是必填的三层职业分类。生命周期不是个人的初级/高级职业成长阶段。

## 真值与投影

`data/career-map/directions-v1.json` 仍是地图关联及适用性的人工维护源。Canonical Role Pack、Career Card、解释规则不随筛选逻辑改变。此修订保留原有的所有职业标签，不新增高校与上市阶段的推断关联。

每个 canonical assignment / JD-driven / beta direction 可带 `lifecycle_applicability`：

- `mapped`：至少一个阶段已标注，不表示标注穷尽所有适用阶段。
- `pending`：没有阶段标注，适用性待确认。
- `not_applicable`：没有阶段标注，且必须有 `lifecycle_review`，包含非空 `reviewed_by`、ISO 日期/时间 `reviewed_at`、`reason`。只在人工确认后使用。

本次现有空阶段统一保守标为 pending，有阶段标为 mapped；没有声称任何方向已完成“不适用”审核。旧 registry 未带字段时仍兼容：有阶段按 mapped、无阶段按 pending；绝不自动升级为 not_applicable。

SQL 的六张关联表继续投影阶段/生态/职能标签，不增加“待确认”或“不适用”伪阶段。适用性元数据由现有 `source_artifacts.raw_content` 保存，current manifest 的 `taxonomy_revision` 指向准确版本。网页只读取该已导入 artifact，不能越过导入器读取磁盘上更新的 taxonomy 文件。这一规模无需添加一套重复的元数据表；后续 SQL 场景需要适用状态索引时再做独立关系投影。

导入时校验状态、阶段有无及不适用审核记录；失败不激活新快照。修改/移除元数据、替换阶段标签，仍走完整源集合导入；同一源文件下 fresh 与 incremental 的当前状态一致，旧 registry 及 manifest 保留。

## 筛选契约

- 同维度多选为 OR；跨维度为 AND；不选即不限。
- 选项旁数量先忽略本维度选择，再应用其他维度条件，统计带该标签的方向数。多选数量可能重叠，不能直接相加；不是 JD 数量。
- 勾选或取消后立即发起 GET 查询，显示更新中状态，数量与结果随页面一起刷新；脚本不可用时回退为“应用筛选”按钮。0 项仍可选择和撤销，系统不悄悄修改用户筛选。
- 生命周期状态数量应用职能与生态条件、忽略阶段条件。选定阶段会排除 pending/not_applicable，并明确提示。
- 空结果表达为“当前知识库没有同时标注这些条件的方向”，不表示职业不存在；提供取消阶段限制且保留其他条件的链接。
- 方向标签的交集不证明特定“机构 × 阶段 × 职能”场景成立，也不生成匹配分数或改变 Profile 解释。

例如：学术生态目前包含考博/保研（阶段待确认）和临床科研（标注临床开发）。选择该生态后，阶段维度应显示已标注 1、待确认 1；选择上市后安全时可得到 0 个结果，此时应建议取消阶段限制。不得把空结果解释成“高校没有上市后研究”。

## 后续人工整理

典型/条件关联需要逐条领域依据，当前不将旧种子批量升级为已审核关系。未来可在 taxonomy source 增加审核后的关系元数据及场景约束；待有真实需求时再投影，不提前设计大型 ontology，也不依据文本相似度生成关联。
