const select = document.querySelector("#profileSelect");
const button = document.querySelector("#compareButton");
const explainButton = document.querySelector("#explainButton");
const statusBox = document.querySelector("#status");
const summary = document.querySelector("#summary");
const results = document.querySelector("#results");
const modelPanel = document.querySelector("#modelPanel");
const modelText = document.querySelector("#modelText");
const modelMeta = document.querySelector("#modelMeta");

const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

async function readJson(response) {
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `请求失败：${response.status}`);
  return body;
}

async function loadProfiles() {
  try {
    const profiles = await readJson(await fetch("/api/profiles"));
    select.innerHTML = profiles.map((profile) => {
      const label = `${profile.education.field} · ${profile.education.stage} · ${profile.profile_id}`;
      return `<option value="${escapeHtml(profile.profile_id)}">${escapeHtml(label)}</option>`;
    }).join("");
    select.disabled = false;
    button.disabled = false;
    statusBox.textContent = "后端连接成功。请选择合成画像。";
  } catch (error) {
    statusBox.textContent = `无法连接后端：${error.message}`;
  }
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
      <h2>${escapeHtml(item.career_name)}</h2>
      <p class="coverage"><strong>${item.evidence_coverage_percent}%</strong> 证据覆盖率 · ${escapeHtml(item.scoring_version)}</p>
      <h3>来自画像的支持证据</h3><ul>${support}</ul>
      <h3>缺口</h3><ul>${gaps || "<li>当前能力组均有部分证据，但仍不等于岗位胜任。</li>"}</ul>
      <h3>未知与约束</h3><ul>${unknowns}${constraints}</ul>
      <h3>下一项验证行动</h3><p class="action">${escapeHtml(item.validation_action)}</p>
    </article>`;
}

async function compareProfile() {
  button.disabled = true;
  statusBox.textContent = "正在运行确定性比较……";
  results.innerHTML = "";
  summary.classList.add("hidden");
  modelPanel.classList.add("hidden");
  explainButton.disabled = true;
  try {
    const run = await readJson(await fetch("/api/career-comparisons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile_id: select.value, maximum_hypotheses: 3 }),
    }));
    summary.textContent = `比较了 ${run.considered_career_ids.length} 个职业方向，返回 ${run.hypotheses.length} 个可修订假设。百分比仅表示已记录证据对预设能力组的覆盖。`;
    summary.classList.remove("hidden");
    results.innerHTML = run.hypotheses.map(renderHypothesis).join("");
    statusBox.textContent = "比较完成；结果由确定性代码生成，没有调用大模型。";
    explainButton.disabled = false;
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function explainProfile() {
  explainButton.disabled = true;
  statusBox.textContent = "正在请求受约束的大模型解释……";
  modelPanel.classList.add("hidden");
  try {
    const body = await readJson(await fetch("/api/career-explanations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile_id: select.value, maximum_hypotheses: 3 }),
    }));
    modelText.textContent = body.explanation.text;
    modelMeta.textContent = `模型角色：${body.explanation.model_role} · 安全门：${body.explanation.quality_gate_version} · 已核对证据：${body.explanation.cited_evidence_ids.join("、")}`;
    modelPanel.classList.remove("hidden");
    statusBox.textContent = "模型解释已通过后端安全门；排序和证据仍来自确定性代码。";
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    explainButton.disabled = false;
  }
}

button.addEventListener("click", compareProfile);
explainButton.addEventListener("click", explainProfile);
loadProfiles();
