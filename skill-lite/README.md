# Medical Resume Skill Lite

[中文说明](#中文说明) | [English](#english)

## 中文说明

这是给 Codex 或 Claude 用户的轻量工作流包，不要求启动本仓库的网页。它把“医学经历如何被准确地翻译成不同方向看得懂的能力证明”整理成一套可复用的对话流程。

它有三种使用方式：从零整理一段零散经历；选中已有简历的一到三条做局部润色；在内容确认后生成可打印的单栏 HTML 简历。它不应用于虚构实验、升级个人责任，或把岗位要求写成个人经历。

Skill 会先区分研究设计和方法、数据工具、临床研究执行、实验技术、医学证据资源与个人产出。例如 R 是工具，MR/Meta 是方法，qPCR 是实验技术，PubMed 是检索资源。确认事实后，它再按目标方向调整表达重点，而不是把同一段经历机械改写四次。

其中的润色采用“两阶段提示词”：先生成经历事实卡并追问缺失信息，再基于用户确认的事实定向改写。这样既能保留高密度表达，也不会为了文案效果把协作经历写成主导成果。

### Windows 一键安装

在项目根目录打开 PowerShell 后执行：

```powershell
.\skill-lite\install-skill.ps1
```

脚本只会把本仓库中的 `medical-resume-skill` 复制到你自己的 Codex skills 目录，不会上传任何简历内容或密钥。安装后请新开一个 Codex 对话。

### 手动安装

将 `skill-lite/medical-resume-skill` 文件夹复制到你的 Codex skills 目录，随后新开一个 Codex 对话。常见目录为：

```text
~/.codex/skills/medical-resume-skill
```

然后可以直接说：

```text
请用 medical-resume-skill 帮我整理这段经历，目标是医学事务 / MSL。
```

已有完整简历时，也可以这样说：

```text
请用 medical-resume-skill 只润色我下面第 2、4 条科研经历；目标是临床研究与医院科研。不要重写其他内容，也不要补充未确认事实。
```

如果你使用 Claude，可将 `SKILL.md` 与 `references/` 内容作为项目指令/参考材料导入。

### 模型与文件交付

Skill 本身不包含 API Key，也不绑定某一家模型；它使用当前 Codex、Claude 或兼容工作流已配置的模型。没有模型时，仍可使用事实卡、能力分类和审校规则，但不应承诺自动生成高质量润色。

在用户确认内容并明确要求导出后，Skill 会生成本机 `resume-output/`：其中有可打印的 `resume.html`、结构化数据、证据摘要、改写对照和导出说明。普通 PDF/DOCX 的文本抽取能力取决于宿主工具；复杂表格、双栏或扫描件仍应在确认页人工校对。

### 联网与 JD 辅助

默认是“仅本地事实模式”：只使用用户在对话或所提供文件中确认的经历。用户也可以明确提供 JD、岗位链接、论文 DOI 或同意联网搜索，启用“JD / 公开证据辅助模式”。此模式只用于提炼岗位语言、核对公开引用和指出能力缺口；网页上的岗位要求不能自动变成用户做过的事情。

### 与网页版本的区别

Skill Lite 负责聊天式经历挖掘、保真表达与本机 HTML 交付；网页版本额外提供确定性 Claim Gate、审计账本、结构化 API 与可视化确认页面。重要投递材料建议再在网页中完成最终确认与审计。

## English

This is a lightweight workflow package for Codex or Claude users. It does not require the web app in this repository. It turns medical-experience translation into a reusable conversational workflow.

On Windows, run `./skill-lite/install-skill.ps1` from the repository root. It copies the bundled Skill into your local Codex skills directory without uploading resume text or keys. Alternatively, copy `skill-lite/medical-resume-skill` into your local Codex skills directory, then begin a new Codex conversation and ask it to use `medical-resume-skill` for a real medical experience and target direction. The Skill guides fact extraction, confirmation, and evidence-bound wording. It must not invent work, upgrade responsibility, or turn a job requirement into a personal achievement.

The Skill supports three routes: build an experience from fragments, polish one to three selected entries in an existing resume, or generate a printable single-column HTML resume after the user accepts the content. It separates research methods, tools, laboratory techniques, evidence resources, compliance work, and personal deliverables before tailoring the wording to a target direction.

The Skill does not include an API key or require a specific model. It uses the model configured in the host workflow. Without a model, the fact-card and review workflow still apply, but it should not promise automatic high-quality rewriting.

By default, the Skill runs in a local-facts-only mode and uses only the user's conversation or supplied files. The user may opt into JD/public-evidence assistance by providing a JD, URL, DOI, or explicit browsing permission. That mode may improve role-language alignment and verify public references, but it must never convert a job requirement or a web result into a personal achievement.

The web app additionally provides deterministic Claim Gate checks, an audit ledger, structured APIs, and a visual confirmation page. Use the web app for important application materials that need the complete audit path.
