from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


RESOURCE_RELS = {'stylesheet', 'icon', 'preload', 'modulepreload', 'prefetch',
                 'preconnect', 'dns-prefetch', 'manifest'}
CSS_URL = re.compile(r'''url\(\s*["']?([^\s)'";]+)|@import\s+["']([^"']+)''', re.I)


def forbidden_host(value: str) -> bool:
    """判定する: リソースURLのホストが旧サイトを指すか。"""
    try:
        return urlsplit(value.strip()).hostname in {'kaisha3.com', 'www.kaisha3.com'}
    except ValueError:
        return False


def forbidden_css(text: str) -> bool:
    """検出する: CSSの静的url()・import参照に含まれる旧ホスト。"""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    return any(forbidden_host(a or b) for a, b in CSS_URL.findall(text))


class ResourceParser(HTMLParser):
    """収集する: HTMLの自動取得リソースだけを検査した結果。"""

    def __init__(self) -> None:
        super().__init__()
        self.forbidden = False
        self.in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        urls: list[str] = []
        if tag in {'script', 'img', 'iframe', 'audio', 'video', 'source', 'track', 'embed', 'input'}:
            urls.append(values.get('src') or '')
        if tag in {'img', 'source'}:
            urls.extend(part.strip().split(' ')[0] for part in (values.get('srcset') or '').split(','))
        if tag == 'video':
            urls.append(values.get('poster') or '')
        if tag == 'object':
            urls.append(values.get('data') or '')
        if tag == 'link' and RESOURCE_RELS.intersection((values.get('rel') or '').lower().split()):
            urls.append(values.get('href') or '')
        self.forbidden |= any(forbidden_host(url) for url in urls)
        self.forbidden |= forbidden_css(values.get('style') or '')
        if tag == 'style':
            self.in_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_style:
            self.forbidden |= forbidden_css(data)


def main(argv: list[str] | None = None) -> int:
    """検査する: 成果物の静的リソース参照。違反時はstderrと終了値で通知。"""
    argv = sys.argv if argv is None else argv
    if len(argv) != 2:
        print("usage: validate_site.py <site_dir>", file=sys.stderr)
        return 2

    site_dir = Path(argv[1])
    if not site_dir.is_dir():
        print(f"site directory not found: {site_dir}", file=sys.stderr)
        return 2

    violations: list[str] = []
    for path in site_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {'.html', '.css'}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        parser = ResourceParser()
        if path.suffix.lower() == '.html':
            parser.feed(text)
        if parser.forbidden or (path.suffix.lower() == '.css' and forbidden_css(text)):
            violations.append(str(path))

    if violations:
        print("Unexpected kaisha3.com resource references found in built site:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print("Built site validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
