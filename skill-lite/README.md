<h1 align="center"> Medical Resume Skill </h1>

[中文说明](#中文说明) · [English](#english)

## 中文说明

`Medical Resume Skill Lite` 是给 Codex、Claude Code 等宿主模型使用的医学简历工作流。它不启动网页或独立 API；模型在对话中根据 Skill 的事实确认、医学能力分类和表达规则，帮助用户整理经历并交付本地 HTML 简历。

### 它解决什么问题

医学经历常被写成“参与科研”“协助数据分析”这类宽泛描述。Skill 会先把一段经历拆成可核对的研究对象、方法、工具、实验技术、个人角色和交付物，再按照目标方向调整表达重点。

它支持三种任务：

1. 从零整理一段零散经历；
2. 只润色现有简历中的一到三条经历；
3. 在内容确认后，生成可打印的单栏 A4 HTML 简历。

默认交付“专业版”表达；同一组已确认事实还可生成稳妥版与高竞争力版供用户比较。Skill 不会虚构实验、升级责任边界，或把 JD 要求写成个人经历。

### 文件职责

| 文件或目录 | 面向谁 | 用途 |
| --- | --- | --- |
| 仓库根目录 `README.md` | GitHub 访客 | 项目概览，以及网页和 Skill 两个入口的选择 |
| 本文件 | 安装 Skill 的用户 | 安装、调用方式、模型与隐私边界 |
| `medical-resume-skill/SKILL.md` | Codex / Claude 等宿主模型 | 主执行流程与不可突破的事实边界 |
| `medical-resume-skill/references/` | 宿主模型按需读取 | 医学能力分类、岗位表达、提示词、HTML 交付与联网规则 |
| `medical-resume-skill/assets/` | 最终交付文件 | 可打印的 A4 HTML 模板 |

安装时请复制整个 `medical-resume-skill` 文件夹，而不是只复制 `SKILL.md`。这样模型才能在需要时读到相应参考资料和模板。

### Windows 一键安装

在仓库根目录打开 PowerShell，执行：

```powershell
.\skill-lite\install-skill.ps1
```

脚本会把 Skill 安装到 `~/.codex/skills/medical-resume-skill`。它不会上传简历内容、照片或密钥。安装后请新开一个 Codex 对话，让 Skill 列表重新加载。

### 手动安装与第一次调用

将 `skill-lite/medical-resume-skill` 整个文件夹复制到：

```text
~/.codex/skills/medical-resume-skill
```

新开对话后，可以这样开始：

```text
请用 medical-resume-skill 帮我整理下面这段真实经历，目标是医学事务 / MSL。
先生成事实卡，只问最关键的缺失信息；不要补充我没有确认的责任、方法、数字或成果。
```

已有完整简历时：

```text
请用 medical-resume-skill 只润色我下面第 2、4 条科研经历；目标是临床研究与医院科研。
保留其他内容，不要新增未确认事实。先展示事实卡和待确认问题。
```

### 模型、联网与交付

Skill 不包含 API Key，也不绑定某一家模型。它使用 Codex、Claude 或兼容工作流中已经配置的模型；没有模型时仍可按事实卡和审校规则工作，但不应承诺自动生成高质量润色。

默认只使用用户在对话或所提供文件中确认的材料。用户可以提供 JD、岗位链接、论文 DOI，或明确允许联网搜索，以启用 JD / 公开证据辅助。公开信息只用于理解岗位语言、核对引用或发现能力缺口，不能成为个人经历的证据。

用户确认内容并明确要求导出后，Skill 在本机生成 `resume-output/`，其中包含可打印的 `resume.html`、结构化数据、证据摘要、改写对照与导出说明。头像默认不显示；用户主动提供本地图片时，才会在 HTML 简历右上角放置本地头像框。复杂 PDF、双栏 Word 或扫描件的文本提取仍需人工核对。

### 与网页版本的关系

网页版本适合可视化地输入、确认和预览；Skill Lite 适合在对话中深入梳理材料、比较多种表达并直接交付本机 HTML。两者共用“事实优先”的原则，但可以独立使用。

## English

`Medical Resume Skill Lite` is a workflow for host models such as Codex and Claude Code. It does not start a web app or a separate API. The host model uses the bundled fact-confirmation flow, medical capability taxonomy, and writing rules to turn real medical experience into a local HTML resume.

Install the entire `medical-resume-skill` folder, not only `SKILL.md`, so the model can access its references and HTML template. On Windows, run:

```powershell
.\skill-lite\install-skill.ps1
```

Start a new Codex conversation, then ask it to use `medical-resume-skill` with a real experience and a target direction. The Skill supports building a single experience, polishing one to three existing entries, and delivering an accepted full resume as printable A4 HTML. It uses only confirmed facts by default and must not invent work, upgrade responsibility, or turn a job requirement into a personal achievement.

The Skill uses the model already configured in the host workflow and contains no API key. JD/public-evidence assistance is opt-in: a user must supply a JD, URL, DOI, or explicit browsing permission. Public information may improve role-language alignment, but never becomes evidence of a user's own experience. The generated `resume-output/` stays local; an optional profile image is used only when the user explicitly supplies one.
