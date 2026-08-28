const $ = (selector) => document.querySelector(selector);
const sessionStorageKey = "medical-resume-agent-session-v1";
const basicsStorageKey = "medical-resume-agent-basics-v1";
let contract = null;
let health = null;
let conversation = null;
let selectedTarget = "doctoral";
let lastMessage = "";

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
  return `<section class="panel soft"><h3>先告诉我们一段真实经历</h3>
    <p>写下研究背景、你实际做过的步骤、方法或工具。系统只把原文支持的内容变成待确认事实。</p>
    <label class="field">经历材料<textarea id="material" placeholder="例如：在导师指导下参与系统综述，使用 PubMed 检索文献并完成文献筛选。"></textarea></label>
    <label class="consent"><input id="consent" type="checkbox"><span>我确认材料来自本人真实经历，并同意在当前电脑的本机服务中保存该会话；点击“开始新简历”会删除当前会话文件。</span></label>
    <button id="submitMaterial" class="primary" type="button">建立事实卡 →</button></section>`;
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
  return `<section class="panel"><h3>系统提取的事实卡</h3><p>这些是候选事实，不等于系统替你认定了责任。</p>${factGroups(facts) || "<p>暂未提取到足够事实。</p>"}</section>
    ${pending.length ? `<section class="panel soft"><h3>逐项确认活动与责任边界</h3><p>每张卡分别确认“做了什么、怎样完成、覆盖多少”。强责任必须由你的选择和原文共同支持。</p>${pending.map(renderProposal).join("")}<button id="confirmActivities" class="primary" type="button">确认活动与事实 →</button></section>` : ""}
    <section class="panel"><h3>补充事实或回答问题</h3><p>${esc((state().pending_questions || ["请补充你实际做过的步骤、工具和责任范围。"]).slice(0, 3).join(" · "))}</p>
    <label class="field">补充内容<textarea id="supplement" placeholder="只写真实、可核验的信息；不确定的可以明确说不知道。"></textarea></label><button id="supplementFacts" class="secondary" type="button">补充并重新提取</button></section>`;
}

function renderTargetSelection() {
  return `<section class="panel soft"><h3>事实已经冻结，选择表达方向</h3><p>方向只改变重点与排序，不会改变已确认的经历。</p><div class="target-grid">${contract.targets.map((target) => `<button class="choice ${selectedTarget === target.id ? "selected" : ""}" data-target="${target.id}" type="button"><b>${esc(target.label)}</b><span>${esc(target.role_pack)}</span></button>`).join("")}</div>
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
  const basics = savedBasics();
  return `<section class="panel"><h3>补齐抬头并交付</h3><p>姓名、联系方式和定位仅保存在当前浏览器，并在下载时随请求用于生成文件，不写回经历事实。</p><div class="basics-grid"><label class="field">姓名<input id="candidateName" value="${esc(basics.name || "")}" placeholder="姓名"></label><label class="field">联系方式<input id="candidateContact" value="${esc(basics.contact || "")}" placeholder="电话 · 邮箱 · 城市"></label></div>
    <label class="field">候选人定位（由你确认）<textarea id="positioning" placeholder="例如：具备系统综述与医学证据整理实践基础的临床医学学生">${esc(basics.positioning || "")}</textarea></label><div class="action-row"><button id="saveBasics" class="secondary" type="button">更新预览</button><button id="downloadBundle" class="primary" type="button">下载完整交付包</button></div></section>
    <section class="panel soft"><h3 class="audit-ready">已进入交付阶段</h3><p>只有通过 Claim Gate 的要点进入右侧预览和下载文件。</p></section>`;
}

function bindWorkspace(stage) {
  if (stage === "intake") {
    $("#submitMaterial").onclick = () => { const text = $("#material").value.trim(); if (!text || !$("#consent").checked) return showError("请填写经历并确认本机处理说明。"); sendMessage({ text, consent_confirmed: true }); };
  } else if (stage === "fact_confirmation") {
    if ($("#supplementFacts")) $("#supplementFacts").onclick = () => { const text = $("#supplement").value.trim(); if (!text) return showError("请填写需要补充的事实。"); sendMessage({ action: "update_facts", text, consent_confirmed: true }); };
    if ($("#confirmActivities")) $("#confirmActivities").onclick = confirmActivities;
  } else if (stage === "representative_sample") {
    document.querySelectorAll("[data-target]").forEach((button) => button.onclick = () => { selectedTarget = button.dataset.target; render(); });
    $("#generateClaims").onclick = () => { const target = contract.targets.find((item) => item.id === selectedTarget); sendMessage({ action: "select_role_packs", role_packs: [target.role_pack] }); };
  } else if (stage === "composition" || stage === "factual_audit") {
    document.querySelectorAll(".saveClaim").forEach((button) => button.onclick = () => editClaim(button));
    document.querySelectorAll(".rewriteClaim").forEach((button) => button.onclick = () => rewriteClaim(button));
    if ($("#acceptClaims")) $("#acceptClaims").onclick = () => sendMessage({ action: "accept_bullets" });
  } else { $("#saveBasics").onclick = saveBasicsAndPreview; $("#downloadBundle").onclick = downloadBundle; }
}

async function confirmActivities() {
  const proposals = (state().activity_proposals || []).filter((item) => item.status === "needs_user_confirmation");
  const cards = [...document.querySelectorAll(".activity-card")];
  const updated = proposals.map((proposal, index) => { const card = cards[index]; const value = (field) => card.querySelector(`[data-field="${field}"]`).value; return { evidence_quote: proposal.evidence_quote, components: proposal.components, ownership_level: value("ownership_level"), execution_mode: value("execution_mode"), coverage: value("coverage"), scope_note: value("scope_note").trim() || null }; });
  if (!updated.length) return showError("当前没有可确认活动，请先补充具体步骤。");
  await sendMessage({ action: "update_activity_proposals", activity_proposals: updated });
  await sendMessage({ action: "confirm_activity_proposals", proposal_ids: [] });
}

function editClaim(button) { const card = button.closest("[data-claim]"); const wording = card.querySelector("textarea").value.trim(); if (!wording) return showError("要点不能为空。"); sendMessage({ action: "edit_wording", claim_id: card.dataset.claim, wording }); }
function rewriteClaim(button) { const card = button.closest("[data-claim]"); sendMessage({ action: "rewrite_claim", source_claim_id: card.dataset.claim, tone: button.dataset.tone, instruction: "保持事实与责任边界，提升医学简历的信息密度。" }); }
function saveBasicsAndPreview() { const basics = { name: $("#candidateName").value.trim(), contact: $("#candidateContact").value.trim(), positioning: $("#positioning").value.trim() }; localStorage.setItem(basicsStorageKey, JSON.stringify(basics)); lastMessage = "抬头信息已保存到当前浏览器。"; render(); }

function renderPreview() {
  const documentData = state().resume_document;
  const paper = $("#preview"); paper.className = `paper theme-${$("#theme").value}`;
  if (!documentData) { paper.innerHTML = '<div class="empty-preview"><b>这里将出现你的简历</b><span>确认活动责任并通过 Claim Gate 后，右侧会显示可交付内容。</span></div>'; $("#print").disabled = true; return; }
  const basics = savedBasics(); const experiences = documentData.research_experience || [];
  const target = targetLabels[documentData.target?.role] || documentData.target?.role || "医学相关方向";
  paper.innerHTML = `<h1>${esc(basics.name || "姓名（请填写）")}</h1><blockquote>${esc(target)}${basics.contact ? ` · ${esc(basics.contact)}` : ""}</blockquote>${basics.positioning ? `<h2>候选人定位</h2><p>${esc(basics.positioning)}</p>` : ""}<h2>科研与实践经历</h2>${experiences.map((experience) => { const organization = experience.organization === "待补充" ? "" : (experience.organization || ""); const heading = [organization, experience.title].filter(Boolean).join(" · ") || "已确认经历"; return `<h3>${esc(heading)}</h3><ul>${(experience.bullets || []).map((item) => `<li>${esc(item.text)}</li>`).join("")}</ul>`; }).join("")}`;
  $("#print").disabled = state().stage !== "delivery";
}

async function downloadBundle() {
  saveBasicsAndPreview();
  try {
    const bundle = await api(`/api/conversations/${encodeURIComponent(conversation.session_id)}/export`, { method: "POST", body: JSON.stringify({ basics: savedBasics(), theme: $("#theme").value }) });
    Object.entries(bundle.files).forEach(([name, content]) => { const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([content], { type: name.endsWith(".html") ? "text/html;charset=utf-8" : "text/plain;charset=utf-8" })); link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000); });
    lastMessage = "完整交付包已下载；服务器没有另存导出副本。"; render();
  } catch (error) { showError(error.message); }
}

async function resetConversation() {
  if (conversation?.session_id) { try { await api(`/api/conversations/${encodeURIComponent(conversation.session_id)}`, { method: "DELETE" }); } catch (_) {} }
  localStorage.removeItem(sessionStorageKey); localStorage.removeItem(basicsStorageKey); await createConversation(); render();
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
