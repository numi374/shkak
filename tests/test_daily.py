import copy
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import publish_daily as daily


class DailyTests(unittest.TestCase):
    def test_every_archived_issue_is_complete(self):
        index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(index), len({entry["date"] for entry in index}))
        self.assertEqual(index, sorted(index, key=lambda entry: entry["date"]))
        for entry in index:
            issue = json.loads((ROOT / "data" / entry["date"] / "day.json").read_text(encoding="utf-8"))
            self.assertEqual(issue["coding"]["day"], entry["day"])
            daily.validate_issue(issue, dt.date.fromisoformat(entry["date"]))

    def test_invalid_draft_does_not_change_archive(self):
        seed = json.loads((ROOT / "data/2026-10-10/day.json").read_text(encoding="utf-8"))
        invalid = copy.deepcopy(seed)
        invalid["date"] = "2026-10-12"
        invalid["coding"]["day"] = "Day 3"
        invalid["newspaper"]["stories"][0]["sources"] = ["http://not-secure.test"]
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            original = '[{"date":"2026-10-10","day":"Day 1"}]'
            (data / "index.json").write_text(original, encoding="utf-8")
            with self.assertRaises(ValueError):
                daily.archive_issue(invalid, data)
            self.assertEqual((data / "index.json").read_text(encoding="utf-8"), original)
            self.assertFalse((data / "2026-10-12/day.json").exists())

    def test_repeated_day_does_not_overwrite(self):
        seed = json.loads((ROOT / "data/2026-10-10/day.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            target = data / "2026-10-10/day.json"
            target.parent.mkdir()
            target.write_text("keep me", encoding="utf-8")
            (data / "index.json").write_text('[]', encoding="utf-8")
            with self.assertRaises(FileExistsError):
                daily.archive_issue(seed, data)
            self.assertEqual(target.read_text(encoding="utf-8"), "keep me")


if __name__ == "__main__":
    unittest.main()
