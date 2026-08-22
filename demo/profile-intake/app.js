const form = document.querySelector("#intakeForm");
const draftButton = document.querySelector("#draftButton");
const statusBox = document.querySelector("#status");
const draftPanel = document.querySelector("#draftPanel");
const evidenceList = document.querySelector("#evidenceList");
const unknownPanel = document.querySelector("#unknownPanel");
const compareButton = document.querySelector("#compareButton");
const comparisonPanel = document.querySelector("#comparisonPanel");
const comparisonSummary = document.querySelector("#comparisonSummary");
const results = document.querySelector("#results");
const explainButton = document.querySelector("#explainButton");
const modelPanel = document.querySelector("#modelPanel");
const modelText = document.querySelector("#modelText");
const modelMeta = document.querySelector("#modelMeta");

let draftState = null;
let allowedCapabilities = [];
let confirmedProfile = null;

const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const splitItems = (value) => value
  .split(/[、，,\n]/)
  .map((item) => item.trim())
  .filter(Boolean);

async function readJson(response) {
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `请求失败：${response.status}`);
  return body;
}

function renderDraft() {
  evidenceList.innerHTML = draftState.evidence.map((item, evidenceIndex) => {
    const chips = item.capabilities.map((capability, capabilityIndex) => `
      <span class="capability">
        ${escapeHtml(capability)}
        <button type="button" class="remove-capability" data-evidence-index="${evidenceIndex}" data-capability-index="${capabilityIndex}" aria-label="删除 ${escapeHtml(capability)}">×</button>
      </span>`).join("");
    const options = allowedCapabilities
      .filter((capability) => !item.capabilities.includes(capability))
      .map((capability) => `<option value="${escapeHtml(capability)}">${escapeHtml(capability)}</option>`)
      .join("");
    return `
      <article class="evidence-card ${item.confirmed ? "confirmed" : ""}" data-evidence-index="${evidenceIndex}">
        <div class="evidence-header">
          <input class="evidence-confirm" type="checkbox" data-evidence-index="${evidenceIndex}" ${item.confirmed ? "checked" : ""}>
          <p class="quote">“${escapeHtml(item.source_quote)}”</p>
        </div>
        <div class="capability-row">${chips || '<span class="warning">尚无能力标签，请补充或不确认此条。</span>'}</div>
        <div class="add-capability">
          <select class="capability-select" data-evidence-index="${evidenceIndex}">
            <option value="">选择要补充的能力……</option>${options}
          </select>
          <button type="button" class="add-capability-button" data-evidence-index="${evidenceIndex}">补充标签</button>
        </div>
      </article>`;
  }).join("");

  const unknowns = draftState.unknowns.length
    ? `<ul>${draftState.unknowns.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
    : "<p>模型没有提出额外未知项，但这不表示信息已经完整。</p>";
  const followUp = draftState.follow_up_question
    ? `<p class="follow-up"><strong>建议下一问：</strong>${escapeHtml(draftState.follow_up_question)}</p>`
    : "";
  unknownPanel.innerHTML = `<h3>仍需补充或验证</h3>${unknowns}${followUp}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  draftButton.disabled = true;
  draftPanel.classList.add("hidden");
  comparisonPanel.classList.add("hidden");
  modelPanel.classList.add("hidden");
  statusBox.textContent = "正在让大模型提取原文证据草稿……";
  try {
    const weeklyValue = document.querySelector("#weeklyHours").value;
    const body = await readJson(await fetch("/api/profile-drafts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        education_field: document.querySelector("#educationField").value,
        education_stage: document.querySelector("#educationStage").value,
        experience_text: document.querySelector("#experienceText").value,
        constraints: {
          locations: splitItems(document.querySelector("#locations").value),
          weekly_learning_hours: weeklyValue ? Number(weeklyValue) : null,
          non_negotiables: splitItems(document.querySelector("#nonNegotiables").value),
        },
        consent_confirmed: document.querySelector("#consent").checked,
      }),
    }));
    draftState = body.profile_draft;
    draftState.evidence = draftState.evidence.map((item) => ({ ...item, confirmed: false }));
    allowedCapabilities = body.allowed_capabilities;
    confirmedProfile = null;
    renderDraft();
    draftPanel.classList.remove("hidden");
    draftPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    statusBox.textContent = "草稿已生成，但尚未成为你的画像；请逐条确认。";
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    draftButton.disabled = false;
  }
});

evidenceList.addEventListener("change", (event) => {
  if (!event.target.matches(".evidence-confirm")) return;
  const index = Number(event.target.dataset.evidenceIndex);
  draftState.evidence[index].confirmed = event.target.checked;
  event.target.closest(".evidence-card").classList.toggle("confirmed", event.target.checked);
});

evidenceList.addEventListener("click", (event) => {
  const removeButton = event.target.closest(".remove-capability");
  if (removeButton) {
    const evidenceIndex = Number(removeButton.dataset.evidenceIndex);
    const capabilityIndex = Number(removeButton.dataset.capabilityIndex);
    draftState.evidence[evidenceIndex].capabilities.splice(capabilityIndex, 1);
    renderDraft();
    return;
  }

  const addButton = event.target.closest(".add-capability-button");
  if (!addButton) return;
  const evidenceIndex = Number(addButton.dataset.evidenceIndex);
  const select = evidenceList.querySelector(`.capability-select[data-evidence-index="${evidenceIndex}"]`);
  if (select.value && !draftState.evidence[evidenceIndex].capabilities.includes(select.value)) {
    draftState.evidence[evidenceIndex].capabilities.push(select.value);
    renderDraft();
  }
});

function buildConfirmedProfile() {
  const evidence = draftState.evidence
    .filter((item) => item.confirmed)
    .map((item) => ({
      source_quote: item.source_quote,
      capabilities: item.capabilities,
      confidence: item.confidence,
      confirmed: true,
    }));
  if (!evidence.length) throw new Error("请至少确认一条证据后再继续。 ");
  if (evidence.some((item) => !item.capabilities.length)) {
    throw new Error("已确认的证据至少需要一个能力标签。 ");
  }
  return {
    profile_confirmed: true,
    consent_recorded: true,
    education: {
      field: draftState.education_field,
      stage: draftState.education_stage,
    },
    evidence,
    constraints: {
      locations: draftState.locations,
      weekly_learning_hours: draftState.weekly_learning_hours,
      non_negotiables: draftState.non_negotiables,
    },
    unknowns: draftState.unknowns,
  };
}

function renderHypothesis(item) {
  const support = item.supporting_evidence
    .map((value) => `<li>${escapeHtml(value.statement)}</li>`).join("");
  const gaps = item.gaps.map((value) => `<li>${escapeHtml(value)}</li>`).join("");
  const unknowns = item.unknowns.map((value) => `<li>${escapeHtml(value)}</li>`).join("");
  const constraints = item.constraint_findings
    .map((value) => `<li class="warning">${escapeHtml(value.explanation)}</li>`).join("");
  return `
    <article class="hypothesis">
      <span class="rank">HYPOTHESIS ${String(item.rank).padStart(2, "0")}</span>
      <h3>${escapeHtml(item.career_name)}</h3>
      <p class="coverage"><strong>${item.evidence_coverage_percent}%</strong> 证据覆盖率</p>
      <h4>来自你确认的证据</h4><ul>${support}</ul>
      <h4>缺口</h4><ul>${gaps || "<li>仍需用真实任务验证，而不是据此判断胜任。</li>"}</ul>
      <h4>未知与约束</h4><ul>${unknowns}${constraints}</ul>
      <h4>下一项验证行动</h4><p class="action">${escapeHtml(item.validation_action)}</p>
      <button type="button" class="resume-handoff" data-career-id="${escapeHtml(item.career_id)}">按这个方向修改简历 →</button>
    </article>`;
}

compareButton.addEventListener("click", async () => {
  compareButton.disabled = true;
  modelPanel.classList.add("hidden");
  statusBox.textContent = "正在用确定性规则比较确认后的证据……";
  try {
    confirmedProfile = buildConfirmedProfile();
    const run = await readJson(await fetch("/api/career-comparisons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: confirmedProfile, maximum_hypotheses: 3 }),
    }));
    comparisonPanel.classList.remove("hidden");
    comparisonSummary.textContent = run.hypotheses.length
      ? `比较了 ${run.considered_career_ids.length} 个职业方向，返回 ${run.hypotheses.length} 个可修订假设。百分比仅表示已确认经历对预设能力组的覆盖。`
      : `比较了 ${run.considered_career_ids.length} 个职业方向，但现有证据不足以形成职业假设。可以补充一件更具体的经历，而不是强行推荐。`;
    results.innerHTML = run.hypotheses.length
      ? run.hypotheses.map(renderHypothesis).join("")
      : '<article class="panel"><p>当前没有达到最低证据门槛的方向。请回到第一步补充包含具体行动和结果的经历。</p></article>';
    explainButton.disabled = !run.hypotheses.length;
    comparisonPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    statusBox.textContent = "比较完成；排序由确定性代码生成。";
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    compareButton.disabled = false;
  }
});

explainButton.addEventListener("click", async () => {
  explainButton.disabled = true;
  statusBox.textContent = "正在请求受约束的大模型解释……";
  modelPanel.classList.add("hidden");
  try {
    const body = await readJson(await fetch("/api/career-explanations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: confirmedProfile, maximum_hypotheses: 3 }),
    }));
    modelText.textContent = body.explanation.text;
    modelMeta.textContent = `模型角色：${body.explanation.model_role} · 已核对证据：${body.explanation.cited_evidence_ids.join("、")}`;
    modelPanel.classList.remove("hidden");
    statusBox.textContent = "解释已通过安全门；它没有改变排序或证据覆盖率。";
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    explainButton.disabled = false;
  }
});

results.addEventListener("click", (event) => {
  const button = event.target.closest(".resume-handoff");
  if (!button || !confirmedProfile) return;
  const resumeEvidence = confirmedProfile.evidence.map((item) => item.source_quote).join("\n");
  sessionStorage.setItem("careerResumeEvidence", resumeEvidence);
  window.location.href = `/demo/resume-beta/index.html?career_id=${encodeURIComponent(button.dataset.careerId)}`;
});
