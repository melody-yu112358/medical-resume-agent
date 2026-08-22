## 波次二启动模板

### 主 Agent：Action 4 Confirmation Gate正式实现

唯一仓库根目录：
D:\Users\书玉\Desktop\creating\medical-career-agent

必须先读取 CLAUDE.md：
是

上一个 Action 的冻结输入：
ExperienceDraft对象（extracted_facts, unknown_items, possible_value_angles, clarifying_questions, risk_flags）

本 Agent 任务：
实现Confirmation Gate服务，处理用户确认/修改/拒绝，生成Canonical Experience，确保原始证据不可覆盖，事实变化后旧Claim失效

允许修改文件：
- src/medical_career_agent/services/confirmation_gate.py
- src/medical_career_agent/api.py  
- tests/test_confirmation_gate.py
- schemas/canonical-experience.schema.json (如需扩展)

禁止修改文件：
- experience_draft.py
- role-packs/*.json
- bullet-claim.schema.json

必须复用的现有代码：
- 现有的Evidence Record结构
- Canonical Experience Schema
- API框架

验收条件：
- 用户可以确认、修改、拒绝事实
- 责任等级必须用户确认
- 原始证据不可覆盖
- 新增事实需要重新确认
- 生成合法的Canonical Experience

测试范围：
- 状态转换测试
- API输入输出测试  
- 用户交互场景测试
- 负向边界测试
- 与Action 3输出的集成测试

完成报告格式：
按协议要求的Action汇报格式

### 子 Agent A：完成 Action 5 Role Packs

唯一仓库根目录：
D:\Users\书玉\Desktop\creating\medical-career-agent

必须先读取 CLAUDE.md：
是

上一个 Action 的缺口矩阵：
[等待子 Agent B结果]

本 Agent 任务：
根据缺口矩阵补全四个Role Pack文件及Contract tests

允许修改文件：
- data/role-packs/doctoral_v1.json
- data/role-packs/clinical_research_v1.json  
- data/role-packs/medical_affairs_v1.json
- data/role-packs/health_ai_data_v1.json
- tests/test_role_packs.py

禁止修改文件：
- canonical-experience.schema.json
- experience_draft.py
- confirmation_gate.py

必须复用的现有代码：
- 现有的Role Pack Schema
- Meta分析样例

验收条件：
- 四个岗位包包含所有必需字段
- Contract tests通过
- 不改变事实，只配置表达边界

测试范围：
- Schema验证
- Contract tests
- 与Bullet Composer的集成测试

完成报告格式：
按协议要求的Action汇报格式

### 子 Agent B：Action 4 负向测试

唯一仓库根目录：
D:\Users\书玉\Desktop\creating\medical-career-agent

必须先读取 CLAUDE.md：
是

上一个 Action 的冻结输入：
Canonical Experience生成规则

本 Agent 任务：
设计并实现Action 4的负向测试用例

允许修改文件：
- tests/test_confirmation_gate_negative.py

禁止修改文件：
- confirmation_gate.py
- experience_draft.py
- api.py

必须复用的现有代码：
- 现有的测试框架
- Meta分析样例

验收条件：
- 覆盖所有负向场景
- 测试用例可重现
- 不产生误报

测试范围：
- 未确认事实进入Canonical Experience
- 模型推断责任等级
- 新增数字未确认
- 修改后丢失证据
- 原始证据被覆盖
- 旧Claim未失效

完成报告格式：
按协议要求的Action汇报格式

### 子 Agent C：Action 6 现有代码复用分析

唯一仓库根目录：
D:\Users\书玉\Desktop\creating\medical-career-agent

必须先读取 CLAUDE.md：
是

上一个 Action 的现状：
resume_translation.py已存在

本 Agent 任务：
分析现有resume_translation.py，输出Bullet Composer最小复用方案

允许修改文件：
- docs/bullet_composer_reuse_plan.md

禁止修改文件：
- resume_translation.py
- experience_draft.py
- confirmation_gate.py

必须复用的现有代码：
- resume_translation.py
- Role Pack配置
- Bullet Claim Schema

验收条件：
- 明确复用点和扩展点
- 不创建重复服务
- 方案可实施

测试范围：
- 现有代码功能分析
- 接口兼容性分析
- 扩展可行性分析

完成报告格式：
复用方案文档