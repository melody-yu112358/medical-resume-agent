# 文档导航与职责

先按问题选择文档。本文是阅读导航，文档分类与冲突处理仍遵循 [Documentation sources](DOCUMENTATION_SOURCES.md)。

| 要回答的问题 | 负责文档 | 不在该处重复维护 |
| --- | --- | --- |
| 当前有哪些资产，各自支持什么入口？ | [当前资产状态](CAREER_CATALOG_STATUS.md)，由机器源生成 | 其他说明文档不复制当前数量或 Pack/Card/规则/入口关联表 |
| 岗位有哪些职责边界，验证记录在哪里？ | [Role Pack 版图](CAREER_ROLE_PACK_LANDSCAPE.md) | 不维护库存与内部任务队列；精确语义仍来自 Pack JSON |
| 什么算角色，如何处理宽方向、角色簇与别名？ | [目录结构](CAREER_CATALOG_STRUCTURE.md) | 审查示例有日期，不作为持续更新的完整清单 |
| 如何采集、去重、分类并衡量扩展？ | [广度扩展方法](research/career-catalog-breadth-plan-v1.md) | 不维护批次工作量、排期或当前完成率 |
| 哪种方向适合何种研究深度？ | [中国覆盖矩阵](research/china-career-coverage-matrix-v1.md) | 启发式判断不是统计、库存或晋升状态 |
| 数据如何导入、版本化和回放？ | [数据库说明](CAREER_MAP_DATABASE.md) | 不重复职业库存 |
| 解释标签、适用性与来源如何定义？ | [解释契约](CAREER_EXPLANATION_CONTRACT.md) | 具体可解释方向读取规则源及状态页 |
| 如何浏览与筛选？ | [本地试用台](CAREER_MAP_LOCAL_VIEWER.md)、[筛选契约](CAREER_MAP_TAXONOMY.md) | 导航标签不决定转岗适配 |
| 候选研究、JD 来源和历史验证在哪里？ | [研究导航](research/README.md) | 研究词条不自动成为运行资产 |

**状态真值关系：** 机器源 → 生成的 `CAREER_CATALOG_STATUS.md` → 其他文档引用。状态页是唯一当前库存展示，不是第二份手工真值；数据库是按源导入的本地投影，未重新导入的数据库不一定等于仓库当前集合。

**历史与计划：** `BUILD_LOG`、`audits`、早期 Career Cards pilot、带阶段或版本的产品计划保留其当时语境；评分卡和 promotion record 保留当时证据及决定，不随库存更新而重写。旧计划中的阶段号、测试数和工作量不能当成当前进度。具体 PR 的实施顺序与工作量留在 PR 描述或任务记录。

本轮目录审查的范围与局限见 [文档审查记录](audits/documentation-boundaries-2026-09-06.md)。
