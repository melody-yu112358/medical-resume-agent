# Medical Career Skill Ecosystem Catalog

这是 `Medical Resume Skill Lite` 的扩展生态与竞品清单。它服务于产品研究和工具发现，不是安装源、质量排名、安全审计或合作伙伴名录。

最后核对：2026-08-28。每项仅根据其公开主页 / README 记录；项目的维护状态、许可证、运行时兼容性和实际效果均可能变化，使用前请回到原始仓库确认。

## 阅读方式

- **直接可比**：简历事实整理、JD 定制、内容改写或 HTML / PDF / DOCX 交付；用于比较产品工作流。
- **中文求职工作流**：面向中文求职用户的材料、经历或求职流程；用于比较中文表达与多 Skill 编排。
- **求职 Agent**：将职位发现、匹配、投递、跟进、面试等串成流程；不是单纯简历 Skill。
- **医学 / 科研相邻能力**：帮助理解医学能力、科研经历或医学工作流；不应被表述为医学简历的直接替代品。
- **生态发现与规范**：用于发现更多公开 Skill 或学习目录维护方法；不等于逐项背书。

## 目录概览

| 分类 | 项目数 | 适合比较的维度 |
| --- | ---: | --- |
| 直接可比：简历 Skill 与交付 | 11 | 事实源、JD 定制、ATS、结构化数据、HTML / PDF / DOCX 输出 |
| 成熟中文求职工作流 | 5 | 中文表达、经历梳理、跨 Skill 交接与本土化体验 |
| 求职 Agent 与职业档案 | 12 | 主档案、职位发现、匹配、申请、面试与反馈循环 |
| 医学 / 科研相邻能力 | 9 | 医学知识分类、科研/论文流程、证据与专业边界 |
| 生态发现与规范 | 5 | 目录框架、跨平台安装、持续收录与维护规则 |

## 1. 直接可比：简历 Skill 与文件交付

| 项目 | 公开定位摘要 | 可比较的产品问题 | 来源 |
| --- | --- | --- | --- |
| Medical Resume Skill Lite | 本项目的事实确认、医学能力解释、方向化表达与本地 HTML 交付工作流。 | 医学专业性、Claim Gate、用户确认权。 | [自研入口](../../../skill-lite/README.md) |
| resume-tailor | 基于主事实档案和职位描述生成 ATS 简历 / 求职信，并由第二模型复核。 | 事实溯源、JD 定制、独立复核。 | [nuin/resume-tailor](https://github.com/nuin/resume-tailor) |
| claude-resume | 用结构化经历源生成多岗位 LaTeX 简历。 | 单一事实源、多版本产物。 | [deusyu/claude-resume](https://github.com/deusyu/claude-resume) |
| html-resume | 将既有简历或职业笔记转为可编辑 HTML 与验证过的 A4 PDF。 | HTML 编辑、版式与输出校验。 | [Gratia2533/html-resume](https://github.com/Gratia2533/html-resume) |
| cc-resume-skills | 使用 JSON、HTML 与 PDF 的 Claude Code 简历生成流程。 | 结构化中间数据、渲染链路。 | [samuncleorange/cc-resume-skills](https://github.com/samuncleorange/cc-resume-skills) |
| claude-resume-kit | 多 Skill 的 LaTeX 简历定制框架，含生成后检查。 | JD 定制、表达规则、输出质检。 | [ARPeeketi/claude-resume-kit](https://github.com/ARPeeketi/claude-resume-kit) |
| resume-builder | 面向 Codex / OpenAI Agent 的简历构建 Skill，维护个人资料、风格和反馈文件。 | Codex 适配、持续个人档案、风格配置。 | [salehabbaas/resume-builder](https://github.com/salehabbaas/resume-builder) |
| job-search-Claude-skills | 从主简历和 JD 输出 ATS 导向 PDF、Word、Markdown 的技能集合。 | 一源多格式、ATS 关键词与缺口提示。 | [doughavlik/job-search-Claude-skills](https://github.com/doughavlik/job-search-Claude-skills) |
| resume-builder-cn | 中文优先、证据驱动的简历 Agent Skill，含岗位情报和可追溯匹配。 | 中文简历、证据链与岗位匹配。 | [LittleDrunkWang/resume-builder-cn](https://github.com/LittleDrunkWang/resume-builder-cn) |
| claude-resume-builder | 针对 JD 做 ATS 优化与专业改写的 Claude Code Skill。 | ATS 定制、表达优化。 | [gargraman/claude-resume-builder](https://github.com/gargraman/claude-resume-builder) |
| Resume-Builder | 用共享控制流支持 Codex 与 Claude Code 的简历生成项目。 | 多运行时流程与协作控制。 | [jananthan30/Resume-Builder](https://github.com/jananthan30/Resume-Builder) |

## 2. 成熟中文求职工作流

| 项目 | 公开定位摘要 | 可比较的产品问题 | 来源 |
| --- | --- | --- | --- |
| ASu-skills | 中文求职工作流插件，涵盖经历酥化、简历制作、同款复刻、Offer 等入口。 | 多入口设计、中文求职体验、主张—证据账本。 | [Hisn00w/ASu-skills](https://github.com/Hisn00w/ASu-skills) |
| resume_skill | 面向 Agent Skills 运行时的中文简历与求职辅助工具集合。 | 中文工具入口与安装边界。 | [dominiciyue/resume_skill](https://github.com/dominciyue/resume_skill) |
| resume-skills | 将简历任务拆分为多个可安装 Skill 的集合。 | Skill 粒度、触发边界。 | [cabbage2000-lab/resume-skills](https://github.com/cabbage2000-lab/resume-skills) |
| agent-skills | 面向 Claude.ai、Claude Code、ChatGPT 与 Codex 的跨 Agent Skills 集合，其中包含简历相关工作流。 | 跨平台打包、通用简历模块。 | [maaarcooo/agent-skills](https://github.com/maaarcooo/agent-skills) |
| resume-agent | 交互式 AI 简历与作品集 Agent，可分析简历文本或 PDF 并按角色生成摘要。 | 网页 Agent、简历解析和角色摘要。 | [user23052036/resume-agent](https://github.com/user23052036/resume-agent) |

## 3. 求职 Agent 与职业档案

| 项目 | 公开定位摘要 | 可比较的产品问题 | 来源 |
| --- | --- | --- | --- |
| resume-agent-skills | 先建立深度职业档案，再为每个岗位定制 ATS 简历。 | 长期职业档案、反复定制、事实边界。 | [vignzpie/resume-agent-skills](https://github.com/vignzpie/resume-agent-skills) |
| next-role | 多阶段职业 Agent，包含职位调研、简历定制与面试准备。 | 多 Agent 分工、阶段交接、可编辑产物。 | [tam159/next-role](https://github.com/tam159/next-role) |
| career-agent | 从简历建立职业档案、发现职位、匹配并输出定制简历的产品化 Agent。 | 档案、职位搜索、匹配评分。 | [lucasrucu/career-agent](https://github.com/lucasrucu/career-agent) |
| job-search-skills | 独立的职位分析、职位爬取、申请表填写和内推路径发现 Skills。 | 完整求职漏斗、浏览器与个人数据边界。 | [sameergdogg/job-search-skills](https://github.com/sameergdogg/job-search-skills) |
| job-scout | 个性化职位搜索、匹配评分与 ATS 简历定制的 Claude Code Skill。 | 职位来源、匹配评分、简历联动。 | [gregorymm/job-scout](https://github.com/gregorymm/job-scout) |
| job-hunt-skills | 覆盖简历、求职信、公司研究、面试、LinkedIn 与证明材料的插件。 | 长周期求职、事实回写。 | [Remotivated/job-hunt-skills](https://github.com/Remotivated/job-hunt-skills) |
| claude-job-search | 在终端搜索职位、按个人资料评分、定制 CV 并跟踪投递的 Agent。 | 终端式工作台、职位跟踪。 | [kevinpz/claude-job-search](https://github.com/kevinpz/claude-job-search) |
| jobclaw-skills | 覆盖职位搜索、匹配评分、定制简历、招聘沟通、面试和谈判的 Skills。 | 一次建档、多 Skill 复用。 | [jain777/jobclaw-skills](https://github.com/jain777/jobclaw-skills) |
| ai-job-search | 以 `/setup`、`/search`、`/apply` 等命令组成的求职助手。 | 命令式流程与审稿 Agent。 | [suraj-davariya/ai-job-search](https://github.com/suraj-davariya/ai-job-search) |
| proficiently-claude-skills | 自动化部分求职事务的 Claude Code Skills，含简历定制。 | 职位、申请与浏览器自动化边界。 | [proficientlyjobs/proficiently-claude-skills](https://github.com/proficientlyjobs/proficiently-claude-skills) |
| open-career-skills | 面向求职的 Claude Code 工作区，使用起草—审阅流程审计主张。 | 主张审阅、工作区式交付。 | [squerne/open-career-skills](https://github.com/squerne/open-career-skills) |
| career-ops | 个人求职命令中心，覆盖职位评估、简历定制和面试准备。 | 高自动化求职闭环。 | [santifer/career-ops](https://github.com/santifer/career-ops) |

## 4. 医学 / 科研相邻能力

| 项目 | 公开定位摘要 | 可比较的产品问题 | 来源 |
| --- | --- | --- | --- |
| MedSci Skills | 覆盖文献检索、报告规范与引文检查、统计、图表与投稿的医学研究 Skills。 | 医学知识资产、科研流程、证据边界。 | [Aperivue/medsci-skills](https://github.com/Aperivue/medsci-skills) |
| medical-research-skills | 大规模医学研究 Agent Skills 库，覆盖生物医学数据分析与论文工作流。 | 医学 Skill 拆分、目录组织。 | [aipoch/medical-research-skills](https://github.com/aipoch/medical-research-skills) |
| medical-research-thesis-supervisor | 面向医学论文选题、证据综合、写作与审稿式检查的 Claude Skill。 | 不虚构引用、科研写作审校。 | [mohamedhadyashry/medical-research-thesis-supervisor](https://github.com/mohamedhadyashry/medical-research-thesis-supervisor) |
| bioresearch-agent | 通过框架与 CLI 执行生物医学研究工作流的可复用 Agent Skills。 | Skill 与执行框架分层。 | [Alim430/bioresearch-agent](https://github.com/Alim430/bioresearch-agent) |
| scientific-agent-skills | 覆盖研究问题、文献、实验设计、R、统计与生命科学分析的可移植 Skills。 | 科研能力分类与跨运行时格式。 | [yigityildiz0/scientific-agent-skills](https://github.com/yigityildiz0/scientific-agent-skills) |
| Hash Medical Research Agent Skills | 针对医学文献评估、PRISMA 检索、证据汇总与 RAG 防护的 Agent Skills。 | 证据评价、研究安全边界。 | [Hash-7777/Hash-Medical-Reasearch-Agent-Skills](https://github.com/Hash-7777/Hash-Medical-Reasearch-Agent-Skills) |
| rh-skills | 为医疗信息学工作流生成可计算、确定性规则的工具集。 | 临床信息学与可计算产物。 | [reason-healthcare/rh-skills](https://github.com/reason-healthcare/rh-skills) |
| clinical-agent-skills | 可复用的临床与医疗 AI Agent Skills 集合。 | 临床场景的模块化能力。 | [elisaterumi-ai/clinical-agent-skills](https://github.com/elisaterumi-ai/clinical-agent-skills) |
| medical-research-skills-codex | 将学术研究 Skills 按 Codex 可用方式打包的项目。 | 学术 Skill 的运行时适配。 | [Imbad0202/academic-research-skills-codex](https://github.com/Imbad0202/academic-research-skills-codex) |

## 5. 生态发现与规范

| 项目 | 公开定位摘要 | 为什么收录 | 来源 |
| --- | --- | --- | --- |
| legal-skills | 法律领域的 Skills 集合，按场景维护自研 Skill、更新记录、安装入口和归档说明。 | 本目录的信息架构参考：自研入口 + 场景分类 + 更新记录 + 边界。 | [cat-xierluo/legal-skills](https://github.com/cat-xierluo/legal-skills) |
| awesome-medical-ai-skills | 医疗 AI Agent Skills、MCP 与工具的公开索引，提供分类、维护状态和质量说明。 | 医学相邻生态发现与维护字段参考。 | [JuneYaooo/awesome-medical-ai-skills](https://github.com/JuneYaooo/awesome-medical-ai-skills) |
| awesome-bio-agent-skills | 生物医学研究 Agent Skills 的公开集合。 | 发现医学科研相邻能力。 | [BioTender-max/awesome-bio-agent-skills](https://github.com/BioTender-max/awesome-bio-agent-skills) |
| awesome-academic-skills | 学术 Agent Skills 的分类清单。 | 发现研究、文档与论文类 Skill。 | [O0000-code/awesome-academic-skills](https://github.com/O0000-code/awesome-academic-skills) |
| awesome-claude-skills | 社区维护的 Claude Code Skills 收集库。 | 发现近期 Skill 生态与安装方式。 | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) |

## 收录与表述边界

1. 条目是公开项目的**索引**，不是安装包、镜像、复刻或安全认证；始终链接回原始来源。
2. 不复制外部 `SKILL.md`、脚本、模板、品牌视觉或 README 内容；只写必要的公开定位摘要。
3. 目录中的“直接可比”只说明可比较的工作流，**不代表功能相同、竞争关系、合作、推荐或质量判断**。
4. 医学 / 临床相邻项目不应被用于医疗决策，也不因收录而取得医学简历专业性背书。
5. 涉及简历、求职或医疗信息时，使用者应自行检查数据上传、账号授权、浏览器自动化、许可证与隐私条款。
6. 新增条目必须补充原始链接、分类、公开定位摘要与“可比较的产品问题”；无法验证来源的条目不收录。
7. 条目失效、改名或长期无法确认时，移动到“待复核”而非继续作为可用工具展示，并更新顶部日期。
