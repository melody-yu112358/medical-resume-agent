const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

let currentExperienceDraft = null;
let currentCanonicalExperience = null;
let selectedRolePacks = ['doctoral_v1', 'clinical_research_v1', 'medical_affairs_v1', 'health_ai_data_v1'];
let generatedBullets = {};

const SAMPLE_EXPERIENCES = Object.freeze({
  meta: `在导师指导下参与某疾病风险因素与临床结局的 Meta 分析。使用 PubMed、Embase 检索文献，按预设入排标准完成文献筛选与数据提取；使用 R 进行效应量合并和敏感性分析，整理结果图表并参与组会汇报。`,
  wetLab: `在课题组参与炎症相关细胞实验。负责细胞培养、RNA 提取和 qPCR 检测，记录原始实验数据并协助整理结果图表；在导师指导下参与组会讨论。`,
  casePresentation: `参加院内临床病例汇报比赛，围绕一例不明原因发热病例，查阅指南和文献，梳理鉴别诊断、检查结果和诊疗思路，制作病例汇报材料并完成现场汇报。`,
});

$$('.sample-button').forEach((button) => {
  button.addEventListener('click', () => {
    const sample = SAMPLE_EXPERIENCES[button.dataset.sample];
    if (!sample) return;
    $('#experienceInput').value = sample;
    $('#experienceInput').focus();
    $('#step1Error').textContent = '';
  });
});

// Utility functions
function esc(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[character]));
}

function showStep(stepNumber) {
  // Hide all steps
  $$('.step-section').forEach(section => section.classList.add('hidden'));
  // Show current step
  $(`#step${stepNumber}`).classList.remove('hidden');
  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Step 1: Extract Facts
$('#extractFacts').onclick = async () => {
  const experienceText = $('#experienceInput').value.trim();
  const contextHint = $('#contextHint').value.trim();
  const consentChecked = $('#consent').checked;
  const errorElement = $('#step1Error');

  errorElement.textContent = '';

  if (!consentChecked) {
    errorElement.textContent = '请先确认隐私提示。';
    return;
  }

  if (!experienceText) {
    errorElement.textContent = '请输入你的医学经历。';
    return;
  }

  const button = $('#extractFacts');
  button.disabled = true;
  button.textContent = '正在提取事实...';

  try {
    const response = await fetch('/api/experience-drafts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        experience_text: experienceText,
        context_hint: contextHint || undefined,
        consent_confirmed: true
      })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || '提取事实失败');
    }

    currentExperienceDraft = data;
    renderExtractedFacts(data);
    showStep(2);
  } catch (error) {
    errorElement.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = '提取事实 →';
  }
};

function renderExtractedFacts(draft) {
  const facts = draft.extracted_facts;

  // Context
  const contextHtml = `
    <p><strong>领域:</strong> ${esc(facts.context.domain || '未指定')}</p>
    <p><strong>场景:</strong> ${esc(facts.context.setting || '未指定')}</p>
    ${facts.context.topic ? `<p><strong>主题:</strong> ${esc(facts.context.topic)}</p>` : ''}
  `;
  $('#contextDisplay').innerHTML = contextHtml;

  // Role
  const roleHtml = `
    <p><strong>职位:</strong> ${facts.role.title ? esc(facts.role.title) : '未指定'}</p>
    <p><strong>责任等级:</strong> ${getResponsibilityLabel(facts.role.responsibility_level)}</p>
  `;
  $('#roleDisplay').innerHTML = roleHtml;

  // Actions
  $('#actionsDisplay').innerHTML = facts.actions.length > 0
    ? facts.actions.map(action => `<span class="fact-tag">${esc(getActionLabel(action))}</span>`).join(' ')
    : '<em>未识别到行动</em>';

  // Methods
  $('#methodsDisplay').innerHTML = facts.methods.length > 0
    ? facts.methods.map(method => `<span class="fact-tag">${esc(getMethodLabel(method))}</span>`).join(' ')
    : '<em>未识别到方法</em>';

  // Tools
  $('#toolsDisplay').innerHTML = facts.tools.length > 0
    ? facts.tools.map(tool => `<span class="fact-tag">${esc(getToolLabel(tool))}</span>`).join(' ')
    : '<em>未识别到工具</em>';

  // Laboratory techniques
  $('#techniquesDisplay').innerHTML = facts.techniques && facts.techniques.length > 0
    ? facts.techniques.map(technique => `<span class="fact-tag">${esc(getTechniqueLabel(technique))}</span>`).join(' ')
    : '<em>未识别到实验技术</em>';

  // Objects
  $('#objectsDisplay').innerHTML = facts.objects.length > 0
    ? facts.objects.map(obj => `<span class="fact-tag">${esc(getObjectLabel(obj))}</span>`).join(' ')
    : '<em>未识别到对象</em>';

  // Collaboration
  $('#collaborationDisplay').innerHTML = facts.collaboration.length > 0
    ? facts.collaboration.map(collab => `<span class="fact-tag">${esc(getCollaborationLabel(collab))}</span>`).join(' ')
    : '<em>未识别到协作</em>';

  // Artifacts
  $('#artifactsDisplay').innerHTML = facts.artifacts.length > 0
    ? facts.artifacts.map(artifact => `<span class="fact-tag">${esc(getArtifactLabel(artifact))}</span>`).join(' ')
    : '<em>未识别到产出物</em>';

  // Outcomes
  $('#outcomesDisplay').innerHTML = facts.outcomes.length > 0
    ? facts.outcomes.map(outcome => `<span class="fact-tag">${esc(outcome)}</span>`).join(' ')
    : '<em>未识别到结果</em>';

  // Scope
  $('#scopeDisplay').innerHTML = Object.keys(facts.scope).length > 0
    ? Object.entries(facts.scope).map(([key, value]) => `<p><strong>${esc(key)}:</strong> ${esc(value)}</p>`).join('')
    : '<em>未识别到范围信息</em>';

  // Value angles
  $('#valueAnglesDisplay').innerHTML = draft.possible_value_angles.length > 0
    ? draft.possible_value_angles.map(angle => `<p>• ${esc(angle)}</p>`).join('')
    : '<p><em>暂无价值角度建议</em></p>';

  // Risk flags
  $('#riskFlagsDisplay').innerHTML = draft.risk_flags.length > 0
    ? draft.risk_flags.map(flag => `<p>⚠️ ${esc(flag)}</p>`).join('')
    : '<p><em>无风险提示</em></p>';
}

function getResponsibilityLabel(level) {
  const labels = {
    'participated': '参与/协助',
    'owned_component': '负责特定任务',
    'led_delivery': '主导交付',
    'project_owner': '项目负责人',
    'unknown': '未知'
  };
  return labels[level] || level;
}

function getActionLabel(action) {
  const labels = {
    'retrieve_literature': '文献检索',
    'screen_studies': '研究筛选',
    'extract_data': '数据提取',
    'create_flowchart': '流程图制作',
    'perform_analysis': '数据分析',
    'write_manuscript': '论文撰写',
    'culture_cells': '细胞培养',
    'perform_qpcr': 'qPCR 检测',
    'perform_western_blot': 'Western Blot 检测',
    'review_clinical_case': '病例分析',
    'prepare_case_presentation': '病例汇报准备',
    'retrieve_guidelines': '指南检索'
  };
  return labels[action] || action;
}

function getMethodLabel(method) {
  const labels = {
    'systematic_review': '系统综述',
    'meta_analysis': 'Meta分析',
    'mendelian_randomization': '孟德尔随机化（MR）',
    'randomized_trial': '随机对照试验',
    'cohort_study': '队列研究',
    'case_control': '病例对照研究'
  };
  return labels[method] || method;
}

function getToolLabel(tool) {
  const labels = {
    r: 'R', python: 'Python', spss: 'SPSS', sql: 'SQL',
    pubmed: 'PubMed', embase: 'Embase', cochrane: 'Cochrane',
    graphpad_prism: 'GraphPad Prism',
  };
  return labels[tool] || tool;
}

function getTechniqueLabel(technique) {
  const labels = {
    cell_culture: '细胞培养', qpcr: 'qPCR', western_blot: 'Western Blot',
    flow_cytometry: '流式细胞术', elisa: 'ELISA', animal_experiment: '动物实验',
  };
  return labels[technique] || technique;
}

function getObjectLabel(obj) {
  const labels = {
    'medical_literature': '医学文献',
    'clinical_studies': '临床研究',
    'research_data': '研究数据',
    'clinical_case': '临床病例',
    'laboratory_samples': '实验样本',
  };
  return labels[obj] || obj;
}

function getCollaborationLabel(collab) {
  const labels = {
    'research_team': '研究团队',
    'supervisor': '导师'
  };
  return labels[collab] || collab;
}

function getArtifactLabel(artifact) {
  const labels = {
    'prisma_flowchart': 'PRISMA流程图',
    'data_extraction_sheet': '数据提取表',
    'research_paper': '研究论文',
    'case_presentation_material': '病例汇报材料',
  };
  return labels[artifact] || artifact;
}

// Step 2 Navigation
$('#proceedToQuestions').onclick = () => {
  renderQuestions();
  showStep(3);
};

$('#backToStep1').onclick = () => {
  showStep(1);
};

// Step 3: Render Questions
function renderQuestions() {
  const questions = currentExperienceDraft.clarifying_questions;
  if (questions.length === 0) {
    $('#questionsContainer').innerHTML = '<p>无需额外问题，可以直接确认经历。</p>';
    return;
  }

  const questionsHtml = questions.map((question, index) => `
    <div class="question-item">
      <label><strong>${index + 1}. ${esc(question)}</strong></label>
      <input type="text" data-question-index="${index}" placeholder="请输入真实可核实的事实..." />
    </div>
  `).join('');

  $('#questionsContainer').innerHTML = questionsHtml;
}

// Step 3 Navigation
$('#confirmExperience').onclick = () => {
  const confirmedFacts = [];
  $$('.question-item input').forEach(input => {
    const value = input.value.trim();
    if (value) {
      confirmedFacts.push(value);
    }
  });

  // Create evidence records
  const evidenceRecords = [{
    evidence_id: 'ev_001',
    source_text: $('#experienceInput').value.trim(),
    status: 'confirmed'
  }];

  // Create user actions
  const userActions = {
    disposition: 'accept',
    confirmed_facts: confirmedFacts
  };

  confirmExperienceWithBackend(userActions, evidenceRecords);
};

$('#backToStep2').onclick = () => {
  showStep(2);
};

// Step 4: Confirmation
async function confirmExperienceWithBackend(userActions, evidenceRecords) {
  const errorElement = $('#step3Error');
  errorElement.textContent = '';

  const button = $('#confirmExperience');
  button.disabled = true;
  button.textContent = '正在确认...';

  try {
    const response = await fetch('/api/experience-confirmations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        experience_draft: currentExperienceDraft,
        user_actions: userActions,
        evidence_records: evidenceRecords,
        previous_experience_id: null
      })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || '确认经历失败');
    }

    if (data.canonical_experience) {
      currentCanonicalExperience = data.canonical_experience;

      // Check confirmation status
      if (data.confirmation_status.status === 'needs_more_info') {
        errorElement.textContent = data.confirmation_status.validation_errors.join('; ');
        button.disabled = false;
        button.textContent = '确认经历 →';
        return;
      }

      showStep(5); // Skip step 4 if directly accepted
    } else {
      showStep(4); // Show modification options
    }
  } catch (error) {
    errorElement.textContent = error.message;
    button.disabled = false;
    button.textContent = '确认经历 →';
  }
}

// Step 4: Handle confirmation options
$('#acceptExperience').onclick = () => {
  const evidenceRecords = [{
    evidence_id: 'ev_001',
    source_text: $('#experienceInput').value.trim(),
    status: 'confirmed'
  }];

  const userActions = {
    disposition: 'accept'
  };

  confirmExperienceWithBackend(userActions, evidenceRecords);
};

$('#modifyExperience').onclick = () => {
  const responsibilityLevel = $('#responsibilityLevel').value;
  const newEvidence = $('#newEvidence').value.trim();

  const evidenceRecords = [{
    evidence_id: 'ev_001',
    source_text: $('#experienceInput').value.trim(),
    status: 'confirmed'
  }];

  if (newEvidence) {
    evidenceRecords.push({
      evidence_id: 'ev_002',
      source_text: newEvidence,
      status: 'confirmed'
    });
  }

  const userActions = {
    disposition: 'accept',
    modified_facts: {
      'role.responsibility_level': responsibilityLevel
    },
    new_evidence: newEvidence
  };

  const errorElement = $('#step4Error');
  errorElement.textContent = '';

  if (responsibilityLevel !== 'participated' && !newEvidence) {
    errorElement.textContent = '升级责任等级需要提供新的证据支持。';
    return;
  }

  confirmExperienceWithBackend(userActions, evidenceRecords);
};

$('#rejectExperience').onclick = () => {
  const evidenceRecords = [{
    evidence_id: 'ev_001',
    source_text: $('#experienceInput').value.trim(),
    status: 'confirmed'
  }];

  const userActions = {
    disposition: 'reject'
  };

  confirmExperienceWithBackend(userActions, evidenceRecords);
};

// Step 5: Role Pack Selection
$$('#role-pack-selector .role-pack-card').forEach(card => {
  card.onclick = () => {
    card.classList.toggle('selected');
    const rolePack = card.dataset.rolePack;
    if (card.classList.contains('selected')) {
      if (!selectedRolePacks.includes(rolePack)) {
        selectedRolePacks.push(rolePack);
      }
    } else {
      selectedRolePacks = selectedRolePacks.filter(rp => rp !== rolePack);
    }
  };
});

$('#generateBullets').onclick = () => {
  if (selectedRolePacks.length === 0) {
    $('#step5Error').textContent = '请至少选择一个目标岗位方向。';
    return;
  }

  generateBulletsForSelectedRoles();
};

// Step 6: Generate Bullets
async function generateBulletsForSelectedRoles() {
  const errorElement = $('#step5Error');
  errorElement.textContent = '';

  const button = $('#generateBullets');
  button.disabled = true;
  button.textContent = '正在生成要点...';

  try {
    generatedBullets = {};

    for (const rolePack of selectedRolePacks) {
      const response = await fetch('/api/bullet-composer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          canonical_experience: currentCanonicalExperience,
          role_pack_name: rolePack
        })
      });

      const bullets = await response.json();
      if (!response.ok) {
        throw new Error(`生成 ${rolePack} 要点失败: ${bullets.error || '未知错误'}`);
      }

      generatedBullets[rolePack] = bullets;
    }

    renderBulletsPreview();
    showStep(6);
  } catch (error) {
    errorElement.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = '生成简历要点 →';
  }
}

function renderBulletsPreview() {
  let bulletsHtml = '';

  Object.entries(generatedBullets).forEach(([rolePack, bullets]) => {
    const rolePackLabels = {
      'doctoral_v1': '考博 / 保研',
      'clinical_research_v1': '临床科研',
      'medical_affairs_v1': 'MSL / 医学事务',
      'health_ai_data_v1': '医疗数据 / 健康科技'
    };

    bulletsHtml += `<div class="bullet-category">
      <h3>${rolePackLabels[rolePack] || rolePack}</h3>
      ${bullets.map(bullet => `
        <div class="bullet-item">
          <p>${esc(bullet.wording)}</p>
        </div>
      `).join('')}
    </div>`;
  });

  $('#bulletsContainer').innerHTML = bulletsHtml;
}

// Step 6 Navigation
$('#reviewBullets').onclick = () => {
  renderBulletDetails();
  showStep(7);
};

$('#backToRoleSelection').onclick = () => {
  showStep(5);
};

// Step 7: Bullet Details
function renderBulletDetails() {
  let detailsHtml = '';

  Object.entries(generatedBullets).forEach(([rolePack, bullets]) => {
    const rolePackLabels = {
      'doctoral_v1': '考博 / 保研',
      'clinical_research_v1': '临床科研',
      'medical_affairs_v1': 'MSL / 医学事务',
      'health_ai_data_v1': '医疗数据 / 健康科技'
    };

    detailsHtml += `<div class="bullet-category">
      <h3>${rolePackLabels[rolePack] || rolePack}</h3>
      ${bullets.map(bullet => `
        <div class="bullet-item">
          <h4>要点内容</h4>
          <p>${esc(bullet.wording)}</p>

          <h4>使用的事实</h4>
          <p>${bullet.used_facts.length > 0
            ? bullet.used_facts.map(fact => `<span class="fact-tag">${esc(fact)}</span>`).join(' ')
            : '<em>无</em>'}</p>

          <h4>证据引用</h4>
          <p>${bullet.evidence_ids.length > 0
            ? bullet.evidence_ids.map(id => `<code>${esc(id)}</code>`).join(', ')
            : '<em>无</em>'}</p>

          <h4>责任等级</h4>
          <p>${getResponsibilityLabel(bullet.responsibility_level)}</p>

          <h4>省略的未知项</h4>
          <p>${bullet.omitted_unknowns.length > 0
            ? bullet.omitted_unknowns.map(unknown => `<span class="fact-tag">${esc(unknown)}</span>`).join(' ')
            : '<em>无</em>'}</p>

          <h4>风险提示</h4>
          <p>${bullet.risk_flags.length > 0
            ? bullet.risk_flags.map(flag => `<p class="risk-flag">⚠️ ${esc(flag)}</p>`).join('')
            : '<em>无风险</em>'}</p>
        </div>
      `).join('')}
    </div>`;
  });

  $('#bulletDetailsContainer').innerHTML = detailsHtml;
}

// Step 7 Navigation
$('#finalizeBullets').onclick = () => {
  renderFinalBullets();
  showStep(8);
};

$('#backToBullets').onclick = () => {
  showStep(6);
};

// Step 8: Final Bullets
function renderFinalBullets() {
  let finalHtml = '';

  Object.entries(generatedBullets).forEach(([rolePack, bullets]) => {
    const rolePackLabels = {
      'doctoral_v1': '考博 / 保研',
      'clinical_research_v1': '临床科研',
      'medical_affairs_v1': 'MSL / 医学事务',
      'health_ai_data_v1': '医疗数据 / 健康科技'
    };

    finalHtml += `<div class="bullet-category">
      <h3>${rolePackLabels[rolePack] || rolePack}</h3>
      ${bullets.map((bullet, index) => `
        <div class="bullet-item">
          <p>${esc(bullet.wording)}</p>
          <input type="hidden" name="bullet-${rolePack}-${index}" value="${esc(bullet.wording)}" />
        </div>
      `).join('')}
    </div>`;
  });

  $('#finalBulletsContainer').innerHTML = finalHtml;
}

// Step 8 Actions
$('#acceptBullets').onclick = () => {
  showStep(9);
};

$('#editBullets').onclick = () => {
  alert('编辑功能将在后续版本中实现。');
};

$('#rejectBullets').onclick = () => {
  if (confirm('确定要拒绝这些要点吗？')) {
    showStep(1);
    // Reset form
    $('#experienceInput').value = '';
    $('#contextHint').value = '';
    $('#consent').checked = false;
    currentExperienceDraft = null;
    currentCanonicalExperience = null;
    generatedBullets = {};
    selectedRolePacks = ['doctoral_v1', 'clinical_research_v1', 'medical_affairs_v1', 'health_ai_data_v1'];
    $$('#role-pack-selector .role-pack-card').forEach(card => {
      card.classList.add('selected');
    });
  }
};

// Step 9: Completion
$('#startNewExperience').onclick = () => {
  showStep(1);
  // Reset form
  $('#experienceInput').value = '';
  $('#contextHint').value = '';
  $('#consent').checked = false;
  currentExperienceDraft = null;
  currentCanonicalExperience = null;
  generatedBullets = {};
  selectedRolePacks = ['doctoral_v1', 'clinical_research_v1', 'medical_affairs_v1', 'health_ai_data_v1'];
  $$('#role-pack-selector .role-pack-card').forEach(card => {
    card.classList.add('selected');
  });
};

$('#copyAllBullets').onclick = () => {
  let allBullets = '';

  Object.entries(generatedBullets).forEach(([rolePack, bullets]) => {
    const rolePackLabels = {
      'doctoral_v1': '考博 / 保研',
      'clinical_research_v1': '临床科研',
      'medical_affairs_v1': 'MSL / 医学事务',
      'health_ai_data_v1': '医疗数据 / 健康科技'
    };

    allBullets += `${rolePackLabels[rolePack] || rolePack}:\n`;
    bullets.forEach(bullet => {
      allBullets += `• ${bullet.wording}\n`;
    });
    allBullets += '\n';
  });

  navigator.clipboard.writeText(allBullets).then(() => {
    alert('所有要点已复制到剪贴板！');
  }).catch(err => {
    console.error('复制失败:', err);
    alert('复制失败，请手动复制。');
  });
};

$('#downloadBullets').onclick = () => {
  let content = '医学经历编译器 - 简历要点\n\n';

  Object.entries(generatedBullets).forEach(([rolePack, bullets]) => {
    const rolePackLabels = {
      'doctoral_v1': '考博 / 保研',
      'clinical_research_v1': '临床科研',
      'medical_affairs_v1': 'MSL / 医学事务',
      'health_ai_data_v1': '医疗数据 / 健康科技'
    };

    content += `${rolePackLabels[rolePack] || rolePack}:\n`;
    bullets.forEach(bullet => {
      content += `• ${bullet.wording}\n`;
    });
    content += '\n';
  });

  content += '\n提示：所有事实须本人核实。';

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '医学经历编译器-简历要点.txt';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

// Initialize
showStep(1);
