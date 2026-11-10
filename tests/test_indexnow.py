from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import indexnow


KEY = Path(indexnow.INDEXNOW_KEY_FILE).stem


def sitemap(entries: list[tuple[str, str]]) -> str:
    rows = "".join(
        f"<url><loc>https://leonbuilds.org{route}</loc><lastmod>{lastmod}</lastmod></url>"
        for route, lastmod in entries
    )
    return f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>'


class FakeResponse:
    def __init__(self, status: int, body: str = "", url: str | None = None) -> None:
        self.status = status
        self.body = body.encode("utf-8")
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def getcode(self) -> int:
        return self.status

    def geturl(self) -> str:
        return self.url or ""

    def read(self, amount: int = -1) -> bytes:
        return self.body if amount < 0 else self.body[:amount]


class GitFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self, message: str) -> str:
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", message], cwd=self.root, check=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, check=True, capture_output=True, text=True
        ).stdout.strip()


class ChangedUrlTests(GitFixture):
    def test_modified_added_and_deleted_html_use_both_canonicals(self) -> None:
        self.write("sitemap.xml", sitemap([("/old", "2026-08-24"), ("/shared", "2026-08-24")]))
        self.write("old.html", '<link rel="canonical" href="https://leonbuilds.org/old">')
        self.write("shared.html", '<link rel="canonical" href="https://leonbuilds.org/shared"><p>one</p>')
        before = self.commit("before")

        (self.root / "old.html").unlink()
        self.write("new.html", '<link rel="canonical" href="https://leonbuilds.org/new">')
        self.write("shared.html", '<link rel="canonical" href="https://leonbuilds.org/shared"><p>two</p>')
        self.write("sitemap.xml", sitemap([("/new", "2026-08-24"), ("/shared", "2026-08-24")]))
        after = self.commit("after")

        self.assertEqual(
            indexnow.derive_changed_urls(self.root, before, after, public_paths=set()),
            [
                "https://leonbuilds.org/new",
                "https://leonbuilds.org/old",
                "https://leonbuilds.org/shared",
            ],
        )

    def test_composed_sitemap_replaces_the_archived_inventory(self) -> None:
        self.write("sitemap.xml", sitemap([("/old", "2026-08-24")]))
        before = self.commit("before public composition")
        self.write("content/subscription-public/sitemap.xml", sitemap([("/new", "2026-11-09")]))
        after = self.commit("publish new composition")
        self.assertEqual(indexnow.derive_changed_urls(self.root, before, after, public_paths=set()),
                         ["https://leonbuilds.org/new", "https://leonbuilds.org/old"])

    def test_shared_public_asset_change_submits_current_sitemap(self) -> None:
        routes = [("/", "2026-08-24"), ("/about", "2026-08-24")]
        self.write("sitemap.xml", sitemap(routes))
        self.write("styles.css", "body { color: black; }")
        before = self.commit("before")
        self.write("styles.css", "body { color: navy; }")
        after = self.commit("after")

        self.assertEqual(
            indexnow.derive_changed_urls(
                self.root, before, after, public_paths={"styles.css", "sitemap.xml"}
            ),
            ["https://leonbuilds.org/", "https://leonbuilds.org/about"],
        )

    def test_internal_change_and_sitemap_format_only_do_not_cry_wolf(self) -> None:
        routes = [("/", "2026-08-24")]
        self.write("sitemap.xml", sitemap(routes))
        self.write("content/note.md", "one")
        before = self.commit("before")
        self.write("content/note.md", "two")
        self.write("sitemap.xml", sitemap(routes) + "\n")
        after = self.commit("after")
        self.assertEqual(
            indexnow.derive_changed_urls(
                self.root, before, after, public_paths={"sitemap.xml"}
            ),
            [],
        )

    def test_missing_before_revision_submits_every_current_url(self) -> None:
        self.write("sitemap.xml", sitemap([("/", "2026-08-24"), ("/about", "2026-08-24")]))
        after = self.commit("initial")
        self.assertEqual(
            indexnow.derive_changed_urls(self.root, indexnow.ZERO_REVISION, after, public_paths=set()),
            ["https://leonbuilds.org/", "https://leonbuilds.org/about"],
        )

    def test_submit_checkout_must_be_clean_current_head(self) -> None:
        self.write("sitemap.xml", sitemap([("/", "2026-08-24")]))
        before = self.commit("before")
        self.write("sitemap.xml", sitemap([("/", "2026-08-25")]))
        after = self.commit("after")
        indexnow.ensure_submit_checkout(self.root, after, {"sitemap.xml"})
        with self.assertRaisesRegex(indexnow.IndexNowError, "currently checked-out HEAD"):
            indexnow.ensure_submit_checkout(self.root, before, {"sitemap.xml"})
        self.write("sitemap.xml", sitemap([("/", "2026-08-26")]))
        with self.assertRaisesRegex(indexnow.IndexNowError, "sources are dirty"):
            indexnow.ensure_submit_checkout(self.root, after, {"sitemap.xml"})


class ProtocolTests(unittest.TestCase):
    def test_origin_only_root_canonical_normalizes_to_slash(self) -> None:
        self.assertEqual(
            indexnow.validate_public_url("https://leonbuilds.org"),
            "https://leonbuilds.org/",
        )

    def test_payload_rejects_off_host_and_duplicates(self) -> None:
        key = KEY
        with self.assertRaises(indexnow.IndexNowError):
            indexnow.make_payload(["https://example.com/page"], key)
        with self.assertRaises(indexnow.IndexNowError):
            indexnow.make_payload(["https://leonbuilds.org/a", "https://leonbuilds.org/a"], key)

    def test_key_body_and_canonical_cardinality_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / indexnow.INDEXNOW_KEY_FILE).write_text("c" * 32, encoding="ascii")
            with self.assertRaisesRegex(indexnow.IndexNowError, "filename"):
                indexnow.read_key(root)
        with self.assertRaisesRegex(indexnow.IndexNowError, "multiple canonical tags"):
            indexnow.canonical_from_html(
                '<link rel="canonical" href="https://leonbuilds.org/about">' * 2,
                "duplicate.html",
            )

    def test_live_proof_requires_exact_fingerprint_key_and_final_recheck(self) -> None:
        fingerprint = "a" * 64
        key = KEY
        calls: list[str] = []

        def opener(request, timeout):
            calls.append(request.full_url)
            parsed = urllib.parse.urlsplit(request.full_url)
            body = key if parsed.path.endswith(indexnow.INDEXNOW_KEY_FILE) else fingerprint
            return FakeResponse(200, body, request.full_url)

        indexnow.verify_live_proof(fingerprint, key, opener=opener)
        self.assertEqual(len(calls), 3)

        def wrong_key(request, timeout):
            parsed = urllib.parse.urlsplit(request.full_url)
            body = "c" * 32 if parsed.path.endswith(indexnow.INDEXNOW_KEY_FILE) else fingerprint
            return FakeResponse(200, body, request.full_url)

        with self.assertRaisesRegex(indexnow.IndexNowError, "key does not match"):
            indexnow.verify_live_proof(fingerprint, key, opener=wrong_key)

    def test_submit_accepts_only_200_or_202(self) -> None:
        payload = indexnow.make_payload(["https://leonbuilds.org/about"], KEY)
        for status in (200, 202):
            with self.subTest(status=status):
                opener = lambda request, timeout, status=status: FakeResponse(
                    status, "", request.full_url
                )
                self.assertEqual(indexnow.submit_payload(payload, opener=opener), status)
        for status in (201, 204, 400, 422, 429, 500):
            with self.subTest(status=status):
                opener = lambda request, timeout, status=status: FakeResponse(
                    status, "failure", request.full_url
                )
                with self.assertRaisesRegex(indexnow.IndexNowError, f"HTTP {status}"):
                    indexnow.submit_payload(payload, opener=opener)

        def redirected(request, timeout):
            return FakeResponse(200, "", "https://www.indexnow.org/indexnow")

        with self.assertRaisesRegex(indexnow.IndexNowError, "redirected"):
            indexnow.submit_payload(payload, opener=redirected)

        def http_error(request, timeout):
            raise urllib.error.HTTPError(
                request.full_url, 403, "forbidden", {}, io.BytesIO(b"bad key")
            )

        with self.assertRaisesRegex(indexnow.IndexNowError, "HTTP 403"):
            indexnow.submit_payload(payload, opener=http_error)

        def network_error(_request, timeout):
            raise urllib.error.URLError("offline")

        with self.assertRaisesRegex(indexnow.IndexNowError, "request failed"):
            indexnow.submit_payload(payload, opener=network_error)

    def test_default_main_is_dry_run_and_zero_url_submit_is_network_free(self) -> None:
        dry_args = argparse.Namespace(
            before_ref="before",
            after_ref="after",
            submit=False,
            expected_fingerprint=None,
            origin=indexnow.SITE_ORIGIN,
            endpoint=indexnow.INDEXNOW_ENDPOINT,
            timeout=1,
        )
        output = io.StringIO()
        with (
            mock.patch.object(indexnow, "parse_args", return_value=dry_args),
            mock.patch.object(
                indexnow, "derive_changed_urls", return_value=["https://leonbuilds.org/about"]
            ),
            mock.patch.object(indexnow, "read_key", return_value=KEY),
            mock.patch.object(indexnow, "verify_live_proof") as verify,
            mock.patch.object(indexnow, "submit_payload") as submit,
            redirect_stdout(output),
        ):
            self.assertEqual(indexnow.main(), 0)
        self.assertIn("dry run", output.getvalue())
        verify.assert_not_called()
        submit.assert_not_called()

        # A no-op submit is deliberately successful without proof because it
        # neither reads the key nor performs any network request.
        submit_args = argparse.Namespace(**{**vars(dry_args), "submit": True})
        with (
            mock.patch.object(indexnow, "parse_args", return_value=submit_args),
            mock.patch.object(indexnow, "derive_changed_urls", return_value=[]),
            mock.patch.object(indexnow, "verify_live_proof") as verify,
            mock.patch.object(indexnow, "submit_payload") as submit,
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(indexnow.main(), 0)
        verify.assert_not_called()
        submit.assert_not_called()

    def test_submit_binds_expected_fingerprint_to_local_build_before_network(self) -> None:
        args = argparse.Namespace(
            before_ref="before",
            after_ref="after",
            submit=True,
            expected_fingerprint="a" * 64,
            origin=indexnow.SITE_ORIGIN,
            endpoint=indexnow.INDEXNOW_ENDPOINT,
            timeout=1,
        )
        with (
            mock.patch.object(indexnow, "parse_args", return_value=args),
            mock.patch.object(
                indexnow, "derive_changed_urls", return_value=["https://leonbuilds.org/about"]
            ),
            mock.patch.object(indexnow, "read_key", return_value=KEY),
            mock.patch.object(indexnow.build_static, "build_manifest", return_value={}),
            mock.patch.object(indexnow, "ensure_submit_checkout"),
            mock.patch.object(indexnow.build_static, "public_fingerprint", return_value="c" * 64),
            mock.patch.object(indexnow, "verify_live_proof") as verify,
            mock.patch.object(indexnow, "submit_payload") as submit,
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(indexnow.main(), 1)
        verify.assert_not_called()
        submit.assert_not_called()


class WorkflowTests(unittest.TestCase):
    def test_workflow_is_main_push_only_and_orders_live_check_before_submit(self) -> None:
        workflow = (ROOT / ".github/workflows/search-production.yml").read_text(encoding="utf-8")
        self.assertIn("push:", workflow)
        self.assertIn("- main", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("cancel-in-progress: true", workflow)
        build = workflow.index("npm run build:static")
        live = workflow.index("tools/check_live_search.py")
        submit = workflow.index("tools/indexnow.py")
        self.assertLess(build, live)
        self.assertLess(live, submit)
        self.assertGreaterEqual(workflow.count("steps.build.outputs.fingerprint"), 2)


if __name__ == "__main__":
    unittest.main()
