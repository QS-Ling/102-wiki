from pathlib import Path
import json
import tempfile
import unittest

from builder import ConfigError, SiteRenderer, WikiRepository
from builder.build import build
from builder.content import biography_parts, highlight_keywords


ROOT = Path(__file__).resolve().parents[1]


class BuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = WikiRepository(ROOT)

    def test_current_repository_validates(self) -> None:
        catalog = self.repository.load()
        self.assertEqual(["jiaoxianting"], [wiki["slug"] for wiki in catalog["wikis"]])
        self.assertEqual(5, len(catalog["wikis"][0]["sections"]))
        self.assertEqual(
            "media/gallery/IMG_20251021_200058.jpg",
            catalog["wikis"][0]["logo"],
        )

    def test_catalog_uses_configured_wiki_media_as_cover(self) -> None:
        rendered = SiteRenderer(self.repository, base_url="/preview/").render_catalog()
        self.assertIn('class="catalog-cover"', rendered)
        self.assertIn('/preview/static/sakuya-logo.svg', rendered)
        self.assertIn(
            "/preview/jiaoxianting/media/gallery/IMG_20251021_200058.jpg",
            rendered,
        )
        self.assertIn('/preview/guide/', rendered)

    def test_content_guide_renders_from_markdown(self) -> None:
        rendered = SiteRenderer(self.repository, base_url="/preview/").render_guide()
        self.assertIn("如何修改已有 Wiki", rendered)
        self.assertIn("如何添加新栏目", rendered)
        self.assertIn('/preview/', rendered)

    def test_urls_support_project_path_and_unicode_media(self) -> None:
        renderer = SiteRenderer(self.repository, base_url="https://example.github.io/yuna-wiki/")
        self.assertEqual(
            "/yuna-wiki/jiaoxianting/media/video/%EF%BC%9F%EF%BC%81%E7%A5%9E%E7%A5%9E%EF%BC%81%EF%BC%9F.mp4",
            renderer.site_url("jiaoxianting", "media", "video/？！神神！？.mp4"),
        )

    def test_static_build_contains_all_routes_and_media(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            build(output, "/preview/")
            expected = [
                output / "index.html",
                output / "CNAME",
                output / "guide/index.html",
                output / "jiaoxianting/index.html",
                output / "jiaoxianting/story/index.html",
                output / "jiaoxianting/biography/index.html",
                output / "jiaoxianting/media/markdown/biography-image1.png",
                output / "jiaoxianting/quotes/index.html",
                output / "jiaoxianting/gallery/index.html",
                output / "jiaoxianting/video/index.html",
                output / "jiaoxianting/media/video/？！神神！？.mp4",
                output / "static/wiki.css",
            ]
            for path in expected:
                self.assertTrue(path.exists(), path)
            rendered = (output / "jiaoxianting/gallery/index.html").read_text(encoding="utf-8")
            self.assertIn("/preview/jiaoxianting/media/gallery/", rendered)
            self.assertNotIn(str(ROOT), rendered)
            self.assertEqual(
                "102wiki.yuna.team\n",
                (output / "CNAME").read_text(encoding="utf-8"),
            )

    def test_new_wiki_needs_only_content_and_registration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "static").mkdir()
            (root / "static/logo.svg").write_text("<svg/>", encoding="utf-8")
            for slug in ("first", "second"):
                wiki_dir = root / "content" / slug
                (wiki_dir / "pages").mkdir(parents=True)
                (wiki_dir / "media").mkdir()
                (wiki_dir / "pages/story.md").write_text(f"# {slug}", encoding="utf-8")
                (wiki_dir / "wiki.json").write_text(json.dumps({
                    "schema_version": 1,
                    "id": slug,
                    "slug": slug,
                    "title": slug.title(),
                    "subtitle": "Test",
                    "description": "Test Wiki",
                    "logo": "/static/logo.svg",
                    "theme": "archive",
                    "sections": [{"id": "story", "name": "Story", "icon": "book", "type": "markdown", "source": "pages/story.md"}],
                }), encoding="utf-8")
            (root / "catalog.json").write_text(json.dumps({
                "schema_version": 1,
                "title": "Test catalog",
                "description": "Test",
                "wikis": [
                    {"id": slug, "directory": f"content/{slug}", "enabled": True, "featured": False}
                    for slug in ("first", "second")
                ],
            }), encoding="utf-8")
            self.assertEqual({"first", "second"}, set(WikiRepository(root).load()["by_slug"]))

    def test_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "catalog.json").write_text(json.dumps({
                "schema_version": 1,
                "title": "Test catalog",
                "description": "Test",
                "wikis": [{"id": "bad", "directory": "../outside", "enabled": True}],
            }), encoding="utf-8")
            with self.assertRaises(ConfigError):
                WikiRepository(root).load()

    def test_keywords_preserve_markup_and_explicit_emphasis(self) -> None:
        html = ('<h1>焦显庭</h1><p title="焦处">焦显庭和焦处 &amp; 焦子'
                '<strong>焦处</strong><b>焦子</b><code>焦处</code>'
                '<a href="https://example.com/焦处">焦处</a>'
                '<img src="焦处.png" alt="焦处" />焦处</p>'
                '<pre>焦处</pre><!--焦处--><script>焦处</script>')
        rendered = highlight_keywords(html, ["焦", "焦处", "焦显庭", "焦子"])
        self.assertEqual(4, rendered.count('class="person-keyword"'))
        self.assertIn('<strong class="person-keyword">焦显庭</strong>', rendered)
        self.assertIn('<h1>焦显庭</h1>', rendered)
        self.assertIn('<strong>焦处</strong><b>焦子</b><code>焦处</code>', rendered)
        self.assertIn('<a href="https://example.com/焦处">焦处</a>', rendered)
        self.assertIn('<img src="焦处.png" alt="焦处" />', rendered)
        self.assertIn('&amp;', rendered)
        self.assertEqual(html, highlight_keywords(html, []))

    def test_biography_title_author_and_fallback(self) -> None:
        self.assertEqual(
            ("文档标题", "作者甲", "第一行\n第二行"),
            biography_parts('\ufeff---\r\nauthor: "作者甲"\r\n---\r\n\r\n# 文档标题 ##\r\n第一行\r\n第二行', "默认标题"),
        )
        self.assertEqual(("默认标题", "", "正文\n\n# 后面的标题"),
                         biography_parts("正文\n\n# 后面的标题", "默认标题"))
        self.assertEqual(("默认标题", "", "```\n# 代码\n```"),
                         biography_parts("```\n# 代码\n```", "默认标题"))
        self.assertEqual(("默认标题", "", "正文"),
                         biography_parts("---\nauthor:\n---\n正文", "默认标题"))

    def test_biography_rendering_preserves_lines_and_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pages").mkdir()
            (root / "media").mkdir()
            (root / "media/photo.png").write_bytes(b"test")
            source = root / "pages/bio.md"
            source.write_text('---\nauthor: 作者甲\n---\n# 自定标题\n焦显庭\n第二行\n\n新段落\n\n![焦处](../media/photo.png)', encoding="utf-8")
            wiki = {"path": root, "slug": "person", "keywords": ["焦显庭", "焦处"]}
            section = {"source": "pages/bio.md", "name": "小传", "default_title": "默认标题"}
            renderer = SiteRenderer(self.repository, base_url="/preview/")
            body = renderer._render_biography(wiki, section)
            self.assertEqual(("自定标题", "作者甲"), (body["title"], body["author"]))
            self.assertIn('</strong><br />\n第二行', body["html"])
            self.assertIn('<p>新段落</p>', body["html"])
            self.assertIn('src="/preview/person/media/photo.png"', body["html"])
            self.assertIn('alt="焦处"', body["html"])
            source.write_text("正文", encoding="utf-8")
            fallback = renderer._render_biography(wiki, section)
            self.assertEqual(("默认标题", ""), (fallback["title"], fallback["author"]))

    def test_published_biography_has_one_title_and_confirmed_author(self) -> None:
        renderer = SiteRenderer(self.repository, base_url="/preview/")
        rendered = renderer.render_section("jiaoxianting", "biography")
        self.assertEqual(1, rendered.count('<h1'))
        self.assertIn('人物传记:jxt</h1>', rendered)
        self.assertIn('作者：坤械23-8涵姐', rendered)
        self.assertIn('/preview/jiaoxianting/media/markdown/biography-image1.png', rendered)
        self.assertIn('class="person-keyword"', renderer.render_section("jiaoxianting", "story"))

    def test_invalid_keyword_config_is_rejected(self) -> None:
        from unittest.mock import patch
        from builder.site import _read_json

        def invalid_keywords(path):
            if path.name == "keywords.json":
                return {"keywords": [""]}
            return _read_json(path)

        with patch("builder.site._read_json", side_effect=invalid_keywords):
            with self.assertRaises(ConfigError):
                self.repository.load()

    def test_insecure_markdown_link_is_rejected(self) -> None:
        source = ROOT / "content/jiaoxianting/pages/story.md"
        wiki = self.repository.load()["wikis"][0]
        renderer = SiteRenderer(self.repository)
        html = '<p><a href="http://example.com">insecure</a></p>'
        with self.assertRaises(ConfigError):
            renderer._validate_external_links(html, source)

    def test_oversized_media_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "static").mkdir()
            (root / "static/logo.svg").write_text("<svg/>", encoding="utf-8")
            wiki_dir = root / "content/test"
            (wiki_dir / "pages").mkdir(parents=True)
            (wiki_dir / "media/gallery").mkdir(parents=True)
            (wiki_dir / "pages/story.md").write_text("# Test", encoding="utf-8")
            with (wiki_dir / "media/gallery/too-large.jpg").open("wb") as file:
                file.truncate(100 * 1024 * 1024 + 1)
            (wiki_dir / "wiki.json").write_text(json.dumps({
                "schema_version": 1,
                "id": "test",
                "slug": "test",
                "title": "Test",
                "subtitle": "Test",
                "description": "Test",
                "logo": "/static/logo.svg",
                "theme": "archive",
                "sections": [{"id": "story", "name": "Story", "icon": "book", "type": "markdown", "source": "pages/story.md"}],
            }), encoding="utf-8")
            (root / "catalog.json").write_text(json.dumps({
                "schema_version": 1,
                "title": "Test",
                "description": "Test",
                "wikis": [{"id": "test", "directory": "content/test", "enabled": True}],
            }), encoding="utf-8")
            with self.assertRaises(ConfigError):
                WikiRepository(root).load()


if __name__ == "__main__":
    unittest.main()
