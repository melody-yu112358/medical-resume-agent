# Medical Career Agent — Claude Code 项目指令

## 唯一工作区

- 仓库根目录：`D:\Users\书玉\Desktop\creating\medical-career-agent`
- 所有读取、搜索、测试、Git 和写文件操作必须限定在该仓库。
- Shell 可能在每次调用后重置到其他目录。执行命令时显式指定仓库根目录；Git 优先使用 `git -C <repo>`。
- 不得读取或修改相邻项目 `爱弥儿_见老师材料包`。
- 找不到目标文件时先搜索真实路径，不根据协议概念猜文件名，不创建同义重复文件。

## 产品目标与冻结范围

本阶段交付“医学经历编译器”：将用户确认的真实经历，转换为四个目标方向下可直接用于简历的 1–3 条要点。

首批 Role Packs：

- `doctoral_v1`
- `clinical_research_v1`
- `medical_affairs_v1`
- `health_ai_data_v1`

Action 1–12 全部保留。不得用删减 Claim Ledger、前端、评测、文档或部署换取速度；优先通过复用、确定性检查和边界清楚的并行任务提速。开发顺序由依赖和验收条件决定，不以工时估算代替通过条件。

## 真实性边界

- 不得新增用户未确认的数字、动作、方法、工具、结果、职责或熟练度。
- 不得把“参与/协助”升级成“负责/独立/主导”。
- `possible_value_angles` 是解释和启发，不是用户事实。
- `confidence` 表示事实可信状态，不表示能力等级。
- 原始证据不可覆盖；用户新增事实必须重新确认。
- 多个候选句只能改变句式、排序和岗位角度，不得改变事实强度。
- 每个候选句是独立 Bullet Claim，具有独立 `claim_id` 和证据引用。

## 真实路径映射

逻辑版本名不是文件名：

- `canonical-experience-v1` → `schemas/canonical-experience.schema.json`
- `role-pack-v1` → `schemas/role-pack.schema.json`
- `bullet-claim-v1` → `schemas/bullet-claim.schema.json`

Action 3 相关文件：

- `src/medical_career_agent/services/experience_draft.py`
- `tests/test_experience_draft.py`
- `data/fixtures/meta-analysis-end-to-end-example.json`
- `tests/test_meta_analysis_example.py`

Role Packs 位于 `data/role-packs/*.json`。修改前先读取现有实现；不得另建同义 Service、Schema 或配置。

## Agent 协作

- 主 Agent 负责公共 Schema、API 契约、路由和最终整合。
- 子 Agent 只接收完成任务所需的最小上下文，并在开始前声明允许修改的文件。
- 同一文件同一时间只能由一个 Agent 修改。
- 审查 Agent 默认只读；测试 Agent 不修改正式实现，除非主 Agent 明确重新分配。
- 子 Agent 的结果必须由主 Agent 验证后才能计入完成状态。
- 不频繁轮询后台 Agent；等待结果后统一汇报。

## 验证阶梯

1. 修改中：只运行当前失败的单项测试。
2. 单项通过后：运行所属测试文件。
3. Action 收口：运行该 Action 的服务、API、Schema 和冻结样例相关回归。
4. 波次整合或 Action 10：运行完整回归。

代码未变化时复用已有测试结果，不为了生成汇报重复运行。只要存在未通过项，就不得宣称 Action 完成。

当前 Action 的完成报告必须包含：修改文件、未修改范围、实际测试结果、未通过项、风险、提交或 PR，以及下一 Action 的依赖是否满足。

## Windows 约束

- Python、JSON 和 Markdown 使用 UTF-8。
- 终端路径乱码不等于源文件损坏，不因此批量重写文件。
- LF/CRLF warning 只记录，不因此批量格式化仓库。
- 不在进行中的并发波次迁移 WSL 或重建环境。
- 禁止提交 `.env`、API Key、个人简历原文或其他敏感数据。
