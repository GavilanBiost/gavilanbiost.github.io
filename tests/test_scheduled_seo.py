"""Regression checks for scheduled indexing and the static homepage fallback."""
import datetime
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import home_data
import update_blog
import update_sitemap


class ScheduledSEO(unittest.TestCase):
    def test_scheduled_post_enters_listings_and_sitemap_only_when_due(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            post = directory / "scheduled.html"
            post.write_text('<html><head><meta name="robots" content="index, follow">'
                            '<meta name="post-date" content="2026-11-23"></head>'
                            '<body><h1>Scheduled</h1></body></html>')
            before, due = datetime.date(2026, 11, 22), datetime.date(2026, 11, 23)
            with patch.object(update_blog, "POSTS_DIR", directory):
                update_blog.sync_post_indexability(before)
                before_content = post.read_text()
                self.assertIn('content="noindex, follow"', before_content)
                self.assertEqual(update_blog.load_posts(before), [])
                self.assertFalse(update_sitemap.should_include_post(post, before))
                update_blog.sync_post_indexability(before)
                self.assertEqual(post.read_text(), before_content)
                update_blog.sync_post_indexability(due)
                self.assertNotIn("noindex", post.read_text())
                self.assertNotIn(update_blog.SCHEDULED_INDEXING_MARKER, post.read_text())
                self.assertEqual(len(update_blog.load_posts(due)), 1)
                self.assertTrue(update_sitemap.should_include_post(post, due))

    def test_editorial_noindex_is_never_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            post = directory / "excluded.html"
            content = '<meta name="post-date" content="2026-11-23"><meta name="robots" content="noindex, follow">'
            post.write_text(content)
            with patch.object(update_blog, "POSTS_DIR", directory):
                update_blog.sync_post_indexability(datetime.date(2026, 11, 22))
                update_blog.sync_post_indexability(datetime.date(2026, 11, 23))
            self.assertEqual(post.read_text(), content)

    def test_static_home_refreshes_only_marked_cards_and_escapes_content(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            index = directory / "index.html"
            index.write_text('<h1>Profile</h1><!-- home-static:posts:start -->old<!-- home-static:posts:end --><footer>Footer</footer>')
            data = {"posts": [{"title": "A < B & C", "url": "/post/example.html", "description": "<script>bad</script>", "links": []}]}
            with patch.object(home_data, "HOME_HTML_PATH", index), patch.object(home_data, "read_home_data", return_value=data), patch.object(home_data, "read_counts", return_value={}):
                home_data.refresh_static_home()
                content = index.read_text()
                home_data.refresh_static_home()
                self.assertEqual(index.read_text(), content)
            self.assertIn("A &lt; B &amp; C", content)
            self.assertNotIn("<script>", content)
            self.assertIn("<footer>Footer</footer>", content)

    def test_sitemap_collects_social_and_content_images_without_logos(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            post = directory / "example.html"
            post.write_text('<meta name="post-date" content="2026-11-01">'
                            '<meta name="post-image" content="https://gavilanbiost.com/img/social.jpg">'
                            '<img src="/img/logo.png"><article><img src="/img/chart.webp">'
                            '<img src="/img/chart.webp"></article>')
            with patch.object(update_sitemap, "POST_DIR", directory), patch.object(update_sitemap, "TUTORIALES_DIR", directory / "missing"), patch.object(update_sitemap, "to_lastmod", return_value="2026-11-22"):
                entries = update_sitemap.collect_entries()
            entry = next(e for e in entries if e["loc"].endswith("/post/example.html"))
            self.assertEqual(entry["images"], ["https://gavilanbiost.com/img/social.jpg", "https://gavilanbiost.com/img/chart.webp"])


if __name__ == "__main__":
    unittest.main()
