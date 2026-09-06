# 本地职业知识试用台

复用 SQLite 与 PR2 解释器的独立只读页面，不挂载到原简历应用。不新增职业、职业卡、真实 Profile、JD 输入或 runtime target。

在仓库根目录运行：

```powershell
python -m pip install -e ".[schema_validation]"
python scripts/import_role_packs_to_career_map.py --database .local/career-map.sqlite
python scripts/serve_career_map.py
```

用浏览器打开 http://127.0.0.1:8765 。保持终端开启；按 Ctrl+C 停止。已安装并导入过的用户只需最后一条命令。端口占用时使用 `--port 8766`；`--database` 可指定另一个已导入的本地库。

1. 用产业生态、生命周期和职能族筛选目录。
2. 打开已有职业卡，阅读职责、交付物和边界。
3. 在有规则的方向选择已有虚构档案，查看解释。
4. 展开“证据与条件”，对照 all-of / any-of、缺失项、原始经历与 scope。
5. 展开来源，区分背景研究与人工支持关系，查看摘要差异及 revision。

解释条目只展示一次，标签可以重叠。未命中可选迁移路径与没有 JD 的条件项不会被默认为 gap。当前页面不接受 JD 上下文，也不提供历史快照选择；历史回放仍使用已有 CLI。页面选择当前快照后，显式把其 ID 传给解释器，避免后续导入改变本次查询版本。

所有数据库连接均使用 SQLite `mode=ro`；目录连接另启用 query_only。页面只接受已有 synthetic profile ID，不接受档案内容或上传，也不写日志文件、缓存或数据库。访问仅限 loopback，启动器固定 127.0.0.1、关闭 debug/reloader；无外部资源、第三方请求或脚本。终端可能显示常规 HTTP 请求日志（仅目录选项和虚构 ID）。这是本地开发试用台，不是公网部署入口；生产入口与隐私 PR3 不在本次范围。

数据库缺失或版本过旧时先导入，不由网页自动建库。解释器不兼容时页面提示重新导入；保留旧知识与用户本地数据库，不自动迁移或修改它们。
