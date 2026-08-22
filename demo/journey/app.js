const questions = [
  {
    title: "现在最困住你的，比较像哪一种？",
    options: [
      { id: "scorecard", label: "我习惯只用论文、学历和成果评价自己" },
      { id: "translation", label: "我不知道医学经历在市场上能换成什么价值" },
      { id: "adjacent", label: "我想看看临床或科研之外还有哪些相邻选择" },
      { id: "browse", label: "还说不清，只想先看一眼" }
    ]
  },
  {
    title: "哪一类经历最值得被重新解释？",
    options: [
      { id: "research", label: "做科研：检索、分析、实验或写作" },
      { id: "clinical", label: "做临床：问诊、判断、解释或随访" },
      { id: "coordination", label: "推进协作：组织、沟通或解决卡点" },
      { id: "learning", label: "自我学习：快速进入陌生领域并产出" }
    ]
  },
  {
    title: "看完线索后，你愿意给探索多少空间？",
    options: [
      { id: "pause", label: "今天先看到这里，保存一个问题" },
      { id: "explore", label: "再用 15 分钟讲一件真实经历" },
      { id: "experiment", label: "如果有方向，之后愿意做一次七天验证" }
    ]
  }
];

const clueMap = {
  research: ["信息检索与证据判断", "把复杂材料整理成结构", "长期推进不确定任务"],
  clinical: ["在信息不完整时形成判断", "面向不同对象解释复杂信息", "责任意识与情境观察"],
  coordination: ["跨角色沟通与协作", "拆解阻碍并推动事情发生", "在约束下安排优先级"],
  learning: ["快速学习陌生知识", "把学习转化为可见产出", "主动定义问题与路径"]
};

const worldMap = {
  research: ["医学研究与临床开发", "医疗 AI 与健康数据"],
  clinical: ["医学事务与专业内容", "医疗产品与用户研究"],
  coordination: ["临床项目与医疗运营", "医疗产品与解决方案"],
  learning: ["医疗 AI 与创新团队", "医学内容与知识服务"]
};

const unknownMap = {
  scorecard: "当成果标签被拿掉，你做事过程中真正反复出现的优势是什么？",
  translation: "哪一段具体经历最能让陌生人看见你的行动和结果？",
  adjacent: "你想离开的究竟是医学本身，还是当前环境里的某种工作方式？",
  browse: "什么样的工作事实，会让你愿意多了解一个方向？"
};

let current = 0;
const answers = new Array(questions.length).fill(null);

const questionShell = document.querySelector("#questionShell");
const resultShell = document.querySelector("#resultShell");
const questionTitle = document.querySelector("#questionTitle");
const questionCount = document.querySelector("#questionCount");
const choices = document.querySelector("#choices");
const nextButton = document.querySelector("#nextButton");
const backButton = document.querySelector("#backButton");
const progress = [...document.querySelectorAll(".progress span")];

function renderQuestion() {
  const question = questions[current];
  questionCount.textContent = `QUESTION ${current + 1} / ${questions.length}`;
  questionTitle.textContent = question.title;
  choices.replaceChildren();

  question.options.forEach((option) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `choice${answers[current] === option.id ? " selected" : ""}`;
    button.textContent = option.label;
    button.addEventListener("click", () => {
      answers[current] = option.id;
      renderQuestion();
    });
    choices.appendChild(button);
  });

  progress.forEach((item, index) => item.classList.toggle("active", index <= current));
  backButton.style.visibility = current === 0 ? "hidden" : "visible";
  nextButton.disabled = answers[current] === null;
  nextButton.textContent = current === questions.length - 1 ? "查看我的线索" : "继续";
}

function fillList(selector, items) {
  const list = document.querySelector(selector);
  list.replaceChildren(...items.map((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    return li;
  }));
}

function showResult() {
  fillList("#capabilityClues", clueMap[answers[1]]);
  fillList("#careerWorlds", worldMap[answers[1]]);
  document.querySelector("#unknownQuestion").textContent = unknownMap[answers[0]];
  questionShell.classList.add("hidden");
  resultShell.classList.remove("hidden");
  resultShell.scrollIntoView({ behavior: "smooth", block: "start" });
}

nextButton.addEventListener("click", () => {
  if (answers[current] === null) return;
  if (current === questions.length - 1) showResult();
  else { current += 1; renderQuestion(); }
});

backButton.addEventListener("click", () => {
  if (current > 0) { current -= 1; renderQuestion(); }
});

renderQuestion();
