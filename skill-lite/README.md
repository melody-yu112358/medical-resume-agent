# Medical Resume Skill Lite

[中文说明](#中文说明) | [English](#english)

## 中文说明

这是给 Codex 或 Claude 用户的轻量工作流包，不要求启动本仓库的网页。

它适用于“我有一段医学经历，想先把事实说清楚，再按目标方向得到一组可信简历要点”的场景。它不应用于虚构实验、升级个人责任，或把岗位要求写成个人经历。

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

如果你使用 Claude，可将 `SKILL.md` 与 `references/` 内容作为项目指令/参考材料导入。

### 与网页版本的区别

Skill Lite 负责聊天式问诊和保真表达；网页版本额外提供确定性 Claim Gate、审计账本、结构化 API 与可视化确认页面。重要投递材料建议再在网页中完成确认与审计。

## English

This is a lightweight workflow package for Codex or Claude users. It does not require the web app in this repository.

On Windows, run `./skill-lite/install-skill.ps1` from the repository root. It copies the bundled Skill into your local Codex skills directory without uploading resume text or keys. Alternatively, copy `skill-lite/medical-resume-skill` into your local Codex skills directory, then begin a new Codex conversation and ask it to use `medical-resume-skill` for a real medical experience and target direction. The Skill guides fact extraction, confirmation, and evidence-bound wording. It must not invent work, upgrade responsibility, or turn a job requirement into a personal achievement.

The web app additionally provides deterministic Claim Gate checks, an audit ledger, structured APIs, and a visual confirmation page. Use the web app for important application materials that need the complete audit path.
