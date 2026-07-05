import urllib.request
import urllib.error
import time


DOCS_URL = "https://iu-students.github.io/route-optimization-platform/"


class TestQRT005DocsAvailability:

    def test_docs_site_returns_200(self):
        start = time.time()
        try:
            with urllib.request.urlopen(DOCS_URL, timeout=15) as resp:
                elapsed = time.time() - start
                assert resp.status == 200, (
                    f"Expected HTTP 200, got {resp.status}"
                )
                assert elapsed < 10.0, (
                    f"Docs site took {elapsed:.2f}s, expected < 10s"
                )
                body = resp.read().decode("utf-8")
                assert "Route Optimization Platform" in body or "route-optimization" in body.lower(), (
                    "Response body does not contain expected project name"
                )
        except urllib.error.HTTPError as e:
            elapsed = time.time() - start
            assert False, (
                f"Docs site returned HTTP {e.code} after {elapsed:.2f}s"
            )
        except urllib.error.URLError as e:
            elapsed = time.time() - start
            assert False, (
                f"Docs site unreachable after {elapsed:.2f}s: {e.reason}"
            )
