const $ = (selector) => document.querySelector(selector);
const sessionStorageKey = "medical-resume-agent-session-v1";
const basicsStorageKey = "medical-resume-agent-basics-v1";
let contract = null;
let health = null;
let conversation = null;
let selectedTarget = "doctoral";
let lastMessage = "";
let selectedQuestionOptions = new Set();
let selectedProfileOption = "";

const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[character]));
const labels = {
  retrieve_literature: "医学文献检索", screen_studies: "文献筛选", extract_data: "数据提取",
  perform_analysis: "统计分析", write_manuscript: "论文材料撰写", meta_analysis: "Meta 分析",
  systematic_review: "系统综述", sensitivity_analysis: "敏感性分析", r: "R", python: "Python",
  spss: "SPSS", pubmed: "PubMed", embase: "Embase", cochrane: "Cochrane",
  prisma_flowchart: "PRISMA 流程图", data_extraction_sheet: "数据提取表",
  group_presentation: "组会汇报", research_team: "课题组", supervisor: "导师",
};
const targetLabels = {
  doctoral_v1: "学术升学与科研申请", clinical_research_v1: "临床研究与医院科研",
  clinical_operations_v1: "临床运营 / 临床项目协调",
  medical_affairs_v1: "医学事务 / MSL", health_ai_data_v1: "医疗数据与数字健康",
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: options.body ? { "Content-Type": "application/json", ...(options.headers || {}) } : options.headers,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "请求失败");
  return payload;
}

async function createConversation() {
  conversation = await api("/api/conversations", { method: "POST", body: "{}" });
  localStorage.setItem(sessionStorageKey, conversation.session_id);
  lastMessage = "新会话已建立。先提交一段真实经历。";
}

async function loadOrCreateConversation() {
  const sessionId = localStorage.getItem(sessionStorageKey);
  if (sessionId) {
    try {
      conversation = await api(`/api/conversations/${encodeURIComponent(sessionId)}`);
      return;
    } catch (_) {
      localStorage.removeItem(sessionStorageKey);
    }
  }
  await createConversation();
}

async function sendMessage(payload) {
  setBusy(true);
  try {
    const result = await api(`/api/conversations/${encodeURIComponent(conversation.session_id)}/messages`, {
      method: "POST", body: JSON.stringify(payload),
    });
    conversation = { session_id: conversation.session_id, state: result.state, events: conversation.events || [] };
    lastMessage = result.assistant_message || "";
    render();
    return result;
  } catch (error) {
    showError(error.message);
    throw error;
  } finally {
    setBusy(false);
  }
}

function state() { return conversation?.state || {}; }
function stageIndex(stage) { const index = contract.stages.findIndex((item) => item.id === stage); return index < 0 ? 0 : index; }
function displayStage(stage) { return contract.stages.find((item) => item.id === stage) || contract.stages[0]; }

function render() {
  const current = displayStage(state().stage || "intake");
  const currentIndex = stageIndex(current.id);
  $("#steps").innerHTML = contract.stages.map((item, index) =>
    `<li class="${index === currentIndex ? "active" : index < currentIndex ? "done" : ""}">${esc(item.label)}</li>`
  ).join("");
  $("#progressBar").style.width = `${current.progress}%`;
  $("#stageKicker").textContent = `STEP ${currentIndex + 1} / ${contract.stages.length}`;
  $("#stageTitle").textContent = current.label;
  $("#saveStatus").textContent = `本机会话 ${conversation.session_id.slice(0, 8)}`;
  $("#connection").textContent = health?.llm_configured ? "本机 Agent 已连接 · 语言模型可用" : "本机 Agent 已连接 · 确定性模式";
  $("#workspace").innerHTML = renderWorkspace(current.id);
  $("#error").className = "status-message";
  $("#error").textContent = lastMessage;
  bindWorkspace(current.id);
  renderPreview();
}

function renderWorkspace(stage) {
  if (stage === "intake") return renderIntake();
  if (stage === "fact_confirmation") return renderFacts();
  if (stage === "representative_sample") return renderTargetSelection();
  if (stage === "composition" || stage === "factual_audit") return renderClaims();
  return renderDelivery();
}

function renderIntake() {
  const profile = state().candidate_profile || {};
  if (profile.status !== "confirmed") return renderCandidateProfile(profile);
  return `${renderExperienceNavigator(false)}<section class="panel soft"><h3>${(state().confirmed_experiences || []).length ? "继续添加一段真实经历" : "先告诉我们一段真实经历"}</h3>
    <p>写下研究背景、你实际做过的步骤、方法或工具。系统只把原文支持的内容变成待确认事实。</p>
    <label class="field">经历材料<textarea id="material" placeholder="例如：在导师指导下参与系统综述，使用 PubMed 检索文献并完成文献筛选。"></textarea></label>
    <label class="consent"><input id="consent" type="checkbox"><span>我确认材料来自本人真实经历，并同意在当前电脑的本机服务中保存该会话；点击“开始新简历”会删除当前会话文件。</span></label>
    <button id="submitMaterial" class="primary" type="button">建立事实卡 →</button></section>`;
}

function renderExperienceNavigator(allowActions) {
  const experiences = state().confirmed_experiences || [];
  if (!experiences.length) return "";
  const activeId = state().active_experience_id;
  const cards = experiences.map((item, index) => `<button class="experience-tab ${item.experience_id === activeId ? "active" : ""}" data-experience-id="${esc(item.experience_id)}" type="button" ${allowActions ? "" : "disabled"}><span>经历 ${index + 1}</span><b>${esc(item.label || "已确认经历")}</b><small>已确认</small></button>`).join("");
  return `<section class="panel experience-navigator"><div class="experience-heading"><div><span class="status-badge">已确认 ${experiences.length} 段</span><h3>你的经历</h3></div>${allowActions ? '<button id="startNewExperience" class="secondary" type="button">＋ 添加另一段经历</button>' : ""}</div><div class="experience-tabs">${cards}</div></section>`;
}

function profileAnswerLabel(id) {
  return { name: "姓名", email: "邮箱", phone: "电话", location: "所在地", institution: "学校", degree: "学历 / 学位", major: "专业", period: "就读时间" }[id] || id;
}

function renderProfileSummary(profile, confirmable = false) {
  const answers = profile.answers || {};
  const rows = Object.entries(answers).filter(([, value]) => value && (typeof value !== "object" || Object.values(value).some(Boolean))).map(([id, value]) => {
    const shown = id === "period" ? `${value.start || "未填开始时间"} 至 ${value.ongoing ? "今" : (value.end || "未填结束时间")}` : value;
    return `<div class="profile-summary-row"><span>${esc(profileAnswerLabel(id))}</span><b>${esc(shown)}</b></div>`;
  }).join("");
  return `<section class="panel profile-summary"><div class="profile-summary-head"><div><span class="status-badge">${confirmable ? "请你确认" : "已收集"}</span><h3>基础资料与教育背景</h3></div>${confirmable ? '<button id="editCandidateProfile" class="quiet" type="button">重新检查</button>' : ""}</div>${rows || "<p>还没有已填写资料。</p>"}${confirmable ? '<button id="confirmCandidateProfile" class="primary" type="button">信息准确，开始聊经历 →</button>' : ""}</section>`;
}

function renderCandidateProfile(profile) {
  if (profile.status === "awaiting_confirmation") return renderProfileSummary(profile, true);
  const question = profile.current_question || {};
  const previous = (profile.answers || {})[question.id];
  let control = `<input id="profileValue" type="${question.kind === "email" ? "email" : "text"}" value="${esc(previous || "")}" placeholder="${esc(question.placeholder || "")}">`;
  if (question.kind === "single_choice") {
    control = `<div class="profile-options" role="group" aria-label="学历或学位选项">${(question.options || []).map((option) => `<button class="answer-option profile-option" data-profile-option="${esc(option)}" aria-pressed="false" type="button">${esc(option)}</button>`).join("")}</div><label class="field">其他情况（可选）<input id="profileValue" value="${esc(previous || "")}" placeholder="${esc(question.placeholder || "")}"></label>`;
  } else if (question.kind === "period") {
    const period = previous || {};
    control = `<div class="period-grid"><label class="field">开始年月<input id="profileStart" type="month" value="${esc(period.start || "")}"></label><label class="field">结束年月<input id="profileEnd" type="month" value="${esc(period.end || "")}" ${period.ongoing ? "disabled" : ""}></label></div><label class="consent"><input id="profileOngoing" type="checkbox" ${period.ongoing ? "checked" : ""}><span>目前仍在读</span></label>`;
  }
  return `${renderProfileSummary(profile)}<section class="panel soft profile-question"><span class="status-badge">资料 ${question.position || 1} / ${question.total || 8}</span><h3>${esc(question.label || "请填写基础资料")}</h3><p>你的回答会保存在本机 session；确认前不会进入最终简历。</p><p>${esc(question.help || "")}</p><div class="field"><span>你的回答</span>${control}</div><div class="action-row"><button id="submitCandidateProfile" class="primary" type="button">保存并继续 →</button>${question.required ? "" : '<button id="skipCandidateProfile" class="quiet" type="button">暂时跳过</button>'}</div></section>`;
}

function factGroups(facts) {
  const groups = [["行动", facts.actions], ["研究方法", facts.methods], ["工具与资源", facts.tools], ["实验技术", facts.techniques], ["交付物", facts.artifacts], ["协作对象", facts.collaboration]];
  return groups.filter(([, values]) => values?.length).map(([title, values]) =>
    `<div class="fact-group"><b>${title}</b><div class="chips">${values.map((item) => `<span class="chip">${esc(labels[item] || item)}</span>`).join("")}</div></div>`
  ).join("");
}

function renderProposal(proposal, index) {
  const components = Object.values(proposal.components || {}).flat().map((item) => labels[item] || item);
  return `<article class="activity-card" data-index="${index}"><span class="status-badge">待确认活动 ${index + 1}</span><h3>${esc(components.join(" · ") || "已识别活动")}</h3>
    <p class="evidence-quote">原文依据：${esc(proposal.evidence_quote)}</p><div class="boundary-grid">
    <label class="field">任务责任<select data-field="ownership_level"><option value="contributed">参与 / 协助</option><option value="owned_component">负责明确模块</option><option value="led_delivery">推动交付</option><option value="accountable">最终责任人</option></select></label>
    <label class="field">执行方式<select data-field="execution_mode"><option value="supervised">在指导下</option><option value="shared">共同完成</option><option value="independent">独立完成</option></select></label>
    <label class="field">覆盖范围<select data-field="coverage"><option value="partial">部分步骤</option><option value="full">完整活动</option></select></label></div>
    <label class="field">具体范围（建议填写）<input data-field="scope_note" placeholder="例如：按既定检索式执行 PubMed 检索"></label></article>`;
}

function renderFacts() {
  const draft = state().extracted_draft || {};
  const facts = draft.extracted_facts || {};
  const pending = (state().activity_proposals || []).filter((item) => item.status === "needs_user_confirmation");
  return `${renderIntakeModelSummary()}<section class="panel"><h3>系统提取的事实卡</h3><p>这些是候选事实，不等于系统替你认定了责任。</p>${factGroups(facts) || "<p>暂未提取到足够事实。</p>"}</section>
    ${pending.length ? `<section class="panel soft"><h3>逐项确认活动与责任边界</h3><p>每张卡分别确认“做了什么、怎样完成、覆盖多少”。强责任必须由你的选择和原文共同支持。</p>${pending.map(renderProposal).join("")}<button id="confirmActivities" class="primary" type="button">确认活动与事实 →</button></section>` : ""}
    ${renderQuestionCard()}`;
}

function renderIntakeModelSummary() {
  const model = state().intake_model || {};
  if (model.status === "validated") return `<section class="panel model-summary"><span class="status-badge">AI 已按原文整理</span><h3>我目前的理解</h3><p>${esc(model.summary)}</p><small>这仍是待确认摘要，不会直接写入简历。</small></section>`;
  if (model.status === "failed" || model.status === "rejected") return `<section class="panel model-summary warning"><span class="status-badge">本轮 AI 整理未完成</span><p>${esc(model.error || "原始回答已保留，请继续回答当前问题。")}</p></section>`;
  if (model.status === "not_configured") return `<section class="panel model-summary warning"><span class="status-badge">尚未使用 AI 整理</span><p>原始回答已保留；配置模型后才会生成 Skill 约束下的自然语言摘要。</p></section>`;
  return "";
}

function renderQuestionCard() {
  const fallback = (state().pending_questions || ["请补充你实际做过的步骤、工具和责任范围。"])[0];
  const card = state().question_card || { text: fallback, selection_mode: "multiple", options: [], allow_free_text: true };
  const options = (card.options || []).map((option) => `<button class="answer-option" data-question-option="${esc(option.id)}" type="button" aria-pressed="false">${esc(option.label)}</button>`).join("");
  return `<section class="panel question-panel" data-selection-mode="${esc(card.selection_mode || "multiple")}">
    <span class="status-badge">本轮只回答这一题</span><h3>${esc(card.text)}</h3>
    ${card.why_it_matters ? `<p>${esc(card.why_it_matters)}</p>` : ""}
    ${options ? `<div class="answer-options" role="group" aria-label="预设答案，可选择一个或多个">${options}</div>` : ""}
    <label class="field">补充说明（可选）<textarea id="supplement" placeholder="选项不完全符合时，在这里补充真实、可核验的信息。"></textarea></label>
    <button id="supplementFacts" class="primary" type="button">发送这一题的回答</button></section>`;
}

function renderTargetSelection() {
  return `${renderExperienceNavigator(true)}<section class="panel soft"><h3>事实已经冻结，选择表达方向</h3><p>方向只改变重点与排序；系统会分别处理上方所有已确认经历。</p><div class="target-grid">${contract.targets.map((target) => `<button class="choice ${selectedTarget === target.id ? "selected" : ""}" data-target="${target.id}" type="button"><b>${esc(target.label)}</b><span>${esc(target.role_pack)}</span></button>`).join("")}</div>
    <div class="action-row"><button id="generateClaims" class="primary" type="button">生成代表要点并审计 →</button></div></section>`;
}

function renderClaim(claim) {
  const gate = state().claim_gate_results?.[claim.claim_id] || {};
  const ready = gate.status === "ready";
  return `<article class="claim ${ready ? "ready" : ""}" data-claim="${esc(claim.claim_id)}"><div class="claim-meta"><b>${ready ? "事实审计通过" : "需要修改"}</b><span>${esc(claim.role_pack || "")}</span></div>
    <textarea class="claim-editor">${esc(claim.wording)}</textarea>${gate.failed_checks?.length ? `<p class="audit-warning">${gate.failed_checks.map(esc).join("；")}</p>` : ""}
    <div class="action-row"><button class="secondary saveClaim" type="button">保存并重新审计</button>${health?.llm_configured ? `<button class="quiet rewriteClaim" data-tone="Conservative" type="button">稳妥版</button><button class="quiet rewriteClaim" data-tone="Professional" type="button">专业版</button><button class="quiet rewriteClaim" data-tone="High-impact" type="button">高竞争力版</button>` : ""}</div></article>`;
}

function renderClaims() {
  const claims = state().generated_claims || [];
  const ready = claims.filter((claim) => state().claim_gate_results?.[claim.claim_id]?.status === "ready");
  return `<section class="panel"><h3>代表要点与事实审计</h3><p>当前 ${ready.length}/${claims.length} 条可进入预览。修改措辞后会重新通过 v2 Claim Gate；未通过的内容不会显示在简历中。</p>${claims.map(renderClaim).join("") || "<p>没有生成可审计要点，请返回补充活动事实。</p>"}
    ${!health?.llm_configured ? '<p class="mode-note">当前未配置模型：可使用确定性要点并手动编辑；三档 AI 改写按钮仅在配置兼容模型后出现。</p>' : ""}<div class="action-row"><button id="acceptClaims" class="primary" type="button" ${ready.length ? "" : "disabled"}>批准当前要点并进入交付 →</button></div></section>`;
}

function savedBasics() { try { return JSON.parse(localStorage.getItem(basicsStorageKey) || "{}"); } catch (_) { return {}; } }
function renderDelivery() {
  const profile = state().candidate_profile || {};
  if (profile.status === "confirmed") {
    return `${renderProfileSummary(profile)}<section class="panel"><h3>下载交付文件</h3><p>抬头和教育背景来自你刚才确认的资料；只有通过 Claim Gate 的经历要点会进入文件。</p><div class="action-row"><button id="downloadBundle" class="primary" type="button">下载完整交付包</button></div></section>`;
  }
  const basics = savedBasics();
  return `<section class="panel"><h3>补齐抬头并交付</h3><p>姓名和联系方式仅保存在当前浏览器，并在下载时随请求用于生成文件，不写回经历事实。</p><div class="basics-grid"><label class="field">姓名<input id="candidateName" value="${esc(basics.name || "")}" placeholder="姓名"></label><label class="field">联系方式<input id="candidateContact" value="${esc(basics.contact || "")}" placeholder="电话 · 邮箱 · 城市"></label></div>
    <div class="action-row"><button id="saveBasics" class="secondary" type="button">更新预览</button><button id="downloadBundle" class="primary" type="button">下载完整交付包</button></div></section>
    <section class="panel soft"><h3 class="audit-ready">已进入交付阶段</h3><p>只有通过 Claim Gate 的要点进入右侧预览和下载文件。</p></section>`;
}

function bindWorkspace(stage) {
  bindExperienceNavigator();
  if (stage === "intake") {
    if ($("#submitCandidateProfile")) bindCandidateProfile();
    else if ($("#confirmCandidateProfile")) bindCandidateProfileConfirmation();
    else $("#submitMaterial").onclick = () => { const text = $("#material").value.trim(); if (!text || !$("#consent").checked) return showError("请填写经历并确认本机处理说明。"); sendMessage({ action: "submit_experience", text, consent_confirmed: true }); };
  } else if (stage === "fact_confirmation") {
    selectedQuestionOptions = new Set();
    document.querySelectorAll("[data-question-option]").forEach((button) => button.onclick = () => toggleQuestionOption(button));
    if ($("#supplementFacts")) $("#supplementFacts").onclick = submitQuestionAnswer;
    if ($("#confirmActivities")) $("#confirmActivities").onclick = confirmActivities;
  } else if (stage === "representative_sample") {
    document.querySelectorAll("[data-target]").forEach((button) => button.onclick = () => { selectedTarget = button.dataset.target; render(); });
    $("#generateClaims").onclick = () => { const target = contract.targets.find((item) => item.id === selectedTarget); sendMessage({ action: "select_role_packs", role_packs: [target.role_pack] }); };
  } else if (stage === "composition" || stage === "factual_audit") {
    document.querySelectorAll(".saveClaim").forEach((button) => button.onclick = () => editClaim(button));
    document.querySelectorAll(".rewriteClaim").forEach((button) => button.onclick = () => rewriteClaim(button));
    if ($("#acceptClaims")) $("#acceptClaims").onclick = () => sendMessage({ action: "accept_bullets" });
  } else { if ($("#saveBasics")) $("#saveBasics").onclick = saveBasicsAndPreview; $("#downloadBundle").onclick = downloadBundle; }
}

function bindExperienceNavigator() {
  if ($("#startNewExperience")) $("#startNewExperience").onclick = () => sendMessage({ action: "start_new_experience" });
  document.querySelectorAll("[data-experience-id]:not([disabled])").forEach((button) => button.onclick = () => sendMessage({ action: "select_experience", experience_id: button.dataset.experienceId }));
}

function bindCandidateProfile() {
  selectedProfileOption = "";
  document.querySelectorAll("[data-profile-option]").forEach((button) => button.onclick = () => {
    selectedProfileOption = button.dataset.profileOption;
    document.querySelectorAll("[data-profile-option]").forEach((item) => {
      const selected = item === button;
      item.classList.toggle("selected", selected);
      item.setAttribute("aria-pressed", String(selected));
    });
    if (selectedProfileOption !== "其他" && $("#profileValue")) $("#profileValue").value = "";
  });
  if ($("#profileOngoing")) $("#profileOngoing").onchange = () => { $("#profileEnd").disabled = $("#profileOngoing").checked; };
  $("#submitCandidateProfile").onclick = () => submitCandidateProfile(false);
  if ($("#skipCandidateProfile")) $("#skipCandidateProfile").onclick = () => submitCandidateProfile(true);
}

function bindCandidateProfileConfirmation() {
  $("#confirmCandidateProfile").onclick = () => sendMessage({ action: "confirm_candidate_profile" });
  $("#editCandidateProfile").onclick = () => sendMessage({ action: "edit_candidate_profile" });
}

function submitCandidateProfile(skipped) {
  const question = state().candidate_profile?.current_question || {};
  const customValue = $("#profileValue")?.value.trim() || "";
  let value = customValue || selectedProfileOption;
  if (question.kind === "single_choice" && selectedProfileOption && selectedProfileOption !== "其他") value = selectedProfileOption;
  if (question.kind === "single_choice" && selectedProfileOption === "其他") value = customValue;
  if (!skipped && question.kind === "single_choice" && selectedProfileOption === "其他" && !customValue) return showError("请选择具体学历，或填写其他真实情况。");
  if (question.kind === "period") value = { start: $("#profileStart").value, end: $("#profileEnd").value, ongoing: $("#profileOngoing").checked };
  if (!skipped && question.required && (!value || (typeof value === "object" && !Object.values(value).some(Boolean)))) return showError("请填写这一项后继续。");
  sendMessage({ action: "answer_candidate_profile", question_id: question.id, value, skipped });
}

function toggleQuestionOption(button) {
  const mode = button.closest("[data-selection-mode]")?.dataset.selectionMode || "multiple";
  const optionId = button.dataset.questionOption;
  if (mode === "single") {
    selectedQuestionOptions.clear();
    document.querySelectorAll("[data-question-option]").forEach((item) => { item.classList.remove("selected"); item.setAttribute("aria-pressed", "false"); });
  }
  if (button.classList.contains("selected") && mode !== "single") selectedQuestionOptions.delete(optionId);
  else selectedQuestionOptions.add(optionId);
  const selected = selectedQuestionOptions.has(optionId);
  button.classList.toggle("selected", selected);
  button.setAttribute("aria-pressed", String(selected));
}

function submitQuestionAnswer() {
  const card = state().question_card || { options: [] };
  const selected = (card.options || []).filter((option) => selectedQuestionOptions.has(option.id)).map((option) => option.answer_text || option.label);
  const extra = $("#supplement").value.trim();
  const text = [...selected, extra].filter(Boolean).join("；");
  if (!text) return showError("请选择至少一个答案，或补充真实信息。");
  sendMessage({ action: "update_facts", text, selected_option_ids: [...selectedQuestionOptions], free_text: extra, display_text: text, consent_confirmed: true });
}

async function confirmActivities() {
  const proposals = (state().activity_proposals || []).filter((item) => item.status === "needs_user_confirmation");
  const cards = [...document.querySelectorAll(".activity-card")];
  const updated = proposals.map((proposal, index) => { const card = cards[index]; const value = (field) => card.querySelector(`[data-field="${field}"]`).value; return { evidence_quote: proposal.evidence_quote, components: proposal.components, ownership_level: value("ownership_level"), execution_mode: value("execution_mode"), coverage: value("coverage"), scope_note: value("scope_note").trim() || null }; });
  if (!updated.length) return showError("当前没有可确认活动，请先补充具体步骤。");
  await sendMessage({ action: "confirm_activity_proposals", activity_proposals: updated, proposal_ids: [] });
}

function editClaim(button) { const card = button.closest("[data-claim]"); const wording = card.querySelector("textarea").value.trim(); if (!wording) return showError("要点不能为空。"); sendMessage({ action: "edit_wording", claim_id: card.dataset.claim, wording }); }
function rewriteClaim(button) { const card = button.closest("[data-claim]"); sendMessage({ action: "rewrite_claim", source_claim_id: card.dataset.claim, tone: button.dataset.tone, instruction: "保持事实与责任边界，提升医学简历的信息密度。" }); }
function saveBasicsAndPreview() { const basics = { name: $("#candidateName").value.trim(), contact: $("#candidateContact").value.trim() }; localStorage.setItem(basicsStorageKey, JSON.stringify(basics)); lastMessage = "抬头信息已保存到当前浏览器。"; render(); }

function renderPreview() {
  const documentData = state().resume_document;
  const paper = $("#preview"); paper.className = `paper theme-${$("#theme").value}`;
  if (!documentData) { paper.innerHTML = '<div class="empty-preview"><b>这里将出现你的简历</b><span>确认活动责任并通过 Claim Gate 后，右侧会显示可交付内容。</span></div>'; $("#print").disabled = true; return; }
  const fallbackBasics = savedBasics(); const basics = documentData.basics || {}; const experiences = documentData.research_experience || [];
  const profileConfirmed = state().candidate_profile?.status === "confirmed";
  const name = basics.name || (profileConfirmed ? "" : fallbackBasics.name) || "姓名（请填写）";
  const contact = [basics.phone, basics.email, basics.location].filter(Boolean).join(" · ") || (profileConfirmed ? "" : fallbackBasics.contact) || "";
  const target = targetLabels[documentData.target?.role] || documentData.target?.role || "医学相关方向";
  const education = (documentData.education || []).map((item) => { const period = item.period || {}; const dates = [period.start, period.ongoing ? "至今" : period.end].filter(Boolean).join(" - "); return `<h3>${esc([item.institution, item.degree, item.major].filter(Boolean).join(" · "))}</h3>${dates ? `<p>${esc(dates)}</p>` : ""}`; }).join("");
  paper.innerHTML = `<h1>${esc(name)}</h1><blockquote>${esc(target)}${contact ? ` · ${esc(contact)}` : ""}</blockquote>${education ? `<h2>教育背景</h2>${education}` : ""}<h2>科研与实践经历</h2>${experiences.map((experience) => { const organization = experience.organization === "待补充" ? "" : (experience.organization || ""); const heading = [organization, experience.title].filter(Boolean).join(" · ") || "已确认经历"; return `<h3>${esc(heading)}</h3><ul>${(experience.bullets || []).map((item) => `<li>${esc(item.text)}</li>`).join("")}</ul>`; }).join("")}`;
  $("#print").disabled = state().stage !== "delivery";
}

async function downloadBundle() {
  if ($("#candidateName") && $("#candidateContact")) saveBasicsAndPreview();
  try {
    const profileConfirmed = state().candidate_profile?.status === "confirmed";
    const bundle = await api(`/api/conversations/${encodeURIComponent(conversation.session_id)}/export`, { method: "POST", body: JSON.stringify({ basics: profileConfirmed ? {} : savedBasics(), theme: $("#theme").value }) });
    Object.entries(bundle.files).forEach(([name, content]) => { const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([content], { type: name.endsWith(".html") ? "text/html;charset=utf-8" : "text/plain;charset=utf-8" })); link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000); });
    lastMessage = "完整交付包已下载；服务器没有另存导出副本。"; render();
  } catch (error) { showError(error.message); }
}

async function resetConversation() {
  setBusy(true);
  try {
    const resetCompleted = await window.ResumeResetFlow.resetResumeConversation({
      sessionId: conversation?.session_id,
      deleteSession: (sessionId) => api(`/api/conversations/${encodeURIComponent(sessionId)}`, { method: "DELETE" }),
      clearLocalState: () => {
        localStorage.removeItem(sessionStorageKey);
        localStorage.removeItem(basicsStorageKey);
      },
      createConversation,
      onDeleteError: (error) => showError(`旧会话删除失败，当前会话仍保留，未创建新简历：${error.message}`),
    });
    if (resetCompleted) render();
  } catch (error) {
    showError(`新会话创建失败：${error.message}`);
  } finally {
    setBusy(false);
  }
}

function setBusy(busy) { document.body.classList.toggle("busy", busy); }
function showError(message) { lastMessage = message; $("#error").className = "error"; $("#error").textContent = message; }
$("#theme").addEventListener("change", renderPreview);
$("#print").addEventListener("click", () => window.print());
$("#reset").addEventListener("click", resetConversation);

(async () => {
  try { [contract, health] = await Promise.all([api("/api/resume-agent/config"), api("/api/health")]); await loadOrCreateConversation(); render(); }
  catch (error) { $("#connection").textContent = "本机服务连接失败"; $("#workspace").innerHTML = `<p class="error">${esc(error.message)}</p>`; }
})();
