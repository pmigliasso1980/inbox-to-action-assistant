import json
import tempfile
import unittest
from pathlib import Path

from agents.review_tools import ToolError, execute_confirmed
from agents.tool_controls import ReadOnlyReviewStore, ReviewCommentBoundary, WritableCommentStore, explicit_test_with_fallback, gate_for


class ToolControlTests(unittest.TestCase):
    def test_tools_validate_and_confirm(self):
        outcome = execute_confirmed("run_linter", {"file": "tags.py", "profile": "all"})
        self.assertTrue(outcome.confirmed)
        self.assertTrue(outcome.value["findings"])
        with self.assertRaises(ToolError):
            execute_confirmed("read_code", {"file": "../../etc/passwd"})

    def test_all_failure_modes_route_to_fallback(self):
        for mode in ["rate_limit", "timeout", "auth", "empty", "garbage"]:
            result = explicit_test_with_fallback(mode=mode, file="tags.py")
            self.assertTrue(result["used_fallback"], mode)
            self.assertTrue(result["grounded"], mode)

    def test_read_handle_cannot_write(self):
        self.assertFalse(hasattr(ReadOnlyReviewStore(), "append"))

    def test_gate_dry_run_and_validation_are_audited(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); audit = root / "audit.jsonl"; comments = root / "comments.jsonl"
            boundary = ReviewCommentBoundary(read_store=ReadOnlyReviewStore(), write_store=WritableCommentStore(comments),
                                             audit_path=audit, gate=gate_for("auto_approve"), dry_run=True)
            result = boundary.post_review_comment(run_id="r", item_id="i", file="tags.py", line=1,
                                                  severity="major", body="Mutable default persists.")
            self.assertTrue(result["dry_run"]); self.assertFalse(comments.exists())
            self.assertEqual(json.loads(audit.read_text())["outcome"], "dry_run")

    def test_denial_is_not_silent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            boundary = ReviewCommentBoundary(read_store=ReadOnlyReviewStore(), write_store=WritableCommentStore(root/"c"),
                                             audit_path=root/"a", gate=gate_for("auto_deny"))
            with self.assertRaisesRegex(ToolError, "declined"):
                boundary.post_review_comment(run_id="r", item_id="i", file="tags.py", line=1,
                                             severity="major", body="No")


if __name__ == "__main__":
    unittest.main()
