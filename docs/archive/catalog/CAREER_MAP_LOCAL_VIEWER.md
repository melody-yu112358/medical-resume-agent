> **历史原件 / archived 2026-09-06。** 原路径：`docs/CAREER_MAP_LOCAL_VIEWER.md`；归档前最后提交日期：2026-09-06。原文版本：[Git 85701b51](https://github.com/melody-yu112358/medical-resume-agent/blob/85701b516f5889412e9791391c4dedcb2d7b0b38/docs/CAREER_MAP_LOCAL_VIEWER.md)。当前承接入口：[有效说明](../../CAREER_MAP_DATABASE.md#local-read-only-viewer)。原有日期、数量、计划、验证与结论保留当时语境，不代表当前库存或本次重新验收；归档不改变 legacy 规则。

# 本地职业知识试用台

复用 SQLite 与 PR2 解释器的独立只读页面，不挂载到原简历应用。不新增职业、职业卡、真实 Profile、JD 输入或 runtime target。

在仓库根目录运行：

```powershell
python -m pip install -e ".[schema_validation]"
python scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite
python scripts/serve_career_map.py
```

用浏览器打开 http://127.0.0.1:8765 。保持终端开启；按 Ctrl+C 停止。已安装并导入过的用户只需最后一条命令。端口占用时使用 `--port 8766`；`--database` 可指定另一个已导入的本地库。

1. 先按职能族浏览，按需选择生态或生命周期；同维度多选为 OR，跨维度为 AND，不选则不限。勾选或取消立即提交只读查询，数量与结果一起刷新，保留在操作的维度附近；脚本不可用时才显示“应用筛选”按钮。
2. 打开已有职业卡，阅读职责、交付物和边界。
3. 在有规则的方向选择已有虚构档案，查看解释。
4. 展开“证据与条件”，对照 all-of / any-of、缺失项、原始经历与 scope。
5. 展开来源，区分背景研究与人工支持关系，查看摘要差异及 revision。

生命周期区分已标注、待确认、不适用。选择具体阶段会排除后两者，页面显示其数量；空结果可取消生命周期限制并保留其他筛选。阶段不是每个职业的必填属性；标签交集不证明具体机构和阶段组合成立。完整规则及 taxonomy 源字段见 [筛选契约](CAREER_MAP_TAXONOMY.md)。

解释条目只展示一次，标签可以重叠。未命中可选迁移路径与没有 JD 的条件项不会被默认为 gap。当前页面不接受 JD 上下文，也不提供历史快照选择；历史回放仍使用已有 CLI。页面选择当前快照后，显式把其 ID 传给解释器，避免后续导入改变本次查询版本。

所有数据库连接均使用 SQLite `mode=ro`；目录连接另启用 query_only。页面只接受已有 synthetic profile ID，不接受档案内容或上传，也不写日志文件、缓存或数据库。访问仅限 loopback，启动器固定 127.0.0.1、关闭 debug/reloader；仅加载本机筛选增强脚本，无外部资源或第三方请求。终端可能显示常规 HTTP 请求日志（仅目录选项和虚构 ID）。这是本地开发试用台，不是公网部署入口；生产入口与隐私 PR3 不在本次范围。

数据库缺失或版本过旧时先导入，不由网页自动建库。解释器不兼容时页面提示重新导入；保留旧知识与用户本地数据库，不自动迁移或修改它们。
