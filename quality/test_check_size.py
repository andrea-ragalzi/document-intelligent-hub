"""Guard against bypassing the size gate with new, moved or exempted files."""

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from check_size import check, source_files


class SizeGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def source(self, name, lines):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n" * lines)
        return path

    def test_new_untracked_file_over_limit_fails(self):
        self.source("backend/app/services/new.py", 601)
        self.assertTrue(check(self.root, "backend", {}))

    def test_warning_does_not_fail_and_limit_is_inclusive(self):
        self.source("frontend/hooks/workflow.ts", 600)
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(check(self.root, "frontend", {}), [])
        self.assertIn("REVIEW frontend/hooks/workflow.ts: 600 lines", output.getvalue())

    def test_warning_starts_above_400_lines(self):
        name = "backend/app/services/workflow.py"
        for lines, warned in ((400, False), (401, True)):
            self.source(name, lines)
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(check(self.root, "backend", {}), [])
            self.assertEqual("REVIEW" in output.getvalue(), warned)

    def test_exception_cannot_grow_or_follow_renamed_file(self):
        name = "backend/app/services/legacy.py"
        exceptions = {name: {"max_lines": 620, "reason": "Legacy workflow"}}
        path = self.source(name, 620)
        self.assertEqual(check(self.root, "backend", exceptions), [])
        self.source(name, 621)
        self.assertTrue(check(self.root, "backend", exceptions))
        path.rename(path.with_name("renamed.py"))
        self.assertEqual(len(check(self.root, "backend", exceptions)), 2)

    def test_stale_or_unjustified_exception_fails(self):
        name = "frontend/components/Legacy.tsx"
        self.source(name, 600)
        self.assertTrue(check(self.root, "frontend", {name: {"max_lines": 620}}))
        self.assertTrue(
            check(
                self.root,
                "frontend",
                {
                    name: {"max_lines": 620, "reason": "Legacy workflow"},
                },
            )
        )

    def test_excludes_generated_and_nonproduction_sources(self):
        self.source("backend/app/generated/models.py", 999)
        self.source("backend/app/migrations/001.py", 999)
        self.source("backend/tests/test_large.py", 999)
        self.assertEqual(source_files(self.root, "backend"), [])
        self.source("frontend/lib/generated.d.ts", 999)
        self.source("frontend/node_modules/vendor.ts", 999)
        self.assertEqual(source_files(self.root, "frontend"), [])

    def test_entrypoint_is_checked(self):
        self.source("backend/main.py", 601)
        self.assertTrue(check(self.root, "backend", {}))


if __name__ == "__main__":
    unittest.main()
