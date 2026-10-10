# 日常｜个人每日网站

手机优先的静态网站。每天一个日期，包含任务、15 分钟 AI 编程、AI 科技报、杭州工作雷达。正式归档从 **2026-10-10** 开始；旧日报不迁移。

## 网站和数据

- 首页：`index.html`、`styles.css`、`app.js`
- 任务存储适配器：`task-store.js`
- 日期目录：`data/YYYY-MM-DD/day.json`
- 归档目录：`data/index.json`
- 自动生成：`scripts/publish_daily.py`
- 定时工作流：`.github/workflows/daily.yml`

任务只保存在**当前浏览器的 localStorage**。换手机、换浏览器或清除浏览器数据后可能消失。未来要做同步，可替换 `task-store.js`，无需改页面其他逻辑。

## 每天如何运行

GitHub Actions 每天北京时间约 09:20 运行（GitHub 的 schedule 可能延迟）。脚本先生成课程，再通过 OpenAI Responses API 的 web search 生成科技报和岗位。它检查搜索工具确实调用、数据结构、原始 HTTPS 链接、内容长度、岗位薪资门槛和重复职位。全部通过后才写当天 JSON 与归档目录；同一天再次运行直接退出，旧日期永不覆盖。若失败，已发布的页面和历史仍可用。

自动来源检查不是人工事实核查。招聘状态、价格、免费额度、版本和许可证会变化，阅读时仍应打开原始来源确认。没有可核实的新岗位时显示 0 个，不凑数。

## 配置

1. 仓库 → **Settings → Secrets and variables → Actions → New repository secret**。
2. Name 填 `OPENAI_API_KEY`，Value 填你自己的 OpenAI API Key。不要把 Key 发到聊天、提交到仓库或放进网页。
3. 可选：在同一页 **Variables → New repository variable**，Name `OPENAI_MODEL`，Value 是支持 Responses API 和 web search 的模型；默认 `gpt-5-mini`。
4. Pages 使用 **main 分支 / (root)**。启用后，首次部署和每天 Actions 推送的新提交都会触发重新部署。
5. Actions → **Publish daily page → Run workflow**，查看运行日志。正式判定成功还需确认新 JSON、自动 commit、Pages 部署和公网内容。

本地检查：`python -m unittest discover -s tests -v`。不带 Key 执行生成脚本时会在写入前失败；已有日期会直接无操作退出。

## 失败排查

在仓库 **Actions → Publish daily page** 查看最新运行。常见原因是 Secret 缺失、API 余额或模型权限不足、联网搜索失败、模型返回格式/引用未通过检查、工作流没有仓库写权限。若生成成功但网页仍旧，检查 **Actions → pages build and deployment**、Settings → Pages，以及 `data/index.json` 中是否出现当天日期。定时任务可能延迟，可手动 Run workflow 重试。

## 成本

GitHub Pages 对公开仓库通常无需单独服务器费用。OpenAI 成本取决于模型、搜索次数和输出长度。以 `gpt-5-mini` 为例，官方标价为输入 $0.25/百万 token、输出 $2/百万 token，web search 为 $0.01/次并另计搜索内容 token。假设每天 3 次搜索、2 万输入 token、6000 输出 token，约 **$0.05/天，$1.50/月**；这是预算估算，实际账单以 OpenAI 平台为准。降低成本可减少搜索主题或输出长度，但可能损失日报深度。
