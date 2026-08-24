# Medical Resume Skill Lite

[中文说明](#中文说明) · [English](#english)

## 中文说明

`Medical Resume Skill Lite` 是给 Codex、Claude Code 等 AI 编程助手使用的医学简历工作流。它不启动网页或独立 API；AI 工具在对话中根据 Skill 的事实确认、医学能力分类和表达规则，帮助用户整理经历并交付本地 HTML 简历。

### 它解决什么问题

医学经历常被写成“参与科研”“协助数据分析”这类宽泛描述。Skill 会先把一段经历拆成可核对的研究对象、方法、工具、实验技术、个人角色和交付物，再按照目标方向调整表达重点。

它支持三种任务：

1. 从零整理一段零散经历；
2. 只润色现有简历中的一到三条经历；
3. 在内容确认后，生成可打印的单栏 A4 HTML 简历。

默认交付“专业版”表达；同一组已确认事实还可生成稳妥版与高竞争力版供用户比较。Skill 不会虚构实验、升级责任边界，或把 JD 要求写成个人经历。

### 核心能力

| 能力 | 作用 |
| --- | --- | --- |
| 经历事实卡 | 从原始描述中提取研究对象、方法、工具、角色、交付物和待确认信息，并一次只追问最多 3 个关键问题 |
| 目标方向翻译 | 按学术升学与科研申请、临床研究与医院科研、医学事务 / MSL、医疗数据与数字健康调整表达重点 |
| 三档改写 | 以同一组确认事实生成稳妥版、专业版和高竞争力版，避免“参与”被无依据升级为“主导” |
| 本机交付 | 在用户确认后生成可打印的 A4 HTML、结构化数据、改写对照与证据摘要；头像为可选本地图片 |

### 医学能力词典概要

Skill 将下列信息分开识别，而不是堆成一串“技能关键词”。完整定义见 [能力词典](medical-resume-skill/references/capability-taxonomy.md)。

| 类别 | 代表内容 |
| --- | --- |
| 研究设计与方法 | 队列研究、RCT、MR、Meta 分析、GWAS、生物信息、机器学习 |
| 数据与工具 | R、Python、SPSS、SQL、数据清洗、统计分析、可视化 |
| 临床研究设计与执行 | 入排标准、随访、CRF、伦理、GCP、真实世界研究、数据质控 |
| 实验技术 | 细胞培养、qPCR、Western Blot、流式细胞术、ELISA、动物实验 |
| 医学证据与信息 | PubMed、Embase、Cochrane、指南解读、证据分级、医学写作 |

### 安装一览

| AI 工具 | 个人安装（所有项目可用） | 项目安装（仅当前仓库） | 调用方式 |
| --- | --- | --- | --- |
| Codex | `~/.codex/skills/medical-resume-skill` | `.codex/skills/medical-resume-skill` | `$medical-resume-skill` 或自然语言 |
| Claude Code | `~/.claude/skills/medical-resume-skill` | `.claude/skills/medical-resume-skill` | `/medical-resume-skill` 或自然语言 |

个人安装更适合长期使用；项目安装更适合团队共同维护的简历项目。不要在已有同名目录内部再次复制该文件夹，否则会形成 `medical-resume-skill/medical-resume-skill` 这种嵌套结构。

### 安装到 Codex

推荐在 Codex 的新对话中发送下面这句，让内置安装器从 GitHub 安装完整 Skill 包：

```text
$skill-installer install https://github.com/melody-yu112358/medical-resume-agent/tree/main/skill-lite/medical-resume-skill
```

安装完成后新开一个 Codex 对话，再这样开始：

```text
请用 medical-resume-skill 帮我整理下面这段真实经历，目标是医学事务 / MSL。
先生成事实卡，只问最关键的缺失信息；不要补充我没有确认的责任、方法、数字或成果。
```

已有完整简历时：

```text
请用 medical-resume-skill 只润色我下面第 2、4 条科研经历；目标是临床研究与医院科研。
保留其他内容，不要新增未确认事实。先展示事实卡和待确认问题。
```

### 安装到 Claude Code

在仓库根目录执行下列命令，将整个 Skill 文件夹复制到 Claude Code 的个人 Skill 目录。macOS / Linux：

```bash
mkdir -p ~/.claude/skills
cp -R skill-lite/medical-resume-skill ~/.claude/skills/
```

如果希望只在当前项目使用，将目标目录改为 `.claude/skills/`：

```bash
mkdir -p .claude/skills
cp -R skill-lite/medical-resume-skill .claude/skills/
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills"
Copy-Item -Recurse -Force ".\skill-lite\medical-resume-skill" "$HOME\.claude\skills\"
```

重启 Claude Code 后，可以输入 `/medical-resume-skill`，或直接说明希望它使用该 Skill 整理一段真实经历。若要更新已安装版本，请先移除或改名同目录下已有的 `medical-resume-skill` 文件夹，再复制新版本，避免产生嵌套目录。

### 可选：Windows 便利脚本

`install-skill.ps1` 仅为 Windows 用户保留，作用也是把完整文件夹复制到 `~/.codex/skills/medical-resume-skill`。跨平台使用时，优先采用上面的 Codex 安装器或 Claude Code 目录复制方式。

### 交付物与边界

Skill 的输入是用户提供或确认的经历、简历片段和可选 JD；输出是经用户确认后生成的简历要点与本机 `resume-output/`。它不是自动背书工具：姓名、时间线、方法熟练度、个人责任、指标、论文状态和证书均需由用户确认。导出前请逐条复核。

### 模型、联网与交付

Skill 不包含 API Key，也不绑定某一家模型。它使用 Codex、Claude 或兼容工作流中已经配置的模型；没有模型时仍可按事实卡和审校规则工作，但不应承诺自动生成高质量润色。

默认只使用用户在对话或所提供文件中确认的材料。用户可以提供 JD、岗位链接、论文 DOI，或明确允许联网搜索，以启用 JD / 公开证据辅助。公开信息只用于理解岗位语言、核对引用或发现能力缺口，不能成为个人经历的证据。

用户确认内容并明确要求导出后，Skill 在本机生成 `resume-output/`，其中包含可打印的 `resume.html`、结构化数据、证据摘要、改写对照与导出说明。头像默认不显示；用户主动提供本地图片时，才会在 HTML 简历右上角放置本地头像框。复杂 PDF、双栏 Word 或扫描件的文本提取仍需人工核对。

### 与网页版本的关系

网页版本适合可视化地输入、确认和预览；Skill Lite 适合在对话中深入梳理材料、比较多种表达并直接交付本机 HTML。两者共用“事实优先”的原则，但可以独立使用。

### 包结构（维护者参考）

| 文件或目录 | 面向谁 | 用途 |
| --- | --- | --- |
| 仓库根目录 `README.md` | GitHub 访客 | 项目概览，以及网页和 Skill 两个入口的选择 |
| 本文件 | 安装 Skill 的用户 | 安装、调用方式、模型与隐私边界 |
| `medical-resume-skill/SKILL.md` | Codex / Claude 等 AI 工具 | 主执行流程与不可突破的事实边界 |
| `medical-resume-skill/references/` | AI 工具按需读取 | 医学能力分类、岗位表达、提示词、HTML 交付与联网规则 |
| `medical-resume-skill/assets/` | 最终交付文件 | 可打印的 A4 HTML 模板 |

安装时请复制整个 `medical-resume-skill` 文件夹，而不是只复制 `SKILL.md`。这样 AI 工具才能在需要时读到相应参考资料和模板。

## English

`Medical Resume Skill Lite` is a workflow for AI coding tools such as Codex and Claude Code. It does not start a web app or a separate API. The AI tool uses the bundled fact-confirmation flow, medical capability taxonomy, and writing rules to turn real medical experience into a local HTML resume.

Install the entire `medical-resume-skill` folder, not only `SKILL.md`, so the model can access its references and HTML template.

For Codex, send this in a new Codex conversation:

```text
$skill-installer install https://github.com/melody-yu112358/medical-resume-agent/tree/main/skill-lite/medical-resume-skill
```

For Claude Code, copy the folder into a personal or project skills directory:

```bash
mkdir -p ~/.claude/skills
cp -R skill-lite/medical-resume-skill ~/.claude/skills/
```

Use `.claude/skills/` instead for a project-only Claude Code Skill. Start a new Codex or Claude Code conversation, then ask it to use `medical-resume-skill` with a real experience and a target direction. The Skill supports building a single experience, polishing one to three existing entries, and delivering an accepted full resume as printable A4 HTML. It uses only confirmed facts by default and must not invent work, upgrade responsibility, or turn a job requirement into a personal achievement.

The Skill uses the model configured for the AI tool and contains no API key. JD/public-evidence assistance is opt-in: a user must supply a JD, URL, DOI, or explicit browsing permission. Public information may improve role-language alignment, but never becomes evidence of a user's own experience. The generated `resume-output/` stays local; an optional profile image is used only when the user explicitly supplies one.

For installation scope, use `~/.codex/skills/medical-resume-skill` or `~/.claude/skills/medical-resume-skill` for a personal Skill, and `.codex/skills/medical-resume-skill` or `.claude/skills/medical-resume-skill` for a project-only Skill. Copy the entire folder and avoid copying it into an existing folder with the same name.
