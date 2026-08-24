const storageKey = 'unbounded.xhs-medical-experience-lite.v1';
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const samples = {
  meta: '在导师指导下参与某疾病风险因素与临床结局的 Meta 分析，使用 PubMed、Embase 检索文献，按预设入排标准完成文献筛选与数据提取；使用 R 进行效应量合并和敏感性分析，整理结果图表并参与组会汇报。',
  wetlab: '在课题组参与炎症相关细胞实验，负责细胞培养、RNA 提取和 qPCR 检测，记录原始实验数据并协助整理结果图表；在导师指导下参与组会讨论。',
  case: '参加院内临床病例汇报比赛，围绕一例不明原因发热病例，查阅指南和文献，梳理鉴别诊断、检查结果和诊疗思路，制作病例汇报材料并完成现场汇报。',
};

const capabilityGroups = [
  { title: '研究设计与方法', items: ['队列研究', 'RCT', 'Meta 分析', '孟德尔随机化（MR）', 'GWAS', '生物信息', '机器学习'] },
  { title: '数据与工具', items: ['R', 'Python', 'SPSS', 'SQL', '数据清洗', '统计分析', '可视化'] },
  { title: '临床研究设计与执行', items: ['入排标准', '随访', 'CRF', '伦理', 'GCP', '真实世界研究', '数据质控'] },
  { title: '实验技术', items: ['细胞培养', 'qPCR', 'Western Blot', '流式细胞术', 'ELISA', '动物实验'] },
  { title: '医学证据与信息', items: ['PubMed', 'Embase', 'Cochrane', '指南解读', '证据分级', '医学写作'] },
];

const roleProfiles = {
  academic: { title: '升学与科研申请', focus: '研究问题、方法深度与科研潜力', frame: '先交代研究问题或疾病领域，再说明你使用的方法、工具或实验技术、本人实际负责的环节，以及论文、报告或汇报等已确认产出。' },
  clinical: { title: '临床研究与医院科研', focus: '临床问题、研究执行与协作', frame: '优先写临床问题或研究设计、你负责的数据/流程环节，以及如何支持研究执行或结果解释。' },
  msl: { title: '医学事务 / MSL', focus: '证据解读、疾病领域与医学沟通', frame: '突出疾病领域材料的检索、解读和整合，以及汇报材料、病例讨论或医学信息沟通等真实交付。' },
  data: { title: '医疗数据与数字健康', focus: '数据流程、分析框架与结果沟通', frame: '优先说明数据来源、清洗或分析方法、结果图表/可视化，以及你如何把分析结果用于研究讨论。' },
};

function renderCapabilityGroups() {
  $('#capabilityGroups').innerHTML = capabilityGroups.map((group) => `
    <div class="capability-group"><h3>${group.title}</h3><div class="chips">
      ${group.items.map((item) => `<button type="button" class="chip" data-capability="${item}" aria-pressed="false">${item}</button>`).join('')}
    </div></div>`).join('');
}

function selectedValues(selector, key) {
  return $$(selector).filter((node) => node.getAttribute('aria-pressed') === 'true').map((node) => node.dataset[key]);
}

function saveDraft() {
  localStorage.setItem(storageKey, JSON.stringify({
    experience: $('#experienceInput').value,
    topic: $('#topicInput').value,
    responsibility: $('#responsibilityInput').value,
    deliverable: $('#deliverableInput').value,
    roles: selectedValues('.role-card', 'role'),
    capabilities: selectedValues('.chip', 'capability'),
  }));
}

function restoreDraft() {
  try {
    const draft = JSON.parse(localStorage.getItem(storageKey) || '{}');
    $('#experienceInput').value = draft.experience || '';
    $('#topicInput').value = draft.topic || '';
    $('#responsibilityInput').value = draft.responsibility || '';
    $('#deliverableInput').value = draft.deliverable || '';
    (draft.roles || []).forEach((role) => setPressed(`.role-card[data-role="${role}"]`, true));
    (draft.capabilities || []).forEach((capability) => setPressed(`.chip[data-capability="${capability}"]`, true));
  } catch (_) { localStorage.removeItem(storageKey); }
}

function setPressed(selector, pressed) {
  const node = $(selector);
  if (!node) return;
  node.setAttribute('aria-pressed', String(pressed));
  node.classList.toggle('selected', pressed);
}

function detectedCapabilities(text, selected) {
  return capabilityGroups.flatMap((group) => group.items).filter((item) => selected.includes(item) || mentionsCapability(text, item));
}

function mentionsCapability(text, item) {
  if (item === 'R') return /(?:\bR\b|R语言|使用\s*R|用\s*R|基于\s*R)/i.test(text);
  return text.toLowerCase().includes(item.toLowerCase());
}

function buildQuestions(text, capabilities) {
  const questions = [];
  if (!/疾病|患者|细胞|样本|队列|病例|临床|数据库/.test(text)) questions.push('这段经历研究或处理的对象是什么？例如疾病领域、患者队列、细胞/样本或临床病例。');
  if (!/负责|完成|独立|协助|参与|整理|筛选|分析|制作/.test(text)) questions.push('你亲自负责了哪几个环节？请区分“参与讨论”和实际完成的任务。');
  if (!/论文|报告|汇报|图表|材料|海报|结果/.test(text)) questions.push('是否有可以确认的交付物？例如结果图表、组会汇报、病例材料、研究报告或论文状态。');
  if (capabilities.length === 0) questions.push('你实际使用过哪些方法、软件、实验技术或研究流程？只填写能解释清楚的项目。');
  return questions.slice(0, 3);
}

function renderResults() {
  const text = $('#experienceInput').value.trim();
  const roles = selectedValues('.role-card', 'role');
  const capabilities = detectedCapabilities(text, selectedValues('.chip', 'capability'));
  if (!text) { $('#status').textContent = '请先写下一段真实经历。'; return; }
  if (!roles.length) { $('#status').textContent = '请至少选择一个目标方向。'; return; }
  saveDraft();
  $('#status').textContent = '已保存在本机。以下内容仅基于你的输入和选择生成。';
  $('#factSummary').innerHTML = `<p class="source">${escapeHtml(text)}</p><div class="tag-list">${capabilities.length ? capabilities.map((item) => `<span>${escapeHtml(item)}</span>`).join('') : '<em>尚未识别到明确的方法或工具；可在上方手动补充。</em>'}</div>`;
  const questions = buildQuestions(text, capabilities);
  $('#questions').innerHTML = questions.length ? questions.map((item) => `<li>${escapeHtml(item)}</li>`).join('') : '<li>信息已经较完整。请复核时间线、个人责任与产出是否均为本人可确认的事实。</li>';
  $('#roleOutput').innerHTML = roles.map((role) => {
    const profile = roleProfiles[role];
    return `<article class="role-output"><h3>${profile.title}</h3><p><b>优先呈现：</b>${profile.focus}</p><textarea class="candidate-draft" data-candidate-role="${role}" rows="5">${escapeHtml(composeCandidate(role, capabilities))}</textarea><p class="frame">${profile.frame}</p></article>`;
  }).join('');
  $('#results').classList.remove('hidden');
  $('#results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function capabilityText(capabilities, groupIndex, fallback) {
  const items = capabilityGroups[groupIndex].items.filter((item) => capabilities.includes(item));
  return items.length ? items.join('、') : fallback;
}

function composeCandidate(role, capabilities) {
  const topic = $('#topicInput').value.trim() || '【待补充研究对象或问题】';
  const responsibility = $('#responsibilityInput').value.trim() || '【待补充本人实际负责的环节】';
  const deliverable = $('#deliverableInput').value.trim() || '【待补充可确认交付物】';
  const methods = capabilityText(capabilities, 0, '');
  const tools = capabilityText(capabilities, 1, '');
  const techniques = capabilityText(capabilities, 3, '');
  const evidence = capabilityText(capabilities, 4, '【待补充证据来源或解读材料】');
  const approach = describeApproach(methods, tools, techniques);
  const candidates = {
    academic: `围绕${topic}，${approach}开展研究；负责${responsibility}，形成${deliverable}。`,
    clinical: `围绕${topic}参与研究执行，负责${responsibility}；${approach}完成相关分析、实验或资料整理，形成${deliverable}。`,
    msl: `围绕${topic}，基于${evidence}开展医学材料检索、解读或整合；负责${responsibility}，形成${deliverable}。`,
    data: `围绕${topic}，${approach}完成研究数据处理、分析或可视化；负责${responsibility}，形成${deliverable}。`,
  };
  return candidates[role];
}

function describeApproach(methods, tools, techniques) {
  const parts = [];
  if (methods) parts.push(`采用${methods}`);
  if (tools) parts.push(`使用${tools}`);
  if (techniques) parts.push(`开展${techniques}等实验操作`);
  return parts.length ? parts.join('，并') : '【待补充研究方法、工具或实验技术】';
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
}

renderCapabilityGroups();
restoreDraft();

$$('[data-sample]').forEach((button) => button.addEventListener('click', () => {
  $('#experienceInput').value = samples[button.dataset.sample] || '';
  $('#experienceInput').focus();
  saveDraft();
}));

document.addEventListener('click', (event) => {
  const button = event.target.closest('.role-card, .chip');
  if (!button) return;
  const pressed = button.getAttribute('aria-pressed') === 'true';
  button.setAttribute('aria-pressed', String(!pressed));
  button.classList.toggle('selected', !pressed);
  saveDraft();
});
['#experienceInput', '#topicInput', '#responsibilityInput', '#deliverableInput'].forEach((selector) => $(selector).addEventListener('input', saveDraft));
$('#analyseButton').addEventListener('click', renderResults);
$('#resetButton').addEventListener('click', () => {
  if (!confirm('确定清空这台设备上的本机草稿吗？')) return;
  localStorage.removeItem(storageKey);
  $('#experienceInput').value = '';
  $('#topicInput').value = '';
  $('#responsibilityInput').value = '';
  $('#deliverableInput').value = '';
  $$('.role-card, .chip').forEach((node) => { node.setAttribute('aria-pressed', 'false'); node.classList.remove('selected'); });
  $('#results').classList.add('hidden');
  $('#status').textContent = '本机草稿已清空。';
});
