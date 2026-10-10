# 日常｜个人每日网站

[打开网站](https://numi374.github.io/shkak/) · 手机优先的静态网站。每天一个日期，包含今日任务、15 分钟 AI 编程、AI 科技报和杭州工作雷达。正式归档从 **2026-10-10** 开始；旧日报不迁移。

## 数据与页面

- `index.html`、`styles.css`、`app.js`：首页、全文与历史归档。
- `task-store.js`：浏览器任务记录。任务只保存在**当前浏览器的 localStorage**；换手机、换浏览器或清除数据后可能消失。将来可替换此适配器接入同步服务。
- `data/YYYY-MM-DD/day.json`：每天独立保存的课程、日报与岗位。
- `data/index.json`：按日期排列的归档目录。
- `scripts/publish_daily.py`：校验 ChatGPT/Codex 撰写的完整草稿，并只新增日期文件。
- `scripts/push_daily.py`：用本机已登录的 GitHub CLI 提交当天数据；拒绝覆盖远端已有日期。

## 每天如何更新

此站改用 **Codex 桌面端的本聊天定时任务**，不再通过 GitHub Actions 调用 OpenAI API，也不需要配置 `OPENAI_API_KEY`。任务计划在北京时间每天 09:20 唤醒，按 [每日发布说明](DAILY_PUBLISHING.md) 检索、写作、校验、提交并检查 Pages。GitHub Pages 仍从 `main` 分支根目录自动部署。定时任务由本机桌面应用执行；电脑和应用需在计划时间可用，离线时不能保证准点更新。定时任务的第一次到点执行还需要实际观察，不能仅凭已创建任务就认定自动链路成功。

本地校验：

```powershell
python -m unittest discover -s tests -v
python scripts/publish_daily.py C:\path\to\complete-draft.json
python scripts/push_daily.py YYYY-MM-DD
```

生成失败时不要提交不完整 JSON。已经发布的旧日期不覆盖，旧网页仍可正常使用。没有可核实的新岗位时显示 0 个，不凑数。岗位状态、产品价格、版本和额度可能变化，阅读时仍应打开原始来源再次确认。

## 排查

先在 Codex 桌面应用打开本聊天的定时任务运行记录，确认任务是否在北京时间 09:20 被唤醒，以及检索、校验、提交哪一步失败。再看仓库的 [提交历史](https://github.com/numi374/shkak/commits/main)、[Pages 部署记录](https://github.com/numi374/shkak/actions/workflows/pages-build-deployment) 和 `data/index.json`。常见原因：电脑或应用没有运行、网络/搜索不可用、GitHub CLI 登录失效或没有写权限、稿件缺少来源而被校验拒绝、Pages 部署延迟。可以在本聊天要求立即补发当天内容。

## 成本

网站使用 GitHub Pages。此方案不单独调用付费 OpenAI API，因此额外 API 账单预计 **0 美元/天、0 美元/月**；Codex/ChatGPT 的订阅和使用额度仍按用户账户规则计算。没有常驻服务器或数据库费用。
