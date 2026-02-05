#!/usr/bin/env python3
"""Check external links in documentation."""

import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from markdown_it import MarkdownIt


def load_ignore_list() -> set[str]:
    """Load URLs to ignore from .linkcheck-ignore file."""
    ignore_file = Path(".linkcheck-ignore")
    if not ignore_file.exists():
        return set()

    ignored = set()
    for line in ignore_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ignored.add(line)
    return ignored


def extract_urls(content: str) -> list[str]:
    """Extract HTTP/HTTPS URLs from markdown using markdown-it-py parser."""
    md = MarkdownIt()
    tokens = md.parse(content)
    urls = []

    def extract_from_tokens(token_list):
        for token in token_list:
            if token.type == "link_open":
                href = token.attrGet("href")
                if href and (href.startswith("http://") or href.startswith("https://")):
                    urls.append(href)
            if token.children:
                extract_from_tokens(token.children)

    extract_from_tokens(tokens)
    return urls


def check_url(url: str) -> tuple[bool, str]:
    """Check if URL is valid. Returns (is_valid, message)."""
    try:
        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MekaraLinkChecker/1.0)"},
            method="HEAD",
        )
        with urlopen(req, timeout=10) as response:
            status = response.status
            if 200 <= status < 400:
                return True, f"OK ({status})"
            else:
                return False, f"Unexpected status {status}"
    except HTTPError as e:
        return False, f"HTTP {e.code}"
    except URLError as e:
        return False, f"Connection error: {e.reason}"
    except TimeoutError:
        return False, "Timeout after 10 seconds"
    except Exception as e:
        return False, f"Error: {type(e).__name__}: {e}"


def main() -> int:
    """Check external links in docs."""
    if len(sys.argv) > 1:
        target_file = Path(sys.argv[1])
        if not target_file.exists():
            print(f"Error: File not found: {target_file}", file=sys.stderr)
            return 1
        md_files = [target_file]
    else:
        docs_dir = Path("docs/docs")
        if not docs_dir.exists():
            print(f"Error: Directory not found: {docs_dir}", file=sys.stderr)
            return 1
        md_files = sorted(docs_dir.rglob("*.md"))

    ignored_urls = load_ignore_list()
    if ignored_urls:
        print(f"Ignoring {len(ignored_urls)} URL(s) from .linkcheck-ignore")

    url_to_files = {}
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        urls = extract_urls(content)
        for url in urls:
            if url in ignored_urls:
                continue
            if url not in url_to_files:
                url_to_files[url] = []
            url_to_files[url].append(md_file)

    if not url_to_files:
        print("No external links found.")
        return 0

    print(f"Checking {len(url_to_files)} unique external URLs...")
    broken_links = []

    for url, files in sorted(url_to_files.items()):
        is_valid, message = check_url(url)
        if not is_valid:
            broken_links.append((url, message, files))
            print(f"✗ {url}")
            print(f"  Status: {message}")
            for file in files:
                print(f"  Found in: {file}")
        else:
            print(f"✓ {url}")

    if broken_links:
        print(f"\n{len(broken_links)} broken link(s) found:")
        for url, message, files in broken_links:
            print(f"\n  {url}")
            print(f"  Status: {message}")
            for file in files:
                print(f"  Found in: {file}")
        return 1

    print(f"\nAll {len(url_to_files)} external links are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
