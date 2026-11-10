#!/usr/bin/env python3
"""Wait for an exact deployment and validate its live crawl foundations."""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

import build_static

from indexnow import (
    FINGERPRINT,
    INDEXNOW_KEY_FILE,
    ROOT,
    SITE_ORIGIN,
    SITE_VERSION_FILE,
    IndexNowError,
    fetch_text,
    normalize_origin,
    parse_sitemap,
    read_key,
    validate_public_url,
)


class PageSignalsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.noindex: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() not in {"link", "meta"}:
            return
        values = {name.lower(): (value or "") for name, value in attrs}
        if tag.lower() == "link" and "canonical" in values.get("rel", "").lower().split():
            href = values.get("href", "").strip()
            if href:
                self.canonicals.append(href)
        if tag.lower() == "meta" and values.get("name", "").lower() in {
            "robots",
            "googlebot",
            "bingbot",
        }:
            directives = {
                part.strip().lower()
                for part in re.split(r"[,\s]+", values.get("content", ""))
                if part.strip()
            }
            if "noindex" in directives or "none" in directives:
                self.noindex.append(values.get("name", "").lower())

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def wait_for_fingerprint(
    expected: str,
    origin: str = SITE_ORIGIN,
    wait_seconds: float = 900,
    poll_seconds: float = 10,
    timeout: float = 20,
    opener: Callable[..., object] = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    if not FINGERPRINT.fullmatch(expected):
        raise IndexNowError("expected fingerprint must be exactly 64 lowercase hexadecimal characters")
    if wait_seconds < 0 or poll_seconds <= 0:
        raise IndexNowError("wait seconds must be non-negative and poll seconds must be positive")
    origin = normalize_origin(origin)
    deadline = clock() + wait_seconds
    attempts = 0
    last_problem = "not checked"
    while True:
        attempts += 1
        try:
            _, body = fetch_text(
                f"{origin}/{SITE_VERSION_FILE}?deployment-check={expected}-{attempts}",
                timeout=timeout,
                opener=opener,
            )
            actual = body.strip()
            if actual == expected:
                return attempts
            last_problem = f"served {actual!r}"
        except IndexNowError as exc:
            last_problem = str(exc)
        now = clock()
        if now >= deadline:
            raise IndexNowError(
                f"timed out waiting for live fingerprint {expected} after {attempts} attempt(s): "
                f"{last_problem}"
            )
        sleeper(min(poll_seconds, max(0.0, deadline - now)))


def _validate_robots(text: str, origin: str) -> None:
    directives = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        directives.append((name.strip().lower(), value.strip()))
    sitemap_url = f"{origin}/sitemap.xml"
    if ("sitemap", sitemap_url) not in directives:
        raise IndexNowError(f"live robots.txt does not advertise {sitemap_url}")
    if any(name == "disallow" and value == "/" for name, value in directives):
        raise IndexNowError("live robots.txt contains a full-site Disallow: /")


def _validate_page(html: str, url: str, origin: str) -> None:
    parser = PageSignalsParser()
    try:
        parser.feed(html)
        parser.close()
    except (UnicodeError, ValueError) as exc:
        raise IndexNowError(f"cannot parse live page {url}: {exc}") from exc
    # Vinext serializes the origin-only homepage canonical without the optional
    # trailing slash. That URL is identical to the sitemap's explicit root `/`.
    canonicals = [f"{origin}/" if value == origin else value for value in parser.canonicals]
    if canonicals != [url]:
        raise IndexNowError(
            f"live page {url} canonical tags are {parser.canonicals!r}, expected exactly {[url]!r}"
        )
    validate_public_url(canonicals[0], origin)
    if parser.noindex:
        raise IndexNowError(f"live page {url} has noindex in {', '.join(parser.noindex)}")


def fetch_live_page(
    url: str,
    timeout: float,
    opener: Callable[..., object],
) -> str:
    request = urllib.request.Request(
        url,
        headers={"Cache-Control": "no-cache", "User-Agent": "LeonBuilds-SearchProduction/1.0"},
    )
    try:
        with opener(request, timeout=timeout) as response:
            status_value = getattr(response, "status", None)
            status = int(status_value if status_value is not None else response.getcode())
            final_url = response.geturl() if hasattr(response, "geturl") else url
            headers = getattr(response, "headers", {})
            content_type = headers.get("Content-Type", "")
            if hasattr(headers, "get_all"):
                x_robots = ",".join(headers.get_all("X-Robots-Tag", []))
            else:
                x_robots = headers.get("X-Robots-Tag", "")
            html = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        try:
            exc.read(512)
        finally:
            exc.close()
        raise IndexNowError(f"GET {url} returned HTTP {exc.code}") from exc
    except (OSError, UnicodeError, urllib.error.URLError) as exc:
        raise IndexNowError(f"GET {url} failed: {exc}") from exc
    if status != 200:
        raise IndexNowError(f"GET {url} returned HTTP {status}")
    if final_url != url:
        raise IndexNowError(f"GET {url} redirected to {final_url}")
    if "text/html" not in content_type.lower():
        raise IndexNowError(f"live page {url} returned non-HTML Content-Type {content_type!r}")
    directives = {
        part.strip().lower()
        for part in re.split(r"[,\s]+", x_robots)
        if part.strip()
    }
    if "noindex" in directives or "none" in directives:
        raise IndexNowError(f"live page {url} has noindex in X-Robots-Tag")
    return html


def check_live_foundations(
    origin: str = SITE_ORIGIN,
    timeout: float = 20,
    opener: Callable[..., object] = urllib.request.urlopen,
    root: Path = ROOT,
) -> dict[str, int]:
    origin = normalize_origin(origin)
    key = read_key(root)
    _, robots = fetch_text(f"{origin}/robots.txt", timeout=timeout, opener=opener)
    _validate_robots(robots, origin)

    _, sitemap_text = fetch_text(f"{origin}/sitemap.xml", timeout=timeout, opener=opener)
    sitemap = parse_sitemap(sitemap_text, origin, "live sitemap.xml")
    try:
        # Validate the composed public sitemap, not the archived page inventory.
        public_sitemap = root / "content/subscription-public/sitemap.xml"
        sitemap_path = public_sitemap if public_sitemap.is_file() else root / "sitemap.xml"
        local_sitemap_text = sitemap_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise IndexNowError(f"cannot read local sitemap.xml: {exc}") from exc
    local_sitemap = parse_sitemap(local_sitemap_text, origin, "local sitemap.xml")
    if sitemap != local_sitemap:
        raise IndexNowError("live sitemap URLs or lastmod values do not match this checkout")

    _, llms = fetch_text(f"{origin}/llms.txt", timeout=timeout, opener=opener)
    if not re.search(r"\bLeon\s*Builds\b", llms, re.I) or origin not in llms:
        raise IndexNowError("live llms.txt is empty or missing the Leon Builds identity and canonical origin")

    _, live_key = fetch_text(f"{origin}/{INDEXNOW_KEY_FILE}", timeout=timeout, opener=opener)
    if live_key.strip() != key:
        raise IndexNowError("live IndexNow key does not match the repository key")

    for url in sitemap:
        html = fetch_live_page(url, timeout=timeout, opener=opener)
        _validate_page(html, url, origin)
    return {"sitemap_urls": len(sitemap), "pages_checked": len(sitemap)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-fingerprint", required=True)
    parser.add_argument("--origin", default=SITE_ORIGIN)
    parser.add_argument("--wait-seconds", type=float, default=900)
    parser.add_argument("--poll-seconds", type=float, default=10)
    parser.add_argument("--timeout", type=float, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.timeout <= 0:
            raise IndexNowError("--timeout must be positive")
        local_fingerprint = build_static.public_fingerprint(build_static.build_manifest())
        if args.expected_fingerprint != local_fingerprint:
            raise IndexNowError(
                "expected fingerprint does not match this checkout's public build: "
                f"expected {args.expected_fingerprint}, local {local_fingerprint}"
            )
        attempts = wait_for_fingerprint(
            args.expected_fingerprint,
            args.origin,
            wait_seconds=args.wait_seconds,
            poll_seconds=args.poll_seconds,
            timeout=args.timeout,
        )
        result = check_live_foundations(args.origin, timeout=args.timeout)
        print(
            f"live search check passed — fingerprint matched after {attempts} attempt(s); "
            f"{result['pages_checked']} sitemap page(s) returned 200 with exact canonicals and no noindex"
        )
        return 0
    except (IndexNowError, build_static.StaticBuildError, OSError, UnicodeError) as exc:
        print(f"live search check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
