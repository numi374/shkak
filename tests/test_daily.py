import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import publish_daily as pub

ROOT=Path(__file__).resolve().parents[1]

class DailyTests(unittest.TestCase):
    def test_seed_archive_is_valid(self):
        index=json.loads((ROOT/"data/index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(index),len({x["date"] for x in index}))
        for item in index:
            day=json.loads((ROOT/"data"/item["date"]/"day.json").read_text(encoding="utf-8"))
            self.assertEqual(day["date"],item["date"])
            self.assertEqual(day["coding"]["day"],item["day"])
            pub.validate_coding(day["coding"],int(item["day"].split()[1]))
            pub.validate_news(day["newspaper"])
            pub.validate_jobs(day["jobs"],item["date"])

    def test_existing_day_does_not_call_api_or_overwrite(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(pub,"DATA",Path(folder)):
            date=dt.date(2026,10,11)
            target=Path(folder)/str(date)/"day.json"
            target.parent.mkdir()
            target.write_text('{"date":"2026-10-11","coding":{"day":"Day 2"}}',encoding="utf-8")
            (Path(folder)/"index.json").write_text('[{"date":"2026-10-11","day":"Day 2"}]',encoding="utf-8")
            with patch.object(pub,"generate",side_effect=AssertionError("API called")):
                self.assertFalse(pub.publish(date))
            self.assertEqual(json.loads(target.read_text())["coding"]["day"],"Day 2")

    def test_generation_failure_keeps_previous_archive(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(pub,"DATA",Path(folder)):
            original='[{"date":"2026-10-10","day":"Day 1"}]'
            (Path(folder)/"index.json").write_text(original,encoding="utf-8")
            date=dt.date(2026,10,11)
            with patch.object(pub,"generate",side_effect=RuntimeError("search failed")):
                with self.assertRaises(RuntimeError): pub.publish(date)
            self.assertEqual((Path(folder)/"index.json").read_text(encoding="utf-8"),original)
            self.assertFalse((Path(folder)/str(date)).exists())

    def test_unverified_job_is_not_published(self):
        jobs={"summary":"查找到的岗位尚待进一步核验，暂时不能发布。","positions":[{
            "company":"公司","title":"职位","location":"杭州","salary":"8k","salary_min":8000,
            "experience":"1年","education":"本科","posted":"未确认","status":"未确认",
            "responsibilities":"客服工作","fit":"日语经验","gap":"技术知识","verdict":"先观察",
            "rating":3,"recommendation":"可以观察","url":"https://example.com/job/1"
        }]}
        pub.validate_jobs(jobs,"2026-10-11")
        self.assertEqual(jobs["positions"],[])

if __name__=="__main__": unittest.main()
