# 医学经历拆解器 Lite（小红书小工具）

这是面向小红书离线小工具容器的轻量体验版，不是 `Medical Resume Skill Lite` 的替代品。

它只使用包内 HTML、CSS、JavaScript 与 `localStorage`，不请求网络、不调用模型、不上传文本。用户可手动输入一段已脱敏经历、选择目标方向与真实使用过的线索，获得事实摘要、最多三个补充问题，以及不同方向的表达重点。

## 上传前检查

- 上传整个本目录，入口为 `index.html`。
- 不要加入外链字体、CDN、`fetch`、`XMLHttpRequest`、WebAssembly、内联脚本、行内 `onclick`、`a[download]` 或外链跳转。
- 不要声称提供 AI 润色、PDF 导出、DOCX/PDF 上传或联网 JD 匹配；这些功能属于 GitHub 的完整 Skill / 网页版本，不属于本离线体验版。

## 本地预览

可直接在浏览器打开 `index.html`。如需验证 `localStorage`，请用任意静态文件服务器预览。
