const $ = (selector) => document.querySelector(selector);
let result = null;
let structureResult = null;
let resumeDocument = null;
let selectedTemplate = "clinical";
let selectedPurpose = "campus";
let selectedTranslationTarget = "clinical_research";
const VERSION_STORAGE_KEY = "unbounded.resume-versions.v1";
const REWRITE_AUDIT_STORAGE_KEY = "unbounded.resume-rewrite-audit.v1";
const EXPERIENCE_COMPILER_HANDOFF_STORAGE_KEY = "unbounded.experience-compiler-handoff.v1";
const CAPABILITY_PROFICIENCY_LABELS = { aware: "了解方法与基本概念", supervised: "可在指导下完成", independent: "可独立完成", advanced: "可设计、优化或指导他人" };
const MEDICAL_CAPABILITY_CATALOG = [
  { name: "孟德尔随机化", category: "research_method", patterns: [/孟德尔随机化/i, /mendelian\s+randomi[sz]ation/i, /\bIVW\b/, /MR[-\s]?Egger/i] },
  { name: "Meta 分析", category: "research_method", patterns: [/meta[ -]?analysis/i, /meta\s*分析/i, /系统综述/i, /systematic review/i] },
  { name: "GWAS 数据分析", category: "data_analysis", patterns: [/\bGWAS\b/i, /全基因组关联/i, /genome-wide association/i] },
  { name: "R 数据分析", category: "data_analysis", patterns: [/\bR语言\b/i, /\bR\s*(?:studio|语言|脚本|分析)/i, /\bR\b/, /tidyverse/i] },
  { name: "Python 数据分析", category: "data_analysis", patterns: [/\bPython\b/i, /pandas/i, /scikit-learn/i] },
  { name: "细胞培养", category: "wet_lab", patterns: [/细胞培养/i, /cell culture/i] },
  { name: "qPCR", category: "wet_lab", patterns: [/\bqPCR\b/i, /实时荧光定量/i] },
  { name: "Western blot", category: "wet_lab", patterns: [/western blot/i, /蛋白印迹/i] },
  { name: "流式细胞术", category: "wet_lab", patterns: [/流式细胞/i, /flow cytometry/i] },
  { name: "临床队列研究", category: "clinical_research", patterns: [/队列研究/i, /cohort study/i, /随访/i] },
  { name: "随机对照试验", category: "clinical_research", patterns: [/\bRCT\b/i, /随机对照/i, /randomized controlled/i] },
  { name: "医学文献检索", category: "medical_information", patterns: [/PubMed/i, /Embase/i, /Cochrane/i, /文献检索/i] },
];

const EXAMPLE = {
  role: "医学联络官（MSL）",
  jd: `医学联络官（MSL）\n核心职责：负责疾病领域医学信息沟通，检索并解读临床研究证据；支持学术活动，与内部跨职能团队协作。\n任职要求：临床医学、药学或生命科学相关硕士学历；具备医学文献检索与解读能力；具备清晰的沟通表达和项目协作能力。`,
  resume: `教育背景\n2021.09-2024.06  某医学院  临床医学硕士\n\n科研 / 实践经历\n2022.03-2024.03  某附属医院课题组  研究生\n• 使用 PubMed 检索并筛选 120 篇相关临床研究，整理证据表并完成 3 次组会汇报\n• 协助维护研究数据表，与 4 名团队成员核对病例信息和随访记录\n• 面向本科生完成 2 次疾病知识分享，并根据现场问题修改讲解材料\n\n技能与证书\n• PubMed、Excel、SPSS\n• 大学英语六级`,
};

const SECTION_HEADINGS = ["个人概述", "核心能力", "教育背景", "相关经历", "实践与项目经历", "研究 / 学术成果", "技能与证书", "与目标岗位相关的已确认表述", "科研 / 学术经历", "临床 / 实践经历", "竞赛与能力", "科研 / 实践经历", "补充材料", "研究方向与科研经历", "论文 / 会议 / 成果", "方法与技能", "校园 / 科研经历", "工作与项目经历", "教育与证书"];
const PURPOSES = {
  recommendation: { label: "保研 / 夏令营", focus: "教育表现、科研潜力、课题经历与学术兴趣", sections: ["教育背景", "科研 / 学术经历", "临床 / 实践经历", "竞赛与能力"] },
  masters: { label: "考研复试", focus: "教育基础、科研训练、临床实践与复试可讲述经历", sections: ["教育背景", "科研 / 实践经历", "竞赛与能力", "补充材料"] },
  phd: { label: "考博", focus: "研究方向、论文成果、方法能力与长期研究计划", sections: ["教育背景", "研究方向与科研经历", "论文 / 会议 / 成果", "方法与技能"] },
  campus: { label: "校招", focus: "实习、项目、校园经历与可迁移能力", sections: ["教育背景", "实践与项目经历", "校园 / 科研经历", "技能与证书"] },
  experienced: { label: "社招", focus: "岗位职责、可核实成果、行业工具与角色匹配", sections: ["个人概述", "核心能力", "工作与项目经历", "教育与证书"] },
  general: { label: "通用简历", focus: "可迁移经历、基础能力与后续定制空间", sections: ["个人概述", "教育背景", "相关经历", "技能与证书"] },
};

function esc(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[character]));
}

function strengthLabel(strength) {
  return ({ strong: "强：有行动和结果线索", medium: "中：有行动，待补结果", weak: "弱：只有相关线索", none: "未找到证据" }[strength] || "待核实");
}

function categoryLabel(category) {
  return ({ hard_requirement: "硬性条件", bonus: "加分项", responsibility: "核心职责", skill_keyword: "技能关键词" }[category] || "岗位要求");
}

async function loadCareerHandoff() {
  const params = new URLSearchParams(location.search);
  const careerId = params.get("career_id");
  const jobId = params.get("job_id");
  const savedResume = sessionStorage.getItem("careerResumeEvidence");
  const selectedJob = sessionStorage.getItem("selectedJob");
  if (savedResume && !$("#resume").value) $("#resume").value = savedResume;
  if (jobId && selectedJob) {
    try {
      const job = JSON.parse(selectedJob);
      if (job.job_id === jobId) {
        $("#role").value = job.title;
        $("#jd").value = [job.description, "主要职责：", ...job.responsibilities, "任职要求：", ...job.requirements].join("\n");
        $("#error").textContent = `已载入“${job.company} · ${job.title}”的公开岗位信息；提交前请再次查看原招聘页。`;
        return;
      }
    } catch (_) { sessionStorage.removeItem("selectedJob"); }
  }
  if (!careerId) return;
  try {
    const response = await fetch(`/api/career-targets/${encodeURIComponent(careerId)}`);
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "目标岗位载入失败");
    $("#role").value = body.career_name;
    $("#jd").value = body.generated_jd_text;
    $("#error").textContent = `已从有来源的职业卡载入“${body.career_name}”目标岗位画像；职业卡状态：${body.review_status}。`;
  } catch (error) { $("#error").textContent = error.message; }
}

function loadExperienceCompilerHandoff() {
  const params = new URLSearchParams(location.search);
  if (params.get("from") !== "experience-compiler") return;
  let handoff;
  try {
    handoff = JSON.parse(sessionStorage.getItem(EXPERIENCE_COMPILER_HANDOFF_STORAGE_KEY) || "");
  } catch (_) {
    $("#error").textContent = "未能读取刚才生成的经历要点；请返回经历编译器后重新打开预览。";
    return;
  }
  if (!handoff?.bullets?.length) {
    $("#error").textContent = "没有可载入的经历要点；请先在经历编译器中完成一段经历。";
    return;
  }
  const capabilities = (handoff.capabilities || []).map((item) => `• ${item}`).join("\n") || "• [请补充本人实际掌握的方法、工具或实验技术]";
  const bullets = handoff.bullets.map((item) => `• ${item}`).join("\n");
  const resumeText = `个人概述\n医学背景候选人，申请${handoff.target_role || "医学相关目标方向"}。以下内容来自本人确认的经历，请在投递前补全教育背景、联系方式与具体经历时间。\n\n核心能力\n${capabilities}\n\n科研 / 学术经历\n已确认医学经历\n${bullets}\n\n技能与证书\n• [请仅保留本人实际使用过的工具、培训或语言能力]`;
  $("#role").value = handoff.target_role || "医学相关目标方向";
  $("#resume").value = resumeText;
  $("#document").value = resumeText;
  $("#documentWrap").classList.remove("hidden");
  $("#error").textContent = "已载入经历编译器生成的要点。点击预览工具栏中的“编辑文字”可修改材料，再点击“刷新预览”。";
  renderPrintableResume();
}

function loadExample() {
  $("#name").value = "示例候选人";
  $("#contact").value = "example@weijie.test · 上海";
  $("#role").value = EXAMPLE.role;
  $("#jd").value = EXAMPLE.jd;
  $("#resume").value = EXAMPLE.resume;
  resetStructureReview();
  $("#error").textContent = "已载入脱敏合成示例。请阅读并勾选隐私提示，然后开始诊断。";
  window.scrollTo({ top: $("#purposePicker").offsetTop, behavior: "smooth" });
}

async function uploadResume(file) {
  const status = $("#uploadStatus");
  if (!file) return;
  status.textContent = `正在读取 ${file.name}…`;
  const body = new FormData();
  body.append("file", file);
  try {
    const response = await fetch("/api/resume/upload", { method: "POST", body });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "文件读取失败");
    $("#resume").value = payload.resume_text;
    resetStructureReview();
    status.textContent = `已读取 ${file.name}，请检查文本是否完整。`;
  } catch (error) {
    status.textContent = error.message;
    $("#resumeFile").value = "";
  }
}

function resetStructureReview() {
  structureResult = null;
  resumeDocument = null;
  $("#structureReview").classList.add("hidden");
  $("#documentModel").classList.add("hidden");
  $("#structureSections").innerHTML = "";
  $("#structureUnclassified").innerHTML = "";
}

const STRUCTURE_LABELS = {
  education: "教育背景", clinical_experience: "临床 / 轮转经历", professional_experience: "工作 / 实习经历",
  research_experience: "科研经历", projects: "项目经历", publications: "论文 / 学术成果",
  awards: "荣誉 / 奖项", skills: "技能与证书", languages: "语言能力",
};

async function identifyResumeStructure() {
  const resume = $("#resume").value.trim();
  const error = $("#error");
  error.textContent = "";
  if (!$("#consent").checked) { error.textContent = "请先确认隐私提示，再识别简历结构。"; return; }
  if (!resume) { error.textContent = "请先粘贴或上传原始简历。"; return; }
  const button = $("#structureResume");
  button.disabled = true;
  button.textContent = "正在识别栏目…";
  try {
    const response = await fetch("/api/resume-structures", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resume_text: resume }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "简历结构识别失败");
    structureResult = body;
    renderStructureReview();
  } catch (requestError) { error.textContent = requestError.message; }
  finally { button.disabled = false; button.textContent = "重新识别简历结构 →"; }
}

function renderStructureReview() {
  const sections = structureResult.sections || [];
  $("#structureSections").innerHTML = sections.length ? sections.map((section) => {
    const lines = section.lines.map((line, index) => {
      const evidenceId = section.evidence_ids[index];
      return `<label class="structure-line"><input class="structure-evidence" type="checkbox" value="${esc(evidenceId)}"><span>${esc(line)}</span></label>`;
    }).join("");
    return `<article class="structure-section"><h3>${esc(STRUCTURE_LABELS[section.section_key] || section.heading)}</h3>${lines || "<small>该栏目下未识别到可确认文本。</small>"}</article>`;
  }).join("") : "<div class=\"structure-unclassified\">未识别到标准栏目。请先补充教育背景、科研经历等标题，或仅使用原始简历编辑。</div>";
  const unknown = structureResult.unclassified_lines || [];
  $("#structureUnclassified").innerHTML = unknown.length ? `<div class="structure-unclassified"><b>未归类内容（不会自动进入成稿）</b><br>${unknown.map(esc).join("<br>")}</div>` : "";
  $("#structureReview").classList.remove("hidden");
  updateStructureStatus();
  $("#structureReview").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function selectedStructuredEvidenceIds() {
  return new Set([...document.querySelectorAll(".structure-evidence:checked")].map((item) => item.value));
}

function updateStructureStatus() {
  const selected = selectedStructuredEvidenceIds().size;
  $("#structureStatus").textContent = selected ? `已确认 ${selected} 条内容；生成定制稿时只会使用这些内容。` : "尚未选择任何内容。";
}

function confirmedStructuredLines(keys) {
  if (!structureResult) return [];
  const selected = selectedStructuredEvidenceIds();
  return (structureResult.sections || [])
    .filter((section) => keys.includes(section.section_key))
    .flatMap((section) => section.lines.filter((_, index) => selected.has(section.evidence_ids[index])));
}

function sectionKeysForHeading(heading) {
  let keys = ["professional_experience", "projects", "clinical_experience"];
  if (heading.includes("教育")) keys = ["education"];
  else if (heading.includes("临床")) keys = ["clinical_experience", "professional_experience"];
  else if (heading.includes("实践") || heading.includes("项目")) keys = ["professional_experience", "projects", "clinical_experience"];
  else if (heading.includes("校园")) keys = ["research_experience", "awards"];
  else if (heading.includes("科研") || heading.includes("研究")) keys = ["research_experience", "projects"];
  else if (heading.includes("论文") || heading.includes("成果")) keys = ["publications", "awards"];
  else if (heading.includes("技能") || heading.includes("能力") || heading.includes("证书")) keys = ["skills", "languages"];
  return keys;
}

function structuredContentForHeading(heading) {
  const keys = sectionKeysForHeading(heading);
  const lines = confirmedStructuredLines(keys);
  return lines.length ? lines.map((line) => `• ${line}`).join("\n") : "• [请在上方结构确认中勾选真实内容，或手动补充]";
}

const MODEL_SECTIONS = {
  education: { label: "教育背景", hint: "填写学校、学位、专业和时间；下方原文仅作证据参考。", fields: [["institution", "学校", "例如：某医学院"], ["degree", "学位", "例如：医学硕士"], ["major", "专业", "例如：临床医学"], ["period", "起止时间", "例如：2021.09–2024.06"]] },
  clinical_experience: { label: "临床 / 轮转经历", hint: "填写医院、科室/领域、角色和时间。", fields: [["organization", "医院 / 单位", "例如：某附属医院"], ["department", "科室 / 领域", "例如：心内科"], ["title", "角色", "例如：实习生 / 轮转医生"], ["period", "起止时间", "例如：2024.01–2024.03"]] },
  professional_experience: { label: "工作 / 实习经历", hint: "填写单位、角色和时间。", fields: [["organization", "单位", "例如：某企业"], ["title", "角色", "例如：医学实习生"], ["period", "起止时间", "例如：2024.01–2024.06"]] },
  research_experience: { label: "科研经历", hint: "填写课题组/机构、研究方向和本人角色。", fields: [["organization", "课题组 / 机构", "例如：某附属医院课题组"], ["department", "研究方向", "例如：临床研究"], ["title", "本人角色", "例如：研究生"], ["period", "起止时间", "例如：2022.03–2024.03"]] },
  projects: { label: "项目经历", hint: "填写项目所属单位、项目名称和角色。", fields: [["organization", "所属单位", "例如：某医学院"], ["department", "项目名称", "例如：医学科普项目"], ["title", "本人角色", "例如：负责人"], ["period", "起止时间", "例如：2024.01–至今"]] },
  publications: { label: "论文 / 学术成果", hint: "填写题目、期刊/会议、作者位次和状态。", fields: [["title", "题目", "论文或成果题目"], ["venue", "期刊 / 会议", "可留空"], ["author_position", "作者位次", "例如：共同一作"], ["status", "状态", "已发表 / 已接收 / 审稿中"]] },
  awards: { label: "荣誉 / 奖项", hint: "填写奖项名称、授予单位和年份。", fields: [["name", "奖项名称", "例如：国家奖学金"], ["issuer", "授予单位", "例如：教育部"], ["year", "年份", "例如：2025"]] },
  skills: { label: "技能与证书", hint: "填写真实使用过的技能或证书；每行一项。", fields: [["items", "技能 / 证书", "例如：PubMed｜医学信息"]] },
  languages: { label: "语言能力", hint: "填写语言及可核实的成绩或级别。", fields: [["items", "语言能力", "例如：英语｜CET-6 580"]] },
};

function selectedSection(section) {
  const selected = selectedStructuredEvidenceIds();
  const lines = section.lines.filter((_, index) => selected.has(section.evidence_ids[index]));
  const ids = section.evidence_ids.filter((id) => selected.has(id));
  return { lines, ids };
}

function detectedMedicalCapabilities() {
  if (!resumeDocument?.evidence) return [];
  return MEDICAL_CAPABILITY_CATALOG.map((capability) => {
    const evidenceIds = resumeDocument.evidence
      .filter((item) => capability.patterns.some((pattern) => pattern.test(item.statement)))
      .map((item) => item.evidence_id);
    return evidenceIds.length ? { ...capability, evidence_ids: evidenceIds } : null;
  }).filter(Boolean);
}

function renderCapabilityProfile() {
  if (!resumeDocument) return;
  const candidates = detectedMedicalCapabilities();
  const selected = new Map((resumeDocument.capability_profile || []).map((item) => [item.name, item]));
  $("#capabilityCandidates").innerHTML = candidates.length ? candidates.map((item) => {
    const current = selected.get(item.name)?.proficiency || "";
    const sourceText = item.evidence_ids.map((id) => resumeDocument.evidence.find((evidence) => evidence.evidence_id === id)?.statement).filter(Boolean).join("；");
    return `<label class="capability-candidate"><span><b>${esc(item.name)}</b><small>原始证据：${esc(sourceText)}</small></span><select data-capability-name="${esc(item.name)}" data-capability-category="${esc(item.category)}" data-capability-evidence="${esc(item.evidence_ids.join(","))}"><option value="">不写入简历</option>${Object.entries(CAPABILITY_PROFICIENCY_LABELS).map(([value, label]) => `<option value="${value}" ${current === value ? "selected" : ""}>${label}</option>`).join("")}</select></label>`;
  }).join("") : "<p class=\"item\">暂未从已确认原文中识别到方法或实验技术。你可以补充包含具体方法、工具或实验名称的真实经历后重新保存。</p>";
  $("#capabilityProfileStatus").textContent = candidates.length ? "选择熟练度后，能力会写入正式结构化简历，并进入顶部核心能力区。" : "";
  $("#capabilityProfile").classList.remove("hidden");
}

function updateCapabilityProfile() {
  if (!resumeDocument) return;
  resumeDocument.capability_profile = [...document.querySelectorAll("[data-capability-name]")].map((select) => ({
    name: select.dataset.capabilityName,
    category: select.dataset.capabilityCategory,
    proficiency: select.value,
    evidence_ids: select.dataset.capabilityEvidence.split(",").filter(Boolean),
  })).filter((item) => item.proficiency);
  localStorage.setItem("unbounded.resume-document-draft.v1", JSON.stringify(resumeDocument));
  const count = resumeDocument.capability_profile.length;
  $("#capabilityProfileStatus").textContent = count ? `已确认 ${count} 项医学能力；它们将显示在简历顶部。` : "尚未确认任何能力，候选项不会写入简历。";
}

function openDocumentEditor() {
  if (!structureResult || !selectedStructuredEvidenceIds().size) { $("#error").textContent = "请先勾选至少一条真实内容。"; return; }
  const cards = (structureResult.sections || []).map((section) => {
    const config = MODEL_SECTIONS[section.section_key];
    const selected = selectedSection(section);
    if (!config || !selected.lines.length) return "";
    const fields = config.fields.map(([name, label, placeholder]) => name === "items"
      ? `<label>${label}<textarea data-model-key="${section.section_key}" data-model-field="${name}" rows="3" placeholder="${placeholder}"></textarea></label>`
      : `<label>${label}<input data-model-key="${section.section_key}" data-model-field="${name}" placeholder="${placeholder}"></label>`).join("");
    return `<article class="model-card" data-model-card="${section.section_key}"><h3>${config.label}</h3><p>${config.hint}</p><div class="form-grid">${fields}</div><label>已确认原文（可编辑为本人确认的表述）<textarea data-model-key="${section.section_key}" data-model-field="bullets" rows="4">${esc(selected.lines.join("\n"))}</textarea></label><div class="model-source">证据：${selected.lines.map(esc).join("<br>")}</div></article>`;
  }).join("");
  $("#documentModelFields").innerHTML = cards || "<p class=\"error\">未找到可编辑的已确认栏目。</p>";
  $("#documentModel").classList.remove("hidden");
  $("#documentModel").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function modelValues(key) {
  const values = {};
  document.querySelectorAll(`[data-model-key="${key}"]`).forEach((input) => { values[input.dataset.modelField] = input.value.trim(); });
  return values;
}

function draftLinesForSection(key, section) {
  const values = section || {};
  const compact = (...items) => items.filter(Boolean).join("｜");
  const header = {
    education: compact(values.institution, values.degree, values.major, values.period),
    clinical_experience: compact(values.organization, values.department, values.title, values.period),
    professional_experience: compact(values.organization, values.title, values.period),
    research_experience: compact(values.organization, values.department, values.title, values.period),
    projects: compact(values.organization, values.department, values.title, values.period),
    publications: compact(values.title, values.venue, values.author_position, values.status),
    awards: compact(values.name, values.issuer, values.year),
    skills: values.items,
    languages: values.items,
  }[key];
  const bullets = (values.bullets || "").split("\n").map((line) => line.trim()).filter(Boolean);
  if ((key === "skills" || key === "languages") && values.items) return values.items.split("\n").map((line) => line.trim()).filter(Boolean);
  const headerSignals = Object.entries(values)
    .filter(([field, value]) => field !== "bullets" && field !== "period" && typeof value === "string" && value.trim())
    .map(([, value]) => value.trim());
  const detailBullets = bullets.filter((line) => headerSignals.filter((signal) => line.includes(signal)).length < 2);
  return [...(header ? [header] : []), ...detailBullets];
}

function draftContentForHeading(heading) {
  if (resumeDocument?.schema_version !== "resume-document-v1") return "";
  const lines = sectionKeysForHeading(heading).flatMap((key) => {
    const items = resumeDocument[key] || [];
    if (key === "education") return items.map((item) => [item.institution, item.degree, item.major, item.period?.start].filter(Boolean).join("｜"));
    if (["clinical_experience", "professional_experience", "research_experience", "projects"].includes(key)) return items.flatMap((item) => [
      [item.organization, item.department_or_field, item.title, item.period?.start].filter(Boolean).join("｜"),
      ...(item.bullets || []).map((bullet) => bullet.text),
    ]);
    if (key === "publications") return items.map((item) => [item.title, item.venue, item.author_position].filter(Boolean).join("｜"));
    if (key === "awards") return items.map((item) => [item.name, item.issuer, item.year].filter(Boolean).join("｜"));
    if (key === "skills") return items.map((item) => item.name);
    if (key === "languages") return items.map((item) => [item.language, item.level_or_score].filter(Boolean).join("｜"));
    return [];
  });
  return lines.length ? lines.map((line) => `• ${line.replace(/^[•●▪◦*\-\s]+/, "")}`).join("\n") : "";
}

function periodFromInput(value) {
  const text = value.trim();
  return { start: text || null, end: null, ongoing: /至今|present|current/i.test(text) };
}

function confirmedEvidence() {
  const selected = selectedStructuredEvidenceIds();
  return (structureResult.evidence || []).filter((item) => selected.has(item.evidence_id)).map((item) => ({
    evidence_id: item.evidence_id,
    statement: item.statement,
    source_document_id: "pasted-resume",
    source_locator: item.source_locator,
    status: "user_confirmed",
    confirmed_at: new Date().toISOString(),
  }));
}

function modelLines(value) {
  return (value || "").split("\n").map((line) => line.trim()).filter(Boolean);
}

function buildFormalResumeDocument() {
  const evidence = confirmedEvidence();
  const targetPurpose = { recommendation: "recommendation", masters: "graduate_retest", phd: "phd", campus: "hospital_campus", experienced: "experienced_hire", general: "general" }[selectedPurpose];
  const sections = {};
  Object.keys(MODEL_SECTIONS).forEach((key) => {
    const values = modelValues(key);
    const evidenceIds = (structureResult.sections || []).filter((item) => item.section_key === key).flatMap((item) => selectedSection(item).ids);
    if (!Object.keys(values).length || !evidenceIds.length) return;
    const bullets = modelLines(values.bullets).map((text) => ({ text, evidence_ids: evidenceIds }));
    if (key === "education" && values.institution) sections.education = [{
      item_id: `education-${Date.now()}`, institution: values.institution, degree: values.degree || null,
      major: values.major || null, period: periodFromInput(values.period || ""), ranking_or_gpa: null,
      highlights: modelLines(values.bullets), evidence_ids: evidenceIds,
    }];
    if (["clinical_experience", "professional_experience", "research_experience", "projects"].includes(key) && values.organization && values.title) {
      sections[key] = [{ item_id: `${key}-${Date.now()}`, organization: values.organization, title: values.title,
        department_or_field: values.department || null, period: periodFromInput(values.period || ""), bullets, evidence_ids: evidenceIds }];
    }
    if (key === "publications" && values.title) sections.publications = [{
      item_id: `publication-${Date.now()}`, title: values.title, venue: values.venue || null,
      status: ({ "已发表": "published", "已接收": "accepted", "审稿中": "under_review", "准备中": "in_preparation" }[values.status] || "unknown"),
      author_position: values.author_position || null, year: null, evidence_ids: evidenceIds,
    }];
    if (key === "awards" && values.name) sections.awards = [{
      item_id: `award-${Date.now()}`, name: values.name, issuer: values.issuer || null,
      year: /^\d{4}$/.test(values.year || "") ? Number(values.year) : null, evidence_ids: evidenceIds,
    }];
    if (key === "skills") sections.skills = modelLines(values.items).map((line) => {
      const [name, category] = line.split("｜").map((item) => item.trim());
      return { name, category: ["clinical", "research", "data", "medical_information", "communication", "certificate", "other"].includes(category) ? category : "other", level: null, evidence_ids: evidenceIds };
    }).filter((item) => item.name);
    if (key === "languages") sections.languages = modelLines(values.items).map((line) => {
      const [language, level] = line.split("｜").map((item) => item.trim());
      return { language, level_or_score: level || null, evidence_ids: evidenceIds };
    }).filter((item) => item.language);
  });
  return {
    schema_version: "resume-document-v1",
    resume_id: `resume-${Date.now()}`,
    source_documents: [{ document_id: "pasted-resume", source_type: "pasted_text", display_name: null, imported_at: new Date().toISOString() }],
    target: { purpose: targetPurpose, role: $("#role").value.trim() || null, organization: null, jd_reference: null },
    basics: { name: $("#name").value.trim() || null, phone: null, email: null, location: $("#contact").value.trim() || null, summary: $("#summary").value.trim() || null, evidence_ids: [] },
    evidence,
    capability_profile: [],
    review_events: [],
    ...sections,
  };
}

function saveDocumentModel() {
  if (!structureResult) return;
  resumeDocument = buildFormalResumeDocument();
  localStorage.setItem("unbounded.resume-document-draft.v1", JSON.stringify(resumeDocument));
  $("#documentModelStatus").textContent = `已保存正式 resume-document-v1：${resumeDocument.evidence.length} 条确认事实。预览将直接读取它，而不再解析成稿文本。`;
  renderCapabilityProfile();
}

function readBrowserList(key) {
  try { return JSON.parse(localStorage.getItem(key) || "[]"); }
  catch { return []; }
}

function writeBrowserList(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function recordRewriteDisposition(item, index, disposition) {
  const events = readBrowserList(REWRITE_AUDIT_STORAGE_KEY);
  events.unshift({
    event_type: "rewrite_disposition",
    suggestion_id: `rewrite-${index}`,
    disposition,
    recorded_at: new Date().toISOString(),
    requirement: item.requirement,
    source_evidence_present: Boolean(item.source_quote),
    rewrite_length: item.rewritten.length,
  });
  writeBrowserList(REWRITE_AUDIT_STORAGE_KEY, events);
}

function insertRewrite(item) {
  const editor = $("#document");
  if (!item || !editor) return;
  const start = editor.selectionStart;
  const end = editor.selectionEnd;
  editor.setRangeText(item.rewritten, start, end, "end");
  $("#documentWrap").classList.remove("hidden");
  editor.focus();
}

function formatSavedAt(value) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function renderVersionList() {
  const versions = readBrowserList(VERSION_STORAGE_KEY);
  const list = $("#versionList");
  if (!list) return;
  list.innerHTML = versions.length ? `<div class="version-list">${versions.slice(0, 5).map((version) => `<div class="version-item"><span>${esc(version.name)} · ${esc(formatSavedAt(version.saved_at))}</span><button class="load-version" data-version-id="${esc(version.version_id)}" type="button">载入</button></div>`).join("")}</div>` : "";
}

function saveResumeVersion() {
  const content = $("#document").value.trim();
  if (!content) { $("#versionStatus").textContent = "请先生成或填写最终简历，再保存版本。"; return; }
  const savedAt = new Date().toISOString();
  const name = $("#versionName").value.trim() || `${PURPOSES[selectedPurpose].label} · ${new Date(savedAt).toLocaleDateString("zh-CN")}`;
  const version = { version_id: `resume-version-${Date.now()}`, name, saved_at: savedAt, purpose: selectedPurpose, template: selectedTemplate, role: $("#role").value.trim() || null, content };
  const versions = readBrowserList(VERSION_STORAGE_KEY);
  versions.unshift(version);
  try {
    writeBrowserList(VERSION_STORAGE_KEY, versions);
    $("#versionStatus").textContent = `已保存“${name}”到当前浏览器。`;
    renderVersionList();
  } catch { $("#versionStatus").textContent = "浏览器存储空间不足，未能保存此版本。"; }
}

function loadResumeVersion(versionId) {
  const version = readBrowserList(VERSION_STORAGE_KEY).find((item) => item.version_id === versionId);
  if (!version) { $("#versionStatus").textContent = "未找到该本机版本。"; return; }
  const editor = $("#document");
  if (editor.value.trim() && !window.confirm("载入版本会覆盖当前未保存的最终简历内容。是否继续？")) return;
  editor.value = version.content;
  selectedPurpose = version.purpose || selectedPurpose;
  selectedTemplate = version.template || selectedTemplate;
  choosePurpose(selectedPurpose);
  chooseTemplate(selectedTemplate);
  $("#versionStatus").textContent = `已载入“${version.name}”。`;
  $("#documentWrap").classList.remove("hidden");
  editor.focus();
}

function render() {
  const matches = result.evidence_matches;
  const supported = matches.filter((item) => item.strength !== "none");
  const missing = matches.filter((item) => item.strength === "none");
  const score = matches.length ? Math.round((supported.length / matches.length) * 100) : 0;
  $("#score").textContent = score;
  $("#requirements").innerHTML = result.requirements.map((item) => (
    `<div class="item"><small>${categoryLabel(item.category)}</small><br>${esc(item.text)}</div>`
  )).join("");
  $("#matched").innerHTML = supported.length ? supported.map((item) => (
    `<div class="item">✓ ${esc(item.requirement)}<br><small>证据强度：${strengthLabel(item.strength)}<br>原始证据：${esc(item.resume_quote)}<br>${esc(item.reason)}</small></div>`
  )).join("") : '<div class="item">暂未找到能直接支持 JD 的简历原句。</div>';
  $("#missing").innerHTML = missing.length ? missing.map((item) => (
    `<div class="item miss">△ 缺少证据：${esc(item.requirement)}<br><small>${esc(item.reason)}</small></div>`
  )).join("") : '<div class="item">每条 JD 要求均找到至少一条相关原文；仍请核对证据强度。</div>';
  $("#questions").innerHTML = result.questions.length ? result.questions.map((question, index) => (
    `<div class="question"><label>${index + 1}. ${esc(question)}</label><input data-fact="${index}" placeholder="只填写可核实的本人事实；没有就留空"></div>`
  )).join("") : '<div class="item">暂无必须补充的问题；你仍可以检查每条原始证据。</div>';
  $("#draft").innerHTML = '<div class="item">确认事实后，可生成“原文 / 改写 / 理由”对照；系统只会使用已确认的原文与事实。</div>';
  renderIntroduction(supported);
  $("#results").classList.remove("hidden");
  $("#results").scrollIntoView({ behavior: "smooth" });
}

function renderIntroduction(supported) {
  const role = $("#role").value.trim() || "目标岗位";
  const quotes = supported.slice(0, 2).map((item) => `“${item.resume_quote}”`).join("；");
  $("#intro").innerHTML = `<div class="draft-line">您好，我拥有医学背景，正在申请${esc(role)}。目前可确认、并与该岗位相关的经历包括：${esc(quotes || "尚未找到可直接引用的经历")}。我会在沟通中进一步说明这些经历中的具体行动、交付物与结果。</div>`;
}

function parseExperiences(text) {
  const datePattern = /^(\d{4}[.\-/]\d{1,2}(?:\s*(?:[-–—]|至)\s*(?:\d{4}[.\-/]\d{1,2}|至今))?|\d{4}\s*[-–—]\s*至今)/;
  const experiences = [];
  let current = null;
  for (const rawLine of text.split("\n")) {
    const line = rawLine.trim();
    if (!line) continue;
    if (SECTION_HEADINGS.includes(line)) { current = null; continue; }
    if (line === "已确认医学经历") {
      current = { date: "", organization: "已确认医学经历", role: "", bullets: [] };
      experiences.push(current);
      continue;
    }
    const date = line.match(datePattern);
    if (date) {
      const rest = line.slice(date[0].length).trim();
      const parts = rest.split(/\t+|\s{2,}/).filter(Boolean);
      current = { date: date[0], organization: parts[0] || "经历", role: parts.slice(1).join(" · "), bullets: [] };
      experiences.push(current);
      continue;
    }
    const bullet = line.replace(/^[•●▪◦\-*\s]+/, "").trim();
    if (current) current.bullets.push(bullet);
  }
  return experiences;
}

function manualCapabilities() {
  const manual = $("#capabilities").value.split("\n").map((item) => item.trim()).filter(Boolean);
  const confirmed = (resumeDocument?.capability_profile || []).map((item) => item.name);
  return [...new Set([...confirmed, ...manual])].slice(0, 6);
}

function tailoredSummary() {
  const manual = $("#summary").value.trim();
  if (manual) return manual;
  const role = $("#role").value.trim() || PURPOSES[selectedPurpose].label;
  return (result?.evidence_matches || []).some((item) => item.strength !== "none") ? `医学背景求职者，申请${role}。以下经历已与岗位要求进行证据匹配，所有表述均须以本人可核实的原始材料为准。` : `医学背景求职者，申请${role}。以下内容均须以本人可核实的原始材料为准。`;
}

function choosePurpose(purpose) {
  selectedPurpose = purpose;
  document.querySelectorAll("[data-purpose]").forEach((item) => item.classList.toggle("selected", item.dataset.purpose === purpose));
  const config = PURPOSES[purpose];
  $("#purposeHint").textContent = `当前为“${config.label}”：成稿会优先组织${config.focus}。`;
}

function chooseTemplate(template) {
  selectedTemplate = template;
  document.querySelectorAll("[data-template]").forEach((item) => item.classList.toggle("selected", item.dataset.template === template));
  if (!$("#resumePreview").classList.contains("hidden")) renderPrintableResume();
}

function extractNamedSection(text, heading, nextHeadings) {
  const lines = text.split("\n").map((line) => line.trim());
  const start = lines.findIndex((line) => line === heading);
  if (start < 0) return [];
  const result = [];
  for (const line of lines.slice(start + 1)) {
    if (nextHeadings.includes(line)) break;
    if (line) result.push(line.replace(/^[•●▪◦\-*\s]+/, "").trim());
  }
  return result;
}

function chooseTranslationTarget(target) {
  selectedTranslationTarget = target;
  document.querySelectorAll("[data-translation-target]").forEach((item) => item.classList.toggle("selected", item.dataset.translationTarget === target));
}

async function translateCapabilities() {
  const error = $("#translationError");
  const output = $("#translationResult");
  error.textContent = "";
  output.innerHTML = "";
  if (!resumeDocument?.capability_profile?.length) {
    error.textContent = "请先保存结构化简历，并在医学科研能力画像中确认至少一项能力。";
    return;
  }
  const jd = $("#jd").value.trim() || $("#role").value.trim();
  if (!jd) { error.textContent = "请先填写目标岗位或 JD。"; return; }
  const button = $("#translateCapabilities");
  button.disabled = true;
  button.textContent = "正在翻译岗位价值…";
  try {
    const response = await fetch("/api/resume-translations", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_document: resumeDocument, jd_text: jd, target_profile: selectedTranslationTarget }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "岗位能力翻译失败");
    output.innerHTML = body.recommendations.length ? `<div class="translation-result"><b>${esc(body.target_label)}：建议前置的真实能力</b>${body.recommendations.map((item) => `<div class="item"><b>${esc(item.capability)}</b> → ${esc(item.market_value)}<br><small>推荐位置：${esc(item.placement)}<br>${esc(item.rationale)}</small></div>`).join("")}</div>` : `<div class="item miss">${esc(body.gaps.join("；"))}</div>`;
  } catch (requestError) { error.textContent = requestError.message; }
  finally { button.disabled = false; button.textContent = "生成岗位能力翻译 →"; }
}

function renderStructuredResumePreview(documentModel) {
  const list = (items, formatter) => items?.length ? `<ul class="resume-list">${items.map((item) => `<li>${esc(formatter(item))}</li>`).join("")}</ul>` : "";
  const experience = (items) => items?.length ? items.map((item) => `<article class="resume-entry"><div class="resume-entry-head"><span class="resume-date">${esc(item.period?.start || "")}</span><strong class="resume-org">${esc(item.organization)}</strong><span class="resume-role">${esc([item.department_or_field, item.title].filter(Boolean).join(" · "))}</span></div>${list(item.bullets, (bullet) => bullet.text)}</article>`).join("") : "";
  const section = (title, content, className = "") => content ? `<section class="resume-section ${className}"><h2>${title}</h2>${content}</section>` : "";
  const educationSection = section("教育背景", list(documentModel.education, (item) => [item.institution, item.degree, item.major, item.period?.start].filter(Boolean).join("｜")), "resume-education-section");
  const experienceSection = section("临床 / 工作 / 项目经历", [experience(documentModel.clinical_experience), experience(documentModel.professional_experience), experience(documentModel.projects)].join(""), "resume-experience-section");
  const researchSection = section("科研与学术成果", `${experience(documentModel.research_experience)}${list(documentModel.publications, (item) => [item.title, item.venue, item.author_position, item.status].filter(Boolean).join("｜"))}`, "resume-research-section");
  const skillsSection = section("技能与语言", `${list(documentModel.skills, (item) => item.name)}${list(documentModel.languages, (item) => [item.language, item.level_or_score].filter(Boolean).join("｜"))}`, "resume-skills-section");
  const awardsSection = section("荣誉与奖项", list(documentModel.awards, (item) => [item.name, item.issuer, item.year].filter(Boolean).join("｜")));
  const capabilitiesSection = section("核心能力", list(documentModel.capability_profile, (item) => `${item.name}｜${CAPABILITY_PROFICIENCY_LABELS[item.proficiency]}`), "resume-capabilities-section");
  const summarySection = documentModel.basics.summary ? section("个人概述", `<p class="resume-summary">${esc(documentModel.basics.summary)}</p>`, "resume-summary-section") : "";
  const identity = `<div><h1 class="resume-name">${esc(documentModel.basics.name || "候选人姓名")}</h1><p class="resume-contact">${esc(documentModel.basics.location || "联系方式请在提交前补充")}</p><p class="resume-target">医学背景 · ${esc(documentModel.target.role || "目标岗位")}</p></div>`;
  const templateBody = selectedTemplate === "research"
    ? `<header class="resume-header resume-header-research">${identity}<p class="resume-document-label">ACADEMIC CURRICULUM VITAE</p></header><div class="research-layout"><main class="resume-main">${educationSection}${researchSection}${experienceSection}</main><aside class="resume-aside">${summarySection}${capabilitiesSection}${skillsSection}${awardsSection}</aside></div>`
    : selectedTemplate === "minimal"
      ? `<header class="resume-header resume-header-minimal">${identity}</header>${summarySection}${capabilitiesSection}${educationSection}${experienceSection}${researchSection}${skillsSection}${awardsSection}`
      : `<header class="resume-header resume-header-clinical">${identity}<div class="resume-photo">证件照<br>可选</div></header>${summarySection}${capabilitiesSection}${educationSection}${experienceSection}${researchSection}${skillsSection}${awardsSection}`;
  $("#resumePreview").innerHTML = `<div class="resume-toolbar"><p>投递版预览 · 直接读取已确认的结构化数据</p><button id="printResume">打印 / 保存为 PDF</button></div><article class="resume-sheet template-${selectedTemplate}">${templateBody}</article>`;
  $("#resumePreview").classList.remove("hidden");
  $("#resumePreview").scrollIntoView({ behavior: "smooth" });
  $("#printResume").onclick = () => window.print();
}

function renderPrintableResume() {
  if (resumeDocument?.schema_version === "resume-document-v1") {
    renderStructuredResumePreview(resumeDocument);
    return;
  }
  const source = $("#document").value.trim() || $("#resume").value.trim();
  if (!source) { $("#error").textContent = "请先填写原始简历。"; return; }
  const experiences = parseExperiences(source);
  const supported = (result?.evidence_matches || []).filter((item) => item.strength !== "none");
  const skills = [];
  const capabilities = extractNamedSection(source, "核心能力", ["教育背景", "相关经历", "研究 / 学术成果", "技能与证书"]);
  const education = extractNamedSection(source, "教育背景", ["相关经历", "研究 / 学术成果", "技能与证书"]);
  const research = extractNamedSection(source, "研究 / 学术成果", ["技能与证书"]);
  const listedSkills = extractNamedSection(source, "技能与证书", []);
  const name = $("#name").value.trim() || "候选人姓名";
  const contact = $("#contact").value.trim() || "联系方式请在提交前补充";
  const role = $("#role").value.trim() || "目标岗位";
  const summary = supported.length
    ? `医学背景，现有经历中已识别到与${role}相关的证据；以下内容均来自候选人确认的原始材料。`
    : `医学背景求职者，以下经历均来自候选人确认的原始材料。`;
  const entries = experiences.length ? experiences.map((item) => `
    <article class="resume-entry">
      <div class="resume-entry-head"><span class="resume-date">${esc(item.date)}</span><strong class="resume-org">${esc(item.organization)}</strong><span class="resume-role">${esc(item.role)}</span></div>
      ${item.bullets.length ? `<ul>${item.bullets.map((bullet) => `<li>${esc(bullet)}</li>`).join("")}</ul>` : ""}
    </article>`).join("") : `<p class="resume-empty">未能从文本中识别出日期开头的经历。请使用“2024.01-2024.06  单位  职位”的格式。</p>`;
  const section = (title, content, className = "") => content ? `<section class="resume-section ${className}"><h2>${title}</h2>${content}</section>` : "";
  const summarySection = section("个人概述", `<p class="resume-summary">${esc(summary)}</p>`, "resume-summary-section");
  const capabilitiesSection = (capabilities.length || skills.length)
    ? section("核心能力", capabilities.length ? `<ul class="resume-list">${capabilities.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>` : `<div>${skills.map((skill) => `<span class="resume-skill">${esc(skill)}</span>`).join("")}</div>`, "resume-capabilities-section")
    : "";
  const educationSection = education.length ? section("教育背景", `<ul class="resume-list">${education.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`, "resume-education-section") : "";
  const experienceSection = section("实践与项目经历", entries, "resume-experience-section");
  const researchSection = research.length ? section("研究 / 学术成果", `<ul class="resume-list">${research.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`, "resume-research-section") : "";
  const skillsSection = listedSkills.length ? section("技能与证书", `<ul class="resume-list">${listedSkills.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`, "resume-skills-section") : "";
  const identity = `<div><h1 class="resume-name">${esc(name)}</h1><p class="resume-contact">${esc(contact)}</p><p class="resume-target">医学背景 · ${esc(role)}</p></div>`;
  const templateBody = selectedTemplate === "research"
    ? `<header class="resume-header resume-header-research">${identity}<p class="resume-document-label">ACADEMIC CURRICULUM VITAE</p></header><div class="research-layout"><main class="resume-main">${educationSection}${researchSection}${experienceSection}</main><aside class="resume-aside">${summarySection}${capabilitiesSection}${skillsSection}</aside></div>`
    : selectedTemplate === "minimal"
      ? `<header class="resume-header resume-header-minimal">${identity}</header>${summarySection}${educationSection}${experienceSection}${researchSection}${capabilitiesSection}${skillsSection}`
      : `<header class="resume-header resume-header-clinical">${identity}<div class="resume-photo">证件照<br>可选</div></header>${summarySection}${capabilitiesSection}${educationSection}${experienceSection}${researchSection}${skillsSection}`;
  $("#resumePreview").innerHTML = `
    <div class="resume-toolbar"><p>投递版预览 · 仅重组排版，不新增事实</p><span><button id="refreshResume">刷新预览</button><button id="editResume">编辑文字</button><button id="printResume">打印 / 保存为 PDF</button></span></div>
    <article class="resume-sheet template-${selectedTemplate}">
      ${templateBody}
    </article>`;
  $("#resumePreview").classList.remove("hidden");
  $("#resumePreview").scrollIntoView({ behavior: "smooth" });
  $("#printResume").onclick = () => window.print();
  $("#refreshResume").onclick = renderPrintableResume;
  $("#editResume").onclick = () => {
    $("#resume").scrollIntoView({ behavior: "smooth", block: "center" });
    $("#resume").focus();
  };
}

$("#analyze").onclick = async () => {
  const resume = $("#resume").value.trim();
  const jd = $("#jd").value.trim();
  const error = $("#error");
  error.textContent = "";
  if (location.protocol === "file:") {
    error.textContent = "请通过本地服务打开本页： http://127.0.0.1:5000/demo/resume-beta/index.html";
    return;
  }
  if (!$("#consent").checked) { error.textContent = "请先确认隐私提示。"; return; }
  if (!resume || !jd) { error.textContent = "请同时粘贴原始简历和目标岗位 JD。"; return; }
  const button = $("#analyze");
  button.disabled = true;
  button.textContent = "正在诊断…";
  try {
    const response = await fetch("/api/resume-intake", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_text: resume, jd_text: jd }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "诊断失败");
    result = body;
    render();
  } catch (requestError) { error.textContent = requestError.message; }
  finally { button.disabled = false; button.textContent = "开始诊断 →"; }
};

document.addEventListener("click", (event) => {
  if (event.target.matches(".copy")) navigator.clipboard.writeText($("#" + event.target.dataset.copy).innerText);
  if (event.target.closest("[data-template]")) chooseTemplate(event.target.closest("[data-template]").dataset.template);
  if (event.target.closest("[data-purpose]")) choosePurpose(event.target.closest("[data-purpose]").dataset.purpose);
  if (event.target.closest("[data-translation-target]")) chooseTranslationTarget(event.target.closest("[data-translation-target]").dataset.translationTarget);
  const rewriteAction = event.target.closest(".accept-rewrite, .reject-rewrite");
  if (rewriteAction) {
    const index = Number(rewriteAction.dataset.index);
    const item = result?.rewrites?.[index];
    if (!item) return;
    const disposition = rewriteAction.matches(".accept-rewrite") ? "accepted" : "rejected";
    if (disposition === "accepted") insertRewrite(item);
    try {
      recordRewriteDisposition(item, index, disposition);
      $("#rewriteAuditStatus").textContent = disposition === "accepted" ? "已接受并插入最终简历；选择记录已保存在当前浏览器。" : "已标记为不采用；选择记录已保存在当前浏览器。";
    } catch { $("#rewriteAuditStatus").textContent = "此次选择已生效，但浏览器未能保存审计记录。"; }
    const card = rewriteAction.closest(".draft-line");
    if (card) {
      card.classList.add(disposition === "accepted" ? "draft-accepted" : "draft-rejected");
      const actions = card.querySelector(".rewrite-audit-actions");
      if (actions) actions.innerHTML = `<small>${disposition === "accepted" ? "已接受并插入" : "已标记为不采用"}</small>`;
    }
  }
});

$("#restart").onclick = () => {
  $("#results").classList.add("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
};

$("#rewriteButton").onclick = async () => {
  const button = $("#rewriteButton");
  const error = $("#rewriteError");
  error.textContent = "";
  button.disabled = true;
  button.textContent = "正在进行受约束改写…";
  try {
    const confirmedFacts = [...document.querySelectorAll("[data-fact]")].map((item) => item.value.trim()).filter(Boolean);
    const response = await fetch("/api/resume-rewrites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_text: $("#resume").value.trim(), jd_text: $("#jd").value.trim(), confirmed_facts: confirmedFacts }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "改写失败");
    if (body.notice) error.textContent = body.notice;
    result.rewrites = body.items;
    $("#rewriteAuditStatus").textContent = "只有你点击“接受”或“不采用”后，系统才会记录该建议的处理结果到当前浏览器。";
    $("#draft").innerHTML = body.items.map((item, index) => (
      `<div class="draft-line"><small>对应 JD：${esc(item.requirement)}</small><p><b>原文：</b>${esc(item.source_quote)}</p><p><b>改写：</b>${esc(item.rewritten)}</p><p><b>理由：</b>${esc(item.reason)}</p><div class="rewrite-audit-actions"><button class="accept-rewrite" data-index="${index}" type="button">接受并插入最终简历</button><button class="reject-rewrite" data-index="${index}" type="button">不采用</button></div></div>`
    )).join("");
  } catch (requestError) { error.textContent = requestError.message; }
  finally { button.disabled = false; button.textContent = "生成修改对照 →"; }
};

$("#buildDocument").onclick = () => {
  const editor = $("#document");
  editor.value = $("#resume").value.trim();
  $("#documentWrap").classList.remove("hidden");
  editor.focus();
  editor.setSelectionRange(editor.value.length, editor.value.length);
};

$("#buildTailoredDocument").onclick = () => {
  const editor = $("#document");
  if (!structureResult) { $("#error").textContent = "请先识别并确认简历结构，再生成定制成稿。"; return; }
  if (!selectedStructuredEvidenceIds().size) { $("#error").textContent = "请至少勾选一条真实内容，再生成定制成稿。"; return; }
  const config = PURPOSES[selectedPurpose];
  const capabilities = manualCapabilities();
  const role = $("#role").value.trim() || config.label;
  const sectionContent = (heading) => {
    if (heading.includes("技能") || heading.includes("能力")) return capabilities.map((item) => `• ${item}`).join("\n") || draftContentForHeading(heading) || structuredContentForHeading(heading);
    if (heading.includes("概述")) return tailoredSummary();
    return draftContentForHeading(heading) || structuredContentForHeading(heading);
  };
  editor.value = `求职 / 申请目标｜${role}\n用途分类｜${config.label}\n\n${config.sections.map((heading) => `${heading}\n${sectionContent(heading)}`).join("\n\n")}`;
  $("#documentWrap").classList.remove("hidden");
  editor.focus();
};

$("#loadMslTemplate").onclick = () => {
  const editor = $("#document");
  if (editor.value.trim() && !window.confirm("载入模板会覆盖当前最终简历内容。是否继续？")) return;
  const role = $("#role").value.trim() || "医学联络官（MSL）/ 医学事务相关岗位";
  const source = $("#resume").value.trim() || "[请粘贴并保留可核实的原始经历]";
  editor.value = `姓名｜[请填写]\n联系方式｜[邮箱] · [手机] · [城市]\n\n求职意向｜${role}\n\n个人概述\n医学背景求职者，具备临床场景理解、医学信息检索与转译、跨学科沟通等可迁移能力。以下表述请仅保留本人真实且可核实的经历。\n\n核心能力\n• 临床与疾病领域理解｜[请补充具体轮转科室、疾病领域或患者场景]\n• 医学信息与证据转译｜[请补充检索、文献解读、医学内容产出等真实证据]\n• 医学沟通与协作｜[请补充汇报、科普、跨团队或专家沟通等真实证据]\n\n教育背景\n• [学校]｜[学位 / 专业]｜[起止时间]\n• [可补充：排名、奖学金、核心课程；没有则删除]\n\n相关经历\n${source}\n\n研究 / 学术成果\n• [论文、会议汇报、专利、竞赛或研究项目；仅列本人真实角色和状态]\n\n技能与证书\n• 医学信息： [例如 PubMed / Embase / CNKI；仅保留实际使用过的工具]\n• 数据与工具： [例如 SQL / Excel / SPSS / Python；仅保留实际使用过的工具]\n• 语言与合规： [例如 英语能力 / GCP 培训；没有则删除]`;
  $("#documentWrap").classList.remove("hidden");
  editor.focus();
  editor.setSelectionRange(0, 0);
};

$("#previewResume").onclick = renderPrintableResume;
$("#saveResumeVersion").onclick = saveResumeVersion;
$("#loadLatestVersion").onclick = () => {
  const latest = readBrowserList(VERSION_STORAGE_KEY)[0];
  if (!latest) { $("#versionStatus").textContent = "当前浏览器还没有已保存的版本。"; return; }
  loadResumeVersion(latest.version_id);
};

$("#previewAndPrint").onclick = () => {
  renderPrintableResume();
  window.setTimeout(() => window.print(), 250);
};

$("#loadExample").onclick = loadExample;
$("#resumeFile").onchange = (event) => uploadResume(event.target.files[0]);
$("#resume").addEventListener("input", resetStructureReview);
$("#structureResume").onclick = identifyResumeStructure;
$("#selectAllStructured").onclick = () => { document.querySelectorAll(".structure-evidence").forEach((item) => { item.checked = true; }); updateStructureStatus(); };
$("#openDocumentEditor").onclick = openDocumentEditor;
$("#saveDocumentModel").onclick = saveDocumentModel;
$("#translateCapabilities").onclick = translateCapabilities;
document.addEventListener("change", (event) => { if (event.target.matches(".structure-evidence")) updateStructureStatus(); });
document.addEventListener("change", (event) => { if (event.target.matches("[data-capability-name]")) updateCapabilityProfile(); });
document.addEventListener("click", (event) => { if (event.target.matches(".load-version")) loadResumeVersion(event.target.dataset.versionId); });
renderVersionList();

$("#reviewButton").onclick = async () => {
  const error = $("#reviewError");
  const review = $("#review");
  const finalResume = $("#document").value.trim() || $("#resume").value.trim();
  error.textContent = "";
  review.innerHTML = "";
  if (!finalResume) { error.textContent = "请先创建并填写最终简历。"; return; }
  const button = $("#reviewButton");
  button.disabled = true;
  button.textContent = "正在审校…";
  try {
    const confirmedFacts = [...document.querySelectorAll("[data-fact]")].map((item) => item.value.trim()).filter(Boolean);
    const response = await fetch("/api/resume-reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_text: $("#resume").value.trim(),
        jd_text: $("#jd").value.trim(),
        final_resume_text: finalResume,
        confirmed_facts: confirmedFacts,
      }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "审校失败");
    review.innerHTML = body.findings.map((item) => (
      `<div class="item ${item.severity === "warning" ? "miss" : ""}"><b>${esc(item.severity === "warning" ? "需核实" : "提示")}</b>：${esc(item.message)}</div>`
    )).join("");
  } catch (requestError) { error.textContent = requestError.message; }
  finally { button.disabled = false; button.textContent = "审校最终简历 →"; }
};

$("#download").onclick = () => {
  if (!result) return;
  const finalResume = $("#document").value.trim();
  const text = `未界｜医学生 JD 定制简历助手\n\n最终简历\n${finalResume || $("#draft").innerText}\n\nHR 自我介绍\n${$("#intro").innerText}\n\n提示：所有事实须本人核实。`;
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
  link.download = "未界-简历定制结果.txt";
  link.click();
  URL.revokeObjectURL(link.href);
};

choosePurpose(selectedPurpose);

loadCareerHandoff();
loadExperienceCompilerHandoff();
