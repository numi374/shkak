#!/usr/bin/env python3
"""Validate a ChatGPT/Codex-written issue and add it to the immutable archive."""
import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
START = dt.date(2026, 10, 10)
CODING = ("title", "what", "why", "code", "task", "answer", "ai_use", "project_increment", "next")
STORY = ("category", "title", "published", "what", "why", "how", "limits", "for_me")
JOB = ("company", "title", "location", "salary", "experience", "education", "posted", "status", "responsibilities", "fit", "gap", "verdict", "recommendation", "url")


def text(obj, key, minimum=4):
    value = obj.get(key)
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ValueError(f"Missing or short {key}")
    return value


def https_url(value):
    parsed = urlparse(value) if isinstance(value, str) else None
    return bool(parsed and parsed.scheme == "https" and "." in parsed.netloc)


def validate_issue(issue, date, previous_urls=()):
    """Reject incomplete content before changing any archive file."""
    if issue.get("date") != date.isoformat() or date < START:
        raise ValueError("Issue date does not match target")
    number = (date - START).days + 1
    coding = issue.get("coding")
    if not isinstance(coding, dict) or coding.get("day") != f"Day {number}":
        raise ValueError("Incorrect course day")
    for key in CODING:
        text(coding, key)
    for key in ("explanation", "line_by_line"):
        lines = coding.get(key)
        if not isinstance(lines, list) or len(lines) < 2 or not all(isinstance(x, str) and x.strip() for x in lines):
            raise ValueError(f"Invalid {key}")
    if len(coding["code"]) < 25 or len(coding["answer"]) < 25 or len(coding["task"]) < 70:
        raise ValueError("Coding lesson too thin")

    news = issue.get("newspaper")
    if not isinstance(news, dict):
        raise ValueError("Missing newspaper")
    for key in ("title", "summary", "intro", "experiment"):
        text(news, key, 20)
    stories = news.get("stories")
    if not isinstance(stories, list) or not 2 <= len(stories) <= 5:
        raise ValueError("Need 2-5 researched stories")
    sources = set()
    for story in stories:
        if not isinstance(story, dict):
            raise ValueError("Invalid story")
        for key in STORY:
            text(story, key)
        if sum(len(story[key]) for key in ("what", "why", "how", "limits", "for_me")) < 350:
            raise ValueError("News story lacks depth")
        links = story.get("sources")
        if not isinstance(links, list) or not links or not all(https_url(x) for x in links):
            raise ValueError("News story lacks HTTPS sources")
        sources.update(links)
    if len(sources) < 2:
        raise ValueError("Need at least two distinct sources")

    jobs = issue.get("jobs")
    if not isinstance(jobs, dict):
        raise ValueError("Missing jobs")
    text(jobs, "summary", 15)
    positions = jobs.get("positions")
    if not isinstance(positions, list) or len(positions) > 5:
        raise ValueError("Invalid jobs list")
    seen = set(previous_urls)
    for position in positions:
        if not isinstance(position, dict):
            raise ValueError("Invalid job")
        for key in JOB:
            text(position, key, 2)
        url = position["url"].split("?")[0]
        if not https_url(url) or re.search(r"/zhaopin/|/search/", url) or url in seen:
            raise ValueError("Job needs a new direct HTTPS listing")
        if not isinstance(position.get("salary_min"), int) or position["salary_min"] < 7000:
            raise ValueError("Job salary floor must be confirmed at 7000 yuan")
        if "未确认" in position["status"] or "已关闭" in position["status"]:
            raise ValueError("Recruitment status is not confirmed open")
        if not isinstance(position.get("rating"), int) or not 1 <= position["rating"] <= 5:
            raise ValueError("Job rating must be 1-5")
        if position.get("first_seen") != date.isoformat() or position.get("last_checked") != date.isoformat():
            raise ValueError("Job tracking dates must match issue date")
        seen.add(url)


def old_job_urls(data=DATA):
    urls = set()
    for path in data.glob("*/day.json"):
        issue = json.loads(path.read_text(encoding="utf-8"))
        urls.update(p["url"].split("?")[0] for p in issue.get("jobs", {}).get("positions", []))
    return urls


def archive_issue(issue, data=DATA):
    date = dt.date.fromisoformat(issue["date"])
    target = data / date.isoformat() / "day.json"
    index_file = data / "index.json"
    index = json.loads(index_file.read_text(encoding="utf-8"))
    if target.exists() or any(x["date"] == date.isoformat() for x in index):
        raise FileExistsError(f"{date} already published; existing days are immutable")
    validate_issue(issue, date, old_job_urls(data))
    new_index = sorted(index + [{"date": date.isoformat(), "day": issue["coding"]["day"]}], key=lambda x: x["date"])
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents a repeated run from replacing a published issue.
    with target.open("x", encoding="utf-8") as handle:
        json.dump(issue, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temp = index_file.with_name("index.json.tmp")
    temp.write_text(json.dumps(new_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, index_file)
    print(f"Archived {date}: {len(issue['newspaper']['stories'])} stories, {len(issue['jobs']['positions'])} jobs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("draft", type=Path, help="Complete day.json prepared by ChatGPT/Codex")
    args = parser.parse_args()
    issue = json.loads(args.draft.read_text(encoding="utf-8"))
    archive_issue(issue)


if __name__ == "__main__":
    main()
