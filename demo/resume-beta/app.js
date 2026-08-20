const $ = (selector) => document.querySelector(selector);
let result = null;
let selectedTemplate = "clinical";
let selectedPurpose = "hospital";

const SECTION_HEADINGS = ["个人概述", "核心能力", "教育背景", "相关经历", "实践与项目经历", "研究 / 学术成果", "与目标岗位相关的已确认表述", "科研 / 学术经历", "临床 / 实践经历", "竞赛与能力", "科研 / 实践经历", "补充材料", "研究方向与科研经历", "论文 / 会议 / 成果", "方法与技能", "校园 / 科研经历", "工作与项目经历", "教育与证书"];
const PURPOSES = {
  recommendation: { label: "保研 / 夏令营", focus: "教育表现、科研潜力、课题经历与学术兴趣", sections: ["教育背景", "科研 / 学术经历", "临床 / 实践经历", "竞赛与能力"], checklist: ["GPA / 排名或奖学金", "英语成绩（如 CET-6 / 雅思）", "科研训练、竞赛与导师课题匹配"] },
  masters: { label: "考研复试", focus: "教育基础、科研训练、临床实践与复试可讲述经历", sections: ["教育背景", "科研 / 实践经历", "竞赛与能力", "补充材料"], checklist: ["专业课程与成绩亮点", "科研、竞赛或临床实践", "英语能力与可讲述的复试经历"] },
  phd: { label: "考博", focus: "研究方向、论文成果、方法能力与长期研究计划", sections: ["教育背景", "研究方向与科研经历", "论文 / 会议 / 成果", "方法与技能"], checklist: ["论文、作者位次与研究项目角色", "研究方法、数据分析或实验技能", "英语、研究计划与导师方向匹配"] },
  hospital: { label: "医院 / 规培校招", focus: "临床轮转、科室场景、证书与患者沟通能力", sections: ["教育背景", "临床 / 实践经历", "科研 / 学术经历", "技能与证书"], checklist: ["轮转科室、病种或患者场景", "执业相关资格、培训与获奖", "临床技能、病例汇报或科研经历"] },
  industry: { label: "医药健康行业校招", focus: "实习项目、医学转译、工具与跨团队协作", sections: ["教育背景", "实践与项目经历", "校园 / 科研经历", "技能与证书"], checklist: ["医药、器械、医疗 AI 或科普项目", "医学文献、数据工具与合规意识", "沟通、汇报与跨团队协作证据"] },
  experienced: { label: "社招", focus: "岗位职责、可核实成果、行业工具与角色匹配", sections: ["个人概述", "核心能力", "工作与项目经历", "教育与证书"], checklist: ["目标岗位职责与对应真实成果", "项目规模、交付物和行业工具", "职责边界、工作年限与职业轨迹"] },
  general: { label: "通用简历", focus: "可迁移经历、基础能力与后续定制空间", sections: ["个人概述", "教育背景", "相关经历", "技能与证书"], checklist: ["教育、核心经历与基础技能", "可迁移能力与可量化结果", "删除无关或无法核实的内容"] },
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

function confirmedFacts() {
  return [...document.querySelectorAll("[data-fact]")].map((item) => item.value.trim()).filter(Boolean);
}

function selectedCapabilities() {
  const entered = $("#capabilities").value.split("\n").map((item) => item.trim()).filter(Boolean);
  const matched = (result?.evidence_matches || []).filter((item) => item.strength !== "none").map((item) => item.requirement);
  return [...new Set(entered.length ? entered : matched)].slice(0, 6);
}

function tailoredSummary() {
  const manual = $("#summary").value.trim();
  if (manual) return manual;
  const role = $("#role").value.trim() || PURPOSES[selectedPurpose].label;
  const evidence = (result?.evidence_matches || []).filter((item) => item.strength !== "none");
  return evidence.length
    ? `医学背景求职者，申请${role}。以下经历已与岗位要求进行证据匹配，所有表述均须以本人可核实的原始材料为准。`
    : `医学背景求职者，申请${role}。以下内容均须以本人可核实的原始材料为准。`;
}

function choosePurpose(purpose) {
  selectedPurpose = purpose;
  document.querySelectorAll("[data-purpose]").forEach((item) => item.classList.toggle("selected", item.dataset.purpose === purpose));
  const config = PURPOSES[purpose];
  $("#purposeHint").textContent = `当前为“${config.label}”：成稿会优先组织${config.focus}。`;
  $("#purposeChecklist").innerHTML = `<b>建议优先补充：</b>${config.checklist.map((item) => `<span>${esc(item)}</span>`).join("")}`;
}

function chooseTemplate(template) {
  selectedTemplate = template;
  document.querySelectorAll("[data-template]").forEach((item) => item.classList.toggle("selected", item.dataset.template === template));
  if (!$("#resumePreview").classList.contains("hidden")) renderPrintableResume();
}

const bankKey = "medicalResumeEvidenceBank.v1";
function readBank() { try { return JSON.parse(localStorage.getItem(bankKey) || "{}"); } catch (_) { return {}; } }
function refreshBank() {
  const bank = readBank(); const select = $("#savedProfiles"); const current = select.value;
  select.innerHTML = '<option value="">选择已保存的主经历库</option>' + Object.keys(bank).map((name) => `<option value="${esc(name)}">${esc(name)}</option>`).join("");
  select.value = current in bank ? current : "";
}
function saveProfile() {
  const name = $("#profileName").value.trim(); if (!name) { $("#bankStatus").textContent = "请先填写主经历库名称。"; return; }
  const bank = readBank(); bank[name] = { name: $("#name").value, contact: $("#contact").value, resume: $("#resume").value, summary: $("#summary").value, capabilities: $("#capabilities").value, updatedAt: new Date().toLocaleString() };
  localStorage.setItem(bankKey, JSON.stringify(bank)); refreshBank(); $("#savedProfiles").value = name; $("#bankStatus").textContent = `已保存在此浏览器：${name}。`;
}
function loadProfile() {
  const name = $("#savedProfiles").value; const profile = readBank()[name]; if (!profile) return;
  ["name", "contact", "resume", "summary", "capabilities"].forEach((key) => { $("#" + key).value = profile[key] || ""; }); $("#profileName").value = name; $("#bankStatus").textContent = `已载入：${name}。`;
}
function deleteProfile() { const name = $("#savedProfiles").value; if (!name || !window.confirm(`删除本机经历库“${name}”？`)) return; const bank = readBank(); delete bank[name]; localStorage.setItem(bankKey, JSON.stringify(bank)); refreshBank(); $("#bankStatus").textContent = "已从当前浏览器删除。"; }

const versionsKey = "medicalResumeVersions.v1";
function readVersions() { try { return JSON.parse(localStorage.getItem(versionsKey) || "{}"); } catch (_) { return {}; } }
function refreshVersions() { const versions = readVersions(); $("#savedVersions").innerHTML = '<option value="">载入已保存版本</option>' + Object.keys(versions).map((name) => `<option value="${esc(name)}">${esc(name)}</option>`).join(""); }
function saveVersion() {
  const name = $("#versionName").value.trim(); const documentText = $("#document").value.trim();
  if (!name || !documentText) { $("#versionStatus").textContent = "请先填写版本名称并生成/编辑最终简历。"; return; }
  const versions = readVersions(); versions[name] = { documentText, purpose: selectedPurpose, template: selectedTemplate, role: $("#role").value, savedAt: new Date().toLocaleString(), rewriteCount: result?.rewrites?.length || 0 };
  localStorage.setItem(versionsKey, JSON.stringify(versions)); refreshVersions(); $("#savedVersions").value = name; $("#versionStatus").textContent = `已保存版本：${name}（含 ${versions[name].rewriteCount} 条已生成改写）。`;
}
function loadVersion() { const item = readVersions()[$("#savedVersions").value]; if (!item) return; selectedPurpose = item.purpose || selectedPurpose; selectedTemplate = item.template || selectedTemplate; $("#role").value = item.role || ""; $("#document").value = item.documentText; $("#documentWrap").classList.remove("hidden"); choosePurpose(selectedPurpose); chooseTemplate(selectedTemplate); $("#versionStatus").textContent = `已载入 ${item.savedAt} 保存的版本。`; }

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

function renderPrintableResume() {
  const source = $("#document").value.trim() || $("#resume").value.trim();
  if (!source) { $("#error").textContent = "请先填写原始简历。"; return; }
  const experiences = parseExperiences(source);
  const supported = (result?.evidence_matches || []).filter((item) => item.strength !== "none");
  const skills = [...new Set(supported.map((item) => item.requirement))].slice(0, 6);
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
  const blocks = {
    summary: `<section class="resume-section"><h2>个人概述</h2><p class="resume-summary">${esc(summary)}</p></section>`,
    capabilities: (capabilities.length || skills.length) ? `<section class="resume-section"><h2>核心能力</h2>${capabilities.length ? `<ul class="resume-list">${capabilities.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>` : `<div>${skills.map((skill) => `<span class="resume-skill">${esc(skill)}</span>`).join("")}</div>`}</section>` : "",
    education: education.length ? `<section class="resume-section"><h2>教育背景</h2><ul class="resume-list">${education.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></section>` : "",
    experience: `<section class="resume-section"><h2>实践与项目经历</h2>${entries}</section>`,
    research: research.length ? `<section class="resume-section"><h2>研究 / 学术成果</h2><ul class="resume-list">${research.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></section>` : "",
    skills: listedSkills.length ? `<section class="resume-section"><h2>技能与证书</h2><ul class="resume-list">${listedSkills.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></section>` : "",
  };
  const previewOrder = { recommendation: ["education", "research", "experience", "capabilities"], masters: ["education", "experience", "research", "capabilities"], phd: ["education", "research", "capabilities", "experience"], hospital: ["education", "experience", "research", "skills"], industry: ["education", "experience", "research", "skills"], experienced: ["summary", "capabilities", "experience", "education", "skills"], general: ["summary", "education", "experience", "capabilities", "skills"] }[selectedPurpose];
  const previewSections = previewOrder.map((key) => blocks[key]).join("");
  $("#resumePreview").innerHTML = `
    <div class="resume-toolbar"><p>投递版预览 · 仅重组排版，不新增事实</p><button id="printResume">打印 / 保存为 PDF</button></div>
    <article class="resume-sheet template-${selectedTemplate}">
      <header class="resume-header"><div><h1 class="resume-name">${esc(name)}</h1><p class="resume-contact">${esc(contact)}</p><p class="resume-target">医学背景 · ${esc(role)}</p></div><div class="resume-photo">证件照<br>可选</div></header>
      ${previewSections}
    </article>`;
  $("#resumePreview").classList.remove("hidden");
  $("#resumePreview").scrollIntoView({ behavior: "smooth" });
  $("#printResume").onclick = () => window.print();
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
  if (event.target.matches(".insert-rewrite")) {
    const item = result.rewrites?.[Number(event.target.dataset.index)];
    const editor = $("#document");
    if (!item || !editor) return;
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    editor.setRangeText(item.rewritten, start, end, "end");
    editor.focus();
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
    $("#draft").innerHTML = body.items.map((item, index) => (
      `<div class="draft-line"><small>对应 JD：${esc(item.requirement)}</small><p><b>原文：</b>${esc(item.source_quote)}</p><p><b>改写：</b>${esc(item.rewritten)}</p><p><b>理由：</b>${esc(item.reason)}</p><button class="insert-rewrite" data-index="${index}">插入最终简历 →</button></div>`
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
  const source = $("#resume").value.trim();
  if (!source) { $("#error").textContent = "请先填写原始简历。"; return; }
  const capabilities = selectedCapabilities();
  const evidenceNotes = (result?.rewrites || []).map((item) => item.rewritten).filter(Boolean);
  const config = PURPOSES[selectedPurpose];
  const role = $("#role").value.trim() || config.label;
  const evidenceBlock = evidenceNotes.map((item) => `• ${item}`).join("\n") || "• [完成受约束改写后，可在此保留已确认表述]";
  const sectionContent = (heading) => {
    if (heading.includes("教育")) return "• [请补充学校、学位、专业和起止时间]";
    if (heading.includes("技能") || heading.includes("能力")) return capabilities.map((item) => `• ${item}`).join("\n") || "• [仅保留实际使用过的工具、方法或证书]";
    if (heading.includes("论文") || heading.includes("成果")) return "• [论文、会议、专利、竞赛或研究项目；仅保留真实角色和状态]";
    if (heading.includes("概述")) return tailoredSummary();
    return `${source}\n\n与目标相关的已确认表述\n${evidenceBlock}`;
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
$("#saveProfile").onclick = saveProfile;
$("#loadProfile").onclick = loadProfile;
$("#deleteProfile").onclick = deleteProfile;
$("#saveVersion").onclick = saveVersion;
$("#loadVersion").onclick = loadVersion;

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
  const text = `Medical Resume Agent｜医学生 JD 定制简历助手\n\n最终简历\n${finalResume || $("#draft").innerText}\n\nHR 自我介绍\n${$("#intro").innerText}\n\n提示：所有事实须本人核实。`;
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
  link.download = "medical-resume-result.txt";
  link.click();
  URL.revokeObjectURL(link.href);
};

// End of resume interactions.
choosePurpose(selectedPurpose);
refreshBank();
refreshVersions();
