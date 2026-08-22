import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medical_career_agent.adapters.file_session_store import FileSessionStore
from medical_career_agent.services.resume_parser import extract_text_from_path


class SessionStoreTest(unittest.TestCase):
    def test_session_crud(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(tmpdir)
            sid = store.create("demo-001")
            fetched = store.get(sid)
            self.assertEqual(fetched["session_id"], sid)

            store.update(sid, state={"phase": "match"})
            updated = store.get(sid)
            self.assertEqual(updated["state"]["phase"], "match")

            store.append_event(sid, {"type": "match", "score": 80})
            updated = store.get(sid)
            self.assertEqual(len(updated["events"]), 1)

            listed = store.list_sessions()
            self.assertEqual(len(listed), 1)


class ResumeParserTest(unittest.TestCase):
    def test_txt_extract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "resume.txt"
            p.write_text("医学背景，负责课题文献检索", encoding="utf-8")
            text = extract_text_from_path(p)
            self.assertIn("课题文献检索", text)


if __name__ == "__main__":
    unittest.main()
