# Action 4 Confirmation Gate 测试设计文档

## 状态转换

Confirmation Gate 的核心状态转换流程（流程状态，不写入Canonical Experience）：

1. **初始状态** (`candidate`) → 用户收到 Experience Draft
   - 包含 `extracted_facts`, `unknown_items`, `possible_value_angles`, `clarifying_questions`, `risk_flags`
   - 所有事实均为候选状态，需要用户确认

2. **用户确认路径** (`needs_confirmation` → `ready`)
   - 用户确认所有提取的事实
   - 责任等级必须明确确认（可以保持 "participated" 或升级）
   - 生成 `canonical_experience` 记录，状态为 `user_confirmed`（Canonical Experience状态）

3. **用户修改路径** (`needs_confirmation` → `edited` → `ready`)
   - 用户修改部分事实（如添加缺失的工具、修正责任等级等）
   - 新增事实必须重新确认并绑定到新证据记录
   - 原始证据不可覆盖，只能创建新的证据记录

4. **用户拒绝路径** (`needs_confirmation` → `rejected`)
   - 用户拒绝整个经历记录
   - Canonical Experience 状态设为 `rejected`
   - 相关 Bullet Claims 状态设为 `superseded`
   - **保留原始Evidence**: 拒绝时保留原始Evidence记录用于审计
   - **不生成可用经历**: 不生成可供Bullet Composer使用的`user_confirmed`经历
   - **状态限制**: 如果保留Canonical Experience审计记录，其状态只能是`rejected`
   - **禁止后续使用**: 拒绝记录不允许进入后续生成流程

5. **事实变更导致失效** (`ready` → `superseded`)
   - 当用户修改原始经历时，旧的 Canonical Experience 和所有相关 Bullet Claims 自动失效
   - 新的确认流程重新开始

**注意**: Confirmation Gate流程状态（`candidate`, `needs_confirmation`, `edited`, `ready`, `rejected`, `superseded`）仅用于内部流程控制，不会写入Canonical Experience。Canonical Experience的`status`字段严格遵守Schema定义：`user_confirmed`、`rejected`、`superseded`。

## API 输入输出契约建议

### POST /api/experience-confirmations

**输入 (Request Body):**
```json
{
  "experience_draft": {
    "extracted_facts": {...},
    "unknown_items": [...],
    "possible_value_angles": [...],
    "clarifying_questions": [...],
    "risk_flags": [...]
  },
  "user_actions": {
    "confirmed_facts": ["fact1", "fact2", ...],
    "modified_facts": {
      "tools": ["spss", "r"],
      "responsibility_level": "owned_component"
    },
    "new_evidence": "用户新增的具体描述文本",
    "disposition": "accept" | "edit" | "reject"
  },
  "evidence_records": [
    {
      "evidence_id": "ev_001",
      "source_text": "原始用户输入",
      "status": "confirmed"
    }
  ]
}
```

**输出 (Response Body):**
```json
{
  "canonical_experience": {
    "schema_version": "canonical-experience-v1",
    "experience_id": "exp_001",
    "evidence_ids": ["ev_001", "ev_002"],
    "context": {...},
    "role": {...},
    "actions": [...],
    "methods": [...],
    "tools": [...],
    "objects": [...],
    "collaboration": [...],
    "artifacts": [...],
    "outcomes": [...],
    "scope": {...},
    "unknowns": [...],
    "status": "user_confirmed" | "rejected" | "superseded"
  },
  "confirmation_status": {
    "status": "ready" | "rejected" | "needs_more_info",
    "missing_confirmations": [...],
    "validation_errors": [...]
  }
}
```

## 确认、修改、拒绝路径

### 确认路径
- 用户确认所有提取的事实无需修改
- 责任等级必须从默认的 "participated" 明确升级或保持
- 生成完整的 Canonical Experience 记录
- 所有字段必须有对应的证据引用

### 修改路径
- 用户可以修改任何字段值（如添加工具、修正方法等）
- 新增的事实必须通过 `new_evidence` 字段提供原始证据
- 系统创建新的证据记录（如 `ev_002`）并与修改后的事实关联
- 原始证据记录（`ev_001`）保持不变，确保不可覆盖原则

### 拒绝路径
- 用户可以拒绝整个经历记录
- Canonical Experience 状态设为 "rejected"
- 所有相关的 Bullet Claims 状态设为 "superseded"
- 用户可以选择提供拒绝原因用于系统改进

## 责任等级确认

责任等级确认是 Confirmation Gate 的关键验证点：

1. **默认保守原则**: Experience Draft 默认设置 `responsibility_level: "participated"`
2. **用户确认要求**: 用户必须明确确认责任等级，可以保持 `participated` 作为最终值，也可以升级到更高级别
3. **升级验证**: 如果用户将责任等级升级（如到 "owned_component" 或 "led_delivery"），必须提供相应的证据支持
4. **防止自动升级**: 系统不得基于关键词（如"负责"、"主导"）自动升级责任等级，必须由用户明确确认。`participated` 是合法的最终责任等级，不需要为了通过确认而强制升级。

## 证据绑定

### 证据不可覆盖原则
- 每个证据记录一旦创建就不可修改
- 证据记录包含：`evidence_id`, `source_text`, `source_locator`, `status`, `confirmed_at`
- 当用户修改事实时，创建新的证据记录而不是修改现有记录

### 证据追溯性
- Canonical Experience 的每个字段都必须能追溯到具体的证据记录
- Bullet Claims 必须明确列出使用的 `evidence_ids`
- 系统维护完整的证据链，确保每个声明都有原始依据
- **字段级证据映射**: Action 4服务响应和Confirmation Record必须维护`fact_evidence_map`，例如：
  ```json
  {
    "fact_evidence_map": {
      "actions.retrieve_literature": ["ev_001"],
      "role.responsibility_level": ["ev_002"]
    }
  }
  ```
- **不修改Schema**: `fact_evidence_map`不直接加入已经冻结的Canonical Experience，不修改`canonical-experience.schema.json`
- **完整性要求**: 每个进入Canonical Experience的非空事实必须出现在`fact_evidence_map`
- **后续使用**: `fact_evidence_map`供Bullet Composer、Claim Gate和Ledger使用

## 用户新增事实重新确认

当用户在确认过程中新增事实时：

1. **新增证据记录**: 创建新的证据记录（如 `ev_002`）包含用户的新增描述
2. **事实绑定**: 将新增的事实字段绑定到新的证据记录
3. **重新验证**: 对新增的事实进行同样的真实性边界检查
4. **完整性检查**: 确保新增事实不会与现有事实产生逻辑冲突

例如：
- 用户原始输入："参与Meta分析"
- 用户新增："使用了PubMed和Embase两个数据库"
- 系统创建 `ev_002` 包含新增文本
- **字段映射**: 数据库名称按现有字段语义进行映射（如归入`scope.databases`而非默认`tools`）
- `scope.database_count` 设置为 "2"

## 事实变化导致旧Claim失效

Action 4只负责识别并输出失效事件，不实现完整Claim Ledger（留给Action 8）：

当用户的原始经历发生变更时：

1. **失效事件输出**: Action 4服务响应中包含失效事件信息，例如：
   ```json
   {
     "invalidation": {
       "previous_experience_id": "exp_001",
       "reason": "confirmed_fact_changed",
       "invalidate_related_claims": true
     }
   }
   ```
2. **版本追踪**: 系统维护经历的版本历史，每个版本有唯一的 `experience_id`
3. **用户通知**: 通知用户之前的简历要点已失效，需要重新确认
4. **数据保留**: 失效的数据仍然保留用于审计和历史追踪，但不再用于简历生成
5. **不提前实现Ledger**: Action 4不实现完整的Claim状态存储和跨页面审计，这些留给Action 8

## 正向测试清单

### 基本功能测试
- [ ] 用户确认所有事实，生成有效的 Canonical Experience
- [ ] 责任等级正确确认和绑定
- [ ] 所有提取的事实都能追溯到证据记录
- [ ] Canonical Experience 通过 Schema 验证

### 修改场景测试
- [ ] 用户添加缺失的工具信息，创建新的证据记录
- [ ] 用户修正责任等级，提供相应证据
- [ ] 用户补充范围信息（如研究数量），正确绑定到新证据
- [ ] 修改后的 Canonical Experience 保持数据一致性

### 集成测试
- [ ] 与 Action 3 的 Experience Draft 输出正确集成
- [ ] 生成的 Canonical Experience 能正确用于 Bullet Composer
- [ ] 四个 Role Pack 能基于确认的经历生成不同的表达
- [ ] 端到端流程：Draft → Confirm → Compose → Generate

### 边界测试
- [ ] 空的未知项列表处理
- [ ] 最大长度的用户输入处理
- [ ] 特殊字符和 Unicode 文本处理
- [ ] 并发确认请求处理

## 负向测试清单

### 真实性边界测试
- [ ] 阻止未确认的事实进入 Canonical Experience
- [ ] 阻止模型自动推断责任等级（如将"参与"升级为"负责"）
- [ ] 阻止新增未确认的数字（如猜测研究数量）
- [ ] 阻止将"参与/协助"升级成"负责/独立/主导"

### 数据完整性测试
- [ ] 阻止原始证据被覆盖或修改
- [ ] 阻止创建没有证据引用的事实字段
- [ ] 阻止责任等级未确认就生成 Canonical Experience
- [ ] 阻止无效的证据 ID 引用

### 安全性测试
- [ ] 阻止 SQL 注入或 XSS 攻击载荷
- [ ] 阻止超大输入导致内存溢出
- [ ] 阻止无效的 JSON 结构导致系统崩溃
- [ ] 阻止未授权访问其他用户的经历数据

### 状态管理测试
- [ ] 阻止对已拒绝的经历进行再次确认
- [ ] 阻止对已失效的经历生成新的 Bullet Claims
- [ ] 阻止在缺少必要字段时完成确认流程
- [ ] 阻止重复的证据 ID 创建

## 对 Action 3 冻结输出的依赖

Confirmation Gate 完全依赖 Action 3 的 Experience Draft 输出格式：

1. **输入结构依赖**: 
   - `extracted_facts` 对象结构
   - `unknown_items` 数组格式
   - `clarifying_questions` 限制为最多3个问题
   - `risk_flags` 识别潜在风险

2. **字段映射依赖**:
   - Context domain/setting 的枚举值
   - Responsibility level 的枚举值
   - Actions/methods/tools 的标准化命名
   - Unknown items 的预定义标识符

3. **验证规则依赖**:
   - 使用相同的事实提取规则
   - 遵循相同的保守默认原则
   - 继承相同的风险识别逻辑

4. **测试数据依赖**:
   - `meta-analysis-end-to-end-example.json` 作为主要测试用例
   - 相同的 forbidden_outputs 列表用于验证
   - 相同的四个 Role Pack 配置

## 仍需主 Agent 决定的问题

1. **API 路由设计**: 
   - 使用协议规定的 `/api/experience-confirmations` 路由
   - 确认状态的持久化策略

2. **证据存储机制**:
   - 证据记录的存储格式和位置
   - 证据 ID 的生成策略（全局唯一 vs 会话内唯一）

3. **用户体验流程**:
   - 确认界面的具体交互设计
   - 修改时的增量确认 vs 全量重新确认
   - 拒绝后的反馈收集机制

4. **错误处理策略**:
   - 部分确认失败时的回滚机制
   - 网络中断时的状态恢复
   - 并发修改的冲突解决

**注意**: 不实现大规模批量确认、缓存优化等与本Action核心功能无关的项目。重点确保正确性、安全性和并发修改处理。