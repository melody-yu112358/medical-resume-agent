# 未界医学简历助手

<p align="center">
  <a href="#在自己的电脑上运行"><img src="https://img.shields.io/badge/LOCAL-FIRST-245A47?style=flat-square" alt="Local first" /></a>
  <img src="https://img.shields.io/badge/EVIDENCE-BOUND-5E8570?style=flat-square" alt="Evidence bound" />
  <img src="https://img.shields.io/badge/285-TESTS-8BAA97?style=flat-square" alt="285 tests" />
  <img src="https://img.shields.io/badge/MEDICAL-CAREER-244638?style=flat-square" alt="Medical career" />
</p>

<p align="center"><b>简体中文</b> · <a href="README.en.md">English</a> · <a href="skill-lite/README.md">Skill Lite</a></p>

一个可在自己电脑上运行的医学经历编译器，面向医学生的申学与医学相关求职场景。

用户先提交一段经历，核对系统提取出的事实，再选择目标方向。系统据此生成可以继续编辑的简历要点，并显示该要点使用了哪些已确认信息。

它适合把“参与科研”“协助数据分析”这类概括性描述，拆成研究对象、方法、工具、个人角色和交付物，再确定应在简历中优先呈现什么。

> 真实经历 → 已确认的研究对象、方法、工具、角色与交付物 → 可迁移能力 → 目标方向关注的价值表达

| 你提供什么 | 系统如何处理 | 你拿到什么 |
| --- | --- | --- |
| 一段真实的医学经历 | 提取事实、追问缺失信息、等待确认 | 按目标方向生成的候选简历要点 |
| 一段包含方法、工具或实验技术的经历 | 分别识别 MR/Meta 等研究方法、R/Python 等分析工具、qPCR/WB 等实验技术，以及 PubMed/Embase 等检索资源 | 可解释的能力结构，而不是关键词堆砌 |
| 你的目标方向 | 调整表达重点，不改写真实经历 | 可追溯、可编辑、可核查的材料 |

## 快速开始

```powershell
.\start-local.ps1
```

然后打开：`http://127.0.0.1:5000/demo/experience-compiler/index.html`

首次使用可载入内置的脱敏 Meta 分析示例。完整安装步骤见[在自己的电脑上运行](#在自己的电脑上运行)。

## 适用场景

医学科研和临床经历往往同时包含研究问题、方法、软件工具、实验技术和执行工作。若简历只保留“参与科研”“负责文献检索”或“协助数据分析”等概括性描述，读者很难判断具体的工作内容和责任边界。

页面将原始经历整理为可确认事实，包括研究设计、分析方法、工具、实验技术、临床研究流程、个人角色、数据或文献来源与交付物。用户确认后，系统再生成对应方向的候选要点。

## 初版医学能力分类

项目目前按下列维度整理医学经历中的能力信息。它们用于帮助用户确认事实和选择表达重点，不代表仅凭关键词即可认定掌握某项能力。

1. **研究设计与方法**：队列研究、RCT、Meta 分析、孟德尔随机化（MR）、GWAS、生物信息学、机器学习等；
2. **数据与工具**：R、Python、SPSS、SQL、数据清洗、统计分析与可视化等；
3. **临床研究设计与执行**：入排标准、随访、CRF、伦理、GCP、真实世界研究与数据质控等；
4. **实验技术**：细胞培养、qPCR、Western Blot、流式细胞术、ELISA、动物实验等；
5. **医学证据与信息能力**：PubMed、Embase、Cochrane 检索、指南解读、证据分级与医学写作等。

## 使用流程

1. 输入一段真实医学经历，或载入内置的脱敏 Meta 分析示例。
2. 查看候选事实与最多 3 个澄清问题。
3. 确认、修改或拒绝事实；未确认信息不会被静默升级成经历。
4. 选择目标方向，生成 1–3 条候选简历要点。
5. 查看依据事实、风险提示和审计记录，再复制或导出使用。

首发版本提供四个重点方向：

- **学术升学与科研申请**（保研、考研复试、直博、博士申请）：研究问题、方法深度与科研潜力。
- **临床研究与医院科研**：研究设计、临床问题、研究执行与协作。
- **医学事务 / MSL**：证据解读、疾病领域知识与医学信息转译。
- **医疗数据与数字健康**：数据处理、分析框架与结果沟通。

药物注册、市场准入、药物警戒、商业化和纯临床诊疗等方向暂未单列为 Role Pack，后续根据测试反馈扩展。

## 使用规则与已知限制

- 候选要点只使用用户确认的事实；系统不会将“参与”改写为“主导”，也不会补充未提供的数字、方法、工具或结果。
- 能力分类用于解释经历，不用于仅凭关键词判断熟练度。R/Python、MR/Meta、qPCR/WB 和 PubMed/Embase 分别属于不同类别，需结合用户说明确认。
- 当前文件提取适合普通 DOCX、TXT、Markdown 和带可复制文字的 PDF。双栏、复杂表格和扫描件 PDF 的文本顺序可能不可靠，应在确认页人工校正。
- 本地 Beta 不提供录用、薪资或岗位匹配结论，也不复刻任意既有简历的视觉版式。

## 在自己的电脑上运行

### 需要什么

- Windows 10/11（首发启动脚本面向 Windows）
- Python 3.11 或更高版本
- 网络仅用于首次安装 Python 依赖；之后网页和经历处理在本机运行

### 最快启动

1. 下载仓库 ZIP 并解压，或执行：

   ```powershell
   git clone https://github.com/melody-yu112358/medical-resume-agent.git
   cd medical-resume-agent
   ```

2. 在项目目录打开 PowerShell 后运行：

   ```powershell
   .\start-local.ps1
   ```

   首次运行会安装所需依赖。若 PowerShell 阻止脚本，请只对当前窗口执行：

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\start-local.ps1
   ```

3. 看到服务启动提示后，在浏览器打开：

   ```text
   http://127.0.0.1:5000/demo/experience-compiler/index.html
   ```

4. 用完后回到 PowerShell，按 `Ctrl + C` 停止本地服务。

### 可选：模型表达优化

不配置模型也可体验确定性事实提取、确认、岗位要点生成和审计流程。若希望启用 OpenAI-compatible 模型（例如 DeepSeek）的受约束表达优化，先执行：

```powershell
Copy-Item .env.example .env
```

再按照 [模型配置说明](docs/LLM_INTEGRATION.md) 在本机 `.env` 中填写自己的密钥。`.env` 已被 Git 忽略，绝不要把密钥粘贴到网页、截图或 GitHub Issue 中。

## 面向 Codex/Claude 用户的 Skill Lite

网页适合不想配置 AI 工具的用户；仓库也提供轻量 Skill，适合在 Codex 或 Claude 中进行更深入的“经历问诊”：

Skill 默认先确认事实，再按不同内容维度规划每段经历，并提供稳妥版、专业版和高竞争力版。证据充分的代表经历可以形成 5–9 条互不重复的要点；默认交付专业版高密度 HTML，同时保留其他版本供用户选择。信息密度来自背景、职责、方法、工具、质控、协作和产出等不同事实，不来自重复句或虚构数字。

- [Skill Lite 使用说明](skill-lite/README.md)
- [Skill 入口](skill-lite/medical-resume-skill/SKILL.md)

Skill Lite 复用了本项目的核心方法：先拆事实、再确认、最后按目标方向翻译。它是提示词与工作流包，不替代网页中的 Claim Gate 和审计能力。

## 验证

```powershell
python -m pip install -e ".[resume_extract,dev,schema_validation]"
python -m pytest -q
```

当前共享发布源包含 205 项单元、接口与端到端测试。发布前还应完成浏览器冒烟测试：载入示例、提取事实、确认、选择方向、生成要点、查看证据并导出。

## 仓库结构

```text
demo/experience-compiler/  可直接体验的医学经历编译器页面
src/medical_career_agent/  经历提取、确认、要点生成、Claim Gate 与账本服务
schemas/                   canonical experience、role pack、bullet claim 数据契约
data/role-packs/           四个目标方向的表达策略
skill-lite/                面向 Codex/Claude 用户的轻量工作流包
docs/                      架构、边界、模型配置与验收材料
tests/                     合成案例、接口与边界测试
```

## 贡献与测试

欢迎医学生、医学相关专业研究生，以及关注医学科研、升学或医疗行业发展的朋友，使用已脱敏的经历参与测试。请勿提交真实姓名、联系方式、病历、受试者信息、未公开研究数据或任何密钥。
