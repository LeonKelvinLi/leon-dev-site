#!/usr/bin/env python3
"""Build the public static site from an explicit, source-derived allowlist.

Source, audit, test and server files stay in the repository but never enter the
publish directory. The builder never deletes output: an unexpected path makes it
stop before copying anything.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

from subscription_public import generate as generate_subscription_public
from testimonial_gate import TestimonialGateError, testimonial_release_errors
from seo_system import assert_publication_paths, validate_topics


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist"
SITE_HOSTS = {"leonbuilds.org", "www.leonbuilds.org"}
SITE_VERSION_FILE = PurePosixPath("site-version.txt")
HOMEPAGE_DIRECTORY = "homepage"
HOMEPAGE_ASSETS = {
    "_next": {".css", ".js", ".woff", ".woff2"},
    "images": {".ico", ".jpeg", ".jpg", ".png", ".svg", ".webp"},
}

PUBLIC_FILES = (
    "styles.css",
    "assist.css",
    "app.js",
    "assist.js",
    "favicon.ico",
    "apple-touch-icon.png",
    "assets/favicon.svg",
    "assets/og.png",
    "assets/vendor/web-vitals-6.2.1.js",
    "assets/vendor/web-vitals.LICENSE.txt",
    "sitemap.xml",
    "robots.txt",
    "llms.txt",
)

FORBIDDEN_TOP_LEVEL = {
    ".git",
    "content",
    "data",
    "docs",
    "homepage",
    "node_modules",
    "research",
    "server",
    "tests",
    "tools",
}
FORBIDDEN_ROOT_NAMES = {
    ".env",
    ".gitignore",
    "LEARNING_LOG.md",
    "README.md",
    "package.json",
    "package-lock.json",
    "render.yaml",
}
ASSET_SUFFIXES = {
    ".css", ".js", ".ico", ".jpeg", ".jpg", ".png", ".svg",
    ".webp", ".woff", ".woff2", ".mp4", ".webm",
}
GOOGLE_VERIFICATION = re.compile(r"google[a-z0-9]+\.html", re.I)
TOKEN_VERIFICATION = re.compile(r"[a-f0-9]{16,}\.txt", re.I)
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)
CSS_IMPORT = re.compile(r"@import\s+(?:url\(\s*)?['\"]([^'\"]+)['\"]", re.I)
JS_ASSET = re.compile(
    r"['\"](/assets/[A-Za-z0-9_./-]+\.(?:css|js|ico|jpe?g|png|svg|webp|woff2?))(?:[?#][^'\"]*)?['\"]",
    re.I,
)


class StaticBuildError(RuntimeError):
    pass


class ResourceParser(HTMLParser):
    """Collect only resource URLs, never ordinary navigation links."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.resources: list[str] = []

    def add(self, value: str | None) -> None:
        if value and value.strip():
            self.resources.append(value.strip())

    def add_srcset(self, value: str | None) -> None:
        if not value:
            return
        for candidate in value.split(","):
            url = candidate.strip().split(None, 1)[0] if candidate.strip() else ""
            self.add(url)

    def handle_starttag(self, tag: str, raw_attrs: list[tuple[str, str | None]]) -> None:
        attrs = {name.lower(): (value or "") for name, value in raw_attrs}
        tag = tag.lower()
        if tag == "link":
            rels = {part.lower() for part in attrs.get("rel", "").split()}
            if rels & {"apple-touch-icon", "icon", "manifest", "modulepreload", "preload", "stylesheet"}:
                self.add(attrs.get("href"))
        elif tag == "script":
            self.add(attrs.get("src"))
        elif tag in {"audio", "embed", "iframe", "img", "input", "source", "track", "video"}:
            self.add(attrs.get("src"))
            self.add_srcset(attrs.get("srcset"))
            if tag == "video":
                self.add(attrs.get("poster"))
        elif tag == "object":
            self.add(attrs.get("data"))
        elif tag == "use":
            self.add(attrs.get("href") or attrs.get("xlink:href"))
        elif tag == "meta":
            key = (attrs.get("property") or attrs.get("name") or "").lower()
            if key in {"og:image", "og:image:url", "twitter:image", "twitter:image:src"}:
                self.add(attrs.get("content"))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def relative_source(path: Path) -> PurePosixPath:
    resolved = path.resolve()
    if resolved == ROOT or ROOT not in resolved.parents:
        raise StaticBuildError(f"source escapes repository: {path}")
    if path.is_symlink():
        raise StaticBuildError(f"public source may not be a symlink: {path.relative_to(ROOT)}")
    return PurePosixPath(resolved.relative_to(ROOT).as_posix())


def require_source(relative: str | PurePosixPath) -> Path:
    rel = PurePosixPath(relative)
    source = ROOT.joinpath(*rel.parts)
    if not source.is_file():
        raise StaticBuildError(f"required public source is missing: {rel.as_posix()}")
    relative_source(source)
    return source


def sitemap_pages() -> list[PurePosixPath]:
    sitemap = require_source("sitemap.xml")
    try:
        root = ET.parse(sitemap).getroot()
    except ET.ParseError as exc:
        raise StaticBuildError(f"cannot parse sitemap.xml: {exc}") from exc

    pages: list[PurePosixPath] = []
    seen_urls: set[str] = set()
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "loc":
            continue
        url = (element.text or "").strip()
        if url in seen_urls:
            raise StaticBuildError(f"duplicate sitemap URL: {url}")
        seen_urls.add(url)
        try:
            parsed = urllib.parse.urlsplit(url)
        except ValueError as exc:
            raise StaticBuildError(f"invalid sitemap URL: {url}") from exc
        if parsed.scheme != "https" or parsed.netloc != "leonbuilds.org" or parsed.query or parsed.fragment:
            raise StaticBuildError(f"unsafe sitemap URL: {url}")

        route = urllib.parse.unquote(parsed.path or "/")
        if "\x00" in route:
            raise StaticBuildError(f"unsafe sitemap path: {route!r}")
        if route == "/":
            relative = PurePosixPath("index.html")
        elif route.endswith("/"):
            relative = PurePosixPath(route.lstrip("/")) / "index.html"
        else:
            stem = PurePosixPath(route.lstrip("/"))
            file_page = PurePosixPath(stem.as_posix() + ".html")
            directory_page = stem / "index.html"
            file_exists = ROOT.joinpath(*file_page.parts).is_file()
            directory_exists = ROOT.joinpath(*directory_page.parts).is_file()
            if file_exists and directory_exists:
                raise StaticBuildError(f"ambiguous HTML source for sitemap route: {route}")
            relative = directory_page if directory_exists else file_page
        if any(part in {"", ".", ".."} for part in relative.parts):
            raise StaticBuildError(f"unsafe sitemap path: {route!r}")
        require_source(relative)
        pages.append(relative)
    if not pages:
        raise StaticBuildError("sitemap.xml has no public pages")
    try:
        paths = [urllib.parse.urlsplit(url).path for url in seen_urls]
        assert_publication_paths(paths, check_rendered=True)
        validate_topics(paths=paths)
    except (ValueError, KeyError, OSError) as exc:
        raise StaticBuildError(f"SEO publication gate: {exc}") from exc
    return pages


def local_resource(value: str, base: PurePosixPath) -> PurePosixPath | None:
    raw = value.strip()
    if not raw or raw.startswith(("#", "data:", "blob:")):
        return None
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError as exc:
        raise StaticBuildError(f"malformed resource URL in {base}: {value!r}") from exc
    if parsed.scheme or parsed.netloc:
        if parsed.scheme and parsed.scheme not in {"http", "https"}:
            return None
        if (parsed.hostname or "").lower() not in SITE_HOSTS:
            return None
        resource_path = urllib.parse.unquote(parsed.path)
    else:
        resource_path = urllib.parse.unquote(parsed.path)
    if not resource_path:
        return None

    if resource_path.startswith("/"):
        candidate = ROOT / resource_path.lstrip("/")
    else:
        candidate = ROOT.joinpath(*base.parent.parts) / resource_path
    resolved = candidate.resolve()
    if resolved == ROOT or ROOT not in resolved.parents:
        raise StaticBuildError(f"resource escapes repository in {base}: {value!r}")
    relative = PurePosixPath(resolved.relative_to(ROOT).as_posix())
    if relative.parts[0] in FORBIDDEN_TOP_LEVEL or relative.name in FORBIDDEN_ROOT_NAMES:
        raise StaticBuildError(f"public page references forbidden source file: {relative.as_posix()}")
    return relative


def add_resource(
    manifest: dict[PurePosixPath, Path],
    relative: PurePosixPath,
    scan_queue: list[PurePosixPath],
) -> None:
    if relative.suffix.lower() == ".html":
        if relative not in manifest:
            raise StaticBuildError(f"embedded HTML is not a sitemap page: {relative.as_posix()}")
        return
    if relative.suffix.lower() not in ASSET_SUFFIXES:
        raise StaticBuildError(f"unsupported public resource type: {relative.as_posix()}")
    if relative not in manifest:
        source = require_source(relative)
        manifest[relative] = source
        if relative.suffix.lower() in {".css", ".js"}:
            scan_queue.append(relative)


def discover_resources(
    manifest: dict[PurePosixPath, Path],
    pages: list[PurePosixPath],
) -> None:
    scan_queue: list[PurePosixPath] = [
        relative for relative in manifest if relative.suffix.lower() in {".css", ".js"}
    ]
    for page in pages:
        parser = ResourceParser()
        try:
            parser.feed(manifest[page].read_text(encoding="utf-8"))
            parser.close()
        except UnicodeError as exc:
            raise StaticBuildError(f"cannot parse public HTML {page}: {exc}") from exc
        for value in parser.resources:
            relative = local_resource(value, page)
            if relative is not None:
                add_resource(manifest, relative, scan_queue)

    scanned: set[PurePosixPath] = set()
    while scan_queue:
        relative = scan_queue.pop()
        if relative in scanned:
            continue
        scanned.add(relative)
        text = manifest[relative].read_text(encoding="utf-8")
        references: list[str] = []
        if relative.suffix.lower() == ".css":
            references.extend(match.group(2) for match in CSS_URL.finditer(text))
            references.extend(match.group(1) for match in CSS_IMPORT.finditer(text))
        else:
            references.extend(match.group(1) for match in JS_ASSET.finditer(text))
        for value in references:
            target = local_resource(value, relative)
            if target is not None:
                add_resource(manifest, target, scan_queue)


def overlay_homepage(manifest: dict[PurePosixPath, Path]) -> None:
    """Publish the reviewed static export without widening the public root.

    Include every allowed chunk/font because module imports are not HTML asset
    references. Build metadata, server output and arbitrary export files never
    become public. Keep the legacy resource manifest for the remaining pages.
    """
    directory = ROOT / HOMEPAGE_DIRECTORY
    if directory.is_symlink() or not directory.is_dir():
        raise StaticBuildError("homepage must be a real directory containing the reviewed export")
    for name in ("index.html", "favicon.svg"):
        manifest[PurePosixPath(name)] = require_source(f"{HOMEPAGE_DIRECTORY}/{name}")
    for name in HOMEPAGE_ASSETS:
        asset_directory = directory / name
        if asset_directory.is_symlink() or not asset_directory.is_dir():
            raise StaticBuildError(f"homepage asset directory is missing or unsafe: {name}")

    for source in sorted(directory.rglob("*")):
        relative = PurePosixPath(source.relative_to(directory).as_posix())
        if source.is_symlink():
            raise StaticBuildError(f"homepage source may not be a symlink: {relative}")
        if any(part.startswith(".") for part in relative.parts):
            raise StaticBuildError(f"hidden path is not a homepage asset: {relative}")
        if relative.as_posix() in {"index.html", "favicon.svg"}:
            if not source.is_file():
                raise StaticBuildError(f"homepage source must be a file: {relative}")
            continue
        allowed_suffixes = HOMEPAGE_ASSETS.get(relative.parts[0])
        if allowed_suffixes is None:
            raise StaticBuildError(f"unexpected homepage export path: {relative}")
        if source.is_dir():
            continue
        if not source.is_file() or relative.suffix.lower() not in allowed_suffixes:
            raise StaticBuildError(f"unsupported homepage asset: {relative}")
        if relative in manifest:
            raise StaticBuildError(f"homepage asset would overwrite a legacy resource: {relative}")
        manifest[relative] = require_source(f"{HOMEPAGE_DIRECTORY}/{relative.as_posix()}")

    # Absolute resource URLs in the export resolve in the combined publication,
    # not in its source storage directory. Fail before writing any missing asset.
    parser = ResourceParser()
    parser.feed(manifest[PurePosixPath("index.html")].read_text(encoding="utf-8"))
    parser.close()
    for value in parser.resources:
        relative = local_resource(value, PurePosixPath("index.html"))
        if relative is not None and relative not in manifest:
            raise StaticBuildError(f"homepage references an unpublished resource: {relative}")


def build_manifest() -> dict[PurePosixPath, Path]:
    pages = sitemap_pages()
    manifest: dict[PurePosixPath, Path] = {page: require_source(page) for page in pages}
    for name in PUBLIC_FILES:
        relative = PurePosixPath(name)
        manifest[relative] = require_source(relative)

    for source in sorted(ROOT.iterdir()):
        if not source.is_file():
            continue
        if GOOGLE_VERIFICATION.fullmatch(source.name) or TOKEN_VERIFICATION.fullmatch(source.name):
            relative = PurePosixPath(source.name)
            manifest[relative] = require_source(relative)

    discover_resources(manifest, pages)
    overlay_homepage(manifest)
    for relative in manifest:
        if relative.parts[0] in FORBIDDEN_TOP_LEVEL or relative.name in FORBIDDEN_ROOT_NAMES:
            raise StaticBuildError(f"forbidden path entered static manifest: {relative.as_posix()}")
        if relative.suffix.lower() in {".csv", ".json", ".md", ".py", ".yaml", ".yml"}:
            raise StaticBuildError(f"source file entered static manifest: {relative.as_posix()}")
    documents = {
        relative.as_posix(): source.read_text(encoding="utf-8")
        for relative, source in manifest.items()
        if relative.suffix.lower() == ".html" or relative.as_posix() == "llms.txt"
    }
    try:
        release_errors = testimonial_release_errors(documents, ROOT)
    except TestimonialGateError as exc:
        raise StaticBuildError(f"testimonial release gate is invalid: {exc}") from exc
    if release_errors:
        detail = "; ".join(release_errors[:8])
        if len(release_errors) > 8:
            detail += f"; and {len(release_errors) - 8} more"
        raise StaticBuildError("testimonial release gate blocked public output: " + detail)
    # Historical content has passed its original proof gates. Publish the new
    # one-offer surfaces, keeping the exact inbound routes and all business data.
    # Run the release gate again on the actual public documents.
    manifest.update(generate_subscription_public(pages))
    discover_resources(manifest, pages)
    public_documents = {str(relative): source.read_text(encoding="utf-8")
        for relative, source in manifest.items()
        if relative.suffix.lower() == ".html" or str(relative) == "llms.txt"}
    public_errors = testimonial_release_errors(public_documents, ROOT)
    if public_errors:
        raise StaticBuildError("subscription public proof gate: " + "; ".join(public_errors))
    return dict(sorted(manifest.items(), key=lambda item: item[0].as_posix()))


def public_fingerprint(manifest: dict[PurePosixPath, Path]) -> str:
    """Hash the exact allowlisted source bytes with unambiguous framing.

    The generated marker lets a post-deploy job distinguish "Render accepted the
    commit" from "the CDN is serving these exact public files". It deliberately
    excludes itself, so the value is deterministic and has no recursive input.
    """
    digest = hashlib.sha256(b"leon-builds-static-v1\0")
    for relative, source in sorted(manifest.items(), key=lambda item: item[0].as_posix()):
        name = relative.as_posix().encode("utf-8")
        content = source.read_bytes()
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def generated_files(manifest: dict[PurePosixPath, Path]) -> dict[PurePosixPath, bytes]:
    return {SITE_VERSION_FILE: (public_fingerprint(manifest) + "\n").encode("ascii")}


def verify_stable_sources(
    manifest: dict[PurePosixPath, Path],
    generated: dict[PurePosixPath, bytes],
) -> None:
    if generated_files(manifest) != generated:
        raise StaticBuildError("public source files changed during the static build; retry")


def safe_output(value: str) -> Path:
    requested = Path(value).expanduser()
    if requested.name != "dist":
        raise StaticBuildError("output directory must be named 'dist'")
    if requested.is_symlink():
        raise StaticBuildError(f"output may not be a symlink: {requested}")
    output = requested.resolve()
    if output == ROOT or output in ROOT.parents:
        raise StaticBuildError(f"refusing repository/ancestor output: {output}")
    filesystem_root = Path(output.anchor).resolve()
    if output.parent in {filesystem_root, Path.home().resolve()}:
        raise StaticBuildError(f"refusing broad output location: {output}")
    if ROOT in output.parents and output != DEFAULT_OUTPUT.resolve():
        raise StaticBuildError(f"the only allowed in-repository output is {DEFAULT_OUTPUT}")
    if output.exists() and not output.is_dir():
        raise StaticBuildError(f"output exists and is not a directory: {output}")
    if not output.parent.is_dir():
        raise StaticBuildError(f"output parent must already exist: {output.parent}")
    return output


def expected_directories(paths) -> set[PurePosixPath]:
    directories: set[PurePosixPath] = set()
    for relative in paths:
        parent = relative.parent
        while parent != PurePosixPath("."):
            directories.add(parent)
            parent = parent.parent
    return directories


def validate_existing(
    output: Path,
    manifest: dict[PurePosixPath, Path],
    generated: dict[PurePosixPath, bytes],
) -> None:
    if not output.exists():
        return
    allowed_files = set(manifest) | set(generated)
    allowed_directories = expected_directories(allowed_files)
    problems: list[str] = []
    for path in sorted(output.rglob("*")):
        relative = PurePosixPath(path.relative_to(output).as_posix())
        if path.is_symlink():
            problems.append(f"symlink {relative}")
        elif path.is_dir():
            if relative not in allowed_directories:
                problems.append(f"unexpected directory {relative}")
        elif path.is_file():
            if relative not in allowed_files:
                problems.append(f"unexpected file {relative}")
        else:
            problems.append(f"unsupported filesystem entry {relative}")
    if problems:
        detail = "; ".join(problems[:8])
        if len(problems) > 8:
            detail += f"; and {len(problems) - 8} more"
        raise StaticBuildError(
            "output contains paths outside the public manifest; nothing was changed: " + detail
        )


def check_output(
    output: Path,
    manifest: dict[PurePosixPath, Path],
    generated: dict[PurePosixPath, bytes],
) -> None:
    validate_existing(output, manifest, generated)
    if not output.exists():
        return
    missing: list[str] = []
    changed: list[str] = []
    for relative, source in manifest.items():
        destination = output.joinpath(*relative.parts)
        if not destination.is_file():
            missing.append(relative.as_posix())
        elif source.read_bytes() != destination.read_bytes():
            changed.append(relative.as_posix())
    for relative, content in generated.items():
        destination = output.joinpath(*relative.parts)
        if not destination.is_file():
            missing.append(relative.as_posix())
        elif destination.read_bytes() != content:
            changed.append(relative.as_posix())
    if missing or changed:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing[:8]))
        if changed:
            details.append("stale: " + ", ".join(changed[:8]))
        raise StaticBuildError("existing output is not current; run the build (" + "; ".join(details) + ")")


def write_output(
    output: Path,
    manifest: dict[PurePosixPath, Path],
    generated: dict[PurePosixPath, bytes],
) -> None:
    # Complete validation happens before the first mkdir/copy. We never remove a
    # path, even when the desired manifest changes.
    validate_existing(output, manifest, generated)
    output.mkdir(exist_ok=True)
    paths = set(manifest) | set(generated)
    for directory in sorted(expected_directories(paths), key=lambda item: (len(item.parts), item.as_posix())):
        output.joinpath(*directory.parts).mkdir(exist_ok=True)
    for relative, source in manifest.items():
        shutil.copyfile(source, output.joinpath(*relative.parts))
    for relative, content in generated.items():
        output.joinpath(*relative.parts).write_bytes(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate only; never create or modify output")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="output directory (must be named dist)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = build_manifest()
        generated = generated_files(manifest)
        output = safe_output(args.output)
        if args.check:
            check_output(output, manifest, generated)
            verify_stable_sources(manifest, generated)
            state = "current" if output.exists() else "not present (manifest validated read-only)"
            print(
                f"static build check passed — {len(manifest)} allowlisted + "
                f"{len(generated)} generated files; output {state}"
            )
        else:
            write_output(output, manifest, generated)
            check_output(output, manifest, generated)
            verify_stable_sources(manifest, generated)
            print(
                f"static build complete — {len(manifest)} allowlisted + "
                f"{len(generated)} generated files -> {output}"
            )
        return 0
    except (OSError, StaticBuildError, UnicodeError) as exc:
        print(f"static build failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
