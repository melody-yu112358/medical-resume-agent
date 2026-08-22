# Action 4 Confirmation Gate 复用映射分析

## 可复用的现有功能

### 1. 用户确认状态管理
- **文件**: `src/medical_career_agent/services/resume_structurer.py`
- **函数**: `ResumeStructurer.structure()`
- **复用点**: 
  - `ExtractedEvidence` 数据类包含 `status` 字段（默认为 "extracted"）
  - 现有状态转换逻辑可扩展为 Confirmation Gate 的核心状态机
  - 证据ID生成模式 (`import-line-{line_number:03d}`) 可复用于经历草稿

### 2. Evidence绑定机制
- **文件**: `src/medical_career_agent/services/resume_translation.py`
- **函数**: `ResumeTranslationService.translate()`
- **复用点**:
  - `confirmed_evidence` 集合过滤逻辑（第90-94行）
  - `evidence_ids` 元组绑定到能力项
  - 证据验证：`set(evidence_ids).issubset(confirmed_evidence)` 模式

### 3. 结构化字段修改处理
- **文件**: `src/medical_career_agent/services/profile_drafter.py`
- **函数**: `confirmed_profile_from_payload()`
- **复用点**:
  - 用户确认的profile payload解析模式
  - 输入验证和错误处理框架

### 4. API请求验证框架
- **文件**: `src/medical_career_agent/api.py`
- **复用点**:
  - 统一的错误处理模式（400/502状态码）
  - payload验证和类型检查
  - `/api/experience-drafts` 端点已存在，可扩展为Confirmation Gate端点

### 5. 本机审计日志
- **文件**: `src/medical_career_agent/adapters/file_session_store.py`
- **复用点**:
  - 会话状态存储和事件追加机制
  - 可用于记录用户确认/修改/拒绝操作的历史

## 缺失能力

### 1. Claim失效和版本处理
- 现有代码中没有处理事实变化导致旧Claim失效的机制
- 需要实现版本控制或时间戳机制来跟踪Claim有效性

### 2. 责任等级确认专用逻辑
- 现有代码没有专门处理责任等级（参与/协助 vs 负责/独立/主导）的确认流程
- 需要新增责任等级验证和升级防护

### 3. 原始证据不可覆盖保护
- 现有代码没有明确的原始证据保护机制
- 需要实现只读保护或版本快照

### 4. Canonical Experience生成
- 现有代码缺少从确认的事实生成Canonical Experience的逻辑
- 需要实现符合 `canonical-experience.schema.json` 的序列化器

## 建议最小新增文件

### 必需新增
1. **`src/medical_career_agent/services/confirmation_gate.py`**
   - 实现Confirmation Gate核心服务
   - 包含状态转换、证据绑定、Claim失效处理

2. **`tests/test_confirmation_gate.py`**
   - 正向测试用例
   - 集成测试

3. **`tests/test_confirmation_gate_negative.py`**
   - 负向测试用例（由子Agent B提供）

### 可选扩展
4. **`src/medical_career_agent/domain/canonical_experience.py`**
   - Canonical Experience数据模型（如果需要复杂验证逻辑）

## 不应重建的能力

- **Evidence ID生成**: 复用现有的 `import-line-{line_number:03d}` 模式
- **API框架**: 复用现有的Flask路由和错误处理模式
- **会话存储**: 复用现有的FileSessionStore
- **输入验证**: 复用现有的payload验证模式

## Action 4与现有系统的接入点

### API层
- 扩展现有 `/api/experience-drafts` 端点或新增 `/api/confirmation-gate` 端点
- 复用现有的认证和错误处理中间件

### 服务层
- Confirmation Gate服务依赖ExperienceDraftService的输出
- 为ResumeTranslationService提供Confirmed Canonical Experience输入

### 数据层
- 复用现有的会话存储机制记录用户交互历史
- 可能需要扩展证据存储以支持版本控制

### 前端集成
- 现有的resume-beta界面可能需要扩展确认流程组件
- 复用现有的证据展示和交互模式