# MVP 发布冻结案例

## 用途

这是一组小而固定的回归案例。它不替代完整测试，也不评估模型的文采；它只检查最容易伤害用户信任的边界：事实是否被补写、责任是否被升级、未知是否被隐藏，以及模型不可用时系统是否诚实降级。

在修改提示词、模型、Schema、Role Pack、交付模板或核心工作流后，先运行这组案例；准备发布时，再运行完整测试。

```powershell
python scripts/run_release_regression.py
python -m pytest -q
```

只想确认本次会跑哪些测试时：

```powershell
python scripts/run_release_regression.py --dry-run
```

## 五个冻结案例

| ID | 场景 | 要守住的边界 | 主要依据 |
| --- | --- | --- | --- |
| RR-01 | 正常、可确认的科研经历 | 已确认事实可以走完整链路；不同岗位可改变表达重点，但不增加未知事实。 | `meta-analysis-end-to-end-example.json` |
| RR-02 | 信息不足的经历 | 缺失信息必须保留为未知或待确认，不能补成方法、成果或责任。 | `information-insufficient-end-to-end-example.json` |
| RR-03 | 责任边界模糊的经历 | “负责”“参与”等模糊说法不能自动升级为独立或项目级所有权。 | `responsibility-ambiguous-end-to-end-example.json` |
| RR-04 | 可能夸大的输入 | 主导、论文、影响因子和成果等未核实说法不能直接进入可投递表述。 | `user-exaggeration-end-to-end-example.json` |
| RR-05 | 模型不可用时的降级 | 不能编造替代答案；应保留已有证据，并清楚告诉用户模型改写当前不可用。 | `test_resume_rewriter.py`、`test_api.py` |

完整机器可读清单在 `data/evaluations/release-regression-manifest-v1.json`。

## 每次变更要留下什么

每次发布或重要改动，在 PR、发布记录或团队日志中写下：

- 当前 Git commit；
- 模型名称与配置；
- 提示词或 Skill 包版本；
- Role Pack / Schema / 模板的变更；
- 冻结案例与完整测试的结果；
- 是否存在已知限制，及负责人。

如果涉及真实模型运行，还应另存一份不含真实用户材料的评测记录：模型、模型版本、提示词、包摘要、合成输入、输出、人工结论与日期。不要将 API Key、真实简历或敏感材料写入仓库或日志。

## 通过与失败

通过不等于“输出最好看”，而是五个案例都守住了各自的边界。任何一项失败，都先判断是代码、规则、提示词、模型还是样例预期发生了变化；不要为了让测试变绿而放宽事实确认或 Claim Gate。
