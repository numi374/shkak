#!/usr/bin/env python3
"""Scheduled AI newspaper publisher. Requires OPENAI_API_KEY; never writes incomplete issues."""
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import urllib.request
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
API="https://api.openai.com/v1/responses"
MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini")
KEY=os.getenv("OPENAI_API_KEY")
if not KEY:
    raise SystemExit("OPENAI_API_KEY is missing: no article was generated or published.")

date=dt.datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
target=ROOT/"archive"/f"{date}.html"
if target.exists():
    print(f"{target} already exists; refusing to overwrite.")
    raise SystemExit(0)

def ask(prompt):
    payload=json.dumps({"model":MODEL,"tools":[{"type":"web_search_preview"}],"input":prompt,"max_output_tokens":12000},ensure_ascii=False).encode()
    req=urllib.request.Request(API,data=payload,headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=240) as response:
        data=json.load(response)
    if data.get("status") not in (None,"completed"):
        raise RuntimeError("API response not completed: "+str(data.get("status")))
    text="\n".join(c.get("text","") for m in data.get("output",[]) if m.get("type")=="message" for c in m.get("content",[]) if c.get("type")=="output_text")
    if not text.strip():
        raise RuntimeError("Empty AI output; no file published")
    return text

prompt=f"""为 {date}（北京时间）制作中文《每日 AI 科技报》。严格使用联网搜索，必须提供可核查的真实原始来源 URL。
需要报头、日期、30秒速览、三个均衡的完整版面：
1 AI新工具：2-3个真实工具，发布日期、功能机制、操作流程、案例、竞品、价格和免费限制、隐私与局限。
2 GitHub开源：真实仓库 URL、许可证、维护状态、架构、安装运行命令、输入输出、替代方案、初学者实验。
3 AI产品实验室：原创构想、目标用户、证据/待验证、竞品、MVP、数据结构、架构、验证指标、15分钟任务。
每条具体新闻/版本/价格都在段落附近附来源 URL；查不到明确写未知。不要把旧新闻写成今日发布。
全文至少2500中文字；Markdown 格式，一级标题仅一个，二级标题对应三个版面，最后必须有“## 来源与核查”并列出不少于6条完整 https 来源链接。
不要生成假链接，不要声称独立实测除非真的有独立实测来源。"""
article=ask(prompt)
urls=set(re.findall(r"https://[^\s)<>\]【】]+",article))
if len(article)<3500 or len(urls)<6 or not all(x in article for x in ["AI新工具","GitHub","产品实验室","来源与核查"]):
    raise RuntimeError(f"Quality gate failed: chars={len(article)} sources={len(urls)}; nothing published")
# Second pass asks for source-grounding critique. It can reject a draft; it is not independent fact-checking.
review=ask("核查下面的稿件。联网检查引用链接及日期、价格、仓库许可证的关键断言；如果发现杜撰或无法可靠验证的重要事实，回答 REJECT；仅在基本证据充分时回答 ACCEPT。只输出 ACCEPT 或 REJECT。\n\n"+article[:26000])
if not review.strip().upper().startswith("ACCEPT"):
    raise RuntimeError("Second-pass source check rejected draft; nothing published")
# Preserve Markdown verbatim in readable, wrapped preformatted layout; escape all model output.
safe=html.escape(article)
safe=re.sub(r'https://[^\\s&lt;&gt;]+',lambda m: '<a href="'+m.group(0)+'" rel="noopener noreferrer" target="_blank">'+m.group(0)+'</a>',safe)
page=f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>每日 AI 科技报｜{date}</title><style>
body{{margin:0;background:#eee9dd;color:#222;font:16px/1.8 system-ui,sans-serif}}main{{max-width:850px;margin:auto;background:#fffdf8;padding:clamp(16px,5vw,48px);min-height:100vh}}header{{border-bottom:4px double #222}}h1{{font:700 clamp(32px,7vw,58px) Georgia,serif}}a{{color:#a13228}}article{{white-space:pre-wrap;overflow-wrap:anywhere;font-family:inherit}}.note{{background:#f6ebdc;padding:12px;border-left:4px solid #a13228;font-size:14px}}</style></head><body><main><header><p><a href="../index.html">← 返回首页</a></p><h1>每日 AI 科技报</h1><p>{date} · 自动生成版</p></header><p class="note">本期由 AI 联网检索生成，并经过自动二次检查；这不等同于人工逐条核验。新闻、价格与命令请以文中官方来源为准。</p><article>{safe}</article></main></body></html>"""
target.write_text(page,encoding="utf-8")
index=ROOT/"archive"/"index.json"
items=json.loads(index.read_text(encoding="utf-8"))
items.append({"date":date,"title":"每日 AI 科技报","path":f"archive/{date}.html","status":"automated-source-checked"})
items.sort(key=lambda x:x["date"],reverse=True)
index.write_text(json.dumps(items,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Created {target} with {len(urls)} cited URLs; automated check passed.")
