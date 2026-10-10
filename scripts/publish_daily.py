#!/usr/bin/env python3
"""Build a complete daily issue, then publish it atomically. Existing days are immutable."""
import argparse
import datetime as dt
import json
import logging
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
START=dt.date(2026,10,10)
CHINA_TIME=dt.timezone(dt.timedelta(hours=8))
MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini")
ROADMAP=[
 "接收并输出用户消息","变量：保存助手名字","字符串：组织回复","清理用户输入的空格",
 "if：判断空输入","if/else：识别问候","多个条件：识别请求","循环：持续聊天",
 "输入再见时退出","函数：封装回复","函数参数与返回值","list：保存消息",
 "遍历聊天记录","dict：结构化消息","list与dict组合聊天记录","拆分主流程与回复函数",
 "文件：保存消息","文件：追加消息","JSON：保存记录","JSON：读取记录",
 "处理文件不存在","处理坏掉的JSON","HTTP请求与响应","状态码与超时",
 "requests读取公开API","把API数据放进回复","环境变量与密钥","FastAPI第一个接口",
 "FastAPI接收消息","FastAPI返回JSON","FastAPI错误处理","SQLite建立消息表",
 "SQLite写入聊天记录","SQLite读取记录","第一次调用LLM API","处理LLM调用失败",
 "Structured Outputs","Prompt设计","加入聊天上下文","限制上下文长度",
 "Tool Calling概念","执行一个安全工具","RAG准备带来源资料","RAG关键词检索",
 "RAG引用资料","Agent任务与停止条件","Agent一轮工具调用","测试助手",
 "部署准备：配置与日志","部署最小助手"
]
CODING=("title","what","why","code","task","answer","ai_use","project_increment","next")
STORY=("category","title","published","what","why","how","limits","for_me")
JOB=("company","title","location","salary","experience","education","posted","status","responsibilities","fit","gap","verdict","recommendation","url")

def ask(prompt,search=False):
    key=os.getenv("OPENAI_API_KEY")
    if not key: raise RuntimeError("OPENAI_API_KEY is missing; no data was written")
    body={"model":MODEL,"input":prompt+"\n只输出一个合法JSON对象，不要Markdown代码围栏。","max_output_tokens":7500}
    if search: body["tools"]=[{"type":"web_search","search_context_size":"medium"}]
    req=urllib.request.Request("https://api.openai.com/v1/responses",
      data=json.dumps(body,ensure_ascii=False).encode(),method="POST",
      headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=300) as response: result=json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenAI API HTTP {exc.code}") from exc
    if result.get("status")!="completed": raise RuntimeError("API response incomplete")
    outputs=result.get("output",[])
    if search and not any(x.get("type")=="web_search_call" for x in outputs):
        raise RuntimeError("Web search did not run; refusing unsourced content")
    text="".join(c.get("text","") for x in outputs if x.get("type")=="message"
      for c in x.get("content",[]) if c.get("type")=="output_text").strip()
    text=re.sub(r"^```(?:json)?\s*|\s*```$","",text,flags=re.I)
    try: return json.loads(text)
    except json.JSONDecodeError as exc: raise RuntimeError("Invalid JSON; no data was written") from exc

def txt(obj,key,n=4):
    value=obj.get(key)
    if not isinstance(value,str) or len(value.strip())<n: raise ValueError("Missing/short "+key)
    return value

def url(value):
    p=urlparse(value) if isinstance(value,str) else None
    return bool(p and p.scheme=="https" and "." in p.netloc)

def validate_coding(c,number):
    for k in CODING: txt(c,k)
    for k in ("explanation","line_by_line"):
        if not isinstance(c.get(k),list) or len(c[k])<2 or not all(isinstance(x,str) and x.strip() for x in c[k]):
            raise ValueError("Invalid coding "+k)
    if len(c["code"])<25 or len(c["answer"])<25 or len(c["task"])<70:
        raise ValueError("Coding lesson too thin")
    c["day"]=f"Day {number}"

def validate_news(n):
    for k in ("title","summary","intro","experiment"): txt(n,k,20)
    stories=n.get("stories")
    if not isinstance(stories,list) or not 2<=len(stories)<=5: raise ValueError("Need 2–5 news stories")
    for s in stories:
        for k in STORY: txt(s,k)
        if sum(len(s[k]) for k in ("what","why","how","limits","for_me"))<350:
            raise ValueError("News story lacks depth")
        if not isinstance(s.get("sources"),list) or not s["sources"] or not all(url(x) for x in s["sources"]):
            raise ValueError("Story lacks HTTPS source")

def prior_jobs():
    seen=set()
    for path in DATA.glob("*/day.json"):
        try:
            old=json.loads(path.read_text(encoding="utf-8"))
            seen.update(x["url"].split("?")[0] for x in old.get("jobs",{}).get("positions",[]))
        except (ValueError,KeyError,TypeError): logging.warning("Ignoring invalid old jobs in %s",path)
    return seen

def validate_jobs(j,date):
    txt(j,"summary",15)
    if not isinstance(j.get("positions"),list) or len(j["positions"])>5: raise ValueError("Invalid jobs")
    seen=prior_jobs(); accepted=[]
    for p in j["positions"]:
        try:
            for k in JOB: txt(p,k,2)
            if not url(p["url"]) or re.search(r"/zhaopin/|/search/",p["url"]):
                raise ValueError("Not a direct HTTPS job link")
            if not isinstance(p.get("salary_min"),int) or p["salary_min"]<7000:
                raise ValueError("Salary minimum not confirmed at 7000+")
            if "未确认" in p["status"] or "已关闭" in p["status"]:
                raise ValueError("Recruiting status not confirmed")
            if not isinstance(p.get("rating"),int) or not 1<=p["rating"]<=5:
                raise ValueError("Invalid rating")
            if p["url"].split("?")[0] in seen: continue
            p["first_seen"]=date;p["last_checked"]=date;accepted.append(p)
        except (ValueError,TypeError,KeyError) as exc: logging.warning("Skipping job: %s",exc)
    j["positions"]=accepted
    if not accepted: j["summary"]="今天未找到能核实薪资不低于 7000 元、适合当前经历且未重复的新岗位。"

def previous(date):
    path=DATA/str(date-dt.timedelta(days=1))/"day.json"
    if not path.exists(): return "昨天没有已发布课程；保持难度循序渐进。"
    try:
        c=json.loads(path.read_text(encoding="utf-8"))["coding"]
        return f"昨天：{c['title']}。项目新增：{c['project_increment']}"
    except (ValueError,KeyError): return "昨天数据不可读；保持难度循序渐进。"

def generate(date):
    number=(date-START).days+1
    topic=ROADMAP[number-1] if number<=len(ROADMAP) else f"继续迭代个人AI助手，第{number-len(ROADMAP)}次小改进"
    coding=ask(f"""日期{date}，AI编程Day {number}，唯一主题：{topic}。
学习者零散接触过Python/API/FastAPI/数据库/LLM/Agent，但按初学者从头教。每天只增加一点，约15分钟。连续项目是assistant.py“我的简单AI助手”。{previous(date)}
中文返回JSON字段：title,what,why,explanation(2-4段字符串数组),code,line_by_line(逐行解释数组),task(约15分钟),answer(可运行完整代码),ai_use,project_increment,next。代码应在前一天基础上增加，不要突然引入未教过的依赖；解释知识和AI应用的联系。""")
    validate_coding(coding,number)
    news=ask(f"""现在是北京时间{date}。先联网搜索并打开原始来源，写真正值得读的中文AI科技报。
优先官方公告、官方文档、GitHub官方仓库。寻找近7天确有变化的AI工具、开源项目、行业趋势或产品创意。较早资料可以收录，但必须写真实日期，绝不可伪装今天发布。
JSON字段：title,summary,intro,stories(2-4个，每个含category,title,published,what,why,how,limits,for_me,sources原始HTTPS链接数组),experiment。
每篇详细解释是什么、为何关注、怎么用、适合与不适合谁、与替代方案区别、限制、对初学者意义。核查发布时间、版本、功能、定价/免费额度、GitHub维护状态/许可证/安装方式；查不到写“未确认”，禁止编造。正文总计至少约1500汉字。""",True)
    validate_news(news)
    jobs=ask(f"""现在是北京时间{date}。必须联网搜索杭州真实在招职位并打开原始职位详情。
候选人：2025届日语本科，约1年日本电商客服，编程初学，学习Python/API/数据库/Agent。兴趣：科技、AI、游戏的产品运营、用户体验、技术支持、客户成功、问题排查、研究。杭州优先，月薪下限必须>=7000元。
只收具体公司、直接职位链接、薪资可核实、适合1年经验或应届的职位，最多5个。发布日期、招聘状态、地点、学历不明写“未确认”，不要猜。找不到合格职位则positions=[]并如实说明。排除已见链接：{json.dumps(sorted(prior_jobs()),ensure_ascii=False)[:7000]}。
返回JSON：summary,positions数组，每个字段：company,title,location,salary,salary_min(人民币月薪整数下限),experience,education,posted,status,responsibilities,fit,gap,verdict,rating(1-5整数),recommendation,url。评价要对照优势和缺口，不照搬JD。""",True)
    validate_jobs(jobs,date.isoformat())
    return {"date":date.isoformat(),"coding":coding,"newspaper":news,"jobs":jobs}

def publish(date):
    target=DATA/date.isoformat()/"day.json"
    index_path=DATA/"index.json"
    index=json.loads(index_path.read_text(encoding="utf-8"))
    if target.exists():
        if not any(x["date"]==date.isoformat() for x in index):
            # Recover an interrupted previous write without regenerating or replacing the day.
            saved=json.loads(target.read_text(encoding="utf-8"))
            if saved.get("date")!=date.isoformat() or "coding" not in saved:
                raise ValueError("Orphan day file is invalid")
            index.append({"date":date.isoformat(),"day":saved["coding"]["day"]})
            index.sort(key=lambda x:x["date"])
            temp=index_path.with_suffix(".json.tmp")
            temp.write_text(json.dumps(index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            temp.replace(index_path)
            logging.info("Repaired archive index for %s",date)
            return True
        logging.info("%s exists; no-op",target)
        return False
    if any(x["date"]==date.isoformat() for x in index): raise ValueError("Index/day mismatch")
    day=generate(date)  # Nothing is written until every section passes validation.
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(day,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(target)
    index.append({"date":date.isoformat(),"day":day["coding"]["day"]})
    index.sort(key=lambda x:x["date"])
    temp=index_path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temp.replace(index_path)
    logging.info("Published %s: %d stories, %d new jobs",date,len(day["newspaper"]["stories"]),len(day["jobs"]["positions"]))
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument("--date",help="ISO date; default today in Asia/Shanghai")
    a=p.parse_args();logging.basicConfig(level=logging.INFO,format="%(levelname)s %(message)s")
    date=dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(CHINA_TIME).date()
    if date<START or date>dt.datetime.now(CHINA_TIME).date(): raise SystemExit("Date outside live range")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is missing; future days cannot be generated")
    publish(date)
if __name__=="__main__": main()
