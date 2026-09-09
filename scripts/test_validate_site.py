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

    def test_article_links_and_quoted_urls_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "index.html").write_text("<a href='https://kaisha3.com/blog'>記事</a><code>https://kaisha3.com</code>", encoding="utf-8")
            Path(tmp, "search.json").write_text('{"text":"https://kaisha3.com"}', encoding="utf-8")
            self.assertEqual(main(["validate_site.py", tmp]), 0)

    def test_resource_references_are_rejected(self) -> None:
        examples = [
            '<script src="https://kaisha3.com/app.js"></script>',
            '<link rel="stylesheet" href="//WWW.KAISHA3.COM/main.css">',
            '<img srcset="/local.png 1x, https://kaisha3.com/img.png 2x">',
            '<iframe src="https://kaisha3.com/"></iframe>',
            '<video poster="https://kaisha3.com/poster.png"></video>',
            '<object data="https://kaisha3.com/file"></object>',
            '<div style="background:url(https://kaisha3.com/bg.png)"></div>',
            '<style>@import "https://kaisha3.com/main.css";</style>',
            '<img src="https:&#47;&#47;kaisha3.com/img.png">',
        ]
        for html in examples:
            with self.subTest(html=html), tempfile.TemporaryDirectory() as tmp:
                Path(tmp, 'index.html').write_text(html, encoding='utf-8')
                self.assertEqual(main(['validate_site.py', tmp]), 1)

    def test_css_resources_are_rejected_without_matching_other_hosts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, 'style.css')
            path.write_text('body { background: url(https://kaisha3.com/bg.png); }', encoding='utf-8')
            self.assertEqual(main(['validate_site.py', tmp]), 1)
            path.write_text('/* url(https://kaisha3.com) */\nbody { background: url(https://kaisha3.com.example/bg.png); }', encoding='utf-8')
            self.assertEqual(main(['validate_site.py', tmp]), 0)


if __name__ == "__main__":
    unittest.main()
