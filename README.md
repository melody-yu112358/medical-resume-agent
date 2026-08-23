# 未界医学简历助手

<p align="center">
  <a href="#在自己的电脑上运行"><img src="https://img.shields.io/badge/LOCAL-FIRST-245A47?style=flat-square" alt="Local first" /></a>
  <img src="https://img.shields.io/badge/EVIDENCE-BOUND-5E8570?style=flat-square" alt="Evidence bound" />
  <img src="https://img.shields.io/badge/205-TESTS-8BAA97?style=flat-square" alt="205 tests" />
  <img src="https://img.shields.io/badge/MEDICAL-CAREER-244638?style=flat-square" alt="Medical career" />
</p>

<p align="center"><b>简体中文</b> · <a href="README.en.md">English</a> · <a href="skill-lite/README.md">Skill Lite</a></p>

一个可在自己电脑上运行的医学经历编译器，面向医学生的申学与医学相关求职场景。

用户先提交一段经历，核对系统提取出的事实，再选择目标方向。系统据此生成可以继续编辑的简历要点，并显示该要点使用了哪些已确认信息。

它适合把“参与科研”“协助数据分析”这类概括性描述，拆成研究对象、方法、工具、个人角色和交付物，再确定应在简历中优先呈现什么。

| 你提供什么 | 系统如何处理 | 你拿到什么 |
| --- | --- | --- |
| 一段真实的医学经历 | 提取事实、提出缺失信息问题并等待确认 | 按目标方向生成的候选简历要点 |
| MR / Meta / R / qPCR 等线索 | 区分方法、工具、实验技术与检索资源 | 可解释的能力结构，而不是关键词堆砌 |
| 你的目标方向 | 调整表达重点，不改写真实经历 | 可追溯、可编辑、可核查的材料 |

## 当前功能

- 输入一段医学经历，或载入内置的脱敏 Meta 分析示例；
- 提取研究方法、软件工具、实验技术、研究流程、个人角色和交付物等候选事实；
- 对信息不足之处提出最多三个澄清问题；
- 允许用户确认、修改或拒绝候选事实；
- 面向四类方向生成候选简历要点，并保留相应的依据和风险提示；
- 复制或导出生成结果；
- 使用本仓库附带的 Skill Lite，在 Codex 中进行相同的事实确认与经历整理流程。

目前提供的目标方向如下：

| 方向 | 写作时优先呈现的内容 |
| --- | --- |
| 保研 / 考博 | 研究问题、方法学基础、研究潜力 |
| 临床科研 | 研究设计、临床研究执行、数据与协作 |
| 医学事务 / MSL | 证据解读、疾病领域信息、医学沟通 |
| 医疗 AI / 医学数据 | 数据处理、分析思路、结果呈现 |

这些方向只影响同一段真实经历的呈现重点，不会改变用户确认过的事实。

## 使用方式

在 Windows PowerShell 中进入项目目录，运行：

```powershell
.\start-local.ps1
```

服务启动后，打开：

```text
http://127.0.0.1:5000/demo/experience-compiler/index.html
```

首次体验建议直接载入页面中的脱敏 Meta 分析示例，依次完成事实确认、目标方向选择和要点生成。

### 首次运行

需要 Windows 10/11 和 Python 3.11 或更高版本。首次运行时，脚本会安装缺失的 Python 依赖；后续处理在本机完成。

如果尚未下载项目，可以使用：

```powershell
git clone https://github.com/melody-yu112358/medical-resume-agent.git
cd medical-resume-agent
.\start-local.ps1
```

如果 PowerShell 阻止脚本执行，只对当前窗口执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-local.ps1
```

服务结束后，在 PowerShell 按 `Ctrl + C` 即可停止。

## 事实与表达边界

系统将“工具、方法、技术和研究资源”分别处理。例如 R/Python 属于软件工具，MR/Meta 属于研究方法，qPCR/WB 属于实验技术，PubMed/Embase 属于文献检索资源。它们在简历中的含义不同，不应简单合并成一项笼统的“科研能力”。

生成较强的简历表述前，用户需要确认个人承担的环节和可核实的产出。对于缺少依据的信息，页面会保留风险提示或提出补充问题；不会自动加入“主导”“独立完成”、数字化结果或未提供的方法。

当前上传与解析功能适合普通 DOCX、TXT、Markdown 和带可复制文字的 PDF。双栏、复杂表格和扫描件 PDF 的文本顺序可能不可靠，建议在确认页人工校正。项目不承诺岗位匹配、录用结果，也不复刻任意已有简历的视觉版式。

## 可选：配置模型

不配置模型也可以使用事实提取、确认、目标方向表达和审计流程。若要启用 OpenAI-compatible 模型（如 DeepSeek）进行受约束的文字优化，先创建本地配置文件：

```powershell
Copy-Item .env.example .env
```

随后按[模型配置说明](docs/LLM_INTEGRATION.md)填写本机 `.env`。不要把密钥提交到 Git、贴到网页代码中，或放入截图和 Issue。

## Skill Lite

`skill-lite/` 包含一个面向 Codex 的轻量工作流包。它适合希望在对话中逐步梳理经历的用户，流程同样要求先确认事实，再生成针对目标方向的表达。

安装与使用方式见：[Skill Lite 使用说明](skill-lite/README.md)。Skill Lite 是提示词和工作流包，不会替代网页中的事实确认、Claim Gate 和审计记录。

## 验证

```powershell
python -m pip install -e ".[resume_extract,dev,schema_validation]"
python -m pytest -q
```

当前发布源包含 205 项单元、接口和端到端测试。发布或演示前，仍建议手动走一遍页面：载入示例、确认事实、选择方向、生成要点、检查依据和导出结果。

## 目录说明

```text
demo/experience-compiler/  医学经历编译器页面
src/medical_career_agent/  经历提取、确认、要点生成、Claim Gate 与账本服务
schemas/                   Canonical Experience、Role Pack、Bullet Claim 的数据契约
data/role-packs/           四类目标方向的表达策略
skill-lite/                Codex Skill Lite
docs/                      架构、边界、模型配置和验收材料
tests/                     合成案例、接口和边界测试
```

## 反馈与隐私

欢迎使用已脱敏的经历进行测试。请不要提交真实姓名、联系方式、病历、受试者信息、未公开研究数据或任何密钥。
