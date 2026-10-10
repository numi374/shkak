#!/usr/bin/env python3
"""Commit one validated issue and its index with the authenticated GitHub CLI."""
import argparse
import base64
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "repos/numi374/shkak"


def api(path, method="GET", body=None):
    command = ["gh", "api"]
    if method != "GET":
        command += ["-X", method]
    command.append(path)
    if body is not None:
        command += ["--input", "-"]
    result = subprocess.run(command, input=json.dumps(body, ensure_ascii=False) if body is not None else None,
                            text=True, encoding="utf-8", capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"GitHub API {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def remote_content(path):
    result = api(f"{REPOSITORY}/contents/{path}")
    return base64.b64decode(result["content"]).decode("utf-8")


def push(date):
    issue_path = f"data/{date}/day.json"
    index_path = "data/index.json"
    issue = json.loads((ROOT / issue_path).read_text(encoding="utf-8"))
    if issue.get("date") != date:
        raise ValueError("Local issue date mismatch")
    index = json.loads((ROOT / index_path).read_text(encoding="utf-8"))
    if sum(x["date"] == date for x in index) != 1:
        raise ValueError("Local archive index mismatch")
    try:
        remote_content(issue_path)
    except RuntimeError as exc:
        if "404" not in str(exc):
            raise
    else:
        raise FileExistsError(f"Remote {issue_path} already exists; refusing overwrite")
    remote_index = json.loads(remote_content(index_path))
    if any(x["date"] == date for x in remote_index):
        raise FileExistsError("Remote index already has this date")
    ref = api(f"{REPOSITORY}/git/ref/heads/main")
    head = ref["object"]["sha"]
    commit = api(f"{REPOSITORY}/git/commits/{head}")
    entries = []
    for path in (issue_path, index_path):
        content = (ROOT / path).read_text(encoding="utf-8")
        blob = api(f"{REPOSITORY}/git/blobs", "POST", {"content": content, "encoding": "utf-8"})
        entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    tree = api(f"{REPOSITORY}/git/trees", "POST", {"base_tree": commit["tree"]["sha"], "tree": entries})
    created = api(f"{REPOSITORY}/git/commits", "POST", {
        "message": f"Publish daily issue {date}", "tree": tree["sha"], "parents": [head]
    })
    api(f"{REPOSITORY}/git/refs/heads/main", "PATCH", {"sha": created["sha"], "force": False})
    print(f"Committed {date}: {created['sha']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="YYYY-MM-DD")
    push(parser.parse_args().date)
