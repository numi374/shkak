# 每日纪事｜每日任务 + AI 科技报

仓库：numi374/shkak。手机优先的报纸式首页；按北京时间分日的本地任务记录。

## 已实现
- `index.html`：报纸风格首页，自动读取 `archive/index.json` 展示最新一期与往期；每日任务、前后日期切换、完成统计和删除。
- `archive/2026-09-29.html`：此前网页试刊版**原文**，未重新核查。该原始网页没有逐条完整来源 URL，不能伪称有。
- `archive/index.json`：仅列出实际已保存 HTML 的期数。
- `archive/missing.json`：已知但无法取回完整逐字正文的期数，**不是**日报正文。
- `.github/workflows/daily-newspaper.yml`：北京时间每天约 09:20 尝试运行；GitHub Actions 定时执行可能延迟。
- `scripts/publish_daily.py`：使用 OpenAI Responses API 的 web_search_preview 搜索、生成新一期，进行最小长度/来源链接数/栏目检查及第二次 AI 检查；未通过时失败且不提交。二次 AI 检查不是人工事实核验。

## 部署（尚待确认）
仓库是公开的，但**保存 HTML 不代表 GitHub Pages 已启用**。
到 GitHub 仓库 → Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: main, folder: /(root) → Save。
启用并部署成功后，预期访问地址： https://numi374.github.io/shkak/ 。
以 Pages 设置页实际显示的 URL 和 Actions 部署状态为准。

## 自动发布（需要用户配置；尚未成功实测）
1. 仓库 → Settings → Secrets and variables → Actions → New repository secret。
2. Name: `OPENAI_API_KEY`；Secret: 你自己的 OpenAI API 密钥。**不要**把密钥放到网页、README、Issue 或聊天记录中。
3. 如需指定模型，Repository variables 中新增 `OPENAI_MODEL`；默认 `gpt-5-mini`。模型必须有 Responses API 和联网搜索工具权限。
4. 仓库 → Actions → Daily AI newspaper → Run workflow，先手动测试。查看工作流日志，确认 API 调用、生成文件、commit 均成功，再等待定时运行。
5. 生成和搜索会消耗 API 额度；GitHub Actions 的 schedule 可能延迟。失败时不会生成空白报纸，也不会假装已发布。

**重要**：当前自动化仅覆盖《每日 AI 科技报》，**没有**自动迁移现有 ChatGPT 定时任务、每日 AI 编程或杭州求职雷达。网站内任务是浏览器本地记录，不跨设备同步。

## 历史迁移审计
- 已找到并保留完整 HTML：2026-09-29 网页试刊版（历史未核查）。
- 确认曾生成但没有可提取逐字正文：第015期（2026-10-05）、第016期（10-06）、第017期（10-07）、第018期（10-08）、第019期（10-09）、第020期（10-10）。
- 更早第001～014期：日期与完整正文目前未能逐期确认。
- **绝不**将回忆、提纲、摘要或重新撰写的文章标成历史原文。

## 内容可信度
历史文章的产品、新闻、价格、许可证及命令未经重新核查。新文章通过联网检索和自动质量门槛，仍可能包含事实错误；来源链接不等于独立事实核实。发布结果应人工抽查。
