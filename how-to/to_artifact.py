"""Prepares an instruction page for publishing as a claude.ai artifact.

usage: python -I -X utf8 to_artifact.py <page.html> [<out.html>]

An artifact wraps the file in html/head/body by itself, so the wrapper is
stripped and <title> is set to the instruction name from CONTENT.title.
By default writes next to the page: <page>.artifact.html. Prints the result path.
"""
import re
import sys
from pathlib import Path


def convert(html: str) -> str:
    title = re.search(r"\btitle:\s*(['\"`])(.+?)\1", html)
    name = title.group(2).strip() if title else "instruction"
    html = re.sub(r"<!doctype[^>]*>\s*", "", html, flags=re.I)
    html = re.sub(r"</?(html|head|body)\b[^>]*>\s*", "", html, flags=re.I)
    html = re.sub(r"<meta\s+(charset|name=\"viewport\")[^>]*>\s*", "", html, flags=re.I)
    html = re.sub(r"<title>.*?</title>", lambda _: f"<title>{name}</title>", html, count=1, flags=re.S | re.I)
    return html.lstrip()


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".artifact.html")
    out.write_text(convert(src.read_text(encoding="utf8")), encoding="utf8", newline="\n")
    print(out)


if __name__ == "__main__":
    main()
