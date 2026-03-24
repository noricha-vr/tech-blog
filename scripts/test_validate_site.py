from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_site import main


class ValidateSiteTests(unittest.TestCase):
    def test_main_returns_2_for_missing_directory(self) -> None:
        self.assertEqual(main(["validate_site.py"]), 2)
        self.assertEqual(main(["validate_site.py", "missing", "extra"]), 2)
        self.assertEqual(main(["validate_site.py", "does-not-exist"]), 2)

    def test_main_returns_0_when_forbidden_url_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "index.html").write_text("<a href='https://example.com'>ok</a>", encoding="utf-8")
            self.assertEqual(main(["validate_site.py", tmp]), 0)

    def test_main_returns_1_when_forbidden_url_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "index.html").write_text("<a href='https://kaisha3.com/blog'>ng</a>", encoding="utf-8")
            self.assertEqual(main(["validate_site.py", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
