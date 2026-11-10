#!/usr/bin/env python3
"""Plan or explicitly submit changed public URLs to IndexNow.

The default command is a dry run: it derives URLs from two Git revisions and
prints the request that would be sent without making any network calls. A real
submission additionally proves that the live host serves the expected static
site fingerprint and IndexNow key before POSTing.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

import build_static


ROOT = Path(__file__).resolve().parents[1]
SITE_ORIGIN = "https://leonbuilds.org"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
INDEXNOW_KEY_FILE = "b20f1e412f2cff8af636fe5676cfdbcd.txt"
SITE_VERSION_FILE = "site-version.txt"
MAX_URLS = 10_000
ZERO_REVISION = "0" * 40
FINGERPRINT = re.compile(r"[0-9a-f]{64}")
INDEXNOW_KEY = re.compile(r"[0-9a-fA-F]{8,128}")
NO_PAGE_SIGNAL_FILES = {
    "sitemap.xml",
    SITE_VERSION_FILE,
    INDEXNOW_KEY_FILE,
    "google632f06756dffc4ba.html",
}


class IndexNowError(RuntimeError):
    pass


class CanonicalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        values = {name.lower(): (value or "") for name, value in attrs}
        if "canonical" in values.get("rel", "").lower().split():
            href = values.get("href", "").strip()
            if href:
                self.canonicals.append(href)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def canonical_from_html(text: str, label: str) -> str | None:
    parser = CanonicalParser()
    try:
        parser.feed(text)
        parser.close()
    except (UnicodeError, ValueError) as exc:
        raise IndexNowError(f"cannot parse canonical in {label}: {exc}") from exc
    if len(parser.canonicals) > 1:
        raise IndexNowError(f"multiple canonical tags in {label}: {', '.join(parser.canonicals)}")
    return parser.canonicals[0] if parser.canonicals else None


def normalize_origin(origin: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(origin.rstrip("/"))
        port = parsed.port
    except ValueError as exc:
        raise IndexNowError(f"unsafe site origin: {origin!r}") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or port is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise IndexNowError(f"unsafe site origin: {origin!r}")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc.lower(), "", "", ""))


def validate_public_url(url: str, origin: str = SITE_ORIGIN) -> str:
    expected = urllib.parse.urlsplit(normalize_origin(origin))
    try:
        parsed = urllib.parse.urlsplit(url.strip())
    except ValueError as exc:
        raise IndexNowError(f"invalid public URL: {url!r}") from exc
    path = parsed.path or "/"
    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() != expected.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not path.startswith("/")
    ):
        raise IndexNowError(f"URL is not a clean same-origin HTTPS URL: {url!r}")
    return urllib.parse.urlunsplit(("https", expected.netloc, path, "", ""))


def parse_sitemap(text: str, origin: str = SITE_ORIGIN, label: str = "sitemap.xml") -> dict[str, str]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise IndexNowError(f"cannot parse {label}: {exc}") from exc
    entries: dict[str, str] = {}
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "url":
            continue
        loc = ""
        lastmod = ""
        for child in node:
            local = child.tag.rsplit("}", 1)[-1]
            if local == "loc":
                loc = (child.text or "").strip()
            elif local == "lastmod":
                lastmod = (child.text or "").strip()
        if not loc:
            raise IndexNowError(f"{label} contains a URL entry without loc")
        url = validate_public_url(loc, origin)
        if url in entries:
            raise IndexNowError(f"duplicate URL in {label}: {url}")
        entries[url] = lastmod
    if not entries:
        raise IndexNowError(f"{label} contains no URLs")
    if len(entries) > MAX_URLS:
        raise IndexNowError(f"{label} contains {len(entries)} URLs; IndexNow accepts at most {MAX_URLS}")
    return entries


def git(root: Path, *args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=not binary,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace") if binary else result.stderr
        raise IndexNowError(f"git {' '.join(args)} failed: {stderr.strip()}")
    return result.stdout


def revision_exists(root: Path, revision: str) -> bool:
    if revision == ZERO_REVISION:
        return False
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
        cwd=root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def git_text(root: Path, revision: str, relative: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IndexNowError(f"cannot decode {relative} at {revision}") from exc


def changed_paths(root: Path, before: str, after: str) -> list[tuple[str, str | None, str | None]]:
    raw = git(root, "diff", "--name-status", "-z", before, after, binary=True)
    assert isinstance(raw, bytes)
    fields = raw.decode("utf-8", errors="strict").split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    changes: list[tuple[str, str | None, str | None]] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        kind = status[:1]
        if kind in {"R", "C"}:
            if index + 1 >= len(fields):
                raise IndexNowError("malformed renamed-path output from git diff")
            old_path, new_path = fields[index], fields[index + 1]
            index += 2
        else:
            if index >= len(fields):
                raise IndexNowError("malformed path output from git diff")
            path = fields[index]
            index += 1
            old_path = None if kind == "A" else path
            new_path = None if kind == "D" else path
        changes.append((kind, old_path, new_path))
    return changes


def _add_canonical(urls: set[str], html: str | None, label: str, origin: str) -> None:
    if html is None:
        return
    canonical = canonical_from_html(html, label)
    if canonical:
        urls.add(validate_public_url(canonical, origin))


def derive_changed_urls(
    root: Path,
    before: str,
    after: str,
    origin: str = SITE_ORIGIN,
    public_paths: set[str] | None = None,
) -> list[str]:
    """Derive changed, added and removed URLs from committed public state."""
    origin = normalize_origin(origin)
    after_sitemap_text = (git_text(root, after, "content/subscription-public/sitemap.xml")
                          or git_text(root, after, "sitemap.xml"))
    if after_sitemap_text is None:
        raise IndexNowError(f"sitemap.xml is missing at {after}")
    after_sitemap = parse_sitemap(after_sitemap_text, origin, f"sitemap.xml at {after}")
    if not revision_exists(root, before):
        return sorted(after_sitemap)

    before_sitemap_text = (git_text(root, before, "content/subscription-public/sitemap.xml")
                           or git_text(root, before, "sitemap.xml"))
    before_sitemap = (
        parse_sitemap(before_sitemap_text, origin, f"sitemap.xml at {before}")
        if before_sitemap_text is not None
        else {}
    )
    urls = {
        url
        for url in set(before_sitemap) | set(after_sitemap)
        if before_sitemap.get(url) != after_sitemap.get(url)
    }
    if public_paths is None:
        public_paths = {path.as_posix() for path in build_static.build_manifest()}

    shared_public_asset_changed = False
    for _kind, old_path, new_path in changed_paths(root, before, after):
        if old_path and old_path.endswith(".html"):
            _add_canonical(urls, git_text(root, before, old_path), f"{old_path} at {before}", origin)
        if new_path and new_path.endswith(".html"):
            _add_canonical(urls, git_text(root, after, new_path), f"{new_path} at {after}", origin)
        for candidate in (old_path, new_path):
            if (
                candidate
                and not candidate.endswith(".html")
                and candidate in public_paths
                and candidate not in NO_PAGE_SIGNAL_FILES
            ):
                shared_public_asset_changed = True

    if shared_public_asset_changed:
        urls.update(after_sitemap)
    normalized = sorted(validate_public_url(url, origin) for url in urls)
    if len(normalized) > MAX_URLS:
        raise IndexNowError(f"change set contains {len(normalized)} URLs; maximum is {MAX_URLS}")
    return normalized


def read_key(root: Path = ROOT) -> str:
    path = root / INDEXNOW_KEY_FILE
    try:
        key = path.read_text(encoding="ascii").strip()
    except OSError as exc:
        raise IndexNowError(f"cannot read IndexNow key file {path}: {exc}") from exc
    if not INDEXNOW_KEY.fullmatch(key):
        raise IndexNowError(f"IndexNow key file has an invalid value: {path}")
    if key != Path(INDEXNOW_KEY_FILE).stem:
        raise IndexNowError("IndexNow key body must exactly match its public filename")
    return key


def resolved_commit(root: Path, revision: str) -> str:
    value = git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")
    assert isinstance(value, str)
    return value.strip()


def ensure_submit_checkout(root: Path, after: str, public_paths: set[str]) -> None:
    if resolved_commit(root, after) != resolved_commit(root, "HEAD"):
        raise IndexNowError("--after-ref must resolve to the currently checked-out HEAD for submission")
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", *sorted(public_paths)],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise IndexNowError(f"cannot inspect public checkout state: {result.stderr.strip()}")
    if result.stdout.strip():
        raise IndexNowError("public build sources are dirty; commit or restore them before submission")


def make_payload(urls: list[str], key: str, origin: str = SITE_ORIGIN) -> dict[str, object]:
    origin = normalize_origin(origin)
    if not urls:
        raise IndexNowError("cannot build an IndexNow payload without URLs")
    normalized = [validate_public_url(url, origin) for url in urls]
    if len(normalized) != len(set(normalized)):
        raise IndexNowError("IndexNow URL list contains duplicates")
    if len(normalized) > MAX_URLS:
        raise IndexNowError(f"IndexNow URL list exceeds {MAX_URLS}")
    if not INDEXNOW_KEY.fullmatch(key):
        raise IndexNowError("invalid IndexNow key")
    if key != Path(INDEXNOW_KEY_FILE).stem:
        raise IndexNowError("IndexNow key must exactly match its public filename")
    host = urllib.parse.urlsplit(origin).netloc
    return {
        "host": host,
        "key": key,
        "keyLocation": f"{origin}/{INDEXNOW_KEY_FILE}",
        "urlList": normalized,
    }


def fetch_text(
    url: str,
    timeout: float = 20,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        headers={"Cache-Control": "no-cache", "User-Agent": "LeonBuilds-SearchProduction/1.0"},
    )
    try:
        with opener(request, timeout=timeout) as response:
            status_value = getattr(response, "status", None)
            status = int(status_value if status_value is not None else response.getcode())
            final_url = response.geturl() if hasattr(response, "geturl") else url
            body = response.read().decode("utf-8")
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
    return status, body


def verify_live_proof(
    expected_fingerprint: str,
    key: str,
    origin: str = SITE_ORIGIN,
    timeout: float = 20,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> None:
    if not FINGERPRINT.fullmatch(expected_fingerprint):
        raise IndexNowError("expected fingerprint must be exactly 64 lowercase hexadecimal characters")
    origin = normalize_origin(origin)
    nonce = f"{expected_fingerprint}-{time.time_ns()}"
    _, live_fingerprint = fetch_text(
        f"{origin}/{SITE_VERSION_FILE}?verify={nonce}", timeout=timeout, opener=opener
    )
    if live_fingerprint.strip() != expected_fingerprint:
        raise IndexNowError(
            "live site fingerprint does not match the requested deployment: "
            f"expected {expected_fingerprint}, got {live_fingerprint.strip()!r}"
        )
    _, live_key = fetch_text(
        f"{origin}/{INDEXNOW_KEY_FILE}?verify={nonce}", timeout=timeout, opener=opener
    )
    if live_key.strip() != key:
        raise IndexNowError("live IndexNow key does not match the repository key")
    # Recheck after the key fetch so a deployment transition cannot race the
    # proof and cause URLs for one revision to be submitted against another.
    _, final_fingerprint = fetch_text(
        f"{origin}/{SITE_VERSION_FILE}?verify={nonce}-final", timeout=timeout, opener=opener
    )
    if final_fingerprint.strip() != expected_fingerprint:
        raise IndexNowError("live site fingerprint changed while verifying the deployment")


def submit_payload(
    payload: dict[str, object],
    endpoint: str = INDEXNOW_ENDPOINT,
    timeout: float = 30,
    opener: Callable[..., object] = urllib.request.urlopen,
) -> int:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "LeonBuilds-SearchProduction/1.0",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=timeout) as response:
            status_value = getattr(response, "status", None)
            status = int(status_value if status_value is not None else response.getcode())
            final_url = response.geturl() if hasattr(response, "geturl") else endpoint
            body = response.read(512).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read(512).decode("utf-8", errors="replace")
        finally:
            exc.close()
        raise IndexNowError(f"IndexNow returned HTTP {exc.code}: {detail}".rstrip()) from exc
    except (OSError, urllib.error.URLError) as exc:
        raise IndexNowError(f"IndexNow request failed: {exc}") from exc
    if status not in {200, 202}:
        raise IndexNowError(f"IndexNow returned HTTP {status}: {body}".rstrip())
    if final_url != endpoint:
        raise IndexNowError(f"IndexNow endpoint redirected to {final_url}")
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-ref", default="HEAD^", help="Git revision before the deployment")
    parser.add_argument("--after-ref", default="HEAD", help="deployed Git revision")
    parser.add_argument("--submit", action="store_true", help="verify live proof and send the request")
    parser.add_argument("--expected-fingerprint", help="64-hex fingerprint required with --submit")
    parser.add_argument("--origin", default=SITE_ORIGIN)
    parser.add_argument("--endpoint", default=INDEXNOW_ENDPOINT)
    parser.add_argument("--timeout", type=float, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.timeout <= 0:
            raise IndexNowError("--timeout must be positive")
        urls = derive_changed_urls(ROOT, args.before_ref, args.after_ref, args.origin)
        if not urls:
            print("indexnow: no changed public URLs; no request sent")
            return 0
        key = read_key(ROOT)
        payload = make_payload(urls, key, args.origin)
        if not args.submit:
            print("indexnow: dry run; no network request sent")
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if not args.expected_fingerprint:
            raise IndexNowError("--expected-fingerprint is required with --submit when URLs changed")
        public_manifest = build_static.build_manifest()
        ensure_submit_checkout(ROOT, args.after_ref, {path.as_posix() for path in public_manifest})
        local_fingerprint = build_static.public_fingerprint(public_manifest)
        if args.expected_fingerprint != local_fingerprint:
            raise IndexNowError(
                "expected fingerprint does not match this checkout's public build: "
                f"expected {args.expected_fingerprint}, local {local_fingerprint}"
            )
        verify_live_proof(
            args.expected_fingerprint,
            key,
            args.origin,
            timeout=args.timeout,
        )
        status = submit_payload(payload, args.endpoint, timeout=args.timeout)
        print(f"indexnow: HTTP {status}; submitted {len(urls)} changed URL(s)")
        return 0
    except (IndexNowError, build_static.StaticBuildError, OSError, UnicodeError) as exc:
        print(f"indexnow failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
