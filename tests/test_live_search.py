from __future__ import annotations

import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import check_live_search
import indexnow


FINGERPRINT = "a" * 64
KEY = Path(indexnow.INDEXNOW_KEY_FILE).stem
ORIGIN = "https://leonbuilds.org"
SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://leonbuilds.org/</loc><lastmod>2026-08-24</lastmod></url>
  <url><loc>https://leonbuilds.org/about</loc><lastmod>2026-08-23</lastmod></url>
</urlset>
"""


class FakeResponse:
    def __init__(
        self,
        status: int,
        body: str,
        url: str,
        content_type: str = "text/plain",
        x_robots: str = "",
    ) -> None:
        self.status = status
        self.body = body.encode("utf-8")
        self.url = url
        self.headers = {"Content-Type": content_type}
        if x_robots:
            self.headers["X-Robots-Tag"] = x_robots

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def getcode(self) -> int:
        return self.status

    def geturl(self) -> str:
        return self.url

    def read(self, _amount: int = -1) -> bytes:
        return self.body


class LiveSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "sitemap.xml").write_text(SITEMAP, encoding="utf-8")
        (self.root / indexnow.INDEXNOW_KEY_FILE).write_text(KEY + "\n", encoding="ascii")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def site_opener(self, overrides: dict[str, FakeResponse] | None = None):
        pages = {
            f"{ORIGIN}/robots.txt": FakeResponse(
                200,
                f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n",
                f"{ORIGIN}/robots.txt",
            ),
            f"{ORIGIN}/sitemap.xml": FakeResponse(
                200, SITEMAP, f"{ORIGIN}/sitemap.xml", "application/xml"
            ),
            f"{ORIGIN}/llms.txt": FakeResponse(
                200, f"# Leon Builds\n- [Home]({ORIGIN}/)", f"{ORIGIN}/llms.txt"
            ),
            f"{ORIGIN}/{indexnow.INDEXNOW_KEY_FILE}": FakeResponse(
                200, KEY, f"{ORIGIN}/{indexnow.INDEXNOW_KEY_FILE}"
            ),
            f"{ORIGIN}/": FakeResponse(
                200,
                f'<link rel="canonical" href="{ORIGIN}/"><p>home</p>',
                f"{ORIGIN}/",
                "text/html; charset=utf-8",
            ),
            f"{ORIGIN}/about": FakeResponse(
                200,
                f'<link rel="canonical" href="{ORIGIN}/about"><p>about</p>',
                f"{ORIGIN}/about",
                "text/html; charset=utf-8",
            ),
        }
        pages.update(overrides or {})

        def opener(request, timeout):
            return pages[request.full_url]

        return opener

    def test_wait_retries_until_exact_fingerprint_and_times_out_on_mismatch(self) -> None:
        bodies = iter(["old", FINGERPRINT])
        requested: list[str] = []

        def opener(request, timeout):
            requested.append(request.full_url)
            return FakeResponse(200, next(bodies), request.full_url)

        sleeps: list[float] = []
        attempts = check_live_search.wait_for_fingerprint(
            FINGERPRINT,
            wait_seconds=10,
            poll_seconds=1,
            opener=opener,
            sleeper=sleeps.append,
            clock=lambda: 0,
        )
        self.assertEqual(attempts, 2)
        self.assertEqual(sleeps, [1])
        self.assertTrue(all(FINGERPRINT in url for url in requested))

        def stale(request, timeout):
            return FakeResponse(200, "old", request.full_url)

        with self.assertRaisesRegex(indexnow.IndexNowError, "timed out"):
            check_live_search.wait_for_fingerprint(
                FINGERPRINT, wait_seconds=0, poll_seconds=1, opener=stale
            )

    def test_live_foundations_validate_local_sitemap_key_and_every_page(self) -> None:
        result = check_live_search.check_live_foundations(
            opener=self.site_opener(), root=self.root
        )
        self.assertEqual(result, {"sitemap_urls": 2, "pages_checked": 2})

    def test_origin_only_homepage_canonical_matches_explicit_root_slash(self) -> None:
        homepage = FakeResponse(
            200,
            f'<link rel="canonical" href="{ORIGIN}"><p>home</p>',
            f"{ORIGIN}/",
            "text/html; charset=utf-8",
        )
        result = check_live_search.check_live_foundations(
            opener=self.site_opener({f"{ORIGIN}/": homepage}), root=self.root
        )
        self.assertEqual(result, {"sitemap_urls": 2, "pages_checked": 2})

    def test_live_foundations_fail_closed_on_crawl_signals(self) -> None:
        cases = {
            "wrong canonical": FakeResponse(
                200,
                f'<link rel="canonical" href="{ORIGIN}/">',
                f"{ORIGIN}/about",
                "text/html",
            ),
            "meta noindex": FakeResponse(
                200,
                f'<link rel="canonical" href="{ORIGIN}/about"><meta name="robots" content="noindex">',
                f"{ORIGIN}/about",
                "text/html",
            ),
            "header noindex": FakeResponse(
                200,
                f'<link rel="canonical" href="{ORIGIN}/about">',
                f"{ORIGIN}/about",
                "text/html",
                "noindex",
            ),
            "non html": FakeResponse(
                200,
                f'<link rel="canonical" href="{ORIGIN}/about">',
                f"{ORIGIN}/about",
                "text/plain",
            ),
            "redirect": FakeResponse(
                200,
                f'<link rel="canonical" href="{ORIGIN}/about">',
                f"{ORIGIN}/about/",
                "text/html",
            ),
        }
        for label, response in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(indexnow.IndexNowError):
                    check_live_search.check_live_foundations(
                        opener=self.site_opener({f"{ORIGIN}/about": response}),
                        root=self.root,
                    )

    def test_composed_public_sitemap_and_current_brand_are_verified(self) -> None:
        public = self.root / "content/subscription-public/sitemap.xml"
        public.parent.mkdir(parents=True)
        public.write_text(SITEMAP, encoding="utf-8")
        (self.root / "sitemap.xml").write_text(SITEMAP.replace("/about", "/retired"), encoding="utf-8")
        result = check_live_search.check_live_foundations(
            opener=self.site_opener({f"{ORIGIN}/llms.txt": FakeResponse(
                200, f"# LeonBuilds\n{ORIGIN}/", f"{ORIGIN}/llms.txt")}), root=self.root)
        self.assertEqual(result["pages_checked"], 2)

    def test_live_foundations_reject_mismatched_sitemap_and_key(self) -> None:
        shorter = SITEMAP.replace(
            '  <url><loc>https://leonbuilds.org/about</loc><lastmod>2026-08-23</lastmod></url>\n',
            "",
        )
        with self.assertRaisesRegex(indexnow.IndexNowError, "do not match"):
            check_live_search.check_live_foundations(
                opener=self.site_opener(
                    {
                        f"{ORIGIN}/sitemap.xml": FakeResponse(
                            200, shorter, f"{ORIGIN}/sitemap.xml", "application/xml"
                        )
                    }
                ),
                root=self.root,
            )
        with self.assertRaisesRegex(indexnow.IndexNowError, "key does not match"):
            check_live_search.check_live_foundations(
                opener=self.site_opener(
                    {
                        f"{ORIGIN}/{indexnow.INDEXNOW_KEY_FILE}": FakeResponse(
                            200, "c" * 32, f"{ORIGIN}/{indexnow.INDEXNOW_KEY_FILE}"
                        )
                    }
                ),
                root=self.root,
            )


if __name__ == "__main__":
    unittest.main()
