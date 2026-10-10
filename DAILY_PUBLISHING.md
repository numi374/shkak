# 每日发布说明（供 Codex 定时任务执行）

目标仓库：`numi374/shkak`。北京时间当日生成且只生成一份完整内容。网站目录在本机 `C:\Users\zy\Documents\Codex\2026-10-10\github-numi374-shkak-1-2-ai\repo`。如果本地目录不可用，先从 GitHub 获取仓库，再按仓库最新说明操作。不要依赖单独的 OpenAI API Key，不要把任何密钥写入数据或仓库。

1. 用 `Asia/Shanghai` 取得当前日期，先查 GitHub 远端 `data/YYYY-MM-DD/day.json`。存在则检查网页是否可见，结束，不重写历史。
2. 读 `data/index.json` 和前一天课程；Day 编号从 2026-10-10 的 Day 1 起按日历递增。编写约 15 分钟的连续项目课程，始终接着 `assistant.py`，每天只增加一小步；需要包含 `coding` 中的所有字段。答案放在 `answer`，网页会折叠显示。
3. 联网查当天适合收录的 AI 工具、GitHub 项目和趋势。优先官方公告、文档和仓库；逐条打开来源，记录真实发布日期、已核实的功能/安装/许可证/价格，无法核实写“未确认”。每期精选 2–5 篇有深度的故事和一个可立即实践的小实验。不要把旧消息说成今天发布。
4. 联网搜索杭州 AI、科技、游戏相关岗位，参照用户背景：2025 届日语本科，约一年日本电商客服经验，编程初学，薪资下限 7000 元/月。只有具体职位原始链接、薪资下限和开放状态均能核实时才收入；对照既有日期去重。找不到时保留空 `positions` 并说明搜索范围与不足，不编造。新岗位需包含 `first_seen` 和 `last_checked`。
5. 将草稿保存在仓库外的临时目录，格式参考已有 `data/YYYY-MM-DD/day.json`。先运行 `python scripts/publish_daily.py 草稿路径`，再运行 `python -m unittest discover -s tests -v`。校验失败先修稿，不能发布半成品。已有日期时脚本会拒绝覆盖。
6. 确认 GitHub CLI 已登录且拥有本仓库写权限，运行 `python scripts/push_daily.py YYYY-MM-DD`。检查远端提交、`data/index.json`、Pages 部署状态和公网 `https://numi374.github.io/shkak/` 当天内容。若提交失败，保留本地完整数据并报告，稍后重试；不要声称部署成功。
7. 向用户只报告实际完成的阶段：内容写入、Git commit、Pages 构建、公网页面。对没发生的步骤如实写“未验证”。若当天远端已发布且一切正常，保持安静；仅在实际发布、失败或需要用户操作时通知。

GitHub Pages 部署由 `main` 的新提交触发，旧日期数据不能因生成失败而被改写。不要把“定时任务已创建”写成“定时任务已成功执行”。
